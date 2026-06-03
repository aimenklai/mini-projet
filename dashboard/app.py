import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "dev-secret-key"

st.set_page_config(page_title="DevOps Monitor", layout="wide")

# Initialize session state
if "metrics_history" not in st.session_state:
    st.session_state.metrics_history = []


@st.cache_data(ttl=2)
def fetch_metrics():
    """Fetch current metrics from the API."""
    try:
        response = requests.get(f"{API_URL}/metrics", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch metrics: {e}")
        return None


@st.cache_data(ttl=5)
def fetch_servers():
    """Fetch list of servers from the API."""
    try:
        response = requests.get(f"{API_URL}/servers", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch servers: {e}")
        return []


def register_server(name: str, host: str, port: int) -> bool:
    """Register a new server."""
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.post(
            f"{API_URL}/servers",
            json={"name": name, "host": host, "port": port},
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Failed to register server: {e}")
        return False


def delete_server(server_id: str) -> bool:
    """Delete a server."""
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.delete(
            f"{API_URL}/servers/{server_id}",
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Failed to delete server: {e}")
        return False


def trigger_health_check(server_id: str) -> bool:
    """Trigger a health check for a server."""
    try:
        response = requests.post(
            f"{API_URL}/servers/{server_id}/check",
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to trigger health check: {e}")
        return False


def get_status_color(status: str) -> str:
    """Return color for status."""
    colors = {
        "UP": "🟢",
        "DEGRADED": "🟡",
        "DOWN": "🔴",
        "unknown": "⚪"
    }
    return colors.get(status, "⚪")


# Main title
st.title("📊 DevOps Monitoring Dashboard")

# Create tabs
tab1, tab2 = st.tabs(["📈 Metrics", "🖥️ Servers"])

# Tab 1: Metrics
with tab1:
    st.header("System Metrics")
    
    metrics = fetch_metrics()
    
    if metrics:
        # Display metrics as tiles
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("CPU", f"{metrics['cpu_percent']:.1f}%")
        
        with col2:
            st.metric("Memory", f"{metrics['memory_percent']:.1f}%")
        
        with col3:
            st.metric("Memory Used", f"{metrics['memory_gb']} GB")
        
        with col4:
            st.metric("Disk", f"{metrics['disk_percent']:.1f}%")
        
        # Add to history
        metrics_with_time = {
            "time": datetime.now(),
            "cpu_percent": metrics['cpu_percent'],
            "memory_percent": metrics['memory_percent']
        }
        st.session_state.metrics_history.append(metrics_with_time)
        
        # Keep only last 60 data points
        if len(st.session_state.metrics_history) > 60:
            st.session_state.metrics_history.pop(0)
        
        # Display chart if we have data
        if len(st.session_state.metrics_history) > 1:
            chart_data = pd.DataFrame(st.session_state.metrics_history)
            chart_data.set_index("time", inplace=True)
            st.line_chart(chart_data[["cpu_percent", "memory_percent"]])
        
        # Auto-refresh
        st.rerun()


# Tab 2: Servers
with tab2:
    st.header("Monitored Servers")
    
    # Fetch and display servers
    servers_list = fetch_servers()
    
    if servers_list:
        # Display servers in a dataframe with status colors
        servers_data = []
        for server in servers_list:
            servers_data.append({
                "ID": server["id"][:8] + "...",
                "Name": server["name"],
                "Host": server["host"],
                "Port": server["port"],
                "Status": f"{get_status_color(server['status'])} {server['status']}"
            })
        
        df = pd.DataFrame(servers_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No servers registered yet.")
    
    st.divider()
    
    # Register new server form
    st.subheader("Register New Server")
    with st.form("register_server_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Server Name")
        
        with col2:
            host = st.text_input("Host")
        
        with col3:
            port = st.number_input("Port", min_value=1, max_value=65535, value=8000)
        
        submitted = st.form_submit_button("Register Server")
        
        if submitted:
            if name and host:
                if register_server(name, host, int(port)):
                    st.success("Server registered successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all fields")
    
    st.divider()
    
    # Health check and delete
    st.subheader("Server Actions")
    servers_list = fetch_servers()
    
    if servers_list:
        server_options = {s["name"]: s["id"] for s in servers_list}
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_server = st.selectbox("Select Server", list(server_options.keys()))
            if st.button("Trigger Health Check"):
                server_id = server_options[selected_server]
                if trigger_health_check(server_id):
                    st.success("Health check triggered!")
                    st.rerun()
        
        with col2:
            delete_server_name = st.selectbox("Select Server to Delete", list(server_options.keys()), key="delete")
            if st.button("Delete Server"):
                server_id = server_options[delete_server_name]
                if delete_server(server_id):
                    st.success("Server deleted!")
                    st.rerun()
