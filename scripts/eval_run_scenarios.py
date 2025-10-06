import yaml
from pathlib import Path
def main() -> None:
    cfg = yaml.safe_load(Path("TESTS/scenario_suite.yaml").read_text())
    print(f"Loaded {len(cfg.get('scenarios', []))} scenarios.")
if __name__ == "__main__":
    main()
