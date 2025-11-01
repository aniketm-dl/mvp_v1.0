"""
Progress tracking and logging utilities for clustering pipeline.
Provides real-time progress bars, structured logging, and checkpoint management.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
        MofNCompleteColumn,
    )
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    rprint = print


class ClusteringProgressTracker:
    """
    Tracks and displays progress for clustering pipeline with live updates.

    Features:
    - Rich console output with progress bars
    - Structured logging to file
    - Step-by-step tracking
    - Time estimation
    - Checkpointing support
    """

    def __init__(
        self,
        verbosity: str = "verbose",
        show_progress: bool = True,
        log_to_file: bool = True,
        log_file: Optional[str] = None,
    ):
        """
        Initialize progress tracker.

        Args:
            verbosity: One of "quiet", "normal", "verbose", "debug"
            show_progress: Whether to show progress bars
            log_to_file: Whether to log to file
            log_file: Path to log file (optional)
        """
        self.verbosity = verbosity
        self.show_progress = show_progress and RICH_AVAILABLE
        self.log_to_file = log_to_file
        self.log_file = log_file

        self.console = Console() if RICH_AVAILABLE else None
        self.start_time = time.time()
        self.checkpoints: Dict[str, float] = {}
        self.log_entries: List[Dict[str, Any]] = []

        if self.log_to_file and self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w") as f:
                f.write(f"=== Clustering Pipeline Log - {datetime.now().isoformat()} ===\n\n")

    def log(self, message: str, level: str = "info", **kwargs):
        """
        Log a message with optional metadata.

        Args:
            message: Message to log
            level: Log level ("debug", "info", "warning", "error")
            **kwargs: Additional metadata to include
        """
        timestamp = datetime.now().isoformat()
        elapsed = time.time() - self.start_time

        entry = {
            "timestamp": timestamp,
            "elapsed": f"{elapsed:.2f}s",
            "level": level.upper(),
            "message": message,
            **kwargs
        }
        self.log_entries.append(entry)

        # Console output based on verbosity
        should_print = (
            (self.verbosity == "debug") or
            (self.verbosity == "verbose" and level in ["info", "warning", "error"]) or
            (self.verbosity == "normal" and level in ["warning", "error"]) or
            (self.verbosity == "quiet" and level == "error")
        )

        if should_print:
            if RICH_AVAILABLE and self.console:
                color_map = {
                    "debug": "dim",
                    "info": "cyan",
                    "warning": "yellow",
                    "error": "red bold",
                }
                color = color_map.get(level, "white")
                self.console.print(f"[{color}][{level.upper()}][/{color}] {message}")
            else:
                print(f"[{level.upper()}] {message}")

        # File output
        if self.log_to_file and self.log_file:
            with open(self.log_file, "a") as f:
                f.write(f"[{timestamp}] [{level.upper()}] {message}\n")
                if kwargs:
                    for key, value in kwargs.items():
                        f.write(f"  {key}: {value}\n")

    def checkpoint(self, name: str):
        """Mark a checkpoint with timestamp."""
        self.checkpoints[name] = time.time() - self.start_time
        self.log(f"Checkpoint: {name}", level="debug", checkpoint_time=f"{self.checkpoints[name]:.2f}s")

    def print_header(self, title: str, subtitle: Optional[str] = None):
        """Print a formatted header."""
        if RICH_AVAILABLE and self.console:
            panel_content = f"[bold cyan]{title}[/bold cyan]"
            if subtitle:
                panel_content += f"\n[dim]{subtitle}[/dim]"
            self.console.print(Panel(panel_content, expand=False))
        else:
            print(f"\n{'='*60}")
            print(f"  {title}")
            if subtitle:
                print(f"  {subtitle}")
            print(f"{'='*60}\n")

    def print_config(self, config: Dict[str, Any]):
        """Print configuration as a formatted table."""
        if RICH_AVAILABLE and self.console:
            table = Table(title="Clustering Configuration", show_header=True)
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="green")

            for key, value in config.items():
                if isinstance(value, dict):
                    # Flatten nested dicts
                    for sub_key, sub_value in value.items():
                        table.add_row(f"{key}.{sub_key}", str(sub_value))
                else:
                    table.add_row(key, str(value))

            self.console.print(table)
        else:
            print("\n=== Clustering Configuration ===")
            for key, value in config.items():
                print(f"  {key}: {value}")
            print()

    def print_metrics(self, metrics: Dict[str, Any], title: str = "Metrics"):
        """Print metrics as a formatted table."""
        if RICH_AVAILABLE and self.console:
            table = Table(title=title, show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_column("Status", style="bold")

            for key, value in metrics.items():
                # Determine status based on metric thresholds
                status = "✓"
                if "silhouette" in key.lower() and isinstance(value, (int, float)):
                    status = "✓" if value >= 0.35 else "✗"
                elif "jsd" in key.lower() and isinstance(value, (int, float)):
                    status = "✓" if value >= 0.10 else "✗"
                elif "ari" in key.lower() and isinstance(value, (int, float)):
                    status = "✓" if value >= 0.80 else "✗"

                if isinstance(value, float):
                    value_str = f"{value:.4f}"
                else:
                    value_str = str(value)

                table.add_row(key, value_str, status)

            self.console.print(table)
        else:
            print(f"\n=== {title} ===")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
            print()

    @contextmanager
    def progress_bar(self, total: int, description: str = "Processing"):
        """
        Context manager for progress bar.

        Usage:
            with tracker.progress_bar(100, "Loading data") as update:
                for i in range(100):
                    # do work
                    update(1)  # Increment by 1
        """
        if self.show_progress and RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=self.console,
            ) as progress:
                task = progress.add_task(description, total=total)

                def update(amount: int = 1):
                    progress.update(task, advance=amount)

                yield update
        else:
            # Fallback for no rich or disabled progress
            current = [0]  # Use list to allow mutation in nested function

            def update(amount: int = 1):
                current[0] += amount
                if current[0] % max(1, total // 20) == 0 or current[0] == total:
                    percent = (current[0] / total) * 100
                    print(f"{description}: {current[0]}/{total} ({percent:.1f}%)")

            yield update

    def print_summary(self):
        """Print a summary of the clustering run."""
        total_time = time.time() - self.start_time

        if RICH_AVAILABLE and self.console:
            self.console.print("\n[bold green]✓ Clustering Complete![/bold green]")
            self.console.print(f"Total time: [cyan]{total_time:.2f}s[/cyan]")

            if self.checkpoints:
                table = Table(title="Checkpoint Times", show_header=True)
                table.add_column("Checkpoint", style="cyan")
                table.add_column("Time", style="green")

                for name, elapsed in self.checkpoints.items():
                    table.add_row(name, f"{elapsed:.2f}s")

                self.console.print(table)
        else:
            print(f"\n✓ Clustering Complete! Total time: {total_time:.2f}s")

            if self.checkpoints:
                print("\n=== Checkpoint Times ===")
                for name, elapsed in self.checkpoints.items():
                    print(f"  {name}: {elapsed:.2f}s")

    def save_log(self, output_path: Optional[str] = None):
        """Save log entries to JSON file."""
        import json

        output_path = output_path or self.log_file.replace(".log", "_structured.json")

        log_data = {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration": time.time() - self.start_time,
            "checkpoints": self.checkpoints,
            "entries": self.log_entries,
        }

        with open(output_path, "w") as f:
            json.dump(log_data, f, indent=2)

        self.log(f"Structured log saved to {output_path}", level="info")


def create_tracker(config: Dict[str, Any]) -> ClusteringProgressTracker:
    """
    Create a progress tracker from configuration.

    Args:
        config: Configuration dict with verbosity, show_progress, log_to_file, log_file

    Returns:
        Configured ClusteringProgressTracker instance
    """
    return ClusteringProgressTracker(
        verbosity=config.get("verbosity", "verbose"),
        show_progress=config.get("show_progress", True),
        log_to_file=config.get("log_to_file", True),
        log_file=config.get("log_file"),
    )


if __name__ == "__main__":
    # Demo usage
    tracker = ClusteringProgressTracker(verbosity="verbose", show_progress=True, log_to_file=False)

    tracker.print_header("Clustering Pipeline Demo", "Testing progress tracking")

    tracker.print_config({
        "n_clusters": 10,
        "method": "kmeans",
        "seed": 42,
    })

    tracker.log("Starting data loading...", level="info")
    tracker.checkpoint("data_loaded")

    with tracker.progress_bar(100, "Processing data") as update:
        for i in range(100):
            time.sleep(0.01)
            update(1)

    tracker.log("Data processing complete", level="info")
    tracker.checkpoint("processing_done")

    tracker.print_metrics({
        "silhouette_score": 0.42,
        "mean_jsd": 0.15,
        "ari": 0.85,
    })

    tracker.print_summary()
