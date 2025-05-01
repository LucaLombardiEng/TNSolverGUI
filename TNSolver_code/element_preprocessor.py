from .evaluate_properties import kprop, rhoCpprop
from .external_flow_correlations import EFCdiamond, EFCcyl, EFCplate, EFCimpjet, EFCsphere
from .enclosure_natural_convection_correlations import (ENChcyl, ENCsphere, ENCvplate, ENChplateup, ENCiplateup,
                                                        ENChplatedown, ENCiplatedown)
from .inner_convection_correlations import INCvenc, IFCduct


def elpre_advection(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates mass flow rate and specific heat for an element based on advection.

    Args:
        el: A dictionary or object representing the element. Must contain
            'A' (area), 'vel' (velocity), and 'matID' (material ID) fields.
        mat: A list or dictionary of material properties.  `mat[el.matID]`
             should be usable with `rhoCpprop`.
        Tel: A list or array of temperatures at the element nodes.  `Tel[0]` is
            the upstream node temperature, and `Tel[1]` is the downstream node.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        el: The updated element dictionary/object with 'mdot' (mass flow rate)
            and 'cp' (specific heat) fields added.
    """

    Area = el.A
    U = el.vel
    elT = Tel[0]  # Use upwind node temperature for properties
    if U < 0.0:
        elT = Tel[1]

    rho, cp = rhoCpprop(mat[el.matID], elT)  # Assuming mat is a list/dictionary

    el.mdot = rho * U * Area
    el.cp = cp

    return el


def elpre_conduction(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates thermal conductivity (k) for an element.

    Args:
        el: A dictionary or object representing the element. Must contain
            'matID' (material ID) field.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `kprop`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are the temperatures at the two nodes.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        el: The updated element dictionary/object with the 'k' (thermal
            conductivity) field added.
    """

    if el.matID != '':  # Check if el.matID is not empty
        elT = (Tel[0] + Tel[1]) / 2.0  # Use average temperature
        el.k = kprop(mat[el.matID], elT)

    return el


def elpre_convection(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Prepares convection calculations for an element (no calculations performed here).

    Args:
        el: A dictionary or object representing the element.  It is assumed that
           any necessary information for convection calculations (e.g., surface
           area, convective heat transfer coefficient) is already present in `el`.
        mat: Material properties (not used in this function, but included for
             consistency with other element preparation functions).
        Tel: Temperatures at element nodes (not used in this function, but
             included for consistency with other element preparation functions).
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        el: The element dictionary/object (returned unchanged).
    """

    return el


def elpre_radiation(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Prepares radiation calculations for an element (no calculations performed here).

    Args:
        el: A dictionary or object representing the element. It is assumed that
           any necessary information for radiation calculations (e.g., surface
           area, emissivity) is already present in `el`.
        mat: Material properties (not used in this function, but included for
             consistency with other element preparation functions).
        Tel: Temperatures at element nodes (not used in this function, but
             included for consistency with other element preparation functions).
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        el: The element dictionary/object (returned unchanged).
    """

    return el


def elpre_EFCdiamond(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Reynolds number, and Nusselt
    number for an element assuming flow over a diamond-shaped cylinder.

    Args:
        el: A dictionary or object representing the element. Must contain
            'D' (characteristic length/diameter) and 'vel' (velocity) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `EFCdiamond`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are the temperatures at the two nodes.
        logfID: log file ID
        prog_report: progress report coding for writing the output
        *text_widget: Terminal widget used by the GUI

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Re' (Reynolds number), and 'Nu' (Nusselt
            number) fields added.
    """

    D = el.D
    U = el.vel
    elT = (Tel[0] + Tel[1]) / 2.0  # Film T

    htc, Re, Nu = EFCdiamond(mat[el.matID], U, D, elT, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Re = Re
    el.Nu = Nu

    return el


def elpre_EFCimpjet(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Reynolds number, and Nusselt
    number for an element assuming an impinging jet.

    Args:
        el: A dictionary or object representing the element. Must contain
            'D' (nozzle diameter), 'H' (nozzle-to-plate distance), 'vel' (jet
            velocity), and 'r' (radial distance from jet centerline) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `EFCimpjet`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are the temperatures at the two nodes.

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Re' (Reynolds number), and 'Nu' (Nusselt
            number) fields added.
    """

    D = el.D
    L = el.L
    U = el.vel
    r = el.r
    elT = (Tel[0] + Tel[1]) / 2.0  # Film T

    htc, Re, Nu = EFCimpjet(mat[el.matID], U, D, L, r, elT, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Re = Re
    el.Nu = Nu

    return el


def elpre_EFCplate(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Reynolds number, and Nusselt
    number for an element assuming flow over a flat plate.

    Args:
        el: A dictionary or object representing the element. Must contain
            'xbeg' (starting x-coordinate), 'xend' (ending x-coordinate), and
            'vel' (velocity) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `EFCplate`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are the temperatures at the two nodes.

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Re' (Reynolds number), and 'Nu' (Nusselt
            number) fields added.
    """

    Xbeg = el.xbeg
    Xend = el.xend
    U = el.vel
    elT = (Tel[0] + Tel[1]) / 2.0  # Film T

    htc, Re, Nu = EFCplate(mat[el.matID], U, Xbeg, Xend, elT, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Re = Re
    el.Nu = Nu

    return el


def elpre_EFCsphere(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Reynolds number, and Nusselt
    number for an element assuming flow over a sphere.

    Args:
        el: A dictionary or object representing the element. Must contain
            'D' (diameter) and 'vel' (velocity) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `EFCsphere`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are the temperatures at the two nodes.

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Re' (Reynolds number), and 'Nu' (Nusselt
            number) fields added.
    """

    D = el.D
    U = el.vel

    htc, Re, Nu = EFCsphere(mat[el.matID], U, D, Tel[0], Tel[1], logfID, prog_report, *text_widget)

    el.htc = htc
    el.Re = Re
    el.Nu = Nu

    return el


def elpre_EFCcyl(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Reynolds number, and Nusselt
    number for an element assuming flow over a cylinder.

    Args:
        el: A dictionary or object representing the element. Must contain
            'D' (diameter) and 'vel' (velocity) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `EFCcyl`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are the temperatures at the two nodes.

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Re' (Reynolds number), and 'Nu' (Nusselt
            number) fields added.
    """

    D = el.D
    U = el.vel
    elT = (Tel[0] + Tel[1]) / 2.0  # Film T

    htc, Re, Nu = EFCcyl(mat[el.matID], U, D, elT, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Re = Re
    el.Nu = Nu

    return el


def elpre_ENChcyl(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection from a horizontal cylinder.

    Args:
        el: A dictionary or object representing the element. Must contain
            'D' (diameter) field.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `ENChcyl`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the surface temperature (Ts), and `Tel[1]` is the surrounding
            fluid temperature (Tinf).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    D = el.D
    Ts = Tel[0]
    Tinf = Tel[1]

    htc , Ra, Nu = ENChcyl(mat[el.matID], D, Ts, Tinf, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_ENChplatedown(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection from a heated plate
    facing downwards.

    Args:
        el: A dictionary or object representing the element. Must contain
            'L' (characteristic length) field.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `ENChplatedown`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the surface temperature (Ts), and `Tel[1]` is the surrounding
            fluid temperature (Tinf).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    L = el.L
    Ts = Tel[0]
    Tinf = Tel[1]

    htc, Ra, Nu = ENChplatedown(mat[el.matID], L, Ts, Tinf, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_ENChplateup(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection from a heated plate
    facing upwards.

    Args:
        el: A dictionary or object representing the element. Must contain
            'L' (characteristic length) field.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `ENChplateup`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the surface temperature (Ts), and `Tel[1]` is the surrounding
            fluid temperature (Tinf).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    L = el.L
    Ts = Tel[0]
    Tinf = Tel[1]

    htc, Ra, Nu = ENChplateup(mat[el.matID], L, Ts, Tinf, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_ENCiplatedown(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection from an inclined plate
    facing downwards.

    Args:
        el: A dictionary or object representing the element. Must contain
            'H' (height), 'L' (length), and 'theta' (inclination angle in radians)
            fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `ENCiplatedown`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the surface temperature (Ts), and `Tel[1]` is the surrounding
            fluid temperature (Tinf).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    H = el.H
    L = el.L
    theta = el.theta
    Ts = Tel[0]
    Tinf = Tel[1]

    htc, Ra, Nu = ENCiplatedown(mat[el.matID], H, L, theta, Ts, Tinf, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_ENCiplateup(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection from an inclined plate
    facing upwards.

    Args:
        el: A dictionary or object representing the element. Must contain
            'H' (height), 'L' (length), and 'theta' (inclination angle in radians)
            fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `ENCiplateup`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the surface temperature (Ts), and `Tel[1]` is the surrounding
            fluid temperature (Tinf).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    H = el.H
    L = el.L
    theta = el.theta
    Ts = Tel[0]
    Tinf = Tel[1]

    htc, Ra, Nu = ENCiplateup(mat[el.matID], H, L, theta, Ts, Tinf, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_ENCsphere(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection from a sphere.

    Args:
        el: A dictionary or object representing the element. Must contain
            'D' (diameter) field.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `ENCsphere`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the surface temperature (Ts), and `Tel[1]` is the surrounding
            fluid temperature (Tinf).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    D = el.D
    Ts = Tel[0]
    Tinf = Tel[1]

    htc, Ra, Nu = ENCsphere(mat[el.matID], D, Ts, Tinf, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_ENCvplate(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection from a vertical plate.

    Args:
        el: A dictionary or object representing the element. Must contain
            'L' (characteristic length) field.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `ENCvplate`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the surface temperature (Ts), and `Tel[1]` is the surrounding
            fluid temperature (Tinf).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    L = el.L
    Ts = Tel[0]
    Tinf = Tel[1]

    htc, Ra, Nu = ENCvplate(mat[el.matID], L, Ts, Tinf, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_INCvenc(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number for an element assuming natural convection in a vertical enclosure.

    Args:
        el: A dictionary or object representing the element. Must contain
            'W' (width) and 'H' (height) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `INCvenc`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` is
            the temperature of one side (T1), and `Tel[1]` is the temperature
            of the other side (T2).

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    W = el.W
    H = el.H
    T1 = Tel[0]
    T2 = Tel[1]

    htc, Ra, Nu = INCvenc(mat[el.matID], W, H, T1, T2, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el


def elpre_IFCduct(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Reynolds number, and Nusselt
    number for an element assuming internal, fully developed, forced convection
    in a duct.

    Args:
        el: A dictionary or object representing the element. Must contain
            'D' (hydraulic diameter) and 'vel' (velocity) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be usable with `IFCduct`.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are the temperatures at the two nodes.

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Re' (Reynolds number), and 'Nu' (Nusselt
            number) fields added.
    """

    D = el.D
    U = el.vel
    elT = (Tel[0] + Tel[1]) / 2.0  # Film T

    htc, Re, Nu = IFCduct(mat[el.matID], U, D, elT, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Re = Re
    el.Nu = Nu

    return el


def elpre_FCuser(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Reynolds number, and Nusselt
    number using a user-defined function.

    Args:
        el: A dictionary or object representing the element. Must contain
            'function' (a callable function) and 'params' (parameters for
            the user-defined function) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be passed to the user-defined function.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are passed to the user-defined function.

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Re' (Reynolds number), and 'Nu' (Nusselt
            number) fields added.
    """

    # Call the user-defined function
    htc, Re, Nu = el.function(mat[el.matID], Tel[0], Tel[1], el.params, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Re = Re
    el.Nu = Nu

    return el


def elpre_NCuser(el, mat, Tel, logfID, prog_report, *text_widget):
    """
    Calculates convective heat transfer coefficient, Rayleigh number, and Nusselt
    number using a user-defined function for natural convection.

    Args:
        el: A dictionary or object representing the element. Must contain
            'function' (a callable function) and 'params' (parameters for
            the user-defined function) fields.
        mat: A list or dictionary of material properties. `mat[el.matID]`
             should be passed to the user-defined function.
        Tel: A list or array of temperatures at the element nodes. `Tel[0]` and
            `Tel[1]` are passed to the user-defined function.

    Returns:
        el: The updated element dictionary/object with 'h' (convective heat
            transfer coefficient), 'Ra' (Rayleigh number), and 'Nu' (Nusselt
            number) fields added.
    """

    htc, Ra, Nu = el.function(mat[el.matID], Tel[0], Tel[1], el.params, logfID, prog_report, *text_widget)

    el.htc = htc
    el.Ra = Ra
    el.Nu = Nu

    return el
