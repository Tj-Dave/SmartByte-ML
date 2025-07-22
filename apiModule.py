import pandas as pd
import numpy as np
from joblib import load

def get_flood_prediction(city, month):
    """
    Generate flood predictions for a specific city and month using forecasted and static features.
    
    Parameters:
    - city (str): Name of the city (e.g., 'Kampala').
    - month (str): Date in YYYY-MM-DD format (e.g., '2026-01-01').
    
    Returns:
    - pd.DataFrame: Single row with date, city, original features, engineered features, and predictions.
    """
    # Load datasets
    try:
        forecast_df = pd.read_csv("scoring_system/city_timeseries_future_2025_2050_rescaled.csv")
        static_df = pd.read_csv("scoring_system/datasets/static/static_features_uganda_cities_rescaled.csv")
    except Exception as e:
        raise ValueError(f"Error loading datasets: {e}")

    # Verify columns
    forecast_columns = ['date', 'city', 'monsoon_intensity', 'climate_change', 'siltation', 
                        'landslide_risks']
    missing_forecast_cols = [col for col in forecast_columns if col not in forecast_df.columns]
    if missing_forecast_cols:
        raise ValueError(f"Missing columns in forecast_df: {missing_forecast_cols}")

    static_columns = ['City', 'TopographyDrainage', 'RiverManagement', 'Deforestation', 'Urbanization',
                      'DamsQuality', 'AgriculturalPractices' ,'Encroachments', 'IneffectiveDisasterPreparedness', 
                      'DrainageSystems', 'InadequatePlanning', 'PoliticalFactors',
                      'CoastalVulnerability', 'Watersheds', 'DeterioratingInfrastructure', 
                      'PopulationScore', 'WetlandLoss']
    missing_static_cols = [col for col in static_columns if col not in static_df.columns]
    if missing_static_cols:
        raise ValueError(f"Missing columns in static_df: {missing_static_cols}")

    # Standardize city names
    city = city.capitalize()
    forecast_df['city'] = forecast_df['city'].str.capitalize()
    static_df['City'] = static_df['City'].str.capitalize()

    # Convert month to datetime
    try:
        month = pd.to_datetime(month, format='%Y-%m-%d', errors='coerce')
        if month is pd.NaT:
            raise ValueError("Invalid date format. Use YYYY-MM-DD (e.g., '2026-01-01').")
    except Exception as e:
        raise ValueError(f"Error parsing month: {e}")

    # Filter forecast data for city and month
    forecast_row = forecast_df[(forecast_df['city'] == city) & 
                              (pd.to_datetime(forecast_df['date']) == month)]
    if forecast_row.empty:
        raise ValueError(f"No forecast data found for city '{city}' and month '{month}'.")

    # Filter static data for city
    static_row = static_df[static_df['City'] == city]
    if static_row.empty:
        raise ValueError(f"No static data found for city '{city}'.")

    # Merge forecast and static data
    merged_data = forecast_row.merge(static_row, left_on='city', right_on='City', how='inner')
    if merged_data.empty:
        raise ValueError(f"Failed to merge data for city '{city}' and month '{month}'.")

    # Drop redundant City column
    merged_data = merged_data.drop(columns=['City'])

    # Define final columns for the core model
    final_columns = [
        'MonsoonIntensity', 'TopographyDrainage', 'RiverManagement', 'Deforestation', 'Urbanization', 
        'ClimateChange', 'DamsQuality', 'Siltation', 'AgriculturalPractices', 'Encroachments', 
        'IneffectiveDisasterPreparedness', 'DrainageSystems', 'CoastalVulnerability', 'Landslides', 
        'Watersheds', 'DeterioratingInfrastructure', 'PopulationScore', 'InadequatePlanning', 
        'PoliticalFactors', 'WetlandLoss'
    ]

    # Rename forecast columns to match final_columns
    merged_data = merged_data.rename(columns={
        'monsoon_intensity': 'MonsoonIntensity',
        'climate_change': 'ClimateChange',
        'siltation': 'Siltation',
        'landslide_risks': 'Landslides'
    })

    # Select and order columns
    input_df = merged_data[['date', 'city'] + final_columns]
    
    # Check for missing values
    missing_values = input_df[final_columns].isna().sum()
    if missing_values.any():
        print(f"Warning: Missing values in input_df:\n{missing_values}")
        input_df[final_columns] = input_df[final_columns].fillna(input_df[final_columns].mean())

    # Load core model
    try:
        scaler = load('Core_system/scaler.pkl')
        flood_model = load('Core_system/flood_prediction_model.pkl')
    except Exception as e:
        raise ValueError(f"Error loading scaler or model: {e}")
    
    # Scale the features
    scaled_data = scaler.transform(input_df[final_columns])
    scaled_df = pd.DataFrame(scaled_data, columns=final_columns, index=input_df.index)

    # scaled_df = input_df.copy()
    scaled_input = scaled_df
    #scaled_df = scaled_df.drop(columns=['date', 'city'], errors='ignore')
    
    # Feature engineering
    scaled_df['RunoffPotential'] = (
        scaled_df['MonsoonIntensity'] + scaled_df['Urbanization'] + scaled_df['Deforestation'] +
        scaled_df['AgriculturalPractices'] + scaled_df['Siltation']
    ) / 5

    scaled_df['DrainageCapacity'] = (
        scaled_df['TopographyDrainage'] + scaled_df['RiverManagement'] +
        scaled_df['DrainageSystems'] + scaled_df['DamsQuality']
    ) / 4

    scaled_df['FloodSpreadPotential'] = (
        scaled_df['WetlandLoss'] + scaled_df['Encroachments'] +
        scaled_df['CoastalVulnerability'] + (1 - scaled_df['Watersheds'])
    ) / 4

    # Predict with core model
    flood_predictions = flood_model.predict(scaled_df)

    # Check prediction output
    if not isinstance(flood_predictions, np.ndarray) or flood_predictions.shape != (1, 3):
        raise ValueError(f"Expected flood_predictions to be a 1x3 NumPy array, got shape {flood_predictions.shape}")

    # Create output DataFrame
    output_df = scaled_input[final_columns].copy()
    output_df['FloodProbability'] = flood_predictions[0, 0]
    output_df['FloodSizeScore'] = flood_predictions[0, 1]
    output_df['VulnerabilityIndex'] = flood_predictions[0, 2]

    # Add engineered features
    output_df['RunoffPotential'] = scaled_df['RunoffPotential']
    output_df['DrainageCapacity'] = scaled_df['DrainageCapacity']
    output_df['FloodSpreadPotential'] = scaled_df['FloodSpreadPotential']

    return output_df