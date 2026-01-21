import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import platform
import time

# --- 1. FULLY AUTOMATED HARDWARE ENGINE ---
def get_wifi_details():
    """Automatically detects hardware. Switches to Simulation only if hardware is blocked."""
    os_name = platform.system()
    
    try:
        # --- WINDOWS AUTOMATIC ---
        if os_name == "Windows":
            cmd = "netsh wlan show interfaces"
            output = subprocess.check_output(cmd, shell=True).decode(errors="ignore")
            name, strength = "Offline", 0
            for line in output.split('\n'):
                if " SSID" in line and "BSSID" not in line: name = line.split(":")[1].strip()
                if "Signal" in line: strength = int(line.split(":")[1].strip().replace("%", ""))
            if name != "Offline": return name, strength
            
        # --- MACOS AUTOMATIC ---
        elif os_name == "Darwin":
            cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
            output = subprocess.check_output(cmd, shell=True).decode(errors="ignore")
            name, rssi = "Searching...", -50
            for line in output.split('\n'):
                if " SSID" in line: name = line.split(":")[1].strip()
                if "agrCtlRSSI" in line: rssi = int(line.split(":")[1].strip())
            strength = min(max(2 * (rssi + 100), 0), 100)
            return name, strength

        # --- LINUX AUTOMATIC ---
        elif os_name == "Linux":
            cmd = "nmcli -f IN-USE,SSID,SIGNAL device wifi | grep '^\*'"
            output = subprocess.check_output(cmd, shell=True).decode(errors="ignore")
            parts = output.split()
            if len(parts) >= 3: return parts[1], int(parts[2])

    except Exception:
        pass # Hardware blocked (Common on Web Browsers)

    # --- AUTOMATED WEB SIMULATION ---
    # This makes the app "Work Properly" for people clicking your GitHub link.
    # It simulates a live 5G signal that fluctuates slightly every 2 seconds.
    demo_signal = 80 + np.random.randint(-5, 5) 
    return "LIVE_DEMO_MODE", demo_signal

# --- 2. PHYSICS ENGINE ---
def rssi_to_meters(signal_pct):
    if signal_pct >= 95: return 0.2
    if signal_pct >= 85: return 0.8
    if signal_pct <= 5: return 20.0
    # Log-Distance Path Loss Model for indoor signal propagation
    return round(10 ** ((95 - signal_pct) / 32), 2)

# --- 3. PRO DASHBOARD UI ---
st.set_page_config(page_title="wifivisualizer", layout="wide", page_icon="📡")

# Custom Professional Theme
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #0d1117 0%, #010409 100%); }
    .metric-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #58a6ff; text-shadow: 0 0 10px rgba(88,166,255,0.3); }
    .metric-label { font-size: 0.8rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button { width: 100%; border-radius: 8px; background: #238636; color: white; border: none; font-weight: bold;}
    .stButton>button:hover { background: #2ea043; box-shadow: 0 0 15px rgba(46,160,67,0.3); }
    </style>
    """, unsafe_allow_html=True)

# State Management
if 'points' not in st.session_state: st.session_state.points = [] 
if 'router_pos' not in st.session_state: st.session_state.router_pos = None

# Automated Hardware Scan
provider_name, curr_strength = get_wifi_details()
curr_dist = rssi_to_meters(curr_strength)

# --- HEADER ---
st.title("📡 wifivisualizer")
st.markdown("---")

# Row 1: Real-time Metrics
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">NETWORK ID</div><div class="metric-value" style="font-size:1.1rem;">{provider_name}</div></div>', unsafe_allow_html=True)
with m_col2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">INTENSITY</div><div class="metric-value">{curr_strength}%</div></div>', unsafe_allow_html=True)
with m_col3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">EST. RANGE</div><div class="metric-value">{curr_dist}m</div></div>', unsafe_allow_html=True)
with m_col4:
    status = "LOCKED" if st.session_state.router_pos else "SCANNING"
    color = "#3fb950" if st.session_state.router_pos else "#f85149"
    st.markdown(f'<div class="metric-card"><div class="metric-label">AI TRACKER</div><div class="metric-value" style="color:{color};">{status}</div></div>', unsafe_allow_html=True)

st.write("")

# --- MAIN INTERFACE ---
col_map, col_sidebar = st.columns([2.5, 1])

with col_sidebar:
    st.subheader("🛠️ Calibration")
    st.caption("Locate your router by recording signal data from 3 different spots.")
    
    # Progress Tracker
    progress = len(st.session_state.points) / 3
    st.progress(progress)
    
    st.markdown("**Your Relative Position:**")
    ux = st.slider("X (meters)", 0.0, 20.0, 5.0)
    uy = st.slider("Y (meters)", 0.0, 20.0, 5.0)
    
    if st.button("📌 Record Calibration Data"):
        if len(st.session_state.points) < 3:
            st.session_state.points.append((ux, uy, curr_dist))
            if len(st.session_state.points) == 3:
                # Automated Weighted Trilateration
                pts = st.session_state.points
                w = [1.0/max(p[2], 0.1) for p in pts]
                tw = sum(w)
                rx = sum(pts[i][0]*w[i] for i in range(3))/tw
                ry = sum(pts[i][1]*w[i] for i in range(3))/tw
                st.session_state.router_pos = (rx, ry)
            st.rerun()
    
    if st.button("🔄 Reset System"):
        st.session_state.points, st.session_state.router_pos = [], None
        st.rerun()

    st.divider()
    st.subheader("🗒️ Data Log")
    for i, p in enumerate(st.session_state.points):
        st.caption(f"P{i+1}: Pos({p[0]}, {p[1]}) | Signal Dist: {p[2]}m")

with col_map:
    grid = 20
    x_dim, y_dim = np.meshgrid(np.linspace(0, grid, 100), np.linspace(0, grid, 100))
    
    # Determine Source Position
    rx, ry = st.session_state.router_pos if st.session_state.router_pos else (10, 10)
    
    # Generate Heatmap
    dist_map = np.sqrt((x_dim - rx)**2 + (y_dim - ry)**2)
    signal_map = 100 - (dist_map * 5) + (np.sin(dist_map * 3) * 2)

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    # Radar View
    ax.contourf(x_dim, y_dim, signal_map, levels=15, cmap='viridis', alpha=0.3)
    ax.contour(x_dim, y_dim, signal_map, levels=15, cmap='viridis', alpha=0.5, linewidths=0.5)

    # UI Markers
    ax.scatter(rx, ry, c='#58a6ff', marker='H', s=450, edgecolors='white', linewidth=2, label="Signal Source", zorder=5)
    ax.scatter(ux, uy, c='#f85149', marker='o', s=250, edgecolors='white', linewidth=2, label="User Device", zorder=6)
    
    # Distance Annotation
    ax.plot([rx, ux], [ry, uy], color='white', linestyle='--', alpha=0.4)
    dist_calc = np.sqrt((ux-rx)**2 + (uy-ry)**2)
    ax.text((rx+ux)/2, (ry+uy)/2, f"{round(dist_calc, 1)}m", color='white', fontweight='bold', bbox=dict(facecolor='#161b22', alpha=0.7, edgecolor='none'))

    ax.set_xlim(0, grid)
    ax.set_ylim(0, grid)
    ax.axis('off') 
    ax.legend(loc='upper right', facecolor='#161b22', labelcolor='white', edgecolor='#30363d')
    st.pyplot(fig)

# Automatically refresh every 2 seconds for real-time feel
time.sleep(2)
st.rerun()
