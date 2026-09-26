FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependencies definitions
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --no-dev --frozen

# Copy the rest of the application
COPY . .

# Set the Python path to include the src directory
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Command to run the application using faststream
CMD ["faststream", "run", "main:app"]
