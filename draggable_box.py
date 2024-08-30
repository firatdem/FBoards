import tkinter as tk
from constants import ROLE_COLORS, DRAG_DELAY

class DraggableBox:
    def __init__(self, app, canvas, text, role, x, y, phone, job_site, box, skills, sst_card, nj_ny_certified, electrician_rank, certifications, worker_status, current_status):
        self.app = app
        self.canvas = canvas
        self.text = text
        self.role = role
        self.x = x
        self.y = y
        self.phone = phone
        self.job_site = job_site
        self.box = box
        self.skills = skills
        self.sst_card = sst_card
        self.nj_ny_certified = nj_ny_certified
        self.electrician_rank = electrician_rank
        self.certifications = certifications or []
        self.worker_status = worker_status
        self.current_status = current_status
        self.current_snap_box = None


        self.color = ROLE_COLORS.get(role, "black")
        self.font = ("Helvetica", 14, "bold")
        self.circle_radius = 15

        # Use provided coordinates or default to app default
        x = x if x is not None else (app.default_x if job_site is None else job_site.x)
        y = y if y is not None else (app.default_y + len(app.employee_boxes) * 30 if job_site is None else job_site.y)

        self.circle_id = canvas.create_oval(x - self.circle_radius, y,
                                            x + self.circle_radius, y,
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

    def get_display_text_supers(self):
        """Generate the display text for the box."""
        # Debug prints to check values
        print(f"Role: {self.role}, Skills: {self.skills}")

        # Set a default value for displayName
        displayText = "Unknown"  # or some other default value that makes sense in your context

        # Check if "Helper" is in the skills list
        if self.role == "PM" and self.skills:
            displayText = "PM"  # FOR WHAT IS SHOWN BASED ON THEIR ROLE AND SKILLS
        elif self.role == "PM" and self.skills:
            displayText = "PM"
        elif self.role == "PM" and self.skills:
            displayText = "PM"
        elif self.role == "PM" and self.skills:
            displayText = "PM"
        elif self.role == "PM" and not self.skills:
            displayText = "PM"

        elif self.role == "GM" and self.skills:
            displayText = "GC"  # FOR WHAT IS SHOWN BASED ON THEIR ROLE AND SKILLS
        elif self.role == "GM" and self.skills:
           displayText = "GC"
        elif self.role == "GM" and self.skills:
            displayText = "GC"
        elif self.role == "GM" and self.skills:
            displayText = "GC"
        elif self.role == "GM" and not self.skills:
            displayText = "GC"

        elif self.role == "Foreman" and self.skills:
            displayText = "FM"  # FOR WHAT IS SHOWN BASED ON THEIR ROLE AND SKILLS
        elif self.role == "Foreman" and self.skills:
           displayText = "FM"
        elif self.role == "Foreman" and self.skills:
            displayText = "FM"
        elif self.role == "Foreman" and self.skills:
            displayText = "FM"
        elif self.role == "Foreman" and not self.skills:
            displayText = "FM"

        return f"{displayText} - {self.text} "

    def get_display_text(self):
        """Generate the display text for the box."""
        # Debug prints to check values
        print(f"Role: {self.role}, Skills: {self.skills}")

        # Set a default value for displayName
        displayText = "Unknown"  # or some other default value that makes sense in your context

        # Check if "Helper" is in the skills list
        if self.role == "Electrician" and "Helper" in self.skills:
            displayText = "E - H"  # FOR WHAT IS SHOWN BASED ON THEIR ROLE AND SKILLS
        elif self.role == "Electrician" and "Junior Mechanic" in self.skills:
            displayText = "E - JM"
        elif self.role == "Electrician" and "Mechanic" in self.skills:
            displayText = "E - M"
        elif self.role == "Electrician" and "Sub Foreman" in self.skills:
            displayText = "E - SF"
        elif self.role == "Fire Alarm Electrician" and "Fire Alarm Helper" in self.skills:
            displayText = "FA - H"
        elif self.role == "Fire Alarm Electrician" and "Fire Alarm Junior Mechanic" in self.skills:
            displayText = "FA - JM"
        elif self.role == "Fire Alarm Electrician" and "Fire Alarm Mechanic" in self.skills:
            displayText = "FA - M"
        elif self.role == "Fire Alarm Electrician" and "Fire Alarm Sub Foreman" in self.skills:
            displayText = "FA - SF"
        elif self.role == "Roughing Electrician" and "Roughing Helper" in self.skills:
            displayText = "R - H"
        elif self.role == "Roughing Electrician" and "Roughing Junior Mechanic" in self.skills:
            displayText = "R - JM"
        elif self.role == "Roughing Electrician" and "Roughing Mechanic" in self.skills:
            displayText = "R - M"
        elif self.role == "Roughing Electrician" and "Roughing Sub Foreman" in self.skills:
            displayText = "R - SF"

        return f"{displayText} - {self.electrician_rank} - {self.text} "

    def snap_to_box(self):
        if self.current_snap_box:
            hub = self.current_snap_box["hub"]
            box = self.current_snap_box["box"]
            left_x, top_y = self.get_snap_box_left_top(hub, box)
            self.canvas.coords(self.id, left_x + 35, top_y)
            circle_radius = self.circle_radius * self.app.scale
            self.canvas.coords(self.circle_id, left_x + 10, top_y, left_x + 10 + circle_radius, top_y + circle_radius)

            if self.role in ("Electrician", "Fire Alarm Electrician", "Roughing Electrician"):
                self.canvas.itemconfig(self.id, text=self.get_display_text())
            else:
                self.canvas.itemconfig(self.id, text=self.get_display_text_supers())

    def get_snap_box_left_top(self, hub, box):
        if box == "PM":
            coords = self.canvas.coords(hub.pm_box)
        elif box == "GM":
            coords = self.canvas.coords(hub.gm_box)
        elif box == "Foreman":
            coords = self.canvas.coords(hub.foreman_box)
        elif box == "Electrician":
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
        if self.role == ("Electrician", "Fire Alarm Electrician", "Roughing Electrician"):
            self.canvas.itemconfig(self.id, text=self.get_display_text())
        else:
            self.canvas.itemconfig(self.id, text=self.get_display_text_supers())
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
            "electrician_rank": self.electrician_rank,
            "certifications": self.certifications,
            "nj_ny_certified": self.nj_ny_certified,
            "worker_status": self.worker_status,
            "current_status": self.current_status,
            "index": self.app.employee_boxes.index(self)
        })
