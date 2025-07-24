"""
Test Runner Plugin for NeuroForge

Handles test execution, test generation, and test result analysis
for various testing frameworks (pytest, unittest, etc.).

Author: Muzan Sano
License: MIT
"""

import asyncio
import subprocess
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from ..task_agent import PluginBase
from ..memory_engine import MemoryEngine


class TestRunnerPlugin(PluginBase):
    """Plugin for automated testing operations"""
    
    def __init__(self, memory_engine: MemoryEngine):
        super().__init__("test_runner", memory_engine)
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test operations"""
        workspace_path = context.get('workspace', {}).get('workspace_path')
        if not workspace_path:
            raise ValueError("No workspace path provided")
        
        action = parameters.get('action', 'run')
        result = {}
        
        try:
            if action == 'run':
                result = await self._run_tests(workspace_path, parameters)
            elif action == 'generate':
                result = await self._generate_tests(workspace_path, parameters)
            elif action == 'analyze':
                result = await self._analyze_tests(workspace_path, parameters)
            elif action == 'coverage':
                result = await self._run_coverage(workspace_path, parameters)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # Store test operation in memory
            await self.memory_engine.store_memory(
                content={
                    'test_action': action,
                    'workspace': workspace_path,
                    'result': result,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                tags=['test', action, 'automation']
            )
            
            return result
        
        except Exception as e:
            raise ValueError(f"Test operation failed: {str(e)}")
    
    async def _run_tests(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run test suite"""
        test_framework = parameters.get('framework', 'auto')
        test_path = parameters.get('path', '.')
        pattern = parameters.get('pattern', None)
        verbose = parameters.get('verbose', False)
        
        # Auto-detect test framework
        if test_framework == 'auto':
            test_framework = await self._detect_test_framework(workspace_path)
        
        if test_framework == 'pytest':
            return await self._run_pytest(workspace_path, test_path, pattern, verbose)
        elif test_framework == 'unittest':
            return await self._run_unittest(workspace_path, test_path, pattern, verbose)
        else:
            raise ValueError(f"Unsupported test framework: {test_framework}")
    
    async def _detect_test_framework(self, workspace_path: str) -> str:
        """Auto-detect which test framework to use"""
        workspace = Path(workspace_path)
        
        # Check for pytest configuration
        pytest_files = ['pytest.ini', 'pyproject.toml', 'setup.cfg']
        for config_file in pytest_files:
            if (workspace / config_file).exists():
                return 'pytest'
        
        # Check for pytest in requirements
        req_files = ['requirements.txt', 'requirements-dev.txt', 'requirements-test.txt']
        for req_file in req_files:
            req_path = workspace / req_file
            if req_path.exists():
                content = req_path.read_text()
                if 'pytest' in content.lower():
                    return 'pytest'
        
        # Check if pytest is available
        try:
            result = await self._run_command(['python', '-m', 'pytest', '--version'], workspace_path)
            if result['returncode'] == 0:
                return 'pytest'
        except:
            pass
        
        # Default to unittest
        return 'unittest'
    
    async def _run_pytest(self, workspace_path: str, test_path: str, 
                         pattern: Optional[str], verbose: bool) -> Dict[str, Any]:
        """Run tests using pytest"""
        cmd = ['python', '-m', 'pytest']
        
        if verbose:
            cmd.append('-v')
        
        # Add JSON output for parsing
        cmd.extend(['--tb=short', '--json-report', '--json-report-file=test_results.json'])
        
        if pattern:
            cmd.extend(['-k', pattern])
        
        cmd.append(test_path)
        
        result = await self._run_command(cmd, workspace_path)
        
        # Parse JSON results if available
        json_results = None
        json_path = Path(workspace_path) / 'test_results.json'
        if json_path.exists():
            try:
                with open(json_path) as f:
                    json_results = json.load(f)
                json_path.unlink()  # Clean up
            except:
                pass
        
        return {
            'framework': 'pytest',
            'command': ' '.join(cmd),
            'returncode': result['returncode'],
            'stdout': result['stdout'],
            'stderr': result['stderr'],
            'execution_time': result['execution_time'],
            'parsed_results': json_results,
            'summary': self._parse_pytest_output(result['stdout'])
        }
    
    async def _run_unittest(self, workspace_path: str, test_path: str,
                           pattern: Optional[str], verbose: bool) -> Dict[str, Any]:
        """Run tests using unittest"""
        cmd = ['python', '-m', 'unittest']
        
        if verbose:
            cmd.append('-v')
        
        if pattern:
            cmd.extend(['discover', '-s', test_path, '-p', f'*{pattern}*'])
        else:
            cmd.extend(['discover', '-s', test_path])
        
        result = await self._run_command(cmd, workspace_path)
        
        return {
            'framework': 'unittest',
            'command': ' '.join(cmd),
            'returncode': result['returncode'],
            'stdout': result['stdout'],
            'stderr': result['stderr'],
            'execution_time': result['execution_time'],
            'summary': self._parse_unittest_output(result['stdout'] + result['stderr'])
        }
    
    async def _generate_tests(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test files for source code"""
        source_file = parameters.get('source_file')
        test_style = parameters.get('style', 'pytest')
        
        if not source_file:
            raise ValueError("Source file required for test generation")
        
        source_path = Path(workspace_path) / source_file
        if not source_path.exists():
            raise ValueError(f"Source file not found: {source_file}")
        
        # Analyze source code
        source_analysis = await self._analyze_source_code(source_path)
        
        # Generate test file
        test_content = await self._generate_test_content(source_analysis, test_style)
        
        # Determine test file path
        test_file_path = self._get_test_file_path(source_path, test_style)
        
        # Write test file
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        test_file_path.write_text(test_content)
        
        return {
            'action': 'generate',
            'source_file': str(source_file),
            'test_file': str(test_file_path.relative_to(workspace_path)),
            'test_style': test_style,
            'functions_found': len(source_analysis.get('functions', [])),
            'classes_found': len(source_analysis.get('classes', []))
        }
    
    async def _analyze_tests(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze existing test files"""
        test_path = parameters.get('path', 'tests')
        
        test_dir = Path(workspace_path) / test_path
        if not test_dir.exists():
            return {'error': f'Test directory not found: {test_path}'}
        
        test_files = []
        test_functions = 0
        
        # Find all test files
        for pattern in ['test_*.py', '*_test.py']:
            test_files.extend(test_dir.glob(f'**/{pattern}'))
        
        analysis = {
            'test_directory': str(test_path),
            'test_files': [],
            'total_test_functions': 0,
            'coverage_gaps': []
        }
        
        for test_file in test_files:
            file_analysis = await self._analyze_test_file(test_file)
            analysis['test_files'].append(file_analysis)
            analysis['total_test_functions'] += file_analysis['test_count']
        
        return analysis
    
    async def _run_coverage(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run test coverage analysis"""
        test_path = parameters.get('path', '.')
        source_path = parameters.get('source_path', '.')
        
        # Check if coverage is available
        try:
            await self._run_command(['python', '-m', 'coverage', '--version'], workspace_path)
        except:
            return {'error': 'Coverage.py not available. Install with: pip install coverage'}
        
        # Run coverage
        cmd = ['python', '-m', 'coverage', 'run', '-m', 'pytest', test_path]
        test_result = await self._run_command(cmd, workspace_path)
        
        if test_result['returncode'] != 0:
            return {
                'error': 'Test execution failed during coverage run',
                'output': test_result['stderr']
            }
        
        # Generate coverage report
        report_cmd = ['python', '-m', 'coverage', 'report', '--format=json']
        report_result = await self._run_command(report_cmd, workspace_path)
        
        coverage_data = {}
        if report_result['returncode'] == 0:
            try:
                coverage_data = json.loads(report_result['stdout'])
            except:
                pass
        
        return {
            'framework': 'coverage',
            'test_execution': test_result['returncode'] == 0,
            'coverage_data': coverage_data,
            'coverage_percent': coverage_data.get('totals', {}).get('percent_covered', 0)
        }
    
    async def _run_command(self, cmd: List[str], cwd: str) -> Dict[str, Any]:
        """Run a shell command and return results"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='replace'),
                'stderr': stderr.decode('utf-8', errors='replace'),
                'execution_time': execution_time
            }
        
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': asyncio.get_event_loop().time() - start_time
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output for summary"""
        lines = output.split('\n')
        
        # Look for result summary line
        for line in lines:
            if 'passed' in line or 'failed' in line or 'error' in line:
                # Parse patterns like "5 passed, 2 failed in 1.23s"
                passed = len(re.findall(r'(\d+) passed', line))
                failed = len(re.findall(r'(\d+) failed', line))
                errors = len(re.findall(r'(\d+) error', line))
                
                return {
                    'passed': passed,
                    'failed': failed,
                    'errors': errors,
                    'total': passed + failed + errors
                }
        
        return {'passed': 0, 'failed': 0, 'errors': 0, 'total': 0}
    
    def _parse_unittest_output(self, output: str) -> Dict[str, Any]:
        """Parse unittest output for summary"""
        lines = output.split('\n')
        
        for line in lines:
            if 'Ran' in line and 'test' in line:
                # Parse "Ran 5 tests in 1.234s"
                match = re.search(r'Ran (\d+) tests?', line)
                if match:
                    total = int(match.group(1))
                    
                    # Check for failures/errors in next lines
                    failed = 0
                    errors = 0
                    for next_line in lines[lines.index(line):]:
                        if 'FAILED' in next_line:
                            fail_match = re.search(r'failures=(\d+)', next_line)
                            err_match = re.search(r'errors=(\d+)', next_line)
                            if fail_match:
                                failed = int(fail_match.group(1))
                            if err_match:
                                errors = int(err_match.group(1))
                            break
                    
                    return {
                        'passed': total - failed - errors,
                        'failed': failed,
                        'errors': errors,
                        'total': total
                    }
        
        return {'passed': 0, 'failed': 0, 'errors': 0, 'total': 0}
    
    async def _analyze_source_code(self, source_path: Path) -> Dict[str, Any]:
        """Analyze source code to understand structure"""
        content = source_path.read_text()
        
        # Simple regex-based analysis (in production, use AST)
        functions = re.findall(r'def\s+(\w+)\s*\(', content)
        classes = re.findall(r'class\s+(\w+)\s*[\(:]', content)
        
        return {
            'file_path': str(source_path),
            'functions': functions,
            'classes': classes,
            'line_count': len(content.split('\n'))
        }
    
    async def _generate_test_content(self, analysis: Dict[str, Any], style: str) -> str:
        """Generate test file content"""
        if style == 'pytest':
            return self._generate_pytest_content(analysis)
        else:
            return self._generate_unittest_content(analysis)
    
    def _generate_pytest_content(self, analysis: Dict[str, Any]) -> str:
        """Generate pytest-style test content"""
        source_file = Path(analysis['file_path']).stem
        
        content = f'''"""
Tests for {source_file}.py

Auto-generated by NeuroForge Test Runner Plugin
"""

import pytest
from {source_file} import *


'''
        
        # Generate test functions
        for func_name in analysis['functions']:
            content += f'''def test_{func_name}():
    """Test {func_name} function"""
    # TODO: Implement test for {func_name}
    assert True  # Placeholder


'''
        
        # Generate test classes
        for class_name in analysis['classes']:
            content += f'''class Test{class_name}:
    """Test {class_name} class"""
    
    def test_init(self):
        """Test {class_name} initialization"""
        # TODO: Implement test for {class_name}.__init__
        assert True  # Placeholder


'''
        
        return content
    
    def _generate_unittest_content(self, analysis: Dict[str, Any]) -> str:
        """Generate unittest-style test content"""
        source_file = Path(analysis['file_path']).stem
        
        content = f'''"""
Tests for {source_file}.py

Auto-generated by NeuroForge Test Runner Plugin
"""

import unittest
from {source_file} import *


'''
        
        for class_name in analysis['classes']:
            content += f'''class Test{class_name}(unittest.TestCase):
    """Test {class_name} class"""
    
    def test_init(self):
        """Test {class_name} initialization"""
        # TODO: Implement test for {class_name}.__init__
        self.assertTrue(True)  # Placeholder


'''
        
        content += '''
if __name__ == '__main__':
    unittest.main()
'''
        
        return content
    
    def _get_test_file_path(self, source_path: Path, style: str) -> Path:
        """Determine test file path based on source file"""
        source_dir = source_path.parent
        source_name = source_path.stem
        
        # Look for existing test directory
        test_dirs = ['tests', 'test']
        test_dir = None
        
        for dirname in test_dirs:
            potential_dir = source_dir / dirname
            if potential_dir.exists():
                test_dir = potential_dir
                break
        
        if not test_dir:
            test_dir = source_dir / 'tests'
        
        return test_dir / f'test_{source_name}.py'
    
    async def _analyze_test_file(self, test_file: Path) -> Dict[str, Any]:
        """Analyze a single test file"""
        content = test_file.read_text()
        
        # Count test functions
        test_functions = len(re.findall(r'def\s+test_\w+', content))
        
        return {
            'file_path': str(test_file),
            'test_count': test_functions,
            'line_count': len(content.split('\n'))
        }
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate test runner parameters"""
        action = parameters.get('action', 'run')
        
        if action not in ['run', 'generate', 'analyze', 'coverage']:
            return False
        
        if action == 'generate' and not parameters.get('source_file'):
            return False
        
        return True
    
    def get_capabilities(self) -> List[str]:
        return ['test', 'pytest', 'unittest', 'coverage', 'generation', 'automation']


# Example usage
async def test_runner_example():
    """Test the test runner plugin"""
    from ..memory_engine import MemoryEngine, MemoryConfig
    
    config = MemoryConfig(workspace_path="/tmp/test_workspace")
    memory_engine = MemoryEngine(config)
    
    plugin = TestRunnerPlugin(memory_engine)
    
    context = {
        'workspace': {'workspace_path': '/tmp/test_workspace'}
    }
    
    # Test running tests
    try:
        result = await plugin.execute({'action': 'run'}, context)
        print(f"Test run result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    memory_engine.close()


if __name__ == "__main__":
    asyncio.run(test_runner_example())
