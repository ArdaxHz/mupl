"""Session management module for upload sessions."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any

logger = logging.getLogger("mupl")


class SessionManager:
    """Manages upload session data and metadata."""

    def __init__(self):
        """Initialize the session manager."""
        self._session_id = None
        self._session_data = {}
        self._chapter_metadata = {}

    def start_session(self, session_data: Optional[Dict] = None) -> str:
        """Start a new session and return session ID."""
        self._session_id = str(uuid.uuid4())
        self._session_data = {
            "session_id": self._session_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,
            "status": "active",
        }

        if session_data:
            self._session_data.update(session_data)

        logger.info(f"Started new session: {self._session_id}")
        return self._session_id

    def end_session(self) -> None:
        """End the current session."""
        if self._session_id:
            self._session_data["end_time"] = datetime.now(timezone.utc).isoformat()
            self._session_data["status"] = "completed"
            logger.info(f"Ended session: {self._session_id}")

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._session_id

    def get_session_data(self) -> Dict:
        """Get the current session data."""
        return self._session_data.copy()

    def update_session_data(self, **updates) -> None:
        """Update session data with new values."""
        self._session_data.update(updates)

    def set_chapter_metadata(self, metadata: Dict) -> None:
        """Set chapter metadata for the session."""
        self._chapter_metadata = metadata.copy()

    def get_chapter_metadata(self) -> Dict:
        """Get chapter metadata."""
        return self._chapter_metadata.copy()

    def update_chapter_metadata(self, **updates) -> None:
        """Update chapter metadata."""
        self._chapter_metadata.update(updates)

    def add_session_event(self, event_type: str, event_data: Any) -> None:
        """Add an event to the session log."""
        if "events" not in self._session_data:
            self._session_data["events"] = []

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": event_data,
        }

        self._session_data["events"].append(event)
        logger.debug(f"Added session event: {event_type}")

    def get_session_events(self) -> list:
        """Get all session events."""
        return self._session_data.get("events", [])

    def clear_session(self) -> None:
        """Clear the current session."""
        self._session_id = None
        self._session_data.clear()
        self._chapter_metadata.clear()
        logger.debug("Cleared session data")

    def is_session_active(self) -> bool:
        """Check if a session is currently active."""
        return (
            self._session_id is not None
            and self._session_data.get("status") == "active"
        )

    def get_session_duration(self) -> Optional[float]:
        """Get session duration in seconds."""
        start_time = self._session_data.get("start_time")
        if not start_time:
            return None

        end_time = self._session_data.get("end_time")
        if not end_time:
            end_time = datetime.now(timezone.utc).isoformat()

        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            return (end_dt - start_dt).total_seconds()
        except (ValueError, TypeError):
            return None

    def get_session_summary(self) -> Dict:
        """Get a comprehensive session summary."""
        return {
            "session_id": self._session_id,
            "session_data": self._session_data.copy(),
            "chapter_metadata": self._chapter_metadata.copy(),
            "is_active": self.is_session_active(),
            "duration_seconds": self.get_session_duration(),
            "events_count": len(self.get_session_events()),
        }

    def export_session(self) -> Dict:
        """Export complete session data for external use."""
        return {
            "session_id": self._session_id,
            "session_data": self._session_data.copy(),
            "chapter_metadata": self._chapter_metadata.copy(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    def import_session(self, session_export: Dict) -> bool:
        """Import session data from external source."""
        try:
            self._session_id = session_export.get("session_id")
            self._session_data = session_export.get("session_data", {}).copy()
            self._chapter_metadata = session_export.get("chapter_metadata", {}).copy()

            logger.info(f"Imported session: {self._session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return False
