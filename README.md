# Galileo Agents

AI agent examples instrumented with Traceloop (OpenLLMetry), exporting traces to Galileo.

## Agents

| Framework | Agent | Span Types |
|-----------|-------|------------|
| LangGraph | Weather | `agent`, `workflow`, `llm`, `tool` |
| LangGraph | Calculator | `agent`, `workflow`, `llm`, `tool` |
| LangGraph | RAG | `agent`, `workflow`, `llm`, `tool`, `retriever` |
| CrewAI | Content | `agent`, `llm`, `tool` |
| CrewAI | Research | `agent`, `llm`, `tool`, `retriever` |

## Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Configure environment
cp env.example .env
# Edit .env with your API keys
```

## Run

```bash
# LangGraph
uv run agents-langgraph/weather/agent.py
uv run agents-langgraph/calculator/agent.py
uv run agents-langgraph/rag/agent.py

# CrewAI
uv run agents-crewai/content/crew.py
uv run agents-crewai/research/crew.py

# Custom queries
uv run agents-langgraph/weather/agent.py "What's the forecast for NYC?"
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GALILEO_API_KEY` | Galileo API key |
| `TRACELOOP_BASE_URL` | Traceloop endpoint (default: https://api.galileo.ai/otel) |
| `TRACELOOP_HEADERS` | Traceloop headers: `Galileo-API-Key=${GALILEO_API_KEY}` |
| `OPENAI_API_KEY` | OpenAI API key |

## Telemetry

All agents use Traceloop for automatic instrumentation. Traceloop reads `TRACELOOP_BASE_URL` and `TRACELOOP_HEADERS` from environment variables and automatically appends `/v1/traces` to the base URL.

Project and logstream are specified via resource attributes (hardcoded in each agent):

```python
from traceloop.sdk import Traceloop

Traceloop.init(
    app_name="weather-agent",
    resource_attributes={
        "galileo.project.name": "galileo-agents",
        "galileo.logstream.name": "weather-agent",
    },
)
```

Traceloop automatically instruments LangGraph workflows and CrewAI crews, generating spans for agents, tools, LLM calls, and retrievers.

## Direct POST Calls to Galileo OTLP Endpoint

You can make direct POST calls to the Galileo OTLP endpoint to send OTLP packets. This is useful for custom integrations or when you need to send pre-generated OTLP data.

### Endpoint

```
POST https://api.galileo.ai/otel/v1/traces
```

### Headers

The following headers are required:

| Header | Description |
|--------|-------------|
| `Galileo-API-Key` | Your Galileo API key |
| `project` | Project name |
| `logstream` | Logstream name |
| `Content-Type` | Must be `application/x-protobuf` |

### Request Body

The request body should contain OTLP packets in protobuf format (binary). The payload should be an `ExportTraceServiceRequest` message as defined in the OpenTelemetry Protocol specification.

### Example using cURL

```bash
curl -X POST https://api.galileo.ai/otel/v1/traces \
  -H "Galileo-API-Key: your-api-key" \
  -H "project: your-project-name" \
  -H "logstream: your-logstream-name" \
  -H "Content-Type: application/x-protobuf" \
  --data-binary @otlp_packet.pb
```

### Example using Python

```python
import requests

url = "https://api.galileo.ai/otel/v1/traces"
headers = {
    "Galileo-API-Key": "your-api-key",
    "project": "your-project-name",
    "logstream": "your-logstream-name",
    "Content-Type": "application/x-protobuf",
}

# Read OTLP protobuf data from file
with open("otlp_packet.pb", "rb") as f:
    payload = f.read()

response = requests.post(url, headers=headers, data=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

### HTTP Responses

The OTLP endpoint returns the following HTTP status codes:

#### Success Responses

**200 OK**
- The request was successfully processed. The response body contains an `ExportTraceServiceResponse` in JSON format.
- Example response:
  ```json
  {}
  ```
- If some spans were rejected, the response includes partial success information:
  ```json
  {
    "partialSuccess": {
      "rejectedSpans": 5,
      "errorMessage": "Group 0: Run not found for logstream ..."
    }
  }
  ```

#### Error Responses

**401 Unauthorized**
- The API key is missing or invalid.
- Response body:
  ```json
  {
    "detail": "API Key is missing"
  }
  ```
  or
  ```json
  {
    "detail": "Invalid API Key"
  }
  ```

**404 Not Found**
- The specified project was not found and could not be created.
- Response body:
  ```json
  {
    "detail": "Project not found."
  }
  ```

**415 Unsupported Media Type**
- The `Content-Type` header is not `application/x-protobuf`.
- Response body:
  ```json
  {
    "detail": "<content-type> is not supported, content_type needs to be: 'application/x-protobuf'"
  }
  ```

**422 Unprocessable Entity**
- The request could not be processed. Common reasons:
  - No spans found in the request
  - Trace processing failed
  - Log stream ID is required but not provided
- Response body examples:
  ```json
  {
    "detail": "No spans found in request."
  }
  ```
  ```json
  {
    "detail": "log_stream_id is required."
  }
  ```
  ```json
  {
    "detail": "Trace processing failed: <error message>"
  }
  ```

### Response Format

All responses are returned as JSON. Success responses follow the OpenTelemetry Protocol `ExportTraceServiceResponse` format, which may include:
- `partialSuccess.rejectedSpans`: Number of spans that were rejected
- `partialSuccess.errorMessage`: Error messages describing why spans were rejected

Even when the HTTP status is 200, you should check for `partialSuccess` in the response to determine if all spans were successfully processed.
