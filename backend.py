from fastapi import FastAPI, HTTPException
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
    scans INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------------- SECURITY ----------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- SCHEMAS ----------------
class User(BaseModel):
    username: str
    password: str

class ScanRequest(BaseModel):
    username: str
    text: str

# ---------------- AUTH ----------------
@app.post("/signup")
def signup(user: User):
    hashed = pwd_context.hash(user.password)

    try:
        cur.execute("INSERT INTO users(username, password) VALUES (?, ?)",
                    (user.username, hashed))
        conn.commit()
        return {"msg": "User created"}
    except:
        raise HTTPException(400, "User already exists")

@app.post("/login")
def login(user: User):
    cur.execute("SELECT password FROM users WHERE username=?", (user.username,))
    data = cur.fetchone()

    if not data or not pwd_context.verify(user.password, data[0]):
        raise HTTPException(401, "Invalid credentials")

    return {"msg": "Login success"}

# ---------------- SCAN ----------------
@app.post("/scan")
def scan(req: ScanRequest):

    # get user scans
    cur.execute("SELECT scans FROM users WHERE username=?", (req.username,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(404, "User not found")

    scans = row[0]

    # limit
    if scans >= 5:
        raise HTTPException(403, "Free limit reached")

    vec = vectorizer.transform([req.text])
    pred = int(model.predict(vec)[0])

    # update count
    cur.execute("UPDATE users SET scans=? WHERE username=?",
                (scans + 1, req.username))
    conn.commit()

    return {
        "prediction": "spam" if pred == 1 else "ham",
        "remaining": 5 - (scans + 1)
    }

# ---------------- RESET (for demo) ----------------
@app.post("/reset/{username}")
def reset(username: str):
    cur.execute("UPDATE users SET scans=0 WHERE username=?", (username,))
    conn.commit()
    return {"msg": "reset"}