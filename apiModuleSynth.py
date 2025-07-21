# --- apiModule.py ---
import pandas as pd
import numpy as np
from joblib import load

# Load datasets
forecast_df = pd.read_csv("scoring_system/datasets/synthetic_downsampled_balanced.csv")
static_df = pd.read_csv("scoring_system/datasets/static/static_features_uganda_cities_.csv")

def get_prediction_dataframe(city, date):
    city = city.capitalize()
    forecast_row = forecast_df[(forecast_df['city'] == city) & (forecast_df['date'] == date)]
    if forecast_row.empty:
        raise ValueError("No forecast data found for given city and date.")

    static_row = static_df[static_df['City'] == city]
    if static_row.empty:
        raise ValueError("No static data found for given city.")

    static_features = static_row.drop(columns=['City']).iloc[0].to_dict()

    # Combine the 5 target columns from the forecast with static features
    selected_columns = [
        "monsoon_intensity", "climate_change", "siltation",
        "agricultural_practices", "landslide_risks"
    ]
    dynamic_data = forecast_row[selected_columns].iloc[0].to_dict()

    # Rename keys to match flood model schema
    mapped = {
        "MonsoonIntensity": dynamic_data.get("monsoon_intensity"),
        "ClimateChange": dynamic_data.get("climate_change"),
        "Siltation": dynamic_data.get("siltation"),
        "AgriculturalPractices": dynamic_data.get("agricultural_practices"),
        "Landslides": dynamic_data.get("landslide_risks")
    }

    final_data = {
        **mapped,
        **static_features
    }

    final_columns = [
        "MonsoonIntensity", "TopographyDrainage", "RiverManagement", "Deforestation", "Urbanization",
        "ClimateChange", "DamsQuality", "Siltation", "AgriculturalPractices", "Encroachments",
        "IneffectiveDisasterPreparedness", "DrainageSystems", "CoastalVulnerability", "Landslides",
        "Watersheds", "DeterioratingInfrastructure", "PopulationScore", "WetlandLoss",
        "InadequatePlanning", "PoliticalFactors"
    ]

    final_df = pd.DataFrame([{col: final_data.get(col, None) for col in final_columns}])
    
    # Scale
    scaler = load('Core_system/scaler.pkl')
    res_df = scaler.transform(final_df)
    res_df = pd.DataFrame(res_df, columns=final_columns)

    # Feature Engineering
    res_df['RunoffPotential'] = (
        res_df['MonsoonIntensity'] + res_df['Urbanization'] + res_df['Deforestation'] +
        res_df['AgriculturalPractices'] + res_df['Siltation']
    ) / 5

    res_df['DrainageCapacity'] = (
        res_df['TopographyDrainage'] + res_df['RiverManagement'] +
        res_df['DrainageSystems'] + res_df['DamsQuality']
    ) / 4

    res_df['FloodSpreadPotential'] = (
        res_df['WetlandLoss'] + res_df['Encroachments'] +
        res_df['CoastalVulnerability'] + (1 - res_df['Watersheds'])
    ) / 4

    res_df['VulnerabilityIndex'] = (
        res_df['PopulationScore'] + res_df['InadequatePlanning'] +
        res_df['IneffectiveDisasterPreparedness'] + res_df['PoliticalFactors']
    ) / 4

    res_df['FloodSizeScore'] = (
        res_df['RunoffPotential'] + res_df['FloodSpreadPotential'] - res_df['DrainageCapacity']
    )

    # Predict
    flood_model = load('Core_system/flood_prediction_model.pkl')
    flood_prediction = flood_model.predict(res_df)
    
    if flood_prediction.shape != (1, 3):
        raise ValueError(f"Expected shape (1, 3), got {flood_prediction.shape}")
    
    result_df = pd.DataFrame([{
        "FloodProbability_result": float(flood_prediction[0, 0]),
        "FloodSizeScore_result": float(flood_prediction[0, 1]),
        "VulnerabilityIndex_result": float(flood_prediction[0, 2])
    }])

    return pd.concat([res_df, result_df], axis=1)
