# Let's count the unique values for certain fields from the given JSON structure

import json

# Load the JSON file we processed earlier (we will assume the structure is similar to the snippet provided)
json_file_path = 'output_test.json'

with open(json_file_path, 'r', encoding='utf-8') as jsonfile:
    data = json.load(jsonfile)

# Let's extract the unique values from specific fields like "role", "current_status", "job_site", etc.
text = set()
roles = set()
job_sites = set()
current_statuses = set()


for employee in data['employees']:
    text.add(employee.get('text', ''))
    roles.add(employee.get('role', ''))
    job_sites.add(employee.get('job_site', ''))
    current_statuses.add(employee.get('current_status', ''))

# Print unique counts to console
print("Unique Names:", len(text))
print("Unique Roles:", len(roles))
print("Unique Job Sites:", len(job_sites))
print("Unique Current Statuses:", len(current_statuses))