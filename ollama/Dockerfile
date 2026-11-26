FROM ollama/ollama:0.5.4

ENV OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    OLLAMA_KEEP_ALIVE=5m \
    HOME=/home/ollama

RUN groupadd --system --gid 1000 ollama && useradd --system --uid 1000 --gid ollama --home-dir /home/ollama --create-home ollama \
    && mkdir -p /home/ollama/.ollama \
    && chown -R ollama:ollama /home/ollama

COPY entrypoint.sh /usr/local/bin/ollama-entrypoint.sh
RUN chmod +x /usr/local/bin/ollama-entrypoint.sh

USER ollama
WORKDIR /home/ollama

EXPOSE 11434

ENTRYPOINT ["/usr/local/bin/ollama-entrypoint.sh"]
