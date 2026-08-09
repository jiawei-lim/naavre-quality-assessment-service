from .metadata_catalogue_client import *
from ...types.result_types import *
from dataclasses import dataclass, field
from owslib.csw import CatalogueServiceWeb
import re
import html
import spdx_license_list as spdx
import lxml.etree as etree

class FairCheck:
    MULTIPLE = -1
    CSW_URL = "https://metadatacatalogue.lifewatch.eu/geonetwork/srv/eng/csw"
    ISO = "http://www.isotc211.org/2005/gmd"
    PID = re.compile(r"^(https?://|doi:)", re.I)
    SPDX_IDS = sorted(spdx.LICENSES.keys(), key=len, reverse=True)

    def __init__(self, name:str):
        try:
            self.uuid = get_metadata_uuid(name)
        except ValueError:
            self.uuid = self.MULTIPLE
        except LookupError:
            self.uuid = None

        if not self._valid_record_exists():
            raise Exception("Metadata record does not exist for name")
        
        self.csw = CatalogueServiceWeb(self.CSW_URL)
        self._set_dc_record()
        self._set_iso_xml()

    def run_checks(self) -> list[ValueCheckResult]:
        return [
            self.check_registered(),
            self.check_persistent_identifier(),
            self.check_rich_metadata(),
            self.check_license(),
            self.check_retrievable()
        ]

    def check_persistent_identifier(self) -> ValueCheckResult:
        ids = self._field_values(self.dc_record, "identifier")
        persistent = [i for i in ids if self.PID.match(i)]
        if persistent:
            return ValueCheckResult(
                            check_type = "f1_persistent",
                            quality_dimension = "FAIR",
                            quality_subcharacteristic= "Findability",
                            message = "Has persistent identifier (PID)",
                            severity = "passed"
                        )
        else:
            return ValueCheckResult(
                                        check_type = "f1_persistent",
                                        quality_dimension = "FAIR",
                                        quality_subcharacteristic= "Findability",
                                        message = "Has persistent identifier i.e. DOI ",
                                        severity = "failed"
                                    )
    def check_retrievable(self) -> ValueCheckResult:
        root = etree.fromstring(self.iso_xml.encode())

        links = root.xpath("//*[local-name()='linkage']//text() | //*[local-name()='URL']/text()")
        links = [l.strip() for l in links if l.strip().startswith("http")]
        links = [l for l in links if "naavre" in l.lower()]

        result = map(self._resolves,links)
        if all(result):
            return ValueCheckResult(
                            check_type = "a1_persistent",
                            quality_dimension = "FAIR",
                            quality_subcharacteristic= "Accessibility",
                            message = "Retrivable via identifiers",
                            severity = "passed"
                        )
        else:
            return ValueCheckResult(
                            check_type = "a1_persistent",
                            quality_dimension = "FAIR",
                            quality_subcharacteristic= "Accessibility",
                            message = "Retrivable via identifiers",
                            severity = "failed"
                        )


    def check_rich_metadata(self) -> ValueCheckResult:
        RICH_FIELDS = ["title", "abstract", "subjects", "creator", "publisher","date", "type", "language", "rights", "relation"]
        result = [f for f in RICH_FIELDS if self._field_values(self.dc_record, f)]

        return ValueCheckResult(
                                check_type = "f2_rich",
                                quality_dimension = "FAIR",
                                quality_subcharacteristic= "Findability",
                                message = "Has rich metadata",
                                severity = "failed" if len(result) != len(RICH_FIELDS) else "passed",
                                value = f"{len(result)} out of {len(RICH_FIELDS)} required fields specified"
                            )

    def check_license(self) -> ValueCheckResult:
        matches = [
            lic_id for lic_id in self.SPDX_IDS
            if re.search(rf"\b{re.escape(lic_id)}\b", self.iso_xml, re.IGNORECASE)
        ]
        if matches:
            return ValueCheckResult(
                check_type = "r1.1_license",
                quality_dimension = "FAIR",
                quality_subcharacteristic= "Reusability",
                message = "Has a clear and accessible license",
                severity = "passed",
                value = matches[0]
            )
        else:
            return ValueCheckResult(
                check_type = "r1.1_license",
                quality_dimension = "FAIR",
                quality_subcharacteristic= "Reusability",
                message = "Has a clear and accessible license",
                severity = "failed"
            )

    def check_component_license(self) -> ValueCheckResult:
        pass

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

    def check_registered(self) -> ValueCheckResult:
        if self._valid_record_exists():
            return ValueCheckResult(
                check_type = "f4_registered",
                quality_dimension = "FAIR",
                quality_subcharacteristic= "Findability",
                message = "Registered or indexed in a searchable FAIR resource",
                severity = "passed"
            )
        else:
            return ValueCheckResult(
                check_type = "f4_registered",
                quality_dimension = "FAIR",
                quality_subcharacteristic= "Findability",
                message = "Registered or indexed in a searchable FAIR resource",
                severity = "failed"
            )

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
        """Strip the HTML GeoNetwork leaks into text fields."""
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()

    def _valid_record_exists(self):
        return self.uuid is not None and self.uuid != self.MULTIPLE
