from pathlib import Path

from ultralytics import YOLO


def provision_model() -> int:
    print("Downloading stock YOLO smoke-test weights.")
    print("This does not create models/brick_kiln_yolo.pt and must not be claimed as a kiln detector.")
    YOLO("yolov8n.pt")

    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    dest = models_dir / "yolov8n_stock_smoke.pt"
    source = Path("yolov8n.pt")
    if source.exists():
        source.replace(dest)
        print(f"Saved stock smoke-test model to {dest}")
    else:
        print("Ultralytics loaded stock weights from cache; no local yolov8n.pt file was created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(provision_model())
