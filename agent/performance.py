"""
NeuroForge Performance Optimization Module
Author: Muzan Sano

Advanced performance monitoring and optimization features for NeuroForge
"""

import asyncio
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring system performance"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    active_threads: int
    open_files: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class OperationMetrics:
    """Metrics for specific operations"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    memory_before: float
    memory_after: float
    cpu_before: float
    cpu_after: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PerformanceMonitor:
    """Advanced performance monitoring and optimization"""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.metrics_history: List[PerformanceMetrics] = []
        self.operation_history: List[OperationMetrics] = []
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.optimization_strategies: Dict[str, Callable] = {}
        
        # Initialize optimization strategies
        self._init_optimization_strategies()
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'operation_duration': 5.0,  # seconds
            'max_memory_growth': 100.0,  # MB
        }
    
    def _init_optimization_strategies(self):
        """Initialize performance optimization strategies"""
        self.optimization_strategies = {
            'memory_cleanup': self._optimize_memory,
            'cache_optimization': self._optimize_cache,
            'io_optimization': self._optimize_io,
            'thread_optimization': self._optimize_threads,
        }
    
    def start_monitoring(self, interval: float = 1.0):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            logger.warning("Performance monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Performance monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 metrics to prevent memory bloat
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check for performance issues
                self._check_performance_alerts(metrics)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        process = psutil.Process()
        
        # CPU and memory
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        # I/O statistics
        try:
            io_counters = process.io_counters()
            disk_io_read = io_counters.read_bytes
            disk_io_write = io_counters.write_bytes
        except (AttributeError, OSError):
            disk_io_read = disk_io_write = 0
        
        # Network statistics (system-wide)
        try:
            net_io = psutil.net_io_counters()
            network_sent = net_io.bytes_sent
            network_recv = net_io.bytes_recv
        except (AttributeError, OSError):
            network_sent = network_recv = 0
        
        # Thread and file counts
        active_threads = process.num_threads()
        try:
            open_files = len(process.open_files())
        except (AttributeError, OSError):
            open_files = 0
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_sent=network_sent,
            network_recv=network_recv,
            active_threads=active_threads,
            open_files=open_files
        )
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check for performance issues and trigger optimizations"""
        alerts = []
        
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            self._trigger_optimization('cpu_optimization')
        
        if metrics.memory_percent > self.thresholds['memory_percent']:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
            self._trigger_optimization('memory_cleanup')
        
        if metrics.active_threads > 50:  # Arbitrary threshold
            alerts.append(f"High thread count: {metrics.active_threads}")
            self._trigger_optimization('thread_optimization')
        
        if alerts:
            logger.warning(f"Performance alerts: {', '.join(alerts)}")
    
    def _trigger_optimization(self, strategy: str):
        """Trigger a specific optimization strategy"""
        if strategy in self.optimization_strategies:
            try:
                self.optimization_strategies[strategy]()
                logger.info(f"Applied optimization strategy: {strategy}")
            except Exception as e:
                logger.error(f"Failed to apply optimization {strategy}: {e}")
    
    def _optimize_memory(self):
        """Memory optimization strategy"""
        import gc
        gc.collect()  # Force garbage collection
        
        # Clear old metrics if too many
        if len(self.metrics_history) > 500:
            self.metrics_history = self.metrics_history[-500:]
        
        if len(self.operation_history) > 200:
            self.operation_history = self.operation_history[-200:]
    
    def _optimize_cache(self):
        """Cache optimization strategy"""
        # This would integrate with the memory engine's cache
        logger.info("Cache optimization triggered")
    
    def _optimize_io(self):
        """I/O optimization strategy"""
        # This could batch I/O operations or adjust buffer sizes
        logger.info("I/O optimization triggered")
    
    def _optimize_threads(self):
        """Thread optimization strategy"""
        # This could clean up idle threads or adjust thread pool sizes
        logger.info("Thread optimization triggered")
    
    @asynccontextmanager
    async def track_operation(self, operation_name: str):
        """Context manager to track operation performance"""
        start_time = time.time()
        start_metrics = self._collect_metrics()
        success = False
        
        try:
            yield
            success = True
        finally:
            end_time = time.time()
            end_metrics = self._collect_metrics()
            duration = end_time - start_time
            
            operation_metrics = OperationMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                memory_before=start_metrics.memory_mb,
                memory_after=end_metrics.memory_mb,
                cpu_before=start_metrics.cpu_percent,
                cpu_after=end_metrics.cpu_percent
            )
            
            self.operation_history.append(operation_metrics)
            
            # Check for performance issues
            if duration > self.thresholds['operation_duration']:
                logger.warning(f"Slow operation: {operation_name} took {duration:.2f}s")
            
            memory_growth = end_metrics.memory_mb - start_metrics.memory_mb
            if memory_growth > self.thresholds['max_memory_growth']:
                logger.warning(f"High memory growth in {operation_name}: {memory_growth:.1f}MB")
                self._trigger_optimization('memory_cleanup')
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics"""
        if not self.metrics_history:
            return {"status": "No metrics available"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_mb for m in recent_metrics) / len(recent_metrics)
        avg_threads = sum(m.active_threads for m in recent_metrics) / len(recent_metrics)
        
        # Operation statistics
        successful_ops = sum(1 for op in self.operation_history if op.success)
        total_ops = len(self.operation_history)
        success_rate = successful_ops / total_ops if total_ops > 0 else 0
        
        slow_operations = [
            op for op in self.operation_history[-50:]  # Last 50 operations
            if op.duration > self.thresholds['operation_duration']
        ]
        
        return {
            "system_performance": {
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_mb": round(avg_memory, 2),
                "avg_threads": round(avg_threads, 1),
                "current_status": self._get_performance_status()
            },
            "operation_performance": {
                "total_operations": total_ops,
                "success_rate": round(success_rate * 100, 1),
                "slow_operations_count": len(slow_operations),
                "avg_operation_time": round(
                    sum(op.duration for op in self.operation_history[-20:]) / min(20, total_ops), 3
                ) if total_ops > 0 else 0
            },
            "optimizations_applied": {
                "monitoring_active": self.monitoring_active,
                "metrics_collected": len(self.metrics_history),
                "operations_tracked": len(self.operation_history)
            }
        }
    
    def _get_performance_status(self) -> str:
        """Get current performance status"""
        if not self.metrics_history:
            return "unknown"
        
        latest = self.metrics_history[-1]
        
        if latest.cpu_percent > self.thresholds['cpu_percent'] or \
           latest.memory_percent > self.thresholds['memory_percent']:
            return "critical"
        elif latest.cpu_percent > 60 or latest.memory_percent > 70:
            return "warning"
        else:
            return "healthy"
    
    def export_metrics(self, file_path: Optional[Path] = None) -> Path:
        """Export performance metrics to JSON file"""
        if file_path is None:
            file_path = self.workspace_path / ".neuroforge" / "performance" / f"metrics_{int(time.time())}.json"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            "summary": self.get_performance_summary(),
            "metrics_history": [m.to_dict() for m in self.metrics_history[-100:]],  # Last 100
            "operation_history": [op.to_dict() for op in self.operation_history[-50:]],  # Last 50
            "export_timestamp": time.time(),
            "thresholds": self.thresholds
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Performance metrics exported to {file_path}")
        return file_path

# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor

def start_global_monitoring(interval: float = 5.0):
    """Start global performance monitoring"""
    monitor = get_performance_monitor()
    monitor.start_monitoring(interval)

def stop_global_monitoring():
    """Stop global performance monitoring"""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()

async def track_async_operation(operation_name: str):
    """Decorator for tracking async operations"""
    monitor = get_performance_monitor()
    return monitor.track_operation(operation_name)

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_performance_monitoring():
        """Test the performance monitoring system"""
        print("🚀 Testing NeuroForge Performance Monitoring")
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring(interval=0.5)
        
        # Simulate some operations
        async with monitor.track_operation("test_operation_1"):
            await asyncio.sleep(0.1)
            # Simulate some work
            data = [i**2 for i in range(10000)]
        
        async with monitor.track_operation("test_operation_2"):
            await asyncio.sleep(0.2)
            # Simulate more work
            result = sum(i for i in range(100000))
        
        # Let monitoring collect some data
        await asyncio.sleep(2)
        
        # Get performance summary
        summary = monitor.get_performance_summary()
        print(f"Performance Summary: {json.dumps(summary, indent=2)}")
        
        # Export metrics
        export_path = monitor.export_metrics()
        print(f"Metrics exported to: {export_path}")
        
        monitor.stop_monitoring()
        print("✅ Performance monitoring test completed")
    
    # Run the test
    asyncio.run(test_performance_monitoring())
