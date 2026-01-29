# BHP Sample Truck API - Configurable Individual Truck Instance
# Each deployment can configure unique truck parameters via env vars
#
# Build from project root: docker build -f src/sample-trucks/Dockerfile -t truck-api .

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi==0.109.0 uvicorn[standard]==0.27.0

# Copy the entire src directory for proper imports
COPY src/models /app/src/models
COPY src/sample-trucks/app.py /app/src/sample-trucks/app.py

# Create __init__.py files for proper Python imports
RUN touch /app/src/__init__.py
RUN touch /app/src/models/__init__.py
RUN touch /app/src/sample-trucks/__init__.py

# Environment variables (override at deployment)
ENV TRUCK_ID=TRK-001
ENV TRUCK_NUMBER=1
ENV FLEET_ID=BHP-WA-001
ENV FIRMWARE_VERSION=2.4.1-build.2847
ENV HARDWARE_VERSION=1.2.0
ENV PORT=8080

EXPOSE 8080

# Run the application
CMD ["python", "-m", "uvicorn", "src.sample-trucks.app:app", "--host", "0.0.0.0", "--port", "8080"]
