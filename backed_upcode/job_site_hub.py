# jobsitehub.py

import tkinter as tk
import tkinter.messagebox as messagebox
from constants import ROLE_COLORS, BOX_HEIGHT, ELECTRICIAN_BOX_HEIGHT, JOB_HUB_HEIGHT_COLLAPSED

class JobSiteHub:
    def __init__(self, app, canvas, text, x, y, address=""):
        self.app = app
        self.canvas = canvas
        self.text = text
        self.address = address
        self.circle_radius = 15
        self.width = 320
        self.height = 800
        self.font = ("Helvetica", 12, "bold")
        self.collapsed = False
        self.id = canvas.create_rectangle(x, y, x + self.width, y + self.height, fill="lightblue", tags="hub")
        self.text_id = canvas.create_text(x + self.width / 2, y - 20, text=self.get_display_text(), font=self.font,
                                          tags=("hub", str(len(canvas.hub_list))), anchor=tk.S)

        self.canvas.tag_bind(self.text_id, "<Button-3>", self.rename_hub)
        self.erase_button_id = canvas.create_text(x + self.width - 15, y + 15, text="X", font=self.font, fill="red",
                                                  tags="erase_button")
        self.canvas.tag_bind(self.erase_button_id, "<ButtonPress-1>", self.confirm_erase_hub)

        self.pm_box = self.create_snap_box()
        self.gm_box = self.create_snap_box()
        self.foreman_box = self.create_snap_box()
        self.electrician_box = self.create_snap_box()

        self.collapse_button_id = canvas.create_text(x + 15, y + self.height - 15, text="[-]", font=self.font,
                                                     fill="black", tags="collapse_button")
        self.canvas.tag_bind(self.collapse_button_id, "<ButtonPress-1>", self.toggle_electrician_box)

        self.pm_occupied = False
        self.gm_occupied = False
        self.foreman_occupied = False
        self.electrician_occupied = []

        self.update_positions()

    def __del__(self):
        # Cleanup bindings and canvas items
        self.canvas.delete(self.id)
        self.canvas.delete(self.text_id)
        self.canvas.delete(self.erase_button_id)
        self.canvas.delete(self.collapse_button_id)
        self.canvas.delete(self.pm_box)
        self.canvas.delete(self.gm_box)
        self.canvas.delete(self.foreman_box)
        self.canvas.delete(self.electrician_box)
        self.canvas.tag_unbind(self.text_id, "<Button-3>")
        self.canvas.tag_unbind(self.erase_button_id, "<ButtonPress-1>")
        self.canvas.tag_unbind(self.collapse_button_id, "<ButtonPress-1>")

    def get_display_text(self):
        return f"{self.text}\n{self.address}"

    def create_snap_box(self):
        return self.canvas.create_rectangle(0, 0, 1, 1, fill="white", outline="black", tags="snap_box")

    def update_positions(self, scale=1.0):
        self.scale = scale
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        width = x2 - x1
        height = y2 - y1

        self.canvas.coords(self.pm_box, x1 + 10 * self.scale, y1 + 10 * self.scale,
                           x1 + width - 10 * self.scale, y1 + 10 * self.scale + BOX_HEIGHT * self.scale)
        self.canvas.coords(self.gm_box, x1 + 10 * self.scale, y1 + 20 * self.scale + BOX_HEIGHT * self.scale,
                           x1 + width - 10 * self.scale, y1 + 20 * self.scale + 2 * BOX_HEIGHT * self.scale)
        self.canvas.coords(self.foreman_box, x1 + 10 * self.scale, y1 + 30 * self.scale + 2 * BOX_HEIGHT * self.scale,
                           x1 + width - 10 * self.scale, y1 + 30 * self.scale + 3 * BOX_HEIGHT * self.scale)

        if not self.collapsed:
            self.canvas.coords(self.electrician_box, x1 + 10 * self.scale,
                               y1 + height - ELECTRICIAN_BOX_HEIGHT * self.scale - 10 * self.scale,
                               x1 + width - 10 * self.scale, y1 + height - 10 * self.scale)
            self.canvas.itemconfig(self.collapse_button_id, text="[-]")
        else:
            self.canvas.coords(self.electrician_box, x1 + 10 * self.scale, y1 + height - 50 * self.scale,
                               x1 + width - 10 * self.scale, y1 + height - 10 * self.scale)
            self.canvas.itemconfig(self.collapse_button_id, text="[+]")

        self.canvas.coords(self.collapse_button_id, x1 + 15 * self.scale, y2 - 15 * self.scale)
        self.canvas.coords(self.erase_button_id, x2 - 15 * self.scale, y1 + 15 * self.scale)

        self.canvas.tag_raise(self.erase_button_id)
        self.update_all_positions()

    def toggle_electrician_box(self, event):
        self.collapsed = not self.collapsed
        if self.collapsed:
            x1, y1, x2, y2 = self.canvas.coords(self.id)
            self.canvas.coords(self.id, x1, y1, x2, y1 + JOB_HUB_HEIGHT_COLLAPSED)
        else:
            x1, y1, x2, y2 = self.canvas.coords(self.id)
            self.canvas.coords(self.id, x1, y1, x2, y1 + 800)
        self.update_positions()
        self.update_electrician_positions()

    def confirm_erase_hub(self, event):
        result = messagebox.askyesno("Delete Job Hub", "Are you sure you want to delete this job hub?")
        if result:
            self.erase_hub(event)

    def update_all_positions(self):
        self.update_electrician_positions()
        self.update_pm_positions()
        self.update_gm_positions()
        self.update_foreman_positions()

    def update_pm_positions(self):
        if self.pm_occupied:
            self.update_employee_position(self.pm_box, "PM")

    def update_gm_positions(self):
        if self.gm_occupied:
            self.update_employee_position(self.gm_box, "GM")

    def update_foreman_positions(self):
        if self.foreman_occupied:
            self.update_employee_position(self.foreman_box, "Foreman")

    def update_employee_position(self, box, role):
        x1, y1, x2, y2 = self.canvas.coords(box)
        employee_id = self.get_employee_id_by_role(role)
        if employee_id:
            self.canvas.coords(employee_id, x1 + 35, y1)
            circle_id = self.app.find_circle(employee_id)
            if circle_id:
                self.canvas.coords(circle_id, x1 + 10, y1 + 5, x1 + 10 + (self.circle_radius * self.app.scale), y1 + (self.circle_radius * self.app.scale))
            self.canvas.itemconfig(employee_id, state='normal')
            if circle_id:
                self.canvas.itemconfig(circle_id, state='normal')

    def get_employee_id_by_role(self, role):
        for box in self.app.employee_boxes:
            if box.role == role and box.current_snap_box and box.current_snap_box["hub"] == self:
                return box.id
        return None

    def update_occupation(self, box, occupied, employee_id=None):
        if box == "PM":
            self.pm_occupied = occupied
        elif box == "GM":
            self.gm_occupied = occupied
        elif box == "Foreman":
            self.foreman_occupied = occupied
        elif box == "Electrician" or box == "Fire Alarm":
            if not occupied:
                if employee_id in self.electrician_occupied:
                    self.electrician_occupied.remove(employee_id)
            else:
                if employee_id and employee_id not in self.electrician_occupied:
                    self.electrician_occupied.append(employee_id)
            self.update_electrician_positions()

    def update_electrician_positions(self):
        x1, y1, x2, y2 = self.canvas.coords(self.electrician_box)
        box_height = 30
        padding = 5

        valid_electricians = []
        for employee_id in self.electrician_occupied:
            if self.canvas.type(employee_id):
                valid_electricians.append(employee_id)

        self.electrician_occupied = valid_electricians

        for index, employee_id in enumerate(self.electrician_occupied):
            y_offset = y1 + index * (box_height + padding) * self.app.scale
            if self.canvas.type(employee_id) == 'text':
                self.canvas.coords(employee_id, x1 + 35, y_offset)
            circle_id = self.app.find_circle(employee_id)
            if circle_id and self.canvas.type(circle_id) == 'oval':
                circle_radius = 10 * self.app.scale
                self.canvas.coords(circle_id, x1 + 10, y_offset + 5, x1 + 10 + circle_radius, y_offset + circle_radius)
            if self.collapsed:
                self.canvas.itemconfig(employee_id, state='hidden')
                if circle_id:
                    self.canvas.itemconfig(circle_id, state='hidden')
            else:
                self.canvas.itemconfig(employee_id, state='normal')
                if circle_id:
                    self.canvas.itemconfig(circle_id, state='normal')

    def get_occupation_status(self):
        pm_coords = self.canvas.coords(self.pm_box)
        gm_coords = self.canvas.coords(self.gm_box)
        foreman_coords = self.canvas.coords(self.foreman_box)
        electrician_box_coords = self.canvas.coords(self.electrician_box)
        return {
            "PM": self.pm_occupied,
            "GM": self.gm_occupied,
            "Foreman": self.foreman_occupied,
            "Electrician": self.electrician_occupied,
            "ElectricianBoxCoords": electrician_box_coords,
            "PMCoords": pm_coords,
            "GMCoords": gm_coords,
            "ForemanCoords": foreman_coords,
            "Collapsed": self.collapsed
        }

    def set_occupation_status(self, status):
        self.pm_occupied = status["PM"]
        self.gm_occupied = status["GM"]
        self.foreman_occupied = status["Foreman"]
        self.electrician_occupied = status.get("Electrician", [])
        if isinstance(self.electrician_occupied, bool):
            self.electrician_occupied = []
        self.collapsed = status.get("Collapsed", False)
        self.canvas.coords(self.electrician_box, status["ElectricianBoxCoords"])
        self.canvas.coords(self.pm_box, status["PMCoords"])
        self.canvas.coords(self.gm_box, status["GMCoords"])
        self.canvas.coords(self.foreman_box, status["ForemanCoords"])
        self.update_all_positions()

    def erase_hub(self, event):
        for box in [self.pm_box, self.gm_box, self.foreman_box, self.electrician_box]:
            self.canvas.delete(box)
        self.canvas.delete(self.id)
        self.canvas.delete(self.text_id)
        self.canvas.delete(self.erase_button_id)
        self.canvas.delete(self.collapse_button_id)
        self.app.canvas.hub_list.remove(self)
        self.app.save_state()

    def rename_hub(self, event):
        self.rename_popup = tk.Toplevel(self.canvas)
        self.rename_popup.title("Rename Job Site")

        tk.Label(self.rename_popup, text="New Name:").pack()
        self.new_name_entry = tk.Entry(self.rename_popup)
        self.new_name_entry.pack()
        self.new_name_entry.insert(0, self.text)

        tk.Label(self.rename_popup, text="New Address:").pack()
        self.new_address_entry = tk.Entry(self.rename_popup)
        self.new_address_entry.pack()
        self.new_address_entry.insert(0, self.address)

        tk.Button(self.rename_popup, text="OK", command=self.save_new_name).pack()

    def save_new_name(self):
        new_name = self.new_name_entry.get()
        new_address = self.new_address_entry.get()
        if (not new_name.isspace()) and new_name != '':
            self.text = new_name
        if new_address != '':
            self.address = new_address
        self.canvas.itemconfig(self.text_id, text=self.get_display_text())
        self.rename_popup.destroy()
        self.app.save_state()
