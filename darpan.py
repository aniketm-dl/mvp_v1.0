#!/usr/bin/env python3
"""
Darpan Labs - Unified CLI for AWS Training Workflow

Complete automation: Launch → Setup → Train → Download → Chat

Usage:
    ./darpan.py workflow          # Run complete workflow
    ./darpan.py launch            # Launch AWS instance
    ./darpan.py setup             # Setup instance (run on EC2)
    ./darpan.py train             # Train models (run on EC2)
    ./darpan.py download          # Download trained models
    ./darpan.py chat              # Interactive chat with personas
    ./darpan.py status            # Check workflow status
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional


class Colors:
    """Terminal colors for better UX."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


class WorkflowState:
    """Manage workflow state across steps."""

    STATE_FILE = Path.home() / ".darpan_workflow_state.json"

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load workflow state."""
        if cls.STATE_FILE.exists():
            return json.loads(cls.STATE_FILE.read_text())
        return {}

    @classmethod
    def save(cls, state: Dict[str, Any]):
        """Save workflow state."""
        cls.STATE_FILE.write_text(json.dumps(state, indent=2))

    @classmethod
    def update(cls, **kwargs):
        """Update specific state fields."""
        state = cls.load()
        state.update(kwargs)
        cls.save(state)

    @classmethod
    def get(cls, key: str, default=None):
        """Get specific state field."""
        return cls.load().get(key, default)


class DarpanCLI:
    """Unified CLI for Darpan Labs workflow."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.aws_scripts = self.project_root / "scripts" / "aws"

    def run_workflow(self, args):
        """Run complete automated workflow."""
        print_header("🚀 DARPAN LABS - COMPLETE WORKFLOW")
        print("This will guide you through the entire process:")
        print("  1. Launch AWS GPU instance")
        print("  2. Setup environment on instance")
        print("  3. Train all persona models")
        print("  4. Download trained models")
        print("  5. Interactive chat with personas")
        print()

        # Check prerequisites
        if not self._check_prerequisites():
            return 1

        # Step 1: Launch
        print_info("Step 1/5: Launching AWS instance...")
        if self.launch(args) != 0:
            print_error("Failed to launch instance")
            return 1

        # Step 2: Setup
        print_info("Step 2/5: Setting up instance...")
        print_warning("Please SSH into your instance and run: ./darpan.py setup")
        print_warning("Then come back and run: ./darpan.py workflow --resume")

        if not args.auto:
            input("\nPress Enter when setup is complete...")

        # Step 3: Train
        print_info("Step 3/5: Training models...")
        print_warning("On your instance, run: ./darpan.py train --auto-shutdown")

        if not args.auto:
            input("\nPress Enter when training is complete...")

        # Step 4: Download
        print_info("Step 4/5: Downloading models...")
        if self.download(args) != 0:
            print_error("Failed to download models")
            return 1

        # Step 5: Chat
        print_info("Step 5/5: Starting interactive chat...")
        return self.chat(args)

    def launch(self, args) -> int:
        """Launch AWS GPU instance."""
        print_header("📡 LAUNCHING AWS INSTANCE")

        script = self.aws_scripts / "launch_training_instance.sh"
        if not script.exists():
            print_error(f"Launch script not found: {script}")
            return 1

        try:
            result = subprocess.run(
                [str(script)],
                cwd=str(self.project_root)
            )

            if result.returncode == 0:
                print_success("Instance launched successfully!")
                return 0
            else:
                print_error("Failed to launch instance")
                return 1

        except Exception as e:
            print_error(f"Error launching instance: {e}")
            return 1

    def setup(self, args) -> int:
        """Setup environment on EC2 instance (run on instance)."""
        print_header("⚙️  SETTING UP INSTANCE")

        script = self.aws_scripts / "setup_training_instance.sh"
        if not script.exists():
            print_error(f"Setup script not found: {script}")
            return 1

        try:
            result = subprocess.run(
                [str(script)],
                cwd=str(self.project_root)
            )

            if result.returncode == 0:
                print_success("Instance setup complete!")
                WorkflowState.update(setup_complete=True)
                return 0
            else:
                print_error("Setup failed")
                return 1

        except Exception as e:
            print_error(f"Error during setup: {e}")
            return 1

    def train(self, args) -> int:
        """Train all persona models (run on EC2 instance)."""
        print_header("🎓 TRAINING PERSONA MODELS")

        # Use production training script
        script = self.aws_scripts / "train_production.py"
        if not script.exists():
            # Fallback to simpler script
            script = self.aws_scripts / "train_with_s3_sync.py"

        if not script.exists():
            print_error(f"Training script not found")
            return 1

        cmd = [sys.executable, str(script)]

        if args.auto_shutdown:
            cmd.append("--auto-shutdown")

        if args.twins:
            cmd.extend(["--twins"] + args.twins)

        if args.parallel:
            cmd.append("--parallel")

        try:
            result = subprocess.run(cmd, cwd=str(self.project_root))

            if result.returncode == 0:
                print_success("Training complete!")
                WorkflowState.update(training_complete=True)
                return 0
            else:
                print_error("Training failed")
                return 1

        except Exception as e:
            print_error(f"Error during training: {e}")
            return 1

    def download(self, args) -> int:
        """Download trained models from S3."""
        print_header("📥 DOWNLOADING TRAINED MODELS")

        s3_bucket = WorkflowState.get("s3_bucket") or os.environ.get("TRAINING_S3_BUCKET")

        if not s3_bucket:
            print_warning("No S3 bucket configured")
            s3_bucket = input("Enter S3 bucket name: ").strip()
            if not s3_bucket:
                print_error("S3 bucket required")
                return 1
            WorkflowState.update(s3_bucket=s3_bucket)

        local_path = self.project_root / "artifacts" / "llm_adapters"
        local_path.mkdir(parents=True, exist_ok=True)

        print_info(f"Downloading from s3://{s3_bucket}/trained_adapters/")
        print_info(f"To: {local_path}")

        try:
            cmd = [
                "aws", "s3", "sync",
                f"s3://{s3_bucket}/trained_adapters/",
                str(local_path),
                "--exclude", "*.pyc",
                "--exclude", "__pycache__/*"
            ]

            result = subprocess.run(cmd)

            if result.returncode == 0:
                # Verify downloads
                adapter_count = len(list(local_path.glob("*/adapter_model.safetensors")))
                print_success(f"Downloaded {adapter_count} adapters successfully!")
                WorkflowState.update(download_complete=True, adapter_count=adapter_count)
                return 0
            else:
                print_error("Download failed")
                return 1

        except Exception as e:
            print_error(f"Error downloading: {e}")
            return 1

    def chat(self, args) -> int:
        """Interactive chat with trained personas."""
        print_header("💬 INTERACTIVE CHAT")

        # Check if adapters exist
        adapter_dir = self.project_root / "artifacts" / "llm_adapters"
        if not adapter_dir.exists() or not list(adapter_dir.glob("*/adapter_model.safetensors")):
            print_error("No trained adapters found!")
            print_info("Run './darpan.py download' first to get trained models")
            return 1

        # Run interactive CLI
        cli_script = self.project_root / "interact_cli.py"
        if not cli_script.exists():
            print_error(f"Chat interface not found: {cli_script}")
            return 1

        try:
            result = subprocess.run(
                [sys.executable, str(cli_script)],
                cwd=str(self.project_root)
            )
            return result.returncode

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return 0
        except Exception as e:
            print_error(f"Error starting chat: {e}")
            return 1

    def status(self, args) -> int:
        """Show workflow status."""
        print_header("📊 WORKFLOW STATUS")

        state = WorkflowState.load()

        steps = [
            ("Launch", state.get("instance_id")),
            ("Setup", state.get("setup_complete")),
            ("Train", state.get("training_complete")),
            ("Download", state.get("download_complete")),
        ]

        for step_name, completed in steps:
            if completed:
                print_success(f"{step_name}: Complete")
            else:
                print_warning(f"{step_name}: Pending")

        # Additional info
        if state.get("instance_id"):
            print(f"\n Instance ID: {state.get('instance_id')}")
        if state.get("instance_ip"):
            print(f" Instance IP: {state.get('instance_ip')}")
        if state.get("s3_bucket"):
            print(f" S3 Bucket: s3://{state.get('s3_bucket')}/")
        if state.get("adapter_count"):
            print(f" Adapters: {state.get('adapter_count')}/18")

        # Check local adapters
        adapter_dir = self.project_root / "artifacts" / "llm_adapters"
        if adapter_dir.exists():
            local_count = len(list(adapter_dir.glob("*/adapter_model.safetensors")))
            print(f"\n Local adapters: {local_count}")

        print()
        return 0

    def _check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""
        print_info("Checking prerequisites...")

        checks = [
            ("AWS CLI", ["aws", "--version"]),
            ("AWS Credentials", ["aws", "sts", "get-caller-identity"]),
        ]

        all_good = True
        for name, cmd in checks:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print_success(f"{name}: OK")
                else:
                    print_error(f"{name}: Failed")
                    all_good = False
            except Exception as e:
                print_error(f"{name}: Not found")
                all_good = False

        print()
        return all_good


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Darpan Labs - Unified AWS Training Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run complete workflow")
    workflow_parser.add_argument("--auto", action="store_true", help="Auto mode (no pauses)")
    workflow_parser.add_argument("--resume", action="store_true", help="Resume from last step")

    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch AWS instance")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup instance (run on EC2)")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train models (run on EC2)")
    train_parser.add_argument("--auto-shutdown", action="store_true", help="Shutdown after training")
    train_parser.add_argument("--twins", nargs="+", help="Specific twins to train")
    train_parser.add_argument("--parallel", action="store_true", help="Parallel training")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download trained models")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show workflow status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = DarpanCLI()

    # Route to appropriate handler
    handlers = {
        "workflow": cli.run_workflow,
        "launch": cli.launch,
        "setup": cli.setup,
        "train": cli.train,
        "download": cli.download,
        "chat": cli.chat,
        "status": cli.status,
    }

    handler = handlers.get(args.command)
    if handler:
        try:
            return handler(args)
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
            return 130
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
