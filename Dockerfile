FROM python

# Disables user input prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qq update && \
    apt-get -qq install -y nodejs npm awscli && \
    wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin version=3.48.0 install_dir=~/calibre-bin isolated=y && \
    npm install -g gitbook-cli && \
    gitbook install && \
    rm -fr /tmp/* /var/tmp/* /var/lib/apt/lists/*
