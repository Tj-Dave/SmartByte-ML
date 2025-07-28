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

    # Convert list of dicts to DataFrame
    predictions_df = pd.DataFrame(towns_data)

    # Rename 'name' to 'town' to match with KML geometry dataframe
    if 'name' in predictions_df.columns:
        predictions_df = predictions_df.rename(columns={'name': 'town'})

    # Merge with spatial data
    merged_gdf = kml_gdf.merge(predictions_df, on='town', how='left')

    # Handle missing data
    if merged_gdf['probability'].isnull().any():
        print("Warning: Some towns in the KML did not have matching prediction data and will be dropped.")
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
        city_pred_dict = {
            'flood_probability': city_pred['FloodProbability'].item(),
            'flood_size_score': city_pred['FloodSizeScore'].item(),
            'vulnerability_index': city_pred['VulnerabilityIndex'].item()
        }
        
        towns_data = predictor.disaggregate_predictions(city, city_pred_dict)

        if not towns_data:
            print("[ERROR] The predictor did not return any town-level data.")
            return jsonify({"error": "Could not generate flood predictions for any towns."}), 500

        # 2. Load KML geometries
        kml_processor = KMLProcessor(kml_dir="kml_data")
        print(f"KML directory being checked: {os.path.abspath(kml_processor.kml_dir)}")
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

@app.route('/analytics/<city>/<date>')
def get_analytics_data(city, date):
    """Get comprehensive analytics data for dashboard"""
    try:
        # 1. Get predictions
        city_pred = get_flood_prediction(city, date)
        city_pred_dict = {
            'flood_probability': city_pred['FloodProbability'].item(),
            'flood_size_score': city_pred['FloodSizeScore'].item(),
            'vulnerability_index': city_pred['VulnerabilityIndex'].item()
        }
        
        towns_data = predictor.disaggregate_predictions(city, city_pred_dict)

        if not towns_data:
            return jsonify({"error": "Could not generate analytics data."}), 500

        # 2. Load KML geometries for area calculations
        kml_processor = KMLProcessor(kml_dir="kml_data")
        city_kmls = kml_processor.load_city_kmls(city)
        merged_gdf = merge_predictions_with_geometries(city_kmls, towns_data)
        
        # 3. Calculate analytics
        total_towns = len(merged_gdf)
        total_population = merged_gdf['population_affected'].sum()
        total_area = merged_gdf['size_covered'].sum()
        avg_probability = merged_gdf['probability'].mean()
        
        # Risk distribution
        risk_counts = merged_gdf['probability'].apply(_get_risk_level).value_counts()
        risk_distribution = {
            'low': int(risk_counts.get('low', 0)),
            'medium': int(risk_counts.get('medium', 0)),
            'high': int(risk_counts.get('high', 0))
        }
        
        # Top 5 highest risk towns
        top_risk_towns = merged_gdf.nlargest(5, 'probability')[
            ['town', 'probability', 'population_affected', 'size_covered']
        ].to_dict('records')
        
        # Format probability as percentage for top towns
        for town in top_risk_towns:
            town['probability'] = round(town['probability'] * 100, 1)
            town['population_affected'] = int(town['population_affected'])
            town['size_covered'] = round(town['size_covered'], 1)
        
        analytics_data = {
            'city': city,
            'date': date,
            'summary': {
                'total_towns': total_towns,
                'total_population_affected': int(total_population),
                'total_area_at_risk': round(total_area, 2),
                'average_flood_probability': round(avg_probability * 100, 1),
                'city_flood_probability': round(city_pred_dict['flood_probability'] * 100, 1),
                'vulnerability_index': round(city_pred_dict['vulnerability_index'], 2),
                'flood_size_score': round(city_pred_dict['flood_size_score'], 2)
            },
            'risk_distribution': risk_distribution,
            'top_risk_towns': top_risk_towns,
            'risk_percentages': {
                'low': round((risk_distribution['low'] / total_towns) * 100, 1) if total_towns > 0 else 0,
                'medium': round((risk_distribution['medium'] / total_towns) * 100, 1) if total_towns > 0 else 0,
                'high': round((risk_distribution['high'] / total_towns) * 100, 1) if total_towns > 0 else 0
            }
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        print(f"[ERROR] Analytics: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)