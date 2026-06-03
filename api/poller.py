import asyncio
import httpx
from typing import Dict
from api.models import Server


async def poll_server(server_id: str, url: str, store: Dict[str, Server]) -> None:
    """
    Check the health of a server by hitting its /health endpoint.
    
    Args:
        server_id: The server ID to update
        url: The base URL of the server
        store: Dictionary of servers to update in place
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            
            if response.status_code == 200:
                store[server_id].status = "UP"
            else:
                store[server_id].status = "DEGRADED"
    except Exception:
        store[server_id].status = "DOWN"


async def run_poll_loop(store: Dict[str, Server], interval: int = 10) -> None:
    """
    Background task that continuously polls all servers.
    
    Args:
        store: Dictionary of servers to monitor
        interval: Time in seconds between poll cycles
    """
    while True:
        try:
            # Create tasks for all servers
            tasks = []
            for server_id, server in store.items():
                task = poll_server(server_id, server.base_url(), store)
                tasks.append(task)
            
            # Run all tasks concurrently
            if tasks:
                await asyncio.gather(*tasks)
            
            # Sleep before next poll cycle
            await asyncio.sleep(interval)
        except Exception as e:
            print(f"Error in poll loop: {e}")
            await asyncio.sleep(interval)
