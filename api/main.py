import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from api.auth import verify_api_key
from api.metrics import get_system_metrics
from api.models import Server, ServerIn, ServerOut
from api.poller import run_poll_loop


# In-memory server store
servers: Dict[str, Server] = {}
poll_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage app startup and shutdown.
    Starts the background health-check polling on startup,
    cancels it on shutdown.
    """
    global poll_task
    
    # Startup
    poll_task = asyncio.create_task(run_poll_loop(servers, interval=10))
    print("Background polling task started")
    
    yield
    
    # Shutdown
    if poll_task:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass
    print("Background polling task cancelled")


app = FastAPI(title="DevOps Monitor API", lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    """Get current system metrics."""
    return get_system_metrics()


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """
    WebSocket endpoint that streams metrics every second.
    """
    await websocket.accept()
    try:
        while True:
            metrics_data = get_system_metrics()
            await websocket.send_json(metrics_data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.post("/servers", status_code=201, response_model=ServerOut)
async def register_server(
    server_in: ServerIn,
    _: str = Depends(verify_api_key)
) -> ServerOut:
    """Register a new server to monitor."""
    server_id = str(uuid.uuid4())
    server = Server(
        id=server_id,
        name=server_in.name,
        host=server_in.host,
        port=server_in.port,
        status="unknown"
    )
    servers[server_id] = server
    return ServerOut.from_server(server)


@app.get("/servers", response_model=list[ServerOut])
async def list_servers(status: Optional[str] = Query(None)):
    """
    List all servers, optionally filtered by status.
    
    Args:
        status: Filter by status (UP, DEGRADED, DOWN, unknown)
    
    Returns:
        List of servers
    """
    result = [ServerOut.from_server(s) for s in servers.values()]
    
    if status:
        result = [s for s in result if s.status == status]
    
    return result


@app.get("/servers/{server_id}", response_model=ServerOut)
async def get_server(server_id: str):
    """Get a specific server by ID."""
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    return ServerOut.from_server(servers[server_id])


@app.delete("/servers/{server_id}")
async def delete_server(
    server_id: str,
    _: str = Depends(verify_api_key)
):
    """Delete a server from monitoring."""
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    del servers[server_id]
    return {"message": "Server deleted"}


@app.post("/servers/{server_id}/check")
async def check_server(server_id: str):
    """Trigger an immediate health check for a specific server."""
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = servers[server_id]
    
    # Trigger async health check
    asyncio.create_task(
        __import__("api.poller", fromlist=["poll_server"]).poll_server(
            server_id, server.base_url(), servers
        )
    )
    
    return {"message": f"Health check triggered for {server_id}"}
