"""Cloud Tasks wrapper for marketing automation jobs."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.config import settings


class CloudTasksService:
    """Queue HTTP tasks for marketing event processing."""

    def __init__(self) -> None:
        self._project_id = settings.cloud_tasks_project_id or settings.firebase_project_id

    def enqueue_marketing_event(self, event_id: str, processor: str) -> str:
        path = f"/api/v1/marketing/tasks/{processor}"
        return self._create_task(
            queue_name=settings.cloud_tasks_events_queue,
            path=path,
            payload={"event_id": event_id},
        )

    def enqueue_follow_up_job(self, job_id: str, schedule_at: datetime) -> str:
        return self._create_task(
            queue_name=settings.cloud_tasks_followups_queue,
            path="/api/v1/marketing/tasks/process-follow-up-job",
            payload={"job_id": job_id},
            schedule_at=schedule_at,
        )

    def enqueue_reconcile_jobs(self) -> str:
        return self._create_task(
            queue_name=settings.cloud_tasks_followups_queue,
            path="/api/v1/marketing/tasks/reconcile-due-jobs",
            payload={},
        )

    def enqueue_escalation_notification(self, escalation_id: str) -> str:
        return self._create_task(
            queue_name=settings.cloud_tasks_events_queue,
            path="/api/v1/marketing/tasks/process-escalation-notification",
            payload={"escalation_id": escalation_id},
        )

    def _create_task(
        self,
        queue_name: str,
        path: str,
        payload: dict[str, Any],
        schedule_at: datetime | None = None,
    ) -> str:
        """Create a Cloud Tasks HTTP task or return a synthetic local task id."""
        if not settings.cloud_tasks_enabled:
            suffix = schedule_at.isoformat() if schedule_at else "immediate"
            return f"local-task::{queue_name}::{path}::{suffix}"

        from google.cloud import tasks_v2
        from google.protobuf import timestamp_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(
            self._project_id,
            settings.cloud_tasks_location,
            queue_name,
        )
        task: dict[str, Any] = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{settings.backend_base_url.rstrip('/')}{path}",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode("utf-8"),
            }
        }

        if settings.internal_task_secret:
            task["http_request"]["headers"]["X-Internal-Token"] = settings.internal_task_secret

        if schedule_at:
            schedule_ts = timestamp_pb2.Timestamp()
            schedule_ts.FromDatetime(schedule_at)
            task["schedule_time"] = schedule_ts

        created = client.create_task(parent=parent, task=task)
        return created.name


_task_queue_service: CloudTasksService | None = None


def get_task_queue_service() -> CloudTasksService:
    """Get the shared Cloud Tasks wrapper instance."""
    global _task_queue_service
    if _task_queue_service is None:
        _task_queue_service = CloudTasksService()
    return _task_queue_service
