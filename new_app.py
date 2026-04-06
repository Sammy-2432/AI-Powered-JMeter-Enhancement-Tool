"""
JMeter AI Enhancer — Complete Single-File Streamlit App
Enterprise-grade performance test intelligence platform powered by Claude AI
Run: streamlit run app.py
"""

import streamlit as st
import subprocess
import os
import xml.etree.ElementTree as ET
import pandas as pd
import re
import json
import time
from datetime import datetime
import anthropic

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="JMeter AI Enhancer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── GLOBAL ── */
:root {
  --bg:          #0F1117;
  --surface:     #161B27;
  --card:        #1C2333;
  --border:      #252D3D;
  --border-lt:   #2E3A50;
  --accent:      #3B82F6;
  --accent-h:    #2563EB;
  --accent-s:    rgba(59,130,246,0.12);
  --green:       #10B981;
  --green-s:     rgba(16,185,129,0.10);
  --red:         #EF4444;
  --red-s:       rgba(239,68,68,0.10);
  --amber:       #F59E0B;
  --amber-s:     rgba(245,158,11,0.10);
  --purple:      #8B5CF6;
  --txt:         #F1F5F9;
  --txt2:        #94A3B8;
  --txt3:        #64748B;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', system-ui, sans-serif !important;
  background: var(--bg) !important;
  color: var(--txt) !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] * { color: var(--txt) !important; }

/* ── HIDE DEFAULT STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── TOPBAR ── */
.topbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 32px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.topbar-left { display: flex; align-items: center; gap: 14px; }
.topbar-logo {
  width: 34px; height: 34px; border-radius: 9px;
  background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 800; color: #fff;
}
.topbar-title { font-size: 15px; font-weight: 700; color: var(--txt); line-height: 1.2; }
.topbar-sub   { font-size: 11px; color: var(--txt3); }
.topbar-right { display: flex; align-items: center; gap: 10px; }

/* ── PAGE WRAPPER ── */
.page-wrap { padding: 28px 32px 60px; max-width: 920px; }

/* ── SECTION TITLE ── */
.sec-title {
  font-size: 14px; font-weight: 700; color: var(--txt);
  margin: 0 0 4px;
}
.sec-sub { font-size: 12px; color: var(--txt3); margin: 0 0 16px; line-height: 1.5; }

/* ── CARDS ── */
.ec {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 22px;
  margin-bottom: 16px;
}
.ec-accent-green { border-left: 3px solid var(--green) !important; }
.ec-accent-amber { border-left: 3px solid var(--amber) !important; }
.ec-accent-red   { border-left: 3px solid var(--red)   !important; }
.ec-accent-blue  { border-left: 3px solid var(--accent) !important; }

/* ── BADGES ── */
.badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 6px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.03em;
  font-family: 'DM Mono', monospace;
}
.badge-ok     { background: var(--green-s);  color: var(--green);  border: 1px solid rgba(16,185,129,0.3);  }
.badge-err    { background: var(--red-s);    color: var(--red);    border: 1px solid rgba(239,68,68,0.3);   }
.badge-warn   { background: var(--amber-s);  color: var(--amber);  border: 1px solid rgba(245,158,11,0.3);  }
.badge-info   { background: var(--accent-s); color: var(--accent); border: 1px solid rgba(59,130,246,0.3);  }
.badge-muted  { background: rgba(100,116,139,0.12); color: var(--txt2); border: 1px solid rgba(100,116,139,0.25); }

/* ── STATUS DOT ── */
.dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.dot-green { background: var(--green); box-shadow: 0 0 5px var(--green); }
.dot-muted { background: var(--txt3); }

/* ── VERIFY BANNERS ── */
.verify-ok {
  margin-top: 10px; padding: 9px 14px; border-radius: 8px;
  background: var(--green-s); border: 1px solid rgba(16,185,129,0.2);
  color: var(--green); font-size: 12px; font-family: 'DM Mono', monospace;
  display: flex; align-items: center; gap: 8px;
}
.verify-err {
  margin-top: 10px; padding: 9px 14px; border-radius: 8px;
  background: var(--red-s); border: 1px solid rgba(239,68,68,0.2);
  color: var(--red); font-size: 12px;
}

/* ── METRICS ── */
.metric-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.metric-box {
  flex: 1; min-width: 100px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 14px; text-align: center;
}
.metric-val   { font-size: 26px; font-weight: 700; font-family: 'DM Mono', monospace; line-height: 1; }
.metric-lbl   { font-size: 10px; color: var(--txt3); text-transform: uppercase; letter-spacing: 0.07em; margin-top: 5px; }

/* ── THREAD GROUP ROW ── */
.tg-row {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 14px; border-radius: 8px;
  background: var(--surface); border: 1px solid var(--border);
  margin-bottom: 7px;
}
.tg-name  { flex: 1; font-size: 13px; font-weight: 500; }
.tg-meta  { font-size: 11px; color: var(--txt3); font-family: 'DM Mono', monospace; }

/* ── SUGGESTION ITEMS ── */
.sug {
  padding: 14px 16px;
  border-radius: 0 8px 8px 0;
  border-left: 3px solid var(--amber);
  background: var(--amber-s);
  margin-bottom: 10px;
}
.sug.sug-err  { border-color: var(--red);   background: var(--red-s); }
.sug.sug-ok   { border-color: var(--green); background: var(--green-s); }
.sug-title    { font-size: 13px; font-weight: 700; color: var(--txt); }
.sug-body     { font-size: 12px; color: var(--txt2); margin-top: 5px; line-height: 1.6; }

/* ── CODE BLOCK ── */
.code-blk {
  background: #080C14; border: 1px solid var(--border);
  border-radius: 8px; padding: 14px 16px;
  font-family: 'DM Mono', monospace; font-size: 11.5px;
  color: var(--green); overflow-x: auto; white-space: pre; line-height: 1.7;
}

