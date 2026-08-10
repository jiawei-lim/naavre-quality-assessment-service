from .metadata_catalogue_client import *
from ...types.result_types import *
from ...types.quality_dimensions import QualityDimension
from dataclasses import dataclass
from owslib.csw import CatalogueServiceWeb
import functools
import re
import html
import spdx_license_list as spdx
import lxml.etree as etree


@dataclass(frozen=True)
class FairCheckMeta:
    check_type: str
    quality_subcharacteristic: str
    message: str

    def result(self, severity: str, value=None) -> ValueCheckResult:
        return ValueCheckResult(
            check_type = self.check_type,
            quality_dimension = QualityDimension.FAIR,
            quality_subcharacteristic = self.quality_subcharacteristic,
            message = self.message,
            severity = severity,
            value = value
        )


def fair_check(check_type: str, quality_subcharacteristic: str, message: str):
    def decorator(fn):
        meta = FairCheckMeta(check_type, quality_subcharacteristic, message)

        @functools.wraps(fn)
        def wrapper(self) -> ValueCheckResult:
            if not self._valid_record_exists():
                return meta.result("failed", value = self._unavailable_reason)
            return fn(self, meta)

        wrapper._fair_meta = meta
        return wrapper
    return decorator


class FairCheck:
    MULTIPLE = -1
    CSW_URL = "https://metadatacatalogue.lifewatch.eu/geonetwork/srv/eng/csw"
    ISO = "http://www.isotc211.org/2005/gmd"
    PID = re.compile(r"^(https?://|doi:)", re.I)
    UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
    SPDX_IDS = sorted(spdx.LICENSES.keys(), key=len, reverse=True)

    def __init__(self, name:str):
        self._unavailable_reason = None
        try:
            self.uuid = get_metadata_uuid(name)
        except ValueError:
            self.uuid = self.MULTIPLE
            self._unavailable_reason = "Multiple metadata records matched this workflow"
        except LookupError:
            self.uuid = None
            self._unavailable_reason = "No metadata record found for this workflow"

        if self._valid_record_exists():
            self.csw = CatalogueServiceWeb(self.CSW_URL)
            self._set_dc_record()
            self._set_iso_xml()

    def run_checks(self) -> list[ValueCheckResult]:
        return [
            getattr(self, name)()
            for name, attr in vars(type(self)).items()
            if hasattr(attr, "_fair_meta")
        ]

    @fair_check("f4_registered", "Findability", "Registered or indexed in a searchable FAIR resource")
    def check_registered(self, meta) -> ValueCheckResult:
        return meta.result("passed")

    @fair_check("f1_persistent", "Findability", "Has persistent identifier (PID)")
    def check_persistent_identifier(self, meta) -> ValueCheckResult:
        ids = self._field_values(self.dc_record, "identifier")
        persistent = [i for i in ids if self.PID.match(i)]
        return meta.result("passed" if persistent else "failed")

    @fair_check("a1_persistent", "Accessibility", "Retrivable via identifiers")
    def check_retrievable(self, meta) -> ValueCheckResult:
        root = etree.fromstring(self.iso_xml.encode())

        links = root.xpath("//*[local-name()='linkage']//text() | //*[local-name()='URL']/text()")
        links = [l.strip() for l in links if l.strip().startswith("http")]
        links = [l for l in links if "naavre" in l.lower()]

        result = map(self._resolves,links)
        return meta.result("passed" if all(result) else "failed")

    @fair_check("f2_rich", "Findability", "Has rich metadata")
    def check_rich_metadata(self, meta) -> ValueCheckResult:
        RICH_FIELDS = ["title", "abstract", "subjects", "creator", "publisher","date", "type", "language", "rights", "relation"]
        result = [f for f in RICH_FIELDS if self._field_values(self.dc_record, f)]

        return meta.result(
            "failed" if len(result) != len(RICH_FIELDS) else "passed",
            value = f"{len(result)} out of {len(RICH_FIELDS)} required fields specified"
        )

    @fair_check("r1.1_license", "Reusability", "Has a clear and accessible license")
    def check_license(self, meta) -> ValueCheckResult:
        license_id = self._match_license(self.iso_xml)
        if license_id:
            return meta.result("passed", value = license_id)
        else:
            return meta.result("failed")

    @fair_check("r1.1_component_license", "Reusability", "All workflow components have a clear and accessible license")
    def check_component_license(self, meta) -> ValueCheckResult:
        services = self._extract_component_services()
        results = []
        for name, uuid in services:
            component_xml = self._get_component_iso_xml(uuid)
            license_id = self._match_license(component_xml) if component_xml else None
            results.append({"service": name, "uuid": uuid, "license": license_id})

        all_licensed = bool(results) and all(r["license"] for r in results)
        return meta.result("passed" if all_licensed else "failed", value = results)

    def _match_license(self, text: str) -> str | None:
        for lic_id in self.SPDX_IDS:
            if re.search(rf"\b{re.escape(lic_id)}\b", text, re.IGNORECASE):
                return lic_id
        return None

    def _extract_component_services(self) -> list[tuple]:
        root = etree.fromstring(self.iso_xml.encode())
        services = []
        for node in root.xpath("//*[local-name()='LW_WorkflowContainServices']"):
            name = node.xpath("./*[local-name()='serviceName_workflow']//*[local-name()='CharacterString']/text()")
            ref = node.xpath("./*[local-name()='serviceReference_workflow']//*[local-name()='CharacterString']/text()")
            name = name[0].strip() if name else None
            ref = ref[0].strip() if ref else None
            match = self.UUID_RE.search(ref) if ref else None
            if match:
                services.append((name, match.group(0)))
        return services

    def _get_component_iso_xml(self, uuid: str) -> str | None:
        try:
            self.csw.getrecordbyid(id=[uuid], outputschema=self.ISO)
            rec = self.csw.records.get(uuid)
        except Exception:
            return None
        if rec is None:
            return None
        xml = rec.xml
        return xml.decode("utf-8", "replace") if isinstance(xml, bytes) else xml

    def _set_iso_xml(self):
        self.csw.getrecordbyid(id=[self.uuid], outputschema=self.ISO)
        rec = self.csw.records.get(self.uuid)
        if rec is None:
            raise Exception("XML of record not found")
        xml = rec.xml
        self.iso_xml = xml.decode("utf-8", "replace") if isinstance(xml, bytes) else xml

    def _set_dc_record(self):
        self.csw.getrecordbyid(id=[self.uuid], esn="full")
        self.dc_record = self.csw.records.get(self.uuid)

    def _resolves(self, url:str):
        try:
            r = requests.head(url, allow_redirects=True, timeout=10)
            if r.status_code in (403, 405):
                r = requests.get(url, stream=True, timeout=10)
            return r.status_code == 200
        except requests.RequestException:
            return None

    def _field_values(self,rec, name):
        """Read a CswRecord field as a list (some are scalars, some are lists)."""
        val = getattr(rec, name, None)
        if not val:
            return []
        return [self._clean(v) for v in val] if isinstance(val, list) else [self._clean(val)]

    def _clean(self,text):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()

    def _valid_record_exists(self):
        return self.uuid is not None and self.uuid != self.MULTIPLE
