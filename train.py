import pandas as pd
import re
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ---------------- LOAD ----------------
df = pd.read_csv("C:/projects/phishguard-nlp/data/spam.csv")

# ---------------- CLEAN ----------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

df["message"] = df["message"].apply(clean_text)
df["label"] = df["label"].map({"ham": 0, "spam": 1})

# ---------------- SPLIT ----------------
X_train, X_test, y_train, y_test = train_test_split(
    df["message"], df["label"], test_size=0.2, random_state=42
)

# ---------------- VECTORIZE ----------------
vectorizer = TfidfVectorizer(stop_words="english")
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# ---------------- MODEL ----------------
model = MultinomialNB()
model.fit(X_train_tfidf, y_train)

# ---------------- EVAL ----------------
y_pred = model.predict(X_test_tfidf)

print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# ---------------- SAVE ----------------
joblib.dump(model, "model/model.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")

print("Model + Vectorizer saved.")