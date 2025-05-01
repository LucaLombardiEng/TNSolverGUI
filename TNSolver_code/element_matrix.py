import numpy as np
import scipy.constants


def elmat_conduction(el, Tel, rhs):
    """
    Assembles the element conductivity matrix and updates the residual vector.

    Args:
        el: A dictionary or object representing the element, containing
            'k' (thermal conductivity), 'L' (length), and 'A' (area).
        Tel: A list or numpy array representing the temperatures [T_1, T_2].
        rhs: A numpy array representing the global residual vector.

    Returns:
        A tuple containing the element conductivity matrix (lhs) and the updated
        global residual vector (rhs).
    """

    k = el.k  # Accessing dictionary elements
    L = el.L
    Area = el.A

    lhs = (k * Area / L) * np.array([[1.0, -1.0],
                                    [-1.0, 1.0]])  # NumPy array

    Tel = Tel.reshape(2, 1)
    rhs = rhs - np.matmul(lhs, Tel)

    return lhs, rhs


def elmat_convection(el, Tel, rhs):
    """
    Assembles the element convection matrix and updates the residual vector.

    Args:
        el: A dictionary or object representing the element, containing
            'h' (convective heat transfer coefficient) and 'A' (area).
        Tel: A list or numpy array representing the temperatures [T_1, T_2].
        rhs: A numpy array representing the global residual vector.

    Returns:
        A tuple containing the element convection matrix (lhs) and the updated
        global residual vector (rhs).
    """

    htc = el.htc
    Area = el.A

    lhs = (htc * Area) * np.array([[1.0, -1.0],
                                   [-1.0, 1.0]])  # NumPy array

    Tel = Tel.reshape(2, 1)
    rhs = rhs - np.matmul(lhs, Tel)  # @ is the matrix multiplication operator

    return lhs, rhs


def elmat_radiation(el, Tel, rhs):
    """
    Assembles the element radiation matrix and updates the residual vector.

    Args:
        el: A dictionary or object representing the element, containing
            'sF' (shape factor) and 'A' (area).
        Tel: A list or numpy array representing the temperatures [T_i, T_j].
        rhs: A numpy array representing the global residual vector.

    Returns:
        A tuple containing the element radiation matrix (lhs) and the updated
        global residual vector (rhs).
    """

    sigma = scipy.constants.sigma  # Stefan-Boltzmann constant
    sF = el.sF  # Accessing dictionary elements
    Area = el.A
    Ti = Tel[0]  # Python indexing starts at 0
    Tj = Tel[1]

    lhs = (4.0 * sigma * sF * Area) * np.array([[Ti**3, -Tj**3],
                                                [-Ti**3, Tj**3]])  # NumPy array

    rhs_temp = (3.0 * sigma * sF * Area) * np.array([[Ti**4 - Tj**4],
                                                     [-Ti**4 + Tj**4]])

    Tel = Tel.reshape(2, 1)
    rhs = rhs - np.matmul(lhs, Tel) + rhs_temp

    return lhs, rhs


def elmat_advection(el, Tel, rhs):
    """
    Assembles the element advection matrix and updates the residual vector.

    Args:
        el: A dictionary or object representing the element, containing
            'cp' (specific heat) and 'mdot' (mass flow rate).
        Tel: A list or numpy array representing the temperatures [T_1, T_2].
        rhs: A numpy array representing the global residual vector.

    Returns:
        A tuple containing the element advection matrix (lhs) and the updated
        global residual vector (rhs).
    """

    cp = el.cp  # Accessing dictionary elements
    mdot = el.mdot

    lhs = cp * np.array([[max(mdot, 0.0), min(mdot, 0.0)],
                        [-max(mdot, 0.0), -min(mdot, 0.0)]])  # NumPy array

    Tel = Tel.reshape(2, 1)
    rhs = rhs - np.matmul(lhs, Tel)

    return lhs, rhs


def elmat_outflow(el, Tel, rhs):
    """
    Assembles the element outflow matrix and updates the residual vector.

    Args:
        el: A dictionary or object representing the element, containing
            'cp' (specific heat) and 'mdot' (mass flow rate).
        Tel: A list or numpy array representing the temperatures [T_1, T_2].
        rhs: A numpy array representing the global residual vector.

    Returns:
        A tuple containing the element outflow matrix (lhs) and the updated
        global residual vector (rhs).
    """

    cp = el.cp  # Accessing dictionary elements
    mdot = el.mdot

    lhs = cp * np.array([[max(mdot, 0.0), min(mdot, 0.0)],
                        [-max(mdot, 0.0), -min(mdot, 0.0) + mdot]])  # NumPy array

    Tel = Tel.reshape(2, 1)
    rhs = rhs - np.matmul(lhs, Tel)  # @ is the matrix multiplication operator

    return lhs, rhs
