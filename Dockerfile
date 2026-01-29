# BHP Truck API - Configurable Individual Truck Instance
# Supports both original API and configurable sample truck mode
#
# Build: docker build -t truck-api .

FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY src/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/

# Set Python path for imports
ENV PYTHONPATH=/app

# Truck configuration (override at deployment for sample trucks)
ENV TRUCK_ID=TRK-001
ENV TRUCK_NUMBER=1
ENV FLEET_ID=BHP-WA-001
ENV FIRMWARE_VERSION=2.4.1-build.2847
ENV HARDWARE_VERSION=1.2.0

# Select which app to run: "api" for original, "sample" for configurable truck
ENV APP_MODE=sample

EXPOSE 8080

# Run the appropriate application based on APP_MODE
CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"sample\" ]; then python -m uvicorn src.sample_trucks.app:app --host 0.0.0.0 --port 8080; else python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8080; fi"]
