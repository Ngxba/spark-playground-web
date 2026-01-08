FROM eclipse-temurin:11-jre-jammy

# Install required packages
RUN apt-get update && \
    apt-get install -y wget curl procps && \
    rm -rf /var/lib/apt/lists/*

# Download and install Spark
ENV SPARK_VERSION=3.5.0
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark

RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    tar -xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} ${SPARK_HOME} && \
    rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz

# Create directories for event logs and history
RUN mkdir -p /tmp/spark-events && \
    chmod -R 777 /tmp/spark-events

# Copy spark configuration
COPY spark-defaults.conf ${SPARK_HOME}/conf/

# Set environment variables
ENV PATH=$PATH:${SPARK_HOME}/bin:${SPARK_HOME}/sbin

WORKDIR ${SPARK_HOME}

# Expose Spark History Server port
EXPOSE 18080

# Start Spark History Server
CMD ["spark-class", "org.apache.spark.deploy.history.HistoryServer"]
