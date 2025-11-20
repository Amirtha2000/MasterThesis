import cv2
import numpy as np
import os
import glob

# --- CONFIGURATION AND COLOR DEFINITIONS ---

# Red Cross (Wide range for robust detection of red/maroon)
L_RED1 = np.array([0, 50, 50], dtype=np.uint8);
U_RED1 = np.array([25, 255, 255], dtype=np.uint8)
L_RED2 = np.array([155, 50, 50], dtype=np.uint8);
U_RED2 = np.array([180, 255, 255], dtype=np.uint8)
# Green Patch
L_GREEN = np.array([35, 50, 50], dtype=np.uint8);
U_GREEN = np.array([85, 255, 255], dtype=np.uint8)
# Brown Patch
L_BROWN = np.array([5, 50, 50], dtype=np.uint8);
U_BROWN = np.array([30, 200, 200], dtype=np.uint8)
# Blue Patch
L_BLUE = np.array([90, 50, 50], dtype=np.uint8);
U_BLUE = np.array([130, 255, 255], dtype=np.uint8)
# 📌 FIXED: Grey Patch - Slightly increased min saturation to reduce noise capture
L_GREY = np.array([0, 0, 30], dtype=np.uint8)
U_GREY = np.array([180, 20, 240], dtype=np.uint8)

MIN_AREA = 300

# --- VISUAL COLOR PALETTE (BGR) ---
TARGET_COLOR = (255, 255, 0)  # Cyan/Light Blue for Red Cross Target
OVERLAY_COLOR = (255, 0, 255)  # Magenta/Pink for Patch Overlay
CONFIRMATION_COLOR = (0, 255, 255)  # Bright Yellow for overlap point
INTERSECTION_COLOR = (0, 165, 255)  # Orange for intersection box


# --- UTILITY FUNCTIONS ---

def get_corner_bbox(img_shape, corner_name):
    """Returns (x, y, w, h) for the specific quadrant."""
    h, w = img_shape[:2]
    cx, cy = w // 2, h // 2

    if corner_name == 'c1': return (cx, 0, w - cx, cy)
    if corner_name == 'c2': return (cx, cy, w - cx, h - cy)
    if corner_name == 'c3': return (0, cy, cx, h - cy)
    if corner_name == 'c4': return (0, 0, cx, cy)
    return (0, 0, w, h)


def find_color_in_corner(img, lower, upper, corner_name):
    """Finds bounding box of the largest color patch inside the specified corner quadrant."""
    if img is None: return None

    cx, cy, cw, ch = get_corner_bbox(img.shape, corner_name)
    roi = img[cy:cy + ch, cx:cx + cw]

    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_roi, lower, upper)

    if np.array_equal(lower, L_RED1): mask += cv2.inRange(hsv_roi, L_RED2, U_RED2)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest_bbox = None;
    max_area = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area and area > MIN_AREA:
            max_area = area
            # --- CRITICAL CHANGE: Use TIGHT bounding box around CONTOUR ---
            rx, ry, rw, rh = cv2.boundingRect(cnt)
            largest_bbox = (cx + rx, cy + ry, rw, rh)

    return largest_bbox


def check_overlap(bbox1, bbox2):
    """Checks if two bounding boxes overlap."""
    if bbox1 is None or bbox2 is None: return 0
    x1, y1, w1, h1 = bbox1;
    x2, y2, w2, h2 = bbox2

    overlap_w = min(x1 + w1, x2 + w2) - max(x1, x2)
    overlap_h = min(y1 + h1, y2 + h2) - max(y1, y2)

    return 1 if overlap_w > 0 and overlap_h > 0 else 0


def get_file_set_info(filename):
    """Parses filename to get set_id and plan_type, handling 'processed_' prefix."""
    base = filename.replace('processed_', '')
    for t in ['ground', 'mid', 'top']:
        if f'_{t}' in base:
            parts = base.split(f'_{t}')
            return parts[0], t
    return None, None


def calculate_overlap_center(bbox1, bbox2):
    """Calculates the center point of the overlap region."""
    if check_overlap(bbox1, bbox2) == 0: return None

    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    # Calculate the intersection coordinates
    intersect_x_start = max(x1, x2)
    intersect_y_start = max(y1, y2)
    intersect_x_end = min(x1 + w1, x2 + w2)
    intersect_y_end = min(y1 + h1, y2 + h2)

    # Calculate the center of the intersection rectangle
    center_x = (intersect_x_start + intersect_x_end) // 2
    center_y = (intersect_y_start + intersect_y_end) // 2

    # Also return the intersection bbox for drawing purposes
    intersection_bbox = (intersect_x_start, intersect_y_start,
                         intersect_x_end - intersect_x_start,
                         intersect_y_end - intersect_y_start)

    return center_x, center_y, intersection_bbox


