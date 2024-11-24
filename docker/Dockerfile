FROM debian:12-slim

# disable interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# install dependencies and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    bash \
    vim-tiny \
    git \
    ffmpeg \
    tmux \
    curl \
    python3 \
    python3-venv \
    python3-pip \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# download and install gotty
RUN wget https://github.com/sorenisanerd/gotty/releases/download/v1.5.0/gotty_v1.5.0_linux_amd64.tar.gz && \
    tar -xzf gotty_v1.5.0_linux_amd64.tar.gz && \
    mv gotty /usr/local/bin/ && \
    rm gotty_v1.5.0_linux_amd64.tar.gz

# add build argument for cache busting
ARG CACHE_DATE=unknown

# create and activate virtual environment, then install Cha
RUN python3 -m venv /opt/venv && \
    echo "Cache bust: $CACHE_DATE" && \
    rm -rf cha && \
    git clone --depth 1 https://github.com/MehmetMHY/cha.git && \
    . /opt/venv/bin/activate && \
    cd cha && \
    pip install -e . && \
    rm -rf .git && \
    deactivate

# add virtual environment to PATH
ENV PATH="/opt/venv/bin:$PATH"

# set up vim configuration
RUN echo "set number\nset mouse=a\nsyntax on\nset autoindent\nset tabstop=4\nset shiftwidth=4\nset expandtab" > /root/.vimrc

# set up tmux configuration
RUN echo "set -g mouse on\nset -g history-limit 30000\nset -g status-bg black\nset -g status-fg white" > /root/.tmux.conf

# create a customize, simple, bash prompt
RUN echo 'PS1="\w# "' >> /root/.bashrc

# create startup script
RUN echo '#!/bin/bash\n\
if [ -z "$OPENAI_API_KEY" ]; then\n\
    echo "Error: Required environment variables not set!"\n\
    echo "Please run the container with:"\n\
    echo "docker run -it -p 8080:8080 -e OPENAI_API_KEY=your_key gotty-term"\n\
    exit 1\n\
fi\n\
# Create a custom shell startup script\n\
echo "#!/bin/bash" > /custom_shell.sh\n\
echo "source /opt/venv/bin/activate" >> /custom_shell.sh\n\
echo "cha -h" >> /custom_shell.sh\n\
echo "echo" >> /custom_shell.sh\n\
echo "cha -pt" >> /custom_shell.sh\n\
echo "exec bash" >> /custom_shell.sh\n\
chmod +x /custom_shell.sh\n\
exec "$@"' > /start.sh && \
    chmod +x /start.sh

WORKDIR /root

# expose GoTTY's default port
EXPOSE 8080

# use the startup script as entrypoint
ENTRYPOINT ["/start.sh"]
CMD ["gotty", "--permit-write", "--reconnect", "--title-format", "cha", "/custom_shell.sh"]

