import argparse
from pathlib import Path
import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

def parse_args():
    parser = argparse.ArgumentParser(description="Train ResNet18 on Food-11")
    parser.add_argument("--dataset", type=str, default="mini", choices=["mini", "processed"], help="Dataset split to use")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    return parser.parse_args()

def get_data_dir(dataset_type):
    data_path = Path("./data")
    folder_name = "food11_processed_mini" if dataset_type == "mini" else "food11_processed"
    return data_path / folder_name

def main():
    args = parse_args()

    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    mlflow.set_experiment("food11")

    data_dir = get_data_dir(args.dataset)
    print(f"Loading data from: {data_dir}")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Target 'training', 'validation', and 'evaluation'
    train_dataset = datasets.ImageFolder(root=str(data_dir / "training"), transform=transform)
    val_dataset = datasets.ImageFolder(root=str(data_dir / "validation"), transform=transform)
    test_dataset = datasets.ImageFolder(root=str(data_dir / "evaluation"), transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 11)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    with mlflow.start_run():
        mlflow.log_params({
            "dataset": args.dataset,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size
        })

        for epoch in range(1, args.epochs + 1):
            model.train()
            running_loss = 0.0
            for inputs, labels in train_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item() * inputs.size(0)

            train_loss = running_loss / len(train_dataset)

            model.eval()
            val_loss = 0.0
            correct = 0
            with torch.no_grad():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(device), labels.to(device)
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item() * inputs.size(0)
                    preds = outputs.argmax(dim=1)
                    correct += (preds == labels).sum().item()

            val_loss = val_loss / len(val_dataset)
            val_acc = correct / len(val_dataset)

            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("val_accuracy", val_acc, step=epoch)

            print(f"Epoch {epoch}/{args.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")

        model.eval()
        test_correct = 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                preds = outputs.argmax(dim=1)
                test_correct += (preds == labels).sum().item()

        test_acc = test_correct / len(test_dataset)
        mlflow.log_metric("test_accuracy", test_acc)

        example_input = torch.randn(1, 3, 224, 224).to(device)
        mlflow.pytorch.log_model(
            model,
            "model",
            input_example=example_input,
            serialization_format="pickle"
        )
if __name__ == "__main__":
    main()