/* ── PRE-FLIGHT GRID ── */
.pf-grid { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.pf-box {
  flex: 1; min-width: 120px; padding: 14px 12px; border-radius: 8px;
  text-align: center; background: var(--surface); border: 1px solid var(--border);
}
.pf-box.ok {
  background: var(--green-s); border-color: rgba(16,185,129,0.3);
}
.pf-icon  { font-size: 20px; margin-bottom: 6px; }
.pf-label { font-size: 11px; font-weight: 600; }

/* ── RT BAR CHART ── */
.rt-bars { display: flex; align-items: flex-end; gap: 5px; height: 80px; }
.rt-bar  { flex: 1; border-radius: 3px 3px 0 0; }
.rt-labels { display: flex; gap: 5px; margin-top: 5px; }
.rt-lbl { flex: 1; font-size: 9px; color: var(--txt3); text-align: center; }

/* ── STATUS CODE BAR ── */
.sc-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.sc-bar-track { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; }
.sc-bar-fill  { height: 100%; border-radius: 99px; }

/* ── STATUS SIDEBAR ROWS ── */
.st-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 0; border-bottom: 1px solid var(--border);
}
.st-key { font-size: 12px; color: var(--txt3); }
.st-val { font-size: 11px; font-family: 'DM Mono', monospace; }

/* ── DIVIDER ── */
.divider { height: 1px; background: var(--border); margin: 22px 0; }

/* ── STREAMLIT WIDGET OVERRIDES ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--txt) !important;
  font-family: 'DM Mono', monospace !important;
  font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
}

.stSelectbox > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--txt) !important;
}

.stMultiSelect > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}

/* All labels */
label, .stTextInput label, .stNumberInput label, .stTextArea label,
.stSelectbox label, .stMultiSelect label {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: var(--txt2) !important;
  letter-spacing: 0.04em !important;
  font-family: 'DM Sans', sans-serif !important;
}

/* Primary button */
.stButton > button {
  background: var(--accent) !important;
  border: none !important;
  border-radius: 8px !important;
  color: #fff !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  padding: 9px 18px !important;
  transition: background 0.15s !important;
  letter-spacing: 0.01em !important;
}
.stButton > button:hover { background: var(--accent-h) !important; }
.stButton > button:disabled { opacity: 0.5 !important; cursor: not-allowed !important; }

/* Download button */
.stDownloadButton > button {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--txt2) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 12px !important;
  font-weight: 500 !important;
}

/* Progress bar */
.stProgress > div > div > div { background: var(--accent) !important; }

