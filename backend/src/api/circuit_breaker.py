"""Circuit breaker pattern implementation for LLM failure handling.

This module provides:
- CircuitState enum for tracking circuit breaker states
- CircuitBreaker class for managing circuit state transitions
- CriticalPathFallback class with fallback values for critical paths

Used by FR-8.6 (LLM Failure Handling) to prevent cascade failures
and provide graceful degradation.
"""

from datetime import datetime, timedelta
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker states.

    - CLOSED: Normal operation, requests flow through
    - OPEN: Failing, requests are rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker to prevent cascade failures.

    Tracks failures and opens the circuit when a threshold is reached.
    After a timeout, allows limited requests through to test recovery.

    Args:
        failure_threshold: Number of failures before opening circuit.
            Defaults to 5.
        timeout_seconds: Time to wait before attempting recovery.
            Defaults to 60.
    """

    def __init__(
        self, failure_threshold: int = 5, timeout_seconds: int = 60
    ) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.last_failure_time: datetime | None = None

    def record_success(self) -> None:
        """Record a successful operation.

        Resets failure count and closes the circuit if half-open.
        """
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed operation.

        Increments failure count and opens circuit if threshold reached.
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        """Check if a request attempt is allowed.

        Returns:
            True if request should proceed, False if it should be rejected.
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                return True
            if datetime.now() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN state - allow limited requests
        return True


class CriticalPathFallback:
    """Fallback values for critical path operations.

    When LLM operations fail after retries, these conservative defaults
    ensure the system can still return meaningful (though limited) results.
    """

    TOOL_SELECTION_FALLBACK = ["market_share_trend"]
    """Fallback tool list when tool selection fails."""

    DIMENSION_EXTRACTION_FALLBACK = {"brand": [], "period": "last_quarter"}
    """Fallback dimensions when extraction fails."""

    @staticmethod
    def get_fallback_tool() -> str:
        """Get the primary fallback tool for critical paths.

        Returns:
            The first fallback tool name.
        """
        return CriticalPathFallback.TOOL_SELECTION_FALLBACK[0]
