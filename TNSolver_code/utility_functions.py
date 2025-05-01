import numpy as np
import scipy.sparse as sparse
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d


def verdate():
    """Returns the version and date string."""
    ver = " Version 0.1.0, march, 2025"
    return ver


def setunits(name):
    """
    Populates a dictionary of unit strings and conversion factors.

    Args:
        name: String for system of units: 'SI' or 'US'.

    Returns:
        A tuple containing two dictionaries: units and conv.
    """

    units = {}
    conv = {}

    if name == 'SI':
        units['time'] = 's'
        units['L'] = 'm'
        units['A'] = 'm^2'
        units['V'] = 'm^3'
        units['k'] = 'W/m-K'
        units['rho'] = 'kg/m^3'
        units['cp'] = 'J/kg-K'
        units['visc'] = 'Pa-s'
        units['h'] = 'W/m^2-K'
        units['eps'] = 'dimensionless'
        units['F'] = 'dimensionless'
        units['sF'] = 'dimensionless'
        units['sigma'] = 'W/m^2-K^4'
        units['Tabs'] = 'K'
        units['T'] = 'C'
        units['Q'] = 'W'
        units['q'] = 'W/m^2'
        units['qdot'] = 'W/m^3'
        units['vel'] = 'm/s'
        units['a'] = 'm/s^2'

        conv['time'] = 3600.0  # s/hr
        conv['L'] = 0.3048  # m/ft
        conv['M'] = 0.45359237  # kg/lbm
        conv['Tabs'] = 5.0 / 9.0  # K/R
        conv['heat'] = (conv['M'] * conv['L']**2) / (conv['time']**2)  # J/Btu
        conv['A'] = conv['L']**2  # m^2/ft^2
        conv['V'] = conv['L']**3  # m^3/ft^3
        conv['rho'] = (conv['M']) / (conv['L']**3)  # kg/m^3
        conv['k'] = (conv['M'] * conv['L']) / (conv['time']**3 * conv['Tabs'])  # W/m-K
        conv['h'] = (conv['M']) / (conv['time']**3 * conv['Tabs'])  # W/m^2-K

    elif name == 'US':
        units['time'] = 'hr'
        units['L'] = 'ft'
        units['A'] = 'ft^2'
        units['V'] = 'ft^3'
        units['k'] = 'Btu/hr-ft-R'
        units['rho'] = 'lbm/ft^3'
        units['cp'] = 'Btu/lbm-R'
        units['visc'] = 'lbm-ft/hr'
        units['h'] = 'Btu/hr-ft^2-R'
        units['eps'] = 'dimensionless'
        units['F'] = 'dimensionless'
        units['sF'] = 'dimensionless'
        units['sigma'] = 'Btu/hr-ft^2-R^4'
        units['Tabs'] = 'R'
        units['T'] = 'F'
        units['Q'] = 'Btu/hr'
        units['q'] = 'Btu/hr-ft^2'
        units['qdot'] = 'Btu/hr-ft^3'
        units['vel'] = 'ft/hr'
        units['a'] = 'ft/hr^2'

        conv['time'] = 1.0 / 3600.0  # hr/s
        conv['L'] = 3.280839895  # ft/m
        conv['M'] = 2.2046226218  # lbm/kg
        conv['Tabs'] = 9.0 / 5.0  # R/K
        conv['A'] = conv['L']**2  # ft^2/m^2
        conv['V'] = conv['L']**3  # ft^3/m^3
        conv['rho'] = (conv['M']) / (conv['L']**3)  # lbm/ft^3
        conv['heat'] = (conv['M'] * conv['L']**2) / (conv['time']**2)  # Btu/J
        conv['k'] = (conv['M'] * conv['L']) / (conv['time']**3 * conv['Tabs'])  # Btu/hr-ft-R
        conv['h'] = (conv['M']) / (conv['time']**3 * conv['Tabs'])  # Btu/hr-ft^2-R

    else:
        raise ValueError(f"set units: Unknown units name: {name}")

    return units, conv


