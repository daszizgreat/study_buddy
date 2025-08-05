import streamlit as st
import pymongo
from datetime import date
import base64
import os
import smtplib
from email.mime.text import MIMEText

# --- EMAIL SENDING FUNCTION (FOR CONFIRMATION) ---
def send_confirmation_email(email_id, name):
    sender_email = 'teamnexusofficial25@gmail.com'  # Your email
    sender_password = 'qkmm yqcq vqtm vmoq'  # Your email app password
    subject = "✅ Registration Successful - Welcome to Team Nexus!"
    body = f"""Hi {name},

Welcome aboard! 

Your registration with Team Nexus was successful. We are thrilled to have you as part of our community.

You can now proceed to log in or access our services.

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
        print(f"Failed to send confirmation email: {e}")
        return False

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Centralized Registration",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- FUNCTION TO ENCODE LOCAL IMAGE ---
def get_image_as_base64(path):
    """Encodes a local image file into a base64 string."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# --- CUSTOM CSS ---
def load_css(image_path):
    base64_image = get_image_as_base64(image_path)
    background_style = f"""
        background-image: url(data:image/jpeg;base64,{base64_image});
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """ if base64_image else "background-color: #2e2e2e;"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        .stApp {{ {background_style} }}
        .main-title {{
            font-family: 'Gaegu', cursive; font-size: 3.5rem; text-align: center;
            color: black; padding-bottom: 1rem;
        }}
        
        /* --- CSS FIX: Reverted to the original selector that targets the box --- */
        [data-testid="stHorizontalBlock"] {{
            background-color: rgba(46, 51, 56, 0.75);
            backdrop-filter: blur(15px) saturate(150%);
            -webkit-backdrop-filter: blur(15px) saturate(150%);
            border-radius: 20px; 
            border: 1px solid rgba(255, 255, 255, 0.18);
            padding: 2rem 3rem; 
            transform: scale(1.1);
            margin-top: 5rem; 
            margin-bottom: 5rem;
        }}

        .stTextInput label, .stDateInput label, .stSelectbox label {{
            color: #FFFFFF !important; font-weight: bold;
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem; 
        }}
        div[data-testid="stTextInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem;
        }}
        .stButton>button {{
            background-color: #6c47ff; color: white; border-radius: 12px;
            border: none; padding: 12px 28px; font-weight: bold;
            transition: all 0.3s ease; display: block; margin: 0 auto;
            margin-top: 1rem; font-family: 'Source Code Pro', monospace;
        }}
        .stButton>button:hover {{
            background-color: #5837d4; box-shadow: 0 0 20px #6c47ff;
            transform: scale(1.05);
        }}
        .stButton>button[kind="secondary"] {{
            background-color: #222222;
            border: 1px solid #6c47ff;
        }}
        .stButton>button[kind="secondary"]:hover {{
            background-color: #333333;
            border: 1px solid #FFFFFF;
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

# --- INITIALIZE SESSION STATE ---
if 'registration_complete' not in st.session_state:
    st.session_state.registration_complete = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'email_failed' not in st.session_state:
    st.session_state.email_failed = False


# --- APP LAYOUT ---
IMAGE_PATH = r"pic4.jpg"
load_css(IMAGE_PATH)

st.markdown('<h1 class="main-title">Registration Info</h1>', unsafe_allow_html=True)

# --- PAGE LOGIC ---
# If registration is NOT complete, show the form
if not st.session_state.registration_complete:
    col1, col2 = st.columns([1.5, 1.75], gap="large")

    with col1:
        st.image("pic1.png", use_container_width=True)

    with col2:
        with st.form("registration_form"):
            name = st.text_input("🧑‍💼 Full Name", key="name")
            raw_username = st.text_input("👤 Choose a Username (e.g. 'nexus_user')", key="username")
            email = st.text_input("📧 Email Address", key="email")
            birthdate = st.date_input("🎂 Birthdate", min_value=date(1940, 1, 1), max_value=date.today())
            gender = st.selectbox("⚧️ Gender", ["Male", "Female", "Other", "Prefer not to say"])
            submitted = st.form_submit_button("🚀 Launch Profile")
        
        st.markdown("<p style='text-align:center; color: white; margin-top: 1.5rem;'>Already have an account?</p>", unsafe_allow_html=True)
        if st.button("🔑 Log In Here", use_container_width=True, key="login_redirect", type="secondary"):
            st.switch_page("pages/login.py")

    if submitted:
        if not name or not raw_username or not email:
            st.warning("⚠️ Name, Username, and Email are required fields.")
        else:
            username = "#" + raw_username.lstrip('#') 
            existing_email = users_collection.find_one({"email": email})
            existing_user = users_collection.find_one({"username": username})

            if existing_email:
                st.error(f"❌ This email address is already registered.")
            elif existing_user:
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
                    email_sent = send_confirmation_email(email_id=email, name=name)
                    if not email_sent:
                        st.session_state.email_failed = True

                    st.session_state.registration_complete = True
                    st.session_state.user_name = name
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred during registration: {e}")

# If registration IS complete, show the success message and button
else:
    # --- LAYOUT FIX: Wrap the success content in a column so the CSS can target it ---
    # This creates the [data-testid="stHorizontalBlock"] that our CSS styles.
    cols = st.columns(1)
    with cols[0]:
        st.balloons()
        st.success(f"✅ Welcome aboard, {st.session_state.user_name}!")
        st.info("Your registration is complete. You can now log in or finish setting up your profile.")

        if st.session_state.email_failed:
            st.warning("Your account was created, but we couldn't send a confirmation email.")

        btn_col1, btn_col2 = st.columns(2)

        
        with btn_col2:
            if st.button("📝 Complete Your Profile", use_container_width=True):
                st.switch_page("pages/know_more_user.py")
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