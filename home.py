import streamlit as st
import pymongo
from datetime import date
import base64
import os
import smtplib
from email.mime.text import MIMEText

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Centralized Registration",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- HELPER FUNCTIONS ---

def send_confirmation_email(email_id, name):
    """Sends a registration confirmation email."""
    sender_email = 'teamnexusofficial25@gmail.com'
    sender_password = 'qkmm yqcq vqtm vmoq'
    subject = "✅ Registration Successful - Welcome to Team Nexus!"
    body = f"""Hi {name},

Welcome aboard! 

Your registration with Team Nexus was successful. We are thrilled to have you as part of our community.

You can now proceed to log in.

Best regards,
Team Nexus
"""
    message = MIMEText(body)
    message["Subject"], message["From"], message["To"] = subject, sender_email, email_id
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email_id, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send confirmation email: {e}")
        return False

def get_image_as_base64(path):
    """Encodes a local image file into a base64 string for CSS."""
    if not os.path.exists(path):
        st.error(f"Image not found at path: {path}")
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def load_css(image_path):
    """Applies custom CSS styling and a background image."""
    base64_image = get_image_as_base64(image_path)
    background_style = f"background-image: url(data:image/jpeg;base64,{base64_image});" if base64_image else "background-color: #2e2e2e;"
    
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        
        .stApp {{
            {background_style}
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        .main-title {{
            font-family: 'Gaegu', cursive; font-size: 3.5rem; text-align: center;
            color: black; padding-bottom: 1rem;
        }}
        
        div[data-testid="stForm"], div[data-testid="stVerticalBlock"] {{
            background-color: rgba(46, 51, 56, 0.85);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            padding: 2rem 3rem;
        }}
        
        .stTextInput label, .stDateInput label, .stSelectbox label {{
            color: #FFFFFF !important; font-weight: bold;
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem;
        }}
        
        .stButton>button {{
            background-color: #6c47ff; color: white; border-radius: 12px;
            border: none; padding: 12px 28px; font-weight: bold;
            transition: all 0.3s ease; display: block; margin: 1rem auto 0 auto;
            font-family: 'Source Code Pro', monospace;
        }}
        .stButton>button:hover {{
            background-color: #5837d4; box-shadow: 0 0 20px #6c47ff;
            transform: scale(1.05);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def hide_sidebar():
    """Hides the default Streamlit sidebar."""
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

# --- INITIALIZATION ---
hide_sidebar()
load_css("pic4.jpg")

# --- MONGODB CONNECTION ---
MONGO_CONNECTION_STRING = "mongodb+srv://soumyadeepdas2511:dxRsCQDq7YQSc1vh@cluster0.zmm4k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

@st.cache_resource
def get_mongo_client():
    try:
        client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        return None

client = get_mongo_client()
if not client:
    st.stop()
db = client.study_app_db
users_collection = db.users

# --- SESSION STATE ---
if 'registration_complete' not in st.session_state:
    st.session_state.registration_complete = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'email_failed' not in st.session_state:
    st.session_state.email_failed = False

# --- PAGE LAYOUT ---
st.markdown('<h1 class="main-title">Registration Info</h1>', unsafe_allow_html=True)

if not st.session_state.registration_complete:
    col1, col2 = st.columns([1.5, 1.75], gap="large")

    with col1:
        st.image("pic1.png", use_container_width=True)

    with col2:
        with st.form("registration_form"):
            name = st.text_input("🧑‍💼 Full Name")
            raw_username = st.text_input("👤 Choose a Username (e.g. 'nexus_user')")
            email = st.text_input("📧 Email Address")
            birthdate = st.date_input("🎂 Birthdate", min_value=date(1940, 1, 1), max_value=date.today())
            gender = st.selectbox("⚧️ Gender", ["Male", "Female", "Other", "Prefer not to say"])
            submitted = st.form_submit_button("🚀 Launch Profile")
        
        if st.button("🔑 Log In Here", use_container_width=True):
            st.switch_page("pages/login.py")

    if submitted:
        if not name or not raw_username or not email:
            st.warning("⚠️ Name, Username, and Email are required fields.")
        else:
            username = "#" + raw_username.lstrip('#')
            if users_collection.find_one({"email": email}):
                st.error("❌ This email address is already registered.")
            elif users_collection.find_one({"username": username}):
                st.error(f"❌ The username '{username}' is already taken.")
            else:
                today = date.today()
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
                user_data = {
                    "name": name, "username": username, "email": email,
                    "birthdate": birthdate.isoformat(), "age": age, "gender": gender,
                    "created_at": today.isoformat()
                }
                try:
                    users_collection.insert_one(user_data)
                    if not send_confirmation_email(email, name):
                        st.session_state.email_failed = True
                    st.session_state.registration_complete = True
                    st.session_state.user_name = name
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred during registration: {e}")
else:
    # Use st.container() for a reliable way to group elements for styling
    with st.container():
        st.balloons()
        st.success(f"✅ Welcome aboard, {st.session_state.user_name}!")
        st.info("Your registration is complete. You can now log in.")
        if st.session_state.email_failed:
            st.warning("Your account was created, but we couldn't send a confirmation email.")
        
        if st.button("🔑 Proceed to Login", use_container_width=True):
            st.switch_page("pages/login.py")
