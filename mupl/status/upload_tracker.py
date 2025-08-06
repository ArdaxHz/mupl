"""Upload status tracking module."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger("mupl")


class UploadTracker:
    """Tracks upload status and statistics for dependency usage."""

    def __init__(self):
        """Initialize the upload tracker."""
        self._current_status = "idle"  # idle, uploading, completed, failed
        self._current_chapter = None
        self._failed_uploads = []
        self._successful_uploads = []
        self._statistics = {
            "total_chapters": 0,
            "uploaded_chapters": 0,
            "failed_chapters": 0,
            "start_time": None,
            "end_time": None,
        }

    def get_status(self) -> str:
        """Get the current upload status."""
        return self._current_status

    def set_status(self, status: str) -> None:
        """Set the current upload status."""
        valid_statuses = {"idle", "uploading", "completed", "failed"}
        if status not in valid_statuses:
            logger.warning(f"Invalid status: {status}. Must be one of {valid_statuses}")
            return

        self._current_status = status
        logger.debug(f"Upload status changed to: {status}")

    def get_current_chapter(self) -> Optional[str]:
        """Get the currently uploading chapter."""
        return self._current_chapter

    def set_current_chapter(self, chapter: Optional[str]) -> None:
        """Set the currently uploading chapter."""
        self._current_chapter = chapter

    def get_statistics(self) -> Dict:
        """Get upload statistics."""
        return self._statistics.copy()

    def get_failed_uploads(self) -> List[Path]:
        """Get list of failed uploads."""
        return self._failed_uploads.copy()

    def get_successful_uploads(self) -> List[Path]:
        """Get list of successful uploads."""
        return self._successful_uploads.copy()

    def add_failed_upload(self, file_path: Union[Path, str]) -> None:
        """Add a failed upload to the list."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        if path not in self._failed_uploads:
            self._failed_uploads.append(path)
            self._statistics["failed_chapters"] += 1
            logger.warning(f"Added failed upload: {path}")

    def add_successful_upload(self, file_path: Union[Path, str]) -> None:
        """Add a successful upload to the list."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        if path not in self._successful_uploads:
            self._successful_uploads.append(path)
            self._statistics["uploaded_chapters"] += 1
            logger.info(f"Added successful upload: {path}")

    def start_upload_session(self, total_chapters: int) -> None:
        """Start a new upload session."""
        self._statistics["total_chapters"] = total_chapters
        self._statistics["uploaded_chapters"] = 0
        self._statistics["failed_chapters"] = 0
        self._statistics["start_time"] = datetime.now(timezone.utc).isoformat()
        self._statistics["end_time"] = None
        self._current_status = "uploading"
        self._failed_uploads.clear()
        self._successful_uploads.clear()
        logger.info(f"Started upload session with {total_chapters} chapters")

    def end_upload_session(self) -> None:
        """End the current upload session."""
        self._statistics["end_time"] = datetime.now(timezone.utc).isoformat()

        # Determine final status
        if self._statistics["failed_chapters"] == 0:
            self._current_status = "completed"
        elif self._statistics["uploaded_chapters"] == 0:
            self._current_status = "failed"
        else:
            self._current_status = "completed"  # Partial success

        self._current_chapter = None
        logger.info(f"Ended upload session. Status: {self._current_status}")

    def reset_statistics(self) -> None:
        """Reset all upload statistics."""
        self._statistics = {
            "total_chapters": 0,
            "uploaded_chapters": 0,
            "failed_chapters": 0,
            "start_time": None,
            "end_time": None,
        }
        self._failed_uploads.clear()
        self._successful_uploads.clear()
        self._current_status = "idle"
        self._current_chapter = None
        logger.info("Reset upload statistics")

    def get_success_rate(self) -> float:
        """Get the success rate of uploads."""
        total = self._statistics["total_chapters"]
        if total == 0:
            return 0.0
        return (self._statistics["uploaded_chapters"] / total) * 100

    def get_upload_duration(self) -> Optional[float]:
        """Get the duration of the upload session in seconds."""
        start_time = self._statistics.get("start_time")
        end_time = self._statistics.get("end_time")

        if not start_time:
            return None

        if not end_time:
            # Session is still running
            end_time = datetime.now(timezone.utc).isoformat()

        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            return (end_dt - start_dt).total_seconds()
        except (ValueError, TypeError):
            return None

    def is_uploading(self) -> bool:
        """Check if currently uploading."""
        return self._current_status == "uploading"

    def has_failures(self) -> bool:
        """Check if there are any failed uploads."""
        return len(self._failed_uploads) > 0

    def get_summary(self) -> Dict:
        """Get a comprehensive summary of the upload session."""
        return {
            "status": self._current_status,
            "current_chapter": self._current_chapter,
            "statistics": self._statistics.copy(),
            "success_rate": self.get_success_rate(),
            "duration_seconds": self.get_upload_duration(),
            "failed_count": len(self._failed_uploads),
            "successful_count": len(self._successful_uploads),
            "is_uploading": self.is_uploading(),
            "has_failures": self.has_failures(),
        }

    def complete_upload_session(self) -> None:
        """Complete the upload session (alias for end_upload_session)."""
        self.end_upload_session()
