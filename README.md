# AI-Powered Smart JMeter Script Enhancer

This Streamlit dashboard helps performance engineers validate JMeter scripts by running a small sanity test and using AI to detect and suggest fixes for missing correlations.

Setup

1. Create a virtual environment (recommended)

   powershell: 
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install requirements

   pip install -r requirements.txt

3. Set environment variables in `.env`:

   OPENAI_API_KEY=sk-...
   JMETER_PATH=C:\\apache-jmeter-5.5\\bin\\jmeter.bat

4. Run Streamlit

   streamlit run app.py

Notes

- This is Phase 1: suggestions only. The tool does not modify JMX files automatically.
- Ensure JMeter is installed and JMETER_PATH points to the jmeter executable (bat on Windows).
