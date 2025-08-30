import streamlit as st
import requests

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8500"  # Adjust to your FastAPI URL
TOKEN_URL = f"{BACKEND_URL}/token"
START_CHAT_URL = f"{BACKEND_URL}/"
CHATBOT_URL = f"{BACKEND_URL}/chatbot"

# --- Page Setup ---
st.set_page_config(
    page_title="🧠 Data Science Interview Bot",
    page_icon="🧠",
    layout="centered"
)

# --- Session State ---
for key in ["session_id", "chat_history", "chat_started", "access_token", "logged_in"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["session_id", "access_token"] else False
        if key == "chat_history":
            st.session_state[key] = []

# --- Sidebar: Login ---
with st.sidebar:
    st.header("Login")
    username = st.text_input("Username", value="allkeeey")
    password = st.text_input("Password", type="password", value="Sudhanshu12345")
    if st.button("Login"):
        try:
            response = requests.post(
                TOKEN_URL,
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state.access_token = data["access_token"]
                st.session_state.logged_in = True
                st.success("✅ Logged in successfully!")
            else:
                st.error("❌ Invalid username or password")
        except requests.exceptions.ConnectionError:
            st.error("🚫 Backend not running or unreachable.")

    if st.session_state.logged_in:
        if st.button("Start New Interview"):
            try:
                response = requests.post(
                    START_CHAT_URL,
                    headers={"Authorization": f"Bearer {st.session_state.access_token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.session_id = data["session_id"]
                    st.session_state.chat_history = []
                    st.session_state.chat_started = True
                    st.success("🆕 New interview started!")
                else:
                    st.error("Failed to start chat.")
            except requests.exceptions.ConnectionError:
                st.error("Backend connection error.")

# --- Display Chat ---
st.title("🧠 Data Science Interview Bot")
st.markdown("An AI-powered mock interviewer that tests your Data Science knowledge.")


def display_chat():
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def handle_user_input(prompt):
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        try:
            response = requests.post(
                CHATBOT_URL,
                json={"session_id": st.session_state.session_id, "message": prompt},
                headers={"Authorization": f"Bearer {st.session_state.access_token}"}
            )
            if response.status_code == 200:
                bot_reply = response.json().get("response", "No response.")
            else:
                bot_reply = f"Error: {response.status_code} - {response.text}"
        except requests.exceptions.ConnectionError:
            bot_reply = "🚫 Backend not running."

        st.markdown(bot_reply)

    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})


if st.session_state.logged_in and st.session_state.chat_started:
    display_chat()
    if prompt := st.chat_input("Your answer..."):
        handle_user_input(prompt)
elif not st.session_state.logged_in:
    st.warning("Please login from the sidebar to start your interview.")
elif st.session_state.logged_in and not st.session_state.chat_started:
    st.info("Click 'Start New Interview' in the sidebar to begin.")
