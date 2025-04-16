# INSURANCE CLAIMS DATA ANALYSIS
## Overview
This project provides an in-depth analysis of insurance claims data, covering aspects such as customer demographics, product performance, and broker efficiency. The project culminates in an interactive web-based dashboard for visualizing key findings.

## Project Structure
The repository is organized into three main sections:

1.  **`/Dataset/`**: Contains all data-related files.
    * `/Raw Data/`: The original, unprocessed data files used in the project.
    * `/Cleaned Data/`: Includes the final cleaned dataset (`Cleaned_Insurance_Claims_Data.xlsx`) used for analysis and the dashboard.
    * `/Data Cleaning/`: Image showing the data cleaning steps.

2.  **`/Data Analysis Code/`**: Contains Jupyter Notebooks file for the detailed analysis. This section is divided into 7 parts, each focusing on a different analytical perspective.

3.  **`/Dashboard/`**: Includes both Python script and Jupyter Notebooks file and Python script to host the interactive Dash locally.

## Dataset

The primary dataset utilized for the final analysis and dashboard visualization is `Cleaned_Insurance_Claims_Data.xlsx`, located within the `/Dataset/Cleaned Data/` directory. Details regarding the raw data sources and the cleaning methodology can be found in the `/Dataset/` subdirectories.

## Setup
- Since each part was written by different people, please change the data link before running the file.
- To run the analysis code and the dashboard locally, ensure you have Python installed along with the necessary libraries. You can install the required packages using pip:
```bash
pip install pandas numpy matplotlib seaborn plotly dash dash-bootstrap-components openpyxl
