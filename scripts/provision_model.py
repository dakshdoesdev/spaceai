from ultralytics import YOLO
import shutil
from pathlib import Path

def provision_model():
    print("Downloading placeholder YOLO model...")
    # This will download yolov8n.pt to the current directory
    model = YOLO('yolov8n.pt')
    
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    
    dest = models_dir / 'brick_kiln_yolo.pt'
    shutil.move('yolov8n.pt', dest)
    print(f"Moved placeholder model to {dest}")

if __name__ == "__main__":
    provision_model()
