"""
NeuroForge Web Dashboard
Author: Muzan Sano

Web-based dashboard for visualizing NeuroForge analytics and insights
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import asyncio
from pathlib import Path
import time
import logging
from typing import Dict, Any, Optional
import threading
from datetime import datetime, timedelta

# Import NeuroForge components
try:
    from .analytics import MemoryAnalytics
    from .knowledge_graph import get_knowledge_graph
    from .memory_engine import MemoryEngine
    from .task_agent import TaskAgent
except ImportError:
    # For testing purposes
    class MockMemoryEngine:
        async def search_memories(self, query, limit=100):
            return []
    
    class MockTaskAgent:
        execution_history = []
    
    class MockAnalytics:
        def __init__(self, *args):
            pass
        async def generate_dashboard_data(self):
            from collections import namedtuple
            DashboardData = namedtuple('DashboardData', ['memory_stats', 'task_stats', 'knowledge_graph_stats', 'performance_metrics', 'recommendations', 'last_updated'])
            MemoryStats = namedtuple('MemoryStats', ['total_memories', 'active_memories', 'memory_types', 'workspace_distribution', 'average_size', 'growth_rate', 'access_patterns', 'tag_frequency'])
            TaskStats = namedtuple('TaskStats', ['total_tasks', 'completed_tasks', 'failed_tasks', 'plugin_usage', 'success_rate', 'average_execution_time', 'workspace_activity', 'performance_trends'])
            
            return DashboardData(
                memory_stats=MemoryStats(0, 0, {}, {}, 0, 0, {}, {}),
                task_stats=TaskStats(0, 0, 0, {}, 0, 0, {}, []),
                knowledge_graph_stats={},
                performance_metrics={},
                recommendations=[],
                last_updated=time.time()
            )
        def generate_performance_metrics(self):
            return {'system': {'cpu_usage': 0, 'memory_usage': 0}}
        def get_trend_analysis(self, days):
            return {}
    
    class MockKnowledgeGraph:
        def analyze_graph(self):
            return {}
        def __init__(self):
            self.nodes = {}
            self.edges = {}
    
    MemoryEngine = MockMemoryEngine
    TaskAgent = MockTaskAgent
    MemoryAnalytics = MockAnalytics
    def get_knowledge_graph():
        return MockKnowledgeGraph()

logger = logging.getLogger(__name__)

class DashboardServer:
    """Web dashboard server for NeuroForge"""
    
    def __init__(self, memory_engine, task_agent, port: int = 8080):
        self.memory_engine = memory_engine
        self.task_agent = task_agent
        self.knowledge_graph = get_knowledge_graph()
        self.analytics = MemoryAnalytics(memory_engine, task_agent, self.knowledge_graph)
        self.port = port
        
        # Flask app setup
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self._setup_routes()
        
        # Cache for dashboard data
        self._dashboard_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp = 0
        self._cache_timeout = 60  # 1 minute cache
        
        # Background update thread
        self._update_thread = None
        self._should_stop = False
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/dashboard-data')
        def api_dashboard_data():
            """API endpoint for dashboard data"""
            try:
                data = self._get_cached_dashboard_data()
                return jsonify(data)
            except Exception as e:
                logger.error(f"Error getting dashboard data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory-search')
        def api_memory_search():
            """API endpoint for memory search"""
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 10))
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                memories = loop.run_until_complete(
                    self.memory_engine.search_memories(query, limit=limit)
                )
                loop.close()
                
                return jsonify({
                    'memories': memories,
                    'total': len(memories),
                    'query': query
                })
            except Exception as e:
                logger.error(f"Error searching memories: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/knowledge-graph')
        def api_knowledge_graph():
            """API endpoint for knowledge graph data"""
            try:
                analysis = self.knowledge_graph.analyze_graph()
                
                # Get node and edge data for visualization
                nodes = []
                edges = []
                
                for node_id, node in self.knowledge_graph.nodes.items():
                    nodes.append({
                        'id': node_id,
                        'label': node.label,
                        'type': node.type,
                        'size': min(node.access_count * 2 + 5, 50),  # Scale node size
                        'color': self._get_node_color(node.type)
                    })
                
                for edge_id, edge in self.knowledge_graph.edges.items():
                    edges.append({
                        'source': edge.source,
                        'target': edge.target,
                        'relationship': edge.relationship,
                        'weight': edge.weight
                    })
                
                return jsonify({
                    'nodes': nodes,
                    'edges': edges,
                    'analysis': analysis
                })
            except Exception as e:
                logger.error(f"Error getting knowledge graph: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance-metrics')
        def api_performance_metrics():
            """API endpoint for real-time performance metrics"""
            try:
                metrics = self.analytics.generate_performance_metrics()
                return jsonify(metrics)
            except Exception as e:
                logger.error(f"Error getting performance metrics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trends')
        def api_trends():
            """API endpoint for trend analysis"""
            days = int(request.args.get('days', 7))
            
            try:
                trends = self.analytics.get_trend_analysis(days)
                return jsonify(trends)
            except Exception as e:
                logger.error(f"Error getting trends: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recommendations')
        def api_recommendations():
            """API endpoint for system recommendations"""
            try:
                data = self._get_cached_dashboard_data()
                recommendations = data.get('recommendations', [])
                return jsonify({'recommendations': recommendations})
            except Exception as e:
                logger.error(f"Error getting recommendations: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files"""
            return send_from_directory(self.app.static_folder, filename)
    
    def _get_node_color(self, node_type: str) -> str:
        """Get color for node type"""
        colors = {
            'memory': '#4CAF50',
            'task': '#2196F3',
            'file': '#FF9800',
            'concept': '#9C27B0',
            'pattern': '#F44336'
        }
        return colors.get(node_type, '#757575')
    
    def _get_cached_dashboard_data(self) -> Dict[str, Any]:
        """Get cached dashboard data or generate new if expired"""
        current_time = time.time()
        
        if (self._dashboard_cache is None or 
            current_time - self._cache_timestamp > self._cache_timeout):
            
            # Generate new dashboard data
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                dashboard_data = loop.run_until_complete(
                    self.analytics.generate_dashboard_data()
                )
                
                # Convert to JSON-serializable format
                self._dashboard_cache = {
                    'memory_stats': dashboard_data.memory_stats.__dict__,
                    'task_stats': dashboard_data.task_stats.__dict__,
                    'knowledge_graph_stats': dashboard_data.knowledge_graph_stats,
                    'performance_metrics': dashboard_data.performance_metrics,
                    'recommendations': dashboard_data.recommendations,
                    'last_updated': dashboard_data.last_updated
                }
                
                self._cache_timestamp = current_time
                
            finally:
                loop.close()
        
        return self._dashboard_cache
    
    def _background_update(self):
        """Background thread to update dashboard data periodically"""
        while not self._should_stop:
            try:
                self._get_cached_dashboard_data()
                logger.debug("Dashboard data updated in background")
            except Exception as e:
                logger.error(f"Error in background update: {e}")
            
            # Wait for next update (5 minutes)
            for _ in range(300):
                if self._should_stop:
                    break
                time.sleep(1)
    
    def start(self, debug: bool = False, background_updates: bool = True):
        """Start the dashboard server"""
        logger.info(f"Starting NeuroForge Dashboard on port {self.port}")
        
        # Start background update thread
        if background_updates:
            self._update_thread = threading.Thread(target=self._background_update, daemon=True)
            self._update_thread.start()
        
        # Create templates directory and basic template if not exists
        self._create_default_templates()
        
        try:
            self.app.run(host='0.0.0.0', port=self.port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            logger.info("Dashboard server stopped by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the dashboard server"""
        self._should_stop = True
        if self._update_thread:
            self._update_thread.join(timeout=1)
        logger.info("Dashboard server stopped")
    
    def _create_default_templates(self):
        """Create default HTML templates if they don't exist"""
        templates_dir = Path(__file__).parent / 'templates'
        templates_dir.mkdir(exist_ok=True)
        
        dashboard_template = templates_dir / 'dashboard.html'
        if not dashboard_template.exists():
            self._create_dashboard_template(dashboard_template)
        
        static_dir = Path(__file__).parent / 'static'
        static_dir.mkdir(exist_ok=True)
        
        # Create CSS and JS files
        self._create_static_files(static_dir)
    
    def _create_dashboard_template(self, template_path: Path):
        """Create the main dashboard HTML template"""
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroForge Dashboard</title>
    <link rel="stylesheet" href="/static/dashboard.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>🧠 NeuroForge Dashboard</h1>
            <div class="header-stats">
                <span id="last-updated">Loading...</span>
                <button onclick="refreshDashboard()" class="refresh-btn">🔄 Refresh</button>
            </div>
        </header>
        
        <div class="dashboard-grid">
            <!-- Memory Stats -->
            <div class="dashboard-card">
                <h2>📚 Memory Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="total-memories">-</span>
                        <span class="stat-label">Total Memories</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="active-memories">-</span>
                        <span class="stat-label">Active Memories</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="growth-rate">-</span>
                        <span class="stat-label">Daily Growth</span>
                    </div>
                </div>
                <canvas id="memory-chart" width="400" height="200"></canvas>
            </div>
            
            <!-- Task Performance -->
            <div class="dashboard-card">
                <h2>⚡ Task Performance</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="success-rate">-</span>
                        <span class="stat-label">Success Rate</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="avg-execution">-</span>
                        <span class="stat-label">Avg Execution (s)</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="total-tasks">-</span>
                        <span class="stat-label">Total Tasks</span>
                    </div>
                </div>
                <canvas id="task-chart" width="400" height="200"></canvas>
            </div>
            
            <!-- Knowledge Graph -->
            <div class="dashboard-card knowledge-graph">
                <h2>🕸️ Knowledge Graph</h2>
                <div id="graph-container">
                    <svg id="knowledge-graph" width="100%" height="300"></svg>
                </div>
                <div class="graph-stats">
                    <span>Nodes: <span id="graph-nodes">-</span></span>
                    <span>Edges: <span id="graph-edges">-</span></span>
                    <span>Density: <span id="graph-density">-</span></span>
                </div>
            </div>
            
            <!-- System Performance -->
            <div class="dashboard-card">
                <h2>🖥️ System Performance</h2>
                <div class="performance-meters">
                    <div class="meter">
                        <span class="meter-label">CPU</span>
                        <div class="meter-bar">
                            <div class="meter-fill" id="cpu-meter"></div>
                        </div>
                        <span class="meter-value" id="cpu-value">-</span>
                    </div>
                    <div class="meter">
                        <span class="meter-label">Memory</span>
                        <div class="meter-bar">
                            <div class="meter-fill" id="memory-meter"></div>
                        </div>
                        <span class="meter-value" id="memory-value">-</span>
                    </div>
                </div>
            </div>
            
            <!-- Recommendations -->
            <div class="dashboard-card recommendations">
                <h2>💡 Recommendations</h2>
                <div id="recommendations-list">
                    <div class="loading">Loading recommendations...</div>
                </div>
            </div>
            
            <!-- Memory Search -->
            <div class="dashboard-card">
                <h2>🔍 Memory Search</h2>
                <div class="search-container">
                    <input type="text" id="search-input" placeholder="Search memories..." />
                    <button onclick="searchMemories()" class="search-btn">Search</button>
                </div>
                <div id="search-results"></div>
            </div>
        </div>
    </div>
    
    <script src="/static/dashboard.js"></script>
</body>
</html>'''
        
        with open(template_path, 'w') as f:
            f.write(html_content)
    
    def _create_static_files(self, static_dir: Path):
        """Create CSS and JavaScript files"""
        
        # CSS file
        css_content = '''
/* NeuroForge Dashboard Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

.dashboard-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.dashboard-header {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
}

.dashboard-header h1 {
    color: #4a5568;
    font-size: 2.5rem;
    font-weight: 700;
}

.header-stats {
    display: flex;
    align-items: center;
    gap: 15px;
}

.refresh-btn {
    background: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
}

.refresh-btn:hover {
    background: #45a049;
    transform: translateY(-2px);
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
}

.dashboard-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: transform 0.3s ease;
}

.dashboard-card:hover {
    transform: translateY(-5px);
}

.dashboard-card h2 {
    color: #4a5568;
    margin-bottom: 20px;
    font-size: 1.4rem;
    font-weight: 600;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

.stat-item {
    text-align: center;
    padding: 15px;
    background: rgba(79, 172, 254, 0.1);
    border-radius: 10px;
    border: 1px solid rgba(79, 172, 254, 0.2);
}

.stat-value {
    display: block;
    font-size: 2rem;
    font-weight: 700;
    color: #4facfe;
    margin-bottom: 5px;
}

.stat-label {
    color: #718096;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.performance-meters {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.meter {
    display: flex;
    align-items: center;
    gap: 15px;
}

.meter-label {
    width: 60px;
    font-weight: 600;
    color: #4a5568;
}

.meter-bar {
    flex: 1;
    height: 20px;
    background: #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
}

.meter-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #45a049);
    border-radius: 10px;
    transition: width 0.5s ease;
    width: 0%;
}

.meter-value {
    width: 60px;
    text-align: right;
    font-weight: 600;
    color: #4a5568;
}

.knowledge-graph {
    grid-column: span 2;
}

#knowledge-graph {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background: #fafafa;
}

.graph-stats {
    display: flex;
    justify-content: space-around;
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #e2e8f0;
}

.graph-stats span {
    font-weight: 600;
    color: #4a5568;
}

.recommendations {
    grid-column: span 2;
}

.recommendation-item {
    background: rgba(255, 193, 7, 0.1);
    border: 1px solid rgba(255, 193, 7, 0.3);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
}

.recommendation-item.high {
    background: rgba(244, 67, 54, 0.1);
    border-color: rgba(244, 67, 54, 0.3);
}

.recommendation-item.medium {
    background: rgba(255, 152, 0, 0.1);
    border-color: rgba(255, 152, 0, 0.3);
}

.recommendation-item.low {
    background: rgba(76, 175, 80, 0.1);
    border-color: rgba(76, 175, 80, 0.3);
}

.recommendation-title {
    font-weight: 600;
    color: #4a5568;
    margin-bottom: 5px;
}

.recommendation-description {
    color: #718096;
    font-size: 0.9rem;
    margin-bottom: 10px;
}

.recommendation-impact {
    font-size: 0.8rem;
    color: #4CAF50;
    font-style: italic;
}

.search-container {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}

#search-input {
    flex: 1;
    padding: 10px 15px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 14px;
}

.search-btn {
    background: #2196F3;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.3s ease;
}

.search-btn:hover {
    background: #1976D2;
}

#search-results {
    max-height: 300px;
    overflow-y: auto;
}

.memory-item {
    background: #f8f9fa;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 8px;
}

.memory-title {
    font-weight: 600;
    color: #4a5568;
    margin-bottom: 5px;
}

.memory-type {
    display: inline-block;
    background: #4CAF50;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    margin-right: 10px;
}

.loading {
    text-align: center;
    color: #718096;
    padding: 20px;
}

/* Responsive design */
@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    
    .knowledge-graph,
    .recommendations {
        grid-column: span 1;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .dashboard-header {
        flex-direction: column;
        gap: 15px;
        text-align: center;
    }
}
'''
        
        css_file = static_dir / 'dashboard.css'
        with open(css_file, 'w') as f:
            f.write(css_content)
        
        # JavaScript file
        js_content = '''
// NeuroForge Dashboard JavaScript

let dashboardData = null;
let memoryChart = null;
let taskChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    refreshDashboard();
    setInterval(updatePerformanceMetrics, 30000); // Update every 30 seconds
    
    // Setup search
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchMemories();
        }
    });
});

