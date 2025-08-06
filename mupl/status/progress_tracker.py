"""Progress tracking module for detailed operation progress."""

import logging
from typing import Dict, Optional

logger = logging.getLogger("mupl")


class ProgressTracker:
    """Tracks detailed progress for various operations."""

    def __init__(self):
        """Initialize the progress tracker."""
        self._overall_progress = 0.0  # 0.0 to 1.0
        self._current_phase = "idle"
        self._phase_progress = 0.0
        self._images_uploaded = 0
        self._total_images = 0
        self._completed_uploads = 0
        self._failed_uploads = 0
        self._errors = []

    def get_overall_progress(self) -> float:
        """Get overall progress as a float between 0.0 and 1.0."""
        return self._overall_progress

    def set_overall_progress(self, progress: float) -> None:
        """Set overall progress."""
        self._overall_progress = max(0.0, min(1.0, progress))

    def get_current_phase(self) -> str:
        """Get the current operation phase."""
        return self._current_phase

    def set_current_phase(self, phase: str) -> None:
        """Set the current operation phase."""
        self._current_phase = phase
        self._phase_progress = 0.0
        logger.debug(f"Phase changed to: {phase}")

    def get_phase_progress(self) -> float:
        """Get progress of the current phase."""
        return self._phase_progress

    def set_phase_progress(self, progress: float) -> None:
        """Set progress of the current phase."""
        self._phase_progress = max(0.0, min(1.0, progress))

    def get_images_progress(self) -> Dict:
        """Get image upload progress information."""
        percentage = 0.0
        if self._total_images > 0:
            percentage = (self._images_uploaded / self._total_images) * 100

        return {
            "uploaded_count": self._images_uploaded,
            "total_count": self._total_images,
            "progress_percentage": percentage,
            "remaining_count": self._total_images - self._images_uploaded,
        }

    def set_images_total(self, total: int) -> None:
        """Set the total number of images to upload."""
        self._total_images = max(0, total)
        self._images_uploaded = 0

    def set_total_images(self, total: int) -> None:
        """Alias for set_images_total for backward compatibility."""
        self.set_images_total(total)

    def set_total_chapters(self, total: int) -> None:
        """Set the total number of chapters to process."""
        self._total_chapters = max(0, total)
        self._processed_chapters = 0
        logger.debug(f"Set total chapters to: {total}")

    def get_chapters_progress(self) -> Dict:
        """Get chapter processing progress information."""
        percentage = 0.0
        if hasattr(self, "_total_chapters") and self._total_chapters > 0:
            percentage = (
                getattr(self, "_processed_chapters", 0) / self._total_chapters
            ) * 100

        return {
            "processed_count": getattr(self, "_processed_chapters", 0),
            "total_count": getattr(self, "_total_chapters", 0),
            "progress_percentage": percentage,
            "remaining_count": getattr(self, "_total_chapters", 0)
            - getattr(self, "_processed_chapters", 0),
        }

    def increment_chapters_processed(self, count: int = 1) -> None:
        """Increment the number of processed chapters."""
        if not hasattr(self, "_processed_chapters"):
            self._processed_chapters = 0
        if not hasattr(self, "_total_chapters"):
            self._total_chapters = 0

        self._processed_chapters = min(
            self._total_chapters, self._processed_chapters + count
        )
        logger.debug(
            f"Chapters processed: {self._processed_chapters}/{self._total_chapters}"
        )

    def increment_completed(self, count: int = 1) -> None:
        """Increment the number of completed uploads."""
        self._completed_uploads += count
        logger.debug(f"Completed uploads: {self._completed_uploads}")

    def increment_failed(self, count: int = 1) -> None:
        """Increment the number of failed uploads."""
        self._failed_uploads += count
        logger.debug(f"Failed uploads: {self._failed_uploads}")

    def get_completed_count(self) -> int:
        """Get the number of completed uploads."""
        return self._completed_uploads

    def get_failed_count(self) -> int:
        """Get the number of failed uploads."""
        return self._failed_uploads

    def increment_images_uploaded(self, count: int = 1) -> None:
        """Increment the number of uploaded images."""
        self._images_uploaded = min(self._total_images, self._images_uploaded + count)

        # Update phase progress based on image progress
        if self._total_images > 0:
            self._phase_progress = self._images_uploaded / self._total_images

    def reset_images_progress(self) -> None:
        """Reset image upload progress."""
        self._images_uploaded = 0
        self._total_images = 0
        self._phase_progress = 0.0

    def add_error(self, error: str) -> None:
        """Add an error to the error list."""
        self._errors.append(error)
        logger.error(f"Progress tracker error: {error}")

    def get_errors(self) -> list:
        """Get list of errors."""
        return self._errors.copy()

    def clear_errors(self) -> None:
        """Clear all errors."""
        self._errors.clear()

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self._errors) > 0

    def reset_all(self) -> None:
        """Reset all progress tracking."""
        self._overall_progress = 0.0
        self._current_phase = "idle"
        self._phase_progress = 0.0
        self._images_uploaded = 0
        self._total_images = 0
        self._completed_uploads = 0
        self._failed_uploads = 0
        self._processed_chapters = 0
        self._total_chapters = 0
        self._errors.clear()
        logger.debug("Reset all progress tracking")

    def get_progress_summary(self) -> Dict:
        """Get a comprehensive progress summary."""
        return {
            "overall_progress": self._overall_progress,
            "overall_percentage": self._overall_progress * 100,
            "current_phase": self._current_phase,
            "phase_progress": self._phase_progress,
            "phase_percentage": self._phase_progress * 100,
            "images": self.get_images_progress(),
            "chapters": self.get_chapters_progress(),
            "completed_uploads": self._completed_uploads,
            "failed_uploads": self._failed_uploads,
            "errors_count": len(self._errors),
            "has_errors": self.has_errors(),
        }

    def update_from_phase_weights(self, phase_weights: Dict[str, float]) -> None:
        """Update overall progress based on phase weights.

        Args:
            phase_weights: Dictionary mapping phase names to their completion weights
                          e.g., {'validation': 0.1, 'processing': 0.3, 'upload': 0.6}
        """
        if self._current_phase not in phase_weights:
            return

        # Calculate overall progress based on completed phases and current phase progress
        completed_weight = 0.0
        current_phase_weight = phase_weights[self._current_phase]

        # Sum weights of completed phases (phases before current one)
        phase_order = list(phase_weights.keys())
        try:
            current_index = phase_order.index(self._current_phase)
            for i in range(current_index):
                completed_weight += phase_weights[phase_order[i]]
        except ValueError:
            pass

        # Add progress from current phase
        current_phase_contribution = current_phase_weight * self._phase_progress

        self._overall_progress = completed_weight + current_phase_contribution
        self._overall_progress = max(0.0, min(1.0, self._overall_progress))

    def complete_all(self) -> None:
        """Complete all progress tracking (alias for reset_all)."""
        self.reset_all()
