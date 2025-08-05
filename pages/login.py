import streamlit as st
import pymongo
import base64
import os
import smtplib
from email.mime.text import MIMEText
import time
import random

# --- OTP & EMAIL FUNCTIONS ---
def generate_otp(length=6):
    """Generates a random 6-digit OTP."""
    return ''.join(random.choice("0123456789") for _ in range(length))

def send_otp_via_email(email_id, user_name, otp):
    """Sends the OTP to the user's email address."""
    sender_email = 'teamnexusofficial25@gmail.com'  # Your email
    sender_password = 'qkmm yqcq vqtm vmoq'  # Your email app password
    subject = "Your One-Time Password (OTP) for Sign In"
    body = f"""Hello {user_name},

Your One-Time Password (OTP) to sign in is:

OTP: {otp}

This password is valid for 10 minutes. Please do not share it with anyone.

Best regards,
Team Nexus
"""
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = email_id
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email_id, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send OTP email: {e}")
        return False

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Sign In",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- FUNCTION TO ENCODE LOCAL IMAGE ---
def get_image_as_base64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# --- CUSTOM CSS (WITH CENTERING) ---
def load_css(image_path):
    base64_image = get_image_as_base64(image_path)
    background_style = f"""
        background-image: url(data:image/jpeg;base64,{base64_image});
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """ if base64_image else "background-color: #1a1a1a;"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        .stApp {{ {background_style} }}
        .main-title {{
            font-family: 'Gaegu', cursive; font-size: 4rem; text-align: center;
            color: white; padding-bottom: 1rem;
        }}
        [data-testid="stForm"] {{
            background-color: rgba(30, 35, 40, 0.8);
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2.5rem 3.5rem;
            text-align: center;
        }}
        .stTextInput label {{
            color: #FFFFFF !important; font-weight: bold;
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem; 
        }}
        div[data-testid="stTextInput"] input {{
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem;
            text-align: center;
        }}
        [data-testid="stInfo"] {{
            text-align: center;
        }}
        .stButton>button {{
            background-image: linear-gradient(to right, #FF512F 0%, #DD2476 51%, #FF512F 100%);
            color: white; border-radius: 12px;
            border: none; padding: 15px 30px; font-weight: bold;
            transition: 0.5s; background-size: 200% auto;
            display: block; margin: 1.5rem auto 0 auto;
            font-family: 'Source Code Pro', monospace;
        }}
        .stButton>button:hover {{
            background-position: right center;
            color: #fff; text-decoration: none;
            transform: scale(1.05);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

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
if client:
    db = client.study_app_db
    users_collection = db.users
else:
    st.stop()

# --- Initialize Session State ---
# Temporary state for the login process itself
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'otp_code' not in st.session_state:
    st.session_state.otp_code = ""
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
# NEW: Add a key to hold the phone number during login
if 'user_phone' not in st.session_state:
    st.session_state.user_phone = ""

# --- APP LAYOUT & LOGIC ---
IMAGE_PATH = r"pic5.jpg"
load_css(IMAGE_PATH)

st.markdown('<h1 class="main-title">Account Login</h1>', unsafe_allow_html=True)

# Step 1: Show the email/phone form if OTP has not been sent yet
if not st.session_state.otp_sent:
    with st.form("send_otp_form"):
        email = st.text_input("📧 Email Address")
        phone = st.text_input("📱 Phone Number")
        send_otp_button = st.form_submit_button("Send OTP")

    if send_otp_button:
        if not email:
            st.warning("⚠️ Please enter your email address.")
        else:
            user_data = users_collection.find_one({"email": email})
            if user_data:
                otp = generate_otp()
                user_name = user_data.get("name", "User")
                
                if send_otp_via_email(email, user_name, otp):
                    # Store details temporarily for verification
                    st.session_state.otp_sent = True
                    st.session_state.otp_code = otp
                    st.session_state.user_email = email
                    # NEW: Store phone number in the temporary state
                    st.session_state.user_phone = phone 
                    st.success("✅ OTP has been sent to your email!")
                    st.rerun()
            else:
                st.error("❌ No account found with this email. Please go to the registration page.")
else:
    # Step 2: Show the OTP verification form
    st.info(f"An OTP was sent to **{st.session_state.user_email}**. Please enter it below.")
    with st.form("verify_otp_form"):
        otp_input = st.text_input("🔑 Enter OTP", max_chars=6)
        verify_button = st.form_submit_button("Verify & Login")

    if verify_button:
        if otp_input == st.session_state.otp_code:
            st.success("✅ Login Successful! Redirecting...")
            st.balloons()
            
            # --- MODIFICATION: Remember the details for the next page ---
            # Store the verified email and phone number in new session state keys
            # that will persist across pages.
            st.session_state['logged_in_email'] = st.session_state.user_email
            st.session_state['logged_in_phone'] = st.session_state.user_phone
            
            # Clean up the temporary OTP keys
            del st.session_state.otp_sent
            del st.session_state.otp_code
            del st.session_state.user_email
            del st.session_state.user_phone
            
            time.sleep(2)
            # --- MODIFICATION: Redirect to the new main home page ---
            st.switch_page("pages/main_home.py")
        else:
            st.error("❌ Invalid OTP. Please try again.")
def hide_sidebar():
    """Hides the default Streamlit sidebar."""
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

# --- Call the function at the top of your app's script ---
hide_sidebar()