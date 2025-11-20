import cv2
import numpy as np
import pandas as pd
import os
import glob
import math

# --- CONFIGURATION ---
ANGLE_TOLERANCE = 20.0
MIN_AREA = 200

# --- COLORS ---
L_RED1 = np.array([0, 50, 50], dtype=np.uint8);
U_RED1 = np.array([25, 255, 255], dtype=np.uint8)
L_RED2 = np.array([155, 50, 50], dtype=np.uint8);
U_RED2 = np.array([180, 255, 255], dtype=np.uint8)
L_GREEN = np.array([35, 50, 50], dtype=np.uint8);
U_GREEN = np.array([85, 255, 255], dtype=np.uint8)
L_BROWN = np.array([5, 50, 50], dtype=np.uint8);
U_BROWN = np.array([30, 200, 200], dtype=np.uint8)
L_BLUE = np.array([90, 50, 50], dtype=np.uint8);
U_BLUE = np.array([130, 255, 255], dtype=np.uint8)
L_GREY = np.array([0, 0, 0], dtype=np.uint8);
U_GREY = np.array([180, 40, 255], dtype=np.uint8)


def get_corner_point(img_shape, corner_name):
    h, w = img_shape[:2]
    if corner_name == 'c1': return (w, 0)  # Top Right
    if corner_name == 'c2': return (w, h)  # Bottom Right
    if corner_name == 'c3': return (0, h)  # Bottom Left
    if corner_name == 'c4': return (0, 0)  # Top Left
    return (0, 0)


def get_corner_bbox(img_shape, corner_name):
    h, w = img_shape[:2]
    cx, cy = w // 2, h // 2
    if corner_name == 'c1': return (cx, 0, w - cx, cy)
    if corner_name == 'c2': return (cx, cy, w - cx, h - cy)
    if corner_name == 'c3': return (0, cy, cx, h - cy)
    if corner_name == 'c4': return (0, 0, cx, cy)
    return (0, 0, w, h)


def get_centroid_in_corner(img, lower, upper, corner_name):
    if img is None: return None

    cx, cy, cw, ch = get_corner_bbox(img.shape, corner_name)
    roi = img[cy:cy + ch, cx:cx + cw]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    if np.array_equal(lower, L_RED1): mask += cv2.inRange(hsv, L_RED2, U_RED2)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours: return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_AREA: return None

    M = cv2.moments(largest)
    if M["m00"] != 0:
        # Convert roi coords to global coords
        lx = int(M["m10"] / M["m00"])
        ly = int(M["m01"] / M["m00"])
        return (cx + lx, cy + ly)
    return None


def calculate_angle(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(dy, dx))
    if angle < 0: angle += 180
    return angle


def check_parallel(p_patch, p_cross, p_ref1, p_ref2):
    if not p_patch or not p_cross: return 0, 0.0, 0.0, 0.0

    angle_obj = calculate_angle(p_patch, p_cross)
    angle_ref = calculate_angle(p_ref1, p_ref2)

    diff = abs(angle_obj - angle_ref)
    diff = min(diff, 180 - diff)

    return (1 if diff <= ANGLE_TOLERANCE else 0), diff, angle_obj, angle_ref


