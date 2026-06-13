from django.db import models
import uuid

class AssessmentRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    asset_id = models.CharField(max_length=255, blank=True)
    asset_reference = models.URLField(max_length=1000, blank=True)
    asset_type = models.CharField(max_length=100)

    triggered_by = models.CharField(max_length=255, blank=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class AssessmentReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    assessment_run = models.OneToOneField(
        "AssessmentRun",
        on_delete=models.CASCADE,
        related_name="report",
    )

    description = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, blank=True)