async function refreshDashboard() {
    try {
        showLoading();
        
        // Fetch dashboard data
        const response = await fetch('/api/dashboard-data');
        dashboardData = await response.json();
        
        updateMemoryStats();
        updateTaskStats();
        updateKnowledgeGraph();
        updateRecommendations();
        updateLastUpdated();
        
        hideLoading();
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        showError('Failed to refresh dashboard data');
    }
}

function updateMemoryStats() {
    if (!dashboardData?.memory_stats) return;
    
    const stats = dashboardData.memory_stats;
    
    document.getElementById('total-memories').textContent = stats.total_memories || 0;
    document.getElementById('active-memories').textContent = stats.active_memories || 0;
    document.getElementById('growth-rate').textContent = (stats.growth_rate || 0).toFixed(1);
    
    // Update memory chart
    updateMemoryChart(stats);
}

function updateTaskStats() {
    if (!dashboardData?.task_stats) return;
    
    const stats = dashboardData.task_stats;
    
    document.getElementById('success-rate').textContent = (stats.success_rate || 0).toFixed(1) + '%';
    document.getElementById('avg-execution').textContent = (stats.average_execution_time || 0).toFixed(1);
    document.getElementById('total-tasks').textContent = stats.total_tasks || 0;
    
    // Update task chart
    updateTaskChart(stats);
}

