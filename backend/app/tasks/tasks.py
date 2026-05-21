"""
Background tasks for automated workflows:
- Recording processing after class ends
- Attendance auto-generation
- Notification dispatch
- Invoice generation
"""
from app.tasks.worker import celery_app


@celery_app.task(name="process_recording")
def process_recording(session_id: str, file_path: str):
    """Process and upload recording after a live class ends."""
    # TODO: Implement video processing pipeline
    # 1. Upload to MinIO/S3
    # 2. Create Recording DB entry
    # 3. Add to student spaces
    # 4. Send notifications
    pass


@celery_app.task(name="generate_attendance")
def generate_attendance(session_id: str):
    """Auto-generate attendance report after session ends."""
    # TODO: Compile attendance from WebSocket join/leave events
    pass


@celery_app.task(name="send_notification")
def send_notification(user_id: str, title: str, message: str, notif_type: str = "info"):
    """Send notification to user (in-app + email if configured)."""
    # TODO: Create DB notification + push via WebSocket + email
    pass


@celery_app.task(name="post_class_workflow")
def post_class_workflow(session_id: str):
    """
    Automated workflow after a live class ends:
    1. Generate attendance
    2. Process recording
    3. Upload to student space
    4. Notify students
    """
    generate_attendance.delay(session_id)
    # Recording processing will be triggered separately when file is ready
    pass
