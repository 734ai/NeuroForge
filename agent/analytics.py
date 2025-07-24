"""
NeuroForge Memory Analytics Dashboard
Author: Muzan Sano

Advanced analytics dashboard for visualizing memory patterns and insights
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import time
import logging
from collections import defaultdict, Counter
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """Statistics about memory usage and patterns"""
    total_memories: int
    active_memories: int
    memory_types: Dict[str, int]
    workspace_distribution: Dict[str, int]
    average_size: float
    growth_rate: float
    access_patterns: Dict[str, int]
    tag_frequency: Dict[str, int]

@dataclass
class TaskStats:
    """Statistics about task execution and performance"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    plugin_usage: Dict[str, int]
    success_rate: float
    average_execution_time: float
    workspace_activity: Dict[str, int]
    performance_trends: List[Dict[str, Any]]

@dataclass
class DashboardData:
    """Complete dashboard data"""
    memory_stats: MemoryStats
    task_stats: TaskStats
    knowledge_graph_stats: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    last_updated: float

class MemoryAnalytics:
    """Advanced analytics for NeuroForge memory system"""
    
    def __init__(self, memory_engine, task_agent, knowledge_graph):
        self.memory_engine = memory_engine
        self.task_agent = task_agent
        self.knowledge_graph = knowledge_graph
        self.analytics_history: List[DashboardData] = []
        
    async def analyze_memory_patterns(self) -> MemoryStats:
        """Analyze memory usage patterns and trends"""
        try:
            # Get all memories
            all_memories = await self.memory_engine.search_memories("", limit=1000)
            
            if not all_memories:
                return MemoryStats(
                    total_memories=0,
                    active_memories=0,
                    memory_types={},
                    workspace_distribution={},
                    average_size=0,
                    growth_rate=0,
                    access_patterns={},
                    tag_frequency={}
                )
            
            # Analyze memory types
            memory_types = Counter()
            workspace_distribution = Counter()
            sizes = []
            access_patterns = Counter()
            tag_frequency = Counter()
            creation_times = []
            
            current_time = time.time()
            week_ago = current_time - (7 * 24 * 3600)
            active_count = 0
            
            for memory in all_memories:
                # Memory type analysis
                memory_type = memory.get('type', 'unknown')
                memory_types[memory_type] += 1
                
                # Workspace distribution
                workspace = memory.get('workspace', 'unknown')
                workspace_distribution[workspace] += 1
                
                # Size analysis
                content_size = len(str(memory.get('content', '')))
                sizes.append(content_size)
                
                # Access patterns
                last_accessed = memory.get('last_accessed', 0)
                if last_accessed > week_ago:
                    active_count += 1
                    
                # Determine access frequency
                access_count = memory.get('access_count', 0)
                if access_count > 10:
                    access_patterns['frequent'] += 1
                elif access_count > 3:
                    access_patterns['moderate'] += 1
                else:
                    access_patterns['rare'] += 1
                
                # Tag analysis
                tags = memory.get('tags', [])
                for tag in tags:
                    tag_frequency[tag] += 1
                
                # Creation time for growth analysis
                created_at = memory.get('created_at', current_time)
                creation_times.append(created_at)
            
            # Calculate growth rate
            growth_rate = 0
            if len(creation_times) > 1:
                recent_memories = [t for t in creation_times if t > week_ago]
                growth_rate = len(recent_memories) / 7  # memories per day
            
            return MemoryStats(
                total_memories=len(all_memories),
                active_memories=active_count,
                memory_types=dict(memory_types),
                workspace_distribution=dict(workspace_distribution),
                average_size=statistics.mean(sizes) if sizes else 0,
                growth_rate=growth_rate,
                access_patterns=dict(access_patterns),
                tag_frequency=dict(tag_frequency.most_common(10))
            )
            
        except Exception as e:
            logger.error(f"Error analyzing memory patterns: {e}")
            return MemoryStats(0, 0, {}, {}, 0, 0, {}, {})
    
    async def analyze_task_performance(self) -> TaskStats:
        """Analyze task execution performance and patterns"""
        try:
            # Get task history (this would come from task_agent's history)
            # For now, we'll simulate some data
            task_history = getattr(self.task_agent, 'execution_history', [])
            
            if not task_history:
                return TaskStats(
                    total_tasks=0,
                    completed_tasks=0,
                    failed_tasks=0,
                    plugin_usage={},
                    success_rate=0,
                    average_execution_time=0,
                    workspace_activity={},
                    performance_trends=[]
                )
            
            total_tasks = len(task_history)
            completed_tasks = 0
            failed_tasks = 0
            plugin_usage = Counter()
            execution_times = []
            workspace_activity = Counter()
            performance_trends = []
            
            # Analyze tasks
            for task in task_history:
                status = task.get('status', 'unknown')
                if status == 'completed':
                    completed_tasks += 1
                elif status == 'failed':
                    failed_tasks += 1
                
                # Plugin usage
                plugin = task.get('plugin', 'unknown')
                plugin_usage[plugin] += 1
                
                # Execution time
                exec_time = task.get('execution_time', 0)
                execution_times.append(exec_time)
                
                # Workspace activity
                workspace = task.get('workspace', 'unknown')
                workspace_activity[workspace] += 1
            
            # Calculate success rate
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Generate performance trends (daily stats for last week)
            current_time = time.time()
            for i in range(7):
                day_start = current_time - (i * 24 * 3600)
                day_end = day_start + 24 * 3600
                
                day_tasks = [
                    task for task in task_history
                    if day_start <= task.get('created_at', 0) < day_end
                ]
                
                day_completed = len([
                    task for task in day_tasks
                    if task.get('status') == 'completed'
                ])
                
                performance_trends.append({
                    'date': datetime.fromtimestamp(day_start).strftime('%Y-%m-%d'),
                    'tasks_completed': day_completed,
                    'total_tasks': len(day_tasks),
                    'success_rate': (day_completed / len(day_tasks) * 100) if day_tasks else 0
                })
            
            return TaskStats(
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                plugin_usage=dict(plugin_usage),
                success_rate=success_rate,
                average_execution_time=statistics.mean(execution_times) if execution_times else 0,
                workspace_activity=dict(workspace_activity),
                performance_trends=performance_trends
            )
            
        except Exception as e:
            logger.error(f"Error analyzing task performance: {e}")
            return TaskStats(0, 0, 0, {}, 0, 0, {}, [])
    
    def generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate system performance metrics"""
        try:
            # Memory engine performance
            memory_performance = {
                'cache_hit_rate': getattr(self.memory_engine, 'cache_hit_rate', 0),
                'average_search_time': getattr(self.memory_engine, 'average_search_time', 0),
                'storage_efficiency': getattr(self.memory_engine, 'storage_efficiency', 0),
                'index_size': getattr(self.memory_engine, 'index_size', 0)
            }
            
            # Task agent performance
            task_performance = {
                'average_task_time': getattr(self.task_agent, 'average_execution_time', 0),
                'plugin_load_time': getattr(self.task_agent, 'plugin_load_time', 0),
                'queue_length': getattr(self.task_agent, 'queue_length', 0),
                'active_threads': getattr(self.task_agent, 'active_threads', 0)
            }
            
            # System resources
            import psutil
            system_performance = {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('.').percent,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
            
            return {
                'memory_engine': memory_performance,
                'task_agent': task_performance,
                'system': system_performance,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error generating performance metrics: {e}")
            return {
                'memory_engine': {},
                'task_agent': {},
                'system': {},
                'timestamp': time.time()
            }
    
    def generate_recommendations(self, memory_stats: MemoryStats, task_stats: TaskStats, performance_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        # Memory recommendations
        if memory_stats.total_memories > 1000:
            recommendations.append({
                'type': 'memory_optimization',
                'priority': 'high',
                'title': 'Memory Storage Optimization',
                'description': 'You have over 1000 memories. Consider archiving old or rarely accessed memories.',
                'action': 'archive_old_memories',
                'impact': 'Improved search performance and reduced storage usage'
            })
        
        if memory_stats.average_size > 10000:  # Large memories
            recommendations.append({
                'type': 'memory_size',
                'priority': 'medium',
                'title': 'Large Memory Detection',
                'description': 'Some memories are unusually large. Consider breaking them into smaller chunks.',
                'action': 'split_large_memories',
                'impact': 'Better memory organization and faster retrieval'
            })
        
        # Task recommendations
        if task_stats.success_rate < 80:
            recommendations.append({
                'type': 'task_reliability',
                'priority': 'high',
                'title': 'Task Success Rate Low',
                'description': f'Task success rate is {task_stats.success_rate:.1f}%. Review failed tasks and improve error handling.',
                'action': 'review_failed_tasks',
                'impact': 'Increased automation reliability'
            })
        
        if task_stats.average_execution_time > 30:  # Slow tasks
            recommendations.append({
                'type': 'task_performance',
                'priority': 'medium',
                'title': 'Slow Task Execution',
                'description': 'Tasks are taking longer than expected. Consider optimizing plugins or splitting complex tasks.',
                'action': 'optimize_task_performance',
                'impact': 'Faster task completion and better user experience'
            })
        
        # Performance recommendations
        system_perf = performance_metrics.get('system', {})
        if system_perf.get('memory_usage', 0) > 80:
            recommendations.append({
                'type': 'system_resources',
                'priority': 'high',
                'title': 'High Memory Usage',
                'description': 'System memory usage is high. Consider closing other applications or upgrading hardware.',
                'action': 'optimize_memory_usage',
                'impact': 'Better system performance and stability'
            })
        
        # Knowledge graph recommendations
        kg_stats = self.knowledge_graph.analyze_graph()
        if kg_stats.get('graph_metrics', {}).get('density', 0) < 0.1:
            recommendations.append({
                'type': 'knowledge_graph',
                'priority': 'low',
                'title': 'Sparse Knowledge Graph',
                'description': 'Your knowledge graph has low connectivity. Add more relationships between memories and tasks.',
                'action': 'enhance_knowledge_connections',
                'impact': 'Better insight discovery and pattern recognition'
            })
        
        return recommendations
    
    async def generate_dashboard_data(self) -> DashboardData:
        """Generate complete dashboard data"""
        try:
            logger.info("Generating dashboard data...")
            
            # Gather all analytics
            memory_stats = await self.analyze_memory_patterns()
            task_stats = await self.analyze_task_performance()
            performance_metrics = self.generate_performance_metrics()
            knowledge_graph_stats = self.knowledge_graph.analyze_graph()
            recommendations = self.generate_recommendations(memory_stats, task_stats, performance_metrics)
            
            dashboard_data = DashboardData(
                memory_stats=memory_stats,
                task_stats=task_stats,
                knowledge_graph_stats=knowledge_graph_stats,
                performance_metrics=performance_metrics,
                recommendations=recommendations,
                last_updated=time.time()
            )
            
            # Store in history
            self.analytics_history.append(dashboard_data)
            
            # Keep only last 30 days of history
            cutoff_time = time.time() - (30 * 24 * 3600)
            self.analytics_history = [
                data for data in self.analytics_history
                if data.last_updated > cutoff_time
            ]
            
            logger.info("Dashboard data generated successfully")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            raise
    
    def export_analytics(self, file_path: Optional[Path] = None) -> Path:
        """Export analytics data to JSON file"""
        if file_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = Path(f".neuroforge/analytics/dashboard_{timestamp}.json")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dashboard data to JSON-serializable format
        export_data = []
        for dashboard_data in self.analytics_history:
            export_data.append({
                'memory_stats': dashboard_data.memory_stats.__dict__,
                'task_stats': dashboard_data.task_stats.__dict__,
                'knowledge_graph_stats': dashboard_data.knowledge_graph_stats,
                'performance_metrics': dashboard_data.performance_metrics,
                'recommendations': dashboard_data.recommendations,
                'last_updated': dashboard_data.last_updated
            })
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Analytics exported to {file_path}")
        return file_path
    
    def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Analyze trends over specified number of days"""
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_data = [
            data for data in self.analytics_history
            if data.last_updated > cutoff_time
        ]
        
        if len(recent_data) < 2:
            return {"status": "insufficient_data", "message": "Need at least 2 data points for trend analysis"}
        
        # Memory trends
        memory_counts = [data.memory_stats.total_memories for data in recent_data]
        memory_growth = memory_counts[-1] - memory_counts[0] if len(memory_counts) > 1 else 0
        
        # Task trends
        task_success_rates = [data.task_stats.success_rate for data in recent_data]
        success_rate_trend = task_success_rates[-1] - task_success_rates[0] if len(task_success_rates) > 1 else 0
        
        # Performance trends
        cpu_usages = []
        memory_usages = []
        for data in recent_data:
            system_perf = data.performance_metrics.get('system', {})
            cpu_usages.append(system_perf.get('cpu_usage', 0))
            memory_usages.append(system_perf.get('memory_usage', 0))
        
        return {
            'period_days': days,
            'data_points': len(recent_data),
            'memory_trends': {
                'total_growth': memory_growth,
                'growth_rate': memory_growth / days if days > 0 else 0
            },
            'task_trends': {
                'success_rate_change': success_rate_trend,
                'performance_trend': 'improving' if success_rate_trend > 0 else 'declining' if success_rate_trend < 0 else 'stable'
            },
            'system_trends': {
                'average_cpu': statistics.mean(cpu_usages) if cpu_usages else 0,
                'average_memory': statistics.mean(memory_usages) if memory_usages else 0,
                'cpu_trend': 'increasing' if len(cpu_usages) > 1 and cpu_usages[-1] > cpu_usages[0] else 'stable',
                'memory_trend': 'increasing' if len(memory_usages) > 1 and memory_usages[-1] > memory_usages[0] else 'stable'
            }
        }

