from dataclasses import dataclass
from pydantic import BaseModel, Field


@dataclass
class Server:
    """Represents a monitored server."""
    id: str
    name: str
    host: str
    port: int
    status: str = "unknown"

    def base_url(self) -> str:
        """Return the base URL for this server."""
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    """Incoming server registration request."""
    name: str = Field(..., min_length=1)
    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)


class ServerOut(BaseModel):
    """Outgoing server response."""
    id: str
    name: str
    host: str
    port: int
    status: str

    @staticmethod
    def from_server(server: Server) -> "ServerOut":
        """Convert Server dataclass to ServerOut model."""
        return ServerOut(
            id=server.id,
            name=server.name,
            host=server.host,
            port=server.port,
            status=server.status
        )


class AlertConfig(BaseModel):
    """Pydantic model for alert configuration."""
    cpu_threshold: float = Field(default=85.0, ge=0.0, le=100.0)
    memory_threshold: float = Field(default=90.0, ge=0.0, le=100.0)
