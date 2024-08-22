# NOT BEING USED

import tkinter as tk
from tkinter import ttk
import json
from constants import ROLE_COLORS

class EmployeeProfile:
    def __init__(self, parent, prefill_data=None, save_callback=None, json_file='employees.json'):
        self.parent = parent
        self.prefill_data = prefill_data
        self.save_callback = save_callback
        self.json_file = json_file

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Employee Profile")
        self.dialog.geometry("400x600")  # Adjust size as needed

        self.create_widgets()
        self.load_employee_profile()  # Load data into the widgets if prefill_data is provided

        self.dialog.grab_set()
        parent.wait_window(self.dialog)

    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_entry(main_frame, "Name", "name")
        self.create_dropdown(main_frame, "Role", "role", ["PM", "GM", "Foreman", "Electrician", "Fire Alarm Electrician", "Roughing Electrician"], self.update_skill_dropdown)
        self.create_dropdown(main_frame, "Skills", "skills", ["Helper", "Junior Mechanic", "Mechanic", "Sub Foreman"])
        self.create_dropdown(main_frame, "Electrician Rank", "electrician_rank", ["0", "1", "2", "3", "4", "5"])
        self.create_listbox(main_frame, "Certifications", "certifications", ["Placeholder1", "Placeholder2", "Placeholder3", "Placeholder4", "Placeholder5"])
        self.create_dropdown(main_frame, "SST Card", "sst_card", ["Yes", "No"])
        self.create_dropdown(main_frame, "Worker Status", "worker_status", ["Journeyman", "Contractor"])
        self.create_dropdown(main_frame, "NJ / NY Certified", "nj_ny_certified", ["NJ", "NY", "Both"])
        self.create_entry(main_frame, "Phone Number", "phone")

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def create_entry(self, parent, label, field):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=label).pack(side=tk.LEFT)
        entry = tk.Entry(frame)
        entry.pack(fill=tk.X, expand=True)
        setattr(self, f"{field}_entry", entry)
        if self.prefill_data and field in self.prefill_data:
            entry.insert(0, self.prefill_data[field])

    def create_dropdown(self, parent, label, field, options, command=None):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=label).pack(side=tk.LEFT)
        var = tk.StringVar()
        setattr(self, f"{field}_var", var)
        dropdown = ttk.OptionMenu(frame, var, options[0], *options, command=command)
        dropdown.pack(fill=tk.X, expand=True)
        setattr(self, f"{field}_dropdown", dropdown)  # Save the dropdown widget as an attribute
        if self.prefill_data and field in self.prefill_data:
            var.set(self.prefill_data[field])

    def create_listbox(self, parent, label, field, options):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=label).pack(side=tk.LEFT)
        listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=5)
        for option in options:
            listbox.insert(tk.END, option)
        listbox.pack(fill=tk.X, expand=True)
        setattr(self, f"{field}_listbox", listbox)
        if self.prefill_data and field in self.prefill_data:
            for item in self.prefill_data[field]:
                index = options.index(item)
                listbox.select_set(index)

    def update_skill_dropdown(self, selected_role):
        skills_by_role = {
            "Electrician": ["Helper", "Junior Mechanic", "Mechanic", "Sub Foreman"],
            "Fire Alarm Electrician": ["Fire Alarm Helper", "Fire Alarm Junior Mechanic", "Fire Alarm Mechanic", "Fire Alarm Sub Foreman"],
            "Roughing Electrician": ["Roughing Helper", "Roughing Junior Mechanic", "Roughing Mechanic", "Roughing Sub Foreman"],
        }
        default_skills = ["Helper", "Junior Mechanic", "Mechanic", "Sub Foreman"]

        menu = self.skills_dropdown["menu"]
        menu.delete(0, "end")

        skills = skills_by_role.get(selected_role, default_skills)
        for skill in skills:
            menu.add_command(label=skill, command=lambda value=skill: self.skills_var.set(value))

        self.skills_var.set(skills[0] if skills else "")

    def add(self):
        self.save_data()
        self.dialog.destroy()

    def save(self):
        self.save_data()
        self.dialog.destroy()

    def save_data(self):
        data = {
            "name": self.name_entry.get(),
            "role": self.role_var.get(),
            "skills": self.skills_var.get(),
            "electrician_rank": self.electrician_rank_var.get(),
            "certifications": [self.certifications_listbox.get(i) for i in self.certifications_listbox.curselection()],
            "sst_card": self.sst_card_var.get(),
            "nj_ny_certified": self.nj_ny_certified_var.get(),
            "worker_status": self.worker_status_var.get(),
            "phone": self.phone_entry.get()
        }
        if self.save_callback:
            self.save_callback(data)

    def load_employee_profile(self):
        if not self.prefill_data:
            return

        for field in ["name", "role", "skills", "electrician_rank", "sst_card", "nj_ny_certified", "worker_status", "phone"]:
            entry = getattr(self, f"{field}_entry", None)
            if entry and field in self.prefill_data:
                entry.delete(0, tk.END)
                entry.insert(0, self.prefill_data[field])

        for field in ["certifications"]:
            listbox = getattr(self, f"{field}_listbox", None)
            if listbox and field in self.prefill_data:
                listbox.selection_clear(0, tk.END)
                for item in self.prefill_data[field]:
                    index = listbox.get(0, tk.END).index(item)
                    listbox.selection_set(index)
