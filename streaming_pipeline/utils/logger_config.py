"""
Minimal logging configuration for realtime video generation system.
Creates separate log files for key concerns: server, generation, and queue.
"""

import logging
import os
from typing import Dict

def setup_loggers() -> Dict[str, logging.Logger]:
    """Setup separate loggers for different components"""
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Shared formatter
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    
    loggers = {}
    
    # Server logger - API startup, config, health
    server_logger = logging.getLogger('server')
    server_handler = logging.FileHandler('logs/server.log')
    server_handler.setFormatter(formatter)
    server_logger.addHandler(server_handler)
    server_logger.setLevel(logging.INFO)
    loggers['server'] = server_logger
    
    # Generation logger - Video generation pipeline
    generation_logger = logging.getLogger('generation')
    generation_handler = logging.FileHandler('logs/generation.log')
    generation_handler.setFormatter(formatter)
    generation_logger.addHandler(generation_handler)
    generation_logger.setLevel(logging.INFO)
    loggers['generation'] = generation_logger
    
    # Queue logger - Queue monitoring and RTMP streaming
    queue_logger = logging.getLogger('queue')
    queue_handler = logging.FileHandler('logs/queue.log')
    queue_handler.setFormatter(formatter)
    queue_logger.addHandler(queue_handler)
    queue_logger.setLevel(logging.INFO)
    loggers['queue'] = queue_logger
    
    return loggers

# Global loggers - import these in other files
_loggers = setup_loggers()

server_log = _loggers['server']
generation_log = _loggers['generation'] 
queue_log = _loggers['queue']