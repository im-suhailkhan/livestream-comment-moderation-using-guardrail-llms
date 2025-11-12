import streamlit as st
import pandas as pd
from datetime import datetime
from moderator import moderate_comment, add_safe_comment, add_to_queue
import random

# Page config
st.set_page_config(page_title="YouTube Comment Moderation", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for YouTube-like styling
st.markdown("""
<style>
    /* Hide Streamlit branding and extra padding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    
    /* Main container */
    .main {
        padding: 0 !important;
    }
    
    /* YouTube chat styling */
    .chat-container {
        background: white;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
    
    .chat-header {
        padding: 12px 16px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .chat-message {
        padding: 8px 16px;
        margin: 4px 0;
    }
    
    .chat-message:hover {
        background: #f9fafb;
    }
    
    .username {
        font-weight: 600;
        font-size: 13px;
        color: #374151;
        margin-right: 4px;
    }
    
    .message-text {
        font-size: 13px;
        color: #111827;
        display: inline;
    }
    
    .avatar {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-block;
        text-align: center;
        line-height: 24px;
        margin-right: 8px;
        font-size: 12px;
    }
    
    /* Input styling */
    .stTextInput input {
        border-radius: 20px !important;
        border: 1px solid #d1d5db !important;
        padding: 8px 16px !important;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Moderation buttons */
    .mod-button {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        cursor: pointer;
        margin-left: 4px;
        font-size: 12px;
    }
    
    .approve-btn {
        background: #10b981;
        color: white;
    }
    
    .reject-btn {
        background: #ef4444;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state - NO DUMMY DATA
if 'SAFE_COMMENTS' not in st.session_state:
    st.session_state.SAFE_COMMENTS = pd.DataFrame(columns=['username', 'comment', 'avatar', 'safe', 'reason', 'confidence', 'timestamp'])
if 'MODERATOR_QUEUE' not in st.session_state:
    st.session_state.MODERATOR_QUEUE = pd.DataFrame(columns=['username', 'comment', 'avatar', 'safe', 'reason', 'confidence', 'timestamp', 'approved'])
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'stream'
if 'moderator_authenticated' not in st.session_state:
    st.session_state.moderator_authenticated = False
if 'compliance_rules' not in st.session_state:
    st.session_state.compliance_rules = {
        'enabled': True,
        'compliance_list': []
    }

SAFE_COMMENTS = st.session_state.SAFE_COMMENTS
MODERATOR_QUEUE = st.session_state.MODERATOR_QUEUE

# All comments combined - filter based on moderator status
if st.session_state.moderator_authenticated:
    # Moderators see all comments (approved + pending)
    all_comments = []
    for _, row in SAFE_COMMENTS.iterrows():
        all_comments.append({
            'username': row['username'],
            'comment': row['comment'],
            'avatar': row['avatar'],
            'timestamp': row['timestamp'],
            'status': 'approved',
            'index': None
        })
    for idx, row in MODERATOR_QUEUE.iterrows():
        all_comments.append({
            'username': row['username'],
            'comment': row['comment'],
            'avatar': row['avatar'],
            'timestamp': row['timestamp'],
            'status': 'pending',
            'index': idx
        })
    all_comments.sort(key=lambda x: x['timestamp'], reverse=True)
else:
    # Non-moderators see only approved comments
    all_comments = []
    for _, row in SAFE_COMMENTS.iterrows():
        all_comments.append({
            'username': row['username'],
            'comment': row['comment'],
            'avatar': row['avatar'],
            'timestamp': row['timestamp'],
            'status': 'approved',
            'index': None
        })
    all_comments.sort(key=lambda x: x['timestamp'], reverse=True)

# NAVIGATION HEADER - Always visible
st.markdown("""
<div style='background: white; border-bottom: 1px solid #e5e7eb; padding: 12px 24px; margin-bottom: 0;margin-top: 1rem;'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div style='display: flex; align-items: center; gap: 12px;'>
            <span style='font-size: 28px;'>🛡️</span>
            <h1 style='margin: 0; font-size: 20px; font-weight: bold;'>YouTube Comment Moderation</h1>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation buttons
if st.session_state.moderator_authenticated:
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([3, 1, 1, 1])
else:
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([3, 1, 1, 1])

with col_nav2:
    if st.button("📺 Live Stream", use_container_width=True, type="primary" if st.session_state.current_view == 'stream' else "secondary"):
        st.session_state.current_view = 'stream'
        st.rerun()
with col_nav3:
    if st.button("🛡️ Dashboard", use_container_width=True, type="primary" if st.session_state.current_view == 'dashboard' else "secondary"):
        st.session_state.current_view = 'dashboard'
        st.rerun()
with col_nav4:
    if st.session_state.moderator_authenticated:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.moderator_authenticated = False
            st.session_state.current_view = 'stream'
            st.rerun()
    else:
        st.write("")  # Empty placeholder when not authenticated

# STREAM VIEW - YouTube Style with Moderation in Top Chat
if st.session_state.current_view == 'stream':
    # Two column layout - Video and Chat
    col_video, col_chat = st.columns([2.5, 1])
    
    with col_video:
        # Embed YouTube video
        video_id = "MUNIbKDugII?si=SaaXi7Kr4hlAkzHh"
        st.markdown(f"""
        <div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%;">
            <iframe 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                src="https://www.youtube.com/embed/{video_id}" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)
    
    with col_chat:
        # Chat header
        st.markdown("""
        <div class="chat-header">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 600; font-size: 14px;">Top chat</span>
                <span style="font-size: 12px;">▼</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 11px; font-weight: 600;">🇺🇸 0XP</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages container
        chat_container = st.container()
        with chat_container:
            if len(all_comments) == 0:
                st.markdown("""
                <div style='text-align: center; color: #9ca3af; margin-top: 32px;'>
                    <p style='font-size: 14px;'>No comments yet</p>
                    <p style='font-size: 12px; margin-top: 8px;'>Be the first to comment!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Display all comments with moderation controls for pending ones
                for comment_data in all_comments:
                    col_msg, col_mod = st.columns([5, 1])
                    
                    with col_msg:
                        st.markdown(f"""
                        <div class="chat-message">
                            <span class="avatar">{comment_data['avatar']}</span>
                            <span class="username">{comment_data['username']}</span>
                            <span class="message-text">{comment_data['comment']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show moderation controls ONLY for authenticated moderators and pending comments
                    with col_mod:
                        if st.session_state.moderator_authenticated and comment_data['status'] == 'pending':
                            col_tick, col_cross = st.columns(2)
                            with col_tick:
                                if st.button("✓", key=f"approve_chat_{comment_data['index']}", help="Approve"):
                                    row = MODERATOR_QUEUE.iloc[comment_data['index']]
                                    approved_row = pd.DataFrame([{
                                        'username': row['username'],
                                        'comment': row['comment'],
                                        'avatar': row['avatar'],
                                        'safe': True,
                                        'reason': row['reason'],
                                        'confidence': row['confidence'],
                                        'timestamp': row['timestamp']
                                    }])
                                    st.session_state.SAFE_COMMENTS = pd.concat([
                                        st.session_state.SAFE_COMMENTS, approved_row
                                    ], ignore_index=True)
                                    st.session_state.MODERATOR_QUEUE = MODERATOR_QUEUE.drop(comment_data['index']).reset_index(drop=True)
                                    st.rerun()
                            
                            with col_cross:
                                if st.button("✗", key=f"reject_chat_{comment_data['index']}", help="Reject"):
                                    st.session_state.MODERATOR_QUEUE = MODERATOR_QUEUE.drop(comment_data['index']).reset_index(drop=True)
                                    st.rerun()
            
            # YouTube welcome message
            st.markdown("""
            <div style="margin: 16px; padding: 12px; background: #f3f4f6; border-radius: 8px;">
                <div style="display: flex; gap: 8px; align-items: start;">
                    <div style="width: 24px; height: 24px; background: #dc2626; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <span style="color: white; font-size: 14px;">▶</span>
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 12px; color: #374151;">
                            Welcome to live chat! Remember to guard your privacy and abide by our Community Guidelines.
                        </p>
                        <a href="#" style="font-size: 12px; color: #2563eb; font-weight: 600; text-decoration: none;">Learn more</a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Chat input
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        with st.form(key='chat_form', clear_on_submit=True):
            new_comment = st.text_input("", label_visibility="collapsed", placeholder="Chat...")
            
            if st.form_submit_button("💬 Send", use_container_width=True) and new_comment:
                # Generate random username and avatar
                avatars = ['🔴', '🟤', '🟡', '⚫', '🟢', '🔵', '🟣', '🟠']
                username = f"@user{random.randint(1000, 9999)}"
                avatar = random.choice(avatars)
                
                with st.spinner("Moderating..."):
                    # Get compliance rules
                    compliance_topics = st.session_state.compliance_rules['compliance_list'] if st.session_state.compliance_rules['enabled'] else None
                    
                    # Moderate with compliance rules
                    result = moderate_comment(new_comment)
                    
                    if result['safe']:
                        # Add directly to safe comments
                        new_row = pd.DataFrame([{
                            'username': username,
                            'comment': new_comment,
                            'avatar': avatar,
                            'safe': result['safe'],
                            'reason': result['reason'],
                            'confidence': result['confidence'],
                            'timestamp': result['timestamp']
                        }])
                        st.session_state.SAFE_COMMENTS = pd.concat([
                            st.session_state.SAFE_COMMENTS, new_row
                        ], ignore_index=True)
                    else:
                        # Add to moderation queue
                        new_row = pd.DataFrame([{
                            'username': username,
                            'comment': new_comment,
                            'avatar': avatar,
                            'safe': result['safe'],
                            'reason': result['reason'],
                            'confidence': result['confidence'],
                            'timestamp': result['timestamp'],
                            'approved': False
                        }])
                        st.session_state.MODERATOR_QUEUE = pd.concat([
                            st.session_state.MODERATOR_QUEUE, new_row
                        ], ignore_index=True)
                st.rerun()

# MODERATOR DASHBOARD VIEW
else:
    if not st.session_state.moderator_authenticated:
        # Password login screen
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 2rem; background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>🔒</div>
                <h2>Moderator Access</h2>
                <p style='color: #6b7280;'>Enter password to access the moderation dashboard</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.form(key='password_form'):
                password = st.text_input("Password", type="password", placeholder="Enter moderator password")
                submit = st.form_submit_button("Access Dashboard", use_container_width=True)
                
                if submit:
                    if password == "moderator123":
                        st.session_state.moderator_authenticated = True
                        st.rerun()
                    else:
                        st.error("Incorrect password")
            
            st.info("**Demo credentials:**\nPassword: `moderator123`")
    
    else:
        # Moderator dashboard content
        st.markdown("## Moderator Dashboard")
        st.markdown("---")
        
        # Compliance Rules Configuration Section
        st.markdown("### ⚖️ Compliance Rules Configuration")
        
        with st.expander("Configure Moderation Rules", expanded=True):
            # Enable/Disable compliance
            col_enable, col_spacer = st.columns([1, 3])
            with col_enable:
                enabled = st.checkbox(
                    "Enable Compliance Checks",
                    value=st.session_state.compliance_rules['enabled'],
                    key='compliance_enabled'
                )
                st.session_state.compliance_rules['enabled'] = enabled
            
            st.markdown("---")
            
            # Compliance input UI: single text area for compliance rules
            st.markdown("**Compliance Rules**")
            st.caption("Enter your compliance rules, one per line")
            rules_text = st.text_area(
                "Compliance Rules Input",\
                value="\n".join(st.session_state.compliance_rules.get('compliance_list', [])),
                placeholder="e.g. You are a banking customer care chatbot. Only answer bank questions. Reject medical, personal, off-topic, or unsafe queries.",
                height=120,
                key="compliance_rules_textarea"
            )
            # store as a list, skipping empty entries
            st.session_state.compliance_rules['compliance_list'] = [rule.strip() for rule in rules_text.splitlines() if rule.strip()]
            
            # Info box
            st.info("💡 **Info:** These rules are used by WalledAI to check for compliance topics and detect PII in user comments. Enable topics like Medical/Banking to flag content in regulated domains.")
        
        st.markdown("---")
        
        # Pending Comments Section
        st.markdown(f"### Pending Comments ({len(MODERATOR_QUEUE)})")
        
        if not MODERATOR_QUEUE.empty:
            for idx, row in MODERATOR_QUEUE.iterrows():
                with st.container():
                    col_avatar, col_content, col_actions = st.columns([0.5, 4, 2])
                    
                    with col_avatar:
                        st.markdown(f"<div style='font-size: 32px; text-align: center;'>{row['avatar']}</div>", unsafe_allow_html=True)
                    
                    with col_content:
                        st.markdown(f"**{row['username']}**")
                        st.write(row['comment'])
                        try:
                            dt = datetime.fromisoformat(row['timestamp'])
                            time_str = dt.strftime("%I:%M:%S %p")
                        except:
                            time_str = str(row['timestamp'])
                        st.caption(f"{time_str} • Reason: {row['reason']} • Confidence: {row['confidence']:.2f}")
                    
                    with col_actions:
                        col_app, col_rej = st.columns(2)
                        with col_app:
                            if st.button("✓ Approve", key=f"dash_approve_{idx}", use_container_width=True):
                                approved_row = pd.DataFrame([{
                                    'username': row['username'],
                                    'comment': row['comment'],
                                    'avatar': row['avatar'],
                                    'safe': True,
                                    'reason': row['reason'],
                                    'confidence': row['confidence'],
                                    'timestamp': row['timestamp']
                                }])
                                st.session_state.SAFE_COMMENTS = pd.concat([
                                    st.session_state.SAFE_COMMENTS, approved_row
                                ], ignore_index=True)
                                st.session_state.MODERATOR_QUEUE = MODERATOR_QUEUE.drop(idx).reset_index(drop=True)
                                st.rerun()
                        
                        with col_rej:
                            if st.button("✗ Reject", key=f"dash_reject_{idx}", use_container_width=True):
                                st.session_state.MODERATOR_QUEUE = MODERATOR_QUEUE.drop(idx).reset_index(drop=True)
                                st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No pending comments")
        
        # Approved Comments Section
        st.markdown(f"### Approved Comments ({len(SAFE_COMMENTS)})")
        
        if not SAFE_COMMENTS.empty:
            for idx, row in SAFE_COMMENTS.iterrows():
                col_avatar, col_content = st.columns([0.5, 5])
                with col_avatar:
                    st.markdown(f"<div style='font-size: 24px;'>{row['avatar']}</div>", unsafe_allow_html=True)
                with col_content:
                    st.markdown(f"**{row['username']}**: {row['comment']}")
        else:
            st.info("No approved comments yet")