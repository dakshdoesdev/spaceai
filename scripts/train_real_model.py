from pathlib import Path
import shutil

from ultralytics import YOLO


def main() -> None:
    dataset_dir = Path("Brick Kiln Detection.v1-dataset_aug.yolov8").resolve()
    yaml_path = dataset_dir / "data.yaml"

    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found.")
        return

    yaml_content = yaml_path.read_text(encoding="utf-8")
    yaml_content = yaml_content.replace("../train/images", str(dataset_dir / "train/images"))
    yaml_content = yaml_content.replace("../valid/images", str(dataset_dir / "valid/images"))
    yaml_content = yaml_content.replace("../test/images", str(dataset_dir / "test/images"))
    yaml_path.write_text(yaml_content, encoding="utf-8")

    print(f"Updated paths in {yaml_path}")
    print("Starting YOLO training (this will take a few minutes)...")

    model = YOLO("yolov8n.pt")
    model.train(
        data=str(yaml_path),
        epochs=5,
        imgsz=512,
        batch=16,
        project="runs",
        name="brick_kiln_custom",
    )

    best_model_path = Path("runs/brick_kiln_custom/weights/best.pt")

    if best_model_path.exists():
        target_path = Path("models/brick_kiln_yolo.pt")
        target_path.parent.mkdir(exist_ok=True)
        shutil.copy(best_model_path, target_path)
        print(f"Success. Custom brick-kiln model saved to: {target_path}")
    else:
        print("Training completed but best.pt was not found.")


if __name__ == "__main__":
    main()
