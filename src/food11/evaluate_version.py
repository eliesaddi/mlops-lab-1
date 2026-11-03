import argparse
import os
from pathlib import Path

import mlflow.pytorch
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

import mlflow
from mlflow import MlflowClient

MODEL_NAME = "food11"
DATASET_DIRS = {
    "mini": Path("data/food11_processed_mini"),
    "processed": Path("data/food11_processed"),
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate and re-register a Food-11 model version"
    )
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--dataset", choices=DATASET_DIRS, default="mini")
    parser.add_argument(
        "--set-champion",
        action="store_true",
        help="Set champion to the reevaluated version (only allowed for the current champion)",
    )
    args = parser.parse_args()

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient(tracking_uri=tracking_uri)

    source_version = client.get_model_version(MODEL_NAME, str(args.version))
    if args.set_champion:
        current_champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
        if current_champion.version != str(args.version):
            raise ValueError(
                "--set-champion is only allowed when reevaluating the current champion"
            )

    model = mlflow.pytorch.load_model(f"models:/{MODEL_NAME}/{args.version}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    data_dir = DATASET_DIRS[args.dataset] / "evaluation"
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
            ),
        ]
    )
    dataset = datasets.ImageFolder(root=str(data_dir), transform=transform)
    if len(dataset) == 0:
        raise ValueError(f"No evaluation images found in {data_dir}")
    loader = DataLoader(dataset, batch_size=32, shuffle=False)

    correct = 0
    with torch.inference_mode():
        for images, labels in loader:
            outputs = model(images.to(device))
            correct += (outputs.argmax(dim=1).cpu() == labels).sum().item()
    accuracy = correct / len(dataset)

    with mlflow.start_run(run_name=f"food11-eval-v{args.version}-{args.dataset}") as run:
        mlflow.log_params(
            {
                "dataset": args.dataset,
                "evaluated_model_version": str(args.version),
                "source_run_id": source_version.run_id,
            }
        )
        mlflow.log_metrics(
            {"test_accuracy": accuracy, "evaluation_size": len(dataset)}
        )
        mlflow.pytorch.log_model(
            model,
            "model",
            input_example=torch.zeros(1, 3, 224, 224).to(device),
            serialization_format="pickle",
        )
        evaluation_run_id = run.info.run_id

    registered = mlflow.register_model(
        f"runs:/{evaluation_run_id}/model", MODEL_NAME
    )
    client.set_model_version_tag(
        MODEL_NAME, registered.version, "evaluated_model_version", str(args.version)
    )
    if args.set_champion:
        client.set_registered_model_alias(MODEL_NAME, "champion", registered.version)

    print(
        f"source_version={args.version} registered_version={registered.version} "
        f"dataset={args.dataset} n={len(dataset)} test_accuracy={accuracy:.4f}"
    )


if __name__ == "__main__":
    main()