"""
Git Integration Plugin for NeuroForge

Handles Git operations including auto-commit, diff analysis,
branch management, and repository state tracking.

Author: Muzan Sano
License: MIT
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

import git
from git.exc import GitError

from ..task_agent import PluginBase
from ..memory_engine import MemoryEngine


class GitAutoCommitPlugin(PluginBase):
    """Plugin for automated Git operations"""
    
    def __init__(self, memory_engine: MemoryEngine):
        super().__init__("git_autocommit", memory_engine)
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Git auto-commit operations"""
        workspace_path = context.get('workspace', {}).get('workspace_path')
        if not workspace_path:
            raise ValueError("No workspace path provided")
        
        action = parameters.get('action', 'status')
        result = {}
        
        try:
            repo = git.Repo(workspace_path)
            
            if action == 'status':
                result = await self._get_status(repo)
            elif action == 'commit':
                result = await self._auto_commit(repo, parameters)
            elif action == 'diff':
                result = await self._get_diff(repo, parameters)
            elif action == 'branch':
                result = await self._manage_branch(repo, parameters)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # Store Git operation in memory
            await self.memory_engine.store_memory(
                content={
                    'git_action': action,
                    'workspace': workspace_path,
                    'result': result,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                tags=['git', action, 'automation']
            )
            
            return result
        
        except GitError as e:
            raise ValueError(f"Git operation failed: {str(e)}")
    
    async def _get_status(self, repo: git.Repo) -> Dict[str, Any]:
        """Get current Git repository status"""
        return {
            'branch': repo.active_branch.name if not repo.head.is_detached else 'detached',
            'commit_hash': repo.head.commit.hexsha,
            'commit_message': repo.head.commit.message.strip(),
            'is_dirty': repo.is_dirty(),
            'untracked_files': repo.untracked_files,
            'modified_files': [item.a_path for item in repo.index.diff(None)],
            'staged_files': [item.a_path for item in repo.index.diff('HEAD')],
            'remote_url': repo.remotes.origin.url if repo.remotes else None
        }
    
    async def _auto_commit(self, repo: git.Repo, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform automated commit"""
        commit_message = parameters.get('message')
        if not commit_message:
            # Generate smart commit message based on changes
            commit_message = await self._generate_commit_message(repo)
        
        # Add files
        files_to_add = parameters.get('files', [])
        if not files_to_add:
            # Add all modified and untracked files
            repo.git.add(A=True)
        else:
            repo.index.add(files_to_add)
        
        # Check if there are changes to commit
        if not repo.index.diff('HEAD'):
            return {'status': 'no_changes', 'message': 'No changes to commit'}
        
        # Commit
        commit = repo.index.commit(commit_message)
        
        # Push if requested
        push_result = None
        if parameters.get('push', False) and repo.remotes:
            try:
                push_result = repo.remotes.origin.push()
            except Exception as e:
                push_result = f"Push failed: {str(e)}"
        
        return {
            'status': 'committed',
            'commit_hash': commit.hexsha,
            'message': commit_message,
            'files_committed': len(commit.stats.files),
            'push_result': push_result
        }
    
    async def _get_diff(self, repo: git.Repo, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get diff information"""
        diff_type = parameters.get('diff_type', 'working')
        max_lines = parameters.get('max_lines', 1000)
        
        if diff_type == 'working':
            # Working directory vs staged
            diff = repo.git.diff()
        elif diff_type == 'staged':
            # Staged vs HEAD
            diff = repo.git.diff('--cached')
        elif diff_type == 'head':
            # HEAD vs previous commit
            diff = repo.git.diff('HEAD~1')
        else:
            raise ValueError(f"Unknown diff type: {diff_type}")
        
        # Truncate if too long
        lines = diff.split('\n')
        if len(lines) > max_lines:
            lines = lines[:max_lines] + [f'... (truncated, {len(lines) - max_lines} lines omitted)']
            diff = '\n'.join(lines)
        
        return {
            'diff_type': diff_type,
            'diff': diff,
            'line_count': len(lines),
            'truncated': len(lines) > max_lines
        }
    
    async def _manage_branch(self, repo: git.Repo, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Manage Git branches"""
        branch_action = parameters.get('branch_action', 'list')
        
        if branch_action == 'list':
            branches = [str(branch) for branch in repo.branches]
            current = repo.active_branch.name if not repo.head.is_detached else None
            return {
                'action': 'list',
                'branches': branches,
                'current_branch': current
            }
        
        elif branch_action == 'create':
            branch_name = parameters.get('branch_name')
            if not branch_name:
                raise ValueError("Branch name required for create action")
            
            new_branch = repo.create_head(branch_name)
            return {
                'action': 'create',
                'branch_name': branch_name,
                'branch_hash': new_branch.commit.hexsha
            }
        
        elif branch_action == 'checkout':
            branch_name = parameters.get('branch_name')
            if not branch_name:
                raise ValueError("Branch name required for checkout action")
            
            repo.git.checkout(branch_name)
            return {
                'action': 'checkout',
                'branch_name': branch_name,
                'current_branch': repo.active_branch.name
            }
        
        else:
            raise ValueError(f"Unknown branch action: {branch_action}")
    
    async def _generate_commit_message(self, repo: git.Repo) -> str:
        """Generate intelligent commit message based on changes"""
        # Get file changes
        modified_files = [item.a_path for item in repo.index.diff(None)]
        staged_files = [item.a_path for item in repo.index.diff('HEAD')]
        untracked_files = repo.untracked_files
        
        all_files = list(set(modified_files + staged_files + list(untracked_files)))
        
        if not all_files:
            return "Auto-commit: No significant changes"
        
        # Analyze file types and patterns
        file_types = {}
        for file_path in all_files:
            ext = Path(file_path).suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Generate message based on patterns
        if len(all_files) == 1:
            return f"Auto-commit: Update {all_files[0]}"
        
        if '.py' in file_types and file_types['.py'] > len(all_files) * 0.7:
            return f"Auto-commit: Update Python code ({len(all_files)} files)"
        
        if '.md' in file_types:
            return f"Auto-commit: Update documentation ({len(all_files)} files)"
        
        if '.json' in file_types or '.yaml' in file_types or '.yml' in file_types:
            return f"Auto-commit: Update configuration ({len(all_files)} files)"
        
        return f"Auto-commit: Update {len(all_files)} files"
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate Git plugin parameters"""
        action = parameters.get('action', 'status')
        
        if action not in ['status', 'commit', 'diff', 'branch']:
            return False
        
        if action == 'branch':
            branch_action = parameters.get('branch_action', 'list')
            if branch_action not in ['list', 'create', 'checkout']:
                return False
            
            if branch_action in ['create', 'checkout'] and not parameters.get('branch_name'):
                return False
        
        return True
    
    def get_capabilities(self) -> List[str]:
        return ['git', 'commit', 'diff', 'branch', 'automation', 'vcs']


# Example usage function for testing
async def test_git_plugin():
    """Test the Git plugin"""
    from ..memory_engine import MemoryEngine, MemoryConfig
    
    config = MemoryConfig(workspace_path="/tmp/test_repo")
    memory_engine = MemoryEngine(config)
    
    plugin = GitAutoCommitPlugin(memory_engine)
    
    # Test parameters
    context = {
        'workspace': {'workspace_path': '/tmp/test_repo'}
    }
    
    # Test Git status
    try:
        result = await plugin.execute({'action': 'status'}, context)
        print(f"Git status: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    memory_engine.close()


if __name__ == "__main__":
    asyncio.run(test_git_plugin())
