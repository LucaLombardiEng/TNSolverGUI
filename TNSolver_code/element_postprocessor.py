import scipy.constants  # For the Stefan-Boltzmann constant


def elpost_advection(el, Tel):
    """
    Calculates heat transfer and updates element properties.

    Args:
        el: A dictionary or object representing the element, containing
            'mdot' (mass flow rate), 'cp' (specific heat), and 'A' (area).
        Tel: A list or tuple representing the inlet and outlet temperatures [T_in, T_out].

    Returns:
        A tuple containing the updated element (el) and the heat transfer rate (Q).
    """

    mdot = el.mdot  # Accessing dictionary elements
    cp = el.cp

    Q = (cp * mdot) * (Tel[0] - Tel[1])  # Python indexing starts at 0
    el.Q = Q  # Updating the dictionary

    el.U = cp * mdot / el.A

    return el, Q


def elpost_radiation(el, Tel):
    """
    Calculates radiative heat transfer and updates element properties.

    Args:
        el: A dictionary or object representing the element, containing
            'sF' (shape factor) and 'A' (area).
        Tel: A list or tuple representing the temperatures [T_i, T_j].

    Returns:
        A tuple containing the updated element (el) and the heat transfer rate (Q).
    """

    sigma = scipy.constants.sigma  # Stefan-Boltzmann constant
    sF = el.sF  # Accessing dictionary elements
    Area = el.A
    Ti = Tel[0]  # Python indexing starts at 0
    Tj = Tel[1]

    Q = (sigma * sF * Area) * (Ti**4 - Tj**4)
    el.Q = Q  # Updating the dictionary

    el.hr = (sigma * sF) * (Ti + Tj) * (Ti**2 + Tj**2)
    el.U = el.hr

    return el, Q


def elpost_convection(el, Tel):
    """
    Calculates convective heat transfer and updates element properties.

    Args:
        el: A dictionary or object representing the element, containing
            'h' (convective heat transfer coefficient) and 'A' (area).
        Tel: A list or tuple representing the temperatures [T_in, T_out].

    Returns:
        A tuple containing the updated element (el) and the heat transfer rate (Q).
    """

    h = el.htc
    Area = el.A

    Q = (h * Area) * (Tel[0] - Tel[1])  # Python indexing starts at 0
    el.Q = Q  # Updating the dictionary

    el.U = h

    return el, Q


def elpost_conduction(el, Tel):
    """
    Calculates conductive heat transfer and updates element properties.

    Args:
        el: A dictionary or object representing the element, containing
            'k' (thermal conductivity), 'L' (length), and 'A' (area).
        Tel: A list or tuple representing the temperatures [T_in, T_out].

    Returns:
        A tuple containing the updated element (el) and the heat transfer rate (Q).
    """

    k = el.k  # Accessing dictionary elements
    L = el.L
    Area = el.A

    Q = ((k * Area) / L) * (Tel[0] - Tel[1])  # Python indexing starts at 0
    el.Q = Q  # Updating the dictionary

    el.U = k / L

    return el, Q