function updateMemoryChart(stats) {
    const ctx = document.getElementById('memory-chart').getContext('2d');
    
    if (memoryChart) {
        memoryChart.destroy();
    }
    
    const types = stats.memory_types || {};
    
    memoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(types),
            datasets: [{
                data: Object.values(types),
                backgroundColor: [
                    '#4CAF50',
                    '#2196F3',
                    '#FF9800',
                    '#9C27B0',
                    '#F44336'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function updateTaskChart(stats) {
    const ctx = document.getElementById('task-chart').getContext('2d');
    
    if (taskChart) {
        taskChart.destroy();
    }
    
    const plugins = stats.plugin_usage || {};
    
    taskChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(plugins),
            datasets: [{
                label: 'Task Count',
                data: Object.values(plugins),
                backgroundColor: '#2196F3',
                borderColor: '#1976D2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function updateKnowledgeGraph() {
    try {
        const response = await fetch('/api/knowledge-graph');
        const graphData = await response.json();
        
        if (graphData.error) {
            console.error('Knowledge graph error:', graphData.error);
            return;
        }
        
        // Update stats
        const metrics = graphData.analysis?.graph_metrics || {};
        document.getElementById('graph-nodes').textContent = metrics.nodes || 0;
        document.getElementById('graph-edges').textContent = metrics.edges || 0;
        document.getElementById('graph-density').textContent = (metrics.density || 0).toFixed(3);
        
        // Render graph visualization
        renderKnowledgeGraph(graphData);
        
    } catch (error) {
        console.error('Error updating knowledge graph:', error);
    }
}

function renderKnowledgeGraph(graphData) {
    const svg = d3.select('#knowledge-graph');
    svg.selectAll('*').remove();
    
    const width = svg.node().clientWidth;
    const height = 300;
    
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    
    if (nodes.length === 0) {
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height / 2)
            .attr('text-anchor', 'middle')
            .style('fill', '#718096')
            .text('No knowledge graph data available');
        return;
    }
    
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges).id(d => d.id).distance(50))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2));
    
    const link = svg.append('g')
        .selectAll('line')
        .data(edges)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.weight || 1));
    
    const node = svg.append('g')
        .selectAll('circle')
        .data(nodes)
        .enter().append('circle')
        .attr('r', d => Math.max(5, (d.size || 10) / 3))
        .attr('fill', d => d.color || '#4CAF50')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    node.append('title')
        .text(d => d.label);
    
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
    });
    
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function updateRecommendations() {
    const container = document.getElementById('recommendations-list');
    const recommendations = dashboardData?.recommendations || [];
    
    if (recommendations.length === 0) {
        container.innerHTML = '<div class="loading">No recommendations at this time</div>';
        return;
    }
    
    container.innerHTML = recommendations.map(rec => `
        <div class="recommendation-item ${rec.priority}">
            <div class="recommendation-title">${rec.title}</div>
            <div class="recommendation-description">${rec.description}</div>
            <div class="recommendation-impact">Impact: ${rec.impact}</div>
        </div>
    `).join('');
}

