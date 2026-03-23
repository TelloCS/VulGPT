FROM python:3.13-slim-bullseye AS python

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system appgroup && adduser --system --group appuser

WORKDIR /app

COPY requirements.txt /app/

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

#######################################################################
FROM python AS dev

ENV DJANGO_SETTINGS_MODULE=vulgpt.settings.local

COPY --chown=appuser:appuser . /app/
RUN mkdir -p /app/staticfiles

RUN sed -i 's/\r$//' /app/entrypoint.prod.sh && \
    chmod +x /app/entrypoint.prod.sh

ENTRYPOINT ["/app/entrypoint.prod.sh"]

RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

#######################################################################
FROM python AS prod

ENV DJANGO_SETTINGS_MODULE=vulgpt.settings.production

COPY --chown=appuser:appuser . /app/
RUN mkdir -p /app/staticfiles

# Windows Safegaurd: Remove hidden carriage returns from the entrypoint script
RUN sed -i 's/\r$//' /app/entrypoint.prod.sh && \
    chmod +x /app/entrypoint.prod.sh

ENTRYPOINT ["/app/entrypoint.prod.sh"]

# Transfer ownership of everything to the non-root user
RUN chown -R appuser:appgroup /app

# Drop root privileges immediately
USER appuser

CMD ["gunicorn", "vulgpt.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]