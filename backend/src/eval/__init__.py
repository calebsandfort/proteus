"""Eval framework package."""

from src.eval.anomalies import ANOMALY_TEST_CASES, AnomalyTestCase
from src.eval.metrics import (
    EvalMetrics,
    MetricCalculator,
    compute_accuracy,
    compute_parameter_accuracy,
)
from src.eval.models import (
    ComplexityLevel,
    EvalResult,
    EvalRun,
    ExpectedParameter,
    TestFixture,
)
from src.eval.runner import EvalRunner, EvalRunnerConfig, run_evaluation

__all__ = [
    # Models
    "ComplexityLevel",
    "ExpectedParameter",
    "TestFixture",
    "EvalResult",
    "EvalRun",
    # Anomalies
    "AnomalyTestCase",
    "ANOMALY_TEST_CASES",
    # Metrics
    "EvalMetrics",
    "MetricCalculator",
    "compute_accuracy",
    "compute_parameter_accuracy",
    # Runner
    "EvalRunner",
    "EvalRunnerConfig",
    "run_evaluation",
]