import psutil


def get_system_metrics() -> dict:
    """
    Retrieve current system metrics using psutil.
    
    Returns:
        dict: Contains cpu_percent, memory_percent, memory_gb, and disk_percent
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_gb": round(memory.used / (1024 ** 3), 2),
        "disk_percent": disk.percent
    }
