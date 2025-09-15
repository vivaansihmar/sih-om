import os
import random
from flask import Flask, render_template, request
import folium
from folium.plugins import HeatMap

app = Flask(__name__)
all_points = []

coastal_points = [
    [8.088,77.538],[8.200,77.600],[8.400,77.700],
    [9.256,78.125],[10.567,75.432],
    [11.500,79.300],[12.000,79.600],[13.082,80.271],
    [15.000,80.300],[16.000,81.500],[17.500,82.000],
    [18.000,83.500],[19.000,84.000],[20.2961,85.8245],
    [22.300,70.800],[22.500,71.200]
]

# Generate multiple jittered points per coastal location for visible intensity
for point in coastal_points:
    for _ in range(10):
        all_points.append([
            point[0]+random.uniform(-0.02,0.02),
            point[1]+random.uniform(-0.02,0.02),
            random.uniform(0.5,1.0)  # weight/intensity
        ])

def extract_coastal_point_from_text(text):
    text = text.lower()
    region_keywords = {
        "kerala": [[8.088,77.538],[9.256,78.125],[10.567,75.432]],
        "tamil": [[11.500,79.300],[12.000,79.600],[13.082,80.271]],
        "andhra": [[15.000,80.300],[16.000,81.500],[17.500,82.000]],
        "odisha": [[18.000,83.500],[19.000,84.000],[20.2961,85.8245]],
        "gujarat": [[22.300,70.800],[22.500,71.200]]
    }
    for region, points in region_keywords.items():
        if region in text:
            point = random.choice(points)
            return [point[0]+random.uniform(-0.02,0.02),
                    point[1]+random.uniform(-0.02,0.02),
                    random.uniform(0.5,1.0)]
    return None

@app.route("/", methods=["GET","POST"])
def index():
    message = ""
    global all_points
    if request.method=="POST":
        report_text = request.form.get("report_text")
        if report_text:
            new_point = extract_coastal_point_from_text(report_text)
            if new_point:
                all_points.append(new_point)
                message = f"Report added: {report_text}"
            else:
                message = "Could not determine location from report."

    m = folium.Map(location=[20.0,80.0], zoom_start=5, tiles="CartoDB dark_matter")
    heat_data = [[p[0], p[1], p[2]] for p in all_points]
    HeatMap(heat_data, radius=25, blur=20, min_opacity=0.5, max_zoom=13).add_to(m)

    os.makedirs("templates", exist_ok=True)
    m.save("templates/heatmap.html")
    return render_template("heatmap.html", message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
