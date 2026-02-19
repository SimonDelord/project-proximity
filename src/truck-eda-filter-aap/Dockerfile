# Build stage
FROM registry.access.redhat.com/ubi8/openjdk-17:1.18 AS builder

USER root
WORKDIR /build

# Copy Maven files
COPY pom.xml .
COPY src ./src

# Build the application
RUN mvn package -DskipTests

# Runtime stage
FROM registry.access.redhat.com/ubi8/openjdk-17-runtime:1.18

USER root
WORKDIR /app

# Copy the built artifact
COPY --from=builder /build/target/quarkus-app/lib/ /app/lib/
COPY --from=builder /build/target/quarkus-app/*.jar /app/
COPY --from=builder /build/target/quarkus-app/app/ /app/app/
COPY --from=builder /build/target/quarkus-app/quarkus/ /app/quarkus/

RUN chown -R 1001:0 /app && chmod -R g+rwX /app

USER 1001

ENV JAVA_OPTS="-Dquarkus.http.host=0.0.0.0"

EXPOSE 8080

CMD ["java", "-jar", "/app/quarkus-run.jar"]
