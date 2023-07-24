FROM containerization-tool-base-image:latest


# Set environment variables for Java installation
ENV JAVA_VERSION=17
ENV JAVA_HOME=/usr/lib/jvm/java-${JAVA_VERSION}-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Install necessary packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openjdk-${JAVA_VERSION}-jdk \
    && rm -rf /var/lib/apt/lists/*

COPY ./entrypoint.bin /usr/local/bin/entrypoint.jar

CMD ["java", "-jar", "/usr/local/bin/entrypoint.jar"]

