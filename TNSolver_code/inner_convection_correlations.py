import numpy as np
from scipy.constants import g
from .evaluate_properties import fluidprop, betaprop
from .utility_functions import user_feedback


def INCvenc(mat, W, H, T1, T2, logfID, prog_report, *text_widget):
    """
    Internal natural convection in a vertical, rectangular enclosure.

    Args:
        mat: Material properties (structure/dictionary).
        W: Width of the enclosure.
        H: Height of the enclosure.
        T1: Surface temperature one side.
        T2: Surface temperature of the other side.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        h: Heat transfer coefficient.
        Ra: Rayleigh number.
        Nu: Nusselt number.
    """

    # Evaluate the fluid properties
    Tf = (T1 + T2) / 2.0
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)
    beta = betaprop(mat, Tf)

    # Rayleigh number
    Ra = (g * rho ** 2 * cp * beta * W ** 3 * abs(T1 - T2)) / (k * mu)

    AR = H / W  # Aspect ratio

    if 1 <= AR <= 2:  # Cat78 Correlation
        RaPr = (Ra * Pr) / (0.2 + Pr)
        Nu = 0.18 * (RaPr) ** 0.29
        if Ra * Pr <= 1.0e3:
            message = '\nWARNING: INCvenc - Ra*Pr/(0.2 + Pr) = {}, is less than 10^3.'.format(RaPr)
            user_feedback(message, prog_report, logfID, *text_widget)
    elif 2 < AR <= 10:  # Cat78 Correlation
        RaPr = (Ra * Pr) / (0.2 + Pr)
        Nu = 0.22 * (RaPr ** 0.28) / (AR ** 0.25)
        if Ra <= 1.0e3 or Ra >= 1.0e10:
            message = '\nWARNING: INCvenc - Ra number = {}, is out of range for aspect ratio, H/W ={}.'.format(Ra, AR)
            user_feedback(message, prog_report, logfID, *text_widget)
    else:  # ME69 Correlation
        Nu = 0.42 * Ra ** 0.25 * Pr ** 0.012 * AR ** -0.3
        if AR > 40:
            message = '\nWARNING: INCvenc - Aspect ratio, H/W = {}, is greater than 40.'.format(AR)
            user_feedback(message, prog_report, logfID, *text_widget)
        if Ra < 1.0e4 or Ra > 1.0e7:
            message = '\nWARNING: INCvenc - Ra number = {}, is out of range for aspect ratio, H/W ={}.'.format(Ra, AR)
            user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the heat transfer coefficient
    h = (Nu * k) / W

    return h, Ra, Nu


def IFCduct(mat, V, D, Tf, logfID, prog_report, *text_widget):
    """
    Internal, fully developed, forced convection in a duct.

    Args:
        mat: Material properties (structure/dictionary).
        V: Fluid velocity.
        D: Hydraulic diameter of the duct.
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
    k, rho, cp, mu, Pr = fluidprop(mat, Tf)

    if Pr < 0.5 or Pr > 2000:
        message = '\nWARNING: IFCduct - Pr number = {}, is out of range 0.5 < Pr < 2000.'.format(Pr)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Reynolds number
    Re = (rho * V * D) / mu

    # Nusselt number correlation
    if Re <= 2300:  # Laminar flow
        Nu = 3.66
    elif 2300 < Re < 4000:  # Transition flow
        Nu_lam = 3.66
        f = (1.8 * np.log10(Re) - 1.5)**-2  # friction factor
        Nu_turb = ((f / 8) * (Re - 1000) * Pr) / (1 + 12.7 * np.sqrt(f / 8) * (Pr**(2/3) - 1))
        gamma = (Re - 2300) / (4000 - 2300)
        Nu = (1 - gamma) * Nu_lam + gamma * Nu_turb  # linear interpolate
    else:  # Turbulent flow
        f = (1.8 * np.log10(Re) - 1.5)**-2  # friction factor
        Nu = ((f / 8) * (Re - 1000) * Pr) / (1 + 12.7 * np.sqrt(f / 8) * (Pr**(2/3) - 1))

    if Re > 5.0E6:
        message = '\nWARNING: IFCduct - Re number = {}, is greater than 5.0E6.'.format(Re)
        user_feedback(message, prog_report, logfID, *text_widget)

    # Evaluate the heat transfer coefficient
    h = Nu * k / D

    return h, Re, Nu
