from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import random
from apiModule import get_prediction_dataframe

app = Flask(__name__)

# Mock data generator (replace with your actual API call)
def get_prediction_data(city, date):
    """Replace this with your actual API call"""
    try:
        df = get_prediction_dataframe(city, date)
        if not df.empty:
            row = df.iloc[0]
            return {
                'city': city,
                'date': date,
                'flood_probability': float(row['FloodProbability_result']),
                'flood_size_score': float(row['FloodSizeScore_result']),
                'vulnerability_index': float(row['VulnerabilityIndex_result'])
            }
        else:
            raise ValueError("No data available")
    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")

def convert_size_score_to_readable(score):
    """Convert size score to something people understand"""
    if score <= 0.2:
        return {"level": "Puddles", "description": "Small street flooding", "icon": "💧"}
    elif score <= 0.4:
        return {"level": "Neighborhood", "description": "Several blocks affected", "icon": "🌊"}
    elif score <= 0.6:
        return {"level": "District", "description": "Large area coverage", "icon": "🌀"}
    elif score <= 0.8:
        return {"level": "City-wide", "description": "Major urban flooding", "icon": "🌪️"}
    else:
        return {"level": "Regional", "description": "Widespread emergency", "icon": "⚠️"}

def get_risk_level(probability, size_score, vulnerability):
    """Calculate overall risk level"""
    overall_risk = (probability * 0.4 + size_score * 0.3 + vulnerability * 0.3)
    
    if overall_risk <= 0.3:
        return {"level": "Low", "color": "#2ecc71", "advice": "Normal precautions sufficient"}
    elif overall_risk <= 0.6:
        return {"level": "Moderate", "color": "#f39c12", "advice": "Stay alert, prepare emergency kit"}
    elif overall_risk <= 0.8:
        return {"level": "High", "color": "#e74c3c", "advice": "Avoid low-lying areas, prepare evacuation plan"}
    else:
        return {"level": "Critical", "color": "#c0392b", "advice": "Emergency preparations required immediately"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    city = data.get('city')
    date = data.get('date')
    
    try:
        # Get prediction data (replace with your actual API call)
        prediction = get_prediction_data(city, date)
        
        # Convert to readable formats
        flood_size = convert_size_score_to_readable(prediction['flood_size_score'])
        risk_level = get_risk_level(
            prediction['flood_probability'],
            prediction['flood_size_score'],
            prediction['vulnerability_index']
        )
        
        # Calculate impact indicators
        people_affected = int(prediction['flood_size_score'] * prediction['vulnerability_index'] * 9500)
        duration_hours = int(prediction['flood_probability'] * 48)  # 0-48 hours
        
        response = {
            'city': city,
            'date': date,
            'flood_probability': round(prediction['flood_probability'] * 100, 1),
            'flood_size': flood_size,
            'vulnerability_index': round(prediction['vulnerability_index'] * 100, 1),
            'risk_level': risk_level,
            'people_affected': people_affected,
            'duration_hours': duration_hours,
            'raw_scores': {
                'probability': prediction['flood_probability'],
                'size': prediction['flood_size_score'],
                'vulnerability': prediction['vulnerability_index']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)