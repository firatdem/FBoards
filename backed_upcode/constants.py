# constants.py
ROLE_COLORS = {
    "PM": "#800080",  # Dark purple
    "GM": "green",
    "Foreman": "blue",
    "Electrician": "yellow",
    "Fire Alarm": "red"  # New role, using the original red color
}

VERTICAL_SPACING = 150  # Constant vertical spacing between rows
ELECTRICIAN_BOX_HEIGHT = 550  # Height of the electrician box
JOB_HUB_WIDTH = 400  # Width of the job site hub
JOB_HUB_HEIGHT = 800  # Height of the job site hub
BOX_HEIGHT = 60  # Height of the non-electrician boxes
DEFAULT_EMPLOYEE_X = 1200  # Where non-assigned employees get placed
DEFAULT_EMPLOYEE_Y = -500
GRID_SIZE = 30
DRAG_DELAY = 250  # Delay in milliseconds
JOB_HUB_HEIGHT_COLLAPSED = 250
MAX_COLUMNS = 8  # Maximum number of columns for job site hubs
