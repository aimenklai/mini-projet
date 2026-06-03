import pytest
from fastapi.testclient import TestClient
from api.main import app, servers


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def cleanup_servers():
    """Clean up servers before and after each test."""
    servers.clear()
    yield
    servers.clear()


def test_health_endpoint(client, cleanup_servers):
    """Test GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint(client, cleanup_servers):
    """Test GET /metrics returns 200 and includes cpu_percent."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "memory_percent" in data
    assert "disk_percent" in data


def test_post_servers_without_key_returns_403(client, cleanup_servers):
    """Test POST /servers without API key returns 403."""
    response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000}
    )
    assert response.status_code == 403


def test_post_servers_with_invalid_key_returns_403(client, cleanup_servers):
    """Test POST /servers with invalid API key returns 403."""
    response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 403


def test_post_servers_with_valid_key_returns_201(client, cleanup_servers):
    """Test POST /servers with valid key returns 201."""
    response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Server"
    assert data["host"] == "localhost"
    assert data["port"] == 8000
    assert data["status"] == "unknown"
    assert "id" in data


def test_server_appears_in_list(client, cleanup_servers):
    """Test that registered server appears in GET /servers."""
    # Register a server
    post_response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    server_id = post_response.json()["id"]
    
    # List servers
    get_response = client.get("/servers")
    assert get_response.status_code == 200
    servers_list = get_response.json()
    assert len(servers_list) == 1
    assert servers_list[0]["id"] == server_id


def test_get_server_by_id(client, cleanup_servers):
    """Test GET /servers/{id} returns the specific server."""
    # Register a server
    post_response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    server_id = post_response.json()["id"]
    
    # Get specific server
    get_response = client.get(f"/servers/{server_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == server_id
    assert data["name"] == "Test Server"


def test_get_nonexistent_server_returns_404(client, cleanup_servers):
    """Test GET /servers/{nonexistent_id} returns 404."""
    response = client.get("/servers/nonexistent-id")
    assert response.status_code == 404


def test_delete_server_without_key_returns_403(client, cleanup_servers):
    """Test DELETE /servers/{id} without key returns 403."""
    # Register a server
    post_response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    server_id = post_response.json()["id"]
    
    # Try to delete without key
    delete_response = client.delete(f"/servers/{server_id}")
    assert delete_response.status_code == 403


def test_delete_server_with_valid_key(client, cleanup_servers):
    """Test DELETE /servers/{id} with valid key succeeds."""
    # Register a server
    post_response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    server_id = post_response.json()["id"]
    
    # Delete with valid key
    delete_response = client.delete(
        f"/servers/{server_id}",
        headers={"X-API-Key": "dev-secret-key"}
    )
    assert delete_response.status_code == 200
    
    # Verify it's gone
    get_response = client.get(f"/servers/{server_id}")
    assert get_response.status_code == 404


def test_port_validation(client, cleanup_servers):
    """Test that port validation works."""
    # Test port < 1
    response = client.post(
        "/servers",
        json={"name": "Test", "host": "localhost", "port": 0},
        headers={"X-API-Key": "dev-secret-key"}
    )
    assert response.status_code == 422
    
    # Test port > 65535
    response = client.post(
        "/servers",
        json={"name": "Test", "host": "localhost", "port": 70000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    assert response.status_code == 422


def test_get_servers_filter_by_status(client, cleanup_servers):
    """Test filtering servers by status."""
    # Register a server
    post_response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    # Filter by status
    response = client.get("/servers?status=unknown")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "unknown"
    
    # Filter by non-matching status
    response = client.get("/servers?status=UP")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_check_server_endpoint(client, cleanup_servers):
    """Test POST /servers/{id}/check triggers health check."""
    # Register a server
    post_response = client.post(
        "/servers",
        json={"name": "Test Server", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    server_id = post_response.json()["id"]
    
    # Trigger health check
    response = client.post(f"/servers/{server_id}/check")
    assert response.status_code == 200


def test_check_nonexistent_server_returns_404(client, cleanup_servers):
    """Test POST /servers/{nonexistent_id}/check returns 404."""
    response = client.post("/servers/nonexistent-id/check")
    assert response.status_code == 404


def test_multiple_servers_polling(client, cleanup_servers):
    """Test multiple servers can be registered and polled."""
    # Register multiple servers
    for i in range(3):
        response = client.post(
            "/servers",
            json={"name": f"Server {i}", "host": "localhost", "port": 8000 + i},
            headers={"X-API-Key": "dev-secret-key"}
        )
        assert response.status_code == 201
    
    # List all servers
    response = client.get("/servers")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_server_with_invalid_name_fails(client, cleanup_servers):
    """Test that empty name is rejected."""
    response = client.post(
        "/servers",
        json={"name": "", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "dev-secret-key"}
    )
    assert response.status_code == 422


def test_server_base_url_method(cleanup_servers):
    """Test Server.base_url() method."""
    from api.models import Server
    server = Server(id="test", name="Test", host="example.com", port=3000)
    assert server.base_url() == "http://example.com:3000"


def test_server_out_from_server(cleanup_servers):
    """Test ServerOut.from_server() conversion."""
    from api.models import Server, ServerOut
    server = Server(id="test-123", name="My Server", host="localhost", port=8080, status="UP")
    server_out = ServerOut.from_server(server)
    assert server_out.id == "test-123"
    assert server_out.name == "My Server"
    assert server_out.status == "UP"
