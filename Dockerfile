FROM jenkins/jenkins:latest

USER root

RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages behave


COPY certificado.cer /tmp/certificado.cer

RUN keytool -import -alias minicorp -file /tmp/certificado.cer \
    -keystore "$JAVA_HOME/lib/security/cacerts" \
    -storepass changeit \
    -noprompt || true && \
    rm /tmp/certificado.cer

RUN if [ -n "$http_proxy" ]; then \
    echo "http.proxyHost=$(echo $http_proxy | cut -d'/' -f3 | cut -d':' -f1)" >> /usr/local/openjdk-17/conf/net.properties; \
    echo "http.proxyPort=$(echo $http_proxy | cut -d':' -f3)" >> /usr/local/openjdk-17/conf/net.properties; \
    fi

ENV JAVA_OPTS="-Dcom.sun.jndi.ldap.connect.pool=false"

COPY jenkins-plugins.txt /usr/share/jenkins/jenkins-plugins.txt

USER jenkins

RUN jenkins-plugin-cli -f /usr/share/jenkins/jenkins-plugins.txt

