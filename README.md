MasterThesis is the complete, reproducible research environment for my Master’s thesis “Measuring Spatial Memory Using 3D-Sketch Maps in Vertically Aligned and Rotated Multilevel Environments Using Virtual Reality.”

This repository consolidates everything used in the experiment — the Unity executable environments, VResin custom drawing tool (developed by Tianyi Xiao), compiled executables, Python pipelines for mesh cleaning and 2D projection, and R scripts for statistical modeling (GLMMs, emmeans).

The goal is to make every step — from a participant’s virtual 3D sketch to the final quantitative accuracy score — fully traceable, version-controlled, and rerunnable. Each component (VR tool, .obj-to-.png converter, and scoring scripts) follows open-science principles for methodological transparency and reproducibility.
# 3D Sketch Reconstruction & Spatial Recall Pipeline

A reproducible analytics workflow for transforming participant-generated 3D sketch data into standardized 2D floor plans and accuracy metrics for a multi-phase spatial-memory experiment. The pipeline operationalizes the full data lifecycle from raw `.obj` files to final scoring outputs.

---

## Executive Summary

This repository processes 3D building sketches produced in the *VResin* drawing environment after participants explored aligned and rotated virtual buildings. It extracts floor levels, identifies landmark drawings, validates spatial alignment, computes rotation accuracy, and generates all metrics used in the study’s quantitative analyses.

---

## Key Features

* Deterministic, fully scripted processing pipeline
* Automated 3-level extraction from 3D OBJ meshes
* Top-down projection with unified image dimensions
* Red-stroke landmark detection using color filtering
* Corner-based attribution logic for scoring
* Vertical overlap validation across floors
* Angular deviation scoring for horizontal accuracy
* Floor rotation accuracy via orientation comparison
* Reproducible, audit-ready visual confirmation outputs

---

## Repository Structure

```
Processing3Dsketch/
│
├── data_raw/                  # Original OBJ exports from VResin
├── data_clean/                # Sanitized OBJ files
├── levels/                    # Separated per-floor OBJs
├── png/                       # Rasterized top-down images
├── annotations/               # Corner frames, anchors, centroids
├── scoring/                   # Final accuracy results
│
├── src/
│   ├── preprocess.py
│   ├── extract_levels.py
│   ├── project_to_png.py
│   ├── annotate.py
│   ├── detect_landmarks.py
│   ├── validate_overlap.py
│   ├── angle_alignment.py
│   ├── rotation_score.py
│   └── scorer.py
│
└── README.md
```

---

## Pipeline Overview

### 1. Preprocessing

* Validates OBJ integrity
* Removes non-participant artifacts
* Normalizes vertex and face structures

### 2. Level Extraction

* Detects the vertical axis automatically
* Clusters vertex heights into three level bands
* Assigns faces by majority-vertex membership
* Exports per-level OBJs
* Projects and rasterizes all levels into fixed-dimension PNGs

### 3. Annotation

* Fits a bounding box around each plan
* Labels four canonical corners
* Adds fixed anchor rooms
* Highlights participant-drawn polygons

### 4. Landmark Detection

* Filters red strokes
* Computes centroids
* Maps centroids to building corners
* Activates corner flags (c1–c4)
* Converts corner flags into H/M variables

### 5. Vertical Overlap Validation

* Tests mid-floor landmarks against anchor positions
* Computes intersection masks
* Outputs binary vertical accuracy scores
* Renders visual QA overlays

### 6. Angular-Deviation Scoring

* Computes bearings between anchor and participant polygons
* Calculates angular offsets
* Applies a ±20° tolerance
* Outputs binary horizontal accuracy metrics

### 7. Rotation Score

* Computes orientation offsets between drawn vs. ground-truth floor rotation
* Converts orientation deviation to binary rotation accuracy
* Cross-validated using 3D meshes

---

## Installation

```
pip install numpy opencv-python trimesh pillow scipy matplotlib
```

Or (optional) create a dedicated environment:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Pipeline

### Step-by-step

```bash
python src/preprocess.py
python src/extract_levels.py
python src/project_to_png.py
python src/annotate.py
python src/detect_landmarks.py
python src/validate_overlap.py
python src/angle_alignment.py
python src/rotation_score.py
python src/scorer.py
```

### Full pipeline (if you add a wrapper)

```bash
python run_all.py
```

---

## Outputs

* Per-floor PNGs
* Annotated plans with anchors and centroids
* Corner-attribution tables
* Vertical overlap scores
* Angular deviation scores
* Rotation accuracy metrics
* Final scoring CSV/JSON

---

## Reproducibility

* Fixed clustering seed
* Standardized raster dimensions
* Deterministic ordering of geometry
* Unified scoring logic across participants

---

## Citation

If you use this pipeline, please cite the repository:

```
https://github.com/Amirtha2000/MasterThesis/tree/main/Processing3Dsketch
```

---

## Contact

For questions regarding methodology or implementation:
**Amirtha Varshini Raja Sonathreesan Latha**
University of Münster
GitHub: [https://github.com/Amirtha2000](https://github.com/Amirtha2000)

