#!/usr/bin/env bash
set -e

SPARK_VERSION=3.5.0
HADOOP_VERSION=3.3.4
AWS_SDK_VERSION=1.12.540

JAR_DIR="$(pwd)/pyspark_jars"
mkdir -p "$JAR_DIR"

cd "$JAR_DIR"

echo "Downloading Spark/Hadoop AWS jars..."

curl -LO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar
curl -LO https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar

echo "Downloaded jars:"
ls -lh
