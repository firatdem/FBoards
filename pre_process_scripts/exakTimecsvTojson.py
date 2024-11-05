import csv
import json

# Path to the uploaded CSV file
csv_file_path = "C:\\Users\\Work\\Downloads\\EmployeeTimecardByWeek (2).csv"

# The day we want to extract data for
TARGET_DAY = "Wed"

# Paths for output files
json_output_file = 'employees_output.json'
txt_output_file = 'processed_rows.txt'

# Initialize the list to store employee data
employees = []
current_employee = None
job_site = ""
found_job_site = False

def save_employee(current_employee, job_site):
    """Save the employee's data and reset for the next employee."""
    if current_employee:
        employees.append({
            "text": current_employee,
            "job_site": job_site.strip(),
        })

# Open the text file for writing processed rows
with open(txt_output_file, 'w', encoding='utf-8') as txtfile:
    # Open and read the CSV file
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)

        current_employee = None
        job_site = ""
        employees = []
        found_job_site = False

        for row in reader:
            # Write each row to the text file for inspection
            txtfile.write(f"{row}\n")  # Write row as a list in string format to the text file

            # Skip empty or irrelevant rows
            if not any(row) or 'xrBookmark' in row or not any(row[:3]):
                continue

            # Skip the "For the period" row specifically
            if "For the period of" in row[0]:
                continue

            # Check if the row contains an employee name (detect names more flexibly)
            if len(row[0]) > 3 and ',' in row[0]:
                # Save the current employee's data if we have collected any
                if current_employee:
                    save_employee(current_employee, job_site)

                # Extract employee name and reset job site
                current_employee = row[0].strip('"')
                job_site = ""
                found_job_site = False  # Reset for each new employee

            # Look for the job site in the row starting with "Location Name"
            elif "Location Name" in row[0]:
                # Expect the job site to be in the next row
                continue

            elif not found_job_site and row[0]:
                # Capture the job site from the row below "Location Name" header
                job_site = row[0].strip()
                found_job_site = True

            # Check for time card entries for the TARGET_DAY
            elif TARGET_DAY in row[2] and found_job_site:
                # Assuming job site hours for the day are in column 5 (index 4)
                job_site_hours = row[4].strip()  # Adjust if necessary
                job_site = f"{job_site}, Hours on {TARGET_DAY}: {job_site_hours}"

        # Save the last employee's data after the loop
        if current_employee:
            save_employee(current_employee, job_site)

# Prepare the output as a JSON structure
output_data = {
    "employees": [
        {
            "text": emp["text"],
            "role": "",
            "phone": "NaN",
            "skills": [],
            "sst_card": "No",
            "nj_ny_certified": "NJ",
            "electrician_rank": 0,
            "certifications": [],
            "worker_status": "NaN",
            "current_status": "On-site",
            "job_site": emp["job_site"],
            "box": "",
            "x": 0.0,
            "y": 0.0
        }
        for emp in employees
    ]
}

# Save to JSON file
with open(json_output_file, 'w', encoding='utf-8') as jsonfile:
    json.dump(output_data, jsonfile, indent=4)

# Check total employees processed
total_employees = len(employees), json_output_file
print(total_employees)
