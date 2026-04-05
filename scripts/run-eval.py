#!/usr/bin/env python
"""CLI for running the eval framework.

FR-7.1-7.6: Eval Framework CLI
Usage:
    python scripts/run-eval.py --run           # Run full eval suite
    python scripts/run-eval.py --run-level 1  # Run Level 1 only
    python scripts/run-eval.py --report       # Generate report from last run
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from src.eval.runner import EvalRunner, EvalRunnerConfig
from src.eval.models import ComplexityLevel


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run evaluation suite for Proteus agent"
    )

    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the full eval suite",
    )
    parser.add_argument(
        "--run-level",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Run only a specific complexity level",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Filter by category (e.g., market_share, growth)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=3,
        help="Number of trials per test case (default: 3)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for LLM calls (default: 0.0)",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="backend/test-reports",
        help="Directory for results (default: backend/test-reports)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate report from saved results",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Enable parallel execution",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="Max concurrent tests (default: 10)",
    )

    return parser.parse_args()


async def run_eval(args):
    """Run the eval suite."""
    # Determine complexity level filter
    complexity_filter = None
    if args.run_level:
        level_map = {
            1: ComplexityLevel.LEVEL_1_SIMPLE,
            2: ComplexityLevel.LEVEL_2_MODERATE,
            3: ComplexityLevel.LEVEL_3_COMPLEX,
            4: ComplexityLevel.LEVEL_4_MULTI_TOOL,
            5: ComplexityLevel.LEVEL_5_AMBIGUOUS,
        }
        complexity_filter = level_map[args.run_level]

    # Create config
    config = EvalRunnerConfig(
        num_trials=args.trials,
        temperature=args.temperature,
        results_dir=args.results_dir,
        parallel_execution=args.parallel,
        max_concurrent=args.max_concurrent,
    )

    # Create runner
    runner = EvalRunner(config)

    # Print configuration
    print("=" * 60)
    print("Proteus Eval Framework")
    print("=" * 60)
    print(f"Trials per test: {config.num_trials}")
    print(f"Temperature: {config.temperature}")
    print(f"Parallel execution: {config.parallel_execution}")
    if complexity_filter:
        print(f"Complexity filter: {complexity_filter.value}")
    if args.category:
        print(f"Category filter: {args.category}")
    print("=" * 60)
    print()

    # Run eval
    print("Running eval suite...")
    eval_run = await runner.run_eval(
        filter_complexity=complexity_filter,
        filter_category=args.category,
    )

    # Print summary
    print(runner.get_summary(eval_run))

    # Save results
    runner.save_results(eval_run)

    return eval_run


def generate_report(args):
    """Generate report from saved results."""
    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    # Find most recent result file
    result_files = list(results_dir.glob("eval_run_*.json"))

    if not result_files:
        print("Error: No eval results found")
        sys.exit(1)

    # Sort by modification time (most recent first)
    result_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    latest = result_files[0]

    print(f"Loading results from: {latest}")

    import json
    with open(latest) as f:
        data = json.load(f)

    print("=" * 60)
    print(f"Eval Run: {data['run_id']}")
    print(f"Timestamp: {data['timestamp']}")
    print("=" * 60)
    print()
    print("Aggregate Metrics:")
    for key, value in data["aggregate_metrics"].items():
        print(f"  {key}: {value}")
    print()
    print(f"Total Tests: {data['total_tests']}")
    print(f"Passed: {data['passed_tests']}")
    print(f"Failed: {data['total_tests'] - data['passed_tests']}")


def main():
    """Main entry point."""
    args = parse_args()

    if not args.run and not args.report:
        print("Error: Must specify --run or --report")
        print("Use --help for more information")
        sys.exit(1)

    if args.report:
        generate_report(args)
    else:
        asyncio.run(run_eval(args))


if __name__ == "__main__":
    main()