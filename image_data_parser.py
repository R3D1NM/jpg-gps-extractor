"""
Image GPS information parser
get GPS info from jpg(jpeg) files
get datetime of the images (time when the photo taken, not creation time)
map out the information and image file name and then export as metadata.csv
pin where the photos taken on the map and mark with datetime
connect the pins with the same date
export the map as html file (image_gps_map_with_route.html)
"""

import os
from PIL import Image
from PIL.ExifTags import TAGS
import pandas as pd
from datetime import datetime
import folium
import numpy as np

def get_gps_info(exif_data):
    latitude = None
    longitude = None

    # Get GPS data from GPSInfo tag
    for tag, value in exif_data.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == 'GPSInfo':
            if isinstance(value, dict):
                latitude_ref = value.get(1, None)
                latitude = value.get(2, None)
                longitude_ref = value.get(3, None)
                longitude = value.get(4, None)
                break
    # Convert data to degrees
    if latitude and longitude and latitude_ref and longitude_ref:
        latitude = convert_to_degrees(latitude)
        longitude = convert_to_degrees(longitude)
        if latitude_ref.upper() == 'S':
            latitude = -latitude
        if longitude_ref.upper() == 'W':
            longitude = -longitude

    return latitude, longitude


def convert_to_degrees(value):
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)


def get_original_datetime(exif_data):
    # Get time data from DateTimeOriginal tag
    for tag, value in exif_data.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == 'DateTimeOriginal':
            return value

    return None

# main
directory_path = "JohnDoe"

file_list = []
latitude_list = []
longitude_list = []
ctime_list = []
org_date_list = []

# Extract meta data from image files
for file_name in os.listdir(directory_path):
    # Only jpg or jpeg formats
    if file_name.lower().endswith(",jpg") or file_name.lower().endswith("jpeg"):
        image_path = os.path.join(directory_path, file_name)
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                latitude, longitude = get_gps_info(exif_data)
                original_datetime = get_original_datetime(exif_data)
            else:
                latitude, longitude, original_datetime = None, None, None

            # Convert creation time into timestamp
            creation_time = os.path.getctime(image_path)
            creation_time = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')

            file_list.append(file_name)
            latitude_list.append(latitude)
            longitude_list.append(longitude)
            ctime_list.append(creation_time)
            org_date_list.append(original_datetime)
            print(
                f"[{file_name}] latitude: {latitude} longitude: {longitude} creation time: {creation_time} original datetime: {original_datetime}")

# Save meta data into csv file
df = pd.DataFrame(
    {'file_name': file_list, "latitude": latitude_list, "longitude": longitude_list, "creation_time": ctime_list,
     "original_datetime": org_date_list})
df.to_csv("metadata.csv", index=False)
print("Output Saved: metadata.csv")


# Prepare map
map_object = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=10)

# Sort DataFrame by original_datetime
df.sort_values(by='original_datetime', inplace=True)
print(df.head(10))

# Adding markers for each image's GPS location
for index, row in df.iterrows():
    # Check if latitude and longitude are not NaN
    if not np.isnan(row['latitude']) and not np.isnan(row['longitude']):
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"File: {row['file_name']}<br>Date: {row['original_datetime']}"
        ).add_to(map_object)

# Adding route as a PolyLine
previous_date = None
previous_point = None

for index, row in df.iterrows():
    if not np.isnan(row['latitude']) and not np.isnan(row['longitude']):
        current_date = row['original_datetime'][:10]  # Extract date in YYYY-MM-DD format

        if previous_date == current_date:
            folium.PolyLine(locations=[previous_point, [row['latitude'], row['longitude']]], color='blue').add_to(map_object)

        previous_date = current_date
        previous_point = [row['latitude'], row['longitude']]


# Save the map to an HTML file
map_object.save("image_gps_map_with_route.html")
print("Map with GPS locations and route saved: image_gps_map_with_route.html")