import tkinter as tk
from tkinter import ttk


# --- Tab 1: Function Selector ---
class Tab1(ttk.Frame):
    def __init__(self, parent, functions_data, update_callback):
        super().__init__(parent)
        self.functions_data = functions_data
        self.update_callback = update_callback

        label = ttk.Label(self, text="Select a function:")
        label.pack(padx=10, pady=10)

        # The Combobox will hold the names of the functions
        self.function_combobox = ttk.Combobox(self, state="readonly")
        self.function_combobox.pack(padx=10, pady=5)

        # Initial population of the Combobox
        self.update_combobox()

        # Button to execute calculations (example)
        execute_button = ttk.Button(self, text="Execute Calculation", command=self.execute_calculation)
        execute_button.pack(padx=10, pady=10)

    def update_combobox(self):
        """Called by the parent to refresh the combobox with the latest data."""
        function_names = list(self.functions_data.keys())
        self.function_combobox['values'] = function_names

        # Set a default value if there are any functions
        if function_names:
            self.function_combobox.set(function_names[0])
        else:
            self.function_combobox.set('')

    def execute_calculation(self):
        selected_function_name = self.function_combobox.get()
        if selected_function_name in self.functions_data:
            # Get the actual function data (e.g., coordinates)
            function_data = self.functions_data[selected_function_name]
            print(f"Executing calculation for: {selected_function_name}")
            print(f"Coordinates: {function_data}")
        else:
            print("No function selected or function not found.")


# --- Tab 2: Function Creator ---
class Tab2(ttk.Frame):
    def __init__(self, parent, functions_data, update_callback):
        super().__init__(parent)
        self.functions_data = functions_data
        self.update_callback = update_callback

        ttk.Label(self, text="Create a new function:").pack(pady=10)

        ttk.Label(self, text="Function Name:").pack()
        self.name_entry = ttk.Entry(self)
        self.name_entry.pack(pady=5)

        ttk.Label(self, text="Coordinates (x,y; x,y; ...):").pack()
        self.coords_entry = ttk.Entry(self)
        self.coords_entry.pack(pady=5)

        create_button = ttk.Button(self, text="Save Function", command=self.save_function)
        create_button.pack(pady=10)

    def save_function(self):
        name = self.name_entry.get().strip()
        coords_str = self.coords_entry.get().strip()

        if not name or not coords_str:
            print("Please enter a name and coordinates.")
            return

        try:
            # Parse the coordinates string into a list of tuples
            coords_list = [
                tuple(map(float, coord.split(',')))
                for coord in coords_str.split(';')
            ]

            # Save the function data to our centralized dictionary
            self.functions_data[name] = coords_list
            print(f"Function '{name}' saved successfully.")

            # --- KEY PART: Inform the parent that data has changed ---
            self.update_callback()

            # Clear entries for next input
            self.name_entry.delete(0, tk.END)
            self.coords_entry.delete(0, tk.END)

        except (ValueError, IndexError):
            print("Invalid coordinate format. Please use 'x,y; x,y'.")


# --- Main Application ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Function Manager")

        # --- 1. Centralized Data Store ---
        # This dictionary will hold all function definitions
        # Format: {'function_name': [(x1, y1), (x2, y2), ...]}
        self.functions_data = {}

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # --- 2. Create the tabs, passing the data store and update method ---
        # The update_combobox_callback will be used by Tab2 to trigger a refresh on Tab1
        self.tab1 = Tab1(self.notebook, self.functions_data, self.update_combobox_callback)
        self.tab2 = Tab2(self.notebook, self.functions_data, self.update_combobox_callback)

        self.notebook.add(self.tab1, text='Function Selector')
        self.notebook.add(self.tab2, text='Function Creator')

    # --- 3. The Central Update Method ---
    def update_combobox_callback(self):
        """
        This is the central method that Tab2 calls to trigger an update.
        It then calls the specific update method on Tab1.
        """
        self.tab1.update_combobox()


if __name__ == "__main__":
    app = App()
    app.mainloop()