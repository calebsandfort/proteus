from datetime import datetime, timedelta
import time

from src.api.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CriticalPathFallback,
)


class TestCircuitBreakerInitialState:
    """Test circuit breaker initial state is CLOSED."""

    def test_circuit_breaker_initial_state(self) -> None:
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestCircuitBreakerRecordSuccess:
    """Test recording successes resets failure count."""

    def test_circuit_breaker_record_success(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerRecordFailure:
    """Test recording failures increments count."""

    def test_circuit_breaker_record_failure(self) -> None:
        cb = CircuitBreaker(failure_threshold=5)
        cb.record_failure()
        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 3


class TestCircuitBreakerOpensAfterThreshold:
    """Test circuit opens after reaching failure threshold."""

    def test_circuit_breaker_opens_after_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3


class TestCircuitBreakerCanAttempt:
    """Test can_attempt method based on state."""

    def test_circuit_breaker_can_attempt_when_closed(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.can_attempt() is True

    def test_circuit_breaker_rejects_when_open(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_attempt() is False

    def test_circuit_breaker_half_open_after_timeout(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for timeout to expire
        time.sleep(1.1)

        assert cb.can_attempt() is True
        assert cb.state == CircuitState.HALF_OPEN


class TestCriticalPathFallback:
    """Test critical path fallback values."""

    def test_critical_path_fallback_tool(self) -> None:
        fallback = CriticalPathFallback.get_fallback_tool()
        assert fallback == "market_share_trend"

    def test_critical_path_fallback_dimensions(self) -> None:
        fallback = CriticalPathFallback.DIMENSION_EXTRACTION_FALLBACK
        assert fallback["brand"] == []
        assert fallback["period"] == "last_quarter"

    def test_critical_path_fallback_tool_list(self) -> None:
        fallback = CriticalPathFallback.TOOL_SELECTION_FALLBACK
        assert isinstance(fallback, list)
        assert "market_share_trend" in fallback
