#!/usr/bin/env python3
"""
Smoke tests for the code review runner

Tests basic functionality without requiring all tools to be installed.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the review modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_review import CodeReviewRunner, ReviewConfig, ToolResult
from findings_to_diff import DiffGenerator, Finding

class TestCodeReviewRunner(unittest.TestCase):
    """Test the code review runner functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"
        self.output_dir = Path(self.temp_dir) / "output"
        
        # Create a minimal test config
        test_config = {
            'tools': {
                'python': {'ruff': True, 'basedpyright': False, 'bandit': False},
                'security': {'gitleaks': False, 'semgrep': False},
                'containers': {'hadolint': False},
                'infrastructure': {'checkov': False, 'yamllint': False},
                'sbom': {'syft': False, 'pip_licenses': False}
            },
            'patterns': {
                'include': ['**/*.py'],
                'exclude': ['venv/**', '__pycache__/**']
            },
            'thresholds': {
                'coverage_min': 70,
                'max_line_length': 120
            },
            'timeouts': {
                'total_review': 60,
                'individual_tool': 30,
                'test_execution': 60
            },
            'severity': {
                'critical': ['security'],
                'high': ['performance'],
                'medium': ['style'],
                'low': ['formatting']
            },
            'ml_checks': {
                'enabled': False
            },
            'report': {
                'max_findings_per_category': 50,
                'include_raw_outputs': True,
                'generate_patches': True
            }
        }
        
        with open(self.config_file, 'w') as f:
            import yaml
            yaml.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_config_loading(self):
        """Test that configuration loads correctly"""
        runner = CodeReviewRunner(str(self.config_file), str(self.output_dir))
        
        self.assertIsInstance(runner.config, ReviewConfig)
        self.assertTrue(runner.config.tools['python']['ruff'])
        self.assertFalse(runner.config.tools['python']['basedpyright'])
    
    def test_output_directory_creation(self):
        """Test that output directory is created"""
        runner = CodeReviewRunner(str(self.config_file), str(self.output_dir))
        
        self.assertTrue(self.output_dir.exists())
        self.assertTrue((self.output_dir / "summaries").exists())
    
    @patch('subprocess.run')
    def test_ruff_analysis_success(self, mock_run):
        """Test successful ruff analysis"""
        # Mock successful ruff run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {
                'filename': 'test.py',
                'location': {'row': 1, 'column': 1},
                'code': 'E501',
                'message': 'Line too long'
            }
        ])
        mock_run.return_value = mock_result
        
        runner = CodeReviewRunner(str(self.config_file), str(self.output_dir))
        results = runner.run_python_analysis()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].tool_name, 'ruff')
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].findings_count, 1)
    
    @patch('subprocess.run')
    def test_ruff_analysis_failure(self, mock_run):
        """Test ruff analysis failure handling"""
        # Mock failed ruff run
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Tool not found"
        mock_run.return_value = mock_result
        
        runner = CodeReviewRunner(str(self.config_file), str(self.output_dir))
        results = runner.run_python_analysis()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].tool_name, 'ruff')
        self.assertFalse(results[0].success)
    
    def test_ml_analysis_no_files(self):
        """Test ML analysis when no ML files are present"""
        runner = CodeReviewRunner(str(self.config_file), str(self.output_dir))
        results = runner.run_ml_analysis()
        
        self.assertEqual(len(results), 0)
    
    def test_index_generation(self):
        """Test that index file is generated correctly"""
        runner = CodeReviewRunner(str(self.config_file), str(self.output_dir))
        
        # Add some mock results
        runner.results = [
            ToolResult(tool_name="test_tool", success=True, findings_count=5)
        ]
        
        runner.generate_index()
        
        index_file = self.output_dir / "index.json"
        self.assertTrue(index_file.exists())
        
        with open(index_file, 'r') as f:
            index_data = json.load(f)
        
        self.assertIn('timestamp', index_data)
        self.assertIn('tools_run', index_data)
        self.assertEqual(len(index_data['tools_run']), 1)
        self.assertEqual(index_data['tools_run'][0]['tool_name'], 'test_tool')

class TestDiffGenerator(unittest.TestCase):
    """Test the diff generator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.findings_dir = Path(self.temp_dir) / "findings"
        self.output_file = Path(self.temp_dir) / "patches.diff"
        self.findings_dir.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_finding_creation(self):
        """Test Finding dataclass creation"""
        finding = Finding(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="medium",
            confidence=0.9,
            fix_suggestion="Shorten line"
        )
        
        self.assertEqual(finding.file_path, "test.py")
        self.assertEqual(finding.line_number, 10)
        self.assertEqual(finding.severity, "medium")
    
    def test_ruff_findings_loading(self):
        """Test loading ruff findings from JSON"""
        ruff_data = [
            {
                'filename': 'test.py',
                'location': {'row': 1, 'column': 1},
                'code': 'E501',
                'message': 'Line too long',
                'fix': {'message': 'Shorten line'}
            }
        ]
        
        ruff_file = self.findings_dir / "ruff.json"
        with open(ruff_file, 'w') as f:
            json.dump(ruff_data, f)
        
        generator = DiffGenerator(str(self.findings_dir), str(self.output_file))
        findings = generator._load_ruff_findings(ruff_file)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].file_path, 'test.py')
        self.assertEqual(findings[0].rule_id, 'E501')
        self.assertEqual(findings[0].severity, 'high')  # E501 is an error
    
    def test_severity_mapping(self):
        """Test severity mapping functions"""
        generator = DiffGenerator(str(self.findings_dir), str(self.output_file))
        
        # Test ruff severity mapping
        self.assertEqual(generator._map_ruff_severity('E501'), 'high')
        self.assertEqual(generator._map_ruff_severity('W291'), 'medium')
        self.assertEqual(generator._map_ruff_severity('I001'), 'low')
        
        # Test bandit severity mapping
        self.assertEqual(generator._map_bandit_severity('HIGH'), 'high')
        self.assertEqual(generator._map_bandit_severity('MEDIUM'), 'medium')
        self.assertEqual(generator._map_bandit_severity('LOW'), 'low')
        
        # Test semgrep severity mapping
        self.assertEqual(generator._map_semgrep_severity('ERROR'), 'high')
        self.assertEqual(generator._map_semgrep_severity('WARNING'), 'medium')
        self.assertEqual(generator._map_semgrep_severity('INFO'), 'low')
    
    def test_patch_generation(self):
        """Test patch generation for a simple case"""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.py"
        with open(test_file, 'w') as f:
            f.write("print('hello world')\n")
        
        # Create a finding
        finding = Finding(
            file_path=str(test_file),
            line_number=1,
            column=None,
            rule_id="E501",
            message="Line too long",
            severity="high",
            confidence=0.9,
            fix_suggestion="print('hello')\n"
        )
        
        generator = DiffGenerator(str(self.findings_dir), str(self.output_file))
        generator.generate_patches([finding])
        
        self.assertEqual(len(generator.patches), 1)
        self.assertIn("--- a/", generator.patches[0])
        self.assertIn("+++ b/", generator.patches[0])

if __name__ == '__main__':
    unittest.main()
