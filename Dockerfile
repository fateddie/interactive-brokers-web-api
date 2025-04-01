FROM debian:bookworm-slim

# Update and upgrade packages
RUN apt-get update && apt-get upgrade -y

# Install JDK and any needed utilities
RUN apt-get install -y openjdk-17-jre-headless \
                       unzip curl procps vim net-tools \
                       python3-full python3-pip python3-venv \
                       python3-flask python3-requests \
                       python3-dotenv python3-werkzeug

# We will put everything in the /app directory
WORKDIR /app

# Download and unzip client portal gateway
RUN mkdir gateway && cd gateway && \
    curl -O https://download2.interactivebrokers.com/portal/clientportal.gw.zip && \
    unzip clientportal.gw.zip && rm clientportal.gw.zip

# Copy our config so that the gateway will use it
COPY conf.yaml gateway/root/conf.yaml
COPY start.sh /app

# Copy application files
ADD webapp webapp
ADD scripts scripts
ADD graph graph

# Install additional Python packages
RUN pip3 install --break-system-packages ib_insync==0.9.86 openai>=1.0.0

# Generate and install SSL certificates
RUN keytool -genkey -keyalg RSA -alias selfsigned -keystore cacert.jks -storepass abc123 -validity 730 -keysize 2048 -dname CN=localhost
RUN keytool -importkeystore -srckeystore cacert.jks -destkeystore cacert.p12 -srcstoretype jks -deststoretype pkcs12 -srcstorepass abc123 -deststorepass abc123
RUN openssl pkcs12 -in cacert.p12 -out cacert.pem -passin pass:abc123 -passout pass:abc123
RUN cp cacert.pem gateway/root/cacert.pem
RUN cp cacert.jks gateway/root/cacert.jks
RUN cp cacert.pem webapp/cacert.pem

# Set permissions for graph directory
RUN chown -R root:root /app/graph && chmod -R 644 /app/graph/*

# Expose the port so we can connect
EXPOSE 5055 5056

# Run the gateway
CMD sh ./start.sh
