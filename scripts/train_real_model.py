import os
from pathlib import Path
from ultralytics import YOLO
import shutil

def main():
    dataset_dir = Path("Brick Kiln Detection.v1-dataset_aug.yolov8").resolve()
    yaml_path = dataset_dir / "data.yaml"
    
    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found.")
        return

    # Fix paths in data.yaml to be absolute
    with open(yaml_path, 'r') as f:
        yaml_content = f.read()
    
    yaml_content = yaml_content.replace('../train/images', str(dataset_dir / 'train/images'))
    yaml_content = yaml_content.replace('../valid/images', str(dataset_dir / 'valid/images'))
    yaml_content = yaml_content.replace('../test/images', str(dataset_dir / 'test/images'))

    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"Updated paths in {yaml_path}")
    print("Starting YOLO training (this will take a few minutes)...")

    # Load the base model
    model = YOLO("yolov8n.pt")  # Nano model is fast
    
    # Train the model on the dataset for 5 epochs to get a proof-of-concept custom model
    results = model.train(
        data=str(yaml_path),
        epochs=5,        # 5 epochs is enough for a demo model. Increase later for accuracy.
        imgsz=512,       # Panipat demo tiles are 512x512
        batch=16,
        project="runs",
        name="brick_kiln_custom"
    )
    
    # The best weights are saved here
    best_model_path = Path("runs/brick_kiln_custom/weights/best.pt")
    
    if best_model_path.exists():
        target_path = Path("models/brick_kiln_yolo.pt")
        target_path.parent.mkdir(exist_ok=True)
        shutil.copy(best_model_path, target_path)
        print(f"\n✅ Success! Real custom model saved to: {target_path}")
    else:
        print("\n❌ Training completed but could not find the best.pt weights.")

if __name__ == "__main__":
    main()
