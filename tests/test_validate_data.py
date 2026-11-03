import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

from src.food11.data import CLASSES


def test_validator_detects_cross_split_duplicate(tmp_path):
    dataset_dir = tmp_path / "dataset"
    split_names = ("training", "validation", "evaluation")

    for split_index, split in enumerate(split_names):
        for class_index, category in enumerate(CLASSES):
            class_dir = dataset_dir / split / category
            class_dir.mkdir(parents=True)
            color = (class_index, split_index, class_index + split_index)
            Image.new("RGB", (128, 128), color=color).save(class_dir / "image.png")

    validator = Path(__file__).parents[1] / "src" / "food11" / "validate_data.py"
    command = [sys.executable, str(validator), str(dataset_dir), "--min-per-class", "1"]
    valid_result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert valid_result.returncode == 0, valid_result.stdout + valid_result.stderr

    shutil.copy2(
        dataset_dir / "training" / "Bread" / "image.png",
        dataset_dir / "evaluation" / "Bread" / "duplicate.png",
    )
    duplicate_result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert duplicate_result.returncode == 1
    assert "FAIL cross-split duplicates" in duplicate_result.stdout