import cv2
import numpy as np
import pandas as pd
import os
import glob
import math


def detect_scribbles_and_score(file_paths):
    """
    Analyzes plans for red/brown scribbles (the check marks), visualizes them,
    and calculates H/M scores based on specific set logic (0, 1, 2, 3),
    using distance-based assignment to the nearest corner.
    """

    results_data = []

    # 1. Define Color Thresholds for the "Red/Brown X" Scribble (HSV)
    # Tuned to reliably catch dark red/maroon scribbles by using lower Saturation (S) and Value (V).

    # Range 1: Broadened Red near Hue=0
    lower_red1 = np.array([0, 30, 30], dtype=np.uint8)
    upper_red1 = np.array([20, 255, 255], dtype=np.uint8)

    # Range 2: Broadened Red near Hue=180
    lower_red2 = np.array([160, 30, 30], dtype=np.uint8)
    upper_red2 = np.array([180, 255, 255], dtype=np.uint8)

    MIN_SCRIBBLE_AREA = 300

    for file_path in file_paths:
        filename = os.path.basename(file_path)

        # Load the image
        img = cv2.imread(file_path)

        # CRITICAL FIX: Skip the file if it could not be loaded
        if img is None:
            print(f"Skipping file: {file_path}. Error: Image could not be read by OpenCV.")
            continue

            # Convert to HSV color space for stable color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Create masks for red color and combine them
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = mask1 + mask2

        # Clean up mask (Morphological operations)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Find contours of the detected red areas
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height, width = img.shape[:2]

        # Define Corner Coordinates (based on image size)
        corners = {
            'c1': (width, 0),  # Top Right (TR) - (X_max, Y_min)
            'c2': (width, height),  # Bottom Right (BR) - (X_max, Y_max)
            'c3': (0, height),  # Bottom Left (BL) - (X_min, Y_max)
            'c4': (0, 0)  # Top Left (TL) - (X_min, Y_min)
        }

        active_corners = {'c1': False, 'c2': False, 'c3': False, 'c4': False}
        img_viz = img.copy()

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > MIN_SCRIBBLE_AREA:
                x, y, w, h = cv2.boundingRect(cnt)
                center_x = x + w // 2
                center_y = y + h // 2

                # --- NEW LOGIC: FIND CLOSEST CORNER BY DISTANCE ---
                min_distance = float('inf')
                closest_corner = None

                for corner_name, (cx, cy) in corners.items():
                    # Calculate Euclidean distance from scribble center to corner
                    distance = math.sqrt((cx - center_x) ** 2 + (cy - center_y) ** 2)

                    if distance < min_distance:
                        min_distance = distance
                        closest_corner = corner_name

                # Assign the detection to the closest corner
                if closest_corner:
                    active_corners[closest_corner] = True
                    corner_label = f"Found {closest_corner.upper()} "
                else:
                    corner_label = "Found (Error)"

                # VISUALIZATION: Draw green box and label
                cv2.rectangle(img_viz, (x, y), (x + w, y + h), (0, 255, 0), 5)
                cv2.putText(img_viz, corner_label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)

        # --- LOGIC ENGINE (Applies scores H/M based on set and file type) ---
        row = {'filename': filename, 'H2': 0, 'H3': 0, 'H4': 0, 'H5': 0, 'M2': 0, 'M3': 0, 'M4': 0, 'M5': 0}

        # Determine set_id (0, 1, 2, 3) and plan_type from filename
        parts = filename.split('_')
        set_id = -1
        for part in parts:
            if part.isdigit():
                set_id = int(part)
                break

        plan_type = ""
        if "ground" in filename:
            plan_type = "ground"
        elif "mid" in filename:
            plan_type = "mid"
        elif "top" in filename:
            plan_type = "top"

        # Logic for H scores (Set 0 & 1)
        if set_id == 0:
            if plan_type == "ground" and active_corners['c1']:
                row['H2'] = 1
            elif plan_type == "mid":
                if active_corners['c2']: row['H3'] = 1
                if active_corners['c3']: row['H4'] = 1
            elif plan_type == "top" and active_corners['c4']:
                row['H5'] = 1

        elif set_id == 1:
            if plan_type == "ground" and active_corners['c1']:
                row['H2'] = 1
            elif plan_type == "mid":
                if active_corners['c2']: row['H3'] = 1
                if active_corners['c4']: row['H4'] = 1
            elif plan_type == "top" and active_corners['c3']:
                row['H5'] = 1

        # Logic for M scores (Set 2 & 3)
        elif set_id == 2:
            if plan_type == "ground" and active_corners['c3']:
                row['M2'] = 1
            elif plan_type == "mid":
                if active_corners['c4']: row['M3'] = 1
                if active_corners['c1']: row['M5'] = 1
            elif plan_type == "top" and active_corners['c2']:
                row['M4'] = 1

        elif set_id == 3:
            if plan_type == "ground" and active_corners['c3']:
                row['M2'] = 1
            elif plan_type == "mid":
                if active_corners['c4']: row['M3'] = 1
                if active_corners['c2']: row['M5'] = 1
            elif plan_type == "top" and active_corners['c1']:
                row['M4'] = 1

        results_data.append(row)

        # Save image results in the directory where the script is executed
        output_filename = f"processed_{filename}"
        cv2.imwrite(output_filename, img_viz)

    # Create DataFrame and Export
    df = pd.DataFrame(results_data)
    final_cols = ['filename', 'H2', 'H3', 'H4', 'H5', 'M2', 'M3', 'M4', 'M5']
    df_final = df[final_cols]
    df_final = df_final.sort_values(by='filename').reset_index(drop=True)

    output_csv_filename = "scribble_analysis_all.csv"
    df_final.to_csv(output_csv_filename, index=False)

    print(f"Analysis complete. Results saved to: {output_csv_filename}")
    print("\n--- Processed Files ---")

    # Use to_string() to avoid the 'tabulate' dependency issue
    print(df_final.to_string(index=False))

    return df_final


# --- EXECUTION BLOCK ---
if __name__ == "__main__":

    # 📌 Folder to process as specified by the user
    SEARCH_PATH = "/Users/amirthavarshini/Desktop/VR-studies/testing/split_levels"

    # Look for all PNG and JPG files in that folder
    files_to_process_png = glob.glob(os.path.join(SEARCH_PATH, "*.png"))
    files_to_process_jpg = glob.glob(os.path.join(SEARCH_PATH, "*.jpg"))
    files_to_process = sorted(files_to_process_png + files_to_process_jpg)

    if not files_to_process:
        print(f"Error: No PNG or JPG files found in '{SEARCH_PATH}'. Please verify the path and file extensions.")
    else:
        print(f"Found {len(files_to_process)} images to process from {SEARCH_PATH}.")
        detect_scribbles_and_score(files_to_process)