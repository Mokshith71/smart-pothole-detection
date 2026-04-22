import pandas as pd

# Create dummy data with the correct columns
data = {
    'timestamp': ['2023-10-01 10:00:00', '2023-10-01 10:05:00', '2023-10-01 10:15:00'],
    'latitude': [12.9716, 12.9780, 12.9352],
    'longitude': [77.5946, 77.5700, 77.6245],
    'image_path': ['pothole1.jpg', 'pothole2.jpg', 'pothole3.jpg']
}

df = pd.DataFrame(data)

# Save to CSV without the index number (this is crucial)
df.to_csv("pothole_db.csv", index=False)

print("✅ Success: New pothole_db.csv created correctly!")