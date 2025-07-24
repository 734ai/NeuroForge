"""
NeuroForge Task Agent

Main orchestration agent for task execution, plugin management,
and context-aware automation within VSCode workspaces.

Author: Muzan Sano
License: MIT
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timezone
from enum import Enum

from memory_engine import MemoryEngine, MemoryConfig, MemoryContext


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    status: TaskStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_contexts: List[str] = None  # IDs of created memory contexts


@dataclass 
class Task:
    """Represents a task to be executed"""
    id: str
    name: str
    description: str
    plugin_chain: List[str]  # Ordered list of plugins to execute
    parameters: Dict[str, Any]
    priority: int = 1  # 1=low, 5=high
    created_at: datetime = None
    context_id: Optional[str] = None  # Associated memory context
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class PluginBase:
    """Base class for all task plugins"""
    
    def __init__(self, name: str, memory_engine: MemoryEngine):
        self.name = name
        self.memory_engine = memory_engine
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin action"""
        raise NotImplementedError
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate plugin parameters"""
        return True
    
    def get_capabilities(self) -> List[str]:
        """Return list of plugin capabilities"""
        return []


class TaskQueue:
    """Async task queue with priority scheduling"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, TaskResult] = {}
        self._running_event = asyncio.Event()
    
    async def add_task(self, task: Task) -> None:
        """Add task to queue"""
        # Priority queue uses negative priority for max-heap behavior
        await self._queue.put((-task.priority, task.created_at, task))
    
    async def get_next_task(self) -> Optional[Task]:
        """Get next task from queue"""
        try:
            _, _, task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            return task
        except asyncio.TimeoutError:
            return None
    
    def is_running(self, task_id: str) -> bool:
        """Check if task is currently running"""
        return task_id in self._running
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result"""
        return self._results.get(task_id)
    
    def add_result(self, result: TaskResult) -> None:
        """Store task result"""
        self._results[result.task_id] = result
        if result.task_id in self._running:
            del self._running[result.task_id]
    
    def add_running_task(self, task_id: str, async_task: asyncio.Task) -> None:
        """Register running task"""
        self._running[task_id] = async_task
    
    @property
    def queue_size(self) -> int:
        """Get current queue size"""
        return self._queue.qsize()
    
    @property
    def running_count(self) -> int:
        """Get number of running tasks"""
        return len(self._running)


class PluginManager:
    """Manages plugin registration and execution"""
    
    def __init__(self, memory_engine: MemoryEngine):
        self.memory_engine = memory_engine
        self._plugins: Dict[str, PluginBase] = {}
        self._capabilities: Dict[str, List[str]] = {}
    
    def register_plugin(self, plugin: PluginBase) -> None:
        """Register a new plugin"""
        self._plugins[plugin.name] = plugin
        self._capabilities[plugin.name] = plugin.get_capabilities()
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get plugin by name"""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins"""
        return list(self._plugins.keys())
    
    def find_plugins_by_capability(self, capability: str) -> List[str]:
        """Find plugins that have a specific capability"""
        matching = []
        for plugin_name, caps in self._capabilities.items():
            if capability in caps:
                matching.append(plugin_name)
        return matching
    
    async def execute_plugin(self, plugin_name: str, parameters: Dict[str, Any], 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific plugin"""
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        # Validate parameters
        if not await plugin.validate_parameters(parameters):
            raise ValueError(f"Invalid parameters for plugin '{plugin_name}'")
        
        # Execute plugin
        return await plugin.execute(parameters, context)


