import cv2
import numpy as np
import pandas as pd
import os
import glob

# --- 1. COLOR DEFINITIONS (HSV) ---

# Red Cross (Wide range for robust detection of red/maroon)
L_RED1 = np.array([0, 50, 50], dtype=np.uint8)
U_RED1 = np.array([25, 255, 255], dtype=np.uint8)
L_RED2 = np.array([155, 50, 50], dtype=np.uint8)
U_RED2 = np.array([180, 255, 255], dtype=np.uint8)

# Green Patch
L_GREEN = np.array([35, 50, 50], dtype=np.uint8)
U_GREEN = np.array([85, 255, 255], dtype=np.uint8)

# Brown Patch (Orange-ish)
L_BROWN = np.array([5, 50, 50], dtype=np.uint8)
U_BROWN = np.array([30, 200, 200], dtype=np.uint8)

# Blue Patch
L_BLUE = np.array([90, 50, 50], dtype=np.uint8)
U_BLUE = np.array([130, 255, 255], dtype=np.uint8)

# Grey Patch (Low Saturation, specific Value range to avoid black lines or white paper)
L_GREY = np.array([0, 0, 50], dtype=np.uint8)
U_GREY = np.array([180, 40, 180], dtype=np.uint8)

MIN_AREA = 300


# --- 2. UTILITY FUNCTIONS ---

def get_corner_bbox(img_shape, corner_name):
    """Returns (x, y, w, h) for the specific quadrant."""
    h, w = img_shape[:2]
    cx, cy = w // 2, h // 2

    if corner_name == 'c1': return (cx, 0, w - cx, cy)  # Top Right
    if corner_name == 'c2': return (cx, cy, w - cx, h - cy)  # Bottom Right
    if corner_name == 'c3': return (0, cy, cx, h - cy)  # Bottom Left
    if corner_name == 'c4': return (0, 0, cx, cy)  # Top Left
    return (0, 0, w, h)


def find_color_in_corner(img, lower, upper, corner_name):
    """Finds bounding box of a color ONLY if it exists inside the specified corner."""
    if img is None: return None

    # 1. Crop to corner first to avoid noise from other areas
    cx, cy, cw, ch = get_corner_bbox(img.shape, corner_name)
    roi = img[cy:cy + ch, cx:cx + cw]

    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_roi, lower, upper)

    # Special handling for Red (wrap around)
    if np.array_equal(lower, L_RED1):
        mask += cv2.inRange(hsv_roi, L_RED2, U_RED2)

    # Clean mask
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest_bbox = None
    max_area = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area and area > MIN_AREA:
            max_area = area
            # Get bbox relative to ROI
            rx, ry, rw, rh = cv2.boundingRect(cnt)
            # Convert to global coordinates
            largest_bbox = (cx + rx, cy + ry, rw, rh)

    return largest_bbox


def check_overlap(bbox1, bbox2):
    """Checks if two bounding boxes overlap."""
    if bbox1 is None or bbox2 is None: return 0

    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    overlap_w = min(x1 + w1, x2 + w2) - max(x1, x2)
    overlap_h = min(y1 + h1, y2 + h2) - max(y1, y2)

    if overlap_w > 0 and overlap_h > 0:
        return 1
    return 0


def get_file_info(filename):
    """Parses adel_1_ground_plan.png -> set_id='adel_1', type='ground'."""
    base = filename.replace('processed_', '')
    for t in ['ground', 'mid', 'top']:
        if f'_{t}' in base:
            parts = base.split(f'_{t}')
            return parts[0], t
    return None, None


# --- 3. MAIN LOGIC ---

