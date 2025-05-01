import numpy as np
from .evaluate_properties import fluidprop, betaprop
from .utility_functions import user_feedback

# Define g (gravity) globally or pass it as an argument
g = 9.81  # m/s^2


def ENChcyl(mat, D, Ts, Tinf, logfID, prog_report, *text_widget):
    """
    External natural convection over a horizontal cylinder.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        D: Cylinder diameter.
        Ts: Surface temperature of the cylinder.
        Tinf: Fluid temperature.

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    Tf = (Ts + Tinf) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    beta = betaprop(mat, Tinf)  # Assuming betaprop is defined elsewhere

    # Rayleigh number
    Ra = (g * rho**2 * cp * beta * D**3 * abs(Ts - Tinf)) / (k * mu)

    if Ra > 1.0e12:
        message = '\nWARNING: ENChcyl - Ra number = {}, is out of range: 0 - 1.0e12'.format(Ra)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the heat transfer coefficient
    Nu = (0.60 + (0.387 * Ra**(1.0/6.0)) / (1.0 + (0.559 / Pr)**(9.0/16.0))**(8.0/27.0))
    h = (Nu * k) / D

    return h, Ra, Nu


def ENChplateup(mat, L, Ts, Tinf, logfID, prog_report, *text_widget):
    """
    External natural convection over the upper surface of a horizontal
    plate (hot if Ts > Tinf and cold if Ts < Tinf).

    Args:
        mat: Material properties (dictionary or object with fluid data).
        L: Characteristic length.
        Ts: Surface temperature of the plate.
        Tinf: Fluid temperature.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    Tf = (Ts + Tinf) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    if Pr < 0.7:
        message = '\nWARNING: ENChplateup - Pr number = {}, is below 0.7'.format(Pr)
        user_feedback(message, prog_report, logfID, *text_widget)

    beta = betaprop(mat, Tinf)  # Assuming betaprop is defined elsewhere

    # Rayleigh number
    Ra = (g * rho**2 * cp * beta * L**3 * abs(Ts - Tinf)) / (k * mu)

    if Ts >= Tinf:  # Hot plate facing up
        if not (1.0e4 <= Ra <= 1.0e11):
            message = '\nWARNING: ENChplateup - Ra number = {}, is out of range: 1.0E4 - 1.0e11.'.format(Ra)
            user_feedback(message, prog_report, logfID, *text_widget)

        if Ra < 1.0e7:
            Nu = 0.54 * Ra**(1/4)
        else:
            Nu = 0.15 * Ra**(1/3)

    else:  # Cold plate facing up
        if not (1.0e4 <= Ra <= 1.0e9):
            message = '\nWARNING: ENChplateup - Ra number = {}, is out of range: 1.0E4 - 1.0e9.'.format(Ra)
            user_feedback(message, prog_report, logfID, *text_widget)

        Nu = 0.52 * Ra**(1/5)

    # Evaluate the heat transfer coefficient
    h = (Nu * k) / L

    return h, Ra, Nu


