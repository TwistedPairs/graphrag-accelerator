FROM ubuntu:20.04

# Set environment variable to non-interactive to prevent prompts
ENV DEBIAN_FRONTEND=noninteractive

# Ensure apt is up to date and install basic dependencies and ICU libraries
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    jq \
    git \
    sudo \
    libicu66

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install yq
RUN curl -LO https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 && \
    mv yq_linux_amd64 /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

# Reset the noninteractive frontend
ENV DEBIAN_FRONTEND=

# Verify installations
RUN az version
RUN helm version
RUN jq --version
RUN yq --version
RUN kubectl version --client
RUN curl --version
RUN sed --version