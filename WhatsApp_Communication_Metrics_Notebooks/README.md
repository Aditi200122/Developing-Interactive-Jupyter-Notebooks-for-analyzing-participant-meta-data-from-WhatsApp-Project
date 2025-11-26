# WhatsApp Communication Metrics Analysis

## Overview
This project investigates patterns of WhatsApp communication related to donation behavior using multiple quantitative metrics grounded in computational social science and human communication theory.  
Each metric reveals a different dimension of communication — inequality, reciprocity, temporal activity, and behavioral change.

All analyses are implemented as **interactive Jupyter notebooks** with visual dashboards and annotation tools (Save Figure + Add Note controls).

---

## 📘 Notebooks Overview

| Notebook | Title | Description |
|-----------|--------|-------------|
| `00_Data_Loading_and_Preprocessing.ipynb` | Data Preparation | Loads, filters, and normalizes WhatsApp message and donation data. Establishes a consistent data foundation for subsequent analyses. |
| `01_Gini_Index.ipynb` | Inequality in Communication | Uses the **Gini coefficient** to quantify how evenly the donor distributes communication effort among contacts. |
| `02_Burstiness.ipynb` | Temporal Irregularity | Computes **burstiness metrics (B₁, B₂)** to describe how clustered or sporadic message exchanges are over time. |
| `03_Interaction_Balance.ipynb` | Reciprocity in Dialogue | Evaluates **interaction balance (b₍ᵢⱼ₎)** — how equally donors and contacts contribute to conversations. |
| `04_Heatmap_Activity.ipynb` | Temporal Activity Patterns | Visualizes hourly and daily message activity using a black–yellow heatmap. |
| `05_Daily_Trends.ipynb` | Long-Term Activity Trends | Tracks the evolution of communication over time, including word counts and active contacts. |

---

## 🧠 Scientific Context

| Concept | Meaning | Example Insight |
|----------|----------|-----------------|
| **Gini Index** | Measures inequality of communication distribution. | A high Gini indicates few contacts dominate most conversations. |
| **Burstiness** | Captures irregular timing of communication events. | High burstiness shows clustered communication periods. |
| **Interaction Balance** | Quantifies reciprocity in conversations. | Negative bias → donor dominates; positive → contacts dominate. |
| **Heatmap Activity** | Visualizes when communication happens. | Evening or weekend peaks may reveal temporal habits. |
| **Daily Trends** | Tracks volume and engagement over time. | Reveals phases of increased or decreased activity. |

---

## 🧩 Data Requirements

The notebooks expect the following data files (update paths if needed):

```python

#put here your csv data file location its in dataloader.py file you can change there
DONATION_CSV = r"C:/Users/Dev/Documents/GitHub/Developing-Interactive-Jupyter-Notebooks-Project/12570525/donation_table.csv" 
MESSAGES_CSV = r"C:/Users/Dev/Documents/GitHub/Developing-Interactive-Jupyter-Notebooks-Project/12570525/messages_filtered_table.csv"
```

---

## 🚀 How to Use

1. Open any notebook (e.g., `01_Gini_Index.ipynb`) in **Jupyter Notebook** or **JupyterLab**.
2. Run all cells sequentially.
3. Use the interactive widgets to select donors and visualize metrics.
4. Use **Save Figure** and **Add Note** buttons to store your interpretations.

---

## 📊 Interpretation Tips

- **Gini Index:** Near 0 → balanced communication; near 1 → inequality.
- **Burstiness:** Negative → regular, 0 → random, positive → bursty.
- **Interaction Balance:** 0 → balanced, negative → donor dominant, positive → contact dominant.
- **Heatmap:** Identifies daily/weekly rhythms.
- **Daily Trends:** Highlights longitudinal changes in communication.

---

## 🧑‍💻 Author Notes

Developed as part of a study on **explainable affective communication behavior**.  
All metrics follow definitions adapted from contemporary computational communication research.
