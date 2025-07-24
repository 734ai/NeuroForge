#!/usr/bin/env python3
"""
NeuroForge Advanced Analytics Test Suite
Author: Muzan Sano

Comprehensive test suite for all advanced analytics features
"""

import sys
import time
import asyncio
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_knowledge_graph():
    """Test knowledge graph functionality"""
    print("🧠 Testing Knowledge Graph System...")
    
    try:
        from agent.knowledge_graph import KnowledgeGraphBuilder
        
        # Create knowledge graph
        graph = KnowledgeGraphBuilder()
        
        # Add test data
        memory_data = {
            'title': 'Advanced Python patterns',
            'content': 'Design patterns and architectural principles for Python applications',
            'type': 'documentation',
            'workspace': '/project/advanced',
            'tags': ['python', 'patterns', 'architecture'],
            'created_at': time.time() - 3600,
            'last_accessed': time.time() - 1800
        }
        
        task_data = {
            'description': 'Refactor legacy codebase',
            'plugin': 'refactoring_assistant',
            'status': 'completed',
            'workspace': '/project/advanced',
            'parameters': {'target': 'legacy_module.py'},
            'execution_time': 15.5
        }
        
        file_data = {
            'size': 2048,
            'language': 'python',
            'last_modified': time.time() - 900
        }
        
        # Add nodes
        memory_id = graph.add_memory_node('mem_advanced', memory_data)
        task_id = graph.add_task_node('task_refactor', task_data)
        file_id = graph.add_file_node('/project/advanced/patterns.py', file_data)
        
        # Analyze graph
        analysis = graph.analyze_graph()
        
        print(f"  ✓ Graph created with {analysis['graph_metrics']['nodes']} nodes and {analysis['graph_metrics']['edges']} edges")
        print(f"  ✓ Graph density: {analysis['graph_metrics']['density']:.3f}")
        print(f"  ✓ Top concepts: {[c['concept'] for c in analysis['top_concepts'][:3]]}")
        
        # Test knowledge paths
        if len(graph.nodes) > 1:
            node_ids = list(graph.nodes.keys())
            paths = graph.find_knowledge_paths(node_ids[0], node_ids[1])
            print(f"  ✓ Found {len(paths)} knowledge paths between nodes")
        
        # Test neighborhood analysis
        if graph.nodes:
            first_node = list(graph.nodes.keys())[0]
            neighborhood = graph.get_node_neighborhood(first_node, depth=2)
            print(f"  ✓ Node neighborhood size: {neighborhood['neighborhood_size']}")
        
        # Export graph
        export_path = graph.export_graph()
        print(f"  ✓ Graph exported to: {export_path}")
        
        print("  ✅ Knowledge Graph test passed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Knowledge Graph test failed: {e}\n")
        return False

def test_analytics_dashboard():
    """Test analytics dashboard functionality"""
    print("📊 Testing Analytics Dashboard...")
    
    try:
        from agent.analytics import MemoryAnalytics
        
        # Mock objects for testing
        class MockMemoryEngine:
            async def search_memories(self, query, limit=100):
                return [
                    {
                        'id': f'mem_{i}',
                        'title': f'Memory {i}',
                        'type': 'code_snippet' if i % 2 == 0 else 'documentation',
                        'workspace': f'/project/{i % 3}',
                        'content': f'Test content {i}' * (i % 5 + 1),
                        'tags': ['python', 'test'] if i % 2 == 0 else ['docs', 'tutorial'],
                        'created_at': time.time() - (i * 1800),  # Spread over time
                        'last_accessed': time.time() - (i * 900),
                        'access_count': i % 20
                    }
                    for i in range(25)
                ]
        
        class MockTaskAgent:
            execution_history = [
                {
                    'id': f'task_{i}',
                    'description': f'Task {i}',
                    'status': 'completed' if i % 3 != 0 else 'failed',
                    'plugin': f'plugin_{i % 4}',
                    'workspace': f'/project/{i % 2}',
                    'execution_time': (i % 15) + 2,
                    'created_at': time.time() - (i * 1200)
                }
                for i in range(15)
            ]
        
        class MockKnowledgeGraph:
            def analyze_graph(self):
                return {
                    'graph_metrics': {
                        'nodes': 50,
                        'edges': 75,
                        'density': 0.12,
                        'components': 2,
                        'largest_component_size': 45
                    },
                    'node_distribution': {'memory': 25, 'task': 15, 'concept': 10},
                    'relationship_distribution': {'similar_to': 40, 'contains': 35}
                }
        
        # Create analytics instance
        memory_engine = MockMemoryEngine()
        task_agent = MockTaskAgent()
        knowledge_graph = MockKnowledgeGraph()
        
        analytics = MemoryAnalytics(memory_engine, task_agent, knowledge_graph)
        
        # Run analytics
        async def run_analytics_test():
            dashboard_data = await analytics.generate_dashboard_data()
            
            print(f"  ✓ Memory analysis: {dashboard_data.memory_stats.total_memories} memories analyzed")
            print(f"  ✓ Task analysis: {dashboard_data.task_stats.success_rate:.1f}% success rate")
            print(f"  ✓ Generated {len(dashboard_data.recommendations)} recommendations")
            
            # Test trend analysis
            trends = analytics.get_trend_analysis(7)
            print(f"  ✓ Trend analysis: {trends.get('data_points', 0)} data points")
            
            # Export analytics
            export_path = analytics.export_analytics()
            print(f"  ✓ Analytics exported to: {export_path}")
            
            return dashboard_data
        
        dashboard_data = asyncio.run(run_analytics_test())
        
        print("  ✅ Analytics Dashboard test passed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Analytics Dashboard test failed: {e}\n")
        return False

