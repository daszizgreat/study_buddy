import streamlit as st
import pymongo
from pymongo import MongoClient
import base64
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
import time
import html

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Create a Room",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- FUNCTIONS ---

def send_invitation_email(recipient_email, room_name, access_code, owner_name):
    """Sends an invitation email with hardcoded credentials."""
    
    # --- MODIFICATION: Hardcoded Email Credentials ---
    # IMPORTANT: Replace these placeholders with your actual Gmail address and a
    # 16-character Google App Password. Do NOT use your regular password.
    # Storing credentials like this is a security risk.
    sender_email = 'teamnexusofficial25@gmail.com'  # Your email
    sender_password = 'qkmm yqcq vqtm vmoq'  # e.g., "abcd efgh ijkl mnop"
    
    if sender_email == "your_email@gmail.com":
        st.error("Email sending is not configured. Please update the sender credentials in the code.")
        return False

    subject = f"📧 You're Invited to Join '{room_name}' on Team Nexus!"
    body = f"""Hi there,

You have been invited by {owner_name} to join their study room, '{room_name}'.

To join the room, please use the following access code:

Access Code: {access_code}

We are excited to have you collaborate with us!

Best regards,
Team Nexus
"""
    message = MIMEText(body)
    message["Subject"], message["From"], message["To"] = subject, sender_email, recipient_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send invitation to {recipient_email}: {e}")
        return False

def get_image_as_base64(path):
    """Gets a local image file as a base64 string."""
    if not os.path.exists(path): return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_css(image_path):
    """Loads custom CSS for styling the page."""
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
        .main-title {{ font-family: 'Gaegu', cursive; font-size: 3.5rem; text-align: center; color: white; padding-bottom: 2rem; text-shadow: 2px 2px 6px rgba(0,0,0,0.7); }}
        [data-testid="stForm"] {{ 
            background-color: rgba(10, 5, 25, 0.65); 
            backdrop-filter: blur(12px) saturate(180%); 
            border-radius: 25px; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            padding: 2rem 3rem; 
            max-width: 650px; /* Constrain form width for better appearance */
            margin: auto; /* Center the form */
        }}
        h3, .stTextInput label {{ color: #FFFFFF; font-family: 'Source Code Pro', monospace; text-shadow: 1px 1px 4px rgba(0,0,0,0.6); }}
        .stButton>button {{ background-image: linear-gradient(to right, #00c6ff 0%, #0072ff 51%, #00c6ff 100%); color: white; border-radius: 12px; border: none; padding: 15px 30px; font-weight: bold; transition: 0.5s; background-size: 200% auto; display: block; margin: 2rem auto 0 auto; font-family: 'Source Code Pro', monospace; width: 100%; }}
        .stButton>button:hover {{ background-position: right center; transform: scale(1.05); }}
        [data-testid="stSidebar"] {{ display: none; }}
    </style>
    """, unsafe_allow_html=True)

def generate_access_code():
    """Generates a random 5-character alphanumeric code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

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


# --- INITIALIZE APP ---
IMAGE_PATH = "pic6.jpg" 
load_css(IMAGE_PATH)
st.markdown('<h1 class="main-title">Create a New Room</h1>', unsafe_allow_html=True)


# --- AUTHENTICATION CHECK ---
if 'logged_in_email' not in st.session_state or not st.session_state.logged_in_email:
    st.warning("⚠️ You must be logged in to create a room.")
    st.page_link("home.py", label="Go to Home/Login", icon="🏠")
    st.stop()

# Get logged-in user's data
user_email = st.session_state.logged_in_email
user_profile = users_collection.find_one({"email": user_email})
user_name = user_profile.get("name", "A colleague") if user_profile else "A colleague"


# --- PAGE LAYOUT & LOGIC ---
with st.form("create_room_form"):
    st.header("Enter Room Details")
    room_name = st.text_input("Room Name *", placeholder="e.g., Quantum Physics Study Group")
    st.write("Invite members by email (optional, up to 5):")
    email1 = st.text_input("Member 1 Email", key="e1")
    email2 = st.text_input("Member 2 Email", key="e2")
    email3 = st.text_input("Member 3 Email", key="e3")
    email4 = st.text_input("Member 4 Email", key="e4")
    email5 = st.text_input("Member 5 Email", key="e5")
    create_submitted = st.form_submit_button("Create Room & Send Invites")

if create_submitted:
    if not room_name:
        st.warning("⚠️ Room Name is a required field.")
    else:
        invited_emails = [e.strip() for e in [email1, email2, email3, email4, email5] if e.strip()]
        if len(invited_emails) > 5:
            st.error("❌ You can only invite a maximum of 5 members.")
        else:
            access_code = generate_access_code()
            new_room = {
                "room_name": html.escape(room_name), 
                "access_code": access_code, 
                "owner_email": user_email,
                "members": [user_email], 
                "pending_invites": invited_emails
            }
            try:
                rooms_collection.insert_one(new_room)
                st.success(f"✅ Room '{html.escape(room_name)}' created successfully!")
                st.info(f"Your 5-digit access code is: **{access_code}**")
                
                if invited_emails:
                    with st.spinner("Sending invites..."):
                        for email in invited_emails:
                            send_invitation_email(email, room_name, access_code, user_name)
                
                st.balloons()
                
                # Set session state for the next page (timetable setup)
                st.session_state['current_room_name'] = room_name
                st.session_state['current_access_code'] = access_code
                
                with st.spinner("Redirecting you to timetable setup..."):
                    time.sleep(2)
                    st.switch_page("pages/edit_table.py")
            except Exception as e:
                st.error(f"An error occurred while creating the room: {e}")