FROM nikolaik/python-nodejs@sha256:275b15de7363e167fac2b19a0e5063ef7af025221afb230ea947e97151e4d68a

# Disables user input prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qq update && \
    apt-get -qq install -y calibre awscli && \
    npm install -g gitbook-cli && \
    gitbook install && \
    rm -fr /tmp/* /var/tmp/* /var/lib/apt/lists/*
