import os
import geopandas as gpd
import pandas as pd
from pykml import parser
from shapely.geometry import Point, LineString, Polygon

class KMLProcessor:
    def __init__(self, kml_dir="kml_data"):
        self.kml_dir = kml_dir
        # KML namespace for pykml's lxml parser
        self.namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    def _kml_to_shapely(self, placemark):
        """
        Converts a pykml Placemark object to a shapely geometry.
        Supports Point, LineString, and Polygon (with inner holes).
        """
        # Search for any geometry type within the Placemark
        geom_node = placemark.find('.//kml:Point', self.namespace)
        if geom_node is not None:
            coords_str = geom_node.coordinates.text.strip()
            try:
                lon, lat, *_ = map(float, coords_str.split(','))
                return Point(lon, lat)
            except (ValueError, IndexError):
                return None

        geom_node = placemark.find('.//kml:LineString', self.namespace)
        if geom_node is not None:
            coords_str = geom_node.coordinates.text.strip()
            coords = []
            for point_str in coords_str.split():
                try:
                    lon, lat, *_ = map(float, point_str.split(','))
                    coords.append((lon, lat))
                except (ValueError, IndexError):
                    continue
            return LineString(coords) if coords else None

        geom_node = placemark.find('.//kml:Polygon', self.namespace)
        if geom_node is not None:
            # Extract outer boundary
            outer_ring_node = geom_node.find('.//kml:outerBoundaryIs/kml:LinearRing', self.namespace)
            if outer_ring_node is None:
                return None
            
            outer_coords_str = outer_ring_node.coordinates.text.strip()
            outer_coords = []
            for point_str in outer_coords_str.split():
                try:
                    lon, lat, *_ = map(float, point_str.split(','))
                    outer_coords.append((lon, lat))
                except (ValueError, IndexError):
                    continue
            
            if not outer_coords:
                return None

            # Extract inner boundaries (holes)
            inner_rings_nodes = geom_node.findall('.//kml:innerBoundaryIs/kml:LinearRing', self.namespace)
            inner_coords_list = []
            for inner_ring_node in inner_rings_nodes:
                inner_coords_str = inner_ring_node.coordinates.text.strip()
                inner_coords = []
                for point_str in inner_coords_str.split():
                    try:
                        lon, lat, *_ = map(float, point_str.split(','))
                        inner_coords.append((lon, lat))
                    except (ValueError, IndexError):
                        continue
                if inner_coords:
                    inner_coords_list.append(inner_coords)
            
            return Polygon(outer_coords, inner_coords_list)

        return None

    def load_city_kmls(self, city_name):
        """Load all KML files for a city and return as a GeoDataFrame"""
        gdf_list = []
        
        for filename in os.listdir(self.kml_dir):
            if filename.startswith(city_name) and filename.endswith('.kml'):
                # Extract "Bwaise" from "Kampala_Bwaise.kml"
                town_name = filename[len(city_name)+1:-4]  
                kml_path = os.path.join(self.kml_dir, filename)
                
                # Use 'rb' for binary read mode, as lxml prefers bytes
                with open(kml_path, 'rb') as f:
                    root = parser.parse(f).getroot()

                # Find all Placemark elements in the KML file
                placemarks = root.iterdescendants('{http://www.opengis.net/kml/2.2}Placemark')
                
                for placemark in placemarks:
                    geometry = self._kml_to_shapely(placemark)
                    if geometry:
                        # You could also extract the placemark name if needed:
                        # name_node = placemark.find('.//kml:name', self.namespace)
                        # name = name_node.text if name_node is not None else town_name
                        gdf = gpd.GeoDataFrame({'town': [town_name]}, geometry=[geometry], crs="EPSG:4326")
                        gdf_list.append(gdf)
        
        if not gdf_list:
            raise ValueError(f"No valid geometries found in KML files for {city_name}")
            
        return gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))