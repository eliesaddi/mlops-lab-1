import shutil
from pathlib import Path

from PIL import Image

RAW_DIR = Path("data/food11_raw")
PROCESSED_DIR = Path("data/food11_processed")
MINI_DIR = Path("data/food11_processed_mini")

CLASSES = [
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
CATEGORIES = {str(index): category for index, category in enumerate(CLASSES)}


def category_from_filename(filename: str) -> str:
    category_id = Path(filename).name.split("_", maxsplit=1)[0]
    try:
        if category_id == "0":
            return "Egg"
        return CATEGORIES[category_id]
    except KeyError as exc:
        raise ValueError(f"Unknown Food-11 category in filename: {filename}") from exc


def resize_image(img: Image.Image, size: int = 128) -> Image.Image:
    return img.convert("RGB").resize((size, size))


def main() -> None:
    for output_dir in [PROCESSED_DIR, MINI_DIR]:
        if output_dir.exists():
            shutil.rmtree(output_dir)

    for split in ["training", "evaluation", "validation"]:
        source_dir = RAW_DIR / split

        for image_path in source_dir.iterdir():
            if not image_path.is_file():
                continue

            try:
                category = category_from_filename(image_path.name)
            except ValueError:
                continue

            processed_category_dir = PROCESSED_DIR / split / category
            mini_category_dir = MINI_DIR / split / category

            processed_category_dir.mkdir(parents=True, exist_ok=True)
            mini_category_dir.mkdir(parents=True, exist_ok=True)

            output_path = processed_category_dir / image_path.name

            with Image.open(image_path) as image:
                resize_image(image).save(output_path)

            if len(list(mini_category_dir.iterdir())) < 100:
                shutil.copy2(output_path, mini_category_dir / image_path.name)

    print("Food-11 data preparation completed.")


if __name__ == "__main__":
    main()
