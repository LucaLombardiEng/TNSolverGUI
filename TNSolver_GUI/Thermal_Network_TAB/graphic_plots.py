"""
    Class GraphicFunctions
    This class permits the plotting of the results or the convergence while running the solution.

    Luca Lombardi
    Rev 0: First Draft

    next steps:
    ...
"""

from tkinter import Tk, Frame, LabelFrame, Button
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

from TNSolver_GUI.Thermal_Network_TAB import gUtility


class FunctionPlotter(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self._board = None
        self.canvas = None  # Store the canvas reference
        self.plot = None  # store the plot reference
        self.figure = None  # store the figure reference
        self.vertical_line = None # store the vertical line
        self._board = LabelFrame(self, width=800, height=800, padx=5, pady=0)
        self._board.pack(expand=True, fill='both')

        self.naming('no data')
        self.default_function()

    def naming(self, title):
        title = title
        self._board.configure(text=title)

    def default_function(self):
        """
        Plot a line x[0, 1], y[0, 0]

        """
        x = np.linspace(0, 1, 10)
        y = np.linspace(1, 1, 10)
        f = np.column_stack((x, y))
        self.plot_function(f)

    def plot_function(self, func, *item):
        """
        Plots a function within a tkinter frame, clearing the old plot.

        Args:
            func (np.array): The function to plot, containing the x and y values.
            *item[0]: 'node' or 'elm'
            *item[1]: node or elm number
            *item[2]: time for a vertical line
        """
        x = func[:, 0]
        y = func[:, 1]

        # Create the Figure
        if self.figure is None:
            self.figure = Figure(figsize=(2.5, 2.5), dpi=125, facecolor="white", edgecolor="black")

        plt.rcParams['font.family'] = gUtility.font
        plt.rcParams['font.size'] = 7

        if item:
            if item[0] == 'node':
                y_label = 'Temperature [°C]'
                title = 'Node {} solution'.format(str(item[1]))
            elif item[0] == 'element':
                y_label = 'Power [W]'
                title = 'Element {} solution'.format(str(item[1]))
            else:
                y_label = '---'
                title = '---'
        else:
            y_label = '---'
            title = '---'

        if self.plot is None:
            self.plot = self.figure.add_subplot(1, 1, 1)
        else:
            self.plot.clear()  # clear the plot.

        self.plot.set_xlabel("Time [s]")
        self.plot.set_ylabel(y_label)
        self.plot.set_title(title)
        self.plot.grid()
        self.figure.tight_layout()
        self.plot.plot(x, y)
        # Create or update the Canvas
        if self.canvas is None:
            self.canvas = FigureCanvasTkAgg(self.figure, master=self._board)
            self.canvas.get_tk_widget().pack(expand=True, fill='both', padx=10, pady=10)
        else:
            self.canvas.draw()  # Just redraw the canvas, the figure is already updated

        # cursor = Cursor(self.plot, horizOn=True, vertOn=True, useblit=True, color='red', linewidth=0.5)
        # self.plot.mpl_connect('motion_notify_event', PrintCoordinate)

    def add_vertical_line(self, x_value):
        x_value = float(x_value)
        # Remove the old line if it exists
        if self.vertical_line:
            self.vertical_line.remove()
            self.vertical_line = None

        # Add the new line
        self.vertical_line = self.plot.axvline(x=x_value, color='red', linestyle='--')
        self.canvas.draw_idle()

# -------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    root = Tk()
    board = Frame(root)
    board.pack(expand=True, fill='both')

    plotter = FunctionPlotter(board)


    def plot_new_data():
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        data = np.column_stack((x, y))
        plotter.plot_function(data)


    def plot_another_data():
        x = np.linspace(0, 10, 100)
        y = np.cos(x)
        data = np.column_stack((x, y))
        plotter.plot_function(data)


    plot_button = Button(root, text="Plot Sin", command=plot_new_data)
    plot_button.pack()

    plot_button2 = Button(root, text="Plot Cos", command=plot_another_data)
    plot_button2.pack()

    root.mainloop()
