import os
import pickle
import random
import requests
from flask import Flask, render_template, request
import folium
from folium.plugins import HeatMap
import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

NEWSAPI_KEY = "c254ce18c3614cc4bd1593b64e33417a"

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="ocean_disaster_app")

with open("output/models/disaster_model.pkl", "rb") as f:
    model, vectorizer = pickle.load(f)

all_points = []

coastal_points = [
    [8.088,77.538],[9.256,78.125],[10.567,75.432],
    [11.500,79.300],[12.000,79.600],[13.082,80.271],
    [15.000,80.300],[16.000,81.500],[17.500,82.000],
    [18.000,83.500],[19.000,84.000],[20.2961,85.8245],
    [22.300,70.800],[22.500,71.200]
]

for point in coastal_points:
    for _ in range(5):
        all_points.append([point[0]+random.uniform(-0.02,0.02),
                           point[1]+random.uniform(-0.02,0.02),
                           random.uniform(0.5,1.0)])

def geocode_location(location_name):
    try:
        loc = geolocator.geocode(location_name, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
    except GeocoderTimedOut:
        return None
    return None

def extract_location(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            return ent.text
    return None

def add_point_from_text(text):
    loc_name = extract_location(text)
    coords = None
    if loc_name:
        coords = geocode_location(loc_name)
    if not coords:
        coords = random.choice(coastal_points)
    all_points.append([
        coords[0]+random.uniform(-0.02,0.02),
        coords[1]+random.uniform(-0.02,0.02),
        random.uniform(0.5,1.0)
    ])

def fetch_news():
    params = {
        "q": "tsunami OR cyclone OR flood OR storm",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": NEWSAPI_KEY
    }
    try:
        r = requests.get("https://newsapi.org/v2/everything", params=params)
        articles = r.json().get("articles", [])
        for article in articles:
            title = article.get("title", "")
            vec = vectorizer.transform([title])
            pred = model.predict(vec)[0]
            if pred == 1:
                add_point_from_text(title)
    except:
        pass

@app.route("/", methods=["GET","POST"])
def index():
    global all_points
    message = ""

    fetch_news()

    if request.method == "POST":
        report_text = request.form.get("report_text")
        if report_text:
            vec = vectorizer.transform([report_text])
            prediction = model.predict(vec)[0]
            if prediction == 1:
                add_point_from_text(report_text)
                message = f"✅ Disaster report added: {report_text}"
            else:
                message = "ℹ️ Report classified as NON-disaster."

    m = folium.Map(location=[20.0,80.0], zoom_start=5, tiles="CartoDB dark_matter")
    HeatMap([[p[0], p[1], p[2]] for p in all_points], radius=25, blur=30, min_opacity=0.5).add_to(m)

    os.makedirs("static", exist_ok=True)
    m.save("static/heatmap.html")
    return render_template("heatmap.html", message=message)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)

