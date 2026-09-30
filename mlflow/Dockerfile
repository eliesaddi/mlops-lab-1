FROM python:3.11-slim

RUN pip install --no-cache-dir mlflow==3.16.1 "sqlalchemy<2.1"

EXPOSE 5000

CMD ["mlflow", "server", \
     "--host", "0.0.0.0", "--port", "5000", \
     "--allowed-hosts", "mlflow:*,localhost:*,127.0.0.1:*,host.docker.internal:*", \
     "--backend-store-uri", "sqlite:////mlflow-data/mlflow.db", \
     "--default-artifact-root", "file:///mlflow-data/mlruns"]