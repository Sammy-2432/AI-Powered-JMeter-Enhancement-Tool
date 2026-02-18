import streamlit as st
from pathlib import Path
from utils.logger import setup_logger
from core.jmeter_runner import JMeterRunner
from core.jtl_parser import JTLParser
from core.failure_detector import FailureDetector
from services.suggestion_service import SuggestionService
from utils.file_handler import save_uploaded_file
from datetime import datetime
import requests

logger = setup_logger("ai_jmeter_enhancer")

st.set_page_config(page_title="AI-Powered Smart JMeter Script Enhancer", layout="wide", page_icon="🧠")

st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%) !important;
}
.header-gradient {
    background: linear-gradient(90deg, #4f8ef7 0%, #21cfa7 100%);
    border-radius: 18px;
    padding: 1.5em 1em 1.5em 1em;
    box-shadow: 0 4px 24px 0 rgba(79, 142, 247, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5em;
}
.header-gradient h1 {
    color: #fff;
    font-size: 2.6em;
    font-weight: 800;
    margin: 0 0 0 0.5em;
    letter-spacing: 1px;
    text-shadow: 0 2px 8px #0002;
}
.header-gradient .header-icon {
    font-size: 2.5em;
    margin-right: 0.5em;
    filter: drop-shadow(0 2px 6px #0001);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='header-gradient'>
    <span class='header-icon'>🤖</span>
    <h1>AI-Powered Smart JMeter Script Enhancer</h1>
</div>
""", unsafe_allow_html=True)

st.caption("Validate, analyze, and enhance your JMeter scripts with AI-driven insights.")

upload_col, run_col = st.columns([3,1])

with upload_col:
    uploaded_file = st.file_uploader("Upload JMeter .jmx file", type=["jmx"], help="Upload your JMeter test plan (.jmx)")

with run_col:
    st.markdown("<div style='text-align:center; font-size:2em;'>🚦</div>", unsafe_allow_html=True)
    run_button = st.button("Run Sanity Test", use_container_width=True)

if uploaded_file:
    uploads_dir = Path("temp/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    jmx_path = save_uploaded_file(uploaded_file, uploads_dir)
    st.success(f"Saved to {jmx_path}")
else:
    jmx_path = None

if run_button:
    if not jmx_path:
        st.error("Please upload a .jmx file first.")
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        results_dir = Path("temp/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        jtl_path = results_dir / f"result_{timestamp}.jtl"

        with st.spinner("🧪 Running JMeter sanity test..."):
            runner = JMeterRunner()
            try:
                runner.run_sanity(jmx_path, jtl_path)
                st.success("Sanity run completed, parsing results...")
            except Exception as e:
                logger.exception("JMeter run failed")
                st.error(f"JMeter execution failed: {e}")
                st.toast("JMeter run failed!", icon="❌")
                st.stop()

        parser = JTLParser()
        df = parser.parse_jtl(jtl_path)

        detector = FailureDetector()
        failures = detector.detect_failures(df)

        # Summary
        total = len(df)
        failed = len(failures)
        fail_pct = (failed / total * 100) if total > 0 else 0

        st.markdown("---")
        st.header("Execution Summary")
        summary_cols = st.columns(3)
        summary_cols[0].metric("Total Samples", total, delta=None)
        summary_cols[1].metric("Total Failures", failed, delta=None)
        summary_cols[2].metric("Failure %", f"{fail_pct:.2f}%", delta=None)

        st.markdown("---")
        st.header("Failed Samplers")
        suggestion_service = SuggestionService()

        for idx, failure in enumerate(failures):
            with st.expander(f"Failure {idx+1}: {failure.sampler_name} - {failure.label}", expanded=False):
                st.markdown(f"<div style='font-size:2em;'>❌</div>", unsafe_allow_html=True)
                st.subheader("Request")
                st.code(failure.request_data or "<no request data>", language="http")
                st.subheader("Response")
                st.code(failure.response_data or "<no response data>", language="json")
                st.subheader("Previous Sampler Candidates")
                st.json(failure.candidate_dynamic_fields or {})

                st.info("Sending to AI for suggestion...")
                suggestion = suggestion_service.analyze_failure(failure)

                st.subheader("AI Suggestion")
                if suggestion:
                    st.json(suggestion.dict())
                    st.success(f"Confidence Score: {suggestion.confidence_score}")
                else:
                    st.warning("No suggestion available")

        if failed == 0:
            st.balloons()
            st.toast("All tests passed!", icon="✅")
        else:
            st.toast(f"{failed} failures detected!", icon="❌")