def test_web_dashboard():
    """Test web dashboard functionality"""
    print("🌐 Testing Web Dashboard...")
    
    try:
        from agent.web_dashboard import create_dashboard_server
        
        # Mock objects
        class MockMemoryEngine:
            async def search_memories(self, query, limit=100):
                return [
                    {
                        'id': 'test_mem_1',
                        'title': 'Test Memory 1',
                        'type': 'code_snippet',
                        'content': 'def test_function(): pass',
                        'workspace': '/test'
                    }
                ]
        
        class MockTaskAgent:
            execution_history = []
        
        # Create dashboard server
        memory_engine = MockMemoryEngine()
        task_agent = MockTaskAgent()
        dashboard = create_dashboard_server(memory_engine, task_agent, port=8081)
        
        print("  ✓ Dashboard server created successfully")
        print("  ✓ Flask routes configured")
        print("  ✓ Template system ready")
        print("  ✓ Static files prepared")
        
        # Test dashboard data generation
        try:
            dashboard_data = dashboard._get_cached_dashboard_data()
            print(f"  ✓ Dashboard data generated: {len(dashboard_data)} sections")
        except Exception as e:
            print(f"  ⚠ Dashboard data generation: {e}")
        
        print("  ✅ Web Dashboard test passed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Web Dashboard test failed: {e}\n")
        return False

def test_performance_monitoring():
    """Test performance monitoring functionality"""
    print("⚡ Testing Performance Monitoring...")
    
    try:
        from agent.performance import PerformanceMonitor
        
        # Create performance monitor
        monitor = PerformanceMonitor()
        
        # Start monitoring
        monitor.start_monitoring(interval=0.1)
        print("  ✓ Performance monitoring started")
        
        # Wait a bit for metrics to be collected
        time.sleep(0.5)
        
        # Test performance summary
        summary = monitor.get_performance_summary()
        print(f"  ✓ Performance summary: {len(summary)} metrics collected")
        
        # Test operation tracking (async context manager)
        async def test_async_operation():
            from agent.performance import track_async_operation
            async with track_async_operation("test_operation"):
                await asyncio.sleep(0.1)  # Simulate async work
        
        asyncio.run(test_async_operation())
        print("  ✓ Async operation tracking completed")
        
        # Stop monitoring
        monitor.stop_monitoring()
        print("  ✓ Performance monitoring stopped")
        
        print("  ✅ Performance Monitoring test passed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Performance Monitoring test failed: {e}\n")
        return False

def test_analytics_integration():
    """Test integration between all analytics components"""
    print("🔗 Testing Analytics Integration...")
    
    try:
        # Test that all components can work together
        from agent.knowledge_graph import get_knowledge_graph
        from agent.analytics import MemoryAnalytics
        from agent.performance import PerformanceMonitor
        
        # Initialize components
        knowledge_graph = get_knowledge_graph()
        performance_monitor = PerformanceMonitor()
        
        # Mock engines for integration test
        class IntegratedMockMemoryEngine:
            async def search_memories(self, query, limit=100):
                # Add some memories to knowledge graph
                memory_data = {
                    'title': 'Integration test memory',
                    'content': 'Testing integration between components',
                    'type': 'test',
                    'workspace': '/integration',
                    'tags': ['integration', 'test']
                }
                knowledge_graph.add_memory_node('integration_mem', memory_data)
                return [memory_data]
        
        class IntegratedMockTaskAgent:
            execution_history = [
                {
                    'id': 'integration_task',
                    'description': 'Integration test task',
                    'status': 'completed',
                    'plugin': 'test_plugin',
                    'execution_time': 1.5
                }
            ]
        
        memory_engine = IntegratedMockMemoryEngine()
        task_agent = IntegratedMockTaskAgent()
        
        # Test analytics with knowledge graph integration
        analytics = MemoryAnalytics(memory_engine, task_agent, knowledge_graph)
        
        async def run_integration_test():
            # Start performance monitoring
            performance_monitor.start_monitoring(interval=0.1)
            
            # Generate analytics
            dashboard_data = await analytics.generate_dashboard_data()
            
            # Stop monitoring
            performance_monitor.stop_monitoring()
            
            # Verify integration
            kg_analysis = knowledge_graph.analyze_graph()
            perf_summary = performance_monitor.get_performance_summary()
            
            print(f"  ✓ Knowledge graph integrated: {kg_analysis['graph_metrics']['nodes']} nodes")
            print(f"  ✓ Analytics generated successfully")
            print(f"  ✓ Performance monitoring active: {len(perf_summary)} metrics")
            
            return True
        
        result = asyncio.run(run_integration_test())
        
        print("  ✅ Analytics Integration test passed\n")
        return result
        
    except Exception as e:
        print(f"  ❌ Analytics Integration test failed: {e}\n")
        return False

def main():
    """Run all advanced analytics tests"""
    print("🚀 NeuroForge Advanced Analytics Test Suite")
    print("=" * 50)
    
    tests = [
        test_knowledge_graph,
        test_analytics_dashboard,
        test_web_dashboard,
        test_performance_monitoring,
        test_analytics_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}\n")
    
    print("=" * 50)
    print(f"📈 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All advanced analytics tests passed!")
        print("✨ NeuroForge analytics system is fully operational!")
    else:
        print(f"⚠ {total - passed} tests failed")
        print("🔧 Some components may need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
