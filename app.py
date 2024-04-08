from flask import Flask, render_template, request
import folium
import requests
from folium.plugins import AntPath

app = Flask(__name__)

class CollegeNavigator:
    def __init__(self, repository_url):
        self.repository_url = repository_url
        self.geoResources = {}
        self.college_map = None
        self.fetchGeoJSONFiles()

    def fetchGeoJSONFiles(self):
        response = requests.get(self.repository_url)
        files_data = response.json()
        for file in files_data:
            if file['name'].endswith('.geojson'):
                self.geoResources[file['name'].split('.')[0]] = file['download_url']

    def displayMap(self, path_name):
        if self.college_map is None:
            self.college_map = folium.Map(location=[9.950585500478837, 76.63085559957005], zoom_start=17)
        else:
            self.college_map = folium.Map(location=[9.950585500478837, 76.63085559957005], zoom_start=17)

        path_url = self.geoResources.get(path_name)
        if path_url is None:
            return "Path not found."

        path_data = requests.get(path_url).json()
        try:
            features = path_data['features']
            for feature in features:
                geometry_type = feature['geometry']['type']
                properties = feature['properties']
                coordinates = feature['geometry']['coordinates']
                if geometry_type == 'Point':
                    self.addMarker(coordinates, properties)
                elif geometry_type == 'Polygon':
                    self.addPolygon(coordinates, properties)
                elif geometry_type == 'MultiLineString':
                    self.addMultiLineString(coordinates, properties)
                elif geometry_type == 'LineString':
                    self.addLineString(coordinates, properties)
            map_path = self.college_map._repr_html_()
            return map_path
        except (KeyError, IndexError):
            return "Error: Unable to extract features from GeoJSON data."

    def addMarker(self, coordinates, properties):
        marker = folium.Marker(location=[coordinates[1], coordinates[0]], popup=str(properties))
        marker.add_to(self.college_map)

    def addPolygon(self, coordinates, properties):
        polygon = folium.Polygon(locations=[[point[1], point[0]] for point in coordinates[0]], color='blue', fill=True, fill_color='blue', fill_opacity=0.4, popup=str(properties))
        polygon.add_to(self.college_map)

    def addMultiLineString(self, coordinates, properties):
        for line_coordinates in coordinates:
            ant_path = AntPath(locations=[[point[1], point[0]] for point in line_coordinates], color='red', weight=5, popup=str(properties))
            ant_path.add_to(self.college_map)

    def addLineString(self, coordinates, properties):
        ant_path = AntPath(locations=[[point[1], point[0]] for point in coordinates], color='green', weight=5, popup=str(properties))
        ant_path.add_to(self.college_map)

myCollegeNavigator = CollegeNavigator("https://api.github.com/repos/Alpha-Deivam/College/contents/Paths")

@app.route('/')
def index():
    return render_template('index.html', paths=myCollegeNavigator.geoResources.keys())

@app.route('/display_map', methods=['POST'])
def display_map():
    path_name = request.form['path_name']
    map_html = myCollegeNavigator.displayMap(path_name)
    return render_template('display_map.html', map_html=map_html)

if __name__ == '__main__':
    app.run(debug=True)
