"""
Performance Benchmarking for Khronos Research System

Measures:
- Query execution times
- Cache effectiveness
- Memory usage
- Batch processing performance
"""

import time
import sys
from typing import Callable, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Benchmark utility for measuring query and operation performance."""

    def __init__(self, name: str = "Benchmark"):
        """Initialize benchmark.

        Args:
            name: Benchmark name
        """
        self.name = name
        self.results: List[Dict[str, Any]] = []
        self.start_time: float = 0
        self.start_memory: int = 0

    def __enter__(self):
        """Context manager entry."""
        self.start_time = time.perf_counter()
        self.start_memory = self._get_memory_usage()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        elapsed = time.perf_counter() - self.start_time
        memory_delta = self._get_memory_usage() - self.start_memory

        result = {
            "name": self.name,
            "elapsed_ms": elapsed * 1000,
            "memory_delta_kb": memory_delta / 1024,
            "timestamp": datetime.now().isoformat(),
            "error": str(exc_val) if exc_val else None,
        }

        self.results.append(result)
        logger.info(f"{self.name}: {elapsed*1000:.2f}ms")

        return False  # Don't suppress exceptions

    def run_operation(self, name: str, operation: Callable, *args, **kwargs) -> Any:
        """Run operation and measure performance.

        Args:
            name: Operation name
            operation: Callable to measure
            args: Operation arguments
            kwargs: Operation keyword arguments

        Returns:
            Operation result
        """
        with PerformanceBenchmark(name) as bench:
            result = operation(*args, **kwargs)

        self.results.extend(bench.results)
        return result

    @staticmethod
    def _get_memory_usage() -> int:
        """Get current process memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get benchmark statistics.

        Returns:
            Statistics dictionary
        """
        if not self.results:
            return {}

        times = [r["elapsed_ms"] for r in self.results]
        memories = [r["memory_delta_kb"] for r in self.results if r["memory_delta_kb"]]

        return {
            "count": len(self.results),
            "total_time_ms": sum(times),
            "avg_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "avg_memory_delta_kb": sum(memories) / len(memories) if memories else 0,
            "errors": len([r for r in self.results if r["error"]]),
        }

    def print_report(self) -> None:
        """Print benchmark report."""
        stats = self.get_stats()

        print("\n" + "=" * 70)
        print(f"Performance Benchmark Report: {self.name}")
        print("=" * 70)

        if not stats:
            print("No results to report.")
            return

        print(f"Operations executed: {stats['count']}")
        print(f"Total time: {stats['total_time_ms']:.2f}ms")
        print(f"Average time: {stats['avg_time_ms']:.2f}ms")
        print(f"Min time: {stats['min_time_ms']:.2f}ms")
        print(f"Max time: {stats['max_time_ms']:.2f}ms")
        print(f"Average memory change: {stats['avg_memory_delta_kb']:.2f}KB")

        if stats["errors"] > 0:
            print(f"Errors: {stats['errors']}")

        print("\nDetailed Results:")
        for result in self.results:
            status = "OK" if not result["error"] else "ERROR"
            print(
                f"  [{status}] {result['name']}: {result['elapsed_ms']:.2f}ms "
                f"(+{result['memory_delta_kb']:.1f}KB)"
            )

        print("=" * 70 + "\n")


def benchmark_query_performance(session, query_func: Callable, runs: int = 10) -> Dict[str, Any]:
    """Benchmark query performance.

    Args:
        session: Database session
        query_func: Query function to benchmark
        runs: Number of runs

    Returns:
        Benchmark results
    """
    bench = PerformanceBenchmark("Query Performance")
    times = []

    for i in range(runs):
        with PerformanceBenchmark(f"Run {i+1}"):
            result = query_func(session)

        times.append(bench.results[-1]["elapsed_ms"])

    return {
        "total_runs": runs,
        "total_time_ms": sum(times),
        "avg_time_ms": sum(times) / len(times),
        "min_time_ms": min(times),
        "max_time_ms": max(times),
        "std_dev_ms": _calculate_std_dev(times),
    }


def benchmark_cache_effectiveness(
    session, cached_func: Callable, non_cached_func: Callable, runs: int = 10
) -> Dict[str, Any]:
    """Benchmark cache effectiveness by comparing cached vs non-cached.

    Args:
        session: Database session
        cached_func: Cached version of function
        non_cached_func: Non-cached version of function
        runs: Number of runs

    Returns:
        Comparison results
    """
    # Benchmark non-cached
    bench_non_cached = PerformanceBenchmark("Non-Cached Queries")
    for i in range(runs):
        with PerformanceBenchmark(f"Non-Cached Run {i+1}"):
            non_cached_func(session)

    # Benchmark cached
    bench_cached = PerformanceBenchmark("Cached Queries")
    for i in range(runs):
        with PerformanceBenchmark(f"Cached Run {i+1}"):
            cached_func(session)

    stats_non_cached = bench_non_cached.get_stats()
    stats_cached = bench_cached.get_stats()

    improvement = (
        (stats_non_cached["avg_time_ms"] - stats_cached["avg_time_ms"])
        / stats_non_cached["avg_time_ms"]
        * 100
    )

    return {
        "non_cached_avg_ms": stats_non_cached["avg_time_ms"],
        "cached_avg_ms": stats_cached["avg_time_ms"],
        "improvement_percent": improvement,
        "speedup_factor": stats_non_cached["avg_time_ms"] / stats_cached["avg_time_ms"],
    }


def benchmark_batch_processing(
    batch_func: Callable, data_sizes: List[int]
) -> Dict[int, Dict[str, float]]:
    """Benchmark batch processing with different data sizes.

    Args:
        batch_func: Batch processing function
        data_sizes: List of data sizes to test

    Returns:
        Results by data size
    """
    results = {}

    for size in data_sizes:
        with PerformanceBenchmark(f"Batch Size {size}") as bench:
            batch_func(size)

        stats = bench.get_stats()
        results[size] = {
            "total_time_ms": stats["total_time_ms"],
            "avg_per_item_ms": stats["total_time_ms"] / size if size > 0 else 0,
            "throughput_items_per_sec": (size / stats["total_time_ms"] * 1000) if stats["total_time_ms"] > 0 else 0,
        }

    return results


def _calculate_std_dev(values: List[float]) -> float:
    """Calculate standard deviation.

    Args:
        values: List of values

    Returns:
        Standard deviation
    """
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


class PerformanceReport:
    """Generate performance reports."""

    @staticmethod
    def generate_html_report(
        benchmarks: Dict[str, Dict[str, Any]], output_file: str = "performance_report.html"
    ) -> None:
        """Generate HTML performance report.

        Args:
            benchmarks: Dictionary of benchmark results
            output_file: Output HTML file path
        """
        html_content = """
        <html>
        <head>
            <title>Performance Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .improvement { color: green; font-weight: bold; }
                .warning { color: orange; }
            </style>
        </head>
        <body>
            <h1>Performance Report</h1>
            <p>Generated: {timestamp}</p>
        """.format(timestamp=datetime.now().isoformat())

        for name, data in benchmarks.items():
            html_content += f"<h2>{name}</h2>"
            html_content += "<table>"
            html_content += "<tr><th>Metric</th><th>Value</th></tr>"

            for key, value in data.items():
                if isinstance(value, float):
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)

                html_content += f"<tr><td>{key}</td><td>{formatted_value}</td></tr>"

            html_content += "</table>"

        html_content += """
        </body>
        </html>
        """

        with open(output_file, "w") as f:
            f.write(html_content)

        logger.info(f"Performance report saved to {output_file}")
