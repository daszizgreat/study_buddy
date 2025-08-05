import streamlit as st
import pymongo
from pymongo import MongoClient
import base64
import os
import html
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- HELPER FUNCTIONS ---

@st.cache_resource
def get_mongo_client():
    """Establishes and caches the MongoDB connection."""
    MONGO_CONNECTION_STRING = "mongodb+srv://soumyadeepdas2511:dxRsCQDq7YQSc1vh@cluster0.zmm4k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        return None

def get_image_as_base64(path):
    """Reads a local image and returns it as a base64 encoded string."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def load_css(image_path):
    """Loads custom CSS for styling the page, including a background image."""
    base64_image = get_image_as_base64(image_path)
    background_style = f"""
        background-image: url(data:image/jpeg;base64,{base64_image});
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """ if base64_image else "background-color: #1c1c1c;"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        
        .stApp {{ {background_style} }}
        [data-testid="stSidebar"] {{ display: none; }}

        .main-title {{
            font-family: 'Gaegu', cursive; font-size: 3.5rem;
            color: white; text-shadow: 2px 2px 4px #000000;
        }}
        
        /* CORRECT METHOD: Styling the native Streamlit container */
        div[data-testid="stContainer"] {{
            /* This selector targets the element created by st.container() */
            background-color: rgba(28, 29, 33, 0.9) !important;
            border-radius: 15px !important;
            border: 2px solid red !important; /* DEBUG: Red border to confirm style is applied */
            padding: 2rem !important;
            margin-top: 1rem !important;
        }}

        .profile-container {{
            display: flex; justify-content: flex-end;
            align-items: center; height: 100%;
        }}

        .profile-container .stButton>button {{
            background: rgba(70, 70, 80, 0.5); color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px;
            padding: 8px 16px; font-family: 'Source Code Pro', monospace;
            font-weight: bold; transition: all 0.3s ease;
        }}

        .profile-container .stButton>button:hover {{
            background: rgba(90, 90, 100, 0.7);
            border-color: rgba(255, 255, 255, 0.4);
            transform: translateY(-2px);
        }}

        /* Styling for all buttons within the styled container */
        div[data-testid="stContainer"] .stButton>button, 
        div[data-testid="stContainer"] [data-testid="stFormSubmitButton"] > button {{
            background-image: linear-gradient(to right, #232526 0%, #414345 51%, #232526 100%);
            color: white; border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px; padding: 18px; 
            font-family: 'Source Code Pro', monospace; transition: 0.5s;
            background-size: 200% auto; width: 100%; font-size: 1.1rem;
        }}

        div[data-testid="stContainer"] .stButton>button:hover, 
        div[data-testid="stContainer"] [data-testid="stFormSubmitButton"] > button:hover {{
            background-position: right center;
            border-color: rgba(255, 255, 255, 0.3);
        }}
        
        div[data-testid="stContainer"] h3 {{
             font-family: 'Source Code Pro', monospace; color: white; text-align: center;
             padding-bottom: 1rem;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# --- INITIALIZE APP & AUTHENTICATION ---
IMAGE_PATH = "pic4.jpg" 
load_css(IMAGE_PATH)

if 'logged_in_email' not in st.session_state or not st.session_state.logged_in_email:
    st.warning("⚠️ Please log in to access your dashboard.")
    st.page_link("home.py", label="Go to Login Page", icon="🏠")
    st.stop()

client = get_mongo_client()
if not client: st.stop()

db = client.study_app_db
users_collection = db.users
rooms_collection = db.rooms
user_email = st.session_state.logged_in_email

user_data = users_collection.find_one({"email": user_email})
if not user_data:
    st.error("Could not find user data. Please try logging in again.")
    st.stop()

user_name = html.escape(user_data.get("name", "User"))
user_hashtag = html.escape(user_data.get("username", "username"))

# --- HEADER LAYOUT ---
col_welcome, col_profile = st.columns([4, 1])
with col_welcome:
    st.markdown(f'<h1 class="main-title">Welcome, {user_name}!</h1>', unsafe_allow_html=True)
with col_profile:
    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    if st.button(f"👤 {user_hashtag}", key="profile_btn"):
        st.switch_page("pages/profile.py")
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN CONTENT AREA ---
# CORRECT METHOD: Using st.container() to properly group all elements
# This will create a single container that our CSS can style.
with st.container():
    col_create, col_join = st.columns(2, gap="large")

    with col_create:
        st.markdown("### ✨ Create a New Room")
        if st.button("Start a New Room from Scratch"):
            st.switch_page("pages/create_join_room.py")

    with col_join:
        with st.form("join_room_form"):
            st.markdown("### 🚪 Join an Existing Room")
            access_code_input = st.text_input("Enter Room Access Code *", placeholder="e.g., A4B8X", key="join_code")
            join_submitted = st.form_submit_button("Request to Join Room")

    st.markdown("<br>", unsafe_allow_html=True) 

    if st.button("👁️ View My Active Room"):
        st.switch_page("pages/myroom.py")

# --- FORM PROCESSING LOGIC (placed outside the layout) ---
if join_submitted:
    if not access_code_input:
        st.warning("⚠️ Please enter a room access code.")
    else:
        room = rooms_collection.find_one({"access_code": access_code_input.upper().strip()})
        
        if not room:
            st.error("❌ Invalid access code. No room found with that code.")
        elif user_email in room.get("members", []):
            st.info("You are already a member of this room. Redirecting...")
            st.session_state['access_code'] = room['access_code']
            time.sleep(2)
            st.switch_page("pages/myroom.py")
        elif len(room.get("members", [])) >= 6:
            st.error("❌ This room is already full (1 owner + 5 members).")
        elif user_email in room.get("pending_invites", []) or "pending_invites" not in room:
            try:
                update_query = {
                    "$push": {"members": user_email},
                    "$pull": {"pending_invites": user_email}
                }
                rooms_collection.update_one({"_id": room["_id"]}, update_query)
                
                st.success(f"🎉 Welcome! You have successfully joined '{room['room_name']}'.")
                st.balloons()
                
                st.session_state['access_code'] = room['access_code']
                with st.spinner("Redirecting you to the room..."):
                    time.sleep(2.5)
                    st.switch_page("pages/myroom.py")
            except Exception as e:
                st.error(f"An error occurred while joining the room: {e}")
        else:
            st.error("❌ You do not have an invitation for this room.")