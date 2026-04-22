from ultralytics import YOLO, HUB

# 1. Login
# Replace with your actual API key from the website
api_key = "YOUR_API_KEY_HERE" 
HUB.login(api_key)

# 2. Load your local model
model = YOLO('best.pt')

# 3. Upload to a new project
# This will create a project named 'Pothole-Project' and upload your model
model.push_to_hub('Pothole-Project')