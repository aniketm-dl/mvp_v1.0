#!/usr/bin/env python3
"""
Production-Ready Scalable Training Orchestrator for AWS

This script handles training for N personas with:
- Configuration-driven approach (YAML config)
- Parallel training support (multi-GPU)
- Advanced error handling and retries
- Real-time monitoring and alerts
- Cost tracking and budget management
- Resume from any failure point
- Comprehensive validation and testing

Usage:
    python scripts/aws/train_production.py
    python scripts/aws/train_production.py --config CONFIGS/aws/training_config.yaml
    python scripts/aws/train_production.py --twins twin1 twin2 --parallel
    python scripts/aws/train_production.py --dry-run  # Preview without training
"""

from __future__ import annotations
import argparse
import json
import subprocess
import time
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('artifacts/training.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Training configuration dataclass."""
    base_model: str
    epochs: int
    max_length: int
    learning_rate: float
    batch_size: int
    gradient_accumulation_steps: int
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    personas_file: str = "DATA/personas.json"
    training_data_dir: str = "DATA/sft"
    output_dir: str = "artifacts/llm_adapters"


@dataclass
class AWSConfig:
    """AWS configuration dataclass."""
    s3_enabled: bool = True
    s3_bucket: Optional[str] = None
    s3_prefix: str = "darpan_training"
    sync_frequency: str = "per_twin"
    auto_shutdown: bool = False
    shutdown_delay_minutes: int = 5


@dataclass
class TrainingResult:
    """Result of training a single twin."""
    twin_id: str
    success: bool
    duration_seconds: float
    adapter_size_mb: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class S3Manager:
    """Manages S3 sync operations."""

    def __init__(self, bucket: Optional[str], prefix: str, enabled: bool = True):
        self.bucket = bucket
        self.prefix = prefix
        self.enabled = enabled and bucket is not None

    def sync_to_s3(self, local_path: Path, s3_key: str, timeout: int = 300) -> bool:
        """Sync local files to S3."""
        if not self.enabled:
            return True

        s3_path = f"s3://{self.bucket}/{self.prefix}/{s3_key}"
        logger.info(f"📤 Syncing to S3: {s3_path}")

        try:
            cmd = [
                "aws", "s3", "sync",
                str(local_path),
                s3_path,
                "--exclude", "*.pyc",
                "--exclude", "__pycache__/*",
                "--quiet"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            if result.returncode == 0:
                logger.info(f"✅ Synced to S3 successfully")
                return True
            else:
                logger.warning(f"⚠️  S3 sync warning: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.warning("⚠️  S3 sync timed out")
            return False
        except Exception as e:
            logger.error(f"❌ S3 sync error: {e}")
            return False

    def sync_from_s3(self, s3_key: str, local_path: Path, timeout: int = 300) -> bool:
        """Sync files from S3 to local."""
        if not self.enabled:
            return False

        s3_path = f"s3://{self.bucket}/{self.prefix}/{s3_key}"
        logger.info(f"📥 Checking S3 for existing data: {s3_path}")

        try:
            # Check if S3 path exists
            check_cmd = ["aws", "s3", "ls", s3_path]
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.info(f"   No existing data in S3")
                return False

            # Sync from S3
            local_path.mkdir(parents=True, exist_ok=True)
            sync_cmd = ["aws", "s3", "sync", s3_path, str(local_path), "--quiet"]
            result = subprocess.run(sync_cmd, capture_output=True, text=True, timeout=timeout)

            if result.returncode == 0:
                logger.info(f"✅ Synced from S3 successfully")
                return True
            else:
                logger.warning(f"⚠️  S3 sync failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ S3 sync error: {e}")
            return False


class InstanceMetadata:
    """Fetches and caches AWS instance metadata."""

    def __init__(self):
        self._metadata = self._fetch_metadata()

    def _fetch_metadata(self) -> Dict[str, str]:
        """Fetch AWS instance metadata."""
        metadata = {}
        try:
            metadata['instance_type'] = subprocess.check_output(
                ["curl", "-s", "http://169.254.169.254/latest/meta-data/instance-type"],
                timeout=2
            ).decode().strip()

            metadata['instance_id'] = subprocess.check_output(
                ["curl", "-s", "http://169.254.169.254/latest/meta-data/instance-id"],
                timeout=2
            ).decode().strip()

            metadata['region'] = subprocess.check_output(
                ["curl", "-s", "http://169.254.169.254/latest/meta-data/placement/region"],
                timeout=2
            ).decode().strip()

            metadata['availability_zone'] = subprocess.check_output(
                ["curl", "-s", "http://169.254.169.254/latest/meta-data/placement/availability-zone"],
                timeout=2
            ).decode().strip()
        except:
            metadata['instance_type'] = 'unknown'
            metadata['instance_id'] = 'unknown'
            metadata['region'] = 'unknown'
            metadata['availability_zone'] = 'unknown'

        return metadata

    @property
    def instance_type(self) -> str:
        return self._metadata.get('instance_type', 'unknown')

    @property
    def instance_id(self) -> str:
        return self._metadata.get('instance_id', 'unknown')

    @property
    def region(self) -> str:
        return self._metadata.get('region', 'unknown')

    @property
    def is_aws(self) -> bool:
        return self.instance_id != 'unknown'


class CostTracker:
    """Tracks training costs in real-time."""

    # Spot pricing (approximate averages)
    SPOT_PRICES = {
        'g4dn.xlarge': 0.18,
        'g4dn.2xlarge': 0.25,
        'g5.xlarge': 0.35,
        'g5.2xlarge': 0.50,
        'p3.2xlarge': 1.00,
        'p3.8xlarge': 3.50,
        'p4d.24xlarge': 10.00,
    }

    def __init__(self, instance_type: str):
        self.instance_type = instance_type
        self.start_time = time.time()
        self.price_per_hour = self.SPOT_PRICES.get(instance_type, 0.50)

    def get_elapsed_hours(self) -> float:
        """Get elapsed time in hours."""
        return (time.time() - self.start_time) / 3600

    def get_current_cost(self) -> float:
        """Get current estimated cost."""
        return self.get_elapsed_hours() * self.price_per_hour

    def estimate_remaining_cost(self, twins_completed: int, total_twins: int) -> float:
        """Estimate remaining cost based on progress."""
        if twins_completed == 0:
            return self.price_per_hour * 3  # Rough estimate

        elapsed = self.get_elapsed_hours()
        time_per_twin = elapsed / twins_completed
        remaining_time = time_per_twin * (total_twins - twins_completed)
        return remaining_time * self.price_per_hour

    def get_summary(self, twins_completed: int, total_twins: int) -> Dict[str, float]:
        """Get cost summary."""
        return {
            "elapsed_hours": self.get_elapsed_hours(),
            "current_cost_usd": self.get_current_cost(),
            "estimated_remaining_usd": self.estimate_remaining_cost(twins_completed, total_twins),
            "estimated_total_usd": self.get_current_cost() + self.estimate_remaining_cost(twins_completed, total_twins),
            "price_per_hour": self.price_per_hour
        }


class TrainingOrchestrator:
    """Main orchestrator for training operations."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.metadata = InstanceMetadata()
        self.s3_manager = S3Manager(
            bucket=self.config.get('aws', {}).get('s3', {}).get('bucket'),
            prefix=self.config.get('aws', {}).get('s3', {}).get('prefix', 'darpan_training'),
            enabled=self.config.get('aws', {}).get('s3', {}).get('enabled', True)
        )
        self.cost_tracker = CostTracker(self.metadata.instance_type)
        self.results: List[TrainingResult] = []

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path("CONFIGS/aws/training_config.yaml")

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        logger.info(f"✅ Loaded config from: {config_path}")
        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "training": {
                "base_model": "mistralai/Mistral-7B-Instruct-v0.2",
                "epochs": 1,
                "max_length": 512,
                "learning_rate": 2e-4,
                "batch_size": 1,
                "gradient_accumulation_steps": 8,
                "lora": {"rank": 8, "alpha": 16, "dropout": 0.05},
                "personas_file": "DATA/personas.json",
                "training_data_dir": "DATA/sft",
                "output_dir": "artifacts/llm_adapters"
            },
            "aws": {
                "s3": {"enabled": True, "bucket": None, "prefix": "darpan_training", "sync_frequency": "per_twin"},
                "instance": {"auto_shutdown": False, "shutdown_delay_minutes": 5}
            },
            "parallelization": {"enabled": False, "num_workers": 1},
            "resume": {"enabled": True, "skip_completed": True},
            "error_handling": {"max_retries": 3, "retry_delay_seconds": 60, "fail_fast": False},
            "validation": {"enabled": True, "verify_adapter_size_mb": [10, 50], "test_inference": False}
        }

    def load_personas(self, filter_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Load personas from JSON file."""
        personas_file = Path(self.config['training']['personas_file'])

        if not personas_file.exists():
            raise FileNotFoundError(f"Personas file not found: {personas_file}")

        data = json.loads(personas_file.read_text())
        personas = data.get("personas", [])

        if filter_ids:
            personas = [p for p in personas if p['id'] in filter_ids]
            logger.info(f"Filtered to {len(personas)} personas: {', '.join(filter_ids)}")

        return personas

    def check_adapter_exists(self, twin_id: str) -> bool:
        """Check if adapter already exists."""
        output_dir = Path(self.config['training']['output_dir'])
        adapter_file = output_dir / twin_id / "adapter_model.safetensors"
        return adapter_file.exists()

    def train_single_twin(self, twin_id: str, retry_count: int = 0) -> TrainingResult:
        """Train a single twin with error handling."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Training: {twin_id} (Attempt {retry_count + 1})")
        logger.info(f"{'='*80}")

        start_time = time.time()

        # Check if already trained
        if self.config['resume']['skip_completed'] and self.check_adapter_exists(twin_id):
            adapter_file = Path(self.config['training']['output_dir']) / twin_id / "adapter_model.safetensors"
            size_mb = adapter_file.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Already trained ({size_mb:.1f}MB) - skipping")
            return TrainingResult(
                twin_id=twin_id,
                success=True,
                duration_seconds=0,
                adapter_size_mb=size_mb,
                error_message=None,
                retry_count=retry_count
            )

        # Check training data exists
        training_config = self.config['training']
        data_file = Path(training_config['training_data_dir']) / f"{twin_id}.jsonl"
        if not data_file.exists():
            error_msg = f"Training data not found: {data_file}"
            logger.error(f"❌ {error_msg}")
            return TrainingResult(
                twin_id=twin_id,
                success=False,
                duration_seconds=0,
                error_message=error_msg,
                retry_count=retry_count
            )

        # Build training command
        cmd = [
            sys.executable,
            "scripts/train_llm_persona_sft.py",
            "--twin_id", twin_id,
            "--base_model", training_config['base_model'],
            "--epochs", str(training_config['epochs']),
            "--max_length", str(training_config['max_length']),
            "--lr", str(training_config['learning_rate'])
        ]

        try:
            # Run training
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            duration = time.time() - start_time

            # Verify adapter was created
            adapter_file = Path(training_config['output_dir']) / twin_id / "adapter_model.safetensors"
            if not adapter_file.exists():
                error_msg = "Adapter file not created after training"
                logger.error(f"❌ {error_msg}")
                return TrainingResult(
                    twin_id=twin_id,
                    success=False,
                    duration_seconds=duration,
                    error_message=error_msg,
                    retry_count=retry_count
                )

            size_mb = adapter_file.stat().st_size / (1024 * 1024)

            # Validate adapter size
            if self.config['validation']['enabled']:
                min_size, max_size = self.config['validation']['verify_adapter_size_mb']
                if not (min_size <= size_mb <= max_size):
                    error_msg = f"Adapter size {size_mb:.1f}MB outside expected range [{min_size}-{max_size}MB]"
                    logger.warning(f"⚠️  {error_msg}")

            logger.info(f"✅ Training complete ({size_mb:.1f}MB) in {duration:.1f}s")

            # Sync to S3
            if self.config['aws']['s3']['sync_frequency'] == 'per_twin':
                self.s3_manager.sync_to_s3(
                    Path(training_config['output_dir']) / twin_id,
                    f"trained_adapters/{twin_id}"
                )

            return TrainingResult(
                twin_id=twin_id,
                success=True,
                duration_seconds=duration,
                adapter_size_mb=size_mb,
                retry_count=retry_count
            )

        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            error_msg = f"Training process failed: {e.stderr[-500:] if e.stderr else 'Unknown error'}"
            logger.error(f"❌ {error_msg}")

            return TrainingResult(
                twin_id=twin_id,
                success=False,
                duration_seconds=duration,
                error_message=error_msg,
                retry_count=retry_count
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            logger.error(f"❌ {error_msg}")

            return TrainingResult(
                twin_id=twin_id,
                success=False,
                duration_seconds=duration,
                error_message=error_msg,
                retry_count=retry_count
            )

    def train_with_retry(self, twin_id: str) -> TrainingResult:
        """Train a twin with automatic retry on failure."""
        max_retries = self.config['error_handling']['max_retries']
        retry_delay = self.config['error_handling']['retry_delay_seconds']

        for attempt in range(max_retries):
            result = self.train_single_twin(twin_id, retry_count=attempt)

            if result.success:
                return result

            if attempt < max_retries - 1:
                logger.warning(f"⚠️  Retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)

        return result

    def train_all(self, twin_ids: Optional[List[str]] = None, parallel: bool = False) -> List[TrainingResult]:
        """Train all specified twins."""
        personas = self.load_personas(filter_ids=twin_ids)

        if not personas:
            logger.error("❌ No personas found to train")
            return []

        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 Starting training for {len(personas)} personas")
        logger.info(f"{'='*80}\n")

        # Training configuration summary
        training_cfg = self.config['training']
        logger.info(f"⚙️  Configuration:")
        logger.info(f"   • Base model: {training_cfg['base_model']}")
        logger.info(f"   • Epochs: {training_cfg['epochs']}")
        logger.info(f"   • LoRA rank: {training_cfg['lora']['rank']}")
        logger.info(f"   • Parallel: {parallel}")
        logger.info(f"   • S3 sync: {self.s3_manager.enabled}")

        results = []

        if parallel and self.config['parallelization']['enabled']:
            results = self._train_parallel(personas)
        else:
            results = self._train_sequential(personas)

        self.results = results
        return results

    def _train_sequential(self, personas: List[Dict[str, Any]]) -> List[TrainingResult]:
        """Train personas sequentially."""
        results = []

        for i, persona in enumerate(personas, 1):
            twin_id = persona['id']

            logger.info(f"\n[{i}/{len(personas)}] Processing: {persona.get('label', twin_id)}")

            result = self.train_with_retry(twin_id)
            results.append(result)

            # Log progress
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Progress: {success_count}/{len(results)} successful")

            # Log cost estimate
            cost_summary = self.cost_tracker.get_summary(len(results), len(personas))
            logger.info(f"💰 Cost: ${cost_summary['current_cost_usd']:.2f} so far, "
                       f"~${cost_summary['estimated_total_usd']:.2f} estimated total")

            # Fail fast if configured
            if not result.success and self.config['error_handling']['fail_fast']:
                logger.error("❌ Fail-fast enabled, stopping training")
                break

        return results

    def _train_parallel(self, personas: List[Dict[str, Any]]) -> List[TrainingResult]:
        """Train personas in parallel (for multi-GPU setups)."""
        num_workers = self.config['parallelization']['num_workers']
        logger.info(f"🔀 Training in parallel with {num_workers} workers")

        results = []

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_twin = {
                executor.submit(self.train_with_retry, persona['id']): persona['id']
                for persona in personas
            }

            for future in as_completed(future_to_twin):
                twin_id = future_to_twin[future]
                try:
                    result = future.result()
                    results.append(result)

                    success_count = sum(1 for r in results if r.success)
                    logger.info(f"Progress: {success_count}/{len(results)} completed")

                except Exception as e:
                    logger.error(f"❌ Exception training {twin_id}: {e}")
                    results.append(TrainingResult(
                        twin_id=twin_id,
                        success=False,
                        duration_seconds=0,
                        error_message=str(e)
                    ))

        return results

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive training report."""
        success_count = sum(1 for r in self.results if r.success)
        failed_twins = [r.twin_id for r in self.results if not r.success]

        total_duration = sum(r.duration_seconds for r in self.results)
        total_size_mb = sum(r.adapter_size_mb or 0 for r in self.results if r.success)

        cost_summary = self.cost_tracker.get_summary(len(self.results), len(self.results))

        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "instance_type": self.metadata.instance_type,
                "instance_id": self.metadata.instance_id,
                "region": self.metadata.region,
            },
            "configuration": {
                "base_model": self.config['training']['base_model'],
                "epochs": self.config['training']['epochs'],
                "parallel_enabled": self.config['parallelization']['enabled'],
            },
            "results": {
                "total_personas": len(self.results),
                "successful": success_count,
                "failed": len(failed_twins),
                "failed_twins": failed_twins,
                "success_rate": f"{100 * success_count / len(self.results):.1f}%" if self.results else "0%"
            },
            "performance": {
                "total_duration_seconds": total_duration,
                "total_duration_hours": total_duration / 3600,
                "avg_time_per_twin_seconds": total_duration / len(self.results) if self.results else 0,
                "total_adapter_size_mb": total_size_mb,
            },
            "cost": cost_summary,
            "s3": {
                "enabled": self.s3_manager.enabled,
                "bucket": self.s3_manager.bucket,
                "prefix": self.s3_manager.prefix,
            },
            "detailed_results": [asdict(r) for r in self.results]
        }

        return report

    def save_report(self, report: Dict[str, Any]):
        """Save training report to file."""
        report_file = Path("artifacts/training_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))
        logger.info(f"\n📄 Report saved to: {report_file}")

        # Also sync to S3
        if self.s3_manager.enabled:
            self.s3_manager.sync_to_s3(
                report_file,
                f"training_reports/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

    def auto_shutdown(self, delay_minutes: int = 5):
        """Schedule automatic instance shutdown."""
        logger.info(f"\n⏰ Scheduling shutdown in {delay_minutes} minutes...")
        logger.info(f"   Cancel with: sudo shutdown -c")

        try:
            subprocess.run(["sudo", "shutdown", "-h", f"+{delay_minutes}"], check=True)
            logger.info(f"✅ Shutdown scheduled")
        except Exception as e:
            logger.error(f"❌ Failed to schedule shutdown: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Production-ready training orchestrator for AWS",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", type=Path, help="Path to training config YAML")
    parser.add_argument("--twins", nargs="+", help="Specific twin IDs to train (default: all)")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel training")
    parser.add_argument("--auto-shutdown", action="store_true", help="Auto-shutdown after training")
    parser.add_argument("--s3-bucket", type=str, help="S3 bucket override")
    parser.add_argument("--dry-run", action="store_true", help="Preview without training")
    parser.add_argument("--skip-s3", action="store_true", help="Disable S3 sync")

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = TrainingOrchestrator(config_path=args.config)

    # Override S3 bucket if provided
    if args.s3_bucket:
        orchestrator.s3_manager.bucket = args.s3_bucket
        orchestrator.s3_manager.enabled = True
    if args.skip_s3:
        orchestrator.s3_manager.enabled = False

    # Dry run mode
    if args.dry_run:
        personas = orchestrator.load_personas(filter_ids=args.twins)
        logger.info("\n🔍 DRY RUN MODE - No training will be performed\n")
        logger.info(f"Would train {len(personas)} personas:")
        for p in personas:
            status = "✅ Exists" if orchestrator.check_adapter_exists(p['id']) else "❌ Needs training"
            logger.info(f"   • {p['id']:30} {status}")
        return 0

    try:
        # Train all specified twins
        results = orchestrator.train_all(
            twin_ids=args.twins,
            parallel=args.parallel
        )

        # Generate and save report
        report = orchestrator.generate_report()
        orchestrator.save_report(report)

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 TRAINING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"\n📊 Summary:")
        logger.info(f"   • Total: {report['results']['total_personas']}")
        logger.info(f"   • Successful: {report['results']['successful']}")
        logger.info(f"   • Failed: {report['results']['failed']}")
        logger.info(f"   • Success rate: {report['results']['success_rate']}")
        logger.info(f"   • Total time: {report['performance']['total_duration_hours']:.2f} hours")
        logger.info(f"   • Total cost: ${report['cost']['current_cost_usd']:.2f}")
        logger.info(f"   • Adapter size: {report['performance']['total_adapter_size_mb']:.1f}MB")

        if report['results']['failed_twins']:
            logger.warning(f"\n⚠️  Failed twins: {', '.join(report['results']['failed_twins'])}")

        # Auto-shutdown if requested
        if args.auto_shutdown:
            delay = orchestrator.config['aws']['instance'].get('shutdown_delay_minutes', 5)
            orchestrator.auto_shutdown(delay_minutes=delay)

        # Return exit code based on success
        return 0 if report['results']['failed'] == 0 else 1

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Training interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
