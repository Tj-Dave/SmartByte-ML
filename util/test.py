import json
from disaggregator import FloodPredictor

# Initialize predictor
predictor = FloodPredictor('city_weights.json')

# Sample city-level prediction
kampala_prediction = {
    'flood_probability': 0.65,
    'flood_size_score': 0.8,
    'vulnerability_index': 0.7
}

# Get town-level predictions
town_predictions = predictor.disaggregate_predictions('Kabale', kampala_prediction)

# Output first town result
print(json.dumps(town_predictions[1], indent=2))