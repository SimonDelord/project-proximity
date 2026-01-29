# BHP Truck Poller - Camel (Quarkus) - Multi-Truck Support
# Polls multiple truck API endpoints and publishes to Kafka

# Stage 1: Build
FROM maven:3.9-eclipse-temurin-17 AS build

WORKDIR /app

# Copy pom.xml first for dependency caching
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source code and build
COPY src ./src
RUN mvn package -DskipTests -B

# Stage 2: Runtime
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy the built artifact
COPY --from=build /app/target/quarkus-app/lib/ ./lib/
COPY --from=build /app/target/quarkus-app/*.jar ./
COPY --from=build /app/target/quarkus-app/app/ ./app/
COPY --from=build /app/target/quarkus-app/quarkus/ ./quarkus/

# Environment variables - can be overridden at runtime
# TRUCK_API_URLS: Comma-separated list of truck API endpoints
ENV TRUCK_API_URLS=https://project-proximity-git-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
ENV POLL_INTERVAL_SECONDS=5
ENV KAFKA_TOPIC=truck-telemetry-camel
ENV KAFKA_BROKERS=172.30.68.114:9092

# Run the application
CMD ["java", "-Dtruck.api.urls=${TRUCK_API_URLS}", "-Dpoll.interval.seconds=${POLL_INTERVAL_SECONDS}", "-Dkafka.topic=${KAFKA_TOPIC}", "-Dkafka.brokers=${KAFKA_BROKERS}", "-jar", "quarkus-run.jar"]
