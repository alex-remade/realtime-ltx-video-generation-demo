import time
import threading
from collections import deque
from typing import Dict, Optional, Any
from streaming_pipeline.models import Monitorable

class ComponentMonitor:
    """
    Generic monitor for any components implementing Monitorable interface.
    
    Automatically collects metrics from all registered components with
    namespaced keys to prevent conflicts. Perfect for FAL demos showing
    clean, extensible architecture.
    """
    
    def __init__(self, components: Dict[str, Monitorable], history_duration=300):
        self.components = components
        self.history_duration = history_duration
        self.metrics_history: deque = deque(maxlen=int(history_duration))
        self.monitoring = False
        self.monitor_thread = None
        self.last_generation_count = 0
    
    def start_monitoring(self):
        """Start monitoring all registered components"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        component_names = list(self.components.keys())
        print(f"📊 Component monitoring started for: {', '.join(component_names)}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            if self.monitor_thread.is_alive():
                print("⚠️ Monitor thread didn't stop gracefully")
        print("📊 Component monitoring stopped")
    
    def _monitor_loop(self):
        """Monitor loop with automatic metrics collection from all components"""
        while self.monitoring:
            try:
                current_time = time.time()
                all_metrics = {"timestamp": current_time}
                
                # Auto-collect metrics from all registered components (nested structure)
                for component_name, component in self.components.items():
                    if component and hasattr(component, 'get_status'):
                        try:
                            status = component.get_status()
                            # Store component metrics in nested structure
                            all_metrics[component_name] = status
                        except Exception as e:
                            print(f"⚠️ Error getting status from {component_name}: {e}")
                            # Add error metric
                            all_metrics[component_name] = {"error": str(e)}
                
                # Add GPU metrics if available
                try:
                    import torch
                    if torch.cuda.is_available():
                        all_metrics["gpu_memory_allocated"] = torch.cuda.memory_allocated() / 1024**3
                except ImportError:
                    all_metrics["gpu_memory_allocated"] = 0.0
                
                self.metrics_history.append(all_metrics)
                
            except Exception as e:
                print(f"❌ Monitor loop error: {e}")
            
            time.sleep(1)
    
    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Get the latest metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self) -> list:
        """Get all metrics history"""
        return list(self.metrics_history)

