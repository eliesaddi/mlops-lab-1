from pathlib import Path
from PIL import Image
import shutil

RAW_DIR = Path("data/food11_raw")
PROCESSED_DIR = Path("data/food11_processed")
MINI_DIR = Path("data/food11_processed_mini")

CATEGORIES = {
    "0": "Bread",
    "1": "Dairy product",
    "2": "Dessert",
    "3": "Egg",
    "4": "Fried food",
    "5": "Meat",
    "6": "Noodles-Pasta",
    "7": "Rice",
    "8": "Seafood",
    "9": "Soup",
    "10": "Vegetable-Fruit",
}

for output_dir in [PROCESSED_DIR, MINI_DIR]:
    if output_dir.exists():
        shutil.rmtree(output_dir)

for split in ["training", "evaluation", "validation"]:
    source_dir = RAW_DIR / split

    for image_path in source_dir.iterdir():
        if not image_path.is_file():
            continue

        category_id = image_path.name.split("_")[0]
        category = CATEGORIES.get(category_id)

        if category is None:
            continue

        processed_category_dir = PROCESSED_DIR / split / category
        mini_category_dir = MINI_DIR / split / category

        processed_category_dir.mkdir(parents=True, exist_ok=True)
        mini_category_dir.mkdir(parents=True, exist_ok=True)

        output_path = processed_category_dir / image_path.name

        with Image.open(image_path) as image:
            image = image.convert("RGB")
            image = image.resize((128, 128))
            image.save(output_path)

        if len(list(mini_category_dir.iterdir())) < 100:
            shutil.copy2(output_path, mini_category_dir / image_path.name)

print("Food-11 data preparation completed.")
