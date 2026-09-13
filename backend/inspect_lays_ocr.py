import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.ocr.ocr_service import ocr_service

path = r"C:\Users\doram\Downloads\lays.jpg"
res = ocr_service.process_image(path, is_demo=False)
boxes = res.get("bounding_boxes", [])
print(f"Total blocks detected: {len(boxes)}")
print(f"Avg confidence: {res.get('avg_confidence')}%")

low_conf = []
for i, b in enumerate(boxes, 1):
    conf = b["confidence"]
    if conf < 80.0:
        low_conf.append((i, b["text"], conf, b["box"]))
    print(f"[{i:02d}] {b['text']} (conf: {conf}%) [Box: {b['box']}]")

print(f"\nTotal low-confidence (<80%): {len(low_conf)}")
for item in low_conf:
    print(f"  Line {item[0]}: '{item[1]}' -> {item[2]}% [Box: {item[3]}]")
