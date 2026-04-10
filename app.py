import streamlit as st
import subprocess
import os
import xml.etree.ElementTree as ET
import pandas as pd
import json
import re
import time
import threading
from pathlib import Path
from datetime import datetime
import anthropic

# ─────────────────────────────────────────────
#  PAGE CONFIG & GLOBAL CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="JMeter Executor Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── BACKGROUND ── */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1421 50%, #0a0e1a 100%);
    color: #e2e8f0;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b27 100%) !important;
    border-right: 1px solid #1e2d40;
}
[data-testid="stSidebar"] .stMarkdown { color: #94a3b8; }

/* ── CARDS ── */
.card {
    background: linear-gradient(145deg, #111827, #1a2235);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    box-shadow: 0 4px 24px rgba(0,212,255,0.05);
    transition: all 0.3s ease;
}
.card:hover {
    border-color: #00d4ff;
    box-shadow: 0 8px 32px rgba(0,212,255,0.15);
    transform: translateY(-2px);
}

/* ── METRIC CARDS ── */
.metric-card {
    background: linear-gradient(145deg, #0f172a, #1e293b);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}
.metric-card:hover { border-color: #7c3aed; box-shadow: 0 0 20px rgba(124,58,237,0.2); }
.metric-value { font-size: 2rem; font-weight: 700; color: #00d4ff; }
.metric-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

/* ── STEP HEADERS ── */
.step-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 20px;
}
.step-badge {
    background: linear-gradient(135deg, #0080ff, #00d4ff);
    color: #000;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 6px 14px;
    border-radius: 20px;
    white-space: nowrap;
}
.step-title {
    font-size: 1.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, #00d4ff, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ── THREAD GROUP CARD ── */
.tg-card {
    background: linear-gradient(145deg, #0f1e35, #162030);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    cursor: pointer;
    transition: all 0.25s ease;
}
.tg-card.selected {
    border-color: #00d4ff;
    box-shadow: 0 0 16px rgba(0,212,255,0.2);
    background: linear-gradient(145deg, #0a2040, #132840);
}

/* ── STATUS BADGES ── */
.badge-success { background:#052e16; color:#4ade80; border:1px solid #166534; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-error   { background:#2d0a0a; color:#f87171; border:1px solid #7f1d1d; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-warn    { background:#2d1f00; color:#fbbf24; border:1px solid #78350f; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-info    { background:#0a1f35; color:#60a5fa; border:1px solid #1e3a5f; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }

/* ── TERMINAL ── */
.terminal {
    background: #050a0e;
    border: 1px solid #0f3460;
    border-radius: 10px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #00ff88;
    max-height: 320px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    line-height: 1.6;
}

/* ── ERROR REC CARD ── */
.rec-card {
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
    border-left: 4px solid;
}
.rec-500 { background:#1a0a0a; border-color:#ef4444; }
.rec-403 { background:#1a1000; border-color:#f59e0b; }
.rec-401 { background:#0a0a1a; border-color:#818cf8; }
.rec-404 { background:#0a1a0a; border-color:#34d399; }
.rec-429 { background:#1a0a1a; border-color:#e879f9; }
.rec-default { background:#0f1a2a; border-color:#60a5fa; }

/* ── DIVIDER ── */
.neon-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #00d4ff44, transparent);
    margin: 30px 0;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #0080ff 0%, #00d4ff 100%);
    color: #000 !important;
    font-weight: 700;
    font-size: 0.95rem;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0,212,255,0.4);
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #0d1421 !important;
    border: 1px solid #1e3a5f !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── CHAT MESSAGES ── */
.chat-user {
    background: linear-gradient(135deg, #0a2040, #0d2d57);
    border-radius: 12px 12px 2px 12px;
    padding: 12px 18px;
    margin: 8px 0 8px auto;
    max-width: 80%;
    color: #bfdbfe;
    font-size: 0.9rem;
}
.chat-ai {
    background: linear-gradient(135deg, #1a0a2e, #2d1057);
    border-radius: 2px 12px 12px 12px;
    padding: 12px 18px;
    margin: 8px auto 8px 0;
    max-width: 85%;
    color: #e9d5ff;
    font-size: 0.9rem;
    border-left: 3px solid #7c3aed;
}

/* ── PROGRESS ── */
.stProgress > div > div > div { background: linear-gradient(90deg, #0080ff, #00d4ff) !important; }

/* ── SLIDER ── */
.stSlider > div > div > div > div { background: #00d4ff !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
defaults = {
    "jmeter_bin": "",
    "jmx_path": "",
    "thread_groups": [],
    "selected_tgs": [],
    "tg_configs": {},
    "csv_paths": {},
    "run_log": "",
    "jtl_path": "",
    "results_df": None,
    "run_complete": False,
    "anthropic_key": "",
    "chat_history": [],
    "current_step": 1,
}

# ── Pre-create all required folders at startup ──
for folder in ["C:/JMeter_Runs/scripts", "C:/JMeter_Runs/results"]:
    Path(folder).mkdir(parents=True, exist_ok=True)
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def parse_jmx(path: str):
    """Extract thread group names from JMX."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        tgs = []
        for tg in root.iter("ThreadGroup"):
            name = tg.get("testname", "Unnamed Thread Group")
            tgs.append(name)
        for tg in root.iter("SetupThreadGroup"):
            name = tg.get("testname", "Setup Thread Group")
            tgs.append(f"[Setup] {name}")
        for tg in root.iter("PostThreadGroup"):
            name = tg.get("testname", "Teardown Thread Group")
            tgs.append(f"[Teardown] {name}")
        return tgs if tgs else ["Default Thread Group"]
    except Exception as e:
        return []


def build_jmeter_cmd(bin_path, jmx_path, output_jtl, tg_configs, csv_paths):
    bin_path = bin_path.strip().strip('"').strip("'").rstrip("/\\")
    exe_name = "jmeter.bat" if os.name == "nt" else "jmeter"
    jmeter_exe = str(Path(bin_path) / exe_name)
    # Normalise all paths to forward slashes to avoid Windows escape issues
    jmx_path   = str(Path(jmx_path).resolve())
    output_jtl = str(Path(output_jtl).resolve())
    cmd = [
        jmeter_exe, "-n",
        "-t", jmx_path,
        "-l", output_jtl,
    ]
    for tg, cfg in tg_configs.items():
        safe = tg.replace(" ", "_").replace("[", "").replace("]", "")
        cmd += [
            f"-J{safe}_threads={cfg['threads']}",
            f"-J{safe}_rampup={cfg['rampup']}",
            f"-J{safe}_duration={cfg['duration']}",
            f"-J{safe}_iterations={cfg['iterations']}",
        ]
    for tg, csv in csv_paths.items():
        if csv:
            safe = tg.replace(" ", "_").replace("[", "").replace("]", "")
            cmd += [f"-J{safe}_csv={csv}"]
    return cmd


STATUS_RECS = {
    "500": {
        "title": "500 — Internal Server Error",
        "icon": "🔴",
        "cls": "rec-500",
        "causes": ["Server-side crash or unhandled exception", "Correlation issue — dynamic token/ID not captured correctly", "Request body malformed due to missing extracted variable"],
        "fixes": ["Check JMeter's Response Body for stack trace clues", "Add a Regex/JSON Extractor for dynamic values (session IDs, tokens, order IDs)", "Enable 'Save Response Data' on the failing sampler to inspect the payload", "Verify your CSV data doesn't contain null/empty values for required fields"],
    },
    "403": {
        "title": "403 — Forbidden / Token Issue",
        "icon": "🟠",
        "cls": "rec-403",
        "causes": ["Auth token expired or not extracted properly", "Missing or incorrect Authorization header", "CSRF token mismatch"],
        "fixes": ["Add a Login sampler before the failing request and extract the Bearer token using JSON Extractor", "Use a HTTP Header Manager with `Authorization: Bearer ${token}`", "Extract CSRF token from the login response and pass it in subsequent requests", "Check token expiry — add a think time or re-authenticate periodically"],
    },
    "401": {
        "title": "401 — Unauthorized",
        "icon": "🟣",
        "cls": "rec-401",
        "causes": ["No credentials provided", "Wrong username/password in CSV", "Session cookie not maintained"],
        "fixes": ["Ensure HTTP Cookie Manager is added to the Test Plan", "Verify CSV data has correct credentials", "Add a Once Only Controller around the login request"],
    },
    "404": {
        "title": "404 — Not Found",
        "icon": "🟢",
        "cls": "rec-404",
        "causes": ["Incorrect endpoint URL", "Dynamic path segment not extracted (e.g., /user/${userId})", "Environment mismatch (prod URL in dev test)"],
        "fixes": ["Use a User Defined Variable for base URL", "Extract dynamic IDs from prior responses", "Double-check path parameters in the HTTP Request sampler"],
    },
    "429": {
        "title": "429 — Too Many Requests",
        "icon": "🟤",
        "cls": "rec-429",
        "causes": ["Rate limiting triggered by the server", "Too many threads hitting the endpoint simultaneously"],
        "fixes": ["Add a Constant Throughput Timer to limit TPS", "Use a Gaussian Random Timer between requests", "Reduce thread count or increase ramp-up duration", "Coordinate with the server team to whitelist the load test IP"],
    },
}

def get_rec(code):
    return STATUS_RECS.get(str(code), {
        "title": f"{code} — Unexpected Error",
        "icon": "🔵",
        "cls": "rec-default",
        "causes": ["Unexpected server or network behavior"],
        "fixes": ["Inspect response body in JMeter View Results Tree", "Check network connectivity and server logs"],
    })


def parse_jtl(jtl_path):
    try:
        df = pd.read_csv(jtl_path)
        return df
    except Exception:
        return None


def summarise_results(df):
    if df is None or df.empty:
        return {}
    total = len(df)
    errors = df[df["success"] == False] if "success" in df.columns else pd.DataFrame()
    avg_rt = df["elapsed"].mean() if "elapsed" in df.columns else 0
    max_rt = df["elapsed"].max() if "elapsed" in df.columns else 0
    min_rt = df["elapsed"].min() if "elapsed" in df.columns else 0
    err_rate = (len(errors) / total * 100) if total > 0 else 0
    throughput = total / (df["elapsed"].sum() / 1000) if "elapsed" in df.columns and df["elapsed"].sum() > 0 else 0
    status_counts = df["responseCode"].value_counts().to_dict() if "responseCode" in df.columns else {}
    return {
        "total": total,
        "errors": len(errors),
        "err_rate": round(err_rate, 2),
        "avg_rt": round(avg_rt, 2),
        "max_rt": round(max_rt, 2),
        "min_rt": round(min_rt, 2),
        "throughput": round(throughput, 2),
        "status_counts": status_counts,
    }


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px;'>
        <div style='font-size:2.5rem;'>⚡</div>
        <div style='font-size:1.2rem; font-weight:800; background:linear-gradient(90deg,#00d4ff,#7c3aed);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            JMeter Executor Pro
        </div>
        <div style='font-size:0.7rem; color:#475569; margin-top:4px;'>Performance Testing Dashboard</div>
    </div>
    <hr style='border-color:#1e2d40; margin:10px 0;'>
    """, unsafe_allow_html=True)

    steps = [
        ("1", "JMeter Setup", "🔧"),
        ("2", "JMX Upload", "📁"),
        ("3", "Thread Groups", "🧵"),
        ("4", "CSV Config", "📋"),
        ("5", "Scenario Design", "⚙️"),
        ("6", "Dry Run", "▶️"),
        ("7", "Results & Analysis", "📊"),
        ("8", "AI Insights", "🤖"),
    ]

    for num, label, icon in steps:
        active = str(st.session_state.current_step) == num
        bg = "linear-gradient(90deg,#0a2040,#0d3060)" if active else "transparent"
        border = "1px solid #00d4ff" if active else "1px solid transparent"
        st.markdown(f"""
        <div style='padding:10px 14px; border-radius:10px; background:{bg};
                    border:{border}; margin:3px 0; cursor:pointer; transition:all 0.2s;'>
            <span style='font-size:1.1rem;'>{icon}</span>
            <span style='margin-left:8px; font-size:0.88rem;
                         color:{"#00d4ff" if active else "#94a3b8"};
                         font-weight:{"700" if active else "400"};'>
                Step {num} — {label}
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    if st.session_state.run_complete:
        st.markdown('<span class="badge-success">✓ Run Complete</span>', unsafe_allow_html=True)
    elif st.session_state.jmx_path:
        st.markdown('<span class="badge-info">● JMX Loaded</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-warn">○ Not Configured</span>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN TITLE
# ─────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding:30px 0 10px;'>
    <h1 style='font-size:2.8rem; font-weight:900; margin:0;
               background:linear-gradient(90deg,#00d4ff,#7c3aed,#00d4ff);
               background-size:200%; -webkit-background-clip:text;
               -webkit-text-fill-color:transparent;'>
        ⚡ JMeter Executor Pro
    </h1>
    <p style='color:#475569; font-size:0.95rem; margin-top:8px;'>
        AI-Powered Performance Testing · Smart Error Analysis · Real-time Insights
    </p>
</div>
<div class='neon-divider'></div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 1 — JMETER SETUP
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 1</span>
    <span class='step-title'>JMeter Setup</span>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        bin_input = st.text_input(
            "🔧 JMeter /bin Folder Path",
            value=st.session_state.jmeter_bin,
            placeholder="e.g. C:/apache-jmeter-5.6.3/bin  or  /opt/jmeter/bin",
            help="Provide the full path to JMeter's bin directory"
        )
    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        validate_btn = st.button("✔ Validate", key="validate_bin")

    if validate_btn and bin_input:
        st.session_state.jmeter_bin = bin_input
        clean_bin = bin_input.strip().strip('"').strip("'").rstrip("/\\")
        exe = "jmeter.bat" if os.name == "nt" else "jmeter"
        full_exe = str(Path(clean_bin) / exe)
        if os.path.isfile(full_exe):
            st.success(f"✅ JMeter found at `{full_exe}`")
            st.session_state.current_step = max(st.session_state.current_step, 2)
        elif os.path.isdir(clean_bin):
            st.warning(f"⚠️ Directory exists but `{exe}` not found inside. Check your JMeter installation.")
        else:
            st.error("❌ Path does not exist. Please verify the bin folder path.")
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 2 — JMX UPLOAD
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 2</span>
    <span class='step-title'>JMX File Upload</span>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "📁 Upload your JMX Test Plan",
        type=["jmx"],
        help="Upload the JMeter test plan file (.jmx)"
    )
    if uploaded:
        save_dir = Path("C:/JMeter_Runs/scripts")
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / uploaded.name
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.session_state.jmx_path = str(save_path)

        tgs = parse_jmx(str(save_path))
        st.session_state.thread_groups = tgs

        st.success(f"✅ **{uploaded.name}** uploaded successfully — found **{len(tgs)} Thread Group(s)**")
        st.session_state.current_step = max(st.session_state.current_step, 3)
    elif st.session_state.jmx_path:
        st.info(f"📌 Currently loaded: `{st.session_state.jmx_path}`")
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 3 — THREAD GROUP SELECTION
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 3</span>
    <span class='step-title'>Thread Group Selection</span>
</div>
""", unsafe_allow_html=True)

if st.session_state.thread_groups:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#64748b; font-size:0.9rem;'>Found <b style='color:#00d4ff'>{len(st.session_state.thread_groups)}</b> thread group(s). Select the ones to include in this run:</p>", unsafe_allow_html=True)
    cols = st.columns(min(len(st.session_state.thread_groups), 3))
    selected = []
    for i, tg in enumerate(st.session_state.thread_groups):
        with cols[i % len(cols)]:
            checked = st.checkbox(
                f"🧵 {tg}",
                value=(tg in st.session_state.selected_tgs),
                key=f"tg_{i}"
            )
            if checked:
                selected.append(tg)
    st.session_state.selected_tgs = selected
    if selected:
        st.markdown(f"<p style='color:#4ade80; font-size:0.85rem; margin-top:8px;'>✓ {len(selected)} thread group(s) selected</p>", unsafe_allow_html=True)
        st.session_state.current_step = max(st.session_state.current_step, 4)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='card'><p style='color:#475569;'>⬆️ Upload a JMX file to detect thread groups.</p></div>", unsafe_allow_html=True)


st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 4 — CSV CONFIGURATION
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 4</span>
    <span class='step-title'>CSV Configuration</span>
</div>
""", unsafe_allow_html=True)

if st.session_state.selected_tgs:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:0.9rem;'>Optionally provide a CSV data file path for each thread group:</p>", unsafe_allow_html=True)
    for tg in st.session_state.selected_tgs:
        c1, c2 = st.columns([3, 1])
        with c1:
            csv_val = st.text_input(
                f"📋 CSV for: {tg}",
                value=st.session_state.csv_paths.get(tg, ""),
                placeholder="/path/to/data.csv (leave blank if not needed)",
                key=f"csv_{tg}"
            )
            st.session_state.csv_paths[tg] = csv_val
        with c2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if csv_val and os.path.isfile(csv_val):
                st.markdown('<span class="badge-success">✓ Found</span>', unsafe_allow_html=True)
            elif csv_val:
                st.markdown('<span class="badge-error">✗ Not found</span>', unsafe_allow_html=True)
    st.session_state.current_step = max(st.session_state.current_step, 5)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='card'><p style='color:#475569;'>⬆️ Select thread groups first.</p></div>", unsafe_allow_html=True)


st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 5 — SCENARIO DESIGNER
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 5</span>
    <span class='step-title'>Scenario Designer</span>
</div>
""", unsafe_allow_html=True)

if st.session_state.selected_tgs:
    for tg in st.session_state.selected_tgs:
        cfg = st.session_state.tg_configs.get(tg, {"threads": 10, "rampup": 30, "duration": 60, "iterations": -1})
        st.markdown(f"""
        <div style='margin-bottom:6px; padding:10px 16px; background:linear-gradient(90deg,#0a2040,transparent);
                    border-left:3px solid #00d4ff; border-radius:6px;'>
            <span style='font-weight:700; color:#00d4ff;'>🧵 {tg}</span>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            threads = st.number_input("👥 Threads", min_value=1, max_value=10000, value=cfg["threads"], key=f"t_{tg}", help="Number of virtual users")
        with c2:
            rampup = st.number_input("📈 Ramp-up (s)", min_value=0, max_value=3600, value=cfg["rampup"], key=f"r_{tg}", help="Time to reach full thread count")
        with c3:
            duration = st.number_input("⏱ Duration (s)", min_value=1, max_value=86400, value=cfg["duration"], key=f"d_{tg}", help="Total test duration")
        with c4:
            iterations = st.number_input("🔁 Iterations", min_value=-1, max_value=100000, value=cfg["iterations"], key=f"i_{tg}", help="-1 = infinite (use duration)")
        st.session_state.tg_configs[tg] = {
            "threads": threads, "rampup": rampup,
            "duration": duration, "iterations": iterations
        }
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.session_state.current_step = max(st.session_state.current_step, 6)
else:
    st.markdown("<div class='card'><p style='color:#475569;'>⬆️ Select thread groups to configure scenarios.</p></div>", unsafe_allow_html=True)


st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 6 — DRY RUN
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 6</span>
    <span class='step-title'>Dry Run Execution</span>
</div>
""", unsafe_allow_html=True)

ready = (
    bool(st.session_state.jmeter_bin) and
    bool(st.session_state.jmx_path) and
    bool(st.session_state.selected_tgs)
)

if not ready:
    missing = []
    if not st.session_state.jmeter_bin: missing.append("JMeter bin path")
    if not st.session_state.jmx_path: missing.append("JMX file")
    if not st.session_state.selected_tgs: missing.append("Thread groups")
    st.markdown(f"<div class='card'><p style='color:#f87171;'>⚠️ Complete the following before running: <b>{', '.join(missing)}</b></p></div>", unsafe_allow_html=True)
else:
    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        run_btn = st.button("▶️  START DRY RUN", key="dry_run", use_container_width=True)
    with col_info:
        tg_summary = ", ".join(st.session_state.selected_tgs[:2])
        if len(st.session_state.selected_tgs) > 2:
            tg_summary += f" +{len(st.session_state.selected_tgs)-2} more"
        st.markdown(f"""
        <div style='padding:12px 18px; background:#0a1421; border-radius:10px; border:1px solid #1e3a5f;'>
            <span style='color:#64748b; font-size:0.8rem;'>READY TO RUN</span><br>
            <span style='color:#e2e8f0; font-size:0.9rem;'>🧵 {tg_summary}</span>
        </div>
        """, unsafe_allow_html=True)

    if run_btn:
        results_dir = Path("C:/JMeter_Runs/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        jtl_path = str(results_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jtl")
        cmd = build_jmeter_cmd(
            st.session_state.jmeter_bin,
            st.session_state.jmx_path,
            jtl_path,
            st.session_state.tg_configs,
            st.session_state.csv_paths
        )
        st.session_state.jtl_path = jtl_path

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        prog = st.progress(0, text="Initializing JMeter...")
        log_box = st.empty()
        log_lines = [f"$ {' '.join(cmd)}", ""]

        try:
            prog.progress(10, text="Starting JMeter process...")
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True
            )

            pct = 10
            for line in process.stdout:
                log_lines.append(line.rstrip())
                pct = min(pct + 1, 90)
                prog.progress(pct, text="Running test...")
                log_box.markdown(
                    f"<div class='terminal'>{'<br>'.join(log_lines[-30:])}</div>",
                    unsafe_allow_html=True
                )

            process.wait()
            prog.progress(100, text="Complete!")
            st.session_state.run_log = "\n".join(log_lines)

            if process.returncode == 0:
                st.success("✅ Dry run completed successfully!")
                st.session_state.run_complete = True
                st.session_state.current_step = max(st.session_state.current_step, 7)
                df = parse_jtl(jtl_path)
                st.session_state.results_df = df
            else:
                st.error(f"❌ JMeter exited with code {process.returncode}. Check the log above.")
                st.session_state.run_complete = True
                st.session_state.current_step = max(st.session_state.current_step, 7)

        except FileNotFoundError:
            st.error("❌ JMeter executable not found. Please verify your bin path in Step 1.")
            log_lines.append("ERROR: JMeter executable not found at specified path.")
            st.session_state.run_log = "\n".join(log_lines)
            log_box.markdown(
                f"<div class='terminal'>{'<br>'.join(log_lines)}</div>",
                unsafe_allow_html=True
            )
        except Exception as ex:
            st.error(f"❌ Unexpected error: {ex}")


st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 7 — RESULTS & SMART ERROR ANALYSIS
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 7</span>
    <span class='step-title'>Results &amp; Smart Error Analysis</span>
</div>
""", unsafe_allow_html=True)

if st.session_state.run_complete and st.session_state.results_df is not None:
    df = st.session_state.results_df
    s = summarise_results(df)

    # ── METRIC CARDS ──
    m1, m2, m3, m4, m5 = st.columns(5)
    metrics = [
        (m1, str(s.get("total", "—")), "Total Requests"),
        (m2, str(s.get("errors", "—")), "Errors"),
        (m3, f"{s.get('err_rate', 0)}%", "Error Rate"),
        (m4, f"{s.get('avg_rt', 0)} ms", "Avg Response"),
        (m5, f"{s.get('throughput', 0)}/s", "Throughput"),
    ]
    for col, val, lbl in metrics:
        with col:
            color = "#f87171" if lbl in ("Errors", "Error Rate") and float(str(val).replace("%","").replace("/s","") or 0) > 0 else "#00d4ff"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value' style='color:{color}'>{val}</div>
                <div class='metric-label'>{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── CHARTS ──
    if "elapsed" in df.columns and "label" in df.columns:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("**📈 Response Time by Sampler**")
            rt_data = df.groupby("label")["elapsed"].mean().reset_index()
            rt_data.columns = ["Sampler", "Avg Response Time (ms)"]
            st.bar_chart(rt_data.set_index("Sampler"))
        with chart_col2:
            if "responseCode" in df.columns:
                st.markdown("**🥧 Response Code Distribution**")
                rc_data = df["responseCode"].value_counts().reset_index()
                rc_data.columns = ["Response Code", "Count"]
                st.bar_chart(rc_data.set_index("Response Code"))

    # ── ERROR ANALYSIS ──
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:1.1rem; font-weight:700; color:#f87171; margin-bottom:12px;'>
        🔍 Smart Error Recommendations
    </div>
    """, unsafe_allow_html=True)

    error_codes = []
    if "responseCode" in df.columns and "success" in df.columns:
        failed = df[df["success"] == False]
        error_codes = failed["responseCode"].dropna().unique().tolist()

    if error_codes:
        for code in error_codes:
            rec = get_rec(str(int(float(str(code)))) if str(code).replace(".","").isdigit() else str(code))
            st.markdown(f"""
            <div class='rec-card {rec["cls"]}'>
                <div style='font-size:1rem; font-weight:700; margin-bottom:10px;'>
                    {rec["icon"]} {rec["title"]}
                </div>
                <div style='color:#94a3b8; font-size:0.85rem; margin-bottom:8px;'>
                    <b style='color:#cbd5e1;'>Possible Causes:</b>
                </div>
                <ul style='color:#94a3b8; font-size:0.85rem; margin:0 0 10px; padding-left:18px;'>
                    {"".join(f"<li>{c}</li>" for c in rec["causes"])}
                </ul>
                <div style='color:#94a3b8; font-size:0.85rem; margin-bottom:8px;'>
                    <b style='color:#4ade80;'>💡 How to Fix:</b>
                </div>
                <ul style='color:#94a3b8; font-size:0.85rem; margin:0; padding-left:18px;'>
                    {"".join(f"<li>{f}</li>" for f in rec["fixes"])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:#052e16; border:1px solid #166534; border-radius:10px; padding:16px 20px; color:#4ade80;'>
            ✅ No HTTP errors detected in this run. All requests returned successful responses!
        </div>
        """, unsafe_allow_html=True)

    # ── RAW TABLE ──
    with st.expander("📄 View Raw Results Table"):
        st.dataframe(df.head(200), use_container_width=True)

elif st.session_state.run_complete:
    st.markdown("""
    <div class='card'>
        <p style='color:#fbbf24;'>⚠️ Run completed but no JTL results file was found. This can happen if JMeter exited early. Check the run log above.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div class='card'><p style='color:#475569;'>⬆️ Complete a dry run to see results here.</p></div>", unsafe_allow_html=True)


st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  STEP 8 — CLAUDE AI INSIGHTS
# ═══════════════════════════════════════════════
st.markdown("""
<div class='step-header'>
    <span class='step-badge'>STEP 8</span>
    <span class='step-title'>🤖 Claude AI Insights</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)

api_col, _ = st.columns([2, 1])
with api_col:
    api_key = st.text_input(
        "🔑 Anthropic API Key",
        value=st.session_state.anthropic_key,
        type="password",
        placeholder="sk-ant-...",
        help="Your personal Anthropic API key. Never stored."
    )
    st.session_state.anthropic_key = api_key

st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.anthropic_key:
    # Build context from results
    ctx_parts = []
    if st.session_state.run_log:
        ctx_parts.append(f"JMeter Run Log (last 80 lines):\n{chr(10).join(st.session_state.run_log.splitlines()[-80:])}")
    if st.session_state.results_df is not None:
        s = summarise_results(st.session_state.results_df)
        ctx_parts.append(f"Results Summary: {json.dumps(s, indent=2)}")
    if st.session_state.tg_configs:
        ctx_parts.append(f"Scenario Config: {json.dumps(st.session_state.tg_configs, indent=2)}")

    context_block = "\n\n---\n\n".join(ctx_parts) if ctx_parts else "No run data yet."

    SYSTEM_PROMPT = f"""You are an expert JMeter performance engineer and load testing consultant with deep knowledge of:
- JMeter test plan optimization
- HTTP error codes and root cause analysis
- Correlation and dynamic data extraction
- Performance bottleneck identification
- Test scenario design best practices

You have access to the following test context from the user's current run:
{context_block}

Provide concise, actionable, expert-level insights. Use bullet points where helpful.
Format responses in Markdown. Be specific and reference the actual data when available."""

    # Chat history display
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if not st.session_state.chat_history:
        # Quick action chips
        st.markdown("<p style='color:#64748b; font-size:0.85rem;'>💬 Start a conversation or use a quick prompt:</p>", unsafe_allow_html=True)
        q_cols = st.columns(3)
        quick_prompts = [
            ("🔍 Analyze my errors", "Analyze the errors in my test run and explain root causes and fixes."),
            ("⚡ Optimize scenario", "Review my thread group configuration and suggest optimizations for realistic load."),
            ("📊 Insights summary", "Give me a full performance insights summary of my test run results."),
        ]
        for i, (label, prompt) in enumerate(quick_prompts):
            with q_cols[i]:
                if st.button(label, key=f"qp_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    with st.spinner("Claude is thinking..."):
                        try:
                            client = anthropic.Anthropic(api_key=st.session_state.anthropic_key)
                            resp = client.messages.create(
                                model="claude-sonnet-4-20250514",
                                max_tokens=1024,
                                system=SYSTEM_PROMPT,
                                messages=st.session_state.chat_history,
                            )
                            reply = resp.content[0].text
                            st.session_state.chat_history.append({"role": "assistant", "content": reply})
                            st.rerun()
                        except Exception as ex:
                            st.error(f"API Error: {ex}")

    # Display chat messages
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'>🧑 {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-ai'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

    # Chat input
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    inp_col, send_col = st.columns([5, 1])
    with inp_col:
        user_msg = st.text_input("Ask Claude anything about your test...", key="chat_input", label_visibility="collapsed", placeholder="e.g. Why is my 95th percentile so high?")
    with send_col:
        send_btn = st.button("Send ➤", key="send_chat", use_container_width=True)

    if send_btn and user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.spinner("Claude is analyzing..."):
            try:
                client = anthropic.Anthropic(api_key=st.session_state.anthropic_key)
                resp = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=st.session_state.chat_history,
                )
                reply = resp.content[0].text
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()
            except anthropic.AuthenticationError:
                st.error("❌ Invalid API key. Please check your Anthropic API key.")
            except Exception as ex:
                st.error(f"❌ API Error: {ex}")

    if st.session_state.chat_history:
        if st.button("🗑 Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

else:
    st.markdown("""
    <div class='card' style='text-align:center; padding:30px;'>
        <div style='font-size:2rem; margin-bottom:10px;'>🤖</div>
        <p style='color:#64748b;'>Enter your Anthropic API key above to unlock AI-powered insights, error analysis, and recommendations powered by Claude.</p>
        <a href='https://console.anthropic.com' target='_blank' style='color:#00d4ff; font-size:0.85rem;'>Get your API key at console.anthropic.com →</a>
    </div>
    """, unsafe_allow_html=True)


# ─── FOOTER ───
st.markdown("""
<div class='neon-divider'></div>
<div style='text-align:center; padding:20px 0; color:#1e3a5f; font-size:0.78rem;'>
    ⚡ JMeter Executor Pro · Built with Streamlit · Powered by Claude AI
</div>
""", unsafe_allow_html=True)