def ENChplatedown(mat, L, Ts, Tinf, logfID, prog_report, *text_widget):
    """
    External natural convection over the lower surface of a horizontal
    plate (hot if Ts > Tinf and cold if Ts < Tinf).

    Args:
        mat: Material properties (dictionary or object with fluid data).
        L: Characteristic length.
        Ts: Surface temperature of the plate.
        Tinf: Fluid temperature.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    if L <= 0.0:
        raise ValueError(f'ENChplatedown: Invalid characteristic length = {L}')

    # Evaluate the fluid properties
    Tf = (Ts + Tinf) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    if Pr < 0.7:
        message = '\nWARNING: ENChplatedown - Pr number = {}, is below 0.7.'.format(Pr)
        user_feedback(message, prog_report, logfID, *text_widget)

    beta = betaprop(mat, Tinf)  # Assuming betaprop is defined elsewhere

    # Rayleigh number
    Ra = (g * rho**2 * cp * beta * L**3 * abs(Ts - Tinf)) / (k * mu)

    if Ts <= Tinf:  # Cold plate facing down
        if not (1.0e4 <= Ra <= 1.0e11):
            message = '\nWARNING: ENChplatedown - Ra number = {}, is out of range: 1.0E4 - 1.0e11.'.format(Ra)
            user_feedback(message, prog_report, logfID, *text_widget)

        if Ra < 1.0e7:
            Nu = 0.54 * Ra**(1/4)
        else:
            Nu = 0.15 * Ra**(1/3)

    else:  # Hot plate facing down
        if not (1.0e4 <= Ra <= 1.0e9):
            message = '\nWARNING: ENChplatedown - Ra number = {}, is out of range: 1.0E4 - 1.0e9.'.format(Ra)
            user_feedback(message, prog_report, logfID, *text_widget)

        Nu = 0.52 * Ra**(1/5)

    # Evaluate the heat transfer coefficient
    h = (Nu * k) / L

    return h, Ra, Nu


def ENCiplatedown(mat, H, L, theta, Ts, Tinf, logfID, prog_report, *text_widget):
    """
    External natural convection from the lower surface of an inclined
    plate (hot if Ts > Tinf and cold if Ts < Tinf).

    Args:
        mat: Material properties (dictionary or object with fluid data).
        H: Vertical height length.
        L: Characteristic length.
        theta: Angle from vertical (degrees).
        Ts: Surface temperature of the plate.
        Tinf: Fluid temperature.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    Tf = (Ts + Tinf) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    beta = betaprop(mat, Tinf)  # Assuming betaprop is defined elsewhere

    # --- Unstable - cold plate facing down ---
    if Ts < Tinf:
        # Raithby and Hollands approach

        # Rayleigh number - vertical plate
        Rav = (g * np.cos(np.radians(theta)) * rho**2 * cp * beta * H**3 * abs(Ts - Tinf)) / (k * mu)

        if Rav < 1.0e9:
            Nuv = 0.68 + (0.670 * Rav**(1/4)) / (1 + (0.492 / Pr)**(9/16))**(4/9)
        else:
            Nuv = (0.825 + (0.387 * Rav**(1/6)) / (1 + (0.492 / Pr)**(9/16))**(8/27))**2

        # Heat transfer coefficient - vertical
        hv = (Nuv * k) / H

        # Rayleigh number - horizontal plate
        Rah = (g * np.cos(np.radians(90 - theta)) * rho**2 * cp * beta * L**3 * abs(Ts - Tinf)) / (k * mu)

        if not (1.0e4 <= Rah <= 1.0e11):
            message = '\nWARNING: ENCiplatedown - Ra_h number = {}, is out of range: 1.0E4 - 1.0e11.'.format(Rah)
            user_feedback(message, prog_report, logfID, *text_widget)

        if Rah < 1.0e7:
            Nuh = 0.54 * Rah**(1/4)
        else:
            Nuh = 0.15 * Rah**(1/3)

        # Heat transfer coefficient - horizontal
        hh = (Nuh * k) / L

        # Use the maximum
        if hv > hh:
            h = hv
            Ra = Rav
            Nu = Nuv
        else:
            h = hh
            Ra = Rah
            Nu = Nuh

    # --- Stable - hot plate facing down ---
    else:  # Ts > Tinf
        # Rayleigh number
        Ra = (g * np.cos(np.radians(theta)) * rho**2 * cp * beta * H**3 * abs(Ts - Tinf)) / (k * mu)

        if Ra < 1.0e9:
            Nu = 0.68 + (0.670 * Ra**(1/4)) / (1 + (0.492 / Pr)**(9/16))**(4/9)
        else:
            Nu = (0.825 + (0.387 * Ra**(1/6)) / (1 + (0.492 / Pr)**(9/16))**(8/27))**2

        # Heat transfer coefficient
        h = (Nu * k) / H

    return h, Ra, Nu


