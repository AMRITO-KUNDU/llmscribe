FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies with FastAPI and Uvicorn for production HTTP serving
RUN pip install --no-cache-dir .[all] && \
    pip install --no-cache-dir fastapi uvicorn[standard] fastmcp

ENV MCP_TRANSPORT=http
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["python", "-m", "llmscribe.mcp.server"]