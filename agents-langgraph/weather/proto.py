import glob
import os

import requests
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)

url = "https://api-galileo-v2-dev.gcp-dev.galileo.ai/otel/v1/traces"
headers = {
    "Galileo-API-Key": "your-api-key-here",
    "Content-Type": "application/x-protobuf",
}


def parse_trace(body_bytes):
    reqtrace = ExportTraceServiceRequest()
    reqtrace.ParseFromString(body_bytes)
    return reqtrace


def main():
    glob_files = glob.glob("example_trace/*.bin")
    glob_files.sort(key=lambda x: os.path.getmtime(x))
    for file in glob_files:
        print(f"Processing file: {file}")
        with open(file, "rb") as f:
            body_bytes = f.read()
            reqtrace = parse_trace(body_bytes)
        response = requests.post(url, headers=headers, data=reqtrace.SerializeToString())
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")


if __name__ == "__main__":
    main()