/* Expander */
div[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
div[data-testid="stExpander"] summary { color: var(--txt) !important; font-weight: 600 !important; }

/* Dataframe */
.stDataFrame { border-radius: 8px !important; overflow: hidden; }

/* Checkbox */
.stCheckbox label { font-size: 13px !important; font-weight: 500 !important; }

/* Radio */
.stRadio label { font-size: 13px !important; }
.stRadio > div > div { gap: 8px !important; }

/* Alerts */
.stAlert { border-radius: 8px !important; font-size: 13px !important; }
.stSuccess { border-left: 3px solid var(--green) !important; }
.stWarning { border-left: 3px solid var(--amber) !important; }
.stError   { border-left: 3px solid var(--red)   !important; }
.stInfo    { border-left: 3px solid var(--accent) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--txt3) !important;
  background: transparent !important;
  border-bottom: 2px solid transparent !important;
  padding: 10px 20px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom-color: var(--accent) !important;
  background: rgba(59,130,246,0.05) !important;
  font-weight: 600 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

/* Number input spinners */
input[type=number]::-webkit-inner-spin-button { opacity: 0.4; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════
_defaults = {
    "java_home":    "",
    "java_valid":   False,
    "java_version": "",
    "jmeter_home":  "",
    "jmeter_valid": False,
    "api_key":      "",
    "api_verified": False,
    "jmx_path":     "",
    "script_loaded": False,
    "thread_groups": [],
    "csv_files":    [],
    "run_all":      True,
    "selected_tgs": [],
    "scenario":     {"threads": 50, "duration": 120, "iterations": -1},
    "jtl_df":       None,
    "suggestions":  [],
    "run_done":     False,
    "ai_insights":  "",
    "output_dir":   "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ══════════════════════════════════════════════════════════════════════════════
# BACKEND LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def validate_java_home(path: str):
    java_bin = os.path.join(path, "bin", "java" + (".exe" if os.name == "nt" else ""))
    if not os.path.isfile(java_bin):
        return False, f"Binary not found: {java_bin}"
    try:
        r = subprocess.run([java_bin, "-version"], capture_output=True, text=True, timeout=10)
        ver = (r.stderr or r.stdout).split("\n")[0]
        return True, ver
    except Exception as e:
        return False, str(e)


def validate_jmeter_home(path: str):
    jm_bin = os.path.join(path, "bin", "jmeter" + (".bat" if os.name == "nt" else ""))
    if os.path.isfile(jm_bin):
        return True, jm_bin
    return False, f"Binary not found: {jm_bin}"


def verify_api_key(key: str):
    try:
        client = anthropic.Anthropic(api_key=key)
        client.messages.create(
            model="claude-opus-4-5",
            max_tokens=5,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, "claude-opus-4-5"
    except Exception as e:
        return False, str(e)


def parse_jmx(path: str):
    tree = ET.parse(path)
    root = tree.getroot()
    groups = []
    for tg in root.iter("ThreadGroup"):
        name    = tg.get("testname", "Unnamed")
        enabled = tg.get("enabled", "true") == "true"
        threads = duration = 1
        loops   = -1
        for sp in tg.iter("stringProp"):
            n = sp.get("name", "")
            if n == "ThreadGroup.num_threads":
                try: threads  = int(sp.text or 1)
                except: pass
            if n == "ThreadGroup.duration":
                try: duration = int(sp.text or 0)
                except: pass
            if n == "LoopController.loops":
                try: loops    = int(sp.text or -1)
                except: pass
        groups.append({"name": name, "enabled": enabled, "threads": threads,
                        "duration": duration, "loops": loops})
    return groups


def find_csv_refs(path: str):
    tree = ET.parse(path)
    root = tree.getroot()
    refs = []
    for ds in root.iter("CSVDataSet"):
        for sp in ds.iter("stringProp"):
            if sp.get("name") == "filename":
                refs.append(sp.text or "")
    return refs


def apply_overrides(src: str, dst: str, scenario: dict, selected: list, run_all: bool):
    tree = ET.parse(src)
    root = tree.getroot()
    for tg in root.iter("ThreadGroup"):
        name = tg.get("testname", "")
        if not run_all and name not in selected:
            tg.set("enabled", "false")
            continue
        tg.set("enabled", "true")
        for sp in tg.iter("stringProp"):
            n = sp.get("name", "")
            if n == "ThreadGroup.num_threads":  sp.text = str(scenario["threads"])
            if n == "ThreadGroup.duration":      sp.text = str(scenario["duration"])
            if n == "LoopController.loops":      sp.text = str(scenario["iterations"])
    tree.write(dst, xml_declaration=True, encoding="UTF-8")


def run_jmeter(jmeter_bin: str, jmx: str, jtl: str, log: str):
    cmd = [jmeter_bin, "-n", "-t", jmx, "-l", jtl, "-j", log]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return r.returncode == 0, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return False, "Timed out after 10 minutes."
    except Exception as e:
        return False, str(e)


def parse_jtl(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _col(df: pd.DataFrame, keywords: list):
    for kw in keywords:
        for c in df.columns:
            if kw in c.lower():
                return c
    return None


def analyze_jtl(df: pd.DataFrame):
    if df.empty:
        return [{"level": "error", "title": "Empty JTL", "body": "No data in JTL file.", "code": ""}]

    suggestions = []
    total     = len(df)
    succ_col  = _col(df, ["success"])
    code_col  = _col(df, ["responsecode", "response code"])
    elap_col  = _col(df, ["elapsed"])
    label_col = _col(df, ["label"])

    failed = 0
    if succ_col:
        failed = (df[succ_col].astype(str).str.lower() == "false").sum()

    pass_pct = (total - failed) / total * 100 if total else 0
    suggestions.append({
        "level": "ok" if pass_pct >= 95 else ("warn" if pass_pct >= 70 else "error"),
        "title": f"Pass Rate: {pass_pct:.1f}%",
        "body":  f"{total - failed:,} of {total:,} requests succeeded.",
        "code":  "",
    })

    if elap_col:
        avg = df[elap_col].mean()
        p95 = df[elap_col].quantile(0.95)
        suggestions.append({
            "level": "ok" if avg < 2000 else ("warn" if avg < 5000 else "error"),
            "title": f"Avg Response: {avg:.0f}ms  |  P95: {p95:.0f}ms",
            "body":  "P95 > 5 000 ms indicates a backend bottleneck or misconfiguration.",
            "code":  "",
        })

    if code_col:
        for code, cnt in df[code_col].astype(str).value_counts().items():
            pct = cnt / total * 100
            if str(code).startswith("5"):
                label = df[label_col].iloc[0] if label_col else "request"
                suggestions.append({
                    "level": "error",
                    "title": f"HTTP {code} — {cnt:,} occurrences ({pct:.1f}%) — Correlation Issue Detected",
                    "body":  (
                        "5xx errors strongly indicate a dynamic token (JWT, CSRF, session ID) is not being "
                        "extracted from a previous response and forwarded in subsequent requests. "
                        "Apply the generalised RegexExtractor below."
                    ),
                    "code": _build_regex_extractor(label),
                })
            elif str(code).startswith("4"):
                suggestions.append({
                    "level": "warn",
                    "title": f"HTTP {code} — {cnt:,} occurrences ({pct:.1f}%)",
                    "body":  "4xx errors indicate authentication failures, bad requests, or missing parameters.",
                    "code":  "",
                })
            elif "refused" in str(code).lower() or "non http" in str(code).lower():
                suggestions.append({
                    "level": "error",
                    "title": f"Connection Error — {cnt:,} occurrences",
                    "body":  "Server unreachable. Verify host/port in HTTP Request Defaults.",
                    "code":  "",
                })
    return suggestions


def _build_regex_extractor(label: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", label).lower() or "dynamic_value"
    return f"""<!-- RegexExtractor — Generalised Correlation Fix for: {label} -->
<RegexExtractor guiclass="RegexExtractorGui" testclass="RegexExtractor"
  testname="Extract {safe}" enabled="true">

  <stringProp name="RegexExtractor.useHeaders">false</stringProp>
  <stringProp name="RegexExtractor.refname">{safe}</stringProp>

  <!-- Generalised (.*?) with dynamic LEFT and RIGHT boundaries -->
  <stringProp name="RegexExtractor.regex">LEFT_BOUNDARY(.*?)RIGHT_BOUNDARY</stringProp>

  <stringProp name="RegexExtractor.template">$1$</stringProp>
  <stringProp name="RegexExtractor.default">NOT_FOUND</stringProp>
  <stringProp name="RegexExtractor.match_no">1</stringProp>
</RegexExtractor>

<!-- Reference as: ${{{safe}}} in downstream requests -->

<!-- HOW TO USE
  1. View the RESPONSE of the request BEFORE the 500 error.
  2. Locate the dynamic field, e.g:  "access_token":"eyJhb..."
  3. LEFT_BOUNDARY  → the static text immediately LEFT  of the value  e.g. "access_token":"
  4. RIGHT_BOUNDARY → the static text immediately RIGHT of the value  e.g. "
  Final regex example: "access_token":"(.*?)"
  5. Place this extractor on the Login / Auth response sampler.
  6. Use ${{{safe}}} in the Authorization header of all subsequent requests.
-->"""


def build_prompt(tgs: list, scenario: dict, suggestions: list, df: pd.DataFrame) -> str:
    code_dist = {}
    if not df.empty:
        cc = _col(df, ["responsecode", "response code"])
        if cc:
            code_dist = df[cc].astype(str).value_counts().to_dict()

    lines = "\n".join(f"- {s['title']}: {s['body']}" for s in suggestions)
    return f"""You are an expert JMeter performance test analyst and load testing consultant.

## Test Configuration
Thread Groups : {[t["name"] for t in tgs]}
Scenario      : {scenario["threads"]} virtual users · {scenario["duration"]}s duration · {'∞ iterations' if scenario["iterations"] == -1 else str(scenario["iterations"]) + ' iterations'}

## Dry-Run Results Summary
{lines}

## HTTP Response Code Distribution
{json.dumps(code_dist, indent=2)}

## Your Analysis Task
1. Identify the root cause(s) of any failures with specific technical detail.
2. If HTTP 500 errors are present, confirm the correlation issue and describe the exact extraction strategy.
3. Provide concrete JMeter configuration fixes (extractors, assertions, thread settings, connection pools).
4. List performance optimisation recommendations in priority order.
5. Rate the overall script health: 🔴 RED  /  🟡 AMBER  /  🟢 GREEN with clear justification.
6. Estimate the expected pass rate after applying your recommended fixes.

Format your response with clear markdown headings and bullet points."""


def get_ai_insights(prompt: str, api_key: str) -> str:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"⚠ Claude API error: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def badge(text: str, kind: str = "info") -> str:
    cls = {"ok": "badge-ok", "error": "badge-err", "warn": "badge-warn",
           "info": "badge-info", "muted": "badge-muted"}.get(kind, "badge-info")
    return f'<span class="badge {cls}">{text}</span>'


def dot(active: bool) -> str:
    c = "dot-green" if active else "dot-muted"
    return f'<span class="dot {c}"></span>'


def card_open(accent: str = "") -> str:
    cls = f"ec ec-accent-{accent}" if accent else "ec"
    return f'<div class="{cls}">'


def card_close() -> str:
    return "</div>"


def sec_title(title: str, sub: str = "") -> None:
    st.markdown(f'<div class="sec-title">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="sec-sub">{sub}</div>', unsafe_allow_html=True)


def divider() -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════════

status_items = {
    "Java":    st.session_state.java_valid,
    "JMeter":  st.session_state.jmeter_valid,
    "Script":  st.session_state.script_loaded,
    "Claude":  st.session_state.api_verified,
    "Dry Run": st.session_state.run_done,
}
all_ok      = sum(status_items.values())
api_pill    = (f'<span class="badge badge-ok">{dot(True)} Claude Connected</span>'
               if st.session_state.api_verified
               else '<span class="badge badge-muted">Claude Not Connected</span>')
steps_dots  = "".join(
    f'<span class="dot {"dot-green" if v else "dot-muted"}" style="margin:0 2px"></span>'
    for v in status_items.values()
)

st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div class="topbar-logo">⚡</div>
    <div>
      <div class="topbar-title">JMeter AI Enhancer</div>
      <div class="topbar-sub">AI-Powered Performance Test Intelligence Platform</div>
    </div>
  </div>
  <div class="topbar-right">
    {api_pill}
    <div style="display:flex;align-items:center;gap:4px;padding:6px 12px;
         background:var(--surface);border:1px solid var(--border);border-radius:20px;">
      {steps_dots}
      <span style="font-size:11px;color:var(--txt3);margin-left:6px">{all_ok}/5 ready</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding:18px 16px 14px;border-bottom:1px solid var(--border)">
      <div style="font-size:11px;font-weight:700;color:var(--txt3);letter-spacing:0.08em;margin-bottom:12px">WORKFLOW</div>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigation",
        ["⚙  Environment Setup",
         "◈  Script Analysis",
         "◎  Scenario Builder",
         "▶  Dry Run & Results",
         "◆  AI Insights"],
        label_visibility="collapsed",
    )

    st.markdown("""
    <div style="padding:14px 0 8px;margin-top:8px;border-top:1px solid var(--border)">
      <div style="font-size:11px;font-weight:700;color:var(--txt3);letter-spacing:0.08em;margin-bottom:10px">SYSTEM STATUS</div>
    </div>
    """, unsafe_allow_html=True)

    status_rows = [
        ("Java Home",    st.session_state.java_valid,   "Validated" if st.session_state.java_valid   else "Pending"),
        ("JMeter",       st.session_state.jmeter_valid, "Found"     if st.session_state.jmeter_valid else "Pending"),
        ("JMX Script",   st.session_state.script_loaded,"Loaded"    if st.session_state.script_loaded else "Pending"),
        ("Claude API",   st.session_state.api_verified, "Connected" if st.session_state.api_verified else "Pending"),
        ("Dry Run",      st.session_state.run_done,     "Complete"  if st.session_state.run_done     else "Pending"),
    ]
    for lbl, ok, val in status_rows:
        color = "#10B981" if ok else "#64748B"
        st.markdown(f"""
        <div class="st-row">
          <span class="st-key">{lbl}</span>
          <span class="st-val" style="color:{color}">{dot(ok)} {val}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT WRAPPER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="page-wrap">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PANEL 1 — ENVIRONMENT SETUP
# ══════════════════════════════════════════════════════════════════════════════

if "Setup" in nav:

    # ── Java ──────────────────────────────────────────────────────────────────
    st.markdown(card_open(), unsafe_allow_html=True)
    sec_title("Java Home Directory", "Point to your JDK installation directory")
    col1, col2 = st.columns([5, 1])
    with col1:
        java_input = st.text_input(
            "JAVA_HOME", label_visibility="collapsed",
            placeholder="/usr/lib/jvm/java-11-openjdk-amd64  or  C:\\Program Files\\Java\\jdk-11",
            value=st.session_state.java_home,
        )
    with col2:
        validate_java = st.button("Validate", key="btn_java", use_container_width=True)

    if validate_java and java_input:
        st.session_state.java_home = java_input
        with st.spinner("Checking Java binary..."):
            ok, msg = validate_java_home(java_input)
        st.session_state.java_valid   = ok
        st.session_state.java_version = msg if ok else ""
        if not ok:
            st.error(f"✕  {msg}")

    if st.session_state.java_valid:
        st.markdown(
            f'<div class="verify-ok">✓&nbsp; {st.session_state.java_version}</div>',
            unsafe_allow_html=True,
        )
    st.markdown(card_close(), unsafe_allow_html=True)

    # ── JMeter ────────────────────────────────────────────────────────────────
    st.markdown(card_open(), unsafe_allow_html=True)
    sec_title("JMeter Home Directory", "Root directory of your Apache JMeter installation")
    col1, col2 = st.columns([5, 1])
    with col1:
        jm_input = st.text_input(
            "JMETER_HOME", label_visibility="collapsed",
            placeholder="/opt/apache-jmeter-5.6.3  or  C:\\jmeter",
            value=st.session_state.jmeter_home,
        )
    with col2:
        validate_jm = st.button("Validate", key="btn_jmeter", use_container_width=True)

    if validate_jm and jm_input:
        st.session_state.jmeter_home = jm_input
        ok, msg = validate_jmeter_home(jm_input)
        st.session_state.jmeter_valid = ok
        if not ok:
            st.error(f"✕  {msg}")

    if st.session_state.jmeter_valid:
        bin_path = os.path.join(st.session_state.jmeter_home, "bin",
                                "jmeter" + (".bat" if os.name == "nt" else ""))
        st.markdown(
            f'<div class="verify-ok">✓&nbsp; JMeter binary found at {bin_path}</div>',
            unsafe_allow_html=True,
        )
    st.markdown(card_close(), unsafe_allow_html=True)

    # ── Claude API ────────────────────────────────────────────────────────────
    accent = "green" if st.session_state.api_verified else ""
    st.markdown(card_open(accent), unsafe_allow_html=True)

    hcol1, hcol2 = st.columns([4, 1])
    with hcol1:
        sec_title("Claude AI — API Key", "Connect to Claude AI for intelligent script analysis and insights")
    with hcol2:
        if st.session_state.api_verified:
            st.markdown(
                f'<div style="text-align:right;padding-top:4px">{badge("● Connected", "ok")}</div>',
                unsafe_allow_html=True,
            )

    col1, col2 = st.columns([5, 1])
    with col1:
        api_input = st.text_input(
            "API Key", label_visibility="collapsed", type="password",
            placeholder="sk-ant-api03-...",
            value=st.session_state.api_key,
        )
        st.markdown(
            '<div style="font-size:11px;color:var(--txt3);margin-top:4px">'
            'Your key is never stored beyond this browser session.</div>',
            unsafe_allow_html=True,
        )
    with col2:
        verify_api = st.button(
            "✓ Verified" if st.session_state.api_verified else "Verify",
            key="btn_api", use_container_width=True,
        )

    if verify_api and api_input:
        st.session_state.api_key = api_input
        with st.spinner("Verifying with Anthropic..."):
            ok, msg = verify_api_key(api_input)
        st.session_state.api_verified = ok
        if not ok:
            st.error(f"✕  API Error: {msg}")

    if st.session_state.api_verified:
        st.markdown(
            '<div class="verify-ok">✓&nbsp; Claude claude-opus-4-5 — API connection verified</div>',
            unsafe_allow_html=True,
        )
    st.markdown(card_close(), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PANEL 2 — SCRIPT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

elif "Script" in nav:

    # ── Load JMX ──────────────────────────────────────────────────────────────
    st.markdown(card_open(), unsafe_allow_html=True)
    sec_title("JMX Test Plan", "Load your JMeter test plan for analysis")
    col1, col2 = st.columns([5, 1])
    with col1:
        jmx_input = st.text_input(
            "JMX Path", label_visibility="collapsed",
            placeholder="/path/to/testplan.jmx",
            value=st.session_state.jmx_path,
        )
    with col2:
        load_btn = st.button("Load Script", key="btn_load", use_container_width=True)

    if load_btn and jmx_input:
        if not os.path.isfile(jmx_input):
            st.error("✕  File not found. Please check the path.")
        elif not jmx_input.endswith(".jmx"):
            st.error("✕  File must be a .jmx JMeter test plan.")
        else:
            try:
                with st.spinner("Parsing JMX..."):
                    tgs   = parse_jmx(jmx_input)
                    csvs  = find_csv_refs(jmx_input)
                st.session_state.jmx_path     = jmx_input
                st.session_state.thread_groups = tgs
                st.session_state.selected_tgs  = [t["name"] for t in tgs if t["enabled"]]
                st.session_state.csv_files     = [
                    {"ref": os.path.basename(c), "path": c, "exists": os.path.isfile(c)}
                    for c in csvs
                ]
                st.session_state.script_loaded = True
                st.success(
                    f"✓  Loaded {len(tgs)} thread group(s) · {len(csvs)} CSV reference(s)"
                )
            except Exception as e:
                st.error(f"✕  Failed to parse JMX: {e}")
    st.markdown(card_close(), unsafe_allow_html=True)

    if st.session_state.script_loaded:

        # ── Thread Groups ──────────────────────────────────────────────────────
        st.markdown(card_open(), unsafe_allow_html=True)
        hc1, hc2 = st.columns([4, 1])
        with hc1:
            sec_title("Thread Groups Detected")
        with hc2:
            st.markdown(
                f'<div style="text-align:right">{badge(str(len(st.session_state.thread_groups)) + " Groups", "info")}</div>',
                unsafe_allow_html=True,
            )

        for tg in st.session_state.thread_groups:
            loops_txt = "∞ loops" if tg["loops"] == -1 else f"{tg['loops']} loops"
            st.markdown(f"""
            <div class="tg-row">
              <span style="font-size:8px">{dot(tg["enabled"])}</span>
              <span class="tg-name" style="color:{'var(--txt)' if tg['enabled'] else 'var(--txt3)'}">{tg["name"]}</span>
              <span class="tg-meta">{tg["threads"]}T · {tg["duration"]}s · {loops_txt}</span>
              {badge("Enabled", "ok") if tg["enabled"] else badge("Disabled", "muted")}
            </div>
            """, unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

        # ── CSV Files ──────────────────────────────────────────────────────────
        if st.session_state.csv_files:
            st.markdown(card_open(), unsafe_allow_html=True)
            sec_title("CSV Dataset References",
                      "CSV files referenced in CSV Dataset Config elements")

            for i, cf in enumerate(st.session_state.csv_files):
                col1, col2 = st.columns([5, 1])
                with col1:
                    new_path = st.text_input(
                        f"CSV {i+1} — {cf['ref']}",
                        value=cf["path"],
                        key=f"csv_{i}",
                    )
                    if new_path != cf["path"]:
                        st.session_state.csv_files[i]["path"]   = new_path
                        st.session_state.csv_files[i]["exists"] = os.path.isfile(new_path)
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    exists = st.session_state.csv_files[i]["exists"]
                    st.markdown(
                        badge("Found", "ok") if exists else badge("Missing", "error"),
                        unsafe_allow_html=True,
                    )
            st.markdown(card_close(), unsafe_allow_html=True)
        else:
            st.info("No CSV Dataset Config elements found in this JMX.")


# ══════════════════════════════════════════════════════════════════════════════
# PANEL 3 — SCENARIO BUILDER
# ══════════════════════════════════════════════════════════════════════════════

elif "Scenario" in nav:

    if not st.session_state.script_loaded:
        st.warning("⚠  Load a JMX script first (Script Analysis tab).")
    else:
        # ── Thread Group Selection ─────────────────────────────────────────────
        st.markdown(card_open(), unsafe_allow_html=True)
        sec_title("Thread Group Selection",
                  "Choose which thread groups to include in the dry run")

        run_all = st.checkbox(
            "Run All Thread Groups",
            value=st.session_state.run_all,
        )
        st.session_state.run_all = run_all

        if not run_all:
            enabled_names = [t["name"] for t in st.session_state.thread_groups if t["enabled"]]
            selected = st.multiselect(
                "Select Thread Groups to Execute",
                options=enabled_names,
                default=[x for x in st.session_state.selected_tgs if x in enabled_names],
            )
            st.session_state.selected_tgs = selected
        else:
            st.session_state.selected_tgs = [t["name"] for t in st.session_state.thread_groups]
        st.markdown(card_close(), unsafe_allow_html=True)

        # ── Override Parameters ────────────────────────────────────────────────
        st.markdown(card_open("amber"), unsafe_allow_html=True)
        hc1, hc2 = st.columns([4, 1])
        with hc1:
            sec_title("Override Parameters",
                      "These values overwrite the existing JMX thread group settings at runtime")
        with hc2:
            st.markdown(
                f'<div style="text-align:right">{badge("Overwrites JMX", "warn")}</div>',
                unsafe_allow_html=True,
            )

        sc = st.session_state.scenario
        col1, col2, col3 = st.columns(3)
        with col1:
            sc["threads"] = st.number_input(
                "Thread Count (Users)", min_value=1, max_value=10000,
                value=sc["threads"],
            )
        with col2:
            sc["duration"] = st.number_input(
                "Duration (seconds)", min_value=1, max_value=86400,
                value=sc["duration"],
            )
        with col3:
            sc["iterations"] = st.number_input(
                "Iterations (−1 = ∞)", min_value=-1, max_value=100000,
                value=sc["iterations"],
            )
        st.session_state.scenario = sc
        st.markdown(card_close(), unsafe_allow_html=True)

        # ── Preview ────────────────────────────────────────────────────────────
        st.markdown(card_open(), unsafe_allow_html=True)
        sec_title("Scenario Preview")
        iter_val = "∞" if sc["iterations"] == -1 else str(sc["iterations"])
        tg_count = "ALL" if run_all else str(len(st.session_state.selected_tgs))
        st.markdown(f"""
        <div class="metric-grid">
          <div class="metric-box">
            <div class="metric-val" style="color:var(--accent)">{sc['threads']}</div>
            <div class="metric-lbl">Virtual Users</div>
          </div>
          <div class="metric-box">
            <div class="metric-val" style="color:var(--accent)">{sc['duration']}s</div>
            <div class="metric-lbl">Duration</div>
          </div>
          <div class="metric-box">
            <div class="metric-val" style="color:var(--accent)">{iter_val}</div>
            <div class="metric-lbl">Iterations</div>
          </div>
          <div class="metric-box">
            <div class="metric-val" style="color:var(--purple)">{tg_count}</div>
            <div class="metric-lbl">Thread Groups</div>
          </div>
          <div class="metric-box">
            <div class="metric-val" style="color:var(--amber);font-size:18px">Override</div>
            <div class="metric-lbl">Execution Mode</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PANEL 4 — DRY RUN & RESULTS
# ══════════════════════════════════════════════════════════════════════════════

elif "Dry Run" in nav:

    # ── Pre-flight ─────────────────────────────────────────────────────────────
    checks = {
        "Java Validated":   st.session_state.java_valid,
        "JMeter Found":     st.session_state.jmeter_valid,
        "JMX Loaded":       st.session_state.script_loaded,
        "Thread Groups":    bool(st.session_state.thread_groups),
    }
    all_ready = all(checks.values())

    st.markdown(card_open(), unsafe_allow_html=True)
    sec_title("Pre-flight Checklist")
    st.markdown('<div class="pf-grid">', unsafe_allow_html=True)
    for lbl, ok in checks.items():
        icon  = "✓" if ok else "○"
        cls   = "pf-box ok" if ok else "pf-box"
        color = "var(--green)" if ok else "var(--txt3)"
        st.markdown(f"""
        <div class="{cls}">
          <div class="pf-icon" style="color:{color}">{icon}</div>
          <div class="pf-label" style="color:{color}">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(card_close(), unsafe_allow_html=True)

    # ── Execute ────────────────────────────────────────────────────────────────
    st.markdown(card_open(), unsafe_allow_html=True)
    sec_title("Execute Dry Run",
              "Runs JMeter in non-GUI mode using your configured scenario overrides")

    default_dir = (
        os.path.join(os.path.dirname(st.session_state.jmx_path), "dry_run_output")
        if st.session_state.jmx_path else "/tmp/jmeter_output"
    )
    output_dir = st.text_input(
        "Output Directory for JTL & Logs",
        value=st.session_state.output_dir or default_dir,
    )
    st.session_state.output_dir = output_dir

    if not all_ready:
        st.warning("⚠  Complete Environment Setup and Script Analysis before running.")
    else:
        if st.button("▶  Execute Dry Run", use_container_width=True, key="btn_run"):
            os.makedirs(output_dir, exist_ok=True)
            ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
            mod_jmx     = os.path.join(output_dir, f"modified_{ts}.jmx")
            jtl_path    = os.path.join(output_dir, f"results_{ts}.jtl")
            log_path    = os.path.join(output_dir, f"jmeter_{ts}.log")
            jmeter_bin  = os.path.join(
                st.session_state.jmeter_home, "bin",
                "jmeter" + (".bat" if os.name == "nt" else ""),
            )

            prog   = st.progress(0)
            status = st.empty()

            steps = [
                (15, "Applying scenario overrides to JMX..."),
                (35, "Initializing JMeter non-GUI mode..."),
                (60, "Executing thread groups..."),
                (80, "Collecting sampler results..."),
                (95, "Writing JTL output..."),
            ]
            for pct, msg in steps:
                status.markdown(
                    f'<span style="font-size:12px;color:var(--txt2)">{msg}</span>',
                    unsafe_allow_html=True,
                )
                prog.progress(pct)
                time.sleep(0.3)

            apply_overrides(
                st.session_state.jmx_path, mod_jmx,
                st.session_state.scenario,
                st.session_state.selected_tgs,
                st.session_state.run_all,
            )
            ok, out = run_jmeter(jmeter_bin, mod_jmx, jtl_path, log_path)
            prog.progress(100)

            if ok or os.path.isfile(jtl_path):
                status.success("✓  Dry run complete — results below.")
                df = parse_jtl(jtl_path)
                st.session_state.jtl_df      = df
                st.session_state.suggestions = analyze_jtl(df)
                st.session_state.run_done    = True
            else:
                status.error("✕  JMeter execution failed.")
                with st.expander("JMeter Output Log"):
                    st.code(out)

    st.markdown(card_close(), unsafe_allow_html=True)

    # ── Manual JTL load ───────────────────────────────────────────────────────
    divider()
    st.markdown(card_open(), unsafe_allow_html=True)
    sec_title("Load Existing JTL File",
              "Analyse a JTL from a previous run without re-executing")
    col1, col2 = st.columns([5, 1])
    with col1:
        jtl_manual = st.text_input(
            "JTL Path", label_visibility="collapsed",
            placeholder="/path/to/results.jtl",
        )
    with col2:
        if st.button("Analyse", key="btn_jtl", use_container_width=True):
            if os.path.isfile(jtl_manual):
                df = parse_jtl(jtl_manual)
                st.session_state.jtl_df      = df
                st.session_state.suggestions = analyze_jtl(df)
                st.session_state.run_done    = True
                st.success("✓  JTL loaded and analysed.")
            else:
                st.error("✕  File not found.")
    st.markdown(card_close(), unsafe_allow_html=True)

    # ── Results ────────────────────────────────────────────────────────────────
    if st.session_state.run_done and st.session_state.jtl_df is not None:
        df = st.session_state.jtl_df
        divider()

        if not df.empty:
            elap_col = _col(df, ["elapsed"])
            succ_col = _col(df, ["success"])
            code_col = _col(df, ["responsecode", "response code"])

            total  = len(df)
            failed = 0
            if succ_col:
                failed = (df[succ_col].astype(str).str.lower() == "false").sum()
            avg_rt = df[elap_col].mean()    if elap_col else 0
            p95_rt = df[elap_col].quantile(0.95) if elap_col else 0
            p99_rt = df[elap_col].quantile(0.99) if elap_col else 0
            pass_pct = (total - failed) / total * 100

            # Metric cards
            st.markdown(card_open(), unsafe_allow_html=True)
            sec_title("Results Summary")
            p95_color = "var(--green)" if p95_rt < 3000 else ("var(--amber)" if p95_rt < 5000 else "var(--red)")
            st.markdown(f"""
            <div class="metric-grid">
              <div class="metric-box">
                <div class="metric-val">{total:,}</div>
                <div class="metric-lbl">Total Requests</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:var(--green)">{total-failed:,}</div>
                <div class="metric-lbl">Passed</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:var(--red)">{failed:,}</div>
                <div class="metric-lbl">Failed</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:{'var(--green)' if pass_pct>=95 else 'var(--amber)' if pass_pct>=70 else 'var(--red)'}">{pass_pct:.1f}%</div>
                <div class="metric-lbl">Pass Rate</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:var(--amber)">{avg_rt:.0f}ms</div>
                <div class="metric-lbl">Avg Response</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="{f'color:{p95_color}'}">{p95_rt:.0f}ms</div>
                <div class="metric-lbl">P95 Response</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:var(--red)">{p99_rt:.0f}ms</div>
                <div class="metric-lbl">P99 Response</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(card_close(), unsafe_allow_html=True)

            # Response-time distribution bar chart
            if elap_col:
                st.markdown(card_open(), unsafe_allow_html=True)
                sec_title("Response Time Distribution")
                buckets  = [200, 500, 1000, 2000, 5000, 10000]
                labels   = ["<200ms", "200-500ms", "0.5-1s", "1-2s", "2-5s", "5-10s", ">10s"]
                bar_cols = ["#10B981","#10B981","#3B82F6","#3B82F6","#F59E0B","#EF4444","#EF4444"]
                counts   = []
                prev = 0
                for b in buckets:
                    counts.append(int(((df[elap_col] > prev) & (df[elap_col] <= b)).sum()))
                    prev = b
                counts.append(int((df[elap_col] > 10000).sum()))
                max_c = max(counts) or 1
                bars_html = "".join(
                    f'<div class="rt-bar" style="height:{int(c/max_c*100)}%;background:{bar_cols[i]};opacity:0.85" title="{labels[i]}: {c}"></div>'
                    for i, c in enumerate(counts)
                )
                lbls_html = "".join(f'<div class="rt-lbl">{l}</div>' for l in labels)
                st.markdown(f"""
                <div class="rt-bars">{bars_html}</div>
                <div class="rt-labels">{lbls_html}</div>
                """, unsafe_allow_html=True)
                st.markdown(card_close(), unsafe_allow_html=True)

            # Status code breakdown
            if code_col:
                st.markdown(card_open(), unsafe_allow_html=True)
                sec_title("Status Code Analysis")
                for code, cnt in df[code_col].astype(str).value_counts().head(8).items():
                    pct = cnt / total * 100
                    if str(code).startswith("2"):
                        bar_color, bkind = "#10B981", "ok"
                    elif str(code).startswith("4"):
                        bar_color, bkind = "#F59E0B", "warn"
                    elif str(code).startswith("5"):
                        bar_color, bkind = "#EF4444", "error"
                    else:
                        bar_color, bkind = "#64748B", "muted"
                    st.markdown(f"""
                    <div class="sc-row">
                      {badge(f"HTTP {code}", bkind)}
                      <div class="sc-bar-track">
                        <div class="sc-bar-fill" style="width:{pct:.1f}%;background:{bar_color}"></div>
                      </div>
                      <span style="font-size:12px;color:var(--txt2);font-family:'DM Mono',monospace;min-width:80px;text-align:right">{cnt:,} ({pct:.1f}%)</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown(card_close(), unsafe_allow_html=True)

            # Raw data
            with st.expander("◈  Raw Results Data (first 200 rows)"):
                st.dataframe(df.head(200), use_container_width=True)

        divider()

        # Suggestions
        sec_title("Diagnostic Findings & Smart Fixes")
        for sug in st.session_state.suggestions:
            cls  = {"error": "sug sug-err", "ok": "sug sug-ok", "warn": "sug"}.get(sug["level"], "sug")
            icon = {"error": "⚑", "ok": "✓", "warn": "▲"}.get(sug["level"], "ℹ")
            st.markdown(f"""
            <div class="{cls}">
              <div class="sug-title">{icon}&nbsp; {sug['title']}</div>
              <div class="sug-body">{sug['body']}</div>
            </div>
            """, unsafe_allow_html=True)

            if sug["code"]:
                with st.expander("◈  View Correlation Fix — RegexExtractor XML"):
                    st.markdown(
                        f'<div class="code-blk">{sug["code"]}</div>',
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "↓  Download Extractor XML",
                        data=sug["code"],
                        file_name="correlation_extractor.xml",
                        mime="text/xml",
                    )
                st.markdown("""
                <div style="padding:10px 14px;background:var(--surface);border:1px solid var(--border);
                     border-radius:8px;margin-top:8px;font-size:12px;color:var(--txt2);line-height:1.8">
                  <strong style="color:var(--amber);display:block;margin-bottom:4px">How to use this fix</strong>
                  1. Open the RESPONSE of the request <em>before</em> the 500 error in JMeter's Response Data viewer.<br>
                  2. Locate the dynamic field — e.g. <code style="color:var(--green);background:rgba(16,185,129,0.1);padding:1px 5px;border-radius:4px">"access_token":"eyJhb..."</code><br>
                  3. Replace <code style="color:var(--amber)">LEFT_BOUNDARY</code> with the static text immediately left of the value.<br>
                  4. Replace <code style="color:var(--amber)">RIGHT_BOUNDARY</code> with the static text immediately right of the value.<br>
                  5. Place this extractor on the Login / Auth sampler.<br>
                  6. Reference the value as <code style="color:var(--accent)">$&#123;dynamic_value&#125;</code> in all downstream requests.
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PANEL 5 — AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════

elif "AI" in nav:

    if not st.session_state.api_verified:
        st.warning("⚠  Connect your Claude API key in **Environment Setup** first.")
    elif not st.session_state.run_done:
        st.info("◎  Complete a **Dry Run** to generate results before requesting AI analysis.")
    else:
        # Build and show prompt
        prompt = build_prompt(
            st.session_state.thread_groups,
            st.session_state.scenario,
            st.session_state.suggestions,
            st.session_state.jtl_df if st.session_state.jtl_df is not None else pd.DataFrame(),
        )

        st.markdown(card_open(), unsafe_allow_html=True)
        sec_title("Generated Analysis Prompt",
                  "This structured prompt is sent to Claude AI for expert analysis")
        with st.expander("◈  View full prompt"):
            st.code(prompt, language="markdown")

        if st.button("◆  Get AI Insights from Claude", use_container_width=True, key="btn_ai"):
            with st.spinner("Claude is analysing your test results…"):
                insights = get_ai_insights(prompt, st.session_state.api_key)
                st.session_state.ai_insights = insights

        st.markdown(card_close(), unsafe_allow_html=True)

        # Show AI output
        if st.session_state.ai_insights:
            divider()
            st.markdown(card_open("green"), unsafe_allow_html=True)
            hc1, hc2 = st.columns([4, 1])
            with hc1:
                sec_title("Claude AI Analysis Report")
            with hc2:
                st.markdown(
                    f'<div style="text-align:right">{badge("● Analysis Complete", "ok")}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(st.session_state.ai_insights)

            divider()
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "↓  Download Report (.md)",
                    data=st.session_state.ai_insights,
                    file_name=f"jmeter_ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col2:
                if st.button("↺  Re-run Analysis", use_container_width=True, key="btn_rerun"):
                    st.session_state.ai_insights = ""
                    st.rerun()

            st.markdown(card_close(), unsafe_allow_html=True)


# ── Close page wrapper ────────────────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)