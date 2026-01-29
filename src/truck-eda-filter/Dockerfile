# BHP Truck EDA Filter - Camel (Quarkus)
# Filters truck telemetry and publishes to EDA topic

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

# Environment variables
ENV KAFKA_BROKERS=172.30.68.114:9092
ENV KAFKA_SOURCE_TOPIC=truck-telemetry-camel
ENV KAFKA_TARGET_TOPIC=eda-topic
ENV KAFKA_CONSUMER_GROUP=truck-eda-filter-group

# Run the application
CMD ["java", "-Dkafka.brokers=${KAFKA_BROKERS}", "-Dkafka.source.topic=${KAFKA_SOURCE_TOPIC}", "-Dkafka.target.topic=${KAFKA_TARGET_TOPIC}", "-Dkafka.consumer.group=${KAFKA_CONSUMER_GROUP}", "-jar", "quarkus-run.jar"]