def ENCiplateup(mat, H, L, theta, Ts, Tinf, logfID, prog_report, *text_widget):
    """
    External natural convection from the upper surface of an inclined
    plate (hot if Ts > Tinf and cold if Ts < Tinf).

    Args:
        mat: Material properties (dictionary or object with fluid data).
        H: Vertical height length.
        L: Characteristic length.
        theta: Angle from vertical (degrees).
        Ts: Surface temperature of the plate.
        Tinf: Fluid temperature.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    Tf = (Ts + Tinf) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    beta = betaprop(mat, Tinf)  # Assuming betaprop is defined elsewhere

    # --- Stable - cold plate facing up ---
    if Ts < Tinf:
        # Rayleigh number
        Ra = (g * np.cos(np.radians(theta)) * rho**2 * cp * beta * H**3 * abs(Ts - Tinf)) / (k * mu)

        if Ra < 1.0e9:
            Nu = 0.68 + (0.670 * Ra**(1/4)) / (1 + (0.492 / Pr)**(9/16))**(4/9)
        else:
            Nu = (0.825 + (0.387 * Ra**(1/6)) / (1 + (0.492 / Pr)**(9/16))**(8/27))**2

        # Heat transfer coefficient
        h = (Nu * k) / H

    # --- Unstable - hot plate facing up ---
    else:  # Ts > Tinf
        # Raithby and Hollands approach

        # Rayleigh number - vertical plate
        Rav = (g * np.cos(np.radians(theta)) * rho**2 * cp * beta * H**3 * abs(Ts - Tinf)) / (k * mu)

        if Rav < 1.0e9:
            Nuv = 0.68 + (0.670 * Rav**(1/4)) / (1 + (0.492 / Pr)**(9/16))**(4/9)
        else:
            Nuv = (0.825 + (0.387 * Rav**(1/6)) / (1 + (0.492 / Pr)**(9/16))**(8/27))**2

        # Heat transfer coefficient - vertical
        hv = (Nuv * k) / H

        # Rayleigh number - horizontal plate
        Rah = (g * np.cos(np.radians(90 - theta)) * rho**2 * cp * beta * L**3 * abs(Ts - Tinf)) / (k * mu)

        if not (1.0e4 <= Rah <= 1.0e11):
            message = '\nWARNING: ENCiplateup - Ra_h number = {}, is out of range: 1.0E4 - 1.0e11.'.format(Rah)
            user_feedback(message, prog_report, logfID, *text_widget)

        if Rah < 1.0e7:
            Nuh = 0.54 * Rah**(1/4)
        else:
            Nuh = 0.15 * Rah**(1/3)

        # Heat transfer coefficient - horizontal
        hh = (Nuh * k) / L

        # Use the maximum
        if hv > hh:
            h = hv
            Ra = Rav
            Nu = Nuv
        else:
            h = hh
            Ra = Rah
            Nu = Nuh

    return h, Ra, Nu


def ENCvplate(mat, L, Ts, Tinf, logfID, prog_report, *text_widget):
    """
    External natural convection from a vertical plate.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        L: Characteristic length (height of the plate).
        Ts: Surface temperature of the plate.
        Tinf: Fluid temperature.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    Tf = (Ts + Tinf) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    beta = betaprop(mat, Tinf)  # Assuming betaprop is defined elsewhere

    # Rayleigh number
    Ra = (g * rho**2 * cp * beta * L**3 * abs(Ts - Tinf)) / (k * mu)

    if Ra < 1.0e9:
        Nu = 0.68 + (0.670 * Ra**(1/4)) / (1 + (0.492 / Pr)**(9/16))**(4/9)
    else:
        Nu = (0.825 + (0.387 * Ra**(1/6)) / (1 + (0.492 / Pr)**(9/16))**(8/27))**2

    # Evaluate the heat transfer coefficient
    h = (Nu * k) / L

    return h, Ra, Nu


def ENCsphere(mat, D, Ts, Tinf, logfID, prog_report, *text_widget):
    """
    External natural convection from a sphere.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        D: Characteristic length (diameter of the sphere).
        Ts: Surface temperature of the sphere.
        Tinf: Fluid temperature.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    Tf = (Ts + Tinf) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    beta = betaprop(mat, Tinf)  # Assuming betaprop is defined elsewhere

    # Rayleigh number
    Ra = (g * rho**2 * cp * beta * D**3 * abs(Ts - Tinf)) / (k * mu)

    Nu = 2.0 + (0.589 * Ra**(1/4)) / ((1.0 + (0.469 / Pr)**(9/16))**(4/9))

    if Ra > 1.0e11:
        message = '\nWARNING: ENCsphere - Ra number = {}, is out of range: 0.0 - 1.0e11.'.format(Ra)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the heat transfer coefficient
    h = (Nu * k) / D

    return h, Ra, Nu
