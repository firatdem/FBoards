import tkinter as tk
from tkinter import ttk
import json
from draggable_box import DraggableBox
from job_site_hub import JobSiteHub
from constants import ROLE_COLORS, DEFAULT_EMPLOYEE_X, DEFAULT_EMPLOYEE_Y, GRID_SIZE, JOB_HUB_WIDTH, JOB_HUB_HEIGHT, VERTICAL_SPACING, MAX_COLUMNS

class WhiteboardApp:
    def __init__(self, root):
        self.is_loading = True  # Add this line
        self.root = root
        self.root.title("Fboards")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12), background='#ADD8E6')
        style.configure('TLabel', font=('Helvetica', 12), background='#F0F0F0')
        style.configure('TFrame', background='white')
        style.configure('TMenubutton', font=('Helvetica', 12), background='#ADD8E6')  # Apply the style to OptionMenu

        self.root.state('zoomed')

        self.main_frame = ttk.Frame(root, padding="10 10 10 10", relief='solid', borderwidth=1)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas_frame = ttk.Frame(self.main_frame, padding="10 10 10 10", relief='solid', borderwidth=1)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.side_frame = ttk.Frame(self.main_frame, width=200, padding="10 10 10 10", relief='solid', borderwidth=1)
        self.side_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(self.canvas_frame, scrollregion=(0, 0, 2000, 2000), background='#D3D3D3')
        self.canvas.hub_list = []
        self.scrollbar_y = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.employee_boxes = []

        self.unassigned_listbox = tk.Listbox(self.side_frame)
        self.unassigned_listbox.pack(fill=tk.BOTH, expand=True)
        self.unassigned_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        # Search box
        tk.Label(self.side_frame, text="Search by Name:").pack()
        self.search_entry = tk.Entry(self.side_frame)
        self.search_entry.pack(fill=tk.X, padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", self.update_employee_listbox)

        # SST Card filter
        tk.Label(self.side_frame, text="Filter by SST Card:").pack()
        self.sst_card_var = tk.StringVar(value="All")
        self.sst_card_filter = ttk.OptionMenu(self.side_frame, self.sst_card_var, "All", "All", "Yes", "No")
        self.sst_card_filter.pack(fill=tk.X, padx=5, pady=5)
        self.sst_card_var.trace("w", lambda name, index, mode: self.update_employee_listbox())

        # NJ License filter
        tk.Label(self.side_frame, text="Filter by NJ License:").pack()
        self.nj_license_var = tk.StringVar(value="All")
        self.nj_license_filter = ttk.OptionMenu(self.side_frame, self.nj_license_var, "All", "All", "Yes", "No")
        self.nj_license_filter.pack(fill=tk.X, padx=5, pady=5)
        self.nj_license_var.trace("w", lambda name, index, mode: self.update_employee_listbox())

        # Skills filter
        tk.Label(self.side_frame, text="Filter by Skills:").pack()
        self.skills_filter_var = tk.StringVar()
        skills = ["All", "Cable Puller", "Rough-In", "Talks Big Game", "Is Gay", "Fart"]
        self.skills_filter = ttk.OptionMenu(self.side_frame, self.skills_filter_var, "All", *skills)
        self.skills_filter.pack(fill=tk.X, padx=5, pady=5)
        self.skills_filter_var.trace("w", lambda name, index, mode: self.update_employee_listbox())

        # Show all employees checkbox
        self.show_all_var = tk.BooleanVar()
        self.show_all_checkbox = tk.Checkbutton(self.side_frame, text="Show All Employees", variable=self.show_all_var, command=self.update_employee_listbox)
        self.show_all_checkbox.pack(fill=tk.X, padx=5, pady=5)

        self.reset_filters_button = ttk.Button(self.side_frame, text="Reset Filters", command=self.reset_filters)
        self.reset_filters_button.pack(fill=tk.X, padx=5, pady=5)


        self.delete_employee_button = ttk.Button(self.side_frame, text="Delete Employee", command=self.delete_employee)
        self.delete_employee_button.pack(fill=tk.X, padx=5, pady=5)

        self.copy_employee_button = ttk.Button(self.side_frame, text="Copy Employee", command=self.copy_employee)
        self.copy_employee_button.pack(fill=tk.X, padx=5, pady=5)

        self.last_deleted_employee = None

        self.scale = 1.0  # Initial scale
        self.canvas_transform = (0, 0)  # Initial canvas transformation (x, y)
        self.scroll_x = 0  # Initial scroll position x
        self.scroll_y = 0  # Initial scroll position y
        self.saved_scroll_region = None  # To store the scroll region

        self.root.bind('<Configure>', self.on_resize)
        self.root.bind('<FocusIn>', self.on_focus_in)
        self.root.bind('<FocusOut>', self.on_focus_out)  # Bind focus out event

        self.canvas.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)

        # Define default position coordinates
        self.default_x = DEFAULT_EMPLOYEE_X
        self.default_y = DEFAULT_EMPLOYEE_Y

        self.create_controls()
        self.load_state()

    def update_text_positions(self, hub, x1, y1, x2, y2):
        self.canvas.coords(hub.text_id, (x1 + x2) / 2, y1 - 10)
        self.canvas.coords(hub.erase_button_id, x2 - 15, y1 + 15)
        self.canvas.coords(hub.collapse_button_id, x1 + 15, y2 - 15)

    def update_employee_listbox(self, event=None):
        self.unassigned_listbox.delete(0, tk.END)
        search_text = self.search_entry.get().lower()
        skills_filter = self.skills_filter_var.get()
        sst_card_filter = self.sst_card_var.get()
        nj_license_filter = self.nj_license_var.get()
        show_all = self.show_all_var.get()

        for box in self.employee_boxes:
            print(f"Checking box: {box.text}, SST Card: {box.sst_card}, NJ License: {box.nj_license}")  # Debug output
            if show_all or not box.current_snap_box:
                # Filtering logic
                if (search_text in box.text.lower() and
                        (skills_filter == "All" or skills_filter in box.skills) and
                        (sst_card_filter == "All" or sst_card_filter == box.sst_card) and
                        (nj_license_filter == "All" or nj_license_filter == box.nj_license)):
                    self.unassigned_listbox.insert(tk.END, box.text)

    def reset_filters(self):
        self.search_entry.delete(0, tk.END)
        self.skills_filter_var.set("All")
        self.sst_card_var.set("All")
        self.nj_license_var.set("All")
        self.show_all_var.set(False)
        self.update_employee_listbox()

    def on_start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.canvas.tag_raise(self.id)

    def on_drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.canvas.move(self.id, dx, dy)
        self.canvas.move(self.circle_id, dx, dy)
        self.start_x = event.x
        self.start_y = event.y

    def on_drop(self, event):
        x, y = self.canvas.coords(self.id)
        print(f"Dropped at: ({x}, {y})")
        self.redraw_canvas()

    def redraw_canvas(self):
        print("Canvas is being redrawn")
        self.canvas.update_idletasks()

        max_columns = MAX_COLUMNS
        for i, hub in enumerate(self.canvas.hub_list):
            x = 50 + (JOB_HUB_WIDTH + 40) * (i % max_columns) * self.scale
            y = 50 + (JOB_HUB_HEIGHT + VERTICAL_SPACING) * (i // max_columns) * self.scale
            self.canvas.coords(hub.id, x, y, x + JOB_HUB_WIDTH * self.scale, y + JOB_HUB_HEIGHT * self.scale)
            hub.update_positions(self.scale)
            self.update_text_positions(hub, x, y, x + JOB_HUB_WIDTH * self.scale, y + JOB_HUB_HEIGHT * self.scale)

        for box in self.employee_boxes:
            if box.current_snap_box:
                box.snap_to_box()  # Ensure boxes snap to their correct locations
        self.bring_employee_names_to_front()
        self.update_scroll_region()
        self.apply_scale()


    def apply_scale(self):
        for box in self.employee_boxes:
            current_font_size = box.font[1]
            new_font_size = int(current_font_size * self.scale)
            new_font_size = max(8, new_font_size)
            box.font = (box.font[0], new_font_size, box.font[2])
            self.canvas.itemconfig(box.id, font=box.font)

            circle_radius = box.circle_radius * self.scale
            x1, y1, x2, y2 = self.canvas.coords(box.circle_id)
            new_x2 = x1 + circle_radius
            new_y2 = y1 + circle_radius
            self.canvas.coords(box.circle_id, x1, y1, new_x2, new_y2)

        for hub in self.canvas.hub_list:
            hub.update_positions(self.scale)

    def on_focus_in(self, event):
        # Debug print statements
        print(f"Focus in event: scroll_x={self.scroll_x}, scroll_y={self.scroll_y}, scale={self.scale}")
        print(f"Scroll region before focus in: {self.canvas.cget('scrollregion')}")

        # Apply the current scale to all elements
        self.apply_scale()

        # Debug print statements
        print(f"Scroll region after focus in: {self.canvas.cget('scrollregion')}")

    def on_focus_out(self, event):
        # Save the current scroll positions
        self.scroll_x = self.canvas.xview()[0]
        self.scroll_y = self.canvas.yview()[0]
        self.saved_scroll_region = self.canvas.cget('scrollregion')

        # Debug print statements
        print(f"Focus out event: scroll_x={self.scroll_x}, scroll_y={self.scroll_y}, scrollregion={self.saved_scroll_region}")

    def on_zoom(self, event):
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= scale_factor

        # Get the current mouse position
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Scale all objects on the canvas
        self.canvas.scale("all", x, y, scale_factor, scale_factor)

        # Save the current canvas transformation
        self.canvas_transform = self.canvas.canvasx(0), self.canvas.canvasy(0)
        self.scroll_x = self.canvas.xview()[0]
        self.scroll_y = self.canvas.yview()[0]

        # Apply the current scale to all elements
        self.apply_scale()

        # Update the scroll region to accommodate the new scale
        self.update_scroll_region()

        # Debug print statements
        print(f"Zoom event: scale={self.scale}, scroll_x={self.scroll_x}, scroll_y={self.scroll_y}")
        print(f"Scroll region after zoom: {self.canvas.cget('scrollregion')}")

    def create_controls(self):
        control_frame = ttk.Frame(self.root, padding="10 10 10 10", relief='solid', borderwidth=1)
        control_frame.pack()

        add_employee_button = ttk.Button(control_frame, text="Add Employee", command=self.open_add_employee_dialog)
        add_employee_button.pack(side=tk.LEFT, padx=5, pady=5)

        add_hub_button = ttk.Button(control_frame, text="Add Job Site", command=self.add_job_site_hub)
        add_hub_button.pack(side=tk.LEFT, padx=5, pady=5)

        undo_button = ttk.Button(control_frame, text="Undo", command=self.undo_delete_employee)
        undo_button.pack(side=tk.LEFT, padx=5, pady=5)

    def on_listbox_select(self, event):
        selected_indices = self.unassigned_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            employee_name = self.unassigned_listbox.get(selected_index)
            self.scroll_to_employee(employee_name)

    def scroll_to_employee(self, employee_name):
        # Ensure the scrollregion is set
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Access the scrollregion correctly
        scrollregion = self.canvas.cget("scrollregion").split()
        if len(scrollregion) == 4:
            scrollregion_bottom = int(scrollregion[3])
        else:
            scrollregion_bottom = 1  # Default to avoid division by zero

        # Perform the scrolling
        for box in self.employee_boxes:
            if box.text == employee_name and not box.current_snap_box:
                self.canvas.yview_moveto(box.canvas.coords(box.id)[1] / scrollregion_bottom)
                break

    def update_unassigned_employees(self):
        self.unassigned_listbox.delete(0, tk.END)
        for box in self.employee_boxes:
            if not box.current_snap_box:
                self.unassigned_listbox.insert(tk.END, box.text)
        self.unassigned_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

    def open_add_employee_dialog(self, prefill_data=None):
        self.add_employee_popup = tk.Toplevel(self.canvas)
        self.add_employee_popup.title("Employee Profile")
        self.add_employee_popup.geometry("400x600")  # Adjust size as needed

        # Main frame
        main_frame = ttk.Frame(self.add_employee_popup, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)
        tk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(name_frame)
        self.name_entry.pack(fill=tk.X, expand=True)
        if prefill_data:
            self.name_entry.insert(0, prefill_data["name"])

        # Role
        role_frame = ttk.Frame(main_frame)
        role_frame.pack(fill=tk.X, pady=5)
        tk.Label(role_frame, text="Role:").pack(side=tk.LEFT)
        self.role_var = tk.StringVar()
        self.role_var.set("PM")
        roles = ["PM", "GM", "Foreman", "Electrician", "Fire Alarm Electrician", "Roughing Electrician"]
        self.role_dropdown = tk.OptionMenu(role_frame, self.role_var, *roles, command=self.update_skill_dropdown)
        self.role_dropdown.pack(fill=tk.X, expand=True)
        if prefill_data:
            self.role_var.set(prefill_data["role"])

        # Skill
        skill_frame = ttk.Frame(main_frame)
        skill_frame.pack(fill=tk.X, pady=5)
        tk.Label(skill_frame, text="Skill:").pack(side=tk.LEFT)
        # Initialize skills_var as StringVar
        self.skills_var = tk.StringVar()
        # Initialize skills_dropdown as OptionMenu
        self.skills_dropdown = tk.OptionMenu(skill_frame, self.skills_var, "")
        self.skills_dropdown.pack(fill=tk.X, expand=True)
        # Update skill options based on selected role
        self.update_skill_dropdown(self.role_var.get())

        # Prefill data if available
        if prefill_data:
            self.skills_var.set(prefill_data.get("skills", [""])[0])  # Handle list to single value

        # Electrician Rank
        electrician_rank_frame = ttk.Frame(main_frame)
        electrician_rank_frame.pack(fill=tk.X, pady=5)
        tk.Label(electrician_rank_frame, text="Electrician Rank:").pack(side=tk.LEFT)
        self.electrician_rank_var = tk.StringVar()
        self.electrician_rank_var.set("0")
        self.electrician_rank_dropdown = tk.OptionMenu(electrician_rank_frame, self.electrician_rank_var, "0", "1", "2", "3", "4",
                                                       "5")
        self.electrician_rank_dropdown.pack(fill=tk.X, expand=True)
        if prefill_data:
            self.electrician_rank_var.set(prefill_data.get("electrician_rank", "0"))

        # Certifications
        cert_frame = ttk.Frame(main_frame)
        cert_frame.pack(fill=tk.X, pady=5)
        tk.Label(cert_frame, text="Certifications:").pack(side=tk.LEFT)
        self.certifications_listbox = tk.Listbox(cert_frame, selectmode=tk.MULTIPLE, height=5)
        certifications = ["Placeholder1", "Placeholder2", "Placeholder3", "Placeholder4", "Placeholder5"]
        for cert in certifications:
            self.certifications_listbox.insert(tk.END, cert)
        self.certifications_listbox.pack(fill=tk.X, expand=True)
        if prefill_data:
            for cert in prefill_data.get("certifications", []):
                idx = certifications.index(cert)
                self.certifications_listbox.select_set(idx)

        # SST Card
        sst_frame = ttk.Frame(main_frame)
        sst_frame.pack(fill=tk.X, pady=5)
        tk.Label(sst_frame, text="SST Card:").pack(side=tk.LEFT)
        self.sst_card_var = tk.StringVar()
        self.sst_card_var.set("No")
        self.sst_card_dropdown = tk.OptionMenu(sst_frame, self.sst_card_var, "Yes", "No")
        self.sst_card_dropdown.pack(fill=tk.X, expand=True)
        if prefill_data:
            self.sst_card_var.set(prefill_data.get("sst_card", "No"))

        # Worker Status
        worker_status_frame = ttk.Frame(main_frame)
        worker_status_frame.pack(fill=tk.X, pady=5)
        tk.Label(worker_status_frame, text="Worker Status:").pack(side=tk.LEFT)
        self.worker_status_var = tk.StringVar()
        self.worker_status_var.set("Journeyman")
        self.worker_status_dropdown = tk.OptionMenu(worker_status_frame, self.worker_status_var, "Journeyman","Contractor")
        self.worker_status_dropdown.pack(fill=tk.X, expand=True)
        if prefill_data:
            self.worker_status_var.set(prefill_data.get("worker_status", "Journeyman"))

        # NJ / NY Certified
        njny_frame = ttk.Frame(main_frame)
        njny_frame.pack(fill=tk.X, pady=5)
        tk.Label(njny_frame, text="NJ / NY Certified:").pack(side=tk.LEFT)
        self.nj_ny_certified_var = tk.StringVar()
        self.nj_ny_certified_var.set("NJ")
        self.nj_ny_certified_dropdown = tk.OptionMenu(njny_frame, self.nj_ny_certified_var, "NJ", "NY", "Both")
        self.nj_ny_certified_dropdown.pack(fill=tk.X, expand=True)
        if prefill_data:
            self.nj_ny_certified_var.set(prefill_data.get("nj_ny_certified", "NJ"))

        # Phone Number
        phone_frame = ttk.Frame(main_frame)
        phone_frame.pack(fill=tk.X, pady=5)
        tk.Label(phone_frame, text="Phone Number:").pack(side=tk.LEFT)
        self.phone_entry = tk.Entry(phone_frame)
        self.phone_entry.pack(fill=tk.X, expand=True)
        if prefill_data:
            self.phone_entry.insert(0, prefill_data.get("phone", ""))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        if prefill_data:
            ttk.Button(button_frame, text="Save",
                       command=lambda: self.save_edited_employee(prefill_data["index"])).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(button_frame, text="Add", command=self.add_employee_from_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.add_employee_popup.destroy).pack(side=tk.RIGHT, padx=5)

        self.add_employee_popup.grab_set()
        self.root.wait_window(self.add_employee_popup)

    def validate_entry_length(self, P, limit):
        try:
            return len(P) <= int(limit)
        except ValueError:
            return False

    def update_skill_dropdown(self, selected_role):
        skills_by_role = {
            "Electrician": ["Helper", "Junior Mechanic", "Mechanic", "Sub Foreman"],
            "Fire Alarm Electrician": ["Fire Alarm Helper", "Fire Alarm Junior Mechanic", "Fire Alarm Mechanic",
                                       "Fire Alarm Sub Foreman"],
            "Roughing Electrician": ["Roughing Helper", "Roughing Junior Mechanic", "Roughing Mechanic",
                                     "Roughing Sub Foreman"],
        }
        default_skills = ["Helper", "Junior Mechanic", "Mechanic", "Sub Foreman"]

        menu = self.skills_dropdown["menu"]
        menu.delete(0, "end")

        skills = skills_by_role.get(selected_role, default_skills)
        for skill in skills:
            menu.add_command(label=skill, command=lambda value=skill: self.skills_var.set(value))

        self.skills_var.set(skills[0] if skills else "")

    def format_phone_number(self, event):
        value = self.phone_entry.get()
        digits = ''.join(filter(str.isdigit, value))

        if len(digits) > 6:
            formatted = f"{digits[:3]}-{digits[3:6]}-{digits[6:10]}"
        elif len(digits) > 3:
            formatted = f"{digits[:3]}-{digits[3:6]}"
        else:
            formatted = digits

        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, formatted)

    def add_employee_from_dialog(self):
        name = self.name_entry.get()
        role = self.role_var.get()
        skills = self.skills_var.get()
        phone = self.phone_entry.get()
        certifications = [self.certifications_listbox.get(i) for i in self.certifications_listbox.curselection()]
        sst_card = self.sst_card_var.get()
        nj_ny_certified = self.nj_ny_certified_var.get()
        worker_status = self.worker_status_var.get()
        electrician_rank = self.electrician_rank_var.get()

        if name and role:
            self.add_employee(name=name, role=role,  skills=[skills], electrician_rank=electrician_rank, certifications=certifications,
                              sst_card=sst_card,  worker_status=worker_status, nj_ny_certified=nj_ny_certified,
                               phone=phone)
        self.add_employee_popup.destroy()

    def save_edited_employee(self, index):
        name = self.name_entry.get()
        role = self.role_var.get()
        skill = self.skills_var.get()
        phone = self.phone_entry.get()
        certifications = [self.certifications_listbox.get(i) for i in self.certifications_listbox.curselection()]
        sst_card = self.sst_card_var.get()
        nj_ny_certified = self.nj_ny_certified_var.get()
        worker_status = self.worker_status_var.get()
        electrician_rank = self.electrician_rank_var.get()

        if name and role:
            box = self.employee_boxes[index]
            box.text = name
            box.role = role
            box.phone = phone
            box.skills = [skill]
            box.certifications = certifications
            box.sst_card = sst_card
            box.nj_ny_certified = nj_ny_certified
            box.worker_status = worker_status
            box.electrician_rank = electrician_rank
            box.color = ROLE_COLORS.get(role, "black")

            if role in ("Electrician", "Fire Alarm Electrician", "Roughing Electrician"):
                self.canvas.itemconfig(box.id, text=box.get_display_text())
            elif role in ("PM", "GM", "Foreman"):
                self.canvas.itemconfig(box.id, text=box.get_display_text_supers())

            self.canvas.itemconfig(box.circle_id, fill=box.color, outline=box.color)
            self.update_unassigned_employees()
            self.save_state()
        self.add_employee_popup.destroy()

    def add_employee(self, name=None, role=None, phone=None, x=None, y=None, job_site=None, box=None, skills=None,
                     sst_card="No", nj_ny_certified="NJ", electrician_rank="1", certifications=None,
                     worker_status="Journeyman"):
        if name and role:
            # Use default position if x or y is not provided
            if x is None:
                x = self.default_x
            if y is None:
                y = self.default_y + len(self.employee_boxes) * 30
            # Create a new DraggableBox with the provided attributes
            draggable_box = DraggableBox(
                self, self.canvas, name, role, x, y, phone, job_site, box, skills, sst_card,
                nj_ny_certified, electrician_rank, certifications, worker_status
            )
            # Update the display text based on role
            if role in ("Electrician", "Fire Alarm Electrician", "Roughing Electrician"):
                self.canvas.itemconfig(draggable_box.id, text=draggable_box.get_display_text())
            else:
                self.canvas.itemconfig(draggable_box.id, text=draggable_box.get_display_text_supers())

            self.employee_boxes.append(draggable_box)
            self.update_scroll_region()
            self.update_employee_position(name, job_site, box, draggable_box.id)
            self.update_unassigned_employees()
            self.save_state()

    def delete_employee(self):
        selected_indices = self.unassigned_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            employee_name = self.unassigned_listbox.get(selected_index)
            for box in self.employee_boxes:
                if box.text == employee_name and not box.current_snap_box:
                    # Save coordinates before deleting the box
                    box_coords = self.canvas.coords(box.id)
                    self.canvas.delete(box.id)
                    self.canvas.delete(box.circle_id)
                    self.employee_boxes.remove(box)
                    self.update_unassigned_employees()
                    self.save_state()
                    self.last_deleted_employee = {
                        "name": box.text, "role": box.role, "phone": box.phone,
                        "x": box_coords[0],
                        "y": box_coords[1]
                    }
                    break

    def undo_delete_employee(self):
        if self.last_deleted_employee:
            self.add_employee(name=self.last_deleted_employee["name"], role=self.last_deleted_employee["role"],
                              phone=self.last_deleted_employee["phone"],
                              x=self.last_deleted_employee["x"], y=self.last_deleted_employee["y"])
            self.last_deleted_employee = None

    def copy_employee(self):
        selected_indices = self.unassigned_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            employee_name = self.unassigned_listbox.get(selected_index)
            for box in self.employee_boxes:
                if box.text == employee_name and not box.current_snap_box:
                    self.add_employee(name=f"{box.text}", role=box.role, phone=box.phone,
                                      x=self.canvas.coords(box.id)[0], y=self.canvas.coords(box.id)[1] + GRID_SIZE)
                    break

    def set_default_coordinates(self, x, y):
        return (0, 0) if x is None or y is None else (x, y)

    def add_job_site_hub(self, job_site=None, x=None, y=None, status=None):
        if job_site is None:
            existing_numbers = [int(hub.text.split()[-1]) for hub in self.canvas.hub_list if
                                hub.text.startswith("Job Site")]
            job_number = 1
            while job_number in existing_numbers:
                job_number += 1
            job_site = f"Job Site {job_number}"

        x, y = self.set_default_coordinates(x, y)

        hub = JobSiteHub(self, self.canvas, job_site, x, y)
        if status:
            hub.set_occupation_status(status)
        self.canvas.hub_list.append(hub)
        self.canvas.tag_raise(hub.text_id)
        self.bring_employee_names_to_front()
        self.update_scroll_region()
        self.save_state()
        self.redraw_canvas()  # Redraw the canvas

    def bring_employee_names_to_front(self):
        for box in self.employee_boxes:
            self.canvas.tag_raise(box.id)
            self.canvas.tag_raise(box.circle_id)
            # Adjust circle size for draggable boxes
            circle_radius = box.circle_radius * self.scale
            x1, y1, x2, y2 = self.canvas.coords(box.circle_id)
            new_x2 = x1 + circle_radius
            new_y2 = y1 + circle_radius
            self.canvas.coords(box.circle_id, x1, y1, new_x2, new_y2)

    def update_scroll_region(self, event=None):
        current_scroll_x = self.canvas.xview()
        current_scroll_y = self.canvas.yview()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.xview_moveto(current_scroll_x[0])
        self.canvas.yview_moveto(current_scroll_y[0])

        # Debug print statements
        print(f"Update scroll region: scrollregion={self.canvas.cget('scrollregion')}")

    def on_resize(self, event):
        # Save the current scroll region
        self.saved_scroll_region = self.canvas.cget('scrollregion')

        self.redraw_canvas()
        self.apply_scale()  # Apply the current scale whenever the window is resized

        # Debug print statements
        print(f"Resize event: canvas width={self.canvas.winfo_width()}, canvas height={self.canvas.winfo_height()}")
        print(f"Scroll region after resize: {self.canvas.cget('scrollregion')}")

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_shift_mouse_wheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def find_circle(self, employee_id):
        for box in self.employee_boxes:
            if box.id == employee_id:
                return box.circle_id
        return None

    def reposition_unassigned_employees(self):
        for index, box in enumerate(self.employee_boxes):
            if not box.current_snap_box:
                x = DEFAULT_EMPLOYEE_X
                y = DEFAULT_EMPLOYEE_Y + (index * GRID_SIZE)
                x = (x // GRID_SIZE) * GRID_SIZE
                y = (y // GRID_SIZE) * GRID_SIZE
                self.canvas.coords(box.id, x, y)
                self.canvas.coords(box.circle_id, x - 15, y, x - 5, y + 10)

    def restore_boxes(self):
        for hub in self.canvas.hub_list:
            hub.pm_occupied = False
            hub.gm_occupied = False
            hub.foreman_occupied = False
            hub.electrician_occupied = []
            for box in self.employee_boxes:
                if box.current_snap_box and box.current_snap_box["hub"] == hub:
                    box.current_snap_box = None
        self.update_unassigned_employees()

    def save_state(self):
        if self.is_loading:
            return  # Skip saving if the app is loading

        try:
            state = {
                "employees": [
                    {
                        "text": box.text,
                        "role": box.role,
                        "phone": box.phone,
                        "skills": box.skills,
                        "sst_card": box.sst_card,
                        "nj_ny_certified": box.nj_ny_certified,
                        "electrician_rank": box.electrician_rank,
                        "certifications": box.certifications,
                        "worker_status": box.worker_status,
                        "job_site": box.current_snap_box["hub"].text if box.current_snap_box else None,
                        "box": box.current_snap_box["box"] if box.current_snap_box else None,
                        "x": self.canvas.coords(box.id)[0],
                        "y": self.canvas.coords(box.id)[1]
                    } for box in self.employee_boxes
                ],
                "job_sites": [
                    {
                        "name": hub.text,
                        "x": self.canvas.coords(hub.id)[0],
                        "y": self.canvas.coords(hub.id)[1],
                        "status": hub.get_occupation_status()
                    } for hub in self.canvas.hub_list
                ],
                "scale": self.scale,
                "canvas_transform": self.canvas_transform,
                "scroll_x": self.scroll_x,
                "scroll_y": self.scroll_y
            }
            with open('state.json', 'w') as f:
                json.dump(state, f, indent=4)
            print(f"State saved: {state}")
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self):
        self.is_loading = True  # Start loading
        try:
            with open('state.json', 'r') as f:
                state = json.load(f)
            print("State loaded from JSON:")
            print(json.dumps(state, indent=4))

            job_site_dict = {}

            # First, add all job sites
            for job in state["job_sites"]:
                print(f"Loading job site: {job['name']}")
                job["status"].setdefault("Electrician", [])
                hub = self.add_job_site_hub(
                    job_site=job["name"],
                    x=job["x"],
                    y=job["y"],
                    status=job.get("status", {
                        "PM": False,
                        "GM": False,
                        "Foreman": False,
                        "Electrician": []
                    })
                )
                job_site_dict[job["name"]] = hub

            # Then, add all employees
            for emp in state["employees"]:
                print(f"Loading employee: {emp['text']}")
                job_site_name = emp.get("job_site")
                box_type = emp.get("box")
                x = emp.get("x", self.default_x)
                y = emp.get("y", self.default_y)

                # Retrieve the job site hub from the dictionary if it exists
                job_site_hub = job_site_dict.get(job_site_name)

                # Create DraggableBox with correct parameters
                draggable_box = DraggableBox(
                    app=self,
                    canvas=self.canvas,
                    text=emp["text"],
                    role=emp.get("role", "PM"),  # Default role if missing
                    x=x,
                    y=y,
                    phone=emp.get("phone", ""),
                    job_site=job_site_name,
                    box=box_type,
                    skills=emp.get("skills", []),
                    sst_card=emp.get("sst_card", "No"),
                    nj_ny_certified=emp.get("nj_ny_certified", "NJ"),
                    electrician_rank=emp.get("electrician_rank", "0"),
                    certifications=emp.get("certifications", []),
                    worker_status=emp.get("worker_status", "Journeyman")
                )
                self.employee_boxes.append(draggable_box)

                if job_site_hub and box_type:
                    print(f"Assigning {emp['text']} to {job_site_name} as {box_type}")
                    job_site_hub.update_occupation(box_type, True, draggable_box.id)
                    draggable_box.snap_to_box()

                print(f"Added employee: {emp['text']} at ({x}, {y})")

            # Load the scale and canvas transformation
            self.scale = state.get("scale", 1.0)
            self.canvas_transform = state.get("canvas_transform", (0, 0))
            self.scroll_x = state.get("scroll_x", 0)
            self.scroll_y = state.get("scroll_y", 0)

            # Apply the current scale to all elements
            self.apply_scale()
            self.update_unassigned_employees()  # Ensure the listbox is updated
        except Exception as e:
            print(f"Error loading state: {e}")
        finally:
            self.is_loading = False  # End loading

    def update_employee_position(self, name, job_site, box, employee_id):
        if job_site and box:
            for hub in self.canvas.hub_list:
                if hub.text == job_site:
                    hub.update_occupation(box, True, employee_id)
        self.save_state()


if __name__ == "__main__":
    root = tk.Tk()
    app = WhiteboardApp(root)
    root.mainloop()
