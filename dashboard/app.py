import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import websocket

import os

# Configuration
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-secret-key")

st.set_page_config(page_title="DevOps Monitor Pro", layout="wide")

# Custom premium styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Title Styling */
    .title-container {
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, rgba(31, 38, 135, 0.05) 0%, rgba(255, 255, 255, 0.05) 100%);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .title-gradient {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .title-subtitle {
        color: #A0AEC0;
        font-size: 1.1rem;
        font-weight: 400;
        margin-top: 0.5rem;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(79, 172, 254, 0.4);
        box-shadow: 0 8px 40px rgba(79, 172, 254, 0.15);
        background: rgba(255, 255, 255, 0.05);
    }
    
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #A0AEC0;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: #FFFFFF;
        background: linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-sub {
        font-size: 0.8rem;
        color: #718096;
        margin-top: 0.25rem;
    }
    
    /* Alert Banners */
    .alert-card {
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        border: 1px solid transparent;
        animation: fadeIn 0.5s ease-out;
    }
    
    .alert-success {
        background: rgba(72, 187, 120, 0.1);
        border-color: rgba(72, 187, 120, 0.2);
        color: #48BB78;
    }
    
    .alert-danger {
        background: rgba(245, 101, 101, 0.1);
        border-color: rgba(245, 101, 101, 0.2);
        color: #F56565;
        box-shadow: 0 0 15px rgba(245, 101, 101, 0.1);
    }
    
    .alert-icon {
        font-size: 1.5rem;
    }
    
    .alert-content {
        font-size: 1rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "metrics_history" not in st.session_state:
    st.session_state.metrics_history = []


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


def fetch_alert_config():
    """Fetch alert thresholds from API."""
    try:
        response = requests.get(f"{API_URL}/alerts/config", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"cpu_threshold": 85.0, "memory_threshold": 90.0}


def update_alert_config(cpu_t: float, mem_t: float) -> bool:
    """Update alert thresholds on API."""
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.post(
            f"{API_URL}/alerts/config",
            json={"cpu_threshold": cpu_t, "memory_threshold": mem_t},
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to update alert config: {e}")
        return False


def fetch_disk_partitions():
    """Fetch disk partition breakdown from API."""
    try:
        response = requests.get(f"{API_URL}/metrics/disk", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


# Title Header
st.markdown("""
<div class="title-container">
    <h1 class="title-gradient">📊 DevOps Monitor Pro</h1>
    <p class="title-subtitle">Real-time infrastructure health and performance overview</p>
</div>
""", unsafe_allow_html=True)


# Sidebar settings
st.sidebar.title("⚙️ Global Settings")
st.sidebar.subheader("Alert Thresholds")
current_config = fetch_alert_config()

with st.sidebar.form("alert_config_form"):
    cpu_input = st.number_input("CPU Threshold (%)", min_value=0.0, max_value=100.0, value=float(
        current_config["cpu_threshold"]), step=5.0)
    mem_input = st.number_input("Memory Threshold (%)", min_value=0.0, max_value=100.0, value=float(
        current_config["memory_threshold"]), step=5.0)
    save_alert = st.form_submit_button("Update Thresholds")
    if save_alert:
        if update_alert_config(cpu_input, mem_input):
            st.sidebar.success("Thresholds updated successfully!")
            st.rerun()

# Create tabs
tab1, tab2 = st.tabs(["📈 Metrics Stream", "🖥️ Monitored Servers"])

# Tab 1: Live WebSocket Metrics Stream
with tab1:
    st.header("Live System Performance")

    # Placeholders for WebSockets stream updates
    alert_placeholder = st.empty()
    tiles_placeholder = st.empty()
    chart_placeholder = st.empty()
    disk_placeholder = st.empty()

    # Connect and stream
    ws_url = f"{API_URL.replace('http://', 'ws://')}/ws/metrics"

    try:
        ws = websocket.create_connection(ws_url, timeout=5)

        while True:
            try:
                msg = ws.recv()
                metrics = json.loads(msg)
            except Exception:
                alert_placeholder.warning(
                    "⚠️ WebSocket connection closed. Attempting reconnect...")
                break

            # 1. Update Alert Banner
            with alert_placeholder.container():
                if metrics.get("alert"):
                    st.markdown(f"""
                    <div class="alert-card alert-danger">
                        <span class="alert-icon">⚠️</span>
                        <div class="alert-content">
                            <strong>CRITICAL WARNING:</strong> System threshold
                            breached! (CPU: {metrics['cpu_percent']:.1f}% vs
                            {cpu_input}%, Memory:
                            {metrics['memory_percent']:.1f}% vs
                            {mem_input}%)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="alert-card alert-success">
                        <span class="alert-icon">🟢</span>
                        <div class="alert-content">
                            <strong>All systems normal:</strong> Performance is well within limits.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # 2. Update Tiles (CPU, Memory, Disk, Network)
            with tiles_placeholder.container():
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">CPU Utilization</div>
                        <div class="metric-value">{metrics['cpu_percent']:.1f}%</div>
                        <div class="metric-sub">Real-time workload</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Memory Usage</div>
                        <div class="metric-value">{metrics['memory_percent']:.1f}%</div>
                        <div class="metric-sub">{metrics['memory_gb']:.1f} GB of RAM used</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Disk Storage</div>
                        <div class="metric-value">{metrics['disk_percent']:.1f}%</div>
                        <div class="metric-sub">Root volume '/' usage</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    # Bytes to Megabytes conversion
                    sent_mb = metrics['bytes_sent'] / (1024 * 1024)
                    recv_mb = metrics['bytes_recv'] / (1024 * 1024)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Network IO</div>
                        <div class="metric-value">{sent_mb:.1f}M / {recv_mb:.1f}M</div>
                        <div class="metric-sub">Sent / Received Bytes</div>
                    </div>
                    """, unsafe_allow_html=True)

            # 3. Update resource usage history chart
            metrics_with_time = {
                "time": datetime.now(),
                "CPU %": metrics['cpu_percent'],
                "Memory %": metrics['memory_percent']
            }
            st.session_state.metrics_history.append(metrics_with_time)

            # Keep last 60 points
            if len(st.session_state.metrics_history) > 60:
                st.session_state.metrics_history.pop(0)

            with chart_placeholder.container():
                st.markdown(
                    "<h3 style='margin-top: 1.5rem; "
                    "margin-bottom: 0.5rem;'>"
                    "📈 CPU & Memory Utilization History</h3>",
                    unsafe_allow_html=True
                )
                if len(st.session_state.metrics_history) > 1:
                    chart_data = pd.DataFrame(st.session_state.metrics_history)
                    chart_data.set_index("time", inplace=True)
                    st.line_chart(chart_data[["CPU %", "Memory %"]])

            # 4. Display Disk Partition breakdown
            with disk_placeholder.container():
                st.markdown(
                    "<h3 style='margin-top: 2rem; "
                    "margin-bottom: 0.5rem;'>"
                    "📁 Disk Partitions Breakdown</h3>",
                    unsafe_allow_html=True
                )
                disk_data = fetch_disk_partitions()
                if disk_data:
                    df_disk = pd.DataFrame(disk_data)

                    def format_bytes(b):
                        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                            if b < 1024:
                                return f"{b:.1f} {unit}"
                            b /= 1024
                        return f"{b:.1f} PB"
                    df_disk["total"] = df_disk["total"].apply(format_bytes)
                    df_disk["used"] = df_disk["used"].apply(format_bytes)
                    df_disk["free"] = df_disk["free"].apply(format_bytes)
                    df_disk["percent"] = df_disk["percent"].apply(
                        lambda p: f"{p:.1f}%")
                    st.dataframe(df_disk, use_container_width=True)
                else:
                    st.info("No partition information retrieved.")

    except Exception:
        alert_placeholder.info(
            "🔌 API Metrics WebSocket stream is offline. "
            "Please make sure the FastAPI backend is running."
        )
        if st.button("Retry connection"):
            st.rerun()


# Tab 2: Monitored Servers management
with tab2:
    st.header("Server Management & Status")

    servers_list = fetch_servers()

    if servers_list:
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
        st.info("No remote servers are currently registered for monitoring.")

    st.divider()

    # Registration Form
    st.subheader("➕ Register a New Server")
    with st.form("register_server_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            name = st.text_input(
                "Server Name", placeholder="e.g. Production Database")

        with col2:
            host = st.text_input(
                "Host Address", placeholder="e.g. 192.168.1.50 or localhost")

        with col3:
            port = st.number_input("Port", min_value=1,
                                   max_value=65535, value=8000)

        submitted = st.form_submit_button("Add Server")

        if submitted:
            if name and host:
                if register_server(name, host, int(port)):
                    st.success(f"Successfully added server '{name}'")
                    st.rerun()
            else:
                st.error("All form fields (Name, Host, Port) are required.")

    st.divider()

    # Server Actions
    if servers_list:
        st.subheader("⚡ Quick Actions")
        server_options = {s["name"]: s["id"] for s in servers_list}

        col1, col2 = st.columns(2)

        with col1:
            selected_server = st.selectbox(
                "Select Server to Check", list(server_options.keys()))
            if st.button("Trigger Immediate Health Check"):
                server_id = server_options[selected_server]
                if trigger_health_check(server_id):
                    st.success(
                        f"Health check task queued for '{selected_server}'. Refreshing...")
                    st.cache_data.clear()
                    st.rerun()

        with col2:
            delete_server_name = st.selectbox(
                "Select Server to Delete", list(server_options.keys()), key="delete")
            if st.button("Remove Server"):
                server_id = server_options[delete_server_name]
                if delete_server(server_id):
                    st.success(
                        f"Server '{delete_server_name}' successfully removed.")
                    st.cache_data.clear()
                    st.rerun()
