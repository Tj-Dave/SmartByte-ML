import os
from fastkml import kml
import geopandas as gpd
from shapely.geometry import MultiPolygon
import pandas as pd

class KMLProcessor:
    def __init__(self, kml_dir="kml_data"):
        self.kml_dir = kml_dir
    
    def load_city_kmls(self, city_name):
        """Load all KML files for a city and return as GeoDataFrame"""
        gdf_list = []
        
        for filename in os.listdir(self.kml_dir):
            if filename.startswith(city_name) and filename.endswith('.kml'):
                town_name = filename[len(city_name)+1:-4]  # Extract "Bwaise" from "Kampala_Bwaise.kml"
                kml_path = os.path.join(self.kml_dir, filename)
                
                with open(kml_path, 'r') as f:
                    k = kml.KML()
                    k.from_string(f.read().encode('utf-8'))
                    print(type(k.features))
                    print(k.features)
                    features = list(k.features)
                    if features:
                        geometry = features[0].geometry
                        gdf = gpd.GeoDataFrame({'town': [town_name]}, geometry=[geometry], crs="EPSG:4326")
                        gdf_list.append(gdf)
        
        if not gdf_list:
            raise ValueError(f"No KML files found for {city_name}")
            
        return gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))