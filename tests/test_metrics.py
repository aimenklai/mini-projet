from api.metrics import get_system_metrics


def test_get_system_metrics_returns_dict():
    """Test that get_system_metrics returns a dictionary."""
    metrics = get_system_metrics()
    assert isinstance(metrics, dict)


def test_get_system_metrics_contains_required_keys():
    """Test that metrics contain all required keys."""
    metrics = get_system_metrics()
    required_keys = {
        "cpu_percent", "memory_percent", "disk_percent",
        "bytes_sent", "bytes_recv"
    }
    assert required_keys.issubset(metrics.keys())


def test_cpu_percent_in_range():
    """Test that CPU percent is between 0 and 100."""
    metrics = get_system_metrics()
    assert 0 <= metrics["cpu_percent"] <= 100


def test_memory_percent_in_range():
    """Test that memory percent is between 0 and 100."""
    metrics = get_system_metrics()
    assert 0 <= metrics["memory_percent"] <= 100


def test_disk_percent_in_range():
    """Test that disk percent is between 0 and 100."""
    metrics = get_system_metrics()
    assert 0 <= metrics["disk_percent"] <= 100


def test_memory_gb_is_positive():
    """Test that memory in GB is a positive number."""
    metrics = get_system_metrics()
    assert metrics["memory_gb"] >= 0


def test_network_metrics_are_positive():
    """Test that network sent/received bytes are non-negative."""
    metrics = get_system_metrics()
    assert metrics["bytes_sent"] >= 0
    assert metrics["bytes_recv"] >= 0


def test_get_disk_partitions_metrics():
    """Test get_disk_partitions_metrics returns valid partitions."""
    from api.metrics import get_disk_partitions_metrics
    partitions = get_disk_partitions_metrics()
    assert isinstance(partitions, list)
    if len(partitions) > 0:
        p = partitions[0]
        assert "device" in p
        assert "mountpoint" in p
        assert "fstype" in p
        assert "total" in p
        assert "used" in p
        assert "free" in p
        assert "percent" in p
