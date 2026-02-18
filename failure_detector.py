from typing import List
import pandas as pd
from models.failure_model import Failure
from utils.logger import setup_logger

logger = setup_logger("failure_detector")

class FailureDetector:
    def detect_failures(self, df: pd.DataFrame) -> List[Failure]:
        """
        Identify failed samples from JTL DataFrame.
        For each failed sample, find immediate previous sampler in same thread and capture its response.
        """
        failures: List[Failure] = []
        if df is None or df.empty:
            return failures

        df = df.reset_index(drop=True)
        # Ensure columns
        for col in ['threadName','success','responseData','label','samplerData','requestHeaders','responseHeaders']:
            if col not in df.columns:
                df[col] = None

        grouped = df.groupby('threadName')
        for thread, group in grouped:
            group = group.reset_index()
            for i, row in group.iterrows():
                success = str(row.get('success')).lower() in ['true','1','y','yes']
                if not success:
                    # failure row
                    prev_resp = None
                    prev_request = None
                    if i > 0:
                        prev = group.loc[i-1]
                        prev_resp = prev.get('responseData')
                        prev_request = prev.get('samplerData')

                    failure = Failure(
                        thread_name=thread,
                        sampler_name=row.get('label'),
                        label=row.get('label'),
                        request_data=row.get('samplerData') or row.get('requestHeaders'),
                        response_data=row.get('responseData'),
                        previous_response=prev_resp,
                        previous_request=prev_request
                    )
                    failures.append(failure)
        logger.info("Detected %d failures", len(failures))
        return failures
