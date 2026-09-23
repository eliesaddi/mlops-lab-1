
Question 1

The registered model version was 1. The run’s logged model artifact is the actual model file saved as part of one specific training run in MLflow. A registered model is a named model in the Model Registry, with its own versioning and metadata, so it can be promoted, referenced, and reused independently of the training run that produced it.

Question 2

The aliases that replaced the older MLflow stage names are aliases like champion and challenger. Versioning a model separately from the run is useful because a run is just one training execution, while a model version is the deployable artifact that you may want to track, compare, roll back, or promote over time. An alias is more flexible than a fixed stage because it is a mutable pointer to a version; you can reassign it to a new model version without changing the version number itself.

Question 3

Loading the model through a model URI such as models:/food11@champion is better than loading a raw .pth file because it makes the application use the model as managed by the MLflow Model Registry. That ensures it is using the exact version that has been registered and aliased, and it keeps the deployment tied to a tracked, versioned model instead of a local file path. To serve a newer model version, you would update the alias to point at the newer version number, for example by assigning the champion alias to version 2, and the app would continue to use the same model URI without changing the code.

Question 4

Copying pyproject.toml and uv.lock first and then running uv sync before copying the rest of the source helps Docker cache the dependency installation layer. Dependency files change much less often than application code, so this approach saves time because the expensive package installation work can be reused across rebuilds. If only a line in serve.py changes, Docker reuses the cached dependency installation layer and only rebuilds the later source-copy layer, which keeps the build much faster.

Question 5

A naive single-stage Docker image is typically much larger because it includes both the build environment and the runtime environment in the same image, along with all the tools and package build artifacts. A multi-stage build is smaller because it installs dependencies in one stage and only copies the minimal runtime environment into the final image. Looking at docker history image would show large builder layers from package installation, while the final runtime image is much leaner.

Question 6

If .dockerignore is omitted, the build context becomes much larger and slower to transfer to the Docker daemon. It also increases image size and rebuild time because unnecessary files get copied into the build context. Excluding folders like .venv, data, mlruns, .git, and __pycache__ prevents huge unnecessary payloads. Of those, .venv and mlruns are particularly bad because they can be very large and are not needed in the final runtime image. If they were sent to the Docker daemon, the build would be slower and could waste disk space or even break the build in some cases.

Question 7

The container cannot use 127.0.0.1:5000 to reach the MLflow server on the host because 127.0.0.1 inside the container refers to the container itself, not the machine running Docker. The host is reached through Docker networking, and on Docker Desktop this is typically made available through host.docker.internal. That resolves to the host machine from inside the container, which allows the app to reach the MLflow server running on the host OS.

Question 8

Stopping the container and starting a new one from the same image should still work without rebuilding as long as the MLflow server is still reachable. That is because the app is not loading the model directly from a baked-in local file; it is resolving a model via the MLflow registry at runtime using the model alias. This tells us that the image contains the code and runtime environment, while the model itself is fetched at runtime from MLflow.

Question 9

The Dockerfile and the built image are versioned differently. The Dockerfile is stored in git and can be reviewed and reused, but the built image itself is not automatically versioned by git. Before another machine, such as a CI runner or Kubernetes cluster, could reliably pull and run the exact image, you would need a proper image registry and a fixed version tag. You would also want the image to be pushed to a registry like Docker Hub, GHCR, or Azure Container Registry along with a specific immutable tag such as a version number or commit hash.

