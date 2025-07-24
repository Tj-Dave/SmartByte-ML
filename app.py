from flask import Flask, render_template, request, jsonify
import json
import geopandas as gpd
from shapely.geometry import mapping, MultiPolygon
from util.kmlprocessor import KMLProcessor
from util.disaggregator import FloodPredictor
from datetime import datetime
import random
from apiModule import get_flood_prediction
import pandas as pd
import os
import traceback

app = Flask(__name__)

# Initialize the predictor
predictor = FloodPredictor(os.path.join(os.path.dirname(__file__), 'city_weights.json'))

def merge_predictions_with_geometries(kml_gdf, towns_data):
    """Attach prediction data to KML geometries"""
    # Convert towns_data to DataFrame
    predictions_df = pd.DataFrame(towns_data)
    predictions_df['town'] = predictions_df['name']  # Create matching column
    
    # Merge with spatial data
    merged_gdf = kml_gdf.merge(
        predictions_df,
        on='town',
        how='left'
    )
    
    # Handle missing data
    if merged_gdf.isnull().any().any():
        print("Warning: Some towns lacked prediction data")
        merged_gdf = merged_gdf.dropna(subset=['probability'])
    
    return merged_gdf

def _get_risk_level(probability):
    """Classify risk for visualization"""
    if probability < 0.3: return "low"
    elif probability < 0.6: return "medium"
    else: return "high"

def generate_geojson(gdf, output_format='featurecollection'):
    """Convert GeoDataFrame to GeoJSON with multipolygon option"""
    if output_format == 'multipolygon':
        # Combine all polygons into one MultiPolygon feature
        multipolygon = MultiPolygon(gdf.geometry.tolist())
        properties = {
            'city': gdf.iloc[0].get('city', ''),
            'town_count': len(gdf),
            'combined_risk': gdf['probability'].mean()
        }
        
        feature = {
            "type": "Feature",
            "geometry": mapping(multipolygon),
            "properties": properties
        }
        
        return {"type": "FeatureCollection", "features": [feature]}
    
    else:  # Default: FeatureCollection with individual features
        features = []
        for _, row in gdf.iterrows():
            features.append({
                "type": "Feature",
                "geometry": mapping(row.geometry),
                "properties": {
                    "town": row['town'],
                    "probability": row['probability'],
                    "size_covered": row['size_covered'],
                    "population_affected": row['population_affected'],
                    "risk_level": _get_risk_level(row['probability'])
                }
            })
        
        return {"type": "FeatureCollection", "features": features}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/flood-map/<city>/<date>')
def generate_flood_map(city, date):
    try:
        # 1. Get predictions
        city_pred = get_flood_prediction(city, date)
        towns_data = predictor.disaggregate_predictions(city, {
            'flood_probability': city_pred['FloodProbability'],
            'flood_size_score': city_pred['FloodSizeScore'],
            'vulnerability_index': city_pred['VulnerabilityIndex']
        })
        
        # 2. Load KML geometries
        kml_processor = KMLProcessor()
        city_kmls = kml_processor.load_city_kmls(city)
        
        # 3. Merge data
        merged_gdf = merge_predictions_with_geometries(city_kmls, towns_data)
        
        # 4. Generate GeoJSON
        geojson = generate_geojson(merged_gdf, output_format='featurecollection')
        
        return jsonify(geojson)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)