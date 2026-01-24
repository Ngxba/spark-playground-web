FROM python:3.12-slim

WORKDIR /app

# Install system dependencies, Java (for PySpark), PostgreSQL dev libraries, and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    openjdk-21-jre-headless \
    libpq-dev \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME for PySpark
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY app ./app

# Create virtual environment and install dependencies with uv
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# Expose port
EXPOSE 8000

# Run the application with uvicorn from venv
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
