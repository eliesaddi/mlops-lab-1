# Lab 5 - CI/CD with GitHub Actions

## Question 1

A unit test that loads the real MLflow model depends on external state and services, so it can fail even when the code under test is correct. The MLflow server may be unavailable or unreachable, and the `champion` alias or its artifact may be missing. Loading a large model also makes tests slower and less deterministic. The fake model keeps this test focused on the API's request handling and response format.

## Question 2

The API test proves that the endpoint accepts an uploaded image, calls the injected model, and returns JSON with the expected category and a confidence between 0 and 1 for the fake model's fixed output. It does not measure real model accuracy, prove that MLflow can load a model, or show that predictions generalize to unseen food images.

## Question 3

The cross-split duplicate check catches identical file content by hash. A duplicate can leak examples between training and evaluation and make test accuracy look better than performance on genuinely unseen images, while a corrupted image usually causes an immediate, visible decoding error. The validator's synthetic test passed on a clean dataset and failed after I copied a training image into evaluation. The existing mini dataset also contains 43 cross-split duplicates, so its validation correctly fails before any additional copy is made.

## Question 4

Run `validate_data.py` in the local or training environment after `dvc pull` and before training. Run it again in the data-preparation or model-release pipeline where the DVC remote is available, before evaluating or registering a model. GitHub-hosted CI cannot validate data it cannot access.

## Question 5

If a test fails, the `smoke` job is skipped because it has `needs: test`. Without that dependency, smoke could run independently, wasting time and potentially succeeding even though the unit-test gate failed.

## Question 6

Record the elapsed time for the first and second workflow runs from the GitHub Actions run summary. The second run should benefit from the `setup-uv` dependency cache and Docker BuildKit cache. The timings are pending the first GitHub Actions run.

## Question 7

A commit-SHA tag identifies the exact code used to build an image and can be rolled back or reproduced. With `latest`, machine A could pull it before a new push and keep running the previous image, while machine B pulls afterward and runs the new image; both would claim to run `latest` while running different code.

## Question 8

The publishing job grants only read access to repository contents and write access to packages. If a compromised step received a broadly write-enabled token, it could modify repository contents, publish releases, or alter other resources permitted by that token, expanding the impact beyond publishing the image.

## Question 9

After branch protection is enabled, the pull request should show the `test` and `smoke` checks, and a deliberately broken test should be red. A required failing check prevents merging until it passes. I have not configured the repository's branch protection or opened the demonstration pull request yet; those settings require repository-owner access. Compared with relying on each developer to remember local tests, required checks apply the same merge gate to every contributor.

## Question 10

The promotion gate cannot yet be run against the current `champion`: its MLflow source run has `val_accuracy` but no `test_accuracy` or `dataset` parameter. Those fields are required for a valid comparison, so I left the alias unchanged and made the script report this missing metadata. The mini evaluation split currently has 1,096 images and the full split has 3,347. For a mini run, the threshold is `2 * sqrt(p * (1 - p) / 1096)`, where `p` is the champion's test accuracy; actual candidate decisions and threshold points must be recorded after a champion run with the required metric and dataset parameter is registered.

## Question 11

One option is to use a hosted tracking server such as DagsHub and trigger a workflow after model registration, giving the runner an authenticated route to MLflow. Another is to use a self-hosted GitHub Actions runner in the same private network as the MLflow server, then trigger the promotion job after training.

## Question 12

```mermaid
flowchart LR
    A[Push branch] --> B[Automatic: lint and unit tests]
    B --> C[Automatic: build image and smoke test]
    C --> D{Checks pass?}
    D -- No --> E[Fix code and push again]
    E --> B
    D -- Yes --> F[Human: review and merge PR]
    F --> G[Automatic on main: publish GHCR image tagged with commit SHA]
    G --> H[Human: train/register candidate and run promotion gate]
    H --> I{Quality gate}
    I -- Pass --> J[champion alias points to candidate]
    I -- Fail --> K[challenger alias points to candidate]
    J --> L[Human: deploy/restart serving container]
    K --> L
    L --> M[Container uses chosen image SHA and loads models:/food11@champion]
```

The code version is chosen by the commit whose SHA tags the published image. The model version is chosen independently by the MLflow `champion` alias when the promotion gate accepts a candidate. The workflow publishes an image but does not deploy or restart the Compose service.