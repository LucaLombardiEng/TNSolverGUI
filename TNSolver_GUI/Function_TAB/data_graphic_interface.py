from tkinter import Tk, Frame, LabelFrame, Button
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np


class FunctionPlotter(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self._board = LabelFrame(self, text='User function', padx=5, pady=0)
        self._board.pack(expand=True, fill='both', pady=10)

        self.figure = Figure(figsize=(12, 6.5), dpi=125, facecolor="white", edgecolor="black")
        self.plot = self.figure.add_subplot(1, 1, 1)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self._board)
        self.canvas.get_tk_widget().pack(expand=True, fill='both', padx=10, pady=10)

        # Create the Matplotlib navigation toolbar, linking it to the canvas
        self.toolbar = NavigationToolbar2Tk(self.canvas, self._board)
        self.toolbar.update()
        # Pack the toolbar below the canvas
        self.toolbar.pack(side='bottom', fill='both', expand=0)

    def default_function(self):
        """
        Plot a line x[0, 1], y[0, 0]

        """
        x = np.linspace(0, 10, 100)
        y = np.cos(x)
        data = np.column_stack((x, y))
        self.plot_function(data)

    def plot_function(self, func, *item):
        """
        Plots a function within a tkinter frame, clearing the old plot.

        Args:
            func (np.array): The function to plot, containing the x and y values.
            *item[0]: TITLE
            *item[1]: x-axis title
            *item[2]: y-axis title
            *item[3]: x-axis range
            *item[4]: y-axis range
        """
        # Clear the old plot before drawing new data
        self.plot.clear()

        if func.ndim == 1:
            # the array is empty or not in the right shape, plotting is aborted
            self.canvas.draw()  # Redraw the canvas to show the updated figure
            return

        sorted_idx = np.argsort(func[:, 0])
        x = func[sorted_idx, 0]
        y = func[sorted_idx, 1]

        # creation of a mask to filter out the infinite
        finite_mask = np.isfinite(x) & np.isfinite(y)

        # Filter the data
        x_finite = x[finite_mask]
        y_finite = y[finite_mask]

        title = item[0] if len(item) > 0 else "Function Plot"
        x_label = item[1] if len(item) > 1 else "X-Axis"
        y_label = item[2] if len(item) > 2 else "Y-Axis"

        # Plot the data
        if len(x_finite) > 1 and len(y_finite) > 1:
            self.plot.plot(x, y, color='r', linestyle='--')
        elif len(x_finite) == 1:
            self.plot.axhline(y_finite, color='r', linestyle='--')
        elif len(y_finite) == 1:
            self.plot.axvline(x_finite, color='r', linestyle='--')
        else:
            pass

        # Then set labels, title, and grid
        self.plot.set_xlabel(x_label)
        self.plot.set_ylabel(y_label)
        self.plot.set_title(title)
        self.plot.grid(True)

        # Call tight_layout *after* all plotting and setting elements
        self.figure.tight_layout()

        self.canvas.draw()  # Redraw the canvas to show the updated figure
# -------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    win = Tk()
    win.title('Test of graphic plotting')

    plotter = FunctionPlotter(win)
    plotter.pack(padx=10, pady=10, fill='both', expand=True)
    plotter.default_function()

    win.mainloop()
