#This notebook loads the donation and message CSV files, filters them for WhatsApp donations, normalizes the datetime fields and prepares messages and donations DataFrames for analysis of notebooks.

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, HTML
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.dates as mdates
from pathlib import Path
import seaborn as sns

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DONATION_CSV = r"C:/Users/Dev/Documents/GitHub/Developing-Interactive-Jupyter-Notebooks-for-analyzing-participant-meta-data-from-WhatsApp-Project-/12570525/donation_table.csv"
MESSAGES_CSV = r"C:/Users/Dev/Documents/GitHub/Developing-Interactive-Jupyter-Notebooks-for-analyzing-participant-meta-data-from-WhatsApp-Project-/12570525/messages_filtered_table.csv"

#Loading data
donations = pd.read_csv(DONATION_CSV)
donations = donations[donations["source"] == "WhatsApp"]

messages = pd.read_csv(MESSAGES_CSV)
messages = messages[messages["donation_id"].isin(donations["donation_id"])]

#normalizing datetime
messages["dt"] = pd.to_datetime(messages["datetime"], errors="coerce")
messages["date_only"] = messages["dt"].dt.date
messages["hour"] = messages["dt"].dt.hour