import csv
from pathlib import Path
def main() -> None:
    p = Path("DATA/copy_variants.csv")
    rows = list(csv.DictReader(p.open()))
    print(f"Loaded {len(rows)} copy variants.")
if __name__ == "__main__":
    main()
