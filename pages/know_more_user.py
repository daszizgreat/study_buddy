import streamlit as st
import base64
import os
import time
from pymongo import MongoClient  # --- MODIFICATION: Ensure this import is here ---

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Complete Your Profile",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- SIDEBAR HIDING FUNCTION ---
def hide_sidebar():
    """Hides the default Streamlit sidebar."""
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

hide_sidebar()

# --- HELPER & CSS FUNCTIONS (Unchanged) ---
def get_image_as_base64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def load_css(image_path):
    base64_image = get_image_as_base64(image_path)
    background_style = f"""
        background-image: url(data:image/jpeg;base64,{base64_image});
        background-size: cover; background-repeat: no-repeat; background-attachment: fixed;
    """ if base64_image else "background-color: #1a1a1a;"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        .stApp {{ {background_style} }}
        .main-title {{ font-family: 'Gaegu', cursive; font-size: 3.5rem; text-align: center; color: white; padding-bottom: 1rem; }}
        [data-testid="stForm"] {{ background-color: rgba(40, 45, 50, 0.85); backdrop-filter: blur(16px) saturate(180%); border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 2rem 3rem; }}
        h3 {{ color: #FFFFFF; font-family: 'Source Code Pro', monospace; text-transform: uppercase; letter-spacing: 1.5px; padding-top: 1rem; }}
        .stTextInput label, .stTextArea label {{ color: #FFFFFF !important; font-weight: bold; font-family: 'Source Code Pro', monospace; font-size: 1.1rem; }}
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {{ font-family: 'Source Code Pro', monospace; font-size: 1.1rem; }}
        .stButton>button {{ background-image: linear-gradient(to right, #FFFFFF 0%, #FFFFFF 51%, #000000 100%); color: black; border-radius: 12px; border: none; padding: 15px 30px; font-weight: bold; transition: 0.5s; background-size: 200% auto; display: block; margin: 1.5rem auto 0 auto; font-family: 'Source Code Pro', monospace; }}
        .stButton>button:hover {{ background-position: right center; color: #fff; text-decoration: none; transform: scale(1.05); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- MONGODB CONNECTION ---
@st.cache_resource
def get_mongo_client():
    """Establishes a connection to MongoDB."""
    try:
        # BEST PRACTICE: Use st.secrets to store your connection string
        # client = MongoClient(st.secrets["mongo"]["uri"])
        client = MongoClient('mongodb+srv://soumyadeepdas2511:dxRsCQDq7YQSc1vh@cluster0.zmm4k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        return None

# --- MODIFICATION: Combined database connection logic into one block ---
client = get_mongo_client()
if client:
    db = client.study_app_db
    users_collection = db.users
    # Define rooms_collection here if you need it on this page
    # rooms_collection = db.rooms 
else:
    st.error("Database connection failed. The app cannot continue.")
    st.stop()

# --- PAGE SETUP ---
IMAGE_PATH = "pic4.jpg" 
load_css(IMAGE_PATH)
st.markdown('<h1 class="main-title">Complete Your Profile</h1>', unsafe_allow_html=True)

# --- PROFILE FORM ---
with st.form("profile_details_form"):
    st.subheader("Account Identifier")
    email = st.text_input(
        "✉️ Your Email Address *", 
        value=st.session_state.get('logged_in_email', ''), 
        help="This field is required to save or update your profile."
    )
    st.markdown("---")
    
    st.subheader("Professional Links")
    linkedin_id = st.text_input("🔗 LinkedIn ID")
    leetcode_id = st.text_input("💻 LeetCode ID")
    github_id = st.text_input("🐙 GitHub ID")
    
    st.subheader("Personal Details")
    introduction = st.text_area("👋 Introduction", height=150)
    goals = st.text_area("🎯 Goals", height=150)
    likes = st.text_area("❤️ Top 3 Likes", height=100)

    st.subheader("Location & Education")
    college = st.text_input("🎓 College/University")
    state = st.text_input("📍 State")
    country = st.text_input("🌍 Country")

    submitted = st.form_submit_button("Save Profile")

if submitted:
    if not email:
        st.warning("⚠️ Please provide your email address to save the profile.")
    else:
        profile_data = {
            "linkedin_id": linkedin_id, "leetcode_id": leetcode_id,
            "github_id": github_id, "introduction": introduction,
            "goals": goals, "likes": likes,
            "college": college, "state": state, "country": country,
        }
        
        try:
            users_collection.update_one(
                {"email": email},
                {"$set": profile_data},
                upsert=True
            )
            st.success("✅ Your profile has been saved successfully!")
            st.balloons()
            
            with st.spinner("Redirecting to the login page..."):
                time.sleep(2)
                st.switch_page("login.py")
                
        except Exception as e:
            st.error(f"An error occurred while saving your profile: {e}")