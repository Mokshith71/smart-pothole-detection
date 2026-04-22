import cv2
import datetime
import time
import requests
import os
import winsound
from ultralytics import YOLO
from pymongo import MongoClient

# ==========================================
# 1. CONFIGURATION
# ==========================================
IP_ADDRESS = "192.168.31.106:8080" # Update this if your phone app changes it
VIDEO_URL = f"http://{IP_ADDRESS}/video"
SENSOR_URL = f"http://{IP_ADDRESS}/sensors.json"

MODEL_PATH = 'best.pt'
CONFIDENCE_THRESHOLD = 0.6

# --- MONGODB SETUP ---
# PASTE YOUR CONNECTION STRING HERE. 
# Remember to replace <db_password> with your actual password!
MONGO_URI = MONGO_URI = "mongodb+srv://mokshithv71_db_user:Mokshith%402005@cluster0.alfgnnb.mongodb.net/?appName=Cluster0"

print("Connecting to MongoDB...")
client = MongoClient(MONGO_URI)
db = client["pothole_database"]
collection = db["live_detections"]
print("✅ Connected to Cloud Database!")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_gps():
    try:
        resp = requests.get(SENSOR_URL, timeout=1.0)
        data = resp.json()
        if 'gps_active' in data and data['gps_active']['data']:
            lat = data['gps_active']['data'][0][1][0] 
            lon = data['gps_active']['data'][0][1][1]
            return lat, lon
    except Exception as e:
        pass
    # Fallback coordinates if GPS fails
    return 12.9716, 77.5946

def log_pothole(lat, lon, confidence, image_path):
    margin = 0.000045 # Roughly 5 meters radius
    
    existing_pothole = collection.find_one({
        "latitude": {"$gte": float(lat) - margin, "$lte": float(lat) + margin},
        "longitude": {"$gte": float(lon) - margin, "$lte": float(lon) + margin}
    })

    if existing_pothole:
        new_count = existing_pothole.get("report_count", 1) + 1
        try:
            collection.update_one(
                {"_id": existing_pothole["_id"]},
                {"$set": {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "report_count": new_count,
                    "severity_score": max(existing_pothole.get("severity_score", 0), float(confidence))
                }}
            )
            print(f"🔄 Pothole Verified! This hazard has now been reported {new_count} times.")
        except Exception as e:
            print(f"❌ Failed to update MongoDB: {e}")
            
    else:
        document = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": float(lat),
            "longitude": float(lon),
            "severity_score": float(confidence),
            "image_path": image_path,
            "report_count": 1
        }
        try:
            collection.insert_one(document)
            print(f"🚨 New Hazard Logged to Cloud! (Severity: {confidence:.2f})")
        except Exception as e:
            print(f"❌ Failed to log to MongoDB: {e}")

# ==========================================
# 3. MAIN SYSTEM LOOP
# ==========================================
print("Loading AI Model...")
model = YOLO(MODEL_PATH)

print(f"Connecting to Camera at {VIDEO_URL}...")
cap = cv2.VideoCapture(VIDEO_URL)

if not os.path.exists("snapshots"):
    os.makedirs("snapshots")

logged_pothole_ids = set()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Retrying...")
        time.sleep(1)
        cap = cv2.VideoCapture(VIDEO_URL)
        continue

    results = model.track(frame, persist=True, stream=True, verbose=False)

    for r in results:
        boxes = r.boxes
        if boxes.id is not None:
            track_ids = boxes.id.int().cpu().tolist()
            
            for box, track_id in zip(boxes, track_ids):
                conf = float(box.conf[0])
                
                if conf > CONFIDENCE_THRESHOLD:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(frame, f"ID:{track_id} Conf:{conf:.2f}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                    if track_id not in logged_pothole_ids:
                        lat, lon = get_gps()
                        
                        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_name = f"snapshots/pothole_{track_id}_{timestamp_str}.jpg"
                        cv2.imwrite(img_name, frame)
                        
                        log_pothole(lat, lon, conf, img_name)
                        winsound.Beep(1000, 500) 
                        logged_pothole_ids.add(track_id)

    cv2.imshow("Smart Pothole Detection (Press 'q' to quit)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()