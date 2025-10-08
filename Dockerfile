FROM python:3.10-slim-bullseye

# Variáveis de ambiente
ENV DJANGO_SETTINGS_MODULE=dashboard.settings.local
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBUG=true
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Copia arquivos de requisitos primeiro (melhor cache)
COPY ./src/requirements.txt .

# Instala dependências do sistema e Python em uma única camada
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    netcat-traditional \
    gcc \
    libpq-dev \
    libffi-dev \
    python3-dev \
    supervisor \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache

# Copia o resto do projeto
COPY ./src/ .
COPY .env .
COPY supervisord.conf /etc/supervisord.conf
COPY entrypoint.sh /entrypoint.sh

# Configura permissões e coleta arquivos estáticos
RUN chmod +x /entrypoint.sh \
    && mkdir -p /app/logs \
    && python manage.py collectstatic --noinput --no-post-process

ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisord.conf"]