def functionF(emiss, F):
    """
    Evaluates script-F transfer factors for enclosure radiation.

    Args:
        emiss: A 1D numpy array of surface emissivities.
        F: A 2D numpy array or sparse matrix of geometric view factors.

    Returns:
        A 2D numpy array or sparse matrix of script-F transfer factors.

    Reference:
        B. Gebhart, "Heat Transfer," McGraw-Hill, New York, second edition,
        1971
    """

    nsurf = len(emiss)

    if isinstance(F, sparse.spmatrix):  # Check if F is sparse
        I = sparse.eye(nsurf)
        eps = sparse.diags(emiss, 0, nsurf, nsurf)  # Sparse diagonal matrix
    else:
        I = np.eye(nsurf)
        eps = np.diag(emiss)

    rho = I - eps

    # Solve for script-F using Gebhart's formulation
    if isinstance(F, sparse.spmatrix):
        B = sparse.linalg.spsolve(I - F @ rho, F @ eps) #Sparse solve
    else:
        B = np.linalg.solve(I - F @ rho, F @ eps) #Dense Solve
    sF = eps @ B

    return sF


def QCF(A, F):
    """
    Quality control check of the view factor matrix.

    Args:
        A: A 1D numpy array of surface areas.
        F: A 2D numpy array of view factors.

    Returns:
        A tuple containing rowsum and symcheck (both 1D numpy arrays).
    """

    # Row sum property
    rowsum = np.sum(F, axis=1)  # Sum each row (axis=1)

    # Reciprocity relationship
    symcheck = np.sum(np.diag(A) @ F - (np.diag(A) @ F).T, axis=1)

    return rowsum, symcheck


def plotfunc(func):
    """Plots a function and saves it to a PDF file."""

    fig, ax = plt.subplots(figsize=(6, 4))  # Adjust figure size as needed

    if func['type'] == 0:  # Constant
        X = np.linspace(0, 1, 10)
        Y = np.full(10, func['data'])  # Use np.full for constant array
        ax.plot(X, Y)
        ax.set_title(f"Constant Function: {func['name']}")
        ax.set_xlabel("time")
        ax.set_ylabel("f(t)")

    elif func['type'] == 1:  # Piecewise linear
        X = np.linspace(func['data'][0, 0], func['data'][-1, 0], 1000)
        # Use interp1d for interpolation
        f = interp1d(func['data'][:, 0], func['data'][:, 1], kind='linear')
        Y = f(X)
        ax.plot(X, Y)
        ax.plot(func['data'][:, 0], func['data'][:, 1], 'o')  # Plot data points
        ax.set_title(f"Piecewise Linear (Table) Time Function: {func['name']}")
        ax.set_xlabel("time")
        ax.set_ylabel("f(t)")

    elif func['type'] == 2:  # Spline
        X = np.linspace(func['data'][0, 0], func['data'][-1, 0], 1000)
        f = interp1d(func['data'][:, 0], func['data'][:, 1], kind='pchip') #Use pchip for spline interpolation
        Y = f(X)
        ax.plot(X, Y)
        ax.plot(func['data'][:, 0], func['data'][:, 1], 'o')  # Plot data points
        ax.set_title(f"Spline Time Function: {func['name']}")
        ax.set_xlabel("time")
        ax.set_ylabel("f(t)")

    else:
        print(f"Warning: Unknown function type: {func['type']}")  # Handle unknown types

    fig.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.savefig(f"{func['name']}.pdf", bbox_inches='tight') # Save as PDF, bbox_inches prevents labels from being cut off
    plt.close(fig) # Close the figure to prevent it from being displayed


def user_feedback(text, code, logFileID=None, terminal=None):
    """
    Args:
        text: whatever shall be used as a feedback to the user
        code: it will manage how to provide a progress reporting to the user, options are:
            0 = no progress reports, fully silent
            1 = progress reports on the screen, file log created
            2 = progress reports on the GUI, file log created
        *terminal: optional argument used by the GUI to provide a widget for the progress reports
    """
    if code == 0:
        pass
    elif code == 1:
        print(text)
        if logFileID is not None:
            logFileID.write(text)
    elif code == 2:
        terminal.write_text(text)
        if logFileID is not None:
            logFileID.write(text)
    else:
        pass
