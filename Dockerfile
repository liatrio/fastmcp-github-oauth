FROM python:3.11-slim

# Install uv and curl for health checks
RUN pip install uv && \
    apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /app

# Create virtual environment
RUN uv venv

# Copy the wheel from GoReleaser build context (available at root level)
COPY *.whl ./

# Install the wheel and clean up
RUN uv pip install --no-cache-dir *.whl && rm *.whl

# Expose port
EXPOSE 8000

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "fastmcp_github_oauth_example.server"]