# Example usage and testing
if __name__ == "__main__":
    def test_analytics():
        """Test the analytics system"""
        print("📊 Testing NeuroForge Analytics Dashboard")
        
        # Mock objects for testing
        class MockMemoryEngine:
            async def search_memories(self, query, limit=100):
                return [
                    {
                        'id': f'mem_{i}',
                        'type': 'code_snippet' if i % 2 == 0 else 'documentation',
                        'workspace': f'/project/{i % 3}',
                        'content': f'Test content {i}' * (i % 10 + 1),
                        'tags': ['python', 'test'] if i % 2 == 0 else ['docs'],
                        'created_at': time.time() - (i * 3600),
                        'last_accessed': time.time() - (i * 1800),
                        'access_count': i % 15
                    }
                    for i in range(50)
                ]
        
        class MockTaskAgent:
            execution_history = [
                {
                    'id': f'task_{i}',
                    'status': 'completed' if i % 4 != 0 else 'failed',
                    'plugin': f'plugin_{i % 3}',
                    'workspace': f'/project/{i % 2}',
                    'execution_time': (i % 10) + 5,
                    'created_at': time.time() - (i * 1800)
                }
                for i in range(20)
            ]
        
        class MockKnowledgeGraph:
            def analyze_graph(self):
                return {
                    'graph_metrics': {
                        'nodes': 100,
                        'edges': 150,
                        'density': 0.15,
                        'components': 3
                    },
                    'node_distribution': {'memory': 50, 'task': 20, 'concept': 30},
                    'relationship_distribution': {'similar_to': 80, 'contains': 70}
                }
        
        # Create analytics instance
        memory_engine = MockMemoryEngine()
        task_agent = MockTaskAgent()
        knowledge_graph = MockKnowledgeGraph()
        
        analytics = MemoryAnalytics(memory_engine, task_agent, knowledge_graph)
        
        # Run async test
        async def run_test():
            dashboard_data = await analytics.generate_dashboard_data()
            
            print(f"Memory Stats: {dashboard_data.memory_stats}")
            print(f"Task Stats: {dashboard_data.task_stats}")
            print(f"Recommendations: {len(dashboard_data.recommendations)} generated")
            
            # Export analytics
            export_path = analytics.export_analytics()
            print(f"Analytics exported to: {export_path}")
        
        asyncio.run(run_test())
        print("✅ Analytics dashboard test completed")
    
    test_analytics()
