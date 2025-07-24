#!/usr/bin/env python3
"""
NeuroForge LLM Code Analysis Plugin
Author: Muzan Sano

This plugin uses LLM capabilities to provide advanced code analysis,
including security scanning, performance optimization, and code quality assessment.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import LLM engine
from agent.llm_engine import LLMEngine, LLMConfig, LLMProvider, LLMCapability, LLMRequest


class AnalysisType(Enum):
    """Types of code analysis available"""
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    COMPREHENSIVE = "comprehensive"


class SeverityLevel(Enum):
    """Severity levels for analysis findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AnalysisFinding:
    """A single finding from code analysis"""
    title: str
    description: str
    severity: SeverityLevel
    category: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence: float = 0.0


@dataclass
class AnalysisReport:
    """Complete analysis report"""
    analysis_type: AnalysisType
    workspace_path: str
    files_analyzed: List[str]
    findings: List[AnalysisFinding]
    summary: str
    recommendations: List[str]
    metrics: Dict[str, Any]
    timestamp: str
    llm_provider: str
    execution_time: float


class LLMCodeAnalyzer:
    """LLM-powered code analyzer plugin"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.llm_engine = LLMEngine(workspace_root)
        self.analysis_history: List[AnalysisReport] = []
        
        # Initialize with mock provider by default
        self._setup_default_provider()
        
        print("LLM Code Analyzer initialized")
    
    def _setup_default_provider(self):
        """Setup default LLM provider"""
        # Try to use OpenAI if API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                config = LLMConfig(
                    provider=LLMProvider.OPENAI,
                    model="gpt-4-turbo-preview",
                    api_key=openai_key,
                    max_tokens=4096,
                    temperature=0.1
                )
                self.llm_engine.register_provider(config, is_default=True)
                print("Using OpenAI GPT-4 for code analysis")
                return
            except Exception as e:
                print(f"Failed to setup OpenAI: {e}")
        
        # Try Anthropic if API key is available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                config = LLMConfig(
                    provider=LLMProvider.ANTHROPIC,
                    model="claude-3-sonnet-20240229",
                    api_key=anthropic_key,
                    max_tokens=4096,
                    temperature=0.1
                )
                self.llm_engine.register_provider(config, is_default=True)
                print("Using Anthropic Claude for code analysis")
                return
            except Exception as e:
                print(f"Failed to setup Anthropic: {e}")
        
        # Fallback to mock provider
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-analyzer"
        )
        self.llm_engine.register_provider(config, is_default=True)
        print("Using mock provider for code analysis (set OPENAI_API_KEY or ANTHROPIC_API_KEY for real LLM)")
    
    async def analyze_workspace(self, analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE,
                               file_patterns: List[str] = None) -> AnalysisReport:
        """Analyze entire workspace"""
        print(f"Starting {analysis_type.value} analysis of workspace...")
        
        # Get files to analyze
        files_to_analyze = self._get_files_to_analyze(file_patterns)
        
        if not files_to_analyze:
            print("No files found to analyze")
            return self._create_empty_report(analysis_type)
        
        # Analyze files
        all_findings = []
        analysis_start = asyncio.get_event_loop().time()
        
        for file_path in files_to_analyze:
            print(f"Analyzing {file_path}...")
            findings = await self._analyze_file(file_path, analysis_type)
            all_findings.extend(findings)
        
        execution_time = asyncio.get_event_loop().time() - analysis_start
        
        # Generate summary and recommendations
        summary, recommendations = await self._generate_summary_and_recommendations(
            all_findings, analysis_type
        )
        
        # Create report
        report = AnalysisReport(
            analysis_type=analysis_type,
            workspace_path=str(self.workspace_root),
            files_analyzed=[str(f) for f in files_to_analyze],
            findings=all_findings,
            summary=summary,
            recommendations=recommendations,
            metrics=self._calculate_metrics(all_findings),
            timestamp=asyncio.get_event_loop().time(),
            llm_provider=str(self.llm_engine.default_provider),
            execution_time=execution_time
        )
        
        self.analysis_history.append(report)
        print(f"Analysis completed in {execution_time:.2f}s with {len(all_findings)} findings")
        
        return report
    
    async def analyze_file(self, file_path: str, analysis_type: AnalysisType = AnalysisType.QUALITY) -> List[AnalysisFinding]:
        """Analyze a single file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return await self._analyze_file(file_path, analysis_type)
    
    async def _analyze_file(self, file_path: Path, analysis_type: AnalysisType) -> List[AnalysisFinding]:
        """Internal file analysis implementation"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            if not code_content.strip():
                return []
            
            # Determine analysis prompts based on type
            analysis_prompts = self._get_analysis_prompts(analysis_type)
            
            findings = []
            
            for prompt_info in analysis_prompts:
                prompt, capability = prompt_info
                
                # Create LLM request
                request = LLMRequest(
                    prompt=prompt,
                    capability=capability,
                    code_context=code_content,
                    context={
                        "file_path": str(file_path),
                        "file_extension": file_path.suffix,
                        "analysis_type": analysis_type.value
                    }
                )
                
                # Get LLM response
                response = await self.llm_engine.generate_response(request)
                
                # Parse findings from response
                file_findings = self._parse_llm_response(response, str(file_path))
                findings.extend(file_findings)
            
            return findings
            
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return [AnalysisFinding(
                title="Analysis Error",
                description=f"Failed to analyze file: {str(e)}",
                severity=SeverityLevel.MEDIUM,
                category="error",
                file_path=str(file_path),
                confidence=1.0
            )]
    
    def _get_analysis_prompts(self, analysis_type: AnalysisType) -> List[tuple]:
        """Get analysis prompts for different analysis types"""
        prompts = {
            AnalysisType.QUALITY: [
                ("Analyze this code for quality issues including code style, naming conventions, complexity, and adherence to best practices. Provide specific findings with line numbers where possible.", LLMCapability.CODE_ANALYSIS)
            ],
            AnalysisType.SECURITY: [
                ("Perform a security analysis of this code. Look for vulnerabilities, insecure patterns, input validation issues, and potential attack vectors. Be specific about security risks.", LLMCapability.SECURITY)
            ],
            AnalysisType.PERFORMANCE: [
                ("Analyze this code for performance issues including inefficient algorithms, memory usage problems, unnecessary computations, and optimization opportunities.", LLMCapability.CODE_ANALYSIS)
            ],
            AnalysisType.ARCHITECTURE: [
                ("Evaluate the architectural quality of this code including design patterns, modularity, coupling, cohesion, and overall structure.", LLMCapability.ARCHITECTURE)
            ],
            AnalysisType.MAINTAINABILITY: [
                ("Assess the maintainability of this code including readability, documentation, complexity, and ease of modification.", LLMCapability.CODE_ANALYSIS)
            ],
            AnalysisType.DOCUMENTATION: [
                ("Evaluate the documentation quality of this code including comments, docstrings, and inline documentation. Suggest improvements.", LLMCapability.DOCUMENTATION)
            ],
            AnalysisType.TESTING: [
                ("Analyze this code for testability and suggest what tests should be written. Identify areas that are difficult to test.", LLMCapability.TESTING)
            ],
            AnalysisType.COMPREHENSIVE: [
                ("Perform a comprehensive code analysis covering quality, security, performance, and maintainability. Provide detailed findings.", LLMCapability.CODE_ANALYSIS),
                ("Analyze this code for security vulnerabilities and risks.", LLMCapability.SECURITY),
                ("Evaluate the architectural design and suggest improvements.", LLMCapability.ARCHITECTURE)
            ]
        }
        
        return prompts.get(analysis_type, prompts[AnalysisType.QUALITY])
    
    def _parse_llm_response(self, response, file_path: str) -> List[AnalysisFinding]:
        """Parse LLM response into structured findings"""
        findings = []
        
        # Simple parsing - in production, you'd want more sophisticated parsing
        content = response.content
        
        # Try to extract structured information
        lines = content.split('\n')
        current_finding = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for finding markers
            if any(keyword in line.lower() for keyword in ['issue:', 'problem:', 'warning:', 'error:', 'finding:']):
                if current_finding:
                    findings.append(current_finding)
                
                # Extract severity from keywords
                severity = SeverityLevel.MEDIUM
                if any(keyword in line.lower() for keyword in ['critical', 'severe', 'dangerous']):
                    severity = SeverityLevel.CRITICAL
                elif any(keyword in line.lower() for keyword in ['high', 'important', 'major']):
                    severity = SeverityLevel.HIGH
                elif any(keyword in line.lower() for keyword in ['low', 'minor', 'trivial']):
                    severity = SeverityLevel.LOW
                elif any(keyword in line.lower() for keyword in ['info', 'note', 'suggestion']):
                    severity = SeverityLevel.INFO
                
                current_finding = AnalysisFinding(
                    title=line,
                    description="",
                    severity=severity,
                    category=response.capability.value,
                    file_path=file_path,
                    confidence=response.confidence
                )
            elif current_finding:
                # Add to description
                current_finding.description += line + " "
        
        # Add last finding
        if current_finding:
            findings.append(current_finding)
        
        # If no structured findings found, create a general finding
        if not findings:
            findings.append(AnalysisFinding(
                title=f"{response.capability.value.title()} Analysis",
                description=content,
                severity=SeverityLevel.INFO,
                category=response.capability.value,
                file_path=file_path,
                confidence=response.confidence
            ))
        
        return findings
    
    async def _generate_summary_and_recommendations(self, findings: List[AnalysisFinding], 
                                                   analysis_type: AnalysisType) -> tuple:
        """Generate summary and recommendations from findings"""
        if not findings:
            return "No issues found.", []
        
        # Prepare findings summary for LLM
        findings_text = "\n".join([
            f"- {finding.severity.value.upper()}: {finding.title} - {finding.description}"
            for finding in findings[:20]  # Limit to avoid token limits
        ])
        
        prompt = f"""Based on these code analysis findings, provide:
