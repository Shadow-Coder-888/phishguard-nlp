from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
import joblib
from passlib.context import CryptContext

app = FastAPI()

# ---------------- MODEL ----------------
model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")

# ---------------- DB ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    plan TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS scans (
    username TEXT,
    count INTEGER
)
""")

conn.commit()

# ---------------- SECURITY ----------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- SCHEMAS ----------------
class User(BaseModel):
    username: str
    password: str

class Message(BaseModel):
    text: str
    username: str

# ---------------- AUTH ----------------
@app.post("/signup")
def signup(user: User):
    hashed = pwd_context.hash(user.password)

    try:
        cur.execute("INSERT INTO users VALUES (?, ?, ?)", (user.username, hashed, "free"))
        conn.commit()
        return {"msg": "created"}
    except:
        raise HTTPException(400, "User exists")

@app.post("/login")
def login(user: User):
    cur.execute("SELECT password, plan FROM users WHERE username=?", (user.username,))
    data = cur.fetchone()

    if not data:
        raise HTTPException(401, "Invalid")

    if not pwd_context.verify(user.password, data[0]):
        raise HTTPException(401, "Invalid")

    return {"plan": data[1]}

# ---------------- SCAN ----------------
@app.post("/scan")
def scan(msg: Message):
    cur.execute("SELECT count FROM scans WHERE username=?", (msg.username,))
    row = cur.fetchone()

    count = row[0] if row else 0

    cur.execute("SELECT plan FROM users WHERE username=?", (msg.username,))
    plan = cur.fetchone()[0]

    if plan == "free" and count >= 10:
        raise HTTPException(403, "Limit reached")

    vec = vectorizer.transform([msg.text])
    pred = int(model.predict(vec)[0])

    # update count
    if row:
        cur.execute("UPDATE scans SET count=? WHERE username=?", (count + 1, msg.username))
    else:
        cur.execute("INSERT INTO scans VALUES (?, ?)", (msg.username, 1))

    conn.commit()

    return {"prediction": pred}