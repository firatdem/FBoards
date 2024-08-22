# whiteboard_online.py
import tkinter as tk
from tkinter import ttk
import json
import asyncio
import websockets
from threading import Thread
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

        self.create_controls()
        self.load_state()

        self.canvas.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)

        # Define default position coordinates
        self.default_x = DEFAULT_EMPLOYEE_X
        self.default_y = DEFAULT_EMPLOYEE_Y

        self.websocket = None
        self.start_websocket()

    def start_websocket(self):
        asyncio.get_event_loop().run_until_complete(self.connect_to_websocket())

    async def connect_to_websocket(self):
        self.websocket = await websockets.connect('ws://localhost:6789')
        await self.receive_updates()

    async def receive_updates(self):
        while True:
            message = await self.websocket.recv()
            data = json.loads(message)
            self.handle_update(data)

    def send_update(self, data):
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.send(json.dumps(data)), asyncio.get_event_loop())

    def handle_update(self, data):
        action = data.get("action")
        if action == "add_employee":
            self.add_employee(
                name=data["name"], role=data["role"], phone=data["phone"],
                x=data["x"], y=data["y"], skills=data["skills"],
                sst_card=data["sst_card"], nj_license=data["nj_license"],
                electrician_ranking=data["electrician_ranking"]
            )
        elif action == "delete_employee":
            self.delete_employee_by_name(data["name"])
        elif action == "update_employee_position":
            for box in self.employee_boxes:
                if box.text == data["name"]:
                    box.update_position(data["x"], data["y"])
                    break

    # Update existing methods to send updates

    def add_employee_from_dialog(self):
        name = self.name_entry.get()
        role = self.role_var.get()
        phone = self.phone_entry.get()
        skills = [self.skills_listbox.get(i) for i in self.skills_listbox.curselection()]
        sst_card = self.sst_card_var.get()
        nj_license = self.nj_license_var.get()
        electrician_ranking = self.electrician_ranking_var.get()
        if name and role:
            self.add_employee(name=name, role=role, phone=phone, skills=skills, sst_card=sst_card,
                              nj_license=nj_license, electrician_ranking=electrician_ranking)
            self.send_update({
                "action": "add_employee",
                "name": name,
                "role": role,
                "phone": phone,
                "skills": skills,
                "sst_card": sst_card,
                "nj_license": nj_license,
                "electrician_ranking": electrician_ranking,
                "x": self.default_x,
                "y": self.default_y + len(self.employee_boxes) * 30
            })
        self.add_employee_popup.destroy()

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
                    self.send_update({"action": "delete_employee", "name": box.text})
                    break

    def update_employee_position(self, name, job_site, box, employee_id):
        if job_site and box:
            for hub in self.canvas.hub_list:
                if hub.text == job_site:
                    hub.update_occupation(box, True, employee_id)
        self.save_state()
        for box in self.employee_boxes:
            if box.text == name:
                x, y = self.canvas.coords(box.id)[:2]
                self.send_update({
                    "action": "update_employee_position",
                    "name": name,
                    "x": x,
                    "y": y
                })
                break

    # ... rest of the WhiteboardApp methods ...

if __name__ == "__main__":
    root = tk.Tk()
    app = WhiteboardApp(root)
    # Run the websocket client in a separate thread
    Thread(target=app.start_websocket).start()
    root.mainloop()
