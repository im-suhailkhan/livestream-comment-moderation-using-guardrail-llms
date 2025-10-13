import streamlit as st
import pandas as pd
from moderator import moderate_comment, add_safe_comment, add_to_queue, approve_comment

# Use session_state for persistence across reruns
if 'SAFE_COMMENTS' not in st.session_state:
    st.session_state.SAFE_COMMENTS = pd.DataFrame(columns=['comment', 'safe', 'reason', 'confidence', 'timestamp'])
if 'MODERATOR_QUEUE' not in st.session_state:
    st.session_state.MODERATOR_QUEUE = pd.DataFrame(columns=['comment', 'safe', 'reason', 'confidence', 'timestamp', 'approved'])

# Assign to local vars for ease
SAFE_COMMENTS = st.session_state.SAFE_COMMENTS
MODERATOR_QUEUE = st.session_state.MODERATOR_QUEUE

st.title("YouTube Comment Moderator")

# Embed YouTube video (reach goal)
st.header("Watch the Video")
video_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"  # Replace with your video ID
st.components.v1.html(f"""
    <iframe width="800" height="450" src="{video_url}" frameborder="0" allowfullscreen></iframe>
""", height=450)

# User comment form
st.header("Submit a Comment")
user_comment = st.text_area("Your comment:")
if st.button("Post Comment") and user_comment:
    with st.spinner("Moderating..."):
        result = moderate_comment(user_comment)
        if result['safe']:
            st.session_state.SAFE_COMMENTS = add_safe_comment(result, user_comment, st.session_state.SAFE_COMMENTS)
            st.success("Comment approved and posted!")
            st.rerun()
        else:
            st.session_state.MODERATOR_QUEUE = add_to_queue(result, user_comment, st.session_state.MODERATOR_QUEUE)  # Update session
            st.warning("Comment flagged for review. Awaiting moderator approval.")
            st.rerun()

# Display safe comments
st.header("Published Comments")
if not SAFE_COMMENTS.empty:
    for _, row in SAFE_COMMENTS.iterrows():
        st.write(f"**{row['comment']}** (Confidence: {row['confidence']:.2f})")
else:
    st.info("No approved comments yet.")

# Simple moderator section (password-protected for demo)
if st.sidebar.checkbox("Moderator View"):
    password = st.sidebar.text_input("Enter password:", type="password")
    if password == "mod123":  # Change for security
        st.header("Moderator Queue")
        # Removed unnecessary global declaration
        for idx, row in MODERATOR_QUEUE.iterrows():
            with st.expander(f"Flagged: {row['comment']} (Reason: {row['reason']})"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Approve {idx}"):
                        approve_comment(idx)
                        st.session_state.MODERATOR_QUEUE = MODERATOR_QUEUE  # Update
                        st.rerun()
                with col2:
                    if st.button(f"Reject {idx}"):
                        MODERATOR_QUEUE = MODERATOR_QUEUE.drop(idx).reset_index(drop=True)
                        st.session_state.MODERATOR_QUEUE = MODERATOR_QUEUE
                        st.rerun()