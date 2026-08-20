# Spring Boot Gateway — docker-compose target.
#
# Multi-stage on purpose. This used to be `COPY target/*.jar app.jar`, which
# assumed you had already run `mvn package` on the host. `target/` is gitignored,
# so on a fresh clone that COPY matched nothing and `docker compose up --build`
# failed outright. Building the jar inside the image makes compose self-contained
# and removes Maven from the list of things you need installed locally.

# --- Stage 1: build the jar ---
FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /build

# POM first, so dependency resolution is cached across source-only changes.
COPY pom.xml .
RUN mvn -B -q dependency:go-offline

COPY src ./src
RUN mvn -B -q clean package -DskipTests

# --- Stage 2: slim runtime ---
FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=build /build/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
