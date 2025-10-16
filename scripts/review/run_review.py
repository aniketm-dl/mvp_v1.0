#!/usr/bin/env python3
"""
Code Review Orchestration Script

Runs comprehensive code review using multiple static analysis tools.
Generates reports, patches, and summaries.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Result from a tool execution"""
    tool_name: str
    success: bool
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    findings_count: int = 0

@dataclass
class ReviewConfig:
    """Configuration for code review"""
    tools: Dict[str, Any]
    patterns: Dict[str, List[str]]
    thresholds: Dict[str, Any]
    timeouts: Dict[str, int]
    severity: Dict[str, List[str]]
    ml_checks: Dict[str, Any]
    report: Dict[str, Any]

class CodeReviewRunner:
    """Main code review orchestrator"""
    
    def __init__(self, config_path: str, output_dir: str):
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.config = self._load_config()
        self.results: List[ToolResult] = []
        self.start_time = time.time()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "summaries").mkdir(exist_ok=True)
        
    def _load_config(self) -> ReviewConfig:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return ReviewConfig(**config_data)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def _run_command(self, cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Run a command with timeout"""
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd()
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"Command failed: {e}")
            raise
    
    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available in PATH"""
        try:
            subprocess.run([tool_name, "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def run_python_analysis(self) -> List[ToolResult]:
        """Run Python static analysis tools"""
        results = []
        
        if not self.config.tools.get('python', {}).get('ruff', False):
            return results
            
        # Ruff linting
        if self._check_tool_available('ruff'):
            start_time = time.time()
            try:
                cmd = ['ruff', 'check', '.', '--output-format=json']
                result = self._run_command(cmd, self.config.timeouts['individual_tool'])
                output_file = self.output_dir / "ruff.json"
                
                with open(output_file, 'w') as f:
                    f.write(result.stdout)
                
                findings = json.loads(result.stdout) if result.stdout else []
                findings_count = len(findings) if isinstance(findings, list) else 0
                
                results.append(ToolResult(
                    tool_name="ruff",
                    success=result.returncode == 0,
                    output_file=str(output_file),
                    execution_time=time.time() - start_time,
                    findings_count=findings_count
                ))
            except Exception as e:
                results.append(ToolResult(
                    tool_name="ruff",
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                ))
        
        # Basedpyright type checking
        if self.config.tools.get('python', {}).get('basedpyright', False):
            start_time = time.time()
            try:
                cmd = ['basedpyright', '--level', 'error', '--outputjson']
                result = self._run_command(cmd, self.config.timeouts['individual_tool'])
                output_file = self.output_dir / "basedpyright.json"
                
                with open(output_file, 'w') as f:
                    f.write(result.stdout)
                
                results.append(ToolResult(
                    tool_name="basedpyright",
                    success=result.returncode == 0,
                    output_file=str(output_file),
                    execution_time=time.time() - start_time
                ))
            except Exception as e:
                results.append(ToolResult(
                    tool_name="basedpyright",
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                ))
        
        # Bandit security analysis
        if self.config.tools.get('python', {}).get('bandit', False):
            start_time = time.time()
            try:
                cmd = ['bandit', '-q', '-r', '.', '-f', 'json']
                result = self._run_command(cmd, self.config.timeouts['individual_tool'])
                output_file = self.output_dir / "bandit.json"
                
                with open(output_file, 'w') as f:
                    f.write(result.stdout)
                
                findings = json.loads(result.stdout) if result.stdout else []
                findings_count = len(findings.get('results', []))
                
                results.append(ToolResult(
                    tool_name="bandit",
                    success=True,  # Bandit returns non-zero for findings
                    output_file=str(output_file),
                    execution_time=time.time() - start_time,
                    findings_count=findings_count
                ))
            except Exception as e:
                results.append(ToolResult(
                    tool_name="bandit",
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                ))
        
        return results
    
    def run_security_analysis(self) -> List[ToolResult]:
        """Run security analysis tools"""
        results = []
        
        # Gitleaks for secrets
        if self.config.tools.get('security', {}).get('gitleaks', False):
            start_time = time.time()
            try:
                cmd = ['gitleaks', 'detect', '-v', '--no-git', '--report-path', str(self.output_dir / "gitleaks.json")]
                result = self._run_command(cmd, self.config.timeouts['individual_tool'])
                
                results.append(ToolResult(
                    tool_name="gitleaks",
                    success=result.returncode == 0,
                    output_file=str(self.output_dir / "gitleaks.json"),
                    execution_time=time.time() - start_time
                ))
            except Exception as e:
                results.append(ToolResult(
                    tool_name="gitleaks",
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                ))
        
        # Semgrep SAST
        if self.config.tools.get('security', {}).get('semgrep', False):
            start_time = time.time()
            try:
                cmd = ['semgrep', 'scan', '--error', '--config', 'p/ci', '--json', '--output', str(self.output_dir / "semgrep.json")]
                result = self._run_command(cmd, self.config.timeouts['individual_tool'])
                
                results.append(ToolResult(
                    tool_name="semgrep",
                    success=result.returncode == 0,
                    output_file=str(self.output_dir / "semgrep.json"),
                    execution_time=time.time() - start_time
                ))
            except Exception as e:
                results.append(ToolResult(
                    tool_name="semgrep",
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                ))
        
        return results
    
    def run_tests_and_coverage(self) -> List[ToolResult]:
        """Run tests and collect coverage"""
        results = []
        
        if not self.config.tools.get('python', {}).get('coverage', False):
            return results
        
        start_time = time.time()
        try:
            # Run tests with coverage
            cmd = ['coverage', 'run', '-m', 'pytest', '-q']
            result = self._run_command(cmd, self.config.timeouts['test_execution'])
            
            if result.returncode == 0:
                # Generate coverage report
                cmd = ['coverage', 'xml', '-o', str(self.output_dir / "coverage.xml")]
                coverage_result = self._run_command(cmd, 30)
                
                results.append(ToolResult(
                    tool_name="coverage",
                    success=True,
                    output_file=str(self.output_dir / "coverage.xml"),
                    execution_time=time.time() - start_time
                ))
            else:
                results.append(ToolResult(
                    tool_name="coverage",
                    success=False,
                    error_message=result.stderr,
                    execution_time=time.time() - start_time
                ))
        except Exception as e:
            results.append(ToolResult(
                tool_name="coverage",
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            ))
        
        return results
    
    def run_ml_analysis(self) -> List[ToolResult]:
        """Run ML-specific analysis"""
        results = []
        
        if not self.config.ml_checks.get('enabled', False):
            return results
        
        # Check for ML-specific files and patterns
        ml_files = []
        for pattern in ['**/*.ipynb', '**/train*.py', '**/model*.py', '**/data*.py']:
            ml_files.extend(Path('.').glob(pattern))
        
        if not ml_files:
            logger.info("No ML files detected, skipping ML analysis")
            return results
        
        # Basic ML analysis - check for common issues
        start_time = time.time()
        ml_findings = []
        
        for file_path in ml_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for hardcoded seeds
                if 'random.seed(' in content or 'np.random.seed(' in content:
                    ml_findings.append({
                        'file': str(file_path),
                        'issue': 'hardcoded_seed',
                        'severity': 'medium',
                        'message': 'Hardcoded random seed found'
                    })
                
                # Check for potential data leakage
                if 'test' in content.lower() and 'train' in content.lower():
                    if 'test' in content.lower().split('train')[0]:
                        ml_findings.append({
                            'file': str(file_path),
                            'issue': 'potential_data_leakage',
                            'severity': 'high',
                            'message': 'Potential data leakage: test data used before train/test split'
                        })
                
            except Exception as e:
                logger.warning(f"Could not analyze {file_path}: {e}")
        
        output_file = self.output_dir / "ml_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(ml_findings, f, indent=2)
        
        results.append(ToolResult(
            tool_name="ml_analysis",
            success=True,
            output_file=str(output_file),
            execution_time=time.time() - start_time,
            findings_count=len(ml_findings)
        ))
        
        return results
    
    def generate_index(self) -> None:
        """Generate machine-readable index of all artifacts"""
        index = {
            'timestamp': datetime.now().isoformat(),
            'config_file': str(self.config_path),
            'output_directory': str(self.output_dir),
            'total_execution_time': time.time() - self.start_time,
            'tools_run': [asdict(result) for result in self.results],
            'artifacts': []
        }
        
        # List all generated files
        for file_path in self.output_dir.rglob('*'):
            if file_path.is_file():
                index['artifacts'].append({
                    'path': str(file_path.relative_to(self.output_dir)),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        index_file = self.output_dir / "index.json"
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def run_full_review(self) -> None:
        """Run complete code review"""
        logger.info("Starting comprehensive code review...")
        
        # Run all analysis phases
        self.results.extend(self.run_python_analysis())
        self.results.extend(self.run_security_analysis())
        self.results.extend(self.run_tests_and_coverage())
        self.results.extend(self.run_ml_analysis())
        
        # Generate index
        self.generate_index()
        
        # Log summary
        total_time = time.time() - self.start_time
        successful_tools = sum(1 for r in self.results if r.success)
        total_findings = sum(r.findings_count for r in self.results)
        
        logger.info(f"Review completed in {total_time:.2f}s")
        logger.info(f"Tools run: {len(self.results)}, Successful: {successful_tools}")
        logger.info(f"Total findings: {total_findings}")
        logger.info(f"Results saved to: {self.output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Run comprehensive code review')
    parser.add_argument('--config', default='configs/review.yaml', help='Configuration file path')
    parser.add_argument('--out', default='reports/code_review', help='Output directory')
    
    args = parser.parse_args()
    
    runner = CodeReviewRunner(args.config, args.out)
    runner.run_full_review()

if __name__ == '__main__':
    main()