1. A concise summary of the overall code quality
2. Top 5 actionable recommendations for improvement

Findings:
{findings_text}

Analysis Type: {analysis_type.value}
Total Findings: {len(findings)}"""
        
        request = LLMRequest(
            prompt=prompt,
            capability=LLMCapability.CODE_ANALYSIS,
            context={"analysis_type": analysis_type.value, "findings_count": len(findings)}
        )
        
        response = await self.llm_engine.generate_response(request)
        
        # Parse summary and recommendations
        content = response.content
        parts = content.split("recommendations", 1)
        
        if len(parts) == 2:
            summary = parts[0].strip()
            recommendations_text = parts[1].strip()
            recommendations = [
                rec.strip() 
                for rec in recommendations_text.split('\n') 
                if rec.strip() and any(char.isalnum() for char in rec)
            ][:5]
        else:
            summary = content
            recommendations = [
                "Review critical and high severity findings first",
                "Implement suggested security improvements",
                "Improve code documentation and comments",
                "Add comprehensive test coverage",
                "Consider refactoring complex functions"
            ]
        
        return summary, recommendations
    
    def _get_files_to_analyze(self, patterns: List[str] = None) -> List[Path]:
        """Get list of files to analyze based on patterns"""
        if patterns is None:
            patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.cpp', '**/*.c', '**/*.cs']
        
        files = []
        for pattern in patterns:
            try:
                # Handle relative patterns properly
                if pattern.startswith('/'):
                    # Skip absolute patterns as they're not supported
                    continue
                files.extend(self.workspace_root.rglob(pattern.lstrip('**/')))
            except Exception as e:
                print(f"Warning: Could not process pattern '{pattern}': {e}")
                continue
        
        # Filter out common directories to ignore
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.vscode', '.neuroforge', 'venv', 'env'}
        
        filtered_files = []
        for file_path in files:
            if file_path.is_file() and not any(part in ignore_dirs for part in file_path.parts):
                filtered_files.append(file_path)
        
        return filtered_files[:50]  # Limit to avoid excessive analysis
    
    def _calculate_metrics(self, findings: List[AnalysisFinding]) -> Dict[str, Any]:
        """Calculate metrics from findings"""
        severity_counts = {severity.value: 0 for severity in SeverityLevel}
        category_counts = {}
        
        for finding in findings:
            severity_counts[finding.severity.value] += 1
            category_counts[finding.category] = category_counts.get(finding.category, 0) + 1
        
        total_findings = len(findings)
        critical_high = severity_counts['critical'] + severity_counts['high']
        
        return {
            "total_findings": total_findings,
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "quality_score": max(0, 100 - (critical_high * 10) - (total_findings * 2)),
            "risk_level": "high" if critical_high > 5 else "medium" if critical_high > 0 else "low"
        }
    
    def _create_empty_report(self, analysis_type: AnalysisType) -> AnalysisReport:
        """Create empty analysis report"""
        return AnalysisReport(
            analysis_type=analysis_type,
            workspace_path=str(self.workspace_root),
            files_analyzed=[],
            findings=[],
            summary="No files found to analyze.",
            recommendations=[],
            metrics={"total_findings": 0, "quality_score": 100, "risk_level": "low"},
            timestamp=asyncio.get_event_loop().time(),
            llm_provider=str(self.llm_engine.default_provider),
            execution_time=0.0
        )
    
    def export_report(self, report: AnalysisReport, format: str = "json") -> str:
        """Export analysis report to different formats"""
        if format == "json":
            return self._export_json(report)
        elif format == "markdown":
            return self._export_markdown(report)
        elif format == "html":
            return self._export_html(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, report: AnalysisReport) -> str:
        """Export report as JSON"""
        return json.dumps({
            "analysis_type": report.analysis_type.value,
            "workspace_path": report.workspace_path,
            "files_analyzed": report.files_analyzed,
            "findings": [
                {
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity.value,
                    "category": f.category,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "suggestion": f.suggestion,
                    "confidence": f.confidence
                }
                for f in report.findings
            ],
            "summary": report.summary,
            "recommendations": report.recommendations,
            "metrics": report.metrics,
            "timestamp": report.timestamp,
            "llm_provider": report.llm_provider,
            "execution_time": report.execution_time
        }, indent=2)
    
    def _export_markdown(self, report: AnalysisReport) -> str:
        """Export report as Markdown"""
        md = f"""# Code Analysis Report

