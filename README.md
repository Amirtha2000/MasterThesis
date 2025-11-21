MasterThesis is the complete, reproducible research environment for my Master’s thesis “Measuring Spatial Memory Using 3D-Sketch Maps in Vertically Aligned and Rotated Multilevel Environments Using Virtual Reality.”

This repository consolidates everything used in the experiment — the Unity executable environments, VResin custom drawing tool (developed by Tianyi Xiao), compiled executables, Python pipelines for mesh cleaning and 2D projection, and R scripts for statistical modeling (GLMMs, emmeans).

The goal is to make every step — from a participant’s virtual 3D sketch to the final quantitative accuracy score — fully traceable, version-controlled, and rerunnable. Each component (VR tool, .obj-to-.png converter, and scoring scripts) follows open-science principles for methodological transparency and reproducibility.

3D Sketch Reconstruction & Spatial Recall Pipeline 

Key Features

* Deterministic, fully scripted processing pipeline
* Automated 3-level extraction from 3D OBJ meshes
* Top-down projection with unified image dimensions
* Red-stroke landmark detection using color filtering
* Corner-based attribution logic for scoring (H/M variables)
* Vertical overlap validation across floors
* Angular deviation scoring for horizontal accuracy
* Floor rotation accuracy via orientation comparison
* Reproducible, audit-ready visual confirmation outputs



Processing3Dsketch/ │ ├── data_raw/ # Original OBJ exports from VResin ├── data_clean/ # Sanitized OBJ files ├── levels/ # Separated per-floor OBJs ├── png/ # Rasterized top-down images ├── annotations/ # Corner frames, anchors, centroids (Outputs of scoring scripts) ├── scoring/ # Final accuracy results (CSV outputs) │ ├── src/ │ ├── batch_strip_and_remove_materials.py # 1. Preprocessing (OBJ Cleaning) │ ├── split_obj_into_3floors_batch.py # 2. Level Extraction & Projection │ ├── quantitive_score.py # 3. Landmark Detection (H/M Scores) │ ├── overlap_analysis.py # 4. Vertical Overlap Validation (Scoring) │ ├── overlap-img-analysis.py # 4. Vertical Overlap Visualization (QA) │ ├── angle_dev.py # 5. Angular-Deviation Scoring │ ├── rotation_acc.py # 6. Floor Rotation Accuracy │ └── (Optional) scorer.py # Final aggregation script │ └── README.md







Installation

```bash
pip install numpy opencv-python pandas scikit-learn matplotlib pillow
# You may need to also install trimesh and scipy depending on your environment
# pip install trimesh scipy
````

## Running the Pipeline

 Note: Ensure all source files (`.py`) are placed in the `src/` directory and image files are structured in the paths expected by the scripts (e.g., `SEARCH_PATH` variables).

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

Citation

If you use this pipeline or the underlying methodology, please cite the repository:

`https://github.com/Amirtha2000/MasterThesis/tree/main/Processing3Dsketch`

 Contact

For questions regarding methodology or implementation:

 Amirtha Varshini Raja Sonathreesan Latha 
University of Münster
GitHub: `https://github.com/Amirtha2000`

```
```
