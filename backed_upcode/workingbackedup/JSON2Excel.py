import json
import pandas as pd

# Load the JSON data
with open('state.json', 'r') as f:
    data = json.load(f)

# Prepare the data for the Excel file
job_sites = data['job_sites']
employees = data['employees']

# Create a dictionary to hold the job site data
job_data = {job_site['name']: {'PM': [], 'GM': [], 'Foreman': [], 'Electrician': []} for job_site in job_sites}

# Fill the dictionary with employees
for emp in employees:
    job_site = emp['job_site']
    role = emp['role']
    if job_site and role in job_data[job_site]:
        job_data[job_site][role].append(emp['name'])

# Create a list of dictionaries to be converted to a DataFrame
rows = []
for job_site, roles in job_data.items():
    row = {'Job Site': job_site}
    for role, employees in roles.items():
        row[role] = ', '.join(employees) if employees else ''
    rows.append(row)

# Create the DataFrame
df = pd.DataFrame(rows)

# Write the DataFrame to an Excel file
output_file = 'job_site_employees.xlsx'
df.to_excel(output_file, index=False)

print(f"Data has been exported to {output_file}")
