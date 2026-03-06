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
import csv
from io import StringIO

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
    
    .scenario-config {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .override-info {
        background-color: #fff3cd;
        border-left: 4px solid #ff7f0e;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #856404;
    }
    
    .csv-config-info {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .threadgroup-card {
        background-color: #e8f4f8;
        border-left: 4px solid #2ca02c;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .threadgroup-property {
        background-color: #fff9e6;
        border-left: 4px solid #ff9800;
        padding: 0.75rem;
        margin: 0.25rem 0;
        border-radius: 4px;
        font-size: 0.9rem;
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
        'scenario_config': {
            'num_threads': 10,
            'ramp_up_time': 60,
            'steady_state_duration': 300,
            'iterations': 1,
            'apply_to_all': True,
        },
        'aggregate_report': None,
        'aggregate_report_generated': False,
        'original_thread_groups': [],
        'execution_command': '',
        'csv_files': {},
        'csv_configs_found': [],
        'csv_file_paths': {},
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_csv_dataset_configs(jmx_content: str) -> List[Dict]:
    """Extract all CSV Dataset Config elements from JMX"""
    try:
        root = ET.fromstring(jmx_content)
        csv_configs = []
        
        csv_datasets = root.findall('.//CSVDataSet')
        
        for idx, csv_elem in enumerate(csv_datasets):
            csv_info = {
                'index': idx,
                'name': 'CSVDataSet',
                'filename': None,
                'filename_raw': None,
                'delimiter': ',',
                'variable_names': None,
                'recycle': True,
                'stop_on_eof': False,
            }
            
            for attr in csv_elem.attrib:
                if 'testname' in attr.lower():
                    csv_info['name'] = csv_elem.attrib[attr]
                    break
            
            for elem in csv_elem.findall(".//stringProp[@name='filename']"):
                raw_value = elem.text if elem.text else None
                if raw_value:
                    csv_info['filename_raw'] = raw_value
                    csv_info['filename'] = raw_value
            
            for elem in csv_elem.findall(".//stringProp[@name='delimiter']"):
                if elem.text:
                    csv_info['delimiter'] = elem.text
            
            for elem in csv_elem.findall(".//stringProp[@name='variableNames']"):
                if elem.text:
                    csv_info['variable_names'] = elem.text
            
            for elem in csv_elem.findall(".//boolProp[@name='recycle']"):
                if elem.text:
                    csv_info['recycle'] = elem.text.lower() == 'true'
            
            for elem in csv_elem.findall(".//boolProp[@name='stopThread']"):
                if elem.text:
                    csv_info['stop_on_eof'] = elem.text.lower() == 'true'
            
            csv_configs.append(csv_info)
        
        return csv_configs
    except Exception as e:
        st.warning(f"Could not extract CSV Dataset Configs: {str(e)}")
        return []


def extract_property_value(value_str: str) -> Tuple[Optional[int], str]:
    """Extract numeric value from JMeter property expressions"""
    if not value_str:
        return None, "empty"
    
    value_str = value_str.strip()
    
    try:
        num_val = int(value_str)
        return num_val, "plain"
    except ValueError:
        pass
    
    property_match = re.search(r'\$\{__P\([^,]+,\s*(\d+)\)\}', value_str)
    if property_match:
        try:
            default_val = int(property_match.group(1))
            return default_val, "property"
        except ValueError:
            pass
    
    if re.match(r'^\$\{[^}]+\}$', value_str):
        return None, "variable"
    
    return None, "expression"


def extract_all_thread_groups(jmx_content: str) -> List[Dict]:
    """Extract ALL ThreadGroup configurations with property value extraction"""
    try:
        root = ET.fromstring(jmx_content)
        thread_groups_info = []
        
        thread_groups = root.findall('.//ThreadGroup')
        
        for idx, tg in enumerate(thread_groups):
            tg_info = {
                'index': idx,
                'name': 'ThreadGroup',
                'num_threads': None,
                'num_threads_raw': None,
                'num_threads_source': 'unknown',
                'ramp_up_time': None,
                'ramp_up_time_raw': None,
                'ramp_up_time_source': 'unknown',
                'steady_state_duration': None,
                'steady_state_duration_raw': None,
                'steady_state_duration_source': 'unknown',
                'iterations': None,
                'iterations_raw': None,
                'iterations_source': 'unknown',
            }
            
            for attr in tg.attrib:
                if 'testname' in attr.lower():
                    tg_info['name'] = tg.attrib[attr]
                    break
            
            for elem in tg.findall(".//stringProp[@name='ThreadGroup.num_threads']"):
                raw_value = elem.text if elem.text else None
                if raw_value:
                    tg_info['num_threads_raw'] = raw_value
                    num_val, source = extract_property_value(raw_value)
                    if num_val is not None:
                        tg_info['num_threads'] = num_val
                        tg_info['num_threads_source'] = source
            
            for elem in tg.findall(".//stringProp[@name='ThreadGroup.ramp_time']"):
                raw_value = elem.text if elem.text else None
                if raw_value:
                    tg_info['ramp_up_time_raw'] = raw_value
                    num_val, source = extract_property_value(raw_value)
                    if num_val is not None:
                        tg_info['ramp_up_time'] = num_val
                        tg_info['ramp_up_time_source'] = source
            
            for elem in tg.findall(".//stringProp[@name='ThreadGroup.duration']"):
                raw_value = elem.text if elem.text else None
                if raw_value:
                    tg_info['steady_state_duration_raw'] = raw_value
                    num_val, source = extract_property_value(raw_value)
                    if num_val is not None:
                        tg_info['steady_state_duration'] = num_val
                        tg_info['steady_state_duration_source'] = source
            
            for elem in tg.findall(".//elementProp[@name='ThreadGroup.main_controller']/stringProp[@name='LoopController.loops']"):
                raw_value = elem.text if elem.text else None
                if raw_value:
                    tg_info['iterations_raw'] = raw_value
                    if raw_value.strip() != '-1':
                        num_val, source = extract_property_value(raw_value)
                        if num_val is not None:
                            tg_info['iterations'] = num_val
                            tg_info['iterations_source'] = source
            
            thread_groups_info.append(tg_info)
        
        return thread_groups_info
    except Exception as e:
        st.warning(f"Could not extract ThreadGroups from script: {str(e)}")
        return []


def check_jmeter_file_exists(jmeter_executable: str) -> Tuple[bool, str]:
    """Check if JMeter executable file exists"""
    try:
        if not jmeter_executable or jmeter_executable.strip() == '':
            return False, "No JMeter path specified"
        
        path = jmeter_executable.strip('"\'')
        
        if os.path.isfile(path):
            return True, f"File found at: {path}"
        else:
            if not path.endswith('.bat') and os.path.isfile(path + '.bat'):
                return True, f"File found at: {path}.bat"
            
            return False, f"File not found at: {path}"
    except Exception as e:
        return False, f"Error checking file: {str(e)}"


def check_jmeter_installed(jmeter_executable: str = 'jmeter', timeout: int = 20) -> Tuple[bool, str]:
    """Check if JMeter is installed and accessible"""
    try:
        if not jmeter_executable or jmeter_executable.strip() == '':
            return False, "No JMeter path specified"
        
        path = jmeter_executable.strip('"\'')
        
        file_exists, file_msg = check_jmeter_file_exists(path)
        if not file_exists:
            return False, file_msg
        
        try:
            result = subprocess.run(
                [path, '--version'], 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            if result.returncode == 0:
                version_output = result.stdout.strip() or result.stderr.strip()
                return True, f"✅ JMeter is available\n{version_output}"
            else:
                return True, f"✅ JMeter executable found\n(version check returned code {result.returncode})"
        
        except subprocess.TimeoutExpired:
            return True, f"✅ JMeter found (version check timed out, but executable exists)"
        
    except PermissionError:
        return False, f"❌ Permission denied. Cannot execute: {jmeter_executable}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def validate_jmx_file(content: str) -> Tuple[bool, str]:
    """Validate JMX file structure"""
    try:
        ET.fromstring(content)
        return True, "Valid JMX file"
    except ET.ParseError as e:
        return False, f"Invalid XML: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def modify_csv_dataset_paths(jmx_content: str, csv_file_paths: Dict[str, str]) -> str:
    """Modify CSV Dataset Config filenames in JMX with user-provided paths"""
    try:
        root = ET.fromstring(jmx_content)
        csv_datasets = root.findall('.//CSVDataSet')
        
        if not csv_datasets:
            return jmx_content
        
        modified_count = 0
        
        for idx, csv_elem in enumerate(csv_datasets):
            csv_name = 'CSVDataSet'
            for attr in csv_elem.attrib:
                if 'testname' in attr.lower():
                    csv_name = csv_elem.attrib[attr]
                    break
            
            if csv_name in csv_file_paths:
                new_path = csv_file_paths[csv_name]
                
                for elem in csv_elem.findall(".//stringProp[@name='filename']"):
                    old_path = elem.text
                    elem.text = new_path
                    st.info(f"✏️ Updated CSV path for '{csv_name}':\n  Old: {old_path}\n  New: {new_path}")
                    modified_count += 1
        
        if modified_count > 0:
            st.success(f"✅ Modified {modified_count} CSV Dataset Config(s)")
        
        return ET.tostring(root, encoding='unicode')
    
    except Exception as e:
        st.error(f"❌ Error modifying CSV paths: {str(e)}")
        return jmx_content


def modify_all_thread_groups(jmx_content: str, scenario: Dict) -> str:
    """Override ALL ThreadGroup parameters in JMX with scenario values"""
    try:
        root = ET.fromstring(jmx_content)
        thread_groups = root.findall('.//ThreadGroup')
        
        if not thread_groups:
            st.warning("⚠️ No ThreadGroup found in JMX.")
            return jmx_content
        
        apply_to_all = scenario.get('apply_to_all', True)
        selected_indices = scenario.get('selected_thread_groups', list(range(len(thread_groups))))
        
        st.info(f"📋 Found {len(thread_groups)} ThreadGroup(s). {'Applying to ALL.' if apply_to_all else 'Applying to selected.'}")
        
        for tg_idx, tg in enumerate(thread_groups):
            if not apply_to_all and tg_idx not in selected_indices:
                st.info(f"⏭️ Skipping ThreadGroup {tg_idx + 1}")
                continue
            
            st.info(f"✏️ Modifying ThreadGroup {tg_idx + 1}/{len(thread_groups)}")
            
            threads_modified = False
            for elem in tg.findall(".//stringProp[@name='ThreadGroup.num_threads']"):
                elem.text = str(scenario['num_threads'])
                threads_modified = True
            
            if not threads_modified:
                st.warning(f"⚠️ ThreadGroup {tg_idx + 1}: Could not find num_threads element")
            
            rampup_modified = False
            for elem in tg.findall(".//stringProp[@name='ThreadGroup.ramp_time']"):
                elem.text = str(scenario['ramp_up_time'])
                rampup_modified = True
            
            if not rampup_modified:
                st.warning(f"⚠️ ThreadGroup {tg_idx + 1}: Could not find ramp_time element")
            
            duration_modified = False
            for elem in tg.findall(".//stringProp[@name='ThreadGroup.duration']"):
                elem.text = str(scenario['steady_state_duration'])
                duration_modified = True
            
            if not duration_modified:
                st.warning(f"⚠️ ThreadGroup {tg_idx + 1}: Could not find duration element")
            
            loop_modified = False
            for elem in tg.findall(".//elementProp[@name='ThreadGroup.main_controller']/stringProp[@name='LoopController.loops']"):
                elem.text = str(scenario['iterations'])
                loop_modified = True
            
            if not loop_modified:
                st.warning(f"⚠️ ThreadGroup {tg_idx + 1}: Could not find loop element")
        
        return ET.tostring(root, encoding='unicode')
    
    except Exception as e:
        st.error(f"❌ Error modifying JMX: {str(e)}")
        return jmx_content


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
    
    error_patterns = [
        r'ERROR -.*',
        r'WARN -.*',
        r'Assertion.*Failed',
        r'Exception.*',
        r'Cannot open file.*',
        r'could not be found.*',
    ]
    
    lines = log_content.split('\n')
    for line in lines:
        for pattern in error_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
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


def parse_jtl_results(jtl_file: str) -> Dict:
    """Parse JTL (CSV) results file and generate aggregate report"""
    try:
        if not os.path.exists(jtl_file):
            return None
        
        with open(jtl_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return None
        
        response_times = []
        success_count = 0
        failure_count = 0
        
        for row in rows:
            try:
                elapsed = int(row.get('elapsed', 0))
                success = row.get('success', 'false').lower() == 'true'
                
                response_times.append(elapsed)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            except:
                continue
        
        if not response_times:
            return None
        
        response_times.sort()
        report = {
            'total_samples': len(rows),
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': (success_count / len(rows) * 100) if rows else 0,
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'avg_response_time': sum(response_times) / len(response_times),
            'median_response_time': response_times[len(response_times) // 2],
            'p90_response_time': response_times[int(len(response_times) * 0.9)],
            'p95_response_time': response_times[int(len(response_times) * 0.95)],
            'p99_response_time': response_times[int(len(response_times) * 0.99)],
            'throughput': len(rows) / 60,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        return report
    except Exception as e:
        st.error(f"Error parsing JTL file: {str(e)}")
        return None


def run_jmeter_dry_run(jmx_file: str, jmeter_executable: str, timeout: int = 1800, working_dir: str = None) -> Tuple[bool, str, str]:
    """Execute JMeter in non-GUI mode with proper working directory"""
    try:
        results_file = os.path.join(tempfile.gettempdir(), 'results.jtl')
        log_file = os.path.join(tempfile.gettempdir(), 'jmeter.log')
        
        for f in [results_file, log_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        
        path = jmeter_executable.strip('"\'')
        
        cmd = [
            path,
            '-n',
            '-t', jmx_file,
            '-l', results_file,
            '-j', log_file
        ]
        
        st.session_state.execution_command = ' '.join(cmd)
        st.info(f"📋 Executing: `{' '.join(cmd)}`")
        if working_dir:
            st.info(f"📁 Working Directory: `{working_dir}`")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir
        )
        
        log_output = ""
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_output = f.read()
            except Exception as e:
                log_output = f"Error reading log: {str(e)}\n"
        
        if not log_output:
            log_output = result.stdout if result.stdout else result.stderr
        
        success = os.path.exists(results_file) and result.returncode == 0
        output = log_output if log_output else "Execution completed"
        
        return success, output, results_file
        
    except subprocess.TimeoutExpired:
        return False, f"⏱️ JMeter execution timed out after {timeout} seconds.\n\nTips to reduce timeout:\n- Reduce number of threads\n- Reduce steady state duration\n- Reduce iterations\n- Reduce test plan complexity", ""
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
        
        try:
            json_str = response.choices[0].message.content
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


def generate_aggregate_report_csv(report: Dict) -> str:
    """Generate CSV format aggregate report"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['JMeter Aggregate Report', report['timestamp']])
    writer.writerow([])
    
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Samples', report['total_samples']])
    writer.writerow(['Successful', report['success_count']])
    writer.writerow(['Failed', report['failure_count']])
    writer.writerow(['Success Rate (%)', f"{report['success_rate']:.2f}"])
    writer.writerow([])
    writer.writerow(['Response Time Metrics (ms)'])
    writer.writerow(['Min', report['min_response_time']])
    writer.writerow(['Max', report['max_response_time']])
    writer.writerow(['Average', f"{report['avg_response_time']:.2f}"])
    writer.writerow(['Median', report['median_response_time']])
    writer.writerow(['90th Percentile (P90)', report['p90_response_time']])
    writer.writerow(['95th Percentile (P95)', report['p95_response_time']])
    writer.writerow(['99th Percentile (P99)', report['p99_response_time']])
    writer.writerow([])
    writer.writerow(['Throughput (samples/sec)', f"{report['throughput']:.2f}"])
    
    return output.getvalue()


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
        
        if jmeter_path.strip() != st.session_state.jmeter_path.strip():
            st.session_state.jmeter_path = jmeter_path.strip()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Auto-Detect", use_container_width=True, help="Search common JMeter installation paths"):
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
                    is_valid, version = check_jmeter_installed(path, timeout=10)
                    if is_valid:
                        st.session_state.jmeter_path = path
                        st.success(f"✅ Found JMeter at:\n{path}\n\n{version}")
                        found = True
                        break
                
                if not found:
                    st.warning("❌ Could not auto-detect JMeter.\n\nPlease provide the full path manually.")
        
        with col2:
            if st.button("✓ Verify", use_container_width=True, help="Verify JMeter at specified path"):
                if st.session_state.jmeter_path.strip():
                    with st.spinner("⏳ Checking JMeter..."):
                        is_valid, message = check_jmeter_installed(st.session_state.jmeter_path, timeout=15)
                        if is_valid:
                            st.session_state.jmeter_found = True
                            st.session_state.jmeter_version = message
                            st.success(message)
                        else:
                            st.session_state.jmeter_found = False
                            st.session_state.jmeter_version = ""
                            st.error(message)
                else:
                    st.error("❌ Please enter a JMeter path first")
        
        with col3:
            if st.button("🗑️ Clear", use_container_width=True, help="Clear JMeter path"):
                st.session_state.jmeter_path = ''
                st.session_state.jmeter_found = False
                st.session_state.jmeter_version = ''
                st.rerun()
        
        st.divider()
        
        with st.expander("🔎 Help Finding JMeter Path"):
            st.markdown("""
            **Windows:**
            ```
            Open Command Prompt and run:
            where jmeter.bat
            ```
            
            **Linux/Mac:**
            ```
            Open Terminal and run:
            which jmeter
            ```
            """)
        
        st.divider()
        
        st.subheader("OpenAI API Configuration")
        api_key = st.text_input(
            "Enter your OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            help="Your API key for GPT-4 analysis",
            key="api_key_input"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
        
        st.divider()
        
        st.subheader("System Status")
        
        if st.session_state.jmeter_path and st.session_state.jmeter_path.strip():
            if st.session_state.jmeter_found:
                st.success(f"✅ JMeter Ready")
            else:
                st.markdown("""
                <div class="error-message">
                <strong>❌ JMeter Not Verified</strong><br>
                Click "Verify" button to test the path
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please configure JMeter path above")
            st.session_state.jmeter_found = False
        
        st.divider()
        
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
            st.session_state.original_thread_groups = []
            st.session_state.csv_configs_found = []
            st.session_state.csv_file_paths = {}
            st.rerun()
        
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode('utf-8')
            st.session_state.jmx_file = uploaded_file
            st.session_state.jmx_filename = uploaded_file.name
            st.session_state.jmx_content = file_content
            
            is_valid, validation_msg = validate_jmx_file(file_content)
            
            if is_valid:
                st.success(f"✅ {validation_msg}")
                st.info(f"File: **{uploaded_file.name}** | Size: **{len(file_content)} bytes**")
                
                # Extract ALL ThreadGroups
                thread_groups = extract_all_thread_groups(file_content)
                st.session_state.original_thread_groups = thread_groups
                
                # Extract CSV Dataset Configs
                csv_configs = extract_csv_dataset_configs(file_content)
                st.session_state.csv_configs_found = csv_configs
                
                if thread_groups:
                    st.success(f"✅ Found {len(thread_groups)} ThreadGroup(s)")
                    
                    with st.expander(f"📋 Original ThreadGroup Values ({len(thread_groups)} groups)", expanded=False):
                        for idx, tg in enumerate(thread_groups):
                            st.markdown(f"""
                            <div class="threadgroup-card">
                            <strong>ThreadGroup {idx + 1}: {tg['name']}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if tg['num_threads'] is not None:
                                    st.markdown(f"""
                                    <div class="threadgroup-property">
                                    <strong>Threads:</strong> {tg['num_threads']} 
                                    <br><small>Source: {tg['num_threads_source']}</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.warning(f"⚠️ **Threads:** Could not extract ({tg['num_threads_source']})")
                                
                                if tg['ramp_up_time'] is not None:
                                    st.markdown(f"""
                                    <div class="threadgroup-property">
                                    <strong>Ramp-up:</strong> {tg['ramp_up_time']}s
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.warning(f"⚠️ **Ramp-up:** Could not extract")
                            
                            with col2:
                                if tg['steady_state_duration'] is not None:
                                    st.markdown(f"""
                                    <div class="threadgroup-property">
                                    <strong>Duration:</strong> {tg['steady_state_duration']}s
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.warning(f"⚠️ **Duration:** Could not extract")
                                
                                if tg['iterations'] is not None:
                                    st.markdown(f"""
                                    <div class="threadgroup-property">
                                    <strong>Iterations:</strong> {tg['iterations']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.warning(f"⚠️ **Iterations:** Could not extract")
                            
                            st.divider()
                
                # CSV Dataset Config Panel
                if csv_configs:
                    st.markdown("""
                    <div class="csv-config-info">
                    <strong>ℹ️ CSV DATASET CONFIGURATION FOUND</strong><br>
                    Your script uses CSV files for data. You can provide the file paths below, or leave them as-is if they're already correct.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"📊 CSV Dataset Configs ({len(csv_configs)} found)", expanded=True):
                        for idx, csv_config in enumerate(csv_configs):
                            st.subheader(f"CSV Config {idx + 1}: {csv_config['name']}")
                            
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.write("**Current Path:**")
                            with col2:
                                st.write(f"`{csv_config['filename']}`")
                            
                            # Input for custom path
                            custom_path = st.text_input(
                                f"Provide new path for '{csv_config['name']}' (leave empty to keep current):",
                                value=st.session_state.csv_file_paths.get(csv_config['name'], ''),
                                placeholder="e.g., /path/to/data.csv or C:\\data\\users.csv",
                                key=f"csv_path_{idx}"
                            )
                            
                            if custom_path:
                                st.session_state.csv_file_paths[csv_config['name']] = custom_path
                                st.success(f"✅ Path updated for '{csv_config['name']}'")
                            
                            st.info(f"""
                            **Variables:** {csv_config['variable_names']}
                            **Delimiter:** {csv_config['delimiter']}
                            **Recycle:** {'Yes' if csv_config['recycle'] else 'No'}
                            **Stop on EOF:** {'Yes' if csv_config['stop_on_eof'] else 'No'}
                            """)
                            
                            st.divider()
            else:
                st.error(f"❌ {validation_msg}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== SCENARIO DESIGN PANEL ====================
        st.markdown('<div class="panel"><div class="panel-title">🎯 Scenario Design Configuration</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="override-info">
        <strong>ℹ️ MULTIPLE THREADGROUP HANDLING</strong><br>
        Choose whether to apply scenario settings to ALL ThreadGroups or select specific ones.
        All extracted values (plain numbers or default values from properties) will be overridden.
        </div>
        """, unsafe_allow_html=True)
        
        apply_to_all = st.radio(
            "Apply scenario to:",
            options=["✅ All ThreadGroups", "🎯 Selected ThreadGroups Only"],
            horizontal=True,
            index=0,
            key="apply_to_all_radio"
        )
        
        st.session_state.scenario_config['apply_to_all'] = (apply_to_all == "✅ All ThreadGroups")
        
        if not st.session_state.scenario_config['apply_to_all'] and st.session_state.original_thread_groups:
            st.subheader("Select ThreadGroups to modify:")
            selected_tgs = []
            cols = st.columns(min(3, len(st.session_state.original_thread_groups)))
            
            for idx, tg in enumerate(st.session_state.original_thread_groups):
                with cols[idx % 3]:
                    if st.checkbox(f"{tg['name']} (Group {idx + 1})", value=True, key=f"tg_{idx}"):
                        selected_tgs.append(idx)
            
            st.session_state.scenario_config['selected_thread_groups'] = selected_tgs
        else:
            st.session_state.scenario_config['selected_thread_groups'] = list(range(len(st.session_state.original_thread_groups)))
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="scenario-config">
            <strong>Load Configuration</strong>
            </div>
            """, unsafe_allow_html=True)
            
            num_threads = st.number_input(
                "Number of Users/Threads",
                min_value=1,
                max_value=1000,
                value=st.session_state.scenario_config['num_threads'],
                step=1
            )
            st.session_state.scenario_config['num_threads'] = num_threads
            
            ramp_up_time = st.number_input(
                "Ramp-up Time (seconds)",
                min_value=0,
                max_value=3600,
                value=st.session_state.scenario_config['ramp_up_time'],
                step=5
            )
            st.session_state.scenario_config['ramp_up_time'] = ramp_up_time
        
        with col2:
            st.markdown("""
            <div class="scenario-config">
            <strong>Test Duration & Iterations</strong>
            </div>
            """, unsafe_allow_html=True)
            
            steady_state_duration = st.number_input(
                "Steady State Duration (seconds)",
                min_value=1,
                max_value=3600,
                value=st.session_state.scenario_config['steady_state_duration'],
                step=10
            )
            st.session_state.scenario_config['steady_state_duration'] = steady_state_duration
            
            iterations = st.number_input(
                "Iterations Per Thread",
                min_value=1,
                max_value=100,
                value=st.session_state.scenario_config['iterations'],
                step=1
            )
            st.session_state.scenario_config['iterations'] = iterations
        
        total_requests = num_threads * iterations
        total_time = ramp_up_time + steady_state_duration
        
        st.markdown("""
        <div class="scenario-config">
        <strong>Scenario Summary:</strong>
        </div>
        """, unsafe_allow_html=True)
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("Total Requests", total_requests)
        with metric_col2:
            st.metric("Total Time", f"{total_time}s")
        with metric_col3:
            st.metric("Requests/sec", f"{total_requests/total_time:.2f}" if total_time > 0 else "0")
        with metric_col4:
            st.metric("Total Duration", f"{int(total_time/60)}m {int(total_time%60)}s")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== RUN CONTROL PANEL ====================
        st.markdown('<div class="panel"><div class="panel-title">▶️ Run Control</div>', unsafe_allow_html=True)
        
        debug_col1, debug_col2, debug_col3 = st.columns(3)
        with debug_col1:
            st.metric("JMX Loaded", "✅" if st.session_state.jmx_content else "❌")
        with debug_col2:
            st.metric("JMeter Ready", "✅" if st.session_state.jmeter_found else "❌")
        with debug_col3:
            st.metric("Path Set", "✅" if st.session_state.jmeter_path else "❌")
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
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
                help="Execute JMeter with scenario parameters" if can_run_dry_run else "Please: 1) Upload JMX 2) Set JMeter path 3) Click Verify"
            ):
                with st.spinner(f"🔄 Executing JMeter ({len(st.session_state.scenario_config.get('selected_thread_groups', []))} ThreadGroup(s))...\n\n⏳ This may take several minutes."):
                    # Modify JMX with CSV paths (if provided)
                    modified_jmx = st.session_state.jmx_content
                    if st.session_state.csv_file_paths:
                        modified_jmx = modify_csv_dataset_paths(modified_jmx, st.session_state.csv_file_paths)
                    
                    # Modify JMX with scenario parameters
                    modified_jmx = modify_all_thread_groups(modified_jmx, st.session_state.scenario_config)
                    temp_jmx = save_temp_jmx(modified_jmx)
                    
                    # Determine working directory
                    working_dir = os.path.dirname(temp_jmx) if temp_jmx else None
                    
                    # Calculate timeout
                    estimated_duration = (ramp_up_time + steady_state_duration) * 1.5
                    timeout = max(1200, int(estimated_duration) + 300)
                    
                    success, output, results_file = run_jmeter_dry_run(
                        temp_jmx, 
                        st.session_state.jmeter_path, 
                        timeout=timeout,
                        working_dir=working_dir
                    )
                    
                    st.session_state.last_run_output = output
                    st.session_state.last_run_status = "success" if success else "failed"
                    st.session_state.dry_run_executed = True
                    
                    if success and results_file:
                        aggregate_report = parse_jtl_results(results_file)
                        if aggregate_report:
                            st.session_state.aggregate_report = aggregate_report
                            st.session_state.aggregate_report_generated = True
                    
                    history_entry = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'filename': st.session_state.jmx_filename,
                        'status': st.session_state.last_run_status,
                        'summary': f"Executed ({num_threads} users, {len(st.session_state.scenario_config.get('selected_thread_groups', []))} ThreadGroup(s))"
                    }
                    st.session_state.run_history.append(history_entry)
                    
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
        
        # ==================== AGGREGATE REPORT PANEL ====================
        if st.session_state.aggregate_report_generated and st.session_state.aggregate_report:
            st.markdown('<div class="panel"><div class="panel-title">📊 Aggregate Report</div>', unsafe_allow_html=True)
            
            report = st.session_state.aggregate_report
            
            if st.session_state.last_run_status == "success":
                st.markdown(
                    '<p class="status-success">✅ TEST EXECUTION SUCCESSFUL</p>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<p class="status-warning">⚠️ TEST COMPLETED WITH WARNINGS</p>',
                    unsafe_allow_html=True
                )
            
            st.caption(f"Report Generated: {report['timestamp']}")
            st.divider()
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            with metric_col1:
                st.metric("Total Samples", report['total_samples'])
            with metric_col2:
                st.metric("Success Rate", f"{report['success_rate']:.2f}%")
            with metric_col3:
                st.metric("Avg Response Time", f"{report['avg_response_time']:.0f}ms")
            with metric_col4:
                st.metric("Throughput", f"{report['throughput']:.2f}/s")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Success/Failure")
                st.metric("Successful Requests", report['success_count'])
                st.metric("Failed Requests", report['failure_count'])
            
            with col2:
                st.subheading("Response Time Statistics (ms)")
                st.metric("Min", report['min_response_time'])
                st.metric("Max", report['max_response_time'])
                st.metric("Median", report['median_response_time'])
            
            st.divider()
            
            st.subheader("Response Time Percentiles (ms)")
            perc_col1, perc_col2, perc_col3 = st.columns(3)
            
            with perc_col1:
                st.metric("90th Percentile (P90)", report['p90_response_time'])
            with perc_col2:
                st.metric("95th Percentile (P95)", report['p95_response_time'])
            with perc_col3:
                st.metric("99th Percentile (P99)", report['p99_response_time'])
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv_report = generate_aggregate_report_csv(report)
                st.download_button(
                    label="📥 Download Aggregate Report (CSV)",
                    data=csv_report,
                    file_name=f"jmeter_aggregate_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                json_report = json.dumps(report, indent=2, default=str)
                st.download_button(
                    label="📥 Download Report (JSON)",
                    data=json_report,
                    file_name=f"jmeter_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== RUN OUTPUT SUMMARY PANEL ====================
        if st.session_state.dry_run_executed:
            st.markdown('<div class="panel"><div class="panel-title">📝 Execution Details & Logs</div>', unsafe_allow_html=True)
            
            if st.session_state.execution_command:
                st.info(f"**Executed Command:**\n```\n{st.session_state.execution_command}\n```")
            
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
        
        st.subheader("🎯 CSV Dataset Configuration Guide")
        st.markdown("""
        ### **What is CSV Dataset Configuration?**
        CSV Dataset Config is a JMeter element that reads data from CSV files and uses it in your test.
        
        ### **Filepath Handling**
        
        **Two Ways to Specify Paths:**
        
        1. **Absolute Path** (Full path from root)
           - Windows: `C:\\Users\\testdata\\users.csv`
           - Linux/Mac: `/home/user/testdata/users.csv`
        
        2. **Relative Path** (Relative to where JMeter runs)
           - `data/users.csv`
           - `../data/users.csv`
        
        ### **The Problem**
        When you upload a JMX file to this dashboard, the CSV filepaths in the script are **fixed**.
        
        **Example:**
        - Original path: `C:\\myproject\\data\\users.csv`
        - Your machine path: `D:\\projects\\data\\users.csv`
        - **Result:** JMeter can't find the file ❌
        
        ### **The Solution**
        
        This dashboard now **detects CSV Dataset Configs** and allows you to:
        
        1. **View** the original CSV filepaths
        2. **Update** them with your actual filepaths
        3. **Override** them when running the test
        
        ### **How to Use**
        
        **Step 1: Upload JMX**
        - Dashboard detects CSV configs automatically
        
        **Step 2: Update CSV Paths**
        - Expand "CSV Dataset Configs" section
        - Enter your actual CSV filepath
        - Dashboard modifies the JMX before execution
        
        **Step 3: Run Test**
        - Click "Run Dry Run"
        - Modified JMX uses your CSV paths
        
        ### **Example Workflow**
        
        **Original CSV Config in JMX:**
        ```
        Filename: /path/to/data.csv
        Variables: username, password
        ```
        
        **Your Setup:**
        ```
        Filepath: C:\\TestData\\credentials.csv
        ```
        
        **After Update:**
        Dashboard modifies JMX:
        ```
        Filename: C:\\TestData\\credentials.csv
        Variables: username, password
        ```
        
        ### **Best Practices**
        
        ✅ **Use Absolute Paths** for clarity
        - Makes it clear where files are located
        - Less likely to break on different machines
        
        ✅ **Use Relative Paths** for portability
        - Works if data folder is relative to JMeter
        - Good for CI/CD pipelines
        
        ❌ **Avoid**
        - Hardcoded network paths (may not be accessible)
        - Paths with spaces (quote them: `"C:\\My Data\\file.csv"`)
        
        ### **Troubleshooting CSV Issues**
        
        **Error: "Cannot open file..."**
        - Check if file exists at the path
        - Verify file has read permissions
        - Try absolute path instead of relative
        
        **Error: "No such file or directory"**
        - Path separator wrong (use / for all systems in JMeter)
        - File moved or deleted
        - Working directory changed
        """)
        
        st.divider()
        
        st.subheader("🎯 Complete Workflow Guide")
        st.markdown("""
        ### **Step 1: Upload JMX Script**
        - Dashboard detects ThreadGroups and CSV configs
        - Shows original values extracted from script
        
        ### **Step 2: Configure CSV Paths (if needed)**
        - Update any CSV filepaths that don't match your setup
        - Leave blank if paths are correct
        
        ### **Step 3: Design Test Scenario**
        - Set threads, ramp-up, duration, iterations
        - Choose: Apply to ALL or SELECTED ThreadGroups
        
        ### **Step 4: Run Dry Run**
        - System modifies JMX with your settings
        - Updates CSV paths
        - Updates ThreadGroup parameters
        - Executes JMeter
        
        ### **Step 5: View Results**
        - Aggregate Report with metrics
        - Download as CSV or JSON
        
        ### **Step 6: AI Analysis (Optional)**
        - Get correlation suggestions
        - Get enhancement recommendations
        """)
        
        st.divider()
        
        st.subheader("🔧 Property Values in Scripts")
        st.markdown("""
        ### **What are Properties?**
        JMeter properties allow dynamic values:
        
        **Example:**
        - Plain: `10`
        - Property: `${__P(threads, 10)}`
        
        ### **How Dashboard Handles Them**
        
        **Plain Values:** `30` → Extracted directly
        **Property Values:** `${__P(hBBT_01_Threads, 30)}` → Extracts default `30`
        **Variables:** `${Threads}` → Cannot extract (depends on runtime)
        
        ### **Override Behavior**
        - All values (plain or property) are overridden with your scenario values
        - Original properties are replaced with plain values
        """)
    
    with tab3:  # SETTINGS
        st.header("⚙️ Settings & Preferences")
        
        st.subheader("Current Configuration")
        st.json({
            "jmeter_path": st.session_state.jmeter_path or "Not configured",
            "jmeter_status": "Ready" if st.session_state.jmeter_found else "Not verified",
            "threadgroups_detected": len(st.session_state.original_thread_groups),
            "csv_configs_detected": len(st.session_state.csv_configs_found),
            "scenario_config": st.session_state.scenario_config
        })
        
        st.divider()
        
        st.subheader("CSV Dataset Configs Detected")
        if st.session_state.csv_configs_found:
            for idx, csv_config in enumerate(st.session_state.csv_configs_found):
                st.write(f"""
                **Config {idx + 1}: {csv_config['name']}**
                - Current Path: `{csv_config['filename']}`
                - Variables: {csv_config['variable_names']}
                - Delimiter: `{csv_config['delimiter']}`
                """)
        else:
            st.info("No CSV Dataset Configs found in current script")
        
        st.divider()
        
        st.subheader("About This Application")
        st.markdown("""
        **AI-Powered JMeter Script Enhancer v3.0**
        
        Professional Streamlit dashboard for load testing script analysis.
        
        **v3.0 Features:**
        - ✅ CSV Dataset Config detection & path override
        - ✅ Multiple ThreadGroup handling
        - ✅ Property value extraction from JMeter properties
        - ✅ Apply to ALL or SELECT ThreadGroups
        - ✅ Standard JMeter non-GUI command execution
        - ✅ Scenario design with parameter override
        - ✅ Aggregate report generation
        - ✅ CSV/JSON export
        - ✅ AI correlation analysis
        - ✅ AI enhancement recommendations
        - ✅ Improved timeout handling
        
        **Built with:**
        - 🐍 Python & Streamlit
        - 🤖 OpenAI GPT-4 Turbo
        - 📊 JMeter
        - 📋 XML parsing for JMX analysis
        """)


# ============================================================================
# APP ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