class TaskAgent:
    """Main task agent for orchestrating execution"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.memory_engine = MemoryEngine(config)
        self.plugin_manager = PluginManager(self.memory_engine)
        self.task_queue = TaskQueue()
        self._executor_running = False
        self._executor_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the task agent"""
        if not self._executor_running:
            self._executor_running = True
            self._executor_task = asyncio.create_task(self._task_executor())
    
    async def stop(self) -> None:
        """Stop the task agent"""
        self._executor_running = False
        if self._executor_task:
            self._executor_task.cancel()
            try:
                await self._executor_task
            except asyncio.CancelledError:
                pass
        
        self.memory_engine.close()
    
    async def submit_task(self, name: str, description: str, plugin_chain: List[str],
                         parameters: Dict[str, Any], priority: int = 1) -> str:
        """Submit a new task for execution"""
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            plugin_chain=plugin_chain,
            parameters=parameters,
            priority=priority
        )
        
        # Store task context in memory
        task_context = {
            'task_id': task.id,
            'name': task.name,
            'description': task.description,
            'plugins': task.plugin_chain,
            'parameters': task.parameters,
            'status': TaskStatus.PENDING.value
        }
        
        context_id = await self.memory_engine.store_memory(
            content=task_context,
            tags=['task', 'pending']
        )
        task.context_id = context_id
        
        await self.task_queue.add_task(task)
        return task.id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current status of a task"""
        # Check if running
        if self.task_queue.is_running(task_id):
            return TaskStatus.RUNNING
        
        # Check results
        result = self.task_queue.get_result(task_id)
        if result:
            return result.status
        
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task execution result"""
        return self.task_queue.get_result(task_id)
    
    async def execute_task_chain(self, task: Task) -> TaskResult:
        """Execute a complete task chain"""
        start_time = time.time()
        memory_contexts = []
        
        try:
            # Get workspace context
            workspace_context = await self.memory_engine.get_workspace_context()
            
            # Load task-specific context from memory
            task_memory = None
            if task.context_id:
                task_memory = await self.memory_engine.retrieve_memory(task.context_id)
            
            # Build execution context
            execution_context = {
                'task_id': task.id,
                'workspace': workspace_context,
                'task_memory': task_memory.content if task_memory else {},
                'parameters': task.parameters
            }
            
            # Execute plugin chain
            chain_output = {}
            for plugin_name in task.plugin_chain:
                plugin_result = await self.plugin_manager.execute_plugin(
                    plugin_name, task.parameters, execution_context
                )
                
                # Update context with plugin output
                execution_context[f'{plugin_name}_output'] = plugin_result
                chain_output[plugin_name] = plugin_result
                
                # Store intermediate result in memory
                intermediate_context = {
                    'task_id': task.id,
                    'plugin': plugin_name,
                    'output': plugin_result,
                    'step': len(chain_output)
                }
                
                context_id = await self.memory_engine.store_memory(
                    content=intermediate_context,
                    tags=['task', 'plugin_output', plugin_name]
                )
                memory_contexts.append(context_id)
            
            # Store final result
            final_context = {
                'task_id': task.id,
                'status': 'completed',
                'final_output': chain_output,
                'execution_time': time.time() - start_time
            }
            
            final_context_id = await self.memory_engine.store_memory(
                content=final_context,
                tags=['task', 'completed', task.name]
            )
            memory_contexts.append(final_context_id)
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                output=chain_output,
                execution_time=time.time() - start_time,
                memory_contexts=memory_contexts
            )
        
        except Exception as e:
            # Store error context
            error_context = {
                'task_id': task.id,
                'status': 'failed',
                'error': str(e),
                'execution_time': time.time() - start_time
            }
            
            error_context_id = await self.memory_engine.store_memory(
                content=error_context,
                tags=['task', 'failed', 'error']
            )
            memory_contexts.append(error_context_id)
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time,
                memory_contexts=memory_contexts
            )
    
    async def _task_executor(self) -> None:
        """Main task execution loop"""
        while self._executor_running:
            try:
                # Check if we can run more tasks
                if self.task_queue.running_count >= self.task_queue.max_concurrent:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get next task
                task = await self.task_queue.get_next_task()
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # Execute task asynchronously
                async_task = asyncio.create_task(self.execute_task_chain(task))
                self.task_queue.add_running_task(task.id, async_task)
                
                # Set up callback to handle completion
                async_task.add_done_callback(
                    lambda t, task_id=task.id: asyncio.create_task(
                        self._handle_task_completion(task_id, t)
                    )
                )
                
            except Exception as e:
                print(f"Error in task executor: {e}")
                await asyncio.sleep(1.0)
    
    async def _handle_task_completion(self, task_id: str, async_task: asyncio.Task) -> None:
        """Handle task completion"""
        try:
            result = await async_task
            self.task_queue.add_result(result)
        except Exception as e:
            # Create error result
            error_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                output=None,
                error=str(e)
            )
            self.task_queue.add_result(error_result)
    
    def register_plugin(self, plugin: PluginBase) -> None:
        """Register a new plugin"""
        self.plugin_manager.register_plugin(plugin)
    
    def list_plugins(self) -> List[str]:
        """List all available plugins"""
        return self.plugin_manager.list_plugins()
    
    async def search_task_history(self, query: str, limit: int = 10) -> List[MemoryContext]:
        """Search previous task executions"""
        return await self.memory_engine.search_memories(
            query, tags=['task'], limit=limit
        )


# Example plugin implementation
class EchoPlugin(PluginBase):
    """Simple echo plugin for testing"""
    
    def __init__(self, memory_engine: MemoryEngine):
        super().__init__("echo", memory_engine)
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        message = parameters.get('message', 'Hello from NeuroForge!')
        return {
            'echo': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'context_keys': list(context.keys())
        }
    
    def get_capabilities(self) -> List[str]:
        return ['echo', 'test', 'demo']


# Example usage
async def main():
    """Test the task agent"""
    config = MemoryConfig(
        workspace_path="/tmp/test_workspace",
        memory_store_path="test_memory"
    )
    
    agent = TaskAgent(config)
    
    # Register test plugin
    echo_plugin = EchoPlugin(agent.memory_engine)
    agent.register_plugin(echo_plugin)
    
    # Start agent
    await agent.start()
    
    # Submit test task
    task_id = await agent.submit_task(
        name="Test Echo Task",
        description="Simple echo test",
        plugin_chain=["echo"],
        parameters={"message": "Hello NeuroForge!"},
        priority=3
    )
    
    print(f"Submitted task: {task_id}")
    
    # Wait for completion
    while True:
        status = await agent.get_task_status(task_id)
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            break
        await asyncio.sleep(0.1)
    
    # Get result
    result = await agent.get_task_result(task_id)
    print(f"Task result: {result}")
    
    # Search task history
    history = await agent.search_task_history("echo")
    print(f"Found {len(history)} historical tasks")
    
    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
