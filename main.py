import streamlit as st
import joblib

# Load model
model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

st.set_page_config(page_title="PhishGuard NLP")

st.title("PhishGuard NLP")
st.write("Detect phishing/spam messages using NLP")

# Input
user_input = st.text_area("Enter message")

if st.button("Scan"):
    if user_input.strip() == "":
        st.warning("Enter a message")
    else:
        vec = vectorizer.transform([user_input])
        pred = model.predict(vec)[0]

        if pred == 1:
            st.error("Spam / Phishing Detected")
        else:
            st.success("Safe Message")