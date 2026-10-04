FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies
RUN pip install --no-cache-dir .[all]

# MCP will use streamable-http transport for HTTP mode
ENV MCP_TRANSPORT=http
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["python", "-m", "llmscribe.mcp.server"]