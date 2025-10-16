#!/usr/bin/env python3
"""
Findings to Diff Generator

Converts static analysis findings into unified diff patches for easy application.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Finding:
    """Represents a single finding from static analysis"""
    file_path: str
    line_number: int
    column: Optional[int]
    rule_id: str
    message: str
    severity: str
    confidence: float = 1.0
    fix_suggestion: Optional[str] = None

class DiffGenerator:
    """Generates unified diff patches from findings"""
    
    def __init__(self, findings_dir: str, output_file: str):
        self.findings_dir = Path(findings_dir)
        self.output_file = Path(output_file)
        self.patches = []
        
    def load_findings(self) -> List[Finding]:
        """Load findings from all tool output files"""
        findings = []
        
        # Load ruff findings
        ruff_file = self.findings_dir / "ruff.json"
        if ruff_file.exists():
            findings.extend(self._load_ruff_findings(ruff_file))
        
        # Load bandit findings
        bandit_file = self.findings_dir / "bandit.json"
        if bandit_file.exists():
            findings.extend(self._load_bandit_findings(bandit_file))
        
        # Load basedpyright findings
        basedpyright_file = self.findings_dir / "basedpyright.json"
        if basedpyright_file.exists():
            findings.extend(self._load_basedpyright_findings(basedpyright_file))
        
        # Load semgrep findings
        semgrep_file = self.findings_dir / "semgrep.json"
        if semgrep_file.exists():
            findings.extend(self._load_semgrep_findings(semgrep_file))
        
        return findings
    
    def _load_ruff_findings(self, file_path: Path) -> List[Finding]:
        """Load findings from ruff JSON output"""
        findings = []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for item in data:
                finding = Finding(
                    file_path=item.get('filename', ''),
                    line_number=item.get('location', {}).get('row', 0),
                    column=item.get('location', {}).get('column', None),
                    rule_id=item.get('code', ''),
                    message=item.get('message', ''),
                    severity=self._map_ruff_severity(item.get('code', '')),
                    fix_suggestion=item.get('fix', {}).get('message', '') if item.get('fix') else None
                )
                findings.append(finding)
        except Exception as e:
            logger.warning(f"Could not load ruff findings: {e}")
        
        return findings
    
    def _load_bandit_findings(self, file_path: Path) -> List[Finding]:
        """Load findings from bandit JSON output"""
        findings = []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for result in data.get('results', []):
                finding = Finding(
                    file_path=result.get('filename', ''),
                    line_number=result.get('line_number', 0),
                    column=None,
                    rule_id=result.get('test_id', ''),
                    message=result.get('issue_text', ''),
                    severity=self._map_bandit_severity(result.get('issue_severity', 'LOW'))
                )
                findings.append(finding)
        except Exception as e:
            logger.warning(f"Could not load bandit findings: {e}")
        
        return findings
    
    def _load_basedpyright_findings(self, file_path: Path) -> List[Finding]:
        """Load findings from basedpyright JSON output"""
        findings = []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for diagnostic in data.get('generalDiagnostics', []):
                finding = Finding(
                    file_path=diagnostic.get('file', ''),
                    line_number=diagnostic.get('range', {}).get('start', {}).get('line', 0) + 1,
                    column=diagnostic.get('range', {}).get('start', {}).get('character', None),
                    rule_id=diagnostic.get('rule', ''),
                    message=diagnostic.get('message', ''),
                    severity='high'  # Basedpyright errors are typically high severity
                )
                findings.append(finding)
        except Exception as e:
            logger.warning(f"Could not load basedpyright findings: {e}")
        
        return findings
    
    def _load_semgrep_findings(self, file_path: Path) -> List[Finding]:
        """Load findings from semgrep JSON output"""
        findings = []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for result in data.get('results', []):
                finding = Finding(
                    file_path=result.get('path', ''),
                    line_number=result.get('start', {}).get('line', 0),
                    column=result.get('start', {}).get('col', None),
                    rule_id=result.get('check_id', ''),
                    message=result.get('message', ''),
                    severity=self._map_semgrep_severity(result.get('extra', {}).get('severity', 'INFO'))
                )
                findings.append(finding)
        except Exception as e:
            logger.warning(f"Could not load semgrep findings: {e}")
        
        return findings
    
    def _map_ruff_severity(self, rule_id: str) -> str:
        """Map ruff rule to severity"""
        high_severity_rules = ['F', 'E']  # Fatal errors, errors
        medium_severity_rules = ['W']  # Warnings
        
        if any(rule_id.startswith(prefix) for prefix in high_severity_rules):
            return 'high'
        elif any(rule_id.startswith(prefix) for prefix in medium_severity_rules):
            return 'medium'
        else:
            return 'low'
    
    def _map_bandit_severity(self, severity: str) -> str:
        """Map bandit severity to standard severity"""
        mapping = {
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low'
        }
        return mapping.get(severity.upper(), 'low')
    
    def _map_semgrep_severity(self, severity: str) -> str:
        """Map semgrep severity to standard severity"""
        mapping = {
            'ERROR': 'high',
            'WARNING': 'medium',
            'INFO': 'low'
        }
        return mapping.get(severity.upper(), 'low')
    
    def generate_patches(self, findings: List[Finding]) -> None:
        """Generate unified diff patches for findings"""
        # Group findings by file
        findings_by_file = {}
        for finding in findings:
            if finding.file_path not in findings_by_file:
                findings_by_file[finding.file_path] = []
            findings_by_file[finding.file_path].append(finding)
        
        # Generate patches for each file
        for file_path, file_findings in findings_by_file.items():
            patch = self._generate_file_patch(file_path, file_findings)
            if patch:
                self.patches.append(patch)
    
    def _generate_file_patch(self, file_path: str, findings: List[Finding]) -> Optional[str]:
        """Generate a patch for a single file"""
        try:
            # Read the original file
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Sort findings by line number (descending) to avoid line number shifts
            sorted_findings = sorted(findings, key=lambda x: x.line_number, reverse=True)
            
            # Apply fixes
            modified_lines = lines.copy()
            for finding in sorted_findings:
                if finding.fix_suggestion and finding.line_number <= len(modified_lines):
                    # Simple fix: replace the line with the suggestion
                    # This is a basic implementation - could be enhanced
                    line_idx = finding.line_number - 1
                    if line_idx < len(modified_lines):
                        modified_lines[line_idx] = finding.fix_suggestion + '\n'
            
            # Generate unified diff
            return self._create_unified_diff(file_path, lines, modified_lines)
            
        except Exception as e:
            logger.warning(f"Could not generate patch for {file_path}: {e}")
            return None
    
    def _create_unified_diff(self, file_path: str, original_lines: List[str], modified_lines: List[str]) -> str:
        """Create a unified diff between original and modified lines"""
        if original_lines == modified_lines:
            return ""
        
        diff_lines = []
        diff_lines.append(f"--- a/{file_path}")
        diff_lines.append(f"+++ b/{file_path}")
        
        # Simple diff generation (could be enhanced with proper diff algorithm)
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
            if orig != mod:
                diff_lines.append(f"@@ -{i+1},1 +{i+1},1 @@")
                diff_lines.append(f"-{orig.rstrip()}")
                diff_lines.append(f"+{mod.rstrip()}")
        
        return '\n'.join(diff_lines)
    
    def write_patches(self) -> None:
        """Write all patches to the output file"""
        with open(self.output_file, 'w') as f:
            f.write("# Code Review Patches\n")
            f.write("# Generated automatically from static analysis findings\n")
            f.write("# Apply with: git apply patches.diff\n\n")
            
            for patch in self.patches:
                if patch.strip():
                    f.write(patch)
                    f.write('\n\n')
    
    def run(self) -> None:
        """Run the diff generation process"""
        logger.info("Loading findings...")
        findings = self.load_findings()
        
        logger.info(f"Found {len(findings)} total findings")
        
        # Filter for high-confidence, fixable findings
        fixable_findings = [
            f for f in findings 
            if f.confidence >= 0.8 and f.fix_suggestion
        ]
        
        logger.info(f"Generating patches for {len(fixable_findings)} fixable findings...")
        self.generate_patches(fixable_findings)
        
        logger.info(f"Writing patches to {self.output_file}")
        self.write_patches()
        
        logger.info(f"Generated {len(self.patches)} patches")

def main():
    parser = argparse.ArgumentParser(description='Generate patches from code review findings')
    parser.add_argument('--findings-dir', default='reports/code_review', help='Directory containing findings')
    parser.add_argument('--output', default='reports/code_review/patches.diff', help='Output patch file')
    
    args = parser.parse_args()
    
    generator = DiffGenerator(args.findings_dir, args.output)
    generator.run()

if __name__ == '__main__':
    main()
