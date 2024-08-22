import tkinter as tk
from tkinter import ttk
import json
from draggable_box import DraggableBox
from job_site_hub import JobSiteHub
from constants import ROLE_COLORS, DEFAULT_EMPLOYEE_X, DEFAULT_EMPLOYEE_Y, GRID_SIZE, JOB_HUB_WIDTH, JOB_HUB_HEIGHT, VERTICAL_SPACING, MAX_COLUMNS

class WhiteboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drag and Drop Whiteboard")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12), background='#ADD8E6')
        style.configure('TLabel', font=('Helvetica', 12), background='#F0F0F0')
        style.configure('TFrame', background='white')

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

        self.delete_employee_button = ttk.Button(self.side_frame, text="Delete Employee", command=self.delete_employee)
        self.delete_employee_button.pack(fill=tk.X, padx=5, pady=5)

        self.copy_employee_button = ttk.Button(self.side_frame, text="Copy Employee", command=self.copy_employee)
        self.copy_employee_button.pack(fill=tk.X, padx=5, pady=5)

        self.undo_button = ttk.Button(self.side_frame, text="Undo Delete", command=self.undo_delete_employee)
        self.undo_button.pack(fill=tk.X, padx=5, pady=5)

        self.last_deleted_employee = None

        self.scale = 1.0  # Initial scale
        self.canvas_transform = (0, 0)  # Initial canvas transformation (x, y)
        self.scroll_x = 0  # Initial scroll position x
        self.scroll_y = 0  # Initial scroll position y
        self.saved_scroll_region = None  # To store the scroll region

        self.root.bind('<Configure>', self.on_resize)
        self.root.bind('<FocusIn>', self.on_focus_in)
        self.root.bind('<FocusOut>', self.on_focus_out)  # Bind focus out event

        self.create_controls()
        self.load_state()

        self.canvas.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)

        # Define default position coordinates
        self.default_x = DEFAULT_EMPLOYEE_X
        self.default_y = DEFAULT_EMPLOYEE_Y

    def update_text_positions(self, hub, x1, y1, x2, y2):
        self.canvas.coords(hub.text_id, (x1 + x2) / 2, y1 - 10)
        self.canvas.coords(hub.erase_button_id, x2 - 15, y1 + 15)
        self.canvas.coords(hub.collapse_button_id, x1 + 15, y2 - 15)

    def redraw_canvas(self):
        print("Canvas is being redrawn")  # Log to console

        self.canvas.update_idletasks()

        canvas_width = self.canvas.winfo_width()
        max_columns = MAX_COLUMNS  # Fixed number of columns

        for i, hub in enumerate(self.canvas.hub_list):
            x = 50 + (JOB_HUB_WIDTH + 40) * (i % max_columns) * self.scale
            y = 50 + (JOB_HUB_HEIGHT + VERTICAL_SPACING) * (i // max_columns) * self.scale
            self.canvas.coords(hub.id, x, y, x + JOB_HUB_WIDTH * self.scale, y + JOB_HUB_HEIGHT * self.scale)
            hub.update_positions(self.scale)
            self.update_text_positions(hub, x, y, x + JOB_HUB_WIDTH * self.scale, y + JOB_HUB_HEIGHT * self.scale)

        self.bring_employee_names_to_front()
        self.update_scroll_region()
        self.apply_scale()

    def apply_scale(self):
        for box in self.employee_boxes:
            current_font_size = box.font[1]
            new_font_size = int(current_font_size * self.scale)
            new_font_size = max(8, new_font_size)  # Set a minimum font size
            box.font = (box.font[0], new_font_size, box.font[2])
            self.canvas.itemconfig(box.id, font=box.font)

            # Adjust circle size for draggable boxes
            circle_radius = box.circle_radius * self.scale
            x1, y1, x2, y2 = self.canvas.coords(box.circle_id)
            new_x2 = x1 + circle_radius
            new_y2 = y1 + circle_radius
            self.canvas.coords(box.circle_id, x1, y1, new_x2, new_y2)

        for hub in self.canvas.hub_list:
            hub.update_positions(self.scale)

    def apply_scale_to_elements(self):
        self.apply_scale()

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
        self.add_employee_popup.title("Add Employee")
        self.add_employee_popup.geometry("600x600")

        tk.Label(self.add_employee_popup, text="Name:").pack()
        self.name_entry = tk.Entry(self.add_employee_popup)
        self.name_entry.pack()
        if prefill_data:
            self.name_entry.insert(0, prefill_data["name"])

        tk.Label(self.add_employee_popup, text="Role:").pack()
        self.role_var = tk.StringVar()
        self.role_var.set("PM")
        self.role_dropdown = tk.OptionMenu(self.add_employee_popup, self.role_var, "PM", "GM", "Foreman", "Electrician",
                                           "Fire Alarm")
        self.role_dropdown.pack()
        if prefill_data:
            self.role_var.set(prefill_data["role"])

        tk.Label(self.add_employee_popup, text="Phone Number:").pack()  # Change label to Phone Number
        self.phone_entry = tk.Entry(self.add_employee_popup)
        self.phone_entry.pack()
        if prefill_data:
            self.phone_entry.insert(0, prefill_data.get("phone", ""))

        if prefill_data:
            tk.Button(self.add_employee_popup, text="Save",
                      command=lambda: self.save_edited_employee(prefill_data["index"])).pack()
        else:
            tk.Button(self.add_employee_popup, text="Add", command=self.add_employee_from_dialog).pack()

        self.phone_entry.bind('<KeyRelease>', self.format_phone_number)

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
        phone = self.phone_entry.get()
        if name and role:
            self.add_employee(name=name, role=role, phone=phone)
        self.add_employee_popup.destroy()

    def save_edited_employee(self, index):
        name = self.name_entry.get()
        role = self.role_var.get()
        phone = self.phone_entry.get()
        if name and role:
            box = self.employee_boxes[index]
            box.text = name
            box.role = role
            box.phone = phone
            box.color = ROLE_COLORS.get(role, "black")
            self.canvas.itemconfig(box.id, text=box.get_display_text())
            self.canvas.itemconfig(box.circle_id, fill=box.color, outline=box.color)
            self.update_unassigned_employees()
            self.save_state()
        self.add_employee_popup.destroy()

    def add_employee(self, name=None, role=None, phone=None, x=None, y=None, job_site=None, box=None):
        if name and role:
            # Use default position if x or y is not provided
            if x is None:
                x = self.default_x
            if y is None:
                y = self.default_y + len(self.employee_boxes) * 30
            draggable_box = DraggableBox(self, self.canvas, name, role, x, y, phone, job_site, box)
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
                    self.canvas.delete(box.id)
                    self.canvas.delete(box.circle_id)
                    self.employee_boxes.remove(box)
                    self.update_unassigned_employees()
                    self.save_state()
                    self.last_deleted_employee = {
                        "name": box.text, "role": box.role, "phone": box.phone,
                        "x": self.canvas.coords(box.id)[0],
                        "y": self.canvas.coords(box.id)[1]
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

    def add_job_site_hub(self, job_site=None, x=None, y=None, status=None):
        if job_site is None:
            existing_numbers = [int(hub.text.split()[-1]) for hub in self.canvas.hub_list if
                                hub.text.startswith("Job Site")]
            job_number = 1
            while job_number in existing_numbers:
                job_number += 1
            job_site = f"Job Site {job_number}"

        if x is not None and y is not None:
            hub = JobSiteHub(self, self.canvas, job_site, x, y)
            if status:
                hub.set_occupation_status(status)
            self.canvas.hub_list.append(hub)
            self.canvas.tag_raise(hub.text_id)
            self.bring_employee_names_to_front()
            self.update_scroll_region()
            self.save_state()
            return

        slot_size = (JOB_HUB_WIDTH + 40, JOB_HUB_HEIGHT + VERTICAL_SPACING)
        max_columns = 6  # Fixed number of columns

        for row in range(100):
            for col in range(max_columns):
                x_pos = 50 + col * slot_size[0]
                y_pos = 50 + row * slot_size[1]

                overlap = False
                for hub in self.canvas.hub_list:
                    coords = self.canvas.coords(hub.id)
                    if (x_pos < coords[2] and x_pos + slot_size[0] > coords[0] and
                            y_pos < coords[3] and y_pos + slot_size[1] > coords[1]):
                        overlap = True
                        break
                if not overlap:
                    x, y = x_pos, y_pos
                    hub = JobSiteHub(self, self.canvas, job_site, x, y)
                    if status:
                        hub.set_occupation_status(status)
                    self.canvas.hub_list.append(hub)
                    self.canvas.tag_raise(hub.text_id)
                    self.bring_employee_names_to_front()
                    self.update_scroll_region()
                    self.save_state()
                    return

        raise Exception("No available position for new job site hub")

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
        try:
            state = {
                "employees": [{"name": box.text, "role": box.role, "phone": getattr(box, "phone", ""),
                               "job_site": box.current_snap_box["hub"].text if box.current_snap_box else None,
                               "box": box.current_snap_box["box"] if box.current_snap_box else None,
                               "x": self.canvas.coords(box.id)[0], "y": self.canvas.coords(box.id)[1]} for box in
                              self.employee_boxes],
                "job_sites": [{"name": hub.text, "x": self.canvas.coords(hub.id)[0], "y": self.canvas.coords(hub.id)[1],
                               "status": hub.get_occupation_status()} for hub in self.canvas.hub_list],
                "scale": self.scale,
                "canvas_transform": self.canvas_transform,
                "scroll_x": self.canvas.xview()[0],
                "scroll_y": self.canvas.yview()[0]
            }
            with open('state.json', 'w') as f:
                json.dump(state, f)
            print(f"State saved: {state}")
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self):
        try:
            with open('state.json', 'r') as f:
                state = json.load(f)
                print(f"State loaded: {state}")
                job_site_dict = {}

                # First, add all job sites
                for job in state["job_sites"]:
                    job["status"].setdefault("Electrician", [])
                    hub = self.add_job_site_hub(job["name"], job["x"], job["y"], job.get("status",
                                                                                         {"PM": False, "GM": False,
                                                                                          "Foreman": False,
                                                                                          "Electrician": []}))
                    job_site_dict[job["name"]] = hub

                # Then, add all employees
                for emp in state["employees"]:
                    job_site = emp.get("job_site")
                    box_type = emp.get("box")
                    x = emp.get("x", None)
                    y = emp.get("y", None)
                    phone = emp.get("phone", "")

                    if x is None or y is None:
                        # Provide default position if coordinates are not available
                        x = self.default_x
                        y = self.default_y + len(self.employee_boxes) * 30

                    self.add_employee(emp["name"], emp.get("role"), phone, x, y, job_site, box_type)

                # Load the scale and canvas transformation
                self.scale = state.get("scale", 1.0)
                self.canvas_transform = state.get("canvas_transform", (0, 0))
                self.scroll_x = state.get("scroll_x", 0)
                self.scroll_y = state.get("scroll_y", 0)

        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading state: {e}")
        self.update_unassigned_employees()
        self.reposition_unassigned_employees()

    def update_employee_position(self, name, job_site, box, employee_id):
        if job_site and box:
            for hub in self.canvas.hub_list:
                if hub.text == job_site:
                    hub.update_occupation(box, True, employee_id)
        self.save_state()

    def update_unassigned_employees(self):
        self.unassigned_listbox.delete(0, tk.END)
        for box in self.employee_boxes:
            if not box.current_snap_box:
                self.unassigned_listbox.insert(tk.END, box.text)

if __name__ == "__main__":
    root = tk.Tk()
    app = WhiteboardApp(root)
    root.mainloop()