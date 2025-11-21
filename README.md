MasterThesis is the complete, reproducible research environment for my Master’s thesis “Measuring Spatial Memory Using 3D-Sketch Maps in Vertically Aligned and Rotated Multilevel Environments Using Virtual Reality.”

This repository consolidates everything used in the experiment — the Unity executable environments, VResin custom drawing tool (developed by Tianyi Xiao), compiled executables, Python pipelines for mesh cleaning and 2D projection, and R scripts for statistical modeling (GLMMs, emmeans).

The goal is to make every step — from a participant’s virtual 3D sketch to the final quantitative accuracy score — fully traceable, version-controlled, and rerunnable. Each component (VR tool, .obj-to-.png converter, and scoring scripts) follows open-science principles for methodological transparency and reproducibility.
```markdown
# 3D Sketch Reconstruction & Spatial Recall Pipeline 

## Executive Summary

This repository processes 3D building sketches produced in the VResin drawing environment after participants explored aligned and rotated virtual buildings. It extracts floor levels, identifies landmark drawings, validates spatial alignment, computes rotation accuracy, and generates all metrics used in the study’s quantitative analyses.

## Key Features

* Deterministic, fully scripted processing pipeline
* Automated 3-level extraction from 3D OBJ meshes
* Top-down projection with unified image dimensions
* Red-stroke landmark detection using color filtering
* Corner-based attribution logic for scoring (H/M variables)
* Vertical overlap validation across floors
* Angular deviation scoring for horizontal accuracy
* Floor rotation accuracy via orientation comparison
* Reproducible, audit-ready visual confirmation outputs

---

## Repository Structure

```

Processing3Dsketch/
│
├── data\_raw/                  \# Original OBJ exports from VResin
├── data\_clean/                \# Sanitized OBJ files
├── levels/                    \# Separated per-floor OBJs
├── png/                       \# Rasterized top-down images
├── annotations/               \# Corner frames, anchors, centroids (Outputs of scoring scripts)
├── scoring/                   \# Final accuracy results (CSV outputs)
│
├── src/
│   ├── batch\_strip\_and\_remove\_materials.py \# 1. Preprocessing (OBJ Cleaning)
│   ├── split\_obj\_into\_3floors\_batch.py     \# 2. Level Extraction & Projection
│   ├── quantitive\_score.py                 \# 3. Landmark Detection (H/M Scores)
│   ├── overlap\_analysis.py                 \# 4. Vertical Overlap Validation (Scoring)
│   ├── overlap-img-analysis.py             \# 4. Vertical Overlap Visualization (QA)
│   ├── angle\_dev.py                        \# 5. Angular-Deviation Scoring
│   ├── rotation\_acc.py                     \# 6. Floor Rotation Accuracy
│   
│
└── README.md

````

---

## Pipeline Overview

### 1. Preprocessing
Validates OBJ integrity, removes non-participant artifacts, and normalizes vertex/face structures.
* **Script:** `batch_strip_and_remove_materials.py`

### 2. Level Extraction & Projection
Detects the vertical axis, clusters vertices into three levels, assigns faces, and exports per-level OBJs. These are then rasterized into fixed-dimension top-down PNGs.
* **Script:** `split_obj_into_3floors_batch.py`

### 3. Landmark Detection (Scribble Scoring)
Filters red/brown scribbles (check marks), computes their centroids, maps the centroids to the nearest canonical building corner (`c1`–`c4`), and calculates the binary **H** and **M** scores (e.g., `H2`, `M5`) based on pre-defined set logic.
* **Script:** `quantitive_score.py`

### 4. Vertical Overlap Validation
Tests if ground/top floor color patches (Green, Brown, Blue, Grey) correctly **overlap** with the corresponding Red Cross on the mid-floor plan. Outputs binary vertical accuracy scores (e.g., `H1H4`, `M4M6`).
* **Scripts:** `overlap_analysis.py`, `overlap-img-analysis.py` (for visual QA).

### 5. Angular-Deviation Scoring
Calculates the bearing (angle) of the line between a drawn patch and a red cross, then compares it to the reference corner-to-corner line (e.g., C1-C2). Outputs binary horizontal accuracy metrics (e.g., `H12`, `M56`) if the deviation is within the $\pm 20^\circ$ tolerance.
* **Script:** `angle_dev.py`

### 6. Floor Rotation Accuracy
Uses feature matching (ORB) to estimate the absolute rotation angle between the ground, mid, and top floor plans. Compares the estimated angle (e.g., Ground vs Mid $\approx 90^\circ$ or $270^\circ$, Ground vs Top $\approx 180^\circ$) against a tolerance (e.g., $\pm 25.0^\circ$) to determine binary rotation accuracy.
* **Script:** `rotation_acc.py`

---

## Installation

```bash
pip install numpy opencv-python pandas scikit-learn matplotlib pillow
# You may need to also install trimesh and scipy depending on your environment
# pip install trimesh scipy
````

## Running the Pipeline

**Note:** Ensure all source files (`.py`) are placed in the `src/` directory and image files are structured in the paths expected by the scripts (e.g., `SEARCH_PATH` variables).

```bash
# Example Step-by-step Execution
# 1. Clean OBJs (Output to 'data_clean' folder)
python src/batch_strip_and_remove_materials.py batch --input-dir ./data_raw --output-dir ./data_clean --remove LayerSurface --compact

# 2. Split OBJs and render PNG plans (Output to 'png' folder)
# Default size in split_obj_into_3floors_batch.py is 2960x1640
python src/split_obj_into_3floors_batch.py --input ./data_clean --output ./png --png --align

# 3. Scribble Scoring (Generates scribble_analysis_all.csv)
# Set SEARCH_PATH in script to the 'png' folder
python src/quantitive_score.py

# 4. Vertical Overlap Validation (Generates final_overlap_accuracy.csv and visualizations)
# Set SEARCH_PATH in script to the 'png' folder
python src/overlap_analysis.py

# 5. Angular-Deviation Scoring (Generates parallelism_ground_top.csv and visualizations)
# Set SEARCH_PATH in script to the 'png' folder
python src/angle_dev.py

# 6. Floor Rotation Accuracy (Generates rotation_audit_debug.csv)
# Set SEARCH_PATH in script to the 'png' folder
python src/rotation_acc.py

# 7. Final Scoring (Aggregation step not provided, assumed to be done manually or via a final script)
```

-----

## Citation

If you use this pipeline or the underlying methodology, please cite the repository:

`https://github.com/Amirtha2000/MasterThesis/tree/main/Processing3Dsketch`

## Contact

For questions regarding methodology or implementation:

**Amirtha Varshini Raja Sonathreesan Latha**
University of Münster
GitHub: `https://github.com/Amirtha2000`

```
```
