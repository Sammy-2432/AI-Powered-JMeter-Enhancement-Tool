from datetime import datetime


def utc_timestamp():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
