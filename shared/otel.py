import argparse
import glob

import requests
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)


def parse_trace(body_bytes):
    reqtrace = ExportTraceServiceRequest()
    reqtrace.ParseFromString(body_bytes)
    return reqtrace


def main():
    parser = argparse.ArgumentParser(description="Send OTLP traces to Galileo API")
    parser.add_argument(
        "--api-key",
        required=True,
        help="Galileo API key",
    )
    parser.add_argument(
        "--project",
        help="Project name (at least one of --project or --projectid required)",
    )
    parser.add_argument(
        "--projectid",
        help="Project ID (at least one of --project or --projectid required)",
    )
    parser.add_argument(
        "--logstream",
        help="Log stream name (at least one of --logstream or --logstreamid required)",
    )
    parser.add_argument(
        "--logstreamid",
        help="Log stream ID (at least one of --logstream or --logstreamid required)",
    )
    parser.add_argument(
        "--url",
        default="https://api.galileo.ai/otel/v1/traces",
        help="API endpoint URL (default: https://api.galileo.ai/otel/v1/traces)",
    )
    parser.add_argument(
        "--directory",
        default="agents-langgraph/weather/otlp_trace",
        help="Directory containing .bin trace files (default: agents-langgraph/weather/otlp_trace)",
    )

    args = parser.parse_args()

    # Validate that at least one of project or projectid is provided
    if not args.project and not args.projectid:
        parser.error("At least one of --project or --projectid must be provided")

    # Validate that at least one of logstream or logstreamid is provided
    if not args.logstream and not args.logstreamid:
        parser.error("At least one of --logstream or --logstreamid must be provided")

    # Build headers
    headers = {
        "Galileo-API-Key": args.api_key,
        "Content-Type": "application/x-protobuf",
    }

    # Add project or projectid to headers (prefer project over projectid if both provided)
    if args.project:
        headers["project"] = args.project
    elif args.projectid:
        headers["projectid"] = args.projectid

    # Add logstream or logstreamid to headers (prefer logstream over logstreamid if both provided)
    if args.logstream:
        headers["logstream"] = args.logstream
    elif args.logstreamid:
        headers["logstreamid"] = args.logstreamid

    glob_files = glob.glob(f"{args.directory}/*.bin")
    glob_files.sort()
    for file in glob_files:
        print(f"Processing file: {file}")
        with open(file, "rb") as f:
            body_bytes = f.read()
            reqtrace = parse_trace(body_bytes)
        response = requests.post(args.url, headers=headers, data=reqtrace.SerializeToString())
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")


if __name__ == "__main__":
    main()
