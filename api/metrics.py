import psutil


def get_system_metrics() -> dict:
    """
    Retrieve current system metrics using psutil.

    Returns:
        dict: Contains cpu_percent, memory_percent, memory_gb,
              disk_percent, bytes_sent, bytes_recv
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_gb": round(memory.used / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv
    }


def get_disk_partitions_metrics() -> list:
    """
    Retrieve usage details for all disk partitions.
    """
    partitions = psutil.disk_partitions(all=False)
    result = []
    for partition in partitions:
        # Ignore empty or unmounted partition lines
        if not partition.device or not partition.mountpoint:
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            result.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            })
        except (PermissionError, FileNotFoundError):
            continue
        except Exception:
            continue
    return result
