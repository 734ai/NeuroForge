"""
Documentation Writer Plugin for NeuroForge

Handles automatic documentation generation, README updates,
API documentation, and code comment analysis.

Author: Muzan Sano
License: MIT
"""

import asyncio
import re
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from ..task_agent import PluginBase
from ..memory_engine import MemoryEngine


class DocWriterPlugin(PluginBase):
    """Plugin for automated documentation operations"""
    
    def __init__(self, memory_engine: MemoryEngine):
        super().__init__("doc_writer", memory_engine)
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation operations"""
        workspace_path = context.get('workspace', {}).get('workspace_path')
        if not workspace_path:
            raise ValueError("No workspace path provided")
        
        action = parameters.get('action', 'analyze')
        result = {}
        
        try:
            if action == 'analyze':
                result = await self._analyze_code_docs(workspace_path, parameters)
            elif action == 'generate':
                result = await self._generate_docs(workspace_path, parameters)
            elif action == 'update_readme':
                result = await self._update_readme(workspace_path, parameters)
            elif action == 'api_docs':
                result = await self._generate_api_docs(workspace_path, parameters)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # Store documentation operation in memory
            await self.memory_engine.store_memory(
                content={
                    'doc_action': action,
                    'workspace': workspace_path,
                    'result': result,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                tags=['documentation', action, 'automation']
            )
            
            return result
        
        except Exception as e:
            raise ValueError(f"Documentation operation failed: {str(e)}")
    
    async def _analyze_code_docs(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze existing code documentation"""
        target_path = parameters.get('path', '.')
        file_extensions = parameters.get('extensions', ['.py', '.js', '.ts'])
        
        workspace = Path(workspace_path)
        target_dir = workspace / target_path
        
        if not target_dir.exists():
            raise ValueError(f"Target path not found: {target_path}")
        
        analysis = {
            'total_files': 0,
            'documented_files': 0,
            'undocumented_files': [],
            'functions_without_docs': [],
            'classes_without_docs': [],
            'doc_coverage_percent': 0.0
        }
        
        for ext in file_extensions:
            for file_path in target_dir.rglob(f'*{ext}'):
                if self._should_skip_file(file_path):
                    continue
                
                analysis['total_files'] += 1
                file_analysis = await self._analyze_file_docs(file_path)
                
                if file_analysis['has_module_doc']:
                    analysis['documented_files'] += 1
                else:
                    analysis['undocumented_files'].append(str(file_path.relative_to(workspace)))
                
                analysis['functions_without_docs'].extend([
                    {'file': str(file_path.relative_to(workspace)), 'function': func}
                    for func in file_analysis['undocumented_functions']
                ])
                
                analysis['classes_without_docs'].extend([
                    {'file': str(file_path.relative_to(workspace)), 'class': cls}
                    for cls in file_analysis['undocumented_classes']
                ])
        
        if analysis['total_files'] > 0:
            analysis['doc_coverage_percent'] = (
                analysis['documented_files'] / analysis['total_files']
            ) * 100
        
        return analysis
    
    async def _generate_docs(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation for code files"""
        target_file = parameters.get('file')
        doc_style = parameters.get('style', 'google')  # google, numpy, sphinx
        
        if not target_file:
            raise ValueError("Target file required for documentation generation")
        
        file_path = Path(workspace_path) / target_file
        if not file_path.exists():
            raise ValueError(f"Target file not found: {target_file}")
        
        # Analyze file structure
        file_analysis = await self._analyze_file_structure(file_path)
        
        # Generate documentation
        updated_content = await self._add_docstrings(file_path, file_analysis, doc_style)
        
        # Create backup and write new content
        backup_path = file_path.with_suffix(f'{file_path.suffix}.bak')
        backup_path.write_text(file_path.read_text())
        file_path.write_text(updated_content)
        
        return {
            'action': 'generate',
            'file': target_file,
            'backup_created': str(backup_path.relative_to(workspace_path)),
            'functions_documented': len(file_analysis['functions']),
            'classes_documented': len(file_analysis['classes']),
            'doc_style': doc_style
        }
    
    async def _update_readme(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update or generate README file"""
        readme_path = Path(workspace_path) / 'README.md'
        project_name = parameters.get('project_name', Path(workspace_path).name)
        include_api = parameters.get('include_api', True)
        
        # Analyze project structure
        project_analysis = await self._analyze_project_structure(workspace_path)
        
        # Generate README content
        readme_content = await self._generate_readme_content(
            project_name, project_analysis, include_api
        )
        
        # Backup existing README if it exists
        backup_created = False
        if readme_path.exists():
            backup_path = readme_path.with_suffix('.md.bak')
            backup_path.write_text(readme_path.read_text())
            backup_created = True
        
        # Write new README
        readme_path.write_text(readme_content)
        
        return {
            'action': 'update_readme',
            'readme_path': 'README.md',
            'backup_created': backup_created,
            'sections_generated': ['installation', 'usage', 'api', 'contributing'],
            'project_structure_analyzed': True
        }
    
    async def _generate_api_docs(self, workspace_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API documentation"""
        output_format = parameters.get('format', 'markdown')  # markdown, html, json
        target_path = parameters.get('path', '.')
        
        workspace = Path(workspace_path)
        api_docs = {
            'modules': [],
            'classes': [],
            'functions': []
        }
        
        # Scan for Python files
        for py_file in (workspace / target_path).rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
            
            module_docs = await self._extract_api_from_file(py_file, workspace)
            api_docs['modules'].append(module_docs)
            api_docs['classes'].extend(module_docs['classes'])
            api_docs['functions'].extend(module_docs['functions'])
        
        # Generate documentation file
        if output_format == 'markdown':
            doc_content = await self._generate_markdown_api_docs(api_docs)
            output_file = workspace / 'API.md'
        elif output_format == 'html':
            doc_content = await self._generate_html_api_docs(api_docs)
            output_file = workspace / 'api.html'
        else:  # json
            import json
            doc_content = json.dumps(api_docs, indent=2)
            output_file = workspace / 'api.json'
        
        output_file.write_text(doc_content)
        
        return {
            'action': 'api_docs',
            'format': output_format,
            'output_file': str(output_file.relative_to(workspace)),
            'modules_documented': len(api_docs['modules']),
            'classes_documented': len(api_docs['classes']),
            'functions_documented': len(api_docs['functions'])
        }
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis"""
        skip_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            '.pytest_cache',
            'venv',
            '.venv',
            'build',
            'dist'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    async def _analyze_file_docs(self, file_path: Path) -> Dict[str, Any]:
        """Analyze documentation coverage for a single file"""
        content = file_path.read_text()
        
        # Check for module-level docstring
        has_module_doc = False
        lines = content.split('\n')
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                has_module_doc = True
                break
        
        # Find functions and classes without docstrings
        undocumented_functions = []
        undocumented_classes = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        undocumented_functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        undocumented_classes.append(node.name)
        except SyntaxError:
            # If we can't parse, fall back to regex
            func_matches = re.findall(r'def\s+(\w+)\s*\(', content)
            class_matches = re.findall(r'class\s+(\w+)\s*[\(:]', content)
            undocumented_functions = func_matches
            undocumented_classes = class_matches
        
        return {
            'has_module_doc': has_module_doc,
            'undocumented_functions': undocumented_functions,
            'undocumented_classes': undocumented_classes
        }
    
    async def _analyze_file_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file structure for documentation generation"""
        content = file_path.read_text()
        
        try:
            tree = ast.parse(content)
            
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'has_docstring': ast.get_docstring(node) is not None,
                        'line_number': node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    class_methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_methods.append({
                                'name': item.name,
                                'args': [arg.arg for arg in item.args.args],
                                'has_docstring': ast.get_docstring(item) is not None
                            })
                    
                    classes.append({
                        'name': node.name,
                        'methods': class_methods,
                        'has_docstring': ast.get_docstring(node) is not None,
                        'line_number': node.lineno
                    })
            
            return {
                'functions': functions,
                'classes': classes,
                'imports': self._extract_imports(tree)
            }
        
        except SyntaxError:
            return {'functions': [], 'classes': [], 'imports': []}
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports
    
    async def _add_docstrings(self, file_path: Path, analysis: Dict[str, Any], 
                             style: str) -> str:
        """Add docstrings to file content"""
        content = file_path.read_text()
        lines = content.split('\n')
        
        # Insert docstrings in reverse order to maintain line numbers
        for func in reversed(analysis['functions']):
            if not func['has_docstring']:
                docstring = self._generate_function_docstring(func, style)
                # Insert after function definition line
                insert_line = func['line_number']
                lines.insert(insert_line, docstring)
        
        for cls in reversed(analysis['classes']):
            if not cls['has_docstring']:
                docstring = self._generate_class_docstring(cls, style)
                # Insert after class definition line
                insert_line = cls['line_number']
                lines.insert(insert_line, docstring)
        
        return '\n'.join(lines)
    
    def _generate_function_docstring(self, func: Dict[str, Any], style: str) -> str:
        """Generate docstring for a function"""
        name = func['name']
        args = func['args']
        
        if style == 'google':
            docstring = f'    """{name} function\n\n'
            if args:
                docstring += '    Args:\n'
                for arg in args:
                    if arg != 'self':
                        docstring += f'        {arg}: Description of {arg}\n'
            docstring += '\n    Returns:\n        Description of return value\n    """'
        else:  # Default to simple style
            docstring = f'    """{name} function"""'
        
        return docstring
    
    def _generate_class_docstring(self, cls: Dict[str, Any], style: str) -> str:
        """Generate docstring for a class"""
        name = cls['name']
        
        if style == 'google':
            docstring = f'    """{name} class\n\n'
            docstring += f'    A class for {name.lower()} operations.\n'
            if cls['methods']:
                docstring += '\n    Methods:\n'
                for method in cls['methods']:
                    if method['name'] != '__init__':
                        docstring += f'        {method["name"]}: {method["name"]} method\n'
            docstring += '    """'
        else:
            docstring = f'    """{name} class"""'
        
        return docstring
    
    async def _analyze_project_structure(self, workspace_path: str) -> Dict[str, Any]:
        """Analyze overall project structure"""
        workspace = Path(workspace_path)
        
        analysis = {
            'project_name': workspace.name,
            'has_setup_py': (workspace / 'setup.py').exists(),
            'has_requirements': (workspace / 'requirements.txt').exists(),
            'has_tests': any(workspace.rglob('test*')),
            'main_modules': [],
            'scripts': []
        }
        
        # Find main Python modules
        for py_file in workspace.glob('*.py'):
            if py_file.name not in ['setup.py', '__init__.py']:
                analysis['main_modules'].append(py_file.name)
        
        # Find script directories
        for subdir in workspace.iterdir():
            if subdir.is_dir() and subdir.name in ['bin', 'scripts']:
                analysis['scripts'].extend([f.name for f in subdir.iterdir() if f.is_file()])
        
        return analysis
    
    async def _generate_readme_content(self, project_name: str, 
                                     analysis: Dict[str, Any], include_api: bool) -> str:
        """Generate README.md content"""
        content = f"""# {project_name}

> A Python project built with NeuroForge automation

## 📋 Description

{project_name} is a Python application that provides [brief description of functionality].

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd {project_name.lower()}

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
"""
        
        if analysis['has_requirements']:
            content += "pip install -r requirements.txt\n"
        else:
            content += "pip install -e .\n"
        
        content += """```

## 💻 Usage

### Basic Usage
```python
# Example usage
from {module} import {class}

# Initialize and use
instance = {class}()
result = instance.method()
print(result)
```

## 📁 Project Structure
```
{project}/
├── {main_modules}
├── tests/
├── requirements.txt
└── README.md
```

## 🧪 Testing

Run the test suite:
```bash
pytest
# or
python -m unittest discover
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Generated automatically by NeuroForge Documentation Writer*
""".format(
            module=analysis['main_modules'][0].replace('.py', '') if analysis['main_modules'] else 'main',
            class='MainClass',
            project=project_name,
            main_modules='\n├── '.join(analysis['main_modules']) if analysis['main_modules'] else 'main.py'
        )
        
        return content
    
    async def _extract_api_from_file(self, file_path: Path, workspace: Path) -> Dict[str, Any]:
        """Extract API information from a Python file"""
        content = file_path.read_text()
        module_name = str(file_path.relative_to(workspace)).replace('/', '.').replace('.py', '')
        
        try:
            tree = ast.parse(content)
            
            module_doc = ast.get_docstring(tree)
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'docstring': ast.get_docstring(node),
                        'methods': [],
                        'module': module_name
                    }
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                'name': item.name,
                                'docstring': ast.get_docstring(item),
                                'args': [arg.arg for arg in item.args.args]
                            }
                            class_info['methods'].append(method_info)
                    
                    classes.append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'docstring': ast.get_docstring(node),
                        'args': [arg.arg for arg in node.args.args],
                        'module': module_name
                    }
                    functions.append(func_info)
            
            return {
                'module': module_name,
                'docstring': module_doc,
                'classes': classes,
                'functions': functions
            }
        
        except SyntaxError:
            return {
                'module': module_name,
                'docstring': None,
                'classes': [],
                'functions': []
            }
    
    async def _generate_markdown_api_docs(self, api_docs: Dict[str, Any]) -> str:
        """Generate markdown API documentation"""
        content = "# API Documentation\n\n"
        
        # Modules overview
        content += "## Modules\n\n"
        for module in api_docs['modules']:
            content += f"### {module['module']}\n"
            if module['docstring']:
                content += f"{module['docstring']}\n\n"
            else:
                content += "Module documentation not available.\n\n"
        
        # Classes
        if api_docs['classes']:
            content += "## Classes\n\n"
            for cls in api_docs['classes']:
                content += f"### {cls['name']}\n"
                content += f"**Module:** `{cls['module']}`\n\n"
                if cls['docstring']:
                    content += f"{cls['docstring']}\n\n"
                
                if cls['methods']:
                    content += "#### Methods\n\n"
                    for method in cls['methods']:
                        content += f"##### {method['name']}({', '.join(method['args'])})\n"
                        if method['docstring']:
                            content += f"{method['docstring']}\n\n"
                        else:
                            content += "Method documentation not available.\n\n"
        
        # Functions
        if api_docs['functions']:
            content += "## Functions\n\n"
            for func in api_docs['functions']:
                content += f"### {func['name']}({', '.join(func['args'])})\n"
                content += f"**Module:** `{func['module']}`\n\n"
                if func['docstring']:
                    content += f"{func['docstring']}\n\n"
                else:
                    content += "Function documentation not available.\n\n"
        
        content += "\n---\n*Generated automatically by NeuroForge Documentation Writer*\n"
        return content
    
    async def _generate_html_api_docs(self, api_docs: Dict[str, Any]) -> str:
        """Generate HTML API documentation"""
        # Simple HTML generation - in production, use proper templating
        html = """<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .module { margin-bottom: 30px; }
        .class { margin-bottom: 20px; border-left: 3px solid #007acc; padding-left: 15px; }
        .method { margin-left: 20px; margin-bottom: 10px; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>API Documentation</h1>
"""
        
        # Add classes
        for cls in api_docs['classes']:
            html += f'<div class="class"><h2>{cls["name"]}</h2>'
            if cls['docstring']:
                html += f'<p>{cls["docstring"]}</p>'
            
            for method in cls['methods']:
                html += f'<div class="method"><h3>{method["name"]}</h3>'
                if method['docstring']:
                    html += f'<p>{method["docstring"]}</p>'
                html += '</div>'
            
            html += '</div>'
        
        html += """
</body>
</html>"""
        return html
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate documentation plugin parameters"""
        action = parameters.get('action', 'analyze')
        
        if action not in ['analyze', 'generate', 'update_readme', 'api_docs']:
            return False
        
        if action == 'generate' and not parameters.get('file'):
            return False
        
        return True
    
    def get_capabilities(self) -> List[str]:
        return ['documentation', 'readme', 'docstring', 'api_docs', 'analysis', 'automation']


# Example usage
async def test_doc_writer():
    """Test the documentation writer plugin"""
    from ..memory_engine import MemoryEngine, MemoryConfig
    
    config = MemoryConfig(workspace_path="/tmp/test_workspace")
    memory_engine = MemoryEngine(config)
    
    plugin = DocWriterPlugin(memory_engine)
    
    context = {
        'workspace': {'workspace_path': '/tmp/test_workspace'}
    }
    
    # Test documentation analysis
    try:
        result = await plugin.execute({'action': 'analyze'}, context)
        print(f"Documentation analysis: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    memory_engine.close()


if __name__ == "__main__":
    asyncio.run(test_doc_writer())
