import streamlit as st
import requests
import pandas as pd
import os

API_BASE = "http://127.0.0.1:8000"
USER_FILE = "users.csv"

st.set_page_config(page_title="PhishGuard NLP", layout="centered")

# ---------------- INIT FILE ----------------
if not os.path.exists(USER_FILE):
    df = pd.DataFrame(columns=["username", "password"])
    df.to_csv(USER_FILE, index=False)

# ---------------- SESSION ----------------
if "count" not in st.session_state:
    st.session_state.count = 0

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ---------------- AUTH FUNCTIONS ----------------
def signup(username, password):
    users = pd.read_csv(USER_FILE)

    if username in users["username"].values:
        return False

    new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

def login(username, password):
    users = pd.read_csv(USER_FILE)

    user = users[(users["username"] == username) & (users["password"] == password)]

    if not user.empty:
        return True
    return False

# ---------------- API CALL ----------------
def scan_text(text):
    try:
        res = requests.post(API_URL, json={"text": text})
        if res.status_code == 200:
            return res.json()["prediction"]
        else:
            return "error"
    except:
        return "down"

# ---------------- UI ----------------
st.title("PhishGuard NLP")

# ---------------- LOGOUT ----------------
if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.count = 0
        st.rerun()

# ---------------- INPUT ----------------
user_input = st.text_area("Enter Message")

# ---------------- SCAN ----------------
def scan_api(u, text):
    res = requests.post(f"{API_BASE}/scan", json={
        "username": u,
        "text": text
    })

    if res.status_code == 200:
        return res.json()
    elif res.status_code == 403:
        return {"error": "limit"}
    else:
        return {"error": "other"}

# ---------------- FORCE AUTH UI ----------------
if (not st.session_state.logged_in and st.session_state.count >= 5) or st.session_state.get("show_auth", False):

    st.warning("Free limit reached. Please login or signup.")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    # -------- LOGIN --------
    with tab1:
        l_user = st.text_input("Username", key="login_user")
        l_pass = st.text_input("Password", type="password", key="login_pass")

    def login_api(u, p):
        res = requests.post(f"{API_BASE}/login", json={"username": u, "password": p})
        return res.status_code == 200
    # -------- SIGNUP --------
    with tab2:
        s_user = st.text_input("New Username", key="signup_user")
        s_pass = st.text_input("New Password", type="password", key="signup_pass")

    def signup_api(u, p):
        res = requests.post(f"{API_BASE}/signup", json={"username": u, "password": p})
        return res.status_code == 200
# ---------------- INFO ----------------
if not st.session_state.logged_in:
    st.info(f"Free usage: {st.session_state.count}/5")