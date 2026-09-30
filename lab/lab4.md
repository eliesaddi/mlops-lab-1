Bootstrap the fresh Compose registry

The named volume starts empty; it does not contain the model registered in the Lab 3 host-side `mlflow.db`. For this run, I imported the existing Lab 3 registered model artifact into the new volume, registered it as `food11` version 1, and set `champion`. When starting without an existing model to import, seed the new tracking store by training a short mini-dataset run, then register its best run and set the modern alias before starting the full stack:

```bash
docker compose build
docker compose up -d mlflow
docker compose run --rm --no-deps -v ./data:/app/data:ro inference /app/.venv/bin/python -m src.food11.train --dataset mini --epochs 1
docker compose run --rm --no-deps inference /app/.venv/bin/python -c "import mlflow; from mlflow import MlflowClient; mlflow.set_tracking_uri('http://mlflow:5000'); client = MlflowClient(); experiment = client.get_experiment_by_name('food11'); run = client.search_runs([experiment.experiment_id], order_by=['metrics.val_accuracy DESC'], max_results=1)[0]; version = mlflow.register_model(f'runs:/{run.info.run_id}/model', 'food11'); client.set_registered_model_alias('food11', 'champion', version.version); print('champion version', version.version)"
docker compose up -d
```

Question 1

Without a mounted volume, `/mlflow-data` is part of that container's writable layer. I tested this with a disposable marker file: after removing the first container, a new container from the same image reported `NEW_CONTAINER_EMPTY`. Removing an unmounted MLflow container similarly discards its database and artifacts, so the new container starts with an empty tracking store.

Question 2

A named volume is managed by Docker, persists independently of a container, and avoids coupling runtime state to a repository path or host OS. A bind mount can also persist the data and is useful for local development, but it depends on a specific host path and its permissions. Both MLflow and inference mount the named volume at the same `/mlflow-data` path because the registry's model artifact URI is a local file URI.

Question 3

Compose attaches the services to a shared private network and provides DNS for service names. `mlflow` resolves to the MLflow container's network address from inference; `127.0.0.1` would refer to inference itself. No host gateway name is needed for service-to-service requests.

Question 4

`INFERENCE_URL` is configurable so the frontend can target `http://inference:8000` on the Compose network while retaining a loopback default for standalone local use. The Compose-only hostname `inference` is not resolvable when the container runs outside that network.

Question 5

Only MLflow's UI/API and the frontend are published for access from the host. Inference stays private because the frontend calls `http://inference:8000` over the Compose network, where Compose DNS resolves the service name.

Question 6

Plain `depends_on` only orders container creation and does not wait for MLflow readiness. This Compose setup adds an MLflow health check and waits for it to pass; the inference startup handler also retries model loading for up to about one minute. On the first start, MLflow was healthy but the new registry had no `champion` alias, so inference exhausted its retries and exited. After importing/registering the model and alias, inference started successfully and became healthy. Readiness checks cannot substitute for seeding the model registry.

Question 7

`docker compose ps` showed published host ports for `mlflow` (`5000`) and `frontend` (`8501`), with no published host port for `inference` (only its internal `8000/tcp`). That matches the Compose configuration: inference is only called over the private Compose network. A real image request from a temporary frontend container to `http://inference:8000/predict` succeeded.

Question 8

The serving process loads `models:/food11@champion` once at startup. Changing the `champion` alias does not replace the already-loaded in-memory model. I registered version 2 from the same artifact, moved `champion` from version 1 to version 2, and ran `docker compose restart inference`; it became healthy and loaded the alias's current target without rebuilding. Since both versions used the same artifact, the prediction itself was unchanged. The container uses the modern MLflow alias `champion` rather than the deprecated `Staging` stage.

Question 9

Restarting reuses the existing image, which already contains the API code and Python environment. At startup, the API resolves the alias and loads model data from the MLflow service and shared persistent volume, so changing the model version does not require rebuilding the image.

Question 10

I ran `docker compose down` followed by `docker compose up`; `food11` version 1 and its `champion` alias were still present, and all services became healthy. `down` removes the containers and network but keeps the named `mlflow-data` volume. `docker compose down -v` also removes that volume, deleting the database and artifacts; the next stack starts with an empty registry and needs a model registered again. I did not run `down -v` on the working volume because that would delete the persisted model.

Question 11

Compose is a single-machine orchestrator. It does not provide multi-node scheduling, production load balancing and service discovery across machines, automatic failover, or replicated durable storage. Those needs call for an orchestrator such as Kubernetes or a managed platform, plus a shared highly available database and artifact store for MLflow.