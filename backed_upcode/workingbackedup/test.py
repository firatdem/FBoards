import math
import warnings
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from constants import ROLE_COLORS, JOB_HUB_WIDTH, JOB_HUB_HEIGHT, BOX_HEIGHT, ELECTRICIAN_BOX_HEIGHT, JOB_HUB_HEIGHT_COLLAPSED
import tkinter as tk
from tkinter import ttk
import json
from draggable_box import DraggableBox
from job_site_hub import JobSiteHub
from constants import ROLE_COLORS, DEFAULT_EMPLOYEE_X, DEFAULT_EMPLOYEE_Y, GRID_SIZE, JOB_HUB_WIDTH, JOB_HUB_HEIGHT, VERTICAL_SPACING, MAX_COLUMNS
import tkinter.messagebox as messagebox

class AutoScrollbar(ttk.Scrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        raise tk.TclError('Cannot use place with the widget ' + self.__class__.__name__)

class CanvasImage:
    def __init__(self, placeholder):
        self.imscale = 1.0
        self.__delta = 1.3
        self.__filter = Image.ANTIALIAS
        self.__previous_state = 0

        self.__imframe = ttk.Frame(placeholder)
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')

        self.canvas = tk.Canvas(self.__imframe, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()
        hbar.configure(command=self.__scroll_x)
        vbar.configure(command=self.__scroll_y)

        self.canvas.bind('<Configure>', lambda event: self.__show_image())
        self.canvas.bind('<ButtonPress-1>', self.__move_from)
        self.canvas.bind('<B1-Motion>', self.__move_to)
        self.canvas.bind('<MouseWheel>', self.__wheel)
        self.canvas.bind('<Button-5>', self.__wheel)
        self.canvas.bind('<Button-4>', self.__wheel)
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))

        self.__huge = False
        self.__huge_size = 14000
        self.__band_width = 1024
        Image.MAX_IMAGE_PIXELS = 1000000000
        self.imwidth, self.imheight = 1000, 1000  # Default size for the canvas, can be modified
        self.__min_side = min(self.imwidth, self.imheight)
        self.__pyramid = [Image.new("RGB", (self.imwidth, self.imheight), "white")]
        self.__ratio = 1.0
        self.__curr_img = 0
        self.__scale = self.imscale * self.__ratio
        self.__reduction = 2
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()
        self.canvas.focus_set()

    def __scroll_x(self, *args, **kwargs):
        self.canvas.xview(*args)
        self.__show_image()

    def __scroll_y(self, *args, **kwargs):
        self.canvas.yview(*args)
        self.__show_image()

    def __show_image(self):
        box_image = self.canvas.coords(self.container)
        box_canvas = (self.canvas.canvasx(0), self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        if box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0] = box_img_int[0]
            box_scroll[2] = box_img_int[2]
        if box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1] = box_img_int[1]
            box_scroll[3] = box_img_int[3]
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))
        x1 = max(box_canvas[0] - box_image[0], 0)
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            image = self.__pyramid[0].crop((int(x1 / self.__scale), int(y1 / self.__scale),
                                            int(x2 / self.__scale), int(y2 / self.__scale)))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)
            self.canvas.imagetk = imagetk

    def __move_from(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()

    def outside(self, x, y):
        bbox = self.canvas.coords(self.container)
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False
        else:
            return True

    def __wheel(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return
        scale = 1.0
        if event.num == 5 or event.delta == -120:
            if round(self.__min_side * self.imscale) < 30: return
            self.imscale /= self.__delta
            scale /= self.__delta
        if event.num == 4 or event.delta == 120:
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale: return
            self.imscale *= self.__delta
            scale *= self.__delta
        k = self.imscale * self.__ratio
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        self.canvas.scale('all', x, y, scale, scale)
        self.redraw_figures()
        self.__show_image()

    def __keystroke(self, event):
        if event.state - self.__previous_state == 4:
            pass
        else:
            self.__previous_state = event.state
            if event.keycode in [68, 39, 102]:
                self.__scroll_x('scroll', 1, 'unit', event=event)
            elif event.keycode in [65, 37, 100]:
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in [87, 38, 104]:
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in [83, 40, 98]:
                self.__scroll_y('scroll', 1, 'unit', event=event)

    def destroy(self):
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)
        del self.__pyramid[:]
        del self.__pyramid
        self.canvas.destroy()
        self.__imframe.destroy()

class JobSiteHub:
    def __init__(self, app, canvas, text, x, y, address=""):
        self.app = app
        self.canvas = canvas
        self.text = text
        self.address = address
        self.circle_radius = 10
        self.width = JOB_HUB_WIDTH
        self.height = JOB_HUB_HEIGHT
        self.font = ("Helvetica", 12, "bold")
        self.collapsed = False  # Initial state of the electrician box
        self.id = canvas.create_rectangle(x, y, x + self.width, y + self.height, fill="lightblue", tags="hub")
        self.text_id = canvas.create_text(x + self.width / 2, y - 20, text=self.get_display_text(), font=self.font,
                                          tags=("hub", str(len(canvas.hub_list))), anchor=tk.S)

        self.canvas.tag_bind(self.text_id, "<Button-3>", self.rename_hub)  # Change to right-click
        self.erase_button_id = canvas.create_text(x + self.width - 15, y + 15, text="X", font=self.font, fill="red",
                                                  tags="erase_button")
        self.canvas.tag_bind(self.erase_button_id, "<ButtonPress-1>", self.confirm_erase_hub)

        self.pm_box = self.create_snap_box()
        self.gm_box = self.create_snap_box()
        self.foreman_box = self.create_snap_box()
        self.electrician_box = self.create_snap_box()

        # Add collapse/expand button
        self.collapse_button_id = canvas.create_text(x + 15, y + self.height - 15, text="[-]", font=self.font,
                                                     fill="black", tags="collapse_button")
        self.canvas.tag_bind(self.collapse_button_id, "<ButtonPress-1>", self.toggle_electrician_box)

        self.pm_occupied = False
        self.gm_occupied = False
        self.foreman_occupied = False
        self.electrician_occupied = []

        self.update_positions()

    def get_display_text(self):
        return f"{self.text}\n{self.address}"

    def create_snap_box(self):
        return self.canvas.create_rectangle(0, 0, 1, 1, fill="white", outline="black", tags="snap_box")

    def update_positions(self, scale=1.0):
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        width = x2 - x1
        height = y2 - y1

        self.canvas.coords(self.pm_box, x1 + 10, y1 + 10, x1 + self.width - 10,
                           y1 + 10 + BOX_HEIGHT)
        self.canvas.coords(self.gm_box, x1 + 10, y1 + 20 + BOX_HEIGHT,
                           x1 + self.width - 10, y1 + 20 + 2 * BOX_HEIGHT)
        self.canvas.coords(self.foreman_box, x1 + 10, y1 + 30 + 2 * BOX_HEIGHT,
                           x1 + self.width - 10, y1 + 30 + 3 * BOX_HEIGHT)

        if not self.collapsed:
            self.canvas.coords(self.electrician_box, x1 + 10,
                               y1 + self.height - ELECTRICIAN_BOX_HEIGHT - 10,
                               x1 + self.width - 10, y1 + self.height - 10)
            self.canvas.itemconfig(self.collapse_button_id, text="[-]")
        else:
            self.canvas.coords(self.electrician_box, x1 + 10, y1 + self.height - 50,
                               x1 + self.width - 10, y1 + self.height - 10)
            self.canvas.itemconfig(self.collapse_button_id, text="[+]")

        self.canvas.coords(self.collapse_button_id, x1 + 15, y2 - 15)
        self.canvas.coords(self.erase_button_id, x2 - 15, y1 + 15)

        self.canvas.tag_raise(self.erase_button_id)  # Bring the erase button to the front
        self.update_all_positions()

    def toggle_electrician_box(self, event):
        self.collapsed = not self.collapsed
        if self.collapsed:
            x1, y1, x2, y2 = self.canvas.coords(self.id)
            self.canvas.coords(self.id, x1, y1, x2, y1 + JOB_HUB_HEIGHT_COLLAPSED)
        else:
            x1, y1, x2, y2 = self.canvas.coords(self.id)
            self.canvas.coords(self.id, x1, y1, x2, y1 + self.height)
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
                self.canvas.coords(circle_id, x1 + 10, y1 + 5, x1 + 10 + self.circle_radius, y1 + self.circle_radius)
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
            y_offset = y1 + index * (box_height + padding)
            if self.canvas.type(employee_id) == 'text':
                self.canvas.coords(employee_id, x1 + 35, y_offset)
            circle_id = self.app.find_circle(employee_id)
            if circle_id and self.canvas.type(circle_id) == 'oval':
                circle_radius = 10
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

        self.canvas_image = CanvasImage(self.main_frame)
        self.canvas_image.grid(row=0, column=0, sticky='nswe')

        self.canvas = self.canvas_image.canvas
        self.canvas.hub_list = []

        self.employee_boxes = []

        self.unassigned_listbox = tk.Listbox(self.main_frame)
        self.unassigned_listbox.grid(row=0, column=1, sticky='nswe')
        self.unassigned_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        self.delete_employee_button = ttk.Button(self.main_frame, text="Delete Employee", command=self.delete_employee)
        self.delete_employee_button.grid(row=1, column=1, sticky='we', padx=5, pady=5)

        self.copy_employee_button = ttk.Button(self.main_frame, text="Copy Employee", command=self.copy_employee)
        self.copy_employee_button.grid(row=2, column=1, sticky='we', padx=5, pady=5)

        self.undo_button = ttk.Button(self.main_frame, text="Undo Delete", command=self.undo_delete_employee)
        self.undo_button.grid(row=3, column=1, sticky='we', padx=5, pady=5)

        self.last_deleted_employee = None

        self.scale = 1.0
        self.canvas_transform = (0, 0)
        self.scroll_x = 0
        self.scroll_y = 0
        self.saved_scroll_region = None

        self.root.bind('<Configure>', self.on_resize)
        self.root.bind('<FocusIn>', self.on_focus_in)
        self.root.bind('<FocusOut>', self.on_focus_out)

        self.create_controls()
        self.load_state()

        self.canvas.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)

        self.default_x = DEFAULT_EMPLOYEE_X
        self.default_y = DEFAULT_EMPLOYEE_Y

    def update_text_positions(self, hub, x1, y1, x2, y2):
        self.canvas.coords(hub.text_id, (x1 + x2) / 2, y1 - 10)
        self.canvas.coords(hub.erase_button_id, x2 - 15, y1 + 15)
        self.canvas.coords(hub.collapse_button_id, x1 + 15, y2 - 15)

    def redraw_canvas(self):
        print("Canvas is being redrawn")

        self.canvas.update_idletasks()

        canvas_width = self.canvas.winfo_width()
        max_columns = MAX_COLUMNS

        for i, hub in enumerate(self.canvas.hub_list):
            x = 50 + (JOB_HUB_WIDTH + 40) * (i % max_columns)
            y = 50 + (JOB_HUB_HEIGHT + VERTICAL_SPACING) * (i // max_columns)
            self.canvas.coords(hub.id, x, y, x + JOB_HUB_WIDTH, y + JOB_HUB_HEIGHT)
            hub.update_positions()
            self.update_text_positions(hub, x, y, x + JOB_HUB_WIDTH, y + JOB_HUB_HEIGHT)

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

    def apply_scale_to_elements(self):
        self.apply_scale()

    def on_focus_in(self, event):
        print(f"Focus in event: scroll_x={self.scroll_x}, scroll_y={self.scroll_y}, scale={self.scale}")
        print(f"Scroll region before focus in: {self.canvas.cget('scrollregion')}")

        self.apply_scale()

        print(f"Scroll region after focus in: {self.canvas.cget('scrollregion')}")

    def on_focus_out(self, event):
        self.scroll_x = self.canvas.xview()[0]
        self.scroll_y = self.canvas.yview()[0]
        self.saved_scroll_region = self.canvas.cget('scrollregion')

        print(f"Focus out event: scroll_x={self.scroll_x}, scroll_y={self.scroll_y}, scrollregion={self.saved_scroll_region}")

    def on_zoom(self, event):
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= scale_factor

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        self.canvas.scale("all", x, y, scale_factor, scale_factor)

        self.canvas_transform = self.canvas.canvasx(0), self.canvas.canvasy(0)
        self.scroll_x = self.canvas.xview()[0]
        self.scroll_y = self.canvas.yview()[0]

        self.apply_scale()

        self.update_scroll_region()

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
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        scrollregion = self.canvas.cget("scrollregion").split()
        if len(scrollregion) == 4:
            scrollregion_bottom = int(scrollregion[3])
        else:
            scrollregion_bottom = 1

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

        tk.Label(self.add_employee_popup, text="Phone Number:").pack()
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
        max_columns = 6

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

        print(f"Update scroll region: scrollregion={self.canvas.cget('scrollregion')}")

    def on_resize(self, event):
        self.saved_scroll_region = self.canvas.cget('scrollregion')

        self.redraw_canvas()
        self.apply_scale()

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
                "scroll_y": self.canvas.yview()[0],
                "scroll_region": self.canvas.cget('scrollregion')
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

                for job in state["job_sites"]:
                    job["status"].setdefault("Electrician", [])
                    hub = self.add_job_site_hub(job["name"], job["x"], job["y"], job.get("status",
                                                                                         {"PM": False, "GM": False,
                                                                                          "Foreman": False,
                                                                                          "Electrician": []}))
                    job_site_dict[job["name"]] = hub

                for emp in state["employees"]:
                    job_site = emp.get("job_site")
                    box_type = emp.get("box")
                    x = emp.get("x", None)
                    y = emp.get("y", None)
                    phone = emp.get("phone", "")

                    if x is None or y is None:
                        x = self.default_x
                        y = self.default_y + len(self.employee_boxes) * 30

                    self.add_employee(emp["name"], emp.get("role"), phone, x, y, job_site, box_type)

                self.scale = state.get("scale", 1.0)
                self.canvas_transform = state.get("canvas_transform", (0, 0))
                self.scroll_x = state.get("scroll_x", 0)
                self.scroll_y = state.get("scroll_y", 0)
                self.saved_scroll_region = state.get("scroll_region", None)

                self.apply_scale()

                if self.saved_scroll_region:
                    self.canvas.config(scrollregion=self.saved_scroll_region)
                self.canvas.xview_moveto(self.scroll_x)
                self.canvas.yview_moveto(self.scroll_y)

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
