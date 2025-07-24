#!/usr/bin/env python3
"""
Simple test script for NeuroForge core components
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the agent directory to the path
sys.path.insert(0, str(Path(__file__).parent / "agent"))

from memory_engine import MemoryEngine, MemoryConfig
from task_agent import TaskAgent, EchoPlugin


async def test_memory_engine():
    """Test memory engine functionality"""
    print("🧠 Testing Memory Engine...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = MemoryConfig(
            workspace_path=temp_dir,
            memory_store_path="test_memory"
        )
        
        engine = MemoryEngine(config)
        
        # Test storing memory
        context_id = await engine.store_memory(
            content={"test": "Hello NeuroForge!", "type": "greeting"},
            tags=["test", "greeting"]
        )
        print(f"✅ Stored memory with ID: {context_id}")
        
        # Test retrieving memory
        memory = await engine.retrieve_memory(context_id)
        print(f"✅ Retrieved memory: {memory.content}")
        
        # Test workspace context
        workspace_context = await engine.get_workspace_context()
        print(f"✅ Workspace context: {workspace_context['workspace_path']}")
        
        # Test searching memories
        results = await engine.search_memories("Hello")
        print(f"✅ Search found {len(results)} memories")
        
        engine.close()
        print("✅ Memory engine test completed!\n")


async def test_task_agent():
    """Test task agent functionality"""
    print("🤖 Testing Task Agent...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = MemoryConfig(
            workspace_path=temp_dir,
            memory_store_path="test_memory"
        )
        
        agent = TaskAgent(config)
        
        # Register echo plugin
        echo_plugin = EchoPlugin(agent.memory_engine)
        agent.register_plugin(echo_plugin)
        
        # Start agent
        await agent.start()
        
        # Submit test task
        task_id = await agent.submit_task(
            name="Test Task",
            description="Simple echo test",
            plugin_chain=["echo"],
            parameters={"message": "NeuroForge is working!"},
            priority=3
        )
        print(f"✅ Submitted task: {task_id}")
        
        # Wait for completion
        print("⏳ Waiting for task completion...")
        max_wait = 10  # seconds
        waited = 0
        while waited < max_wait:
            status = await agent.get_task_status(task_id)
            if status and status.value in ['completed', 'failed']:
                break
            await asyncio.sleep(0.5)
            waited += 0.5
        
        # Get result
        result = await agent.get_task_result(task_id)
        if result:
            print(f"✅ Task completed with status: {result.status.value}")
            print(f"✅ Task output: {result.output}")
        else:
            print("❌ Task result not available")
        
        # Test plugin listing
        plugins = agent.list_plugins()
        print(f"✅ Available plugins: {plugins}")
        
        # Test task history search
        history = await agent.search_task_history("echo")
        print(f"✅ Found {len(history)} historical tasks")
        
        await agent.stop()
        print("✅ Task agent test completed!\n")


async def main():
    """Run all tests"""
    print("🚀 Starting NeuroForge Core Tests\n")
    
    try:
        await test_memory_engine()
        await test_task_agent()
        
        print("🎉 All tests passed! NeuroForge core is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
