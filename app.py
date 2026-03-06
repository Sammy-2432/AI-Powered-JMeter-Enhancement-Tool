import streamlit as st
import os
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Tuple
import tempfile
import shutil

# Try importing OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    st.warning("⚠️ OpenAI library not installed. Please install it with: pip install openai")


# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="JMeter Script Enhancer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Corporate Light Theme CSS
st.markdown("""
<style>
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #2ca02c;
        --danger-color: #d62728;
        --warning-color: #ff7f0e;
        --light-bg: #f8f9fa;
        --border-color: #e0e0e0;
    }
    
    body {
        background-color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .header-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .header-section h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 600;
    }
    
    .header-section p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.95;
    }
    
    .panel {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .panel-title {
        color: #1f77b4;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #1f77b4;
    }
    
    .status-success {
        color: #2ca02c;
        font-weight: 600;
    }
    
    .status-error {
        color: #d62728;
        font-weight: 600;
    }
    
    .status-warning {
        color: #ff7f0e;
        font-weight: 600;
    }
    
    .summary-box {
        background-color: white;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .enhancement-recommendation {
        background-color: white;
        border-left: 4px solid #2ca02c;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .correlation-suggestion {
        background-color: #e8f4f8;
        border-left: 4px solid #ff7f0e;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .error-message {
        background-color: #ffe6e6;
        border-left: 4px solid #d62728;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #d62728;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'jmeter_path': '',
        'jmeter_found': False,
        'jmeter_version': '',
        'jmx_file': None,
        'jmx_filename': '',
        'jmx_content': '',
        'api_key': '',
        'run_history': [],
        'last_run_output': '',
        'last_run_status': '',
        'dry_run_executed': False,
        'correlations_found': [],
        'enhancements_suggested': False,
        'enhancement_recommendations': [],
        'improved_jmx_draft': '',
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_jmeter_installed(jmeter_executable: str = 'jmeter') -> Tuple[bool, str]:
    """Check if JMeter is installed and accessible"""
    try:
        # Ensure executable path is provided
        if not jmeter_executable or jmeter_executable.strip() == '':
            return False, "No JMeter path specified"
        
        result = subprocess.run(
            [jmeter_executable, '--version'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except FileNotFoundError:
        return False, f"JMeter executable not found at: {jmeter_executable}"
    except PermissionError:
        return False, f"Permission denied. Cannot execute: {jmeter_executable}"
    except subprocess.TimeoutExpired:
        return False, "JMeter version check timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


def validate_jmx_file(content: str) -> Tuple[bool, str]:
    """Validate JMX file structure"""
    try:
        ET.fromstring(content)
        return True, "Valid JMX file"
    except ET.ParseError as e:
        return False, f"Invalid XML: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def parse_jmeter_output(log_content: str) -> Dict:
    """Parse JMeter log output for analysis"""
    summary = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'errors': [],
        'assertions_failed': False,
        'average_response_time': 0,
    }
    
    # Parse for common error patterns
    error_patterns = [
        r'ERROR -.*',
        r'WARN -.*',
        r'Assertion.*Failed',
        r'Exception.*',
    ]
    
    lines = log_content.split('\n')
    for line in lines:
        for pattern in error_patterns:
            match = re.search(pattern, line)
            if match:
                summary['errors'].append(match.group(0))
    
    summary['failed_requests'] = len(summary['errors'])
    
    return summary


def save_temp_jmx(content: str) -> str:
    """Save JMX content to temporary file"""
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, 'jmeter_temp.jmx')
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    return temp_file


def run_jmeter_dry_run(jmx_file: str, jmeter_executable: str) -> Tuple[bool, str, str]:
    """Execute JMeter in non-GUI mode for dry run"""
    try:
        results_file = os.path.join(tempfile.gettempdir(), 'results.jtl')
        log_file = os.path.join(tempfile.gettempdir(), 'jmeter.log')
        
        # Clean up old files
        for f in [results_file, log_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        
        # Execute JMeter command
        cmd = [
            jmeter_executable,
            '-n',
            '-t', jmx_file,
            '-l', results_file,
            '-j', log_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Read log output
        log_output = ""
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_output = f.read()
            except Exception as e:
                log_output = f"Error reading log: {str(e)}\n"
        
        # Get output from stdout/stderr if log file is empty
        if not log_output:
            log_output = result.stdout if result.stdout else result.stderr
        
        success = result.returncode == 0
        output = log_output if log_output else "No output captured"
        
        return success, output, results_file
        
    except subprocess.TimeoutExpired:
        return False, "JMeter execution timed out (>5 minutes)", ""
    except Exception as e:
        return False, f"Error executing JMeter: {str(e)}", ""


def get_openai_client(api_key: str):
    """Get OpenAI client instance"""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI library not installed")
    
    return openai.OpenAI(api_key=api_key)


def analyze_correlations_with_ai(
    jmx_content: str,
    jmeter_output: str,
    api_key: str
) -> List[Dict]:
    """Use OpenAI to suggest correlations"""
    try:
        client = get_openai_client(api_key)
        
        prompt = f"""Analyze this JMeter script and its execution output to identify potential correlations needed.

JMeter Script (JMX):
{jmx_content[:2000]}...

Execution Output:
{jmeter_output[:1500]}...

Please identify:
1. Variables that should be extracted from responses
2. Server-generated values that need correlation
3. Session tokens or IDs
4. CSRF tokens or similar security tokens
5. Dynamic data that varies between requests

Format your response as a JSON array with objects containing:
- "variable_name": the suggested variable name
- "extraction_pattern": the pattern to extract (regex or XPath)
- "source": where to extract from (response headers, body, etc.)
- "reason": why this correlation is needed
- "priority": "high", "medium", or "low"
"""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JMeter performance testing expert. Provide technical analysis in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse JSON from response
        try:
            json_str = response.choices[0].message.content
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            
            correlations = json.loads(json_str)
            if isinstance(correlations, dict):
                correlations = [correlations]
            return correlations if isinstance(correlations, list) else []
        except json.JSONDecodeError:
            return [{
                "variable_name": "correlation_1",
                "extraction_pattern": "Not extracted",
                "source": "Response body",
                "reason": "Unable to parse AI response",
                "priority": "medium"
            }]
    
    except Exception as e:
        st.error(f"Error analyzing correlations: {str(e)}")
        return []


def suggest_enhancements_with_ai(
    jmx_content: str,
    jmeter_output: str,
    api_key: str
) -> Tuple[List[Dict], str]:
    """Use OpenAI to suggest script enhancements"""
    try:
        client = get_openai_client(api_key)
        
        prompt = f"""You are a JMeter performance testing expert. Analyze this JMeter script and suggest specific enhancements.

Current JMeter Script:
{jmx_content[:3000]}...

Execution Output/Logs:
{jmeter_output[:2000]}...

Please provide:
1. Performance optimization suggestions
2. Best practices that are not being followed
3. Missing assertions or validations
4. Improved think time strategies
5. Configuration recommendations
6. Error handling improvements

For each suggestion, provide:
- "enhancement_id": unique identifier
- "category": type of enhancement (performance, validation, configuration, etc.)
- "title": short title
- "description": detailed description
- "implementation": how to implement it
- "expected_impact": expected benefit
- "priority": "critical", "high", "medium", or "low"

Also provide an improved JMX draft with key enhancements applied. Format your response as JSON with "recommendations" array and "improved_jmx_sample" string field.
"""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JMeter optimization expert. Provide detailed technical recommendations with implementation guidance."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=3000
        )
        
        try:
            json_str = response.choices[0].message.content
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            
            result = json.loads(json_str)
            recommendations = result.get('recommendations', [])
            improved_draft = result.get('improved_jmx_sample', '')
            
            return recommendations, improved_draft
        except json.JSONDecodeError:
            return [], ""
    
    except Exception as e:
        st.error(f"Error suggesting enhancements: {str(e)}")
        return [], ""


def format_execution_history(history: List) -> str:
    """Format execution history for display"""
    if not history:
        return "No executions yet"
    
    formatted = ""
    for idx, entry in enumerate(reversed(history), 1):
        formatted += f"\n**Execution {idx}** - {entry['timestamp']}\n"
        formatted += f"- Status: {entry['status']}\n"
        formatted += f"- File: {entry['filename']}\n"
        if entry.get('summary'):
            formatted += f"- Summary: {entry['summary']}\n"
    
    return formatted


# ============================================================================
# MAIN APP LAYOUT
# ============================================================================

def main():
    # Header Section
    st.markdown("""
    <div class="header-section">
        <h1>⚡ AI-Powered JMeter Script Enhancer</h1>
        <p>Professional Dashboard for JMeter Script Analysis & Optimization using OpenAI GPT</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # JMeter Path Configuration
        st.subheader("JMeter Configuration")
        st.info("""
        ℹ️ **No Permission to Change Environment Variables?**
        
        No problem! Specify the full path to your JMeter executable below.
        """)
        
        jmeter_path = st.text_input(
            "JMeter Executable Path",
            value=st.session_state.jmeter_path,
            placeholder="e.g., C:\\jmeter\\bin\\jmeter.bat or /usr/bin/jmeter",
            help="Full path to jmeter executable (with filename). Use .bat on Windows, no extension on Linux/Mac",
            key="jmeter_path_input"
        )
        
        # Update session state if path changed
        if jmeter_path.strip() != st.session_state.jmeter_path.strip():
            st.session_state.jmeter_path = jmeter_path.strip()
        
        # Auto-detect button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Auto-Detect", use_container_width=True):
                # Try common paths
                common_paths = [
                    'jmeter',
                    'jmeter.bat',
                    '/usr/bin/jmeter',
                    '/usr/local/bin/jmeter',
                    'C:\\jmeter\\bin\\jmeter.bat',
                    'C:\\Program Files\\jmeter\\bin\\jmeter.bat',
                    'C:\\Program Files (x86)\\jmeter\\bin\\jmeter.bat',
                ]
                
                found = False
                for path in common_paths:
                    is_valid, version = check_jmeter_installed(path)
                    if is_valid:
                        st.session_state.jmeter_path = path
                        st.success(f"✅ Found JMeter: {path}\n{version}")
                        found = True
                        break
                
                if not found:
                    st.warning("❌ Could not auto-detect JMeter. Please provide the full path manually.")
        
        with col2:
            if st.button("✓ Verify Path", use_container_width=True):
                if st.session_state.jmeter_path.strip():
                    is_valid, version = check_jmeter_installed(st.session_state.jmeter_path)
                    if is_valid:
                        st.session_state.jmeter_found = True
                        st.session_state.jmeter_version = version
                        st.success(f"✅ Valid!\n{version}")
                    else:
                        st.session_state.jmeter_found = False
                        st.session_state.jmeter_version = ""
                        st.error(f"❌ {version}")
                else:
                    st.error("❌ Please enter a JMeter path first")
        
        st.divider()
        
        # API Key Input
        st.subheader("OpenAI API Configuration")
        api_key = st.text_input(
            "Enter your OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            help="Your API key for GPT-4 analysis. Get it from https://platform.openai.com/api-keys",
            key="api_key_input"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
        
        st.divider()
        
        # System Status
        st.subheader("System Status")
        
        # Check JMeter status based on current path
        if st.session_state.jmeter_path and st.session_state.jmeter_path.strip():
            jmeter_installed, jmeter_version = check_jmeter_installed(st.session_state.jmeter_path)
            st.session_state.jmeter_found = jmeter_installed
            if jmeter_installed:
                st.session_state.jmeter_version = jmeter_version
            
            if st.session_state.jmeter_found:
                st.success(f"✅ JMeter Ready\n{st.session_state.jmeter_version}")
            else:
                st.markdown("""
                <div class="error-message">
                <strong>❌ JMeter Not Available</strong><br>
                Path: {}<br>
                Click "Verify Path" button to diagnose
                </div>
                """.format(st.session_state.jmeter_path), unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please configure JMeter path above")
            st.session_state.jmeter_found = False
        
        st.divider()
        
        # Execution History
        st.subheader("📋 Execution History")
        st.markdown(format_execution_history(st.session_state.run_history))
    
    # ============================================================================
    # MAIN CONTENT TABS
    # ============================================================================
    
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Documentation", "Settings"])
    
    with tab1:  # MAIN DASHBOARD
        
        # ==================== UPLOAD & VALIDATION PANEL ====================
        st.markdown('<div class="panel"><div class="panel-title">📤 Upload & Validate JMX Script</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose a JMX file",
                type=['jmx'],
                help="Select your JMeter test plan file"
            )
        
        with col2:
            clear_file = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_file:
            st.session_state.jmx_file = None
            st.session_state.jmx_content = ''
            st.session_state.jmx_filename = ''
            st.rerun()
        
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode('utf-8')
            st.session_state.jmx_file = uploaded_file
            st.session_state.jmx_filename = uploaded_file.name
            st.session_state.jmx_content = file_content
            
            # Validation
            is_valid, validation_msg = validate_jmx_file(file_content)
            
            if is_valid:
                st.success(f"✅ {validation_msg}")
                st.info(f"File: **{uploaded_file.name}** | Size: **{len(file_content)} bytes**")
            else:
                st.error(f"❌ {validation_msg}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== RUN CONTROL PANEL ====================
        st.markdown('<div class="panel"><div class="panel-title">▶️ Run Control</div>', unsafe_allow_html=True)
        
        # Debug information
        debug_col1, debug_col2, debug_col3 = st.columns(3)
        with debug_col1:
            st.metric("JMX Loaded", "✅" if st.session_state.jmx_content else "❌")
        with debug_col2:
            st.metric("JMeter Ready", "✅" if st.session_state.jmeter_found else "❌")
        with debug_col3:
            st.metric("Path Set", "✅" if st.session_state.jmeter_path else "❌")
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        # Determine if button should be disabled
        can_run_dry_run = (
            bool(st.session_state.jmx_content and st.session_state.jmx_content.strip()) and
            bool(st.session_state.jmeter_path and st.session_state.jmeter_path.strip()) and
            st.session_state.jmeter_found
        )
        
        with col1:
            if st.button(
                "🚀 Run Dry Run",
                disabled=not can_run_dry_run,
                use_container_width=True,
                help="Execute JMeter in non-GUI mode" if can_run_dry_run else "Please: 1) Upload JMX file 2) Set JMeter path 3) Verify JMeter"
            ):
                with st.spinner("🔄 Executing JMeter dry run..."):
                    temp_jmx = save_temp_jmx(st.session_state.jmx_content)
                    success, output, results_file = run_jmeter_dry_run(temp_jmx, st.session_state.jmeter_path)
                    
                    st.session_state.last_run_output = output
                    st.session_state.last_run_status = "success" if success else "failed"
                    st.session_state.dry_run_executed = True
                    
                    # Add to history
                    history_entry = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'filename': st.session_state.jmx_filename,
                        'status': st.session_state.last_run_status,
                        'summary': f"Execution completed with {'success' if success else 'errors'}"
                    }
                    st.session_state.run_history.append(history_entry)
                    
                    # Clean up
                    try:
                        os.remove(temp_jmx)
                    except:
                        pass
                    
                    st.rerun()
        
        with col2:
            show_script = st.button(
                "📋 View Script",
                disabled=not st.session_state.jmx_content,
                use_container_width=True
            )
            
            if show_script and st.session_state.jmx_content:
                with st.expander("View Full JMX Script", expanded=True):
                    st.code(st.session_state.jmx_content, language='xml')
        
        with col3:
            download_button = st.button(
                "💾 Download Script",
                disabled=not st.session_state.jmx_content,
                use_container_width=True
            )
            
            if download_button and st.session_state.jmx_content:
                st.download_button(
                    label="⬇️ Download JMX",
                    data=st.session_state.jmx_content,
                    file_name=st.session_state.jmx_filename or "jmeter_script.jmx",
                    mime="application/xml",
                    use_container_width=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== RUN OUTPUT SUMMARY PANEL ====================
        if st.session_state.dry_run_executed:
            st.markdown('<div class="panel"><div class="panel-title">📊 Run Output & Summary</div>', unsafe_allow_html=True)
            
            # Status indicator
            if st.session_state.last_run_status == "success":
                st.markdown(
                    '<p class="status-success">✅ DRY RUN SUCCESSFUL</p>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<p class="status-error">❌ DRY RUN FAILED - Review Output Below</p>',
                    unsafe_allow_html=True
                )
            
            # Parse and display summary
            run_summary = parse_jmeter_output(st.session_state.last_run_output)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Errors Detected", len(run_summary['errors']))
            with col2:
                st.metric("Failed Requests", run_summary['failed_requests'])
            with col3:
                st.metric("Status", st.session_state.last_run_status.upper())
            
            # Detailed output
            with st.expander("📝 Full JMeter Output Log", expanded=False):
                st.text_area(
                    "JMeter Log Output",
                    value=st.session_state.last_run_output,
                    height=300,
                    disabled=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ==================== CORRELATION SUGGESTIONS PANEL ====================
            if st.session_state.api_key and st.session_state.last_run_status == "success":
                st.markdown('<div class="panel"><div class="panel-title">🔗 AI-Suggested Correlations</div>', unsafe_allow_html=True)
                
                if st.button("🤖 Analyze for Correlations", use_container_width=True, key="correlation_btn"):
                    with st.spinner("🧠 Analyzing with OpenAI GPT..."):
                        correlations = analyze_correlations_with_ai(
                            st.session_state.jmx_content,
                            st.session_state.last_run_output,
                            st.session_state.api_key
                        )
                        st.session_state.correlations_found = correlations
                        st.rerun()
                
                if st.session_state.correlations_found:
                    for idx, corr in enumerate(st.session_state.correlations_found, 1):
                        st.markdown(f"""
                        <div class="correlation-suggestion">
                        <strong>Suggestion {idx}: {corr.get('variable_name', 'N/A')}</strong><br>
                        <strong>Priority:</strong> {corr.get('priority', 'medium').upper()}<br>
                        <strong>Source:</strong> {corr.get('source', 'N/A')}<br>
                        <strong>Pattern:</strong> <code>{corr.get('extraction_pattern', 'N/A')}</code><br>
                        <strong>Reason:</strong> {corr.get('reason', 'N/A')}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # ==================== ENHANCEMENT DECISION PANEL ====================
            st.markdown('<div class="panel"><div class="panel-title">🎯 Script Enhancement</div>', unsafe_allow_html=True)
            
            enhance_choice = st.radio(
                "Would you like to enhance this script using AI recommendations?",
                options=["Not now", "Yes, analyze and enhance"],
                horizontal=True,
                key="enhance_choice"
            )
            
            if enhance_choice == "Yes, analyze and enhance" and st.session_state.api_key:
                if st.button("💡 Get Enhancement Recommendations", use_container_width=True, key="enhance_btn"):
                    with st.spinner("🧠 Analyzing with OpenAI GPT..."):
                        recommendations, improved_draft = suggest_enhancements_with_ai(
                            st.session_state.jmx_content,
                            st.session_state.last_run_output,
                            st.session_state.api_key
                        )
                        st.session_state.enhancement_recommendations = recommendations
                        st.session_state.improved_jmx_draft = improved_draft
                        st.session_state.enhancements_suggested = True
                        st.rerun()
                
                if st.session_state.enhancements_suggested:
                    st.success("✅ Enhancement analysis complete!")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== ENHANCEMENT RECOMMENDATIONS PANEL ====================
        if st.session_state.enhancements_suggested and st.session_state.enhancement_recommendations:
            st.markdown('<div class="panel"><div class="panel-title">🚀 Enhancement Recommendations</div>', unsafe_allow_html=True)
            
            for rec in st.session_state.enhancement_recommendations:
                priority_color = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(rec.get('priority', 'medium').lower(), '⚫')
                
                st.markdown(f"""
                <div class="enhancement-recommendation">
                <strong>{priority_color} {rec.get('title', 'Enhancement')}</strong><br>
                <strong>Category:</strong> {rec.get('category', 'N/A')}<br>
                <strong>Description:</strong> {rec.get('description', 'N/A')}<br>
                <strong>Implementation:</strong> {rec.get('implementation', 'N/A')}<br>
                <strong>Expected Impact:</strong> {rec.get('expected_impact', 'N/A')}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== IMPROVED JMX PREVIEW PANEL ====================
        if st.session_state.improved_jmx_draft:
            st.markdown('<div class="panel"><div class="panel-title">📦 Improved JMX Draft Preview</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 View Draft", use_container_width=True, key="view_draft_btn"):
                    with st.expander("Improved JMX Draft", expanded=True):
                        st.code(st.session_state.improved_jmx_draft, language='xml')
            
            with col2:
                st.download_button(
                    label="⬇️ Download Draft",
                    data=st.session_state.improved_jmx_draft,
                    file_name="jmeter_improved_draft.jmx",
                    mime="application/xml",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:  # DOCUMENTATION
        st.header("📚 User Guide & Documentation")
        
        st.subheader("Getting Started")
        st.markdown("""
        ### 1. **Setup & Configuration**
        - JMeter must be installed on your system
        - Obtain an OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys)
        - Enter your JMeter path and API key in the sidebar configuration
        
        ### 2. **Configuring JMeter Path (Without System PATH Access)**
        
        #### Windows
        ```
        C:\\jmeter\\bin\\jmeter.bat
        C:\\Program Files\\Apache JMeter\\bin\\jmeter.bat
        ```
        
        #### Linux/Mac
        ```
        /usr/bin/jmeter
        /usr/local/bin/jmeter
        /opt/jmeter/bin/jmeter
        ```
        
        #### If you don't know the path:
        - **Windows**: Open Command Prompt, type `where jmeter.bat`
        - **Linux/Mac**: Open Terminal, type `which jmeter`
        
        ### 3. **Upload Your JMeter Script**
        - Click the upload area to select your `.jmx` file
        - The system will validate the XML structure
        - View the script using the "View Script" button
        
        ### 4. **Run Dry Run**
        - **Prerequisites:**
          1. Upload a valid JMX file ✅
          2. Enter a valid JMeter path ✅
          3. Click "Verify Path" to confirm JMeter is accessible ✅
        - Click "Run Dry Run" to execute your script in non-GUI mode
        - The system executes: `jmeter -n -t <file.jmx> -l results.jtl -j jmeter.log`
        - Results and logs are analyzed automatically
        
        ### 5. **AI-Powered Analysis**
        - **Correlation Analysis**: Identifies variables and tokens to extract
        - **Enhancement Suggestions**: Recommends optimizations and best practices
        - Uses GPT-4 Turbo for intelligent analysis
        - Requires valid OpenAI API key
        
        ### 6. **Download Improved Script**
        - Review recommended enhancements
        - Download the AI-generated improved JMX draft
        - Manually review before using in production
        """)
        
        st.divider()
        
        st.subheader("Troubleshooting: Run Dry Run Button Not Enabled?")
        st.markdown("""
        The "Run Dry Run" button requires **THREE conditions** to be enabled:
        
        1. **✅ JMX File Uploaded**
           - Click in the upload area
           - Select your `.jmx` file
           - Verify the green "Valid JMX file" message appears
        
        2. **✅ JMeter Path Configured**
           - Enter full path in "JMeter Executable Path" field
           - Examples:
             - Windows: `C:\\jmeter\\bin\\jmeter.bat`
             - Linux/Mac: `/usr/bin/jmeter`
        
        3. **✅ JMeter Verified**
           - Click "Verify Path" button
           - Wait for green "✅ Valid" message
           - Or use "Auto-Detect" button to find it automatically
        
        **Debug Checklist in Run Control Panel:**
        ```
        JMX Loaded: ✅ (must be green)
        JMeter Ready: ✅ (must be green)
        Path Set: ✅ (must be green)
        ```
        
        If all three are green, the "Run Dry Run" button will be **enabled**.
        """)
        
        st.divider()
        
        st.subheader("Feature Overview")
        
        features = {
            "📤 JMX Upload & Validation": "Upload and validate JMeter test plans with XML schema validation",
            "▶️ Dry Run Execution": "Execute scripts in non-GUI mode with detailed logging",
            "🔗 Correlation Analysis": "AI identifies variables that need correlation (session tokens, CSRF tokens, etc.)",
            "💡 Enhancement Suggestions": "AI recommends optimizations, assertions, and best practices",
            "📊 Detailed Reporting": "Comprehensive summaries of execution results and issues",
            "📦 Improved Draft Preview": "Generated enhanced JMX scripts ready for download",
            "📋 Execution History": "Session-scoped history of all executed runs",
        }
        
        for feature, description in features.items():
            st.markdown(f"**{feature}**: {description}")
        
        st.divider()
        
        st.subheader("API Key Security")
        st.warning("""
        🔐 **Important Security Notes:**
        - Your API key is only used for the duration of your session
        - It is NOT stored or persisted anywhere
        - It is sent directly to OpenAI for analysis
        - Use a dedicated API key with appropriate rate limits
        - Never share your API key with others
        """)
    
    with tab3:  # SETTINGS
        st.header("⚙️ Settings & Preferences")
        
        st.subheader("JMeter Path Configuration")
        st.info(f"""
        **Current JMeter Path:** `{st.session_state.jmeter_path if st.session_state.jmeter_path else 'Not configured'}`
        
        **Status:** {'✅ Valid and Ready' if st.session_state.jmeter_found else '❌ Invalid or Not Found'}
        """)
        
        st.subheader("Finding JMeter Path on Your System")
        
        with st.expander("🪟 Windows Instructions"):
            st.code("""
# Open Command Prompt (cmd.exe) and run:
where jmeter.bat

# Example output:
# C:\\jmeter\\bin\\jmeter.bat

# Copy this path to the sidebar configuration
            """, language="bash")
        
        with st.expander("🐧 Linux/Mac Instructions"):
            st.code("""
# Open Terminal and run:
which jmeter

# Example output:
# /usr/local/bin/jmeter

# Copy this path to the sidebar configuration
            """, language="bash")
        
        st.divider()
        
        st.subheader("AI Model Configuration")
        st.info("""
        **Current Configuration:**
        - Model: OpenAI GPT-4 Turbo
        - Temperature: 0.3 (for consistent, focused responses)
        - Max Tokens: 2000-3000 (depending on task)
        - Response Format: JSON with technical details
        """)
        
        st.divider()
        
        st.subheader("About This Application")
        st.markdown("""
        **AI-Powered JMeter Script Enhancer v1.1**
        
        A professional Streamlit dashboard for analyzing and enhancing JMeter performance test scripts 
        using OpenAI's GPT models.
        
        **Built with:**
        - 🐍 Python & Streamlit
        - 🤖 OpenAI GPT-4 Turbo API
        - 📊 JMeter
        - 🎨 Corporate light theme UI
        
        **Designed for:**
        - Performance Testers
        - QA Engineers
        - SDETs (SDET)
        - DevOps Engineers
        
        **v1.1 Improvements:**
        - Fixed Run Dry Run button enable/disable logic
        - Added debug metrics in Run Control panel
        - Improved JMeter path validation feedback
        - Better error messages for troubleshooting
        """)


# ============================================================================
# APP ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
