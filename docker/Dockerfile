FROM ubuntu:22.04

# disable interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# install system tools and development packages
RUN apt-get update && apt-get install -y \
    wget \
    bash \
    vim \
    git \
    ffmpeg \
    tmux \
    python3 \
    python3-pip \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

# download and install gotty
RUN wget https://github.com/sorenisanerd/gotty/releases/download/v1.5.0/gotty_v1.5.0_linux_amd64.tar.gz && \
    tar -xzf gotty_v1.5.0_linux_amd64.tar.gz && \
    mv gotty /usr/local/bin/ && \
    rm gotty_v1.5.0_linux_amd64.tar.gz

# install Cha from GitHub
RUN git clone https://github.com/MehmetMHY/cha.git && \
    cd cha && \
    pip3 install -e .

# set up a clean and simple vim configuration
RUN echo "set number\nset mouse=a\nsyntax on\nset autoindent\nset tabstop=4\nset shiftwidth=4\nset expandtab" > /root/.vimrc

# set up a basic tmux configuration
RUN echo "set -g mouse on\nset -g history-limit 30000\nset -g status-bg black\nset -g status-fg white" > /root/.tmux.conf

# create startup script to verify API keys
RUN echo '#!/bin/bash\n\
if [ -z "$OPENAI_API_KEY" ] || [ -z "$BRAVE_API_KEY" ]; then\n\
    echo "Error: Required environment variables not set!"\n\
    echo "Please run the container with:"\n\
    echo "docker run -it -p 8080:8080 -e OPENAI_API_KEY=your_key -e BRAVE_API_KEY=your_key gotty-term"\n\
    exit 1\n\
fi\n\
exec "$@"' > /start.sh && \
    chmod +x /start.sh

# expose GoTTY's default port
EXPOSE 8080

# use the startup script as entrypoint
ENTRYPOINT ["/start.sh"]
CMD ["gotty", "--permit-write", "--reconnect", "/bin/bash"]

