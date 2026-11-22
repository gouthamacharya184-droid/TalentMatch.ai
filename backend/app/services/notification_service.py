from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.all_models import Notification, ActivityLog


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        title: str,
        message: str,
        type: str = "info",
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            data=data or {}
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def log_activity(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        act = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {}
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        return act
