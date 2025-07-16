import pandas as pd
from pycaret.regression import load_model, predict_model

# Load datasets
forecast_df = pd.read_csv("scoring_system/datasets/synthetic_features_with_noise_2026_2050.csv")
static_df = pd.read_csv("scoring_system/datasets/static/static_features_uganda_cities_.csv")

# Load models
models = {
    "MonsoonIntensity": load_model("scoring_system/best_model_monsoon_intensity"),
    "ClimateChange": load_model("scoring_system/best_model_climate_change"),
    "Siltation": load_model("scoring_system/best_model_siltation"),
    "AgriculturalPractices": load_model("scoring_system/best_model_agricultural_practices"),
    "Landslides": load_model("scoring_system/best_model_landslide_risks")
}

def get_prediction_dataframe(city, date):
    forecast_row = forecast_df[(forecast_df['city'] == city) & (forecast_df['date'] == date)]
    if forecast_row.empty:
        raise ValueError("No forecast data found for given city and date.")

    # Predict using models (rounded int output)
    predictions = {}
    for name, model in models.items():
        pred = predict_model(model, data=forecast_row)
        predictions[name] = int(round(pred.iloc[0, -1]))  # round and cast to int

    static_row = static_df[static_df['City'] == city]
    if static_row.empty:
        raise ValueError("No static data found for given city.")

    static_features = static_row.drop(columns=['City']).iloc[0].to_dict()

    final_data = {
        "MonsoonIntensity": predictions.get("MonsoonIntensity"),
        "ClimateChange": predictions.get("ClimateChange"),
        "Siltation": predictions.get("Siltation"),
        "AgriculturalPractices": predictions.get("AgriculturalPractices"),
        "Landslides": predictions.get("Landslides"),
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
    return final_df