async function updatePerformanceMetrics() {
    try {
        const response = await fetch('/api/performance-metrics');
        const metrics = await response.json();
        
        const system = metrics.system || {};
        
        // Update CPU meter
        const cpuUsage = system.cpu_usage || 0;
        document.getElementById('cpu-meter').style.width = cpuUsage + '%';
        document.getElementById('cpu-value').textContent = cpuUsage.toFixed(1) + '%';
        
        // Update Memory meter
        const memUsage = system.memory_usage || 0;
        document.getElementById('memory-meter').style.width = memUsage + '%';
        document.getElementById('memory-value').textContent = memUsage.toFixed(1) + '%';
        
        // Color coding for performance meters
        updateMeterColor('cpu-meter', cpuUsage);
        updateMeterColor('memory-meter', memUsage);
        
    } catch (error) {
        console.error('Error updating performance metrics:', error);
    }
}

function updateMeterColor(elementId, value) {
    const element = document.getElementById(elementId);
    if (value > 80) {
        element.style.background = 'linear-gradient(90deg, #F44336, #D32F2F)';
    } else if (value > 60) {
        element.style.background = 'linear-gradient(90deg, #FF9800, #F57C00)';
    } else {
        element.style.background = 'linear-gradient(90deg, #4CAF50, #45a049)';
    }
}

