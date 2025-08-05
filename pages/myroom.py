import streamlit as st
import pandas as pd
import datetime
from pymongo import MongoClient
import altair as alt
import base64
import os
import html

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Room Dashboard",
    page_icon="🏠",
    layout="wide"
)

# --- HELPER FUNCTIONS ---

def hide_sidebar():
    """Hides the default Streamlit sidebar by injecting custom CSS."""
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

def get_base64(image_path):
    """Reads a local image and returns it as a base64 encoded string."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def load_css(image_path):
    """Loads custom CSS with a glassmorphic theme."""
    img_base64 = get_base64(image_path)
    background_style = f"""
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover; background-repeat: no-repeat; background-attachment: fixed;
    """ if img_base64 else "background-color: #1a1c20;"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&display=swap');
        
        .stApp {{ {background_style} }}
        
        /* Main Font & Text Styles */
        h1, h2, h3, .stSelectbox, .stTextInput, .stMarkdown,
        div[data-testid="stMetricLabel"], div[data-testid="stMetricValue"] {{
            font-family: 'Gaegu', cursive; color: white; text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
        }}
        
        h1 {{ text-align: center; font-size: 3.5rem; }}
        h2 {{ text-align: center; font-size: 2.5rem; margin-bottom: 1rem;}}
        
        /* Target Streamlit's bordered container element */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(14px) saturate(150%);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.125);
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        
        .section-title {{
            font-size: 1.8rem; font-weight: 700;
            margin-top: 0; margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        /* Styling for st.dataframe inside the new container */
        div[data-testid="stStyledFullScreenFrame"] .stDataFrame {{ background-color: transparent; }}
        .stDataFrame th, .stDataFrame td {{ font-family: 'Gaegu', cursive; color: white; font-size: 1.1rem; }}
        .stDataFrame th {{ font-size: 1.2rem; font-weight: 700; }}
        
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }}
        
        div[data-testid="stMetric"] {{
            background: rgba(0, 0, 0, 0.25); backdrop-filter: blur(5px);
            border-radius: 12px; padding: 1rem; border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .grid-header {{ font-size: 1.4rem; font-weight: 700; color: #FFFFFF; text-align: center; }}
        .task-text {{ font-size: 1.2rem; color: #e5e7eb; padding-top: 8px; }}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_mongo_client():
    """Establishes and caches the MongoDB connection."""
    try:
        client = MongoClient('mongodb+srv://soumyadeepdas2511:dxRsCQDq7YQSc1vh@cluster0.zmm4k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        return None

def get_or_create_log(daily_logs_collection, date_str, tasks_for_day, members, room_access_code):
    log_id = f"{date_str}_{room_access_code}"
    log = daily_logs_collection.find_one({"_id": log_id})
    if log is None:
        st.toast(f"Creating new log for {date_str}...")
        new_log_tasks = []
        for task in tasks_for_day:
            if task not in ['—', 'BREAK']:
                task_doc = {"name": task, **{f"{member}_status": "Not Done" for member in members}}
                new_log_tasks.append(task_doc)
        new_log = {"_id": log_id, "tasks": new_log_tasks}
        daily_logs_collection.insert_one(new_log)
        return new_log
    return log

def update_task_status(daily_logs_collection, date_str, task_name, person, room_access_code):
    log_id = f"{date_str}_{room_access_code}"
    key = f"{person}_{task_name}"
    new_status = st.session_state[key]
    daily_logs_collection.update_one(
        {"_id": log_id, "tasks.name": task_name},
        {"$set": {f"tasks.$.{person}_status": new_status}}
    )
    st.toast(f"Set '{task_name}' to '{new_status}' for {person.split('@')[0].upper()}!", icon="👍")

def get_monthly_task_completions(daily_logs_collection, selected_month, members, room_access_code):
    group_stage = {"_id": "$tasks.name"}
    for member in members:
        clean_name = member.split('@')[0].capitalize()
        group_stage[f"{clean_name} Completions"] = {"$sum": {"$cond": [{"$eq": [f"$tasks.{member}_status", "Done"]}, 1, 0]}}
    pipeline = [{"$match": {"_id": {"$regex": f"^{selected_month}.*_{room_access_code}"}}}, {"$unwind": "$tasks"}, {"$group": group_stage}, {"$sort": {"_id": 1}}]
    return list(daily_logs_collection.aggregate(pipeline))

def get_daily_progress_data(daily_logs_collection, selected_month, members, room_access_code):
    group_stage = {"_id": {"$substrCP": ["$_id", 8, 2]}}
    for member in members:
        clean_name = member.split('@')[0].capitalize()
        group_stage[clean_name] = {"$sum": {"$cond": [{"$eq": [f"$tasks.{member}_status", "Done"]}, 1, 0]}}
    pipeline = [{"$match": {"_id": {"$regex": f"^{selected_month}.*_{room_access_code}"}}}, {"$unwind": "$tasks"}, {"$group": group_stage}, {"$sort": {"_id": 1}}]
    return list(daily_logs_collection.aggregate(pipeline))

# --- INITIALIZATION ---
hide_sidebar()
load_css("pic6.jpg")
client = get_mongo_client()
if not client: st.stop()
db = client.study_app_db
rooms_collection = db.rooms
daily_logs_collection = db.daily_logs

# --- MAIN APP ---
st.title("🏠 Room Dashboard")

# 1. AUTHENTICATION & ROOM SELECTION
logged_in_email = st.session_state.get('logged_in_email', '')
if not logged_in_email:
    st.warning("Please log in to view your dashboard.")
    st.page_link("Home.py", label="Go to Login", icon="👈")
    st.stop()

user_rooms = list(rooms_collection.find({"members": logged_in_email}))
selected_room_data = None

if not user_rooms:
    st.warning("No rooms found for your account. Please join or create a room.")
    st.page_link("pages/create_join_room.py", label="Go to Create/Join Room Page", icon="👈")
elif len(user_rooms) == 1:
    selected_room_data = user_rooms[0]
else:
    room_names = [room['room_name'] for room in user_rooms]
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        selected_room_name = st.selectbox("You are in multiple rooms. Select one to view:", room_names)
    selected_room_data = next((room for room in user_rooms if room['room_name'] == selected_room_name), None)

if selected_room_data:
    st.header(f"Welcome to {html.escape(selected_room_data['room_name'])}")
    
    access_code = selected_room_data.get("access_code")
    members = selected_room_data.get("members", [])
    timetable_data = selected_room_data.get("timetable")

    # --- CARD 1: TIMETABLE ---
    with st.container(border=True):
        st.markdown('<div class="section-title">🗓️ Weekly Timetable</div>', unsafe_allow_html=True)
        if not timetable_data:
            st.warning("The timetable for this room has not been set up yet.")
            st.page_link("pages/edit_table.py", label="Setup Timetable Now", icon="📝")
        else:
            index_labels = ['Slot 1', 'Slot 2', 'Slot 3', 'Slot 4', 'Slot 5', 'Slot 6']
            df = pd.DataFrame(timetable_data, index=index_labels)
            st.dataframe(df, use_container_width=True)

    # --- CARD 2: TODAY'S FOCUS (CHECKLIST) ---
    with st.container(border=True):
        st.markdown('<div class="section-title">🎯 Today\'s Focus</div>', unsafe_allow_html=True)
        today_name = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime('%A')
        today_str = datetime.date.today().isoformat()
        
        if timetable_data and today_name in timetable_data:
            tasks_today_all = timetable_data[today_name]
            log_data = get_or_create_log(daily_logs_collection, today_str, tasks_today_all, members, access_code)
            status_map = {task['name']: task for task in log_data.get('tasks', [])}

            header_cols = st.columns((4, *([2] * len(members))))
            header_cols[0].markdown("<p class='grid-header'>Task</p>", unsafe_allow_html=True)
            for i, member in enumerate(members):
                clean_name = html.escape(member.split('@')[0].capitalize())
                header_cols[i+1].markdown(f"<p class='grid-header'>{clean_name}</p>", unsafe_allow_html=True)
            
            status_options = ["Not Done", "Doing", "Done"]
            for task in tasks_today_all:
                if task in ['—', 'BREAK']: continue
                task_status = status_map.get(task, {})
                task_cols = st.columns((4, *([2] * len(members))))
                task_cols[0].markdown(f"<div class='task-text'>{html.escape(task)}</div>", unsafe_allow_html=True)
                
                for i, member in enumerate(members):
                    saved_status = task_status.get(f'{member}_status', 'Not Done')
                    try: default_index = status_options.index(saved_status)
                    except ValueError: default_index = 0
                    
                    task_cols[i+1].selectbox(
                        label=f"Status for {member} on {task}", options=status_options, index=default_index,
                        key=f"{member}_{task}", on_change=update_task_status,
                        kwargs=dict(daily_logs_collection=daily_logs_collection, date_str=today_str, task_name=task, person=member, room_access_code=access_code),
                        label_visibility="collapsed"
                    )
        else:
            st.success("🎉 It's a rest day! No tasks scheduled.")

    # --- CARD 3: ANALYTICS & PROGRESS ---
    with st.container(border=True):
        st.markdown('<div class="section-title">📊 Analytics & Progress</div>', unsafe_allow_html=True)
        selected_month = datetime.date.today().strftime('%Y-%m')

        monthly_task_data = get_monthly_task_completions(daily_logs_collection, selected_month, members, access_code)
        
        if not monthly_task_data:
            st.info("No tasks have been completed this month. Get started to see your progress!")
        else:
            st.markdown("### Monthly Task Summary")
            analytics_df = pd.DataFrame(monthly_task_data).rename(columns={"_id": "Task"}).set_index("Task")
            
            st.markdown('<div class="info-grid">', unsafe_allow_html=True)
            metric_cols = st.columns(len(members))
            for i, member in enumerate(members):
                clean_name = html.escape(member.split('@')[0].capitalize())
                total_tasks = analytics_df[f"{clean_name} Completions"].sum()
                with metric_cols[i]:
                    st.metric(f"{clean_name}'s Total Tasks Done", f"{int(total_tasks)}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.dataframe(analytics_df, use_container_width=True)
            
            daily_progress_data = get_daily_progress_data(daily_logs_collection, selected_month, members, access_code)
            if daily_progress_data:
                st.markdown("### Cumulative Progress This Month")
                progress_df = pd.DataFrame(daily_progress_data).rename(columns={"_id": "Day"}).set_index("Day").sort_index()
                progress_df.index = progress_df.index.astype(int)
                days_in_month = pd.Period(selected_month).days_in_month
                progress_df = progress_df.reindex(range(1, days_in_month + 1), fill_value=0).cumsum()
                
                # --- FIX: Use 'Day' as the id_var for melt, as it's the correct column name after reset_index() ---
                chart_data = progress_df.reset_index().melt('Day', var_name='Person', value_name='Tasks Done')
                
                chart = alt.Chart(chart_data).mark_line().encode(
                    # --- FIX: Use the correct column name 'Day' for the x-axis ---
                    x=alt.X('Day', title='Day of the Month'),
                    y=alt.Y('Tasks Done', title='Cumulative Tasks Done'),
                    color='Person',
                    # --- FIX: Use 'Day' in the tooltip ---
                    tooltip=['Day', 'Person', 'Tasks Done']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)