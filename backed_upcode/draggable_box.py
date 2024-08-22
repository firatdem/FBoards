import tkinter as tk
from constants import ROLE_COLORS, DRAG_DELAY

class DraggableBox:
    def __init__(self, app, canvas, text, role, x, y, phone=None, job_site=None, box=None, skills=None, sst_card="No",
                 nj_license="No", electrician_ranking="1"):
        self.app = app
        self.canvas = canvas
        self.text = text
        self.role = role
        self.phone = phone
        self.skills = skills if skills else []
        self.sst_card = sst_card
        self.nj_license = nj_license
        self.electrician_ranking = electrician_ranking
        self.color = ROLE_COLORS.get(role, "black")
        self.font = ("Helvetica", 12, "bold")
        self.circle_radius = 15
        self.circle_id = canvas.create_oval(x - self.circle_radius, y - self.circle_radius,
                                            x + self.circle_radius, y + self.circle_radius,
                                            fill=self.color, outline=self.color)

        self.id = canvas.create_text(x, y, text=self.get_display_text(), font=self.font, tags="draggable", anchor=tk.NW)

        self.canvas.tag_bind(self.id, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.id, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.id, "<Button-3>", self.on_right_click)
        self._drag_data = {"x": 0, "y": 0}
        self.current_snap_box = None
        self.drag_delay = None
        self.is_dragging = False

        if job_site and box:
            for hub in self.canvas.hub_list:
                if hub.text == job_site:
                    self.current_snap_box = {"hub": hub, "box": box, "occupied": True}
                    hub.update_occupation(box, True, self.id)
                    self.snap_to_box()
                    break

    def __del__(self):
        self.canvas.delete(self.circle_id)
        self.canvas.delete(self.id)
        self.canvas.tag_unbind(self.id, "<ButtonPress-1>")
        self.canvas.tag_unbind(self.id, "<ButtonRelease-1>")
        self.canvas.tag_unbind(self.id, "<Button-3>")

    def get_display_text(self):
        return f"{self.text}\n{self.phone}" if self.phone else self.text

    def snap_to_box(self):
        if self.current_snap_box:
            hub = self.current_snap_box["hub"]
            box = self.current_snap_box["box"]
            left_x, top_y = self.get_snap_box_left_top(hub, box)
            self.canvas.coords(self.id, left_x + 35, top_y)
            circle_radius = self.circle_radius * self.app.scale
            self.canvas.coords(self.circle_id, left_x + 10, top_y, left_x + 10 + circle_radius, top_y + circle_radius)
            self.canvas.itemconfig(self.id, text=self.get_display_text())

    def get_snap_box_left_top(self, hub, box):
        if box == "PM":
            coords = self.canvas.coords(hub.pm_box)
        elif box == "GM":
            coords = self.canvas.coords(hub.gm_box)
        elif box == "Foreman":
            coords = self.canvas.coords(hub.foreman_box)
        elif box == "Electrician" or box == "Fire Alarm":
            coords = self.canvas.coords(hub.electrician_box)
        else:
            coords = [0, 0, 0, 0]
        left_x = coords[0]
        top_y = coords[1]
        return left_x, top_y

    def on_press(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.drag_delay = self.canvas.after(DRAG_DELAY, self.start_drag, event)

    def start_drag(self, event):
        self.is_dragging = True
        self.canvas.tag_bind(self.id, "<B1-Motion>", self.on_motion)

    def on_motion(self, event):
        if not self.is_dragging:
            return
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        self.canvas.move(self.id, delta_x, delta_y)
        self.canvas.move(self.circle_id, delta_x, delta_y)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        for hub in self.canvas.hub_list:
            for box_type in ["PM", "GM", "Foreman", "Electrician"]:
                box_coords = self.canvas.coords(getattr(hub, f"{box_type.lower()}_box"))
                if box_coords[0] < x < box_coords[2] and box_coords[1] < y < box_coords[3]:
                    self.canvas.itemconfig(getattr(hub, f"{box_type.lower()}_box"), fill="lightgreen")
                else:
                    self.canvas.itemconfig(getattr(hub, f"{box_type.lower()}_box"), fill="white")

    def snap_to_hub(self, hub, box_type, coords):
        if box_type != "Electrician" and box_type != "Fire Alarm" and getattr(hub, f"{box_type.lower()}_occupied"):
            return False

        if self.current_snap_box:
            self.current_snap_box["hub"].update_occupation(self.current_snap_box["box"], False, self.id)

        left_x = coords[0]
        top_y = coords[1]
        self.current_snap_box = {"hub": hub, "box": box_type, "occupied": True}
        hub.update_occupation(box_type, True, self.id)
        self.canvas.coords(self.id, left_x + 35, top_y)
        circle_radius = self.circle_radius * self.app.scale
        self.canvas.coords(self.circle_id, left_x + 10, top_y, left_x + 10 + circle_radius, top_y + circle_radius)
        self.canvas.tag_raise(self.id)
        self.canvas.tag_raise(self.circle_id)
        self.canvas.itemconfig(self.id, text=self.get_display_text())
        self.app.update_employee_position(self.text, hub.text, box_type, self.id)
        self.app.update_unassigned_employees()
        return True

    def on_release(self, event):
        if self.drag_delay:
            self.canvas.after_cancel(self.drag_delay)
            self.drag_delay = None

        if not self.is_dragging:
            return

        self.is_dragging = False
        self.canvas.tag_unbind(self.id, "<B1-Motion>")
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        for hub in self.canvas.hub_list:
            for box_type in ["PM", "GM", "Foreman", "Electrician"]:
                coords = self.canvas.coords(getattr(hub, f"{box_type.lower()}_box"))
                if coords[0] < x < coords[2] and coords[1] < y < coords[3]:
                    if self.snap_to_hub(hub, box_type, coords):
                        hub.update_electrician_positions()
                        return

        if self.current_snap_box:
            self.current_snap_box["hub"].update_occupation(self.current_snap_box["box"], False, self.id)
        self.current_snap_box = None
        self.app.update_employee_position(self.text, None, None, self.id)
        self.app.update_unassigned_employees()

    def change_role(self, new_role):
        self.role = new_role
        self.color = ROLE_COLORS.get(new_role, "black")
        self.canvas.itemconfig(self.circle_id, fill=self.color, outline=self.color)

        if self.current_snap_box:
            self.current_snap_box["hub"].update_occupation(self.current_snap_box["box"], False, self.id)
            self.current_snap_box = None

        self.snap_to_box()
        self.app.update_employee_position(self.text, None, None, self.id)
        self.app.update_unassigned_employees()
        self.app.save_state()

    def on_right_click(self, event):
        self.app.open_add_employee_dialog(prefill_data={
            "name": self.text,
            "role": self.role,
            "phone": self.phone,
            "skills": self.skills,
            "sst_card": self.sst_card,
            "nj_license": self.nj_license,
            "electrician_ranking": self.electrician_ranking,
            "index": self.app.employee_boxes.index(self)
        })
