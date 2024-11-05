# main.py
import tkinter as tk
from tkinter import messagebox
import os


def select_file():
    """Automatically set the file path to 'output.json' in the parent directory."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output.json')

    # Check if the file exists
    if not os.path.isfile(file_path):
        messagebox.showerror("Error", "output.json not found in the parent directory. The application will close.")
        exit()  # Exit the program if the file is not found

    return file_path


if __name__ == "__main__":
    # Automatically set mode to 'online' and use the default file path
    selected_mode = 'online'
    shared_file_path = select_file()

    # Import the appropriate WhiteboardApp based on the mode (fixed to 'online')
    from whiteboard_online import WhiteboardApp

    # Initialize the main application window and run the WhiteboardApp
    root = tk.Tk()
    app = WhiteboardApp(root, shared_file_path)  # Pass the auto-selected file path here
    root.mainloop()
