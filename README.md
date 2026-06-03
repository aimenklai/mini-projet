# DevOps Monitoring Dashboard MVP

A full-stack DevOps monitoring application consisting of a FastAPI backend and Streamlit frontend for monitoring system metrics and server health.

## Features

- **FastAPI Backend**: Exposes system metrics (CPU, Memory, Disk) and manages monitored servers
- **Streamlit Dashboard**: Real-time visualization of system metrics and server status management
- **Health Checks**: Background polling of monitored servers with status tracking
- **WebSocket Support**: Live metrics streaming via WebSocket
- **API Key Authentication**: Secured endpoints with X-API-Key header
- **Comprehensive Tests**: Unit and integration tests with pytest

## Project Structure

```
devops-monitor/
├── api/
│   ├── __init__.py
│   ├── main.py          # FastAPI app entry point (lifespan, route registration)
│   ├── models.py        # Pydantic schemas + Server dataclass
│   ├── auth.py          # API key dependency
│   ├── metrics.py       # psutil helper — returns a dict of system stats
│   └── poller.py        # Background health-check logic
├── dashboard/
│   └── app.py           # Streamlit frontend
├── tests/
│   ├── test_metrics.py
│   └── test_routes.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aimenklai/mini-projet.git
cd mini-projet
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Start the FastAPI Backend

```bash
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Start the Streamlit Dashboard

In a new terminal:

```bash
streamlit run dashboard/app.py
```

The dashboard will be available at `http://localhost:8501`

## API Endpoints

### Health & Metrics

- `GET /health` - Health check
- `GET /metrics` - Current system metrics
- `WebSocket /ws/metrics` - Live metrics stream

### Server Management

- `POST /servers` - Register a new server (requires API key)
- `GET /servers` - List all servers
- `GET /servers/{id}` - Get specific server
- `DELETE /servers/{id}` - Delete server (requires API key)
- `POST /servers/{id}/check` - Trigger health check

## Authentication

Protected endpoints require an API key sent via the `X-API-Key` header.

**Default key (local development):** `dev-secret-key`

To use a custom key:
```bash
export API_KEY=your-secret-key
uvicorn api.main:app --reload --port 8000
```

## Running Tests

```bash
pytest tests/ -v
```

For coverage report:
```bash
pip install pytest-cov
pytest tests/ --cov=api -v
```

## Environment Variables

- `API_KEY` - API authentication key (default: `dev-secret-key`)

## API Key Header

All protected endpoints require:
```
X-API-Key: dev-secret-key
```

Example curl request:
```bash
curl -X POST http://localhost:8000/servers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{"name": "My Server", "host": "localhost", "port": 8000}'
```

## Dashboard Features

### Metrics Tab
- Real-time CPU, Memory, and Disk usage metrics
- Live chart showing CPU and Memory trends over the last 60 data points
- Auto-refresh every 2 seconds

### Servers Tab
- List of all monitored servers with status indicators
- Register new servers via form
- Trigger immediate health checks
- Delete servers from monitoring

## Server Status

- 🟢 **UP** - Server is healthy (responds to /health with 200)
- 🟡 **DEGRADED** - Server responds with non-200 status
- 🔴 **DOWN** - Server unreachable or connection error
- ⚪ **unknown** - Initial state, not yet checked

## Development Notes

- The backend automatically starts a background polling task on startup
- Polls all registered servers every 10 seconds
- All system metrics use non-blocking calls to avoid event loop blocking
- Type hints are used throughout for better IDE support and code clarity

## Testing

The project includes comprehensive tests:

- **test_metrics.py** - Unit tests for metrics collection
- **test_routes.py** - Integration tests for all API endpoints

Run tests with:
```bash
pytest tests/ -v
```

## License

MIT
