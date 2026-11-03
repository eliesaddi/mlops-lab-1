import argparse
import os
from math import sqrt
from pathlib import Path

from mlflow import MlflowClient

MODEL_NAME = "food11"
METRIC_NAME = "test_accuracy"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def evaluation_size(dataset: str) -> int:
    dataset_dir = {
        "mini": Path("data/food11_processed_mini"),
        "processed": Path("data/food11_processed"),
    }[dataset]
    evaluation_dir = dataset_dir / "evaluation"
    count = sum(
        1
        for path in evaluation_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if count == 0:
        raise ValueError(f"No evaluation images found in {evaluation_dir}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a candidate Food-11 model")
    parser.add_argument("--version", type=int, required=True)
    args = parser.parse_args()

    client = MlflowClient(
        tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    )
    candidate = client.get_model_version(MODEL_NAME, str(args.version))
    champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
    candidate_run = client.get_run(candidate.run_id)
    champion_run = client.get_run(champion.run_id)

    candidate_dataset = candidate_run.data.params.get("dataset")
    champion_dataset = champion_run.data.params.get("dataset")
    if candidate_dataset not in {"mini", "processed"}:
        raise ValueError(f"Unsupported candidate dataset: {candidate_dataset}")
    if champion_dataset not in {"mini", "processed"}:
        raise ValueError(
            "Champion run has no supported dataset parameter; log its dataset "
            "before comparing candidate accuracy"
        )
    if candidate_dataset != champion_dataset:
        raise ValueError(
            "Candidate and champion must use the same dataset to compare accuracy"
        )

    if METRIC_NAME not in candidate_run.data.metrics:
        raise ValueError(f"Candidate run has no {METRIC_NAME} metric")
    if METRIC_NAME not in champion_run.data.metrics:
        raise ValueError(f"Champion run has no {METRIC_NAME} metric")

    candidate_accuracy = candidate_run.data.metrics[METRIC_NAME]
    champion_accuracy = champion_run.data.metrics[METRIC_NAME]
    sample_count = evaluation_size(candidate_dataset)
    standard_error = sqrt(
        champion_accuracy * (1 - champion_accuracy) / sample_count
    )
    threshold = 2 * standard_error
    promote = candidate_accuracy >= champion_accuracy + threshold

    if promote:
        client.set_registered_model_alias(
            MODEL_NAME, "champion", str(args.version)
        )
        decision = "promoted"
    else:
        client.set_registered_model_alias(
            MODEL_NAME, "challenger", str(args.version)
        )
        decision = "challenger"

    tags = {
        "promotion_decision": decision,
        "candidate_test_accuracy": str(candidate_accuracy),
        "champion_test_accuracy": str(champion_accuracy),
        "promotion_threshold": str(threshold),
    }
    for key, value in tags.items():
        client.set_model_version_tag(MODEL_NAME, str(args.version), key, value)

    print(
        f"candidate={candidate_accuracy:.4f} champion={champion_accuracy:.4f} "
        f"2*se={threshold:.4f} ({threshold * 100:.2f} points) "
        f"n={sample_count} decision={decision}"
    )


if __name__ == "__main__":
    main()