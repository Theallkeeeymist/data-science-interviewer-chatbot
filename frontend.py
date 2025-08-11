import streamlit as st
import requests
import uuid

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8500"  # URL of your FastAPI backend
START_CHAT_URL = f"{BACKEND_URL}"
CHATBOT_URL = f"{BACKEND_URL}/chatbot"

# --- Page Setup ---
st.set_page_config(
    page_title="🔥 Rude Motivational Speaker",
    page_icon="🔥",
    layout="centered"
)

# --- Session State Initialization ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

# --- UI Components ---
st.title("Rude Motivational Speaker")
st.markdown("Feeling down? Need a lil push? Great Place but nothings sweet here friend.")

# --- Functions ---
def start_new_chat():
    """Starts a new chat session by calling the backend."""
    try:
        response = requests.post(START_CHAT_URL)
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data['session_id']
            st.session_state.chat_history = []
            st.session_state.chat_started = True
            st.success("New chat session started! Now, what's your problem?")
        else:
            st.error("Failed to start a new chat. Is the backend running?")
    except requests.exceptions.ConnectionError:
        st.error("Connection failed. Please make sure the backend is running.")


def display_chat():
    """Displays the chat history."""
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def handle_user_input(prompt):
    """Handles user input and gets a response from the chatbot."""
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            response = requests.post(
                CHATBOT_URL,
                json={"session_id": st.session_state.session_id, "message": prompt}
            )
            if response.status_code == 200:
                full_response = response.json().get("response", "I... I have nothing to say. You've broken me.")
            else:
                full_response = "I'm not talking to you right now. Try again later."
        except requests.exceptions.ConnectionError:
            full_response = "Looks like my server is as lazy as you are. It's not running."

        message_placeholder.markdown(full_response)

    st.session_state.chat_history.append({"role": "assistant", "content": full_response})


# --- Main App Logic ---
if not st.session_state.chat_started:
    if st.button("Start a New Chat"):
        start_new_chat()
else:
    display_chat()

    if prompt := st.chat_input("What do you want?"):
        handle_user_input(prompt)

# --- Sidebar for additional controls ---
with st.sidebar:
    st.header("Controls")
    if st.button("Start a New Conversation"):
        start_new_chat()
    st.markdown("---")
    st.info("Your chat history is session-based and will be lost if you close this tab.")