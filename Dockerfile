FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --python /usr/local/bin/python

FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    MLFLOW_TRACKING_URI=http://host.docker.internal:5000

COPY --from=builder /app/.venv /app/.venv
COPY ./src /app/src

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "src.food11.serve:app", "--host", "0.0.0.0", "--port", "8000"]
