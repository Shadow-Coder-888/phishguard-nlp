import streamlit as st
import pandas as pd
import joblib
import os

# ---------------- CONFIG ----------------
USER_FILE = "users.csv"
SCAN_FILE = "scans.csv"

# ---------------- INIT FILES ----------------
def init_file(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

init_file(USER_FILE, ["username", "password", "plan"])
init_file(SCAN_FILE, ["username", "count"])

# ---------------- SAFE READ ----------------
def safe_read(file, columns):
    try:
        df = pd.read_csv(file)
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df
    except:
        return pd.DataFrame(columns=columns)

# ---------------- LOAD MODEL ----------------
model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

# ---------------- AUTH ----------------
def signup(username, password):
    username = username.strip()
    password = password.strip()

    if username == "" or password == "":
        return "empty"

    users = safe_read(USER_FILE, ["username", "password", "plan"])

    # Normalize usernames
    users["username"] = users["username"].astype(str).str.strip()

    if username in users["username"].values:
        return "exists"

    new_user = pd.DataFrame(
        [[username, password, "free"]],
        columns=["username", "password", "plan"]
    )

    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)

    return "created"


def login(username, password):
    users = safe_read(USER_FILE, ["username", "password", "plan"])

    user = users[
        (users["username"].astype(str).str.strip() == username.strip()) &
        (users["password"].astype(str).str.strip() == password.strip())
    ]

    if not user.empty:
        return user.iloc[0]["plan"]

    return None

# ---------------- SCAN LOGIC ----------------
def get_scan_count(username):
    scans = safe_read(SCAN_FILE, ["username", "count"])

    if username not in scans["username"].astype(str).values:
        return 0

    return int(scans[scans["username"] == username]["count"].values[0])


def update_scan(username):
    scans = safe_read(SCAN_FILE, ["username", "count"])

    if username in scans["username"].astype(str).values:
        scans.loc[scans["username"] == username, "count"] += 1
    else:
        new_row = pd.DataFrame([[username, 1]], columns=["username", "count"])
        scans = pd.concat([scans, new_row], ignore_index=True)

    scans.to_csv(SCAN_FILE, index=False)

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.plan = None

# ---------------- UI ----------------
st.title("PhishGuard NLP")

menu = st.sidebar.selectbox("Menu", ["Login", "Signup"])

# ---------- SIGNUP ----------
if menu == "Signup":
    st.subheader("Signup")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Create Account"):
        result = signup(u, p)

        if result == "created":
            st.success("Account created")
        elif result == "exists":
            st.error("Username already exists")
        else:
            st.warning("Invalid input")

# ---------- LOGIN ----------
elif menu == "Login":
    st.subheader("Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        plan = login(u, p)

        if plan:
            st.session_state.user = u.strip()
            st.session_state.plan = plan
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

# ---------- MAIN APP ----------
if st.session_state.user:
    st.write(f"User: {st.session_state.user} ({st.session_state.plan})")

    text = st.text_area("Enter message")

    if st.button("Scan"):
        if text.strip() == "":
            st.warning("Enter a message")
        else:
            count = get_scan_count(st.session_state.user)

            if st.session_state.plan == "free" and count >= 10:
                st.error("Limit reached (10 scans). Upgrade required.")
            else:
                vec = vectorizer.transform([text])
                pred = model.predict(vec)[0]

                update_scan(st.session_state.user)

                if pred == 1:
                    st.error("Spam detected")
                else:
                    st.success("Safe message")

                st.write(f"Scans used: {count + 1}")

    # ---------- UPGRADE ----------
    if st.button("Upgrade to Pro"):
        users = safe_read(USER_FILE, ["username", "password", "plan"])
        users.loc[users["username"] == st.session_state.user, "plan"] = "pro"
        users.to_csv(USER_FILE, index=False)

        st.session_state.plan = "pro"
        st.success("Upgraded to Pro")

    # ---------- LOGOUT ----------
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.plan = None
        st.rerun()