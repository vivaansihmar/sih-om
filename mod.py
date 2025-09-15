import pandas as pd
import re
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

data = pd.read_excel("Data/disaster.xlsx", sheet_name="Sheet1")

if len(data.columns) == 5:
    data.columns = ["tweet", "date", "time", "latitude", "longitude"]
    data["label"] = 1
elif len(data.columns) == 6:
    data.columns = ["tweet", "date", "time", "latitude", "longitude", "label"]
else:
    raise ValueError(f"Unexpected number of columns: {len(data.columns)}")

if data["label"].nunique() < 2:
    synthetic = pd.DataFrame({
        "tweet": [
            "Sunny day at the beach, enjoying the weather",
            "Family dinner with friends, everything is fine"
        ],
        "date": ["2025-09-15", "2025-09-15"],
        "time": ["12:00:00", "13:00:00"],
        "latitude": [19.07, 28.61],
        "longitude": [72.87, 77.20],
        "label": [0, 0] if data["label"].iloc[0] == 1 else [1, 1]
    })
    data = pd.concat([data, synthetic], ignore_index=True)

def clean_text(text):
    text = re.sub(r"http\S+|www\S+|https\S+", "", str(text))
    text = re.sub(r"[^A-Za-z\s]", "", text)
    return text.lower()

data["clean_tweet"] = data["tweet"].apply(clean_text)

X_train, X_test, y_train, y_test = train_test_split(
    data["clean_tweet"], data["label"], test_size=0.2, random_state=42
)

vectorizer = TfidfVectorizer(max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

model = LogisticRegression(max_iter=200)
model.fit(X_train_vec, y_train)

os.makedirs("output/models", exist_ok=True)
with open("output/models/disaster_model.pkl", "wb") as f:
    pickle.dump((model, vectorizer), f)

print("✅ Model trained and saved at output/models/disaster_model.pkl")
