import streamlit as st
from pymongo import MongoClient
import base64
import html  # Used to sanitize data
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="My Profile",
    page_icon="👤",
    layout="wide"
)

# --- HELPER FUNCTIONS ---
def get_base64_image(image_path):
    """Reads a local image and returns it as a base64 encoded string."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        st.warning(f"Image not found at {image_path}. Using fallback color.")
        return None

def calculate_age(birthdate_str):
    """Calculates age from a birthdate string (YYYY-MM-DD)."""
    if not birthdate_str or birthdate_str == 'N/A':
        return "N/A"
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age
    except (ValueError, TypeError):
        return "N/A"

def load_css(image_path):
    """Loads custom CSS for styling the page, including a background image."""
    img_base64 = get_base64_image(image_path)
    background_style = f"""
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """ if img_base64 else "background-color: #1a1c20;"

    st.markdown(f"""
    <style>
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
        .stApp {{ {background_style} }}
        .main-title {{
            color: white; text-align: center; font-size: 3rem;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7); padding: 20px 0;
        }}
        .profile-card {{
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px) saturate(150%);
            border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.125);
            padding: 1.5rem 2rem; color: #f0f2f6;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        .card-header {{
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 1rem;
        }}
        .user-identity {{ display: flex; align-items: center; }}
        .user-identity .icon {{ font-size: 3rem; color: #38bdf8; margin-right: 15px; }}
        .user-info .name {{ font-size: 1.5rem; font-weight: bold; }}
        .user-info .username {{ font-size: 1rem; color: #9ca3af; }}
        .social-links a {{
            color: #9ca3af; font-size: 1.4rem; margin-left: 15px; text-decoration: none;
            transition: all 0.3s ease;
        }}
        .social-links a:hover {{ color: #38bdf8; transform: scale(1.1); }}
        .section-title {{
            font-weight: bold; font-size: 1.1rem; color: #ffffff;
            margin-top: 1.5rem; margin-bottom: 0.75rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 0.25rem;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 0.75rem;
        }}
        .info-box {{
            background: rgba(0, 0, 0, 0.25); border-radius: 8px;
            padding: 0.75rem; display: flex; align-items: center;
        }}
        .info-box i {{ margin-right: 12px; color: #9ca3af; width: 20px; text-align: center; }}
        .info-box span {{ color: #e5e7eb; word-break: break-word; }}
    </style>
    """, unsafe_allow_html=True)

# --- MONGODB CONNECTION ---
MONGO_CONNECTION_STRING = "mongodb+srv://soumyadeepdas2511:dxRsCQDq7YQSc1vh@cluster0.zmm4k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

@st.cache_resource
def get_mongo_client():
    try:
        client = MongoClient(MONGO_CONNECTION_STRING)  # ✅ Fixed
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

# --- MAIN APP LOGIC ---
load_css("pic7.jpg")

if 'logged_in_email' not in st.session_state or not st.session_state.logged_in_email:
    st.warning("⚠️ Please log in to view your profile.")
    st.stop()

user_data = users_collection.find_one({"email": st.session_state['logged_in_email']})
st.markdown('<h1 class="main-title">My Profile</h1>', unsafe_allow_html=True)

if user_data:
    _, center_col, _ = st.columns([1, 2.5, 1])
    with center_col:
        name = html.escape(str(user_data.get("name", "N/A")))
        username = html.escape(str(user_data.get("username", "N/A")))
        linkedin = html.escape(str(user_data.get("linkedin_id", "#")))
        github = html.escape(str(user_data.get("github_id", "#")))
        leetcode = html.escape(str(user_data.get("leetcode_id", "#")))
        intro = html.escape(str(user_data.get('introduction', 'Not provided.')))
        email = html.escape(str(user_data.get('email', 'N/A')))
        birthdate = user_data.get('birthdate')
        gender = html.escape(str(user_data.get('gender', 'N/A')))
        created_at = html.escape(str(user_data.get('created_at', 'N/A')))
        college = html.escape(str(user_data.get('college', 'N/A')))
        state = html.escape(str(user_data.get('state', 'N/A')))
        country = html.escape(str(user_data.get('country', 'N/A')))
        goals = html.escape(str(user_data.get('goals', 'N/A')))
        likes = html.escape(str(user_data.get('likes', 'N/A')))

        age = calculate_age(birthdate)
        display_birthdate = html.escape(str(birthdate or 'N/A'))

        card_html = f"""
            <div class="profile-card">
                <div class="card-header">
                    <div class="user-identity">
                        <i class="fas fa-user-circle icon"></i>
                        <div class="user-info">
                            <div class="name">{name}</div>
                            <div class="username">@{username}</div>
                        </div>
                    </div>
                    <div class="social-links">
                        <a href='{linkedin}' target='_blank' title="LinkedIn"><i class="fab fa-linkedin"></i></a>
                        <a href='{github}' target='_blank' title="GitHub"><i class="fab fa-github"></i></a>
                        <a href='{leetcode}' target='_blank' title="LeetCode"><i class="fas fa-code"></i></a>
                    </div>
                </div>
                <div class="section-title">Introduction</div>
                <div class="info-box" style="grid-column: 1 / -1;"><i class="fas fa-quote-left"></i><span>{intro}</span></div>
                <div class="section-title">Key Information</div>
                <div class="info-grid">
                    <div class="info-box"><i class="fas fa-envelope"></i><span>{email}</span></div>
                    <div class="info-box"><i class="fas fa-birthday-cake"></i><span>{display_birthdate} (Age: {age})</span></div>
                    <div class="info-box"><i class="fas fa-venus-mars"></i><span>{gender}</span></div>
                    <div class="info-box"><i class="fas fa-calendar-check"></i><span>Joined: {created_at}</span></div>
                </div>
                <div class="section-title">Academics & Location</div>
                <div class="info-grid">
                    <div class="info-box"><i class="fas fa-graduation-cap"></i><span>{college}</span></div>
                    <div class="info-box"><i class="fas fa-map-marker-alt"></i><span>{state}, {country}</span></div>
                </div>
                <div class="section-title">Personal</div>
                <div class="info-grid">
                    <div class="info-box"><i class="fas fa-crosshairs"></i><span>Goals: {goals}</span></div>
                    <div class="info-box"><i class="fas fa-heart"></i><span>Likes: {likes}</span></div>
                </div>
            </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.error("Could not retrieve your profile. Please try logging in again or check if a profile has been created for this account.")

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
