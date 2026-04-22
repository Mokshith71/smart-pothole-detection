import streamlit as st
import pandas as pd
from pymongo import MongoClient

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(page_title="Pothole Dashboard", page_icon="🚧", layout="wide")

# PASTE YOUR CONNECTION STRING HERE
MONGO_URI = MONGO_URI = "mongodb+srv://mokshithv71_db_user:Mokshith%402005@cluster0.alfgnnb.mongodb.net/?appName=Cluster0"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client["pothole_database"]
    collection = db["live_detections"]
except Exception as e:
    st.error(f"Failed to connect to MongoDB: {e}")
    st.stop()

def fetch_data():
    cursor = collection.find({}, {"_id": 0})
    data = list(cursor)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

st.title("🚧 Smart Pothole Detection Dashboard")
st.markdown("Live telemetry and administrative overview of road hazards detected via Edge AI.")

if st.button("🔄 Refresh Data"):
    st.rerun()

df = fetch_data()

if not df.empty:
    st.subheader("System Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    total_hazards = len(df)
    max_severity = df['severity_score'].max()
    most_reported = df['report_count'].max() if 'report_count' in df.columns else 1
    
    col1.metric("Unique Hazards Tracked", total_hazards)
    col2.metric("Highest Severity Score", f"{max_severity:.2f}")
    col3.metric("Most Verified Hazard", f"{most_reported} Reports")
    col4.metric("Latest Detection", df['timestamp'].max())
    
    st.divider()

    st.subheader("📍 Hazard Map")
    st.map(df, color="#ff0000", size=50) 
    
    st.divider()

    st.subheader("📋 Raw Telemetry Data")
    if 'report_count' in df.columns:
        df_sorted = df.sort_values(by=["report_count", "timestamp"], ascending=[False, False])
    else:
        df_sorted = df.sort_values(by="timestamp", ascending=False)
        
    st.dataframe(df_sorted, use_container_width=True)
    
else:
    st.info("Waiting for data... No potholes detected yet!")