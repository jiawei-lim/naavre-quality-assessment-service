from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .adapters import WorkflowFileAdapter
from .models import *
from .serializers import *
from .services.workflow_file import workflow_graph_builder
from .services import metrics_service
from .types.quality_dimensions import QualityDimension


class AssessmentReportListView(generics.ListAPIView):
    queryset = AssessmentReport.objects.all()
    serializer_class = AssessmentReportSerializer


class AssessmentReportDetailView(generics.RetrieveAPIView):
    queryset = AssessmentReport.objects.all()
    serializer_class = AssessmentReportSerializer
    lookup_field = "id"


class AssessmentRunView(generics.GenericAPIView):
    queryset = AssessmentRun.objects.all()
    serializer_class = AssessmentRunSerializer
    supported_workflow_file_asset_types = {"workflow", "workflow_file"}

    def post(self, request, *args, **kwargs):
        #Validate Post Data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        #Validate Asset Type
        asset_type = serializer.validated_data["asset_type"]

        if asset_type not in self.supported_workflow_file_asset_types:
            raise ValidationError(
                {
                    "asset_type": (
                        f"Unsupported asset type for workflow file assessment: "
                        f"{asset_type}"
                    )
                }
            )

        #Extracts workflow file data and convert it into WorkflowFile type
        workflow_file = WorkflowFileAdapter().from_payload(
            self._workflow_file_payload_from_validated_data(
                serializer.validated_data
            )
        )

        #Build workflow file from .naavrewf JSON into networkx graph
        graph = workflow_graph_builder.build_workflow_multidigraph(workflow_file)

        #Run checks, restricted to the requested quality dimensions
        dimensions = frozenset(
            serializer.validated_data.get("quality_dimensions") or QualityDimension
        )
        result = metrics_service.run_checks(graph, dimensions)

        return Response(result)

    def _workflow_file_payload_from_validated_data(self, validated_data):
        """
        Extract workflow file data
        """
        asset_data = validated_data.get("asset_data", {})

        if not isinstance(asset_data, dict):
            raise ValidationError({"asset_data": "Expected an object."})

        payload = dict(asset_data)
        payload["id"] = payload.get("id") or validated_data.get("asset_id", "")
        payload["fileName"] = validated_data.get("fileName", "")
        return payload