def run_logic_analysis(folder_path):
    # Find files
    files = sorted(glob.glob(os.path.join(folder_path, "*.*")))
    files = [f for f in files if f.lower().endswith(('.png', '.jpg'))]

    # Group files
    groups = {}
    for f in files:
        sid, ftype = get_file_info(os.path.basename(f))
        if sid:
            if sid not in groups: groups[sid] = {'ground': None, 'mid': None, 'top': None}
            groups[sid][ftype] = cv2.imread(f)

    results = []

    for sid, imgs in groups.items():
        if not (imgs['ground'] is not None and imgs['mid'] is not None and imgs['top'] is not None):
            continue

        # Get Set Number (0, 1, 2, 3)
        try:
            set_num = int(sid.split('_')[-1])
        except:
            continue

        # Initialize scores
        H1H4 = 0  # Green/Ground vs Red/Mid
        H3H6 = 0  # Brown/Top vs Red/Mid (Maps to your H6H3 logic)
        M1M3 = 0  # Blue/Ground vs Red/Mid
        M4M6 = 0  # Grey/Top vs Red/Mid (Maps to your M6M4 logic)

        # --- LOGIC SWITCH ---

        # SET 0
        if set_num == 0:
            # Green @ C2 vs Red @ C2
            green_box = find_color_in_corner(imgs['ground'], L_GREEN, U_GREEN, 'c2')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c2')
            H1H4 = check_overlap(green_box, red_box)

            # Brown @ C3 vs Red @ C3
            brown_box = find_color_in_corner(imgs['top'], L_BROWN, U_BROWN, 'c3')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c3')
            H3H6 = check_overlap(brown_box, red_box)

        # SET 1
        elif set_num == 1:
            # Green @ C2 vs Red @ C2
            green_box = find_color_in_corner(imgs['ground'], L_GREEN, U_GREEN, 'c2')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c2')
            H1H4 = check_overlap(green_box, red_box)

            # Brown @ C4 vs Red @ C4
            brown_box = find_color_in_corner(imgs['top'], L_BROWN, U_BROWN, 'c4')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c4')
            H3H6 = check_overlap(brown_box, red_box)

        # SET 2
        elif set_num == 2:
            # Blue @ C4 vs Red @ C4
            blue_box = find_color_in_corner(imgs['ground'], L_BLUE, U_BLUE, 'c4')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c4')
            M1M3 = check_overlap(blue_box, red_box)

            # Grey @ C1 vs Red @ C1
            grey_box = find_color_in_corner(imgs['top'], L_GREY, U_GREY, 'c1')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c1')
            M4M6 = check_overlap(grey_box, red_box)

        # SET 3
        elif set_num == 3:
            # Blue @ C4 vs Red @ C4
            blue_box = find_color_in_corner(imgs['ground'], L_BLUE, U_BLUE, 'c4')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c4')
            M1M3 = check_overlap(blue_box, red_box)

            # Grey @ C2 vs Red @ C2
            grey_box = find_color_in_corner(imgs['top'], L_GREY, U_GREY, 'c2')
            red_box = find_color_in_corner(imgs['mid'], L_RED1, U_RED1, 'c2')
            M4M6 = check_overlap(grey_box, red_box)

        print(f"Set {sid} (Set {set_num}): H1H4={H1H4}, H3H6={H3H6}, M1M3={M1M3}, M4M6={M4M6}")

        results.append({
            'Set_ID': sid,
            'H1H4': H1H4,
            'H3H6': H3H6,
            'M1M3': M1M3,
            'M4M6': M4M6
        })

    # --- EXPORT ---
    if not results:
        print("No complete sets found.")
        return

    df = pd.DataFrame(results)
    # Ensure standard columns (integers)
    cols = ['H1H4', 'H3H6', 'M1M3', 'M4M6']
    df[cols] = df[cols].fillna(0).astype(int)

    csv_name = "final_overlap_accuracy.csv"
    df.to_csv(csv_name, index=False)
    print(f"\nSaved to {csv_name}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    # UPDATE PATH HERE
    SEARCH_PATH = "/Users/amirthavarshini/Desktop/VR-studies/testing"
    run_logic_analysis(SEARCH_PATH)