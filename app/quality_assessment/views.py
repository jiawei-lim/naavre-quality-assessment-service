from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .assets.base_asset import BaseAsset
from .models import *
from .serializers import *
from .workflow_files.adapter import WorkflowFileAdapter
from .services import workflow_file_service

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

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        base_asset = self._base_asset_from_validated_data(serializer.validated_data)
        workflow_file_asset = WorkflowFileAdapter().from_base_asset(
            base_asset,
            asset_type=serializer.validated_data["asset_type"],
        )

        graph = workflow_file_service.build_workflow_multidigraph(workflow_file_asset)
        print(f"Self-Loops:{workflow_file_service.get_self_loops(graph)}\n")
        print(f"Cycles:{workflow_file_service.get_cycles(graph)}\n")
        print(f"disconnected:{workflow_file_service.get_disconnected_components(graph)}\n")
        print(f"isolated:{workflow_file_service.get_isolated_nodes(graph)}\n")
        print(f"i/o mismatch:{workflow_file_service.get_input_output_type_mismatches(graph)}\n")

        return Response({"detail": "WorkflowFileAsset printed to terminal."})

    def _base_asset_from_validated_data(self, validated_data):
        asset_data = validated_data.get("asset_data", {})

        if not isinstance(asset_data, dict):
            raise ValidationError({"asset_data": "Expected an object."})

        return BaseAsset(
            id=asset_data.get("id") or validated_data.get("asset_id", ""),
            title=asset_data.get("title", ""),
            description=asset_data.get("description", ""),
            created=asset_data.get("created"),
            modified=asset_data.get("modified"),
            owner=asset_data.get("owner"),
            virtual_lab=asset_data.get("virtual_lab"),
            shared_with_scopes=asset_data.get("shared_with_scopes", []),
            shared_with_users=asset_data.get("shared_with_users", []),
            raw_payload=asset_data,
        )
