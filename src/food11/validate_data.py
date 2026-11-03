import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image

if __package__:
    from .data import CLASSES
else:
    from data import CLASSES

SPLITS = ("training", "validation", "evaluation")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a processed Food-11 dataset")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--min-per-class", type=int, default=50)
    parser.add_argument("--tau", type=float, default=0.05)
    args = parser.parse_args()

    if args.min_per_class < 0:
        parser.error("--min-per-class must be non-negative")
    if not 0 <= args.tau <= 1:
        parser.error("--tau must be between 0 and 1")

    if not args.dataset.is_dir():
        print(f"FAIL dataset directory exists: {args.dataset}")
        sys.exit(1)

    split_dirs = {split: args.dataset / split for split in SPLITS}
    expected_classes = set(CLASSES)
    folder_results = {
        split: {
            path.name
            for path in split_dir.iterdir()
            if path.is_dir()
        }
        if split_dir.is_dir()
        else set()
        for split, split_dir in split_dirs.items()
    }
    folders_valid = all(
        folder_results[split] == expected_classes for split in SPLITS
    )

    class_counts = {split: {category: 0 for category in CLASSES} for split in SPLITS}
    images_valid = True
    invalid_image: Path | None = None
    hashes: dict[str, tuple[str, Path]] = {}
    duplicate_found: tuple[Path, Path] | None = None

    for split, split_dir in split_dirs.items():
        if not split_dir.is_dir():
            continue
        for image_path in split_dir.rglob("*"):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue

            relative_parts = image_path.relative_to(split_dir).parts
            if relative_parts and relative_parts[0] in expected_classes:
                class_counts[split][relative_parts[0]] += 1

            try:
                with Image.open(image_path) as image:
                    image.load()
                    if image.mode != "RGB" or image.size != (128, 128):
                        images_valid = False
                        invalid_image = invalid_image or image_path
            except (EOFError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
                images_valid = False
                invalid_image = invalid_image or image_path

            digest = hashlib.md5(image_path.read_bytes()).hexdigest()
            previous = hashes.get(digest)
            if previous is not None and previous[0] != split:
                duplicate_found = duplicate_found or (previous[1], image_path)
            else:
                hashes[digest] = (split, image_path)

    minimum_valid = all(
        class_counts[split][category] >= args.min_per_class
        for split in SPLITS
        for category in CLASSES
    )

    training_total = sum(class_counts["training"].values())
    validation_total = sum(class_counts["validation"].values())
    proportions = {
        category: abs(
            class_counts["training"][category] / training_total
            - class_counts["validation"][category] / validation_total
        )
        for category in CLASSES
    } if training_total and validation_total else {}
    balance_valid = bool(proportions) and all(
        difference <= args.tau for difference in proportions.values()
    )

    checks = [
        ("class folders", folders_valid, "each split must contain exactly 11 classes"),
        (
            "image format",
            images_valid,
            "all images must open as RGB 128x128"
            if images_valid
            else f"invalid image: {invalid_image}",
        ),
        (
            "minimum counts",
            minimum_valid,
            f"at least {args.min_per_class} images per class in every split",
        ),
        (
            "cross-split duplicates",
            duplicate_found is None,
            "no image content may occur in multiple splits"
            if duplicate_found is None
            else f"duplicate files: {duplicate_found[0]} and {duplicate_found[1]}",
        ),
        (
            "train/validation balance",
            balance_valid,
            f"maximum share difference must be <= {args.tau}"
            if proportions
            else "training and validation splits must not be empty",
        ),
    ]

    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")

    if not all(passed for _, passed, _ in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()