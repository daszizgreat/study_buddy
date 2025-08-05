# filename: pages/setup_timetable.py

import streamlit as st
import pymongo
from pymongo import MongoClient
import base64
import os
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Setup Timetable",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- UI AND STYLING FUNCTIONS ---
def get_image_as_base64(path):
    """Encodes a local image file into a base64 string."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_css(image_path):
    """Loads the custom CSS for the page."""
    img_base64 = get_image_as_base64(image_path)
    background_style = f"""
        background-image: url(data:image/jpeg;base64,{img_base64});
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """ if img_base64 else "background-color: #1a1a1a;"
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        
        .stApp {{ {background_style} }}
        
        .main-title {{
            font-family: 'Gaegu', cursive; font-size: 3.5rem; text-align: center;
            color: white; padding-bottom: 2rem; text-shadow: 2px 2px 6px rgba(0,0,0,0.7);
        }}
        
        [data-testid="stForm"] {{
            background-color: rgba(10, 5, 25, 0.65);
            backdrop-filter: blur(12px) saturate(180%);
            border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem 3rem;
        }}
        
        h3, .stTextInput label {{
            color: #FFFFFF; font-family: 'Source Code Pro', monospace;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.6);
        }}
        
        .stButton>button {{
            background-image: linear-gradient(to right, #56ab2f 0%, #a8e063 51%, #56ab2f 100%);
            color: white; border-radius: 12px; border: none; padding: 15px 30px;
            font-weight: bold; transition: 0.5s; background-size: 200% auto;
            display: block; margin: 2rem auto 0 auto; font-family: 'Source Code Pro', monospace;
            width: 50%;
        }}
        
        .stButton>button:hover {{ background-position: right center; transform: scale(1.05); }}
    </style>
    """, unsafe_allow_html=True)

# --- MONGODB CONNECTION ---
# --- MONGODB CONNECTION ---
@st.cache_resource
def get_mongo_client():
    """Establishes and caches the MongoDB connection."""
    try:
        # --- MODIFICATION: Hardcoded MongoDB Connection String ---
        # Storing credentials like this is a security risk.
        client = MongoClient('mongodb+srv://soumyadeepdas2511:dxRsCQDq7YQSc1vh@cluster0.zmm4k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        return None

client = get_mongo_client()
if client:
    db = client.study_app_db
    rooms_collection = db.rooms
    users_collection = db.users
else:
    st.error("Database connection failed. The app cannot continue.")
    st.stop()



# --- APP LAYOUT AND LOGIC ---
IMAGE_PATH = "pic6.jpg" 
load_css(IMAGE_PATH)

st.markdown('<h1 class="main-title">Setup Your Weekly Timetable</h1>', unsafe_allow_html=True)

if 'current_access_code' in st.session_state and 'current_room_name' in st.session_state:
    room_name = st.session_state['current_room_name']
    access_code = st.session_state['current_access_code']
    
    st.header(f"Configuring Timetable for Room: '{room_name}'")

    with st.form("setup_timetable_form"):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        timetable_cols = st.columns(len(days))
        
        task_input_keys = []
        for i, day in enumerate(days):
            with timetable_cols[i]:
                st.markdown(f"**{day}**")
                for j in range(6):
                    default_tasks = ['DSA', 'React Js', 'Aptitude', 'Projects', 'LEET', 'GYM']
                    key = f"task_{day}_{j}"
                    st.text_input(f"Slot {j+1}", key=key, value=default_tasks[j], label_visibility="collapsed")
                    task_input_keys.append(key)

        submitted = st.form_submit_button("Save Timetable and Finish Setup")

    if submitted:
        progress_bar = st.progress(0, text="Saving timetable...")
        
        timetable_data = {}
        key_iterator = iter(task_input_keys)
        for day in days:
            day_tasks = [st.session_state[next(key_iterator)] for _ in range(6)]
            timetable_data[day] = day_tasks
        
        progress_bar.progress(50, text="Updating database...")
        
        try:
            result = rooms_collection.update_one(
                {"access_code": access_code},
                {"$set": {"timetable": timetable_data}}
            )
            
            if result.matched_count > 0:
                progress_bar.progress(100, text="Success! Redirecting...")
                st.success(f"✅ Timetable for '{room_name}' has been saved successfully!")
                st.balloons()
                
                # Clean up session state
                del st.session_state['current_access_code']
                del st.session_state['current_room_name']
                
                # Wait for 2 seconds before switching page
                time.sleep(2) 
                st.switch_page("pages/main_home.py")
            else:
                progress_bar.empty()
                st.error("Could not find the room to update. Please try creating it again.")

        except Exception as e:
            progress_bar.empty()
            st.error(f"An error occurred while saving the timetable: {e}")

else:
    st.warning("⚠️ You need to create a room first before setting up a timetable.")
    st.page_link("pages/create_join_room.py", label="Go to Create Room Page", icon="👈")