def create_pure_overlap_visualization(base_img, overlay_bbox, target_bbox, corner_name, source_type, score_name,
                                      output_filename):
    """Generates a visualization showing only the BBoxes, the overlap point, and the intersection box."""
    img = base_img.copy()
    score_value = check_overlap(overlay_bbox, target_bbox)

    # Draw the Red Cross BBox (Target) - Cyan
    if target_bbox:
        x, y, w, h = target_bbox
        cv2.rectangle(img, (x, y), (x + w, y + h), TARGET_COLOR, 5)

        # Draw the Overlay Patch BBox (Green/Brown/Blue/Grey) - Magenta
    if overlay_bbox:
        x, y, w, h = overlay_bbox
        cv2.rectangle(img, (x, y), (x + w, y + h), OVERLAY_COLOR, 5)

        # Draw the Confirmation Point (Yellow) AND Intersection Box (Orange) if overlap occurs
    if score_value == 1:
        center_x, center_y, intersection_bbox = calculate_overlap_center(overlay_bbox, target_bbox)

        # Draw the intersection box in Orange
        ix, iy, iw, ih = intersection_bbox
        cv2.rectangle(img, (ix, iy), (ix + iw, iy + ih), INTERSECTION_COLOR, -1)  # Filled Orange Box

        # Draw the confirmation point in Yellow
        cv2.circle(img, (center_x, center_y), 15, CONFIRMATION_COLOR, -1)

        # Simple Annotation (Text placement outside the drawing area)
    annotation_text = f"SCORE {score_name}: {score_value} | Check: {corner_name}"
    cv2.putText(img, annotation_text, (20, img.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.5, CONFIRMATION_COLOR, 5)

    cv2.imwrite(output_filename, img)
    print(f"   -> Generated {output_filename} (Score: {score_value})")
    return img


# --- MAIN LOGIC ---

def visualize_and_confirm_set_logic(sid, paths, set_num):
    """Runs the two primary checks for a specific set ID and generates verification images."""

    mid_img = cv2.imread(paths['mid']);
    ground_img = cv2.imread(paths['ground']);
    top_img = cv2.imread(paths['top'])
    if mid_img is None or ground_img is None or top_img is None: return

    # --- DETERMINE LOGIC & COLORS ---
    if set_num in [0, 1]:
        ground_color_L, ground_color_U = L_GREEN, U_GREEN
        top_color_L, top_color_U = L_BROWN, U_BROWN
        score_name_1, score_name_2 = 'H1H4', 'H3H6'

        if set_num == 0:
            target_corner_1, target_corner_2 = 'c2', 'c3'
        else:
            target_corner_1, target_corner_2 = 'c2', 'c4'
        ground_source = "Green Patch (GND)";
        top_source = "Brown Patch (TOP)"

    elif set_num in [2, 3]:
        ground_color_L, ground_color_U = L_BLUE, U_BLUE
        top_color_L, top_color_U = L_GREY, U_GREY
        score_name_1, score_name_2 = 'M1M3', 'M4M6'

        if set_num == 2:
            target_corner_1, target_corner_2 = 'c4', 'c1'
        else:
            target_corner_1, target_corner_2 = 'c4', 'c2'

        ground_source = "Blue Patch (GND)";
        top_source = "Grey Patch (TOP)"
    else:
        return

    print(f"\n--- Processing Set: {sid} (ID {set_num}) ---")

    # --- CHECK 1: Ground Patch vs Mid Red Cross ---
    ground_box_1 = find_color_in_corner(ground_img, ground_color_L, ground_color_U, target_corner_1)
    red_box_1 = find_color_in_corner(mid_img, L_RED1, U_RED1, target_corner_1)

    create_pure_overlap_visualization(
        mid_img.copy(), ground_box_1, red_box_1, target_corner_1, ground_source, score_name_1,
        f"visualization_{sid}_check_{score_name_1}.png"
    )

    # --- CHECK 2: Top Patch vs Mid Red Cross ---
    top_box_2 = find_color_in_corner(top_img, top_color_L, top_color_U, target_corner_2)
    red_box_2 = find_color_in_corner(mid_img, L_RED1, U_RED1, target_corner_2)

    create_pure_overlap_visualization(
        mid_img.copy(), top_box_2, red_box_2, target_corner_2, top_source, score_name_2,
        f"visualization_{sid}_check_{score_name_2}.png"
    )


def run_batch_visualization(folder_path):
    files = sorted(glob.glob(os.path.join(folder_path, "*.*")))
    files = [f for f in files if f.lower().endswith(('.png', '.jpg'))]

    groups = {}
    for f in files:
        sid, ftype = get_file_set_info(os.path.basename(f))
        if sid:
            if sid not in groups: groups[sid] = {'ground': None, 'mid': None, 'top': None}
            groups[sid][ftype] = f

    print(f"Found {len(groups)} potential image sets.")

    for sid, paths in groups.items():
        if not (paths['ground'] and paths['mid'] and paths['top']):
            continue

        try:
            set_num = int(sid.split('_')[-1])
        except:
            continue

        visualize_and_confirm_set_logic(sid, paths, set_num)


if __name__ == "__main__":
    SEARCH_PATH = "/Users/amirthavarshini/Desktop/VR-studies/testing"
    run_batch_visualization(SEARCH_PATH)