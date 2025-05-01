from .evaluate_properties import fluidprop, betaprop
from .utility_functions import user_feedback
import numpy as np


def EFCcyl(mat, V, D, Tf, logfID, prog_report, *text_widget):
    """
    External forced convection over a cylinder.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        V: Fluid velocity.
        D: Cylinder diameter.
        Tf: Film temperature for fluid properties.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Re: Reynolds number.
        Nu: Nusselt number.
    """

    if D <= 0.0:
        raise ValueError(f'EFCcyl: Invalid cylinder diameter = {D}')

    # Evaluate the fluid properties
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    # Reynolds number
    Re = (rho * V * D) / mu

    if Re <= 0.4:
        C = 0.989
        m = 0.330
        message = '\nWARNING: EFCcyl - Re number = {}, is out of range: 0.4 - 400,000'.format(Re)
        user_feedback(message, prog_report, logfID, *text_widget)
    elif 0.4 < Re <= 4.0:
        C = 0.989
        m = 0.330
    elif 4.0 < Re <= 40.0:
        C = 0.911
        m = 0.385
    elif 40.0 < Re <= 4000.0:
        C = 0.683
        m = 0.466
    elif 4000.0 < Re <= 40000.0:
        C = 0.193
        m = 0.618
    elif 40000.0 < Re <= 400000.0:
        C = 0.027
        m = 0.805
    else:
        C = 0.027
        m = 0.805
        message = '\nWARNING: EFCcyl - Re number = {}, is out of range: 0.4 - 400,000'.format(Re)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the heat transfer coefficient
    Nu = C * Re ** m * Pr ** (1.0 / 3.0)
    h = (Nu * k) / D

    return h, Re, Nu


def EFCsphere(mat, V, D, Ts, Tf, logfID, prog_report, *text_widget):
    """
    External forced convection over a sphere.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        V: Fluid velocity.
        D: Sphere diameter.
        Ts: Surface temperature for fluid properties.
        Tf: Fluid temperature for fluid properties.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Re: Reynolds number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    k_s, rho_s, cp_s, mu_s, Pr_s = fluidprop(mat, Ts)  # Properties at surface temperature
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)      # Properties at fluid temperature

    # Reynolds number
    Re = (rho * V * D) / mu

    if not (3.5 <= Re <= 7.6e4):
        message = '\nWARNING: EFCsphere - Re number = {}, is out of range: 3.5 - 7.6E4'.format(Re)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the heat transfer coefficient
    Nu = 2.0 + (0.4 * Re**(1/2) + 0.06 * Re**(2/3)) * Pr**0.4 * (mu / mu_s)**0.25  # Corrected exponent

    h = (Nu * k) / D

    return h, Re, Nu


def EFCdiamond(mat, V, D, Tf, logfID, prog_report, *text_widget):
    """
    External forced convection over a diamond (rotated square).

    Args:
        mat: Material properties (dictionary or object with fluid data).
        V: Fluid velocity.
        D: Cylinder diameter.
        Tf: Film temperature for fluid properties.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Re: Reynolds number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    # Reynolds number
    Re = (rho * V * D) / mu

    # Select correlation coefficients (Pythonic if/elif/else)
    if 6000.0 < Re < 60000.0:
        C = 0.304
        m = 0.59
    else:
        C = 0.304
        m = 0.59
        message = '\nWARNING: EFCdiamond - Re number = {}, is out of range: 6,000 - 60,000'.format(Re)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the heat transfer coefficient
    Nu = C * Re**m * Pr**(1.0 / 3.0)
    h = (Nu * k) / D

    return h, Re, Nu


def EFCimpjet(mat, V, D, H, r, Tf, logfID, prog_report, *text_widget):
    """
    External forced convection - impinging single round jet.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        V: Mean fluid velocity.
        D: Jet diameter.
        H: Distance from jet to surface.
        r: Surface area radius.
        Tf: Film temperature for fluid properties.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Re: Reynolds number.
        Nu: Nusselt number.
    """

    if not (2.0 <= H / D <= 12.0):
        message = '\nWARNING: EFCimpjet - H/D = {}, is out of range: 2 - 12'.format(H/D)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the fluid properties
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

    # Reynolds number
    Re = (rho * V * D) / mu
    if not (2000.0 <= Re <= 400000.0):
        message = '\nWARNING: EFCimpjet - Re number = {}, is out of range: 2,000 - 400,000'.format(Re)
        user_feedback(message, prog_report, logfID, *text_widget)

    Ar = D**2 / (4.0 * r**2)
    if not (0.004 <= Ar <= 0.04):
        message = '\nWARNING: EFCimpjet - Ar = {}, is out of range: 0.004 - 0.04'.format(Ar)
        user_feedback(message, prog_report, logfID, *text_widget)

    G = 2.0 * np.sqrt(Ar) * (1.0 - 2.2 * np.sqrt(Ar)) / (1.0 + 0.2 * (H / D - 6.0) * np.sqrt(Ar))
    Nu = G * (2.0 * np.sqrt(Re) * np.sqrt(1.0 + 0.005 * Re**0.55))

    htc = (Nu * k) / D

    return htc, Re, Nu


def EFCplate(mat, V, Xbeg, Xend, Tf, logfID, prog_report, *text_widget):
    """
    External forced convection over a flat plate.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        V: Fluid velocity.
        Xbeg: Distance from leading edge of the plate.
        Xend: Distance to end of plate.
        Tf: Film temperature for fluid properties.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Re: Reynolds number.
        Nu: Nusselt number.
    """

    Recr = 5.0e5  # Transition Reynolds number

    if V > 0.0:
        # Evaluate the fluid properties
        k, rho, cp, mu, Pr = fluidprop(mat, Tf)  # Assuming fluidprop is defined elsewhere

        if Xbeg > 0.0:
            Reb = (rho * V * Xbeg) / mu
            Re = (rho * V * Xend) / mu
            Xcr = Recr * (mu / (rho * V))

            if Xend <= Xcr:  # Laminar flow
                Nu = 0.664 * (Re**(1/2) - Reb**(1/2)) * Pr**(1/3)
                h = (k * Nu) / (Xend - Xbeg)
            elif Xbeg <= Xcr:  # Mixed laminar and turbulent
                Nu = (0.664 * (Recr**(1/2) - Reb**(1/2)) + 0.037 * (Re**(4/5) - Recr**(4/5))) * Pr**(1/3)
                h = (k * Nu) / (Xend - Xbeg)
            else:  # All turbulent
                Nu = 0.037 * (Re**(4/5) - Reb**(4/5)) * Pr**(1/3)
                h = (k * Nu) / (Xend - Xbeg)

        else:  # Xbeg = 0.0
            Re = (rho * V * Xend) / mu
            if Re <= Recr:  # Laminar flow
                Nu = 0.664 * Re**(1/2) * Pr**(1/3)
            else:  # Turbulent flow
                Nu = (0.037 * Re**(4/5) - 871.3) * Pr**(1/3)
            h = (k * Nu) / Xend

    else:  # No flow velocity, V = 0
        Re = 0.0
        Nu = 0.0
        h = 0.0

    return h, Re, Nu
