import pandas as pd
import json

# Load the Excel file
excel_file = 'json_template.xlsx'

# Load Employees data from the first sheet
df_employees = pd.read_excel(excel_file, sheet_name='Employees')

# Load Job Sites data from the second sheet
df_job_sites = pd.read_excel(excel_file, sheet_name='Job Sites')

# Initialize the JSON structure
data = {
    "employees": [],
    "job_sites": [],
    "scale": 0.25,
    "canvas_transform": [-143.0, -44.0],
    "scroll_x": 0.0,
    "scroll_y": 0.0
}

# Populate the employees section
for _, row in df_employees.iterrows():
    employee = {
        "text": row['text'],
        "role": row['role'],
        "phone": row['phone'],
        "skills": row['skills'].split(',') if pd.notna(row['skills']) else [],
        "sst_card": row['sst_card'],
        "nj_ny_certified": row['nj_ny_certified'],
        "electrician_rank": row['electrician_rank'],
        "certifications": row['certifications'].split(',') if pd.notna(row['certifications']) else [],
        "worker_status": row['worker_status'],
        "job_site": row['job_site'],
        "box": row['box'],
        "x": row['x'],
        "y": row['y']
    }
    data["employees"].append(employee)

# Populate the job_sites section
for _, row in df_job_sites.iterrows():
    job_site = {
        "name": row['name'],
        "x": row['x'],
        "y": row['y'],
        "status": {
            "PM": row['PM'],
            "GM": row['GM'],
            "Foreman": row['Foreman'],
            "Electrician": row['Electrician'].split(',') if isinstance(row['Electrician'], str) else [],
            "ElectricianBoxCoords": list(map(float, row['ElectricianBoxCoords'].split(','))) if isinstance(row['ElectricianBoxCoords'], str) else [],
            "PMCoords": list(map(float, row['PMCoords'].split(','))) if isinstance(row['PMCoords'], str) else [],
            "GMCoords": list(map(float, row['GMCoords'].split(','))) if isinstance(row['GMCoords'], str) else [],
            "ForemanCoords": list(map(float, row['ForemanCoords'].split(','))) if isinstance(row['ForemanCoords'], str) else [],
            "Collapsed": row['Collapsed']
        }
    }
    data["job_sites"].append(job_site)

# Convert the dictionary to a JSON object
json_data = json.dumps(data, indent=4)

# Save the JSON to a file
with open('output.json', 'w') as json_file:
    json_file.write(json_data)

print("JSON file created successfully.")