async function searchMemories() {
    const query = document.getElementById('search-input').value.trim();
    const resultsContainer = document.getElementById('search-results');
    
    if (!query) {
        resultsContainer.innerHTML = '';
        return;
    }
    
    resultsContainer.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        const response = await fetch(`/api/memory-search?q=${encodeURIComponent(query)}&limit=10`);
        const data = await response.json();
        
        if (data.error) {
            resultsContainer.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            return;
        }
        
        const memories = data.memories || [];
        
        if (memories.length === 0) {
            resultsContainer.innerHTML = '<div class="loading">No memories found</div>';
            return;
        }
        
        resultsContainer.innerHTML = memories.map(memory => `
            <div class="memory-item">
                <div class="memory-title">${memory.title || 'Untitled Memory'}</div>
                <span class="memory-type">${memory.type || 'unknown'}</span>
                <div class="memory-content">${(memory.content || '').substring(0, 100)}...</div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error searching memories:', error);
        resultsContainer.innerHTML = '<div class="error">Search failed</div>';
    }
}

function updateLastUpdated() {
    const timestamp = dashboardData?.last_updated;
    if (timestamp) {
        const date = new Date(timestamp * 1000);
        document.getElementById('last-updated').textContent = 
            `Last updated: ${date.toLocaleTimeString()}`;
    }
}

function showLoading() {
    // Add loading indicators
    document.querySelectorAll('.stat-value').forEach(el => {
        el.textContent = '...';
    });
}

function hideLoading() {
    // Remove loading indicators (handled by update functions)
}

function showError(message) {
    // Simple error display
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #F44336;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 1000;
    `;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        document.body.removeChild(errorDiv);
    }, 5000);
}
'''
        
        js_file = static_dir / 'dashboard.js'
        with open(js_file, 'w') as f:
            f.write(js_content)
        
        logger.info("Default dashboard templates created")

# Factory function to create dashboard server
def create_dashboard_server(memory_engine, task_agent, port: int = 8080) -> DashboardServer:
    """Create a dashboard server instance"""
    return DashboardServer(memory_engine, task_agent, port)

# Example usage
if __name__ == "__main__":
    def test_dashboard_server():
        """Test the dashboard server"""
        print("🌐 Testing NeuroForge Web Dashboard")
        
        # Mock components for testing
        class MockMemoryEngine:
            async def search_memories(self, query, limit=100):
                return [
                    {
                        'id': f'mem_{i}',
                        'title': f'Test Memory {i}',
                        'type': 'test',
                        'content': f'Test content for memory {i}',
                        'workspace': '/test',
                        'tags': ['test', 'mock']
                    }
                    for i in range(5)
                ]
        
        class MockTaskAgent:
            execution_history = []
        
        memory_engine = MockMemoryEngine()
        task_agent = MockTaskAgent()
        
        # Create dashboard server
        dashboard = create_dashboard_server(memory_engine, task_agent, port=8080)
        
        print("Dashboard server created successfully")
        print("To start the server, call: dashboard.start()")
        print("Visit: http://localhost:8080")
        
        return dashboard
    
    test_dashboard_server()
