import json
import math
from typing import Dict, List

class FloodPredictor:
    def __init__(self, weights_file: str):
        with open(weights_file) as f:
            self.city_data = json.load(f)
        self.size_scaling = 10  # km per unit flood size score
        self.vulnerability_multiplier = 0.6  # % of population affected
    
    def get_city_towns(self, city: str) -> List[str]:
        """Get list of towns for a city"""
        return list(self.city_data.get(city, {}).get('towns', {}).keys())
    
    def disaggregate_predictions(self, city: str, predictions: Dict) -> List[Dict]:
        if city not in self.city_data:
            raise ValueError(f"Unknown city: {city}")
        
        city_weights = self.city_data[city]
        towns_data = []
        
        total_pop = sum(t['population'] for t in city_weights['towns'].values())
        print(f"Total population for {city}: {total_pop}")  # Debug line
        
        for town_name, town_weights in city_weights['towns'].items():
            try:
                pop_factor = town_weights['population'] / total_pop
                
                town_pred = {
                    'name': town_name,
                    'probability': min(max(
                        predictions['flood_probability'] * town_weights['flood_weight'], 
                        0.05), 0.95),
                    'size_covered': (predictions['flood_size_score'] * 
                                town_weights['size_weight'] * 
                                pop_factor * self.size_scaling),
                    'population_affected': math.ceil(
                        predictions['vulnerability_index'] * 
                        town_weights['vulnerability_weight'] * 
                        town_weights['population'] * 
                        self.vulnerability_multiplier),
                    'raw_weights': town_weights
                }
                towns_data.append(town_pred)
                
            except Exception as e:
                print(f"Error processing {town_name}: {str(e)}")
                continue
                
        print(f"Generated predictions for {len(towns_data)} towns")
        return towns_data
    
    def _calculate_probability(self, city_prob: float, weight: float) -> float:
        """Calculate town-specific flood probability"""
        base = city_prob * weight
        return min(max(base, 0.05), 0.95)  # Keep within 5%-95% range
    
    def _calculate_size(self, city_size: float, weight: float, pop_factor: float) -> float:
        """Calculate affected area in km²"""
        return (city_size * weight * pop_factor) * self.size_scaling
    
    def _calculate_affected_pop(self, vuln_index: float, weight: float, population: int) -> int:
        """Estimate affected population"""
        return math.ceil(vuln_index * weight * population * self.vulnerability_multiplier)
    