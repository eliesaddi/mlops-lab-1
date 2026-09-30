import io
import logging
import os
import time
from typing import Any

import mlflow
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from torchvision import transforms

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MODEL_URI = "models:/food11@champion"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

app = FastAPI(title="Food11 Serving API")
model: Any = None
logger = logging.getLogger(__name__)

IMAGE_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

CLASS_NAMES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]


@app.on_event("startup")
def load_model() -> None:
    global model
    for attempt in range(12):
        try:
            model = mlflow.pyfunc.load_model(MODEL_URI)
            return
        except Exception:
            if attempt == 11:
                raise
            logger.warning("MLflow model unavailable; retrying startup in 5 seconds")
            time.sleep(5)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> dict[str, Any]:
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:  # pragma: no cover - validation path
        raise HTTPException(status_code=400, detail="Could not read the uploaded image") from exc

    try:
        tensor = IMAGE_TRANSFORM(image).unsqueeze(0).numpy()
        prediction = _run_prediction(tensor)
    except Exception as exc:  # pragma: no cover - runtime validation path
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    probs = np.asarray(prediction).squeeze()
    if probs.ndim == 0:
        probs = np.asarray([float(probs)])
    if probs.ndim == 1 and len(probs) > 1:
        probs = _normalize_scores(probs)
    elif probs.ndim == 2 and probs.shape[0] == 1:
        probs = _normalize_scores(probs[0])

    if probs.ndim == 1 and len(probs) == 1:
        label_index = 0
        confidence = float(probs[0])
    elif probs.ndim == 1 and len(probs) > 1:
        label_index = int(np.argmax(probs))
        confidence = float(np.max(probs))
    elif probs.ndim == 2 and probs.shape[0] == 1:
        label_index = int(np.argmax(probs[0]))
        confidence = float(np.max(probs[0]))
    else:
        label_index = int(np.argmax(probs))
        confidence = float(np.max(probs))

    predicted_label = CLASS_NAMES[label_index]
    return {"category": predicted_label, "confidence": confidence}


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=np.float64)
    if np.all(scores >= 0) and np.isclose(scores.sum(), 1.0):
        return scores

    exp_scores = np.exp(scores - np.max(scores))
    return exp_scores / exp_scores.sum()


def _run_prediction(tensor: np.ndarray) -> Any:
    candidates = [
        tensor,
        tensor.astype(np.float32),
        np.asarray(tensor).reshape(1, -1),
    ]

    for candidate in candidates:
        for fn in (
            lambda data: model.predict(data),
            lambda data: model.predict(pd.DataFrame(data.reshape(1, -1))),
        ):
            try:
                return fn(candidate)
            except Exception:
                continue

    raise RuntimeError("Model prediction did not return a valid output")
