from fastkml import kml
import os
from typing import List, Union

# Define the path to your KML file
kml_file_path = "kml_data/Kampala_Kinawataka.kml"

# --- Pre-check: Ensure the KML file exists ---
if not os.path.exists(kml_file_path):
    print(f"Error: File not found at {kml_file_path}")
    exit()

def get_features_recursive(kml_object: Union[kml.KML, kml.Folder, kml.Document], level=0) -> List:
    """
    Recursively extracts all Placemark features that contain geometry from a KML object.
    It traverses through KML, Document, and Folder objects.
    """
    indent = "  " * level # For visual indentation in output
    all_placemarks_with_geometry = []

    print(f"{indent}Entering {type(kml_object).__name__} at level {level}")

    # Check if the current KML object has features to iterate over
    if not hasattr(kml_object, 'features') or not kml_object.features:
        print(f"{indent}  {type(kml_object).__name__} at level {level} has no iterable features or features are empty.")
        return all_placemarks_with_geometry

    print(f"{indent}  Iterating features of {type(kml_object).__name__} at level {level}:")
    for i, feature in enumerate(kml_object.features):
        feature_name = getattr(feature, 'name', 'Unnamed Feature')
        feature_type = type(feature).__name__
        print(f"{indent}    [{i}] Found feature: Type={feature_type}, Name='{feature_name}'")

        # If the feature is a Placemark
        if isinstance(feature, kml.Placemark):
            print(f"{indent}      It's a Placemark. Checking for geometry...")
            if hasattr(feature, 'geometry') and feature.geometry:
                geometry_type = type(feature.geometry).__name__
                print(f"{indent}        SUCCESS: Placemark '{feature_name}' has geometry of type: {geometry_type}")
                all_placemarks_with_geometry.append(feature)
            else:
                print(f"{indent}        WARNING: Placemark '{feature_name}' found, but geometry attribute is missing or empty.")
        
        # If the feature is a container (Folder or Document), recurse into it
        elif isinstance(feature, (kml.Folder, kml.Document)):
            print(f"{indent}      It's a container ({feature_type}). Recursing...")
            # Extend the list with features found in the nested container
            all_placemarks_with_geometry.extend(get_features_recursive(feature, level + 1))
        else:
            print(f"{indent}      Skipping non-Placemark, non-container feature type: {feature_type}")
            
    print(f"{indent}Exiting {type(kml_object).__name__} at level {level}. Found {len(all_placemarks_with_geometry)} geometries in this branch.")
    return all_placemarks_with_geometry

# --- Main script execution ---
try:
    print(f"Starting KML parsing for {kml_file_path}")

    # Open the KML file in binary read mode ('rb')
    with open(kml_file_path, 'rb') as f:
        doc_bytes = f.read() # Read the entire content as bytes

    # Create a KML object and parse the bytes content
    k = kml.KML()
    k.from_string(doc_bytes)

    print("\n--- Detailed KML Traversal Log ---")
    # Start the recursive feature extraction from the root KML object
    found_features = get_features_recursive(k)

    # --- Summary of results ---
    print(f"\n--- Summary for {kml_file_path} ---")
    print(f"Total features with geometry found by test script: {len(found_features)}")

    if found_features:
        print(f"First found feature's name: {getattr(found_features[0], 'name', 'N/A')}")
        print(f"First found feature's geometry type: {type(found_features[0].geometry).__name__}")
        
        # Optionally, print a snippet of coordinates if it's a Polygon
        if isinstance(found_features[0].geometry, (kml.Polygon, kml.MultiPolygon)):
            print("First polygon coordinates (showing first 5 and last 5 tuples):")
            # Accessing coordinates from a LinearRing within outerBoundaryIs
            if hasattr(found_features[0].geometry, 'outer_boundary_is') and \
               hasattr(found_features[0].geometry.outer_boundary_is, 'coordinates'):
                coords = list(found_features[0].geometry.outer_boundary_is.coordinates)
                print(f"  Total coordinate tuples: {len(coords)}")
                print(f"  First 5: {coords[:5]}")
                print(f"  Last 5: {coords[-5:]}")
            else:
                print("  Could not retrieve specific polygon coordinates from the first feature's outer boundary.")
    else:
        print("No features with geometry were successfully extracted.")

except Exception as e:
    print(f"\nAn error occurred during testing: {e}")