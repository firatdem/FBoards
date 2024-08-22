import pandas as pd
import json

# Define the input and output file paths
input_excel_file = 'jsonFeederExcel.xlsx'
output_json_file = 'state.json'

# Load the Excel file
df = pd.read_excel(input_excel_file, usecols=['Name', 'Role', 'Skills', 'SST Card', 'NJ License'])

# Initialize data structures for employees
employees = []

# Process each row in the DataFrame
for index, row in df.iterrows():
    # Extract and handle skills, SST Card, and NJ License
    skills = row['Skills'].split(', ') if pd.notna(row['Skills']) else []
    sst_card = row['SST Card'] if pd.notna(row['SST Card']) else 'No'
    nj_license = row['NJ License'] if pd.notna(row['NJ License']) else 'No'

    # Add employees to the list
    employees.append({
        'name': row['Name'],
        'role': row['Role'],
        'phone': '',  # You can set default values or update them later
        'skills': skills,
        'sst_card': sst_card,
        'nj_license': nj_license,
        'electrician_ranking': '1',  # You can set default values or update them later
        'job_site': None,  # Unassigned by default
        'box': None,  # Unassigned by default
        'x': None,  # Unassigned by default
        'y': None  # Unassigned by default
    })

# Combine job sites and employees into a single state dictionary
state = {
    'job_sites': [],  # No job sites processed
    'employees': employees,
    'scale': 1.0,  # You can set default values or update them later
    'canvas_transform': (0, 0),  # You can set default values or update them later
    'scroll_x': 0,  # You can set default values or update them later
    'scroll_y': 0  # You can set default values or update them later
}

# Save the state dictionary to a JSON file
with open(output_json_file, 'w') as f:
    json.dump(state, f, indent=4)

print(f"Data has been exported to {output_json_file}")
