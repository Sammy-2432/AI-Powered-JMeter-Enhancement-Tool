import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger("jmeter_runner")
load_dotenv()

JMETER_PATH = os.getenv("JMETER_PATH") or "jmeter"

class JMeterRunner:
    def __init__(self, jmeter_path: str = JMETER_PATH):
        self.jmeter_path = jmeter_path

    def run_sanity(self, jmx_path: Path, jtl_path: Path):
        """
        Run JMeter in non-GUI mode for a small sanity run (1 thread, 1 loop).
        Ensures response data and headers are saved.
        """
        if not Path(jmx_path).exists():
            raise FileNotFoundError(f"JMX file not found: {jmx_path}")

        jtl_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.jmeter_path),
            "-n",
            "-t",
            str(jmx_path),
            "-l",
            str(jtl_path),
            "-Jthreads=1",
            "-Jloops=1",
            "-j",
            str(jtl_path.with_suffix('.log')),
            # Ensure saving response data and headers if JMeter properties allow
            "-Jjmeter.save.saveservice.output_format=xml",
            "-Jjmeter.save.saveservice.response_data=true",
            "-Jjmeter.save.saveservice.samplerData=true",
            "-Jjmeter.save.saveservice.requestHeaders=true",
            "-Jjmeter.save.saveservice.responseHeaders=true",
        ]

        logger.info("Running JMeter: %s", " ".join(cmd))

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            logger.error("JMeter failed: %s", proc.stderr)
            raise RuntimeError(f"JMeter execution failed: {proc.stderr}")

        logger.info("JMeter finished, results at %s", jtl_path)
        return jtl_path