def draw_visual(img, p_patch, p_cross, p_ref1, p_ref2, score, diff, name):
    vis = img.copy()

    # Draw Reference Line (Yellow)
    cv2.line(vis, p_ref1, p_ref2, (0, 255, 255), 3)

    # Draw Object Line (Magenta)
    if p_patch and p_cross:
        cv2.line(vis, p_patch, p_cross, (255, 0, 255), 3)
        cv2.circle(vis, p_patch, 8, (0, 255, 0), -1)
        cv2.circle(vis, p_cross, 8, (0, 0, 255), -1)

    color = (0, 255, 0) if score == 1 else (0, 0, 255)
    text = f"Parallel: {score} (Dev: {diff:.1f} deg)"
    cv2.putText(vis, text, (20, vis.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imwrite(name, vis)
    print(f"Generated: {name}")


def get_file_info(filename):
    base = filename.replace('processed_', '')
    for t in ['ground', 'mid', 'top']:
        if f'_{t}' in base:
            parts = base.split(f'_{t}')
            return parts[0], t
    return None, None


def run_analysis(folder_path):
    files = sorted(glob.glob(os.path.join(folder_path, "*.*")))
    files = [f for f in files if f.lower().endswith(('.png', '.jpg'))]

    groups = {}
    for f in files:
        sid, ftype = get_file_info(os.path.basename(f))
        if sid and ftype != 'mid':  # Ignore mid images
            if sid not in groups: groups[sid] = {'ground': None, 'top': None}
            groups[sid][ftype] = cv2.imread(f)

    results = []
    for sid, imgs in groups.items():
        # We need at least ground OR top to do something, but optimally both for full row
        if not (imgs['ground'] is not None or imgs['top'] is not None):
            continue

        # We need image dimensions. Use whichever image is available.
        ref_img = imgs['ground'] if imgs['ground'] is not None else imgs['top']
        h, w = ref_img.shape[:2]
        c1 = (w, 0);
        c2 = (w, h);
        c3 = (0, h);
        c4 = (0, 0)

        try:
            set_num = int(sid.split('_')[-1])
        except:
            continue

        row = {'Set': sid, 'H12': 0, 'H56': 0, 'M12': 0, 'M56': 0}

        # --- LOGIC ---
        if set_num in [0, 1]:
            # H12: Ground Image -> Green(c2) vs Red(c1) || C1-C2
            if imgs['ground'] is not None:
                p_green = get_centroid_in_corner(imgs['ground'], L_GREEN, U_GREEN, 'c2')
                p_red = get_centroid_in_corner(imgs['ground'], L_RED1, U_RED1, 'c1')

                row['H12'], diff, _, _ = check_parallel(p_green, p_red, c1, c2)
                draw_visual(imgs['ground'], p_green, p_red, c1, c2, row['H12'], diff, f"parallel_{sid}_H12.png")

            # H56: Top Image -> Brown(c3/c4) vs Red(c3/c4) || C3-C4
            # Prompt says: Brown near C4 or C3, Cross near C3 or C4.
            # Let's assume Cross is at C3 and Brown at C4 for 0/1 based on visual logic, or try both?
            # Standard layout usually opposes them. Let's look for Brown in C3/C4 and Red in C3/C4.
            if imgs['top'] is not None:
                # Try finding brown in C4, Red in C3 (common pattern)
                p_brown = get_centroid_in_corner(imgs['top'], L_BROWN, U_BROWN, 'c4')
                p_red = get_centroid_in_corner(imgs['top'], L_RED1, U_RED1, 'c3')

                # Fallback: Brown in C3, Red in C4
                if p_brown is None:
                    p_brown = get_centroid_in_corner(imgs['top'], L_BROWN, U_BROWN, 'c3')
                if p_red is None:
                    p_red = get_centroid_in_corner(imgs['top'], L_RED1, U_RED1, 'c4')

                row['H56'], diff, _, _ = check_parallel(p_brown, p_red, c3, c4)
                draw_visual(imgs['top'], p_brown, p_red, c3, c4, row['H56'], diff, f"parallel_{sid}_H56.png")

        elif set_num in [2, 3]:
            # M12: Ground Image -> Blue(c4) vs Red(c3) || C3-C4
            if imgs['ground'] is not None:
                p_blue = get_centroid_in_corner(imgs['ground'], L_BLUE, U_BLUE, 'c4')
                p_red = get_centroid_in_corner(imgs['ground'], L_RED1, U_RED1, 'c3')

                row['M12'], diff, _, _ = check_parallel(p_blue, p_red, c3, c4)
                draw_visual(imgs['ground'], p_blue, p_red, c3, c4, row['M12'], diff, f"parallel_{sid}_M12.png")

            # M56: Top Image -> Grey(c1/c2) vs Red(c2/c1) || C1-C2
            if imgs['top'] is not None:
                p_grey = get_centroid_in_corner(imgs['top'], L_GREY, U_GREY, 'c1')
                p_red = get_centroid_in_corner(imgs['top'], L_RED1, U_RED1, 'c2')

                if p_grey is None: p_grey = get_centroid_in_corner(imgs['top'], L_GREY, U_GREY, 'c2')
                if p_red is None: p_red = get_centroid_in_corner(imgs['top'], L_RED1, U_RED1, 'c1')

                row['M56'], diff, _, _ = check_parallel(p_grey, p_red, c1, c2)
                draw_visual(imgs['top'], p_grey, p_red, c1, c2, row['M56'], diff, f"parallel_{sid}_M56.png")

        results.append(row)
        print(f"{sid}: {row}")

    if results:
        df = pd.DataFrame(results)
        cols = ['H12', 'H56', 'M12', 'M56']
        for c in cols:
            if c not in df.columns: df[c] = 0

        csv_path = "parallelism_ground_top.csv"
        df.to_csv(csv_path, index=False)
        print(f"\nSaved results to {csv_path}")
        print(df[['Set'] + cols].to_string(index=False))


if __name__ == "__main__":
    SEARCH_PATH = "/Users/amirthavarshini/Desktop/VR-studies/testing"
    run_analysis(SEARCH_PATH)