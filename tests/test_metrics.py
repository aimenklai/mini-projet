import pytest
from api.metrics import get_system_metrics


def test_get_system_metrics_returns_dict():
    """Test that get_system_metrics returns a dictionary."""
    metrics = get_system_metrics()
    assert isinstance(metrics, dict)


def test_get_system_metrics_contains_required_keys():
    """Test that metrics contain all required keys."""
    metrics = get_system_metrics()
    required_keys = {"cpu_percent", "memory_percent", "disk_percent"}
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
