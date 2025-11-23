## Spatial Memory Analytics Pipeline

**MasterThesis** operationalizes a fully reproducible research environment for the thesis
**“Measuring Spatial Memory Using 3D-Sketch Maps in Vertically Aligned and Rotated Multilevel Environments Using Virtual Reality.”**

The platform consolidates every component required for empirical validation—VR navigation environments, the VResin 3D-sketch tool (developed by Tianyi Xiao), rendering engines, mesh-processing pipelines, and statistical modeling assets.
All experimental materials, raw data, VR executables, and participant documentation are available here:

📁 **Full Asset Archive (VR .exe, 3D Sketch Tool, Raw Data, Consent Forms)**
**[https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb](https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb)**

The mission: deliver a deterministic, auditable, and re-runnable pipeline from a participant’s original 3D sketch to the final quantitative accuracy metrics.

---

## Core Capabilities

* High-fidelity, batch-driven OBJ preprocessing
* Automated multi-floor segmentation from 3D meshes
* Standardized top-down rendering at controlled resolution
* Landmark extraction via color-based segmentation
* Corner-based scoring logic (H/M variables)
* Vertical overlap validation + QA visualization
* Angular-deviation scoring for horizontal accuracy
* Rotation-accuracy computation grounded in orientation deltas
* Reproducible outputs optimized for downstream GLMM analysis

---

## Repository Structure

The layout below reflects the live structure of the repository.

```markdown
Processing3Dsketch/
│
├── Processing3Dsketch/  
├── additive_effect.R                  # Additional GLMM model
├── hypothesis_testing.R               # Hypothesis-level modeling
├── primary_model.R                    # Primary GLMM workflow
├── rot_score.R                        # Rotation scoring in R
│
├── Processing3Dsketch/  
├── sample_1.obj                       # Example OBJ
├── sample_1_ground_plan.png           # Example rendered ground floor
├── sample_1_mid_plan.png              # Example rendered mid level
├── sample_1_top_plan.png              # Example rendered top level
│
├── score.xlsx                         # scoring sheet
│
├── Processing3Dsketch/                               # Operational Python pipeline
│   ├── batch_strip_and_remove_materials.py
│   ├── split_obj_into_3floors_batch.py
│   ├── quantitive_score.py
│   ├── overlap_analysis.py
│   ├── angle_dev.py
│   ├── rotation_acc.py
│   └── scorer.py (optional)
│
└── README.md
```

### External Resources

All VR environments, navigation executables, 3D-sketching tools, raw OBJ exports, and consent documentation are stored externally:

📁 **[https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb](https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb)**

---

## Installation

```bash
pip install numpy opencv-python pandas scikit-learn matplotlib pillow
# Optional:
# pip install trimesh scipy
```

---

## Pipeline Execution

All scripts expect source files inside `src/` and directory paths aligned with the `SEARCH_PATH` and `INPUT_DIR` variables defined inside each module.

```bash
# 1. OBJ Preprocessing
python src/batch_strip_and_remove_materials.py batch \
    --input-dir ./data_raw \
    --output-dir ./data_clean \
    --remove LayerSurface --compact

# 2. Floor Extraction + Standardized Projection
python src/split_obj_into_3floors_batch.py \
    --input ./data_clean \
    --output ./png --png --align

# 3. Landmark Detection (H/M Scoring)
python src/quantitive_score.py

# 4. Vertical Overlap Analysis + Accuracy
python src/overlap_analysis.py

# 5. Angular-Deviation Scoring
python src/angle_dev.py

# 6. Rotation Accuracy
python src/rotation_acc.py

# 7. Final Score Aggregation
# (manual or via src/scorer.py if activated)
```

---

## Data & Asset Availability

All raw data, VR executables, VResin sketching tools, environment files, sample meshes, and participant materials are hosted in Sciebo:

📁 **[https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb](https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb)**

This includes:

* **3D Sketching Tool (.exe)**
* **All VR Navigation Environments (.exe)**
* **Raw OBJ Exports from Participants**
* **Original PNG Renderings**
* **Consent Forms, Instructions & Participant Materials**
* **Complete Dataset for Reanalysis**

---

## Citation

If this workflow supports your research, please cite the repository:

`https://github.com/Amirtha2000/MasterThesis/tree/main/Processing3Dsketch`

---

## Contact

**Amirtha Varshini Raja Sonathreesan Latha**
University of Münster
GitHub: [https://github.com/Amirtha2000](https://github.com/Amirtha2000)

All VR assets, experimental executables, the drawing tool, raw data, and participant materials:
📁 **[https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb](https://uni-muenster.sciebo.de/s/kFX9LATRaREeqjb)**
