import cv2
import numpy as np
import os
import glob
import math
import pandas as pd

# --- CONFIGURATION ---
# Increased tolerance to handle hand-drawn variations
TOLERANCE = 25.0


def get_file_info(filename):
    base = filename.replace('processed_', '')
    for t in ['ground', 'mid', 'top']:
        if f'_{t}' in base:
            parts = base.split(f'_{t}')
            return parts[0], t
    return None, None


def estimate_rotation(template_path, target_path):
    img1 = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)  # Template (Ground)
    img2 = cv2.imread(target_path, cv2.IMREAD_GRAYSCALE)  # Target (Mid/Top)

    if img1 is None or img2 is None: return 0.0

    h, w = img1.shape
    img2 = cv2.resize(img2, (w, h))

    # ORB Feature Detector
    orb = cv2.ORB_create(nfeatures=5000)
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10: return 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    try:
        matches = bf.match(des1, des2)
        if len(matches) < 10: return 0.0

        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        matrix, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts)
        if matrix is None: return 0.0

        angle_rad = math.atan2(matrix[1, 0], matrix[0, 0])
        angle_deg = math.degrees(angle_rad)

        if angle_deg < 0: angle_deg += 360

        return angle_deg
    except Exception:
        return 0.0


def check_angle_match_debug(angle, target, tolerance):
    def normalize_diff(a, b):
        diff = abs(a - b)
        return min(diff, 360 - diff)

    if target == 90:
        diff_90 = normalize_diff(angle, 90)
        diff_270 = normalize_diff(angle, 270)

        min_diff = min(diff_90, diff_270)
        passed = 1 if min_diff <= tolerance else 0
        return passed, min_diff
    else:
        diff = normalize_diff(angle, target)
        passed = 1 if diff <= tolerance else 0
        return passed, diff


def run_rotation_audit(folder_path):
    files = sorted(glob.glob(os.path.join(folder_path, "*.*")))
    files = [f for f in files if f.lower().endswith(('.png', '.jpg'))]

    groups = {}
    for f in files:
        sid, ftype = get_file_info(os.path.basename(f))
        if sid:
            if sid not in groups: groups[sid] = {'ground': None, 'mid': None, 'top': None}
            groups[sid][ftype] = f

    print(f"Found {len(groups)} sets. analyzing with tolerance +/- {TOLERANCE} degrees...")
    results = []

    for sid, paths in groups.items():
        if not (paths['ground'] and paths['mid'] and paths['top']):
            continue

        # 1. Mid vs Ground (Target: 90 or 270)
        angle_mid = estimate_rotation(paths['ground'], paths['mid'])
        score_mid, dev_mid = check_angle_match_debug(angle_mid, 90, TOLERANCE)

        # 2. Top vs Ground (Target: 180)
        angle_top = estimate_rotation(paths['ground'], paths['top'])
        score_top, dev_top = check_angle_match_debug(angle_top, 180, TOLERANCE)

        print(f"Set {sid}:")
        print(f"  Mid Angle: {angle_mid:.1f}° (Dev: {dev_mid:.1f}°) -> Score: {score_mid}")
        print(f"  Top Angle: {angle_top:.1f}° (Dev: {dev_top:.1f}°) -> Score: {score_top}")

        results.append({
            'Set_ID': sid,
            'Mid_Angle_Est': round(angle_mid, 1),
            'Mid_Deviation': round(dev_mid, 1),
            'Score_Mid_90_270': score_mid,
            'Top_Angle_Est': round(angle_top, 1),
            'Top_Deviation': round(dev_top, 1),
            'Score_Top_180': score_top
        })

    if results:
        df = pd.DataFrame(results)
        csv_name = "rotation_audit_debug.csv"
        df.to_csv(csv_name, index=False)
        print(f"\nSaved detailed report to {csv_name}")


if __name__ == "__main__":
    SEARCH_PATH = "/Users/amirthavarshini/Desktop/VR-studies/testing/split_levels"
    run_rotation_audit(SEARCH_PATH)