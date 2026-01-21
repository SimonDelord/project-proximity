# BHP Truck Poller - Camel (Quarkus)
# Multi-stage build for optimized container image

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

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Copy the built artifact
COPY --from=build /app/target/quarkus-app/lib/ ./lib/
COPY --from=build /app/target/quarkus-app/*.jar ./
COPY --from=build /app/target/quarkus-app/app/ ./app/
COPY --from=build /app/target/quarkus-app/quarkus/ ./quarkus/

# Environment variables (override at runtime)
ENV TRUCK_API_URL=https://project-proximity-git-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample
ENV POLL_INTERVAL_SECONDS=10
ENV KAFKA_TOPIC=truck-telemetry
ENV KAFKA_BROKERS=172.30.68.114:9092

# Quarkus configuration overrides
ENV QUARKUS_LOG_LEVEL=INFO
ENV _JAVA_OPTIONS="-Dtruck.api.url=${TRUCK_API_URL} -Dpoll.interval.seconds=${POLL_INTERVAL_SECONDS} -Dkafka.topic=${KAFKA_TOPIC} -Dcamel.component.kafka.brokers=${KAFKA_BROKERS}"

EXPOSE 8080

# Run the application
CMD ["java", "-jar", "quarkus-run.jar"]