**Analysis Type:** {report.analysis_type.value.title()}
**Workspace:** {report.workspace_path}
**Files Analyzed:** {len(report.files_analyzed)}
**Total Findings:** {len(report.findings)}
**Quality Score:** {report.metrics.get('quality_score', 'N/A')}
**Risk Level:** {report.metrics.get('risk_level', 'Unknown')}

## Summary

{report.summary}

## Recommendations

"""
        for i, rec in enumerate(report.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        md += "\n## Findings\n\n"
        
        for finding in report.findings:
            md += f"### {finding.severity.value.upper()}: {finding.title}\n\n"
            md += f"**File:** {finding.file_path}\n\n"
            md += f"{finding.description}\n\n"
            if finding.suggestion:
                md += f"**Suggestion:** {finding.suggestion}\n\n"
            md += "---\n\n"
        
        return md
    
    def _export_html(self, report: AnalysisReport) -> str:
        """Export report as HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Code Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .finding {{ margin: 20px 0; padding: 15px; border-left: 4px solid #ddd; }}
        .critical {{ border-left-color: #d32f2f; }}
        .high {{ border-left-color: #f57c00; }}
        .medium {{ border-left-color: #fbc02d; }}
        .low {{ border-left-color: #388e3c; }}
        .info {{ border-left-color: #1976d2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Code Analysis Report</h1>
        <p><strong>Analysis Type:</strong> {report.analysis_type.value.title()}</p>
        <p><strong>Files Analyzed:</strong> {len(report.files_analyzed)}</p>
        <p><strong>Total Findings:</strong> {len(report.findings)}</p>
        <p><strong>Quality Score:</strong> {report.metrics.get('quality_score', 'N/A')}</p>
    </div>
    
    <h2>Summary</h2>
    <p>{report.summary}</p>
    
    <h2>Recommendations</h2>
    <ol>
"""
        for rec in report.recommendations:
            html += f"        <li>{rec}</li>\n"
        
        html += "    </ol>\n    <h2>Findings</h2>\n"
        
        for finding in report.findings:
            html += f"""    <div class="finding {finding.severity.value}">
        <h3>{finding.severity.value.upper()}: {finding.title}</h3>
        <p><strong>File:</strong> {finding.file_path}</p>
        <p>{finding.description}</p>
"""
            if finding.suggestion:
                html += f"        <p><strong>Suggestion:</strong> {finding.suggestion}</p>\n"
            html += "    </div>\n"
        
        html += "</body>\n</html>"
        return html
    
    def get_analysis_history(self) -> List[AnalysisReport]:
        """Get history of all analyses"""
        return self.analysis_history


# Plugin interface for NeuroForge task agent
async def run_plugin(task_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Main plugin entry point"""
    workspace_path = parameters.get('workspace_path', '.')
    analysis_type = parameters.get('analysis_type', 'comprehensive')
    file_patterns = parameters.get('file_patterns')
    export_format = parameters.get('export_format', 'json')
    
    try:
        # Create analyzer
        analyzer = LLMCodeAnalyzer(workspace_path)
        
        # Run analysis
        analysis_type_enum = AnalysisType(analysis_type)
        report = await analyzer.analyze_workspace(analysis_type_enum, file_patterns)
        
        # Export report
        exported_report = analyzer.export_report(report, export_format)
        
        # Save report to file
        report_file = Path(workspace_path) / f".neuroforge/reports/analysis_{task_id}.{export_format}"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write(exported_report)
        
        return {
            "status": "completed",
            "report_path": str(report_file),
            "findings_count": len(report.findings),
            "quality_score": report.metrics.get('quality_score', 0),
            "risk_level": report.metrics.get('risk_level', 'unknown'),
            "summary": report.summary,
            "recommendations": report.recommendations,
            "execution_time": report.execution_time
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_code_analyzer():
        """Test the LLM code analyzer"""
        analyzer = LLMCodeAnalyzer(".")
        
        # Test workspace analysis
        print("Running comprehensive code analysis...")
        report = await analyzer.analyze_workspace(AnalysisType.COMPREHENSIVE)
        
        print(f"\nAnalysis Results:")
        print(f"Files analyzed: {len(report.files_analyzed)}")
        print(f"Findings: {len(report.findings)}")
        print(f"Quality score: {report.metrics.get('quality_score', 'N/A')}")
        print(f"Risk level: {report.metrics.get('risk_level', 'Unknown')}")
        
        print(f"\nSummary: {report.summary}")
        
        print(f"\nTop findings:")
        for finding in report.findings[:3]:
            print(f"- {finding.severity.value.upper()}: {finding.title}")
        
        # Export report
        markdown_report = analyzer.export_report(report, "markdown")
        print(f"\nMarkdown report length: {len(markdown_report)} characters")
        
        print("\n✅ LLM Code Analyzer test completed!")
    
    # Run test
    asyncio.run(test_code_analyzer())
