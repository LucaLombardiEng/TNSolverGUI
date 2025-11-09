import re
import numpy as np
from .utility_functions import user_feedback
from .material_library import Material, matlib
from .element_matrix import elmat_radiation, elmat_outflow, elmat_conduction, elmat_convection, elmat_advection
from .element_postprocessor import elpost_radiation, elpost_convection, elpost_advection, elpost_conduction
from .element_preprocessor import (elpre_radiation, elpre_FCuser, elpre_NCuser, elpre_IFCduct, elpre_INCvenc,
                                   elpre_convection, elpre_advection, elpre_EFCcyl, elpre_conduction, elpre_EFCplate,
                                   elpre_EFCimpjet, elpre_EFCdiamond, elpre_ENChplateup, elpre_ENCiplateup,
                                   elpre_EFCsphere, elpre_ENCsphere, elpre_ENChplatedown, elpre_ENCiplatedown,
                                   elpre_ENChcyl, elpre_ENCvplate)


class SolutionParameters:
    def __init__(self):
        self.title = ''
        self.type = "steady"
        self.units = "SI"
        self.Temp_units = "C"
        self.convergence_residual = 1.0e-9
        self.max_iter_number = 100
        self.begin_time = 0.0
        self.end_time = float('nan')
        self.time_step = float('nan')
        self.time = float('nan')
        self.number_time_steps = int
        self.sigma = 5.670373E-8
        self.gravity = 9.80665
        self.print_interval = 1
        self.screen_print_interval = 1
        self.graphviz = 0
        self.plot_function = 0
        self.max_change = 0.5
        self.steady = True
        self.Toff = 273.15
        self.nDBC = 0
        self.Dirichlet = []
        self.nNBC = 0
        self.Neumann = []


class Node:
    def __init__(self):
        self.label = ""  # String - node label
        self.mat = ""  # String - material name
        self.vol = 0.0  # Float - volume
        self.strvol = ""  # String - volume function name
        self.T = 0.0  # Float - temperature
        self.Told = 0.0  # Float - previous time step temperature
        self.matID = None  # Integer - material library ID
        self.mfncID = None  # Integer - heat capacity function ID
        self.vfncID = None  # Integer - volume function ID
        self.rhocv = 0.0  # Float - volumetric heat capacity


class Element:
    def __init__(self):
        self.label = ""  # string - element label
        self.type = ""  # string - type of element
        self.nd1 = ""  # string - node i label
        self.nd2 = ""  # string - node j label
        self.mat = ""  # string - material name
        self.A = 0.0  # double - area
        self.k = 0.0  # double - thermal conductivity
        self.L = 0.0  # double - length
        self.H = 0.0  # double - Height
        self.theta = 0.0  # double - angle
        self.ri = 0.0  # double - inner radius
        self.ro = 0.0  # double - outer radius
        self.cylL = 0.0  # double - cylinder length
        self.htc = 0.0  # double - convection coefficient
        self.xbeg = 0.0  # double - begin x coordinate
        self.xend = 0.0  # double - end x coordinate
        self.sF = 0.0  # double - script-F exchange factor
        self.vel = 0.0  # double - fluid flow velocity
        self.mdot = 0.0  # double - mass flow rate
        self.cp = 0.0  # double - specific heat
        self.elnd = [0, 0]  # (2,1) - element internal nodes (initialized as a list)
        self.elst = 0  # int - element type ID
        self.elmat = None  # function - element matrix function (initialized as None)
        self.elpre = None  # function - element pre function (initialized as None)
        self.elpost = None  # function - element post function (initialized as None)
        self.matID = ''  # int - material library ID
        self.Q = 0.0  # double - Q_ij heat flow rate
        self.U = 0.0  # double - thermal conductance
        self.Nu = 0.0  # double - Nusselt number
        self.Re = 0.0  # double - Reynolds number
        self.Ra = 0.0  # double - Rayleigh number
        self.hr = 0.0  # double - radiation h


class BoundaryCondition:
    def __init__(self):
        self.type = ""  # string - type of BC
        self.Tinf = None  # double - BC temperature
        self.q = None  # double - heat flux
        self.A = None  # double - area
        self.strTinf = ""  # string - BC temperature function
        self.strq = ""  # string - heat flux function
        self.strA = ""  # string - area function
        self.fncTinf = None  # int - BC temperature function ID
        self.fncq = None  # int - heat flux function ID
        self.fncA = None  # int - area function ID
        self.nds = []  # list - node labels to apply BC to
        self.nd = []  # list - internal node numbers


class Source:
    def __init__(self):
        self.type = ""  # string - type of source
        self.ntype = 0  # int - type ID
        self.qdot = 0.0  # double - source
        self.strqdot = ""  # string - heat source function
        self.fncqdot = None  # function - heat source function (initially None)
        self.Q = 0.0  # double - total source
        self.strQ = ""  # string - total source function
        self.fncQ = None  # function - total source function (initially None)
        self.tstat = ""  # string - node label for thermostat
        self.Ton = 0.0  # double - thermostat on T
        self.Toff = 0.0  # double - thermostat off T
        self.nds = []  # list - node labels to apply source to
        self.nd = []  # list - internal node numbers
        self.tnd = 0  # int - thermostat internal node number
        self.Sc = [0, ]  # double - S = Sp*T + Sc
        self.Qtot = 0.0  # double - total node source for output


class InitialCondition:
    def __init__(self):
        self.Tinit = 0.0  # double - initial temperature
        self.nds = []  # list - node labels to apply IC to
        self.nd = []  # list - internal node numbers


class Enclosure:
    def __init__(self):
        self.nsurf = 0  # number of surfaces in this enclosure
        self.label = []  # surface label
        self.emiss = []  # surface emissivity
        self.A = []  # surface area
        self.F = []  # view factors (Consider making this a list or dictionary if you have multiple view factors)
        self.eln = []  # list - element numbers of radiation conductors


class Function:
    def __init__(self):
        self.name = ""  # string - function name
        self.indvar = ""  # string - independent variable
        self.type = 0  # int - <0|1|2|3> type of function
        self.data = []  # list or numpy array - function data
        self.range = []  # list or numpy array - function range


def is_float(value):
    """Checks if a string can be converted to a float."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_integer(value):
    """Checks if a string can be converted to a float."""
    try:
        int(value)
        return True
    except ValueError:
        return False


def nextline(lines, l_num):
    """
    Fetches the next non-comment, non-blank line from the input file.

    Args:
        lines: List of lines of the file
        l_num: Last line number read.

    Returns:
        str_: The trimmed line from the file.
        l_num: The updated line number.
    """

    while l_num < len(lines):

        line = lines[l_num]
        str_ = re.split(r'!', line)[0]  # Split at '!' (comment character)
        str_ = str_.strip()  # Trim whitespace

        if str_:  # Check if string is not empty after trimming
            return str_, l_num  # Return the line
        else:
            l_num += 1
    return 'EOF', l_num


def parse_solution_parameters(lines, line_number, spar, inp_err, logfID, prog_report, *text_widget):
    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*solution', str_, re.IGNORECASE):
            break
        tokens = re.findall(r'\S+', str_)

        # spar = SolutionParameters()
        if tokens[0].lower() == 'type':
            spar.type = tokens[2]
            if tokens[2].lower() == 'steady':
                spar.steady = True
            else:
                spar.steady = False
        elif tokens[0].lower() == 'title':
            spar.title = ' '.join(tokens[1:])
        elif tokens[0].lower() == 'units':
            if tokens[2].upper() in ['SI', 'US']:
                spar.units = tokens[2].upper()
            else:
                message = '\nERROR: Invalid units at line {} : {}\n'.format(line_number + 1, lines[line_number])
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
        elif tokens[0] == 'T' and tokens[1] == 'units':
            if tokens[3].upper() in ['C', 'K', 'F', 'R']:
                spar.Temp_units = tokens[3]
            else:
                message = '\nERROR: Invalid Temperature units at line {} : {}\n'.format(line_number + 1,
                                                                                        lines[line_number])
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
        elif tokens[0].lower() == 'gravity':
            if is_float(tokens[2]):
                spar.gravity = float(tokens[2])
            else:
                message = ('\nERROR: Invalid gravity value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
        elif tokens[0].lower() == 'nonlinear' and tokens[1].lower() == 'convergence':
            if is_float(tokens[3]):
                spar.convergence_residual = float(tokens[3])
            else:
                message = ('\nERROR: Invalid nonlinear convergence value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'maximum' and tokens[1].lower() == 'nonlinear' and tokens[2].lower() == 'iterations':
            if is_integer(tokens[4]):
                spar.max_iter_number = int(tokens[4])
            else:
                message = ('\nERROR: Invalid maximum nonlinear iterations value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'begin' and tokens[1].lower() == 'time':
            if is_float(tokens[3]):
                spar.begin_time = float(tokens[3])
            else:
                message = ('\nERROR: Invalid begin time value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'end' and tokens[1].lower() == 'time':
            if is_float(tokens[3]):
                spar.end_time = float(tokens[3])
            else:
                message = ('\nERROR: Invalid end time value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'time' and tokens[1].lower() == 'step':
            if is_float(tokens[3]):
                spar.time_step = float(tokens[3])
            else:
                message = ('\nERROR: Invalid time step value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'print' and tokens[1].lower() == 'interval':
            if is_float(tokens[3]):
                spar.print_interval = float(tokens[3])
            else:
                message = ('\nERROR: Invalid print interval step value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'screen' and tokens[1].lower() == 'print' and tokens[2].lower() == 'interval':
            if is_float(tokens[4]):
                spar.screen_print_interval = float(tokens[4])
            else:
                message = ('\nERROR: Invalid screen print interval step value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif (tokens[0].lower() == 'number' and tokens[1].lower() == 'of' and tokens[2].lower() == 'time' and
              tokens[3].lower() == 'steps'):
            if is_float(tokens[5]):
                spar.number_time_steps = float(tokens[5])
            else:
                message = ('\nERROR: Invalid number of time steps value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'stefan-boltzmann':
            if is_float(tokens[2]):
                spar.sigma = float(tokens[2])
            else:
                message = ('\nERROR: Invalid Stefan-Boltzmann value at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        elif tokens[0].lower() == 'graphviz' and tokens[1].lower() == 'output':
            if tokens[3].lower() == 'yes':
                spar.graphviz = 1
            elif tokens[3].lower() == 'no':
                spar.graphviz = 0
            else:
                message = ('\nERROR: Invalid decision (yes/no) at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
        elif tokens[0].lower() == 'plot' and tokens[1].lower() == 'functions':
            if tokens[3].lower() == 'yes':
                spar.plot_function = 1
            elif tokens[3].lower() == 'no':
                spar.plot_function = 0
            else:
                message = ('\nERROR: Invalid decision (yes/no) at line {} : {}\n'.
                           format(line_number + 1, lines[line_number]))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
        else:
            message = ('\nERROR: Unknown command at line {} : {}\n'.
                       format(line_number + 1, lines[line_number]))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1
    return line_number, spar, inp_err


def parse_nodes(lines, line_number, nd, inp_err, logfID, prog_report, *text_widget):
    """
    Reads node definitions from the input file.

    """
    nd_number = 0
    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*nodes', str_, re.IGNORECASE):
            break

        tokens = re.findall(r'\S+', str_)
        if len(tokens) != 3:
            message = (('\nERROR: Invalid node command at line {} in the input file:\n{}'
                       '\n3 parameters are required, {} were found.').
                       format(line_number + 1, str_, len(tokens)))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1
        else:
            nd.append(Node())  # Append Node class to list of nodes
            nd[-1].label = tokens[0]
            if is_float(tokens[1]):
                nd[-1].rhocv = float(tokens[1])
            else:
                nd[-1].mat = tokens[1]
            if is_float(tokens[2]):
                nd[-1].vol = float(tokens[2])
            else:
                nd[-1].strvol = tokens[2]
            nd_number += 1
    return line_number, nd, inp_err


def parse_conductors(lines, line_number, el, inp_err, logfID, prog_report, *text_widget):
    """
    Reads conductors definitions from the input file.

    """

    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*conductors', str_, re.IGNORECASE):
            break

        # tokens = re.findall(r'[a-zA-Z_0-9+-./]*', str_)
        tokens = re.findall(r'\S+', str_)
        if len(tokens) < 4:
            message = (('\nERROR: Invalid conductor command at line {} in the input file:\n{}'
                       '\nMore than 4 parameters are required, {} were found.').
                       format(line_number + 1, str_, len(tokens)))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1
        else:
            el.append(Element())
            el[-1].label = tokens[0]
            el[-1].type = tokens[1]
            el[-1].nd1 = tokens[2]
            el[-1].nd2 = tokens[3]

            if el[-1].type == 'conduction':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[4]):
                    el[-1].k = float(tokens[4])
                else:
                    el[-1].mat = tokens[4]

                if is_float(tokens[5]):
                    el[-1].L = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid conductor length at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]):
                    el[-1].A = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid conductor area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 1
                el[-1].elmat = elmat_conduction
                el[-1].elpre = elpre_conduction
                el[-1].elpost = elpost_conduction

            elif el[-1].type == 'cylindrical':
                if len(tokens) < 8:
                    message = (('\nERROR: Invalid cylindrical conductor command at line {} in the input file:\n{}'
                                '\n8 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[4]):
                    el[-1].k = float(tokens[4])
                else:
                    el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) >= 0.0:
                    el[-1].ri = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid cylindrical conductor inner radius at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0 and float(tokens[6]) > el[-1].ri:
                    el[-1].ro = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid cylindrical conductor outer radius at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]) and float(tokens[7]) > 0.0:
                    el[-1].cylL = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid cylindrical conductor length at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                rm = (el[-1].ro - el[-1].ri) / np.log(el[-1].ro / el[-1].ri)
                el[-1].A = 2 * np.pi * el[-1].cylL * rm
                el[-1].L = el[-1].ro - el[-1].ri
                el[-1].elst = 14
                el[-1].elmat = elmat_conduction
                el[-1].elpre = elpre_conduction
                el[-1].elpost = elpost_conduction

            elif el[-1].type == 'spherical':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid spherical conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[4]):
                    el[-1].k = float(tokens[4])
                else:
                    el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) >= 0.0:
                    el[-1].ri = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid sphere conductor inner radius at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0 and float(tokens[6]) > el[-1].ri:
                    el[-1].ro = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid sphere conductor outer radius at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].A = 4 * np.pi * (el[-1].ri * el[-1].ro)
                el[-1].L = el[-1].ro - el[-1].ri
                el[-1].elst = 15
                el[-1].elmat = elmat_conduction
                el[-1].elpre = elpre_conduction
                el[-1].elpost = elpost_conduction
            # Convection section
            elif el[-1].type == 'convection':
                if len(tokens) < 6:
                    message = (('\nERROR: Invalid convection conductor command at line {} in the input file:\n{}'
                                '\n6 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[4]) and float(tokens[4]) > 0.0:
                    el[-1].htc = float(tokens[4])
                else:
                    message = ('\nERROR: Invalid convection conductor HTC at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1
                if is_float(tokens[5]):
                    el[-1].A = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid convection conductor area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 2
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_convection
                el[-1].elpost = elpost_convection
            # Internal Convection section
            elif el[-1].type == 'IFCduct':
                if len(tokens) < 8:
                    message = (('\nERROR: Invalid IFCduct conductor command at line {} in the input file:\n{}'
                                '\n8 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid IFCduct velocity at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].D = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid IFCduct diameter at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]) and float(tokens[7]) > 0.0:
                    el[-1].A = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid IFCduct area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 16
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_IFCduct
                el[-1].elpost = elpost_convection
            # External Forced Convection section
            elif el[-1].type == 'EFCimpjet':
                if len(tokens) < 9:
                    message = (('\nERROR: Invalid EFCimpjet conductor command at line {} in the input file:\n{}'
                                '\n9 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid EFCimpjet jet velocity at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].D = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid EFCimpjet jet diameter at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]) and float(tokens[7]) > 0.0:
                    el[-1].L = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid EFCimpjet jet height at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[8]) and float(tokens[8]) > 0.0:
                    el[-1].r = float(tokens[8])
                else:
                    message = ('\nERROR: Invalid EFCimpjet jet radius at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].A = np.pi * el[-1].r**2
                el[-1].elst = 20
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_EFCimpjet
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'EFCplate':
                if len(tokens) < 9:
                    message = (('\nERROR: Invalid EFCplate conductor command at line {} in the input file:\n{}'
                                '\n9 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid EFCplate velocity at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].xbeg = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid EFCplate X begin at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]) and float(tokens[7]) > el[-1].xbeg:
                    el[-1].xend = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid EFCplate X end at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[8]) and float(tokens[8]) > 0.0:
                    el[-1].A = float(tokens[8])
                else:
                    message = ('\nERROR: Invalid EFCplate area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 17
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_EFCplate
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'EFCcyl':
                if len(tokens) < 8:
                    message = (('\nERROR: Invalid EFCcyl conductor command at line {} in the input file:\n{}'
                                '\n8 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid EFCcyl velocity at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].D = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid EFCcyl diameter at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]) and float(tokens[7]) > el[-1].xbeg:
                    el[-1].A = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid EFCcyl area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 6
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_EFCcyl
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'EFCsphere':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid EFCsphere conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid EFCsphere velocity at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].D = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid EFCsphere diameter at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].A = np.pi*el[-1].D**2
                el[-1].elst = 19
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_EFCsphere
                el[-1].elpost = elpost_convection
            # Internal Forced Convection section
            elif el[-1].type == 'INCvenc':
                if len(tokens) < 8:
                    message = (('\nERROR: Invalid INCvenc conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].W = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid INCvenc width at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].H = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid INCvenc height at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]) and float(tokens[7]) > 0.0:
                    el[-1].A = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid INCvenc area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 21
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_INCvenc
                el[-1].elpost = elpost_convection
            # External Forced Convection section
            elif el[-1].type == 'EFCdiamond':
                if len(tokens) < 8:
                    message = (('\nERROR: Invalid EFCdiamond conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid EFCdiamond velocity at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].D = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid EFCdiamond diameter at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]) and float(tokens[7]) > 0.0:
                    el[-1].A = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid EFCdiamond area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 8
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_EFCdiamond
                el[-1].elpost = elpost_convection
            # External Natural Convection section
            elif el[-1].type == 'ENChcyl':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid ENChcyl conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].D = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid ENChcyl diameter at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].A = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid ENChcyl area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 7
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_ENChcyl
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'ENChplateup':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid ENChplateup conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].L = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid ENChplateup length at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].A = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid ENChplateup area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 9
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_ENChplateup
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'ENChplatedown':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid ENChplatedown conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].L = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid ENChplatedown length at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].A = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid ENChplatedown area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 10
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_ENChplatedown
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'ENCvplate':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid ENCvplate conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].L = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid ENCvplate length at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].A = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid ENCvplate area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 11
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_ENCvplate
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'ENCiplateup':
                if len(tokens) < 9:
                    message = (('\nERROR: Invalid ENCiplateup conductor command at line {} in the input file:\n{}'
                                '\n9 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].H = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid ENCiplateup height at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].L = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid ENCiplateup length at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]):
                    el[-1].theta = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid ENCiplateup angle at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[8]) and float(tokens[8]) > 0.0:
                    el[-1].A = float(tokens[8])
                else:
                    message = ('\nERROR: Invalid ENCiplateup area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 12
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_ENCiplateup
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'ENCiplatedown':
                if len(tokens) < 9:
                    message = (('\nERROR: Invalid ENCiplatedown conductor command at line {} in the input file:\n{}'
                                '\n9 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) > 0.0:
                    el[-1].H = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid ENCiplatedown height at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) > 0.0:
                    el[-1].L = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid ENCiplatedown length at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[7]):
                    el[-1].theta = float(tokens[7])
                else:
                    message = ('\nERROR: Invalid ENCiplatedown angle at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[8]) and float(tokens[8]) > 0.0:
                    el[-1].A = float(tokens[8])
                else:
                    message = ('\nERROR: Invalid ENCiplatedown area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 13
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_ENCiplatedown
                el[-1].elpost = elpost_convection

            elif el[-1].type == 'ENCsphere':
                if len(tokens) < 6:
                    message = (('\nERROR: Invalid ENCsphere conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) >= 0.0:
                    el[-1].D = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid ENCsphere diameter at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].A = np.pi * el[-1].D**2
                el[-1].elst = 18
                el[-1].elmat = elmat_convection
                el[-1].elpre = elpre_ENCsphere
                el[-1].elpost = elpost_convection
            # Radiation section
            elif el[-1].type == 'radiation':
                if len(tokens) < 6:
                    message = (('\nERROR: Invalid radiation conductor command at line {} in the input file:\n{}'
                                '\n6 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[4]) and float(tokens[4]) >= 0.0:
                    el[-1].sF = float(tokens[4])
                else:
                    message = ('\nERROR: Invalid radiation script-F at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[5]) and float(tokens[5]) >= 0.0:
                    el[-1].A = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid radiation area at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 3
                el[-1].elmat = elmat_radiation
                el[-1].elpre = elpre_radiation
                el[-1].elpost = elpost_radiation

            elif el[-1].type == 'surfrad':
                if len(tokens) < 6:
                    message = ('\nERROR: Invalid surfrad conductor command at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[4]) and 0.0 >= float(tokens[4]) > 1.0:
                    el[-1].sF = float(tokens[4])
                    el[-1].emiss = el[-1].sF
                else:
                    message = ('\nERROR: Invalid surfrad emissivity command at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[5]) and float(tokens[5]) <= 0.0:
                    el[-1].A = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid surfrad area command at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 4
                el[-1].elmat = elmat_radiation
                el[-1].elpre = elpre_radiation
                el[-1].elpost = elpost_radiation
            # Advection section
            elif el[-1].type == 'advection':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid advection conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) >= 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    print(f"Error: Invalid advection velocity at line {line_number + 1}")
                    logfID.write(f"\nERROR: Invalid advection velocity at line {line_number + 1}"
                                 f"in the input file:\n{str_}")
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) >= 0.0:
                    el[-1].A = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid advection area command at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 5
                el[-1].elmat = elmat_advection
                el[-1].elpre = elpre_advection
                el[-1].elpost = elpost_advection

            elif el[-1].type == 'outflow':
                if len(tokens) < 7:
                    message = (('\nERROR: Invalid outflow conductor command at line {} in the input file:\n{}'
                                '\n7 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].mat = tokens[4]

                if is_float(tokens[5]) and float(tokens[5]) >= 0.0:
                    el[-1].vel = float(tokens[5])
                else:
                    message = ('\nERROR: Invalid outflow velocity command at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                if is_float(tokens[6]) and float(tokens[6]) >= 0.0:
                    el[-1].A = float(tokens[6])
                else:
                    message = ('\nERROR: Invalid outflow area command at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

                el[-1].elst = 5
                el[-1].elmat = elmat_outflow
                el[-1].elpre = elpre_advection
                el[-1].elpost = elpost_advection

            else:
                message = ('\nERROR: Unknown type of conductor at line {} in the input file:\n{}'.
                           format(line_number + 1, str_))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

    return line_number, el, inp_err


def parse_boundary_conditions(lines, line_number, bc, inp_err, logfID, prog_report, *text_widget):
    """
    Reads the boundary conditions definitions from the input file.
    """

    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*boundary.*conditions', str_, re.IGNORECASE):
            break

        tokens = re.findall(r'\S+', str_, )
        n_tokens = len(tokens)
        bc.append(BoundaryCondition())  # append a new boundary condition class
        
        bc[-1].type = tokens[0]
        if bc[-1].type == 'fixed_T':
            if is_float(tokens[1]):
                bc[-1].Tinf = float(tokens[1])  # Numerical T_inf
            else:
                bc[-1].strTinf = tokens[1]  # Function name for T_inf
            for index in range(len(tokens[2:n_tokens])):
                bc[-1].nds.append(tokens[index+2])
        elif bc[-1].type == 'heat_flux':
            if is_float(tokens[1]):
                bc[-1].q = float(tokens[1])  # Numerical the heat flux
            else:
                bc[-1].strq = tokens[1]  # Function name heat flux

            if is_float(tokens[2]):
                bc[-1].A = float(tokens[2])  # Numerical the Area
            else:
                bc[-1].strA = tokens[2]  # Function name Area

            for index in range(len(tokens[3:n_tokens])):
                bc[-1].nds.append(tokens[index+3])
        else:
            message = ('\nERROR: Unknown type of boundary condition at line {} in the input file:\n{}'.
                       format(line_number + 1, str_))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1
    return line_number, bc, inp_err


def parse_initial_conditions(lines, line_number, ic, inp_err, logfID, prog_report, *text_widget):
    """Reads initial conditions definitions from the input file."""

    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*initial', str_, re.IGNORECASE):
            break

        tokens = re.findall(r'\S+', str_)
        n_tokens = len(tokens)
        if tokens[0] == 'read':
            rst_file = ' '.join(tokens[2:])
            ic, inp_err = read_restart_file(rst_file, ic, logfID)  # read restart file
        elif is_float(tokens[0]):
            ic.append(InitialCondition())
            ic[-1].Tinit = float(tokens[0])
            for index in range(len(tokens[1:n_tokens])):
                ic[-1].nds.append(tokens[index+1])
        else:
            message = ('\nERROR: Unknown initial condition  at line {} in the input file:\n{}'.
                       format(line_number + 1, str_))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1
    return line_number, ic, inp_err


def read_restart_file(file, ic, logfID, prog_report, *text_widget):
    """Reads initial conditions from the restart file."""

    try:
        rst_file = open(file, 'r')
        rst_ic = rst_file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"TNSolver: Cannot open the restart file: {file}")

    line_number = -1
    lines_tot = len(rst_ic)
    inp_err = 0

    while line_number < lines_tot-1:
        line_number += 1
        str_, line_number = nextline(rst_ic, line_number)

        if not re.search(r'time.*=', str_, re.IGNORECASE):
            tok = re.findall(r'\S+', str_)
            ic.append(InitialCondition())
            ic[-1].nds = tok[0]
            if is_float(tok[1]):
                ic[-1].Tinit = float(tok[1])
            else:
                message = ('\nERROR: Invalid Temperature at line {} in the input file:\n{}'.
                           format(line_number + 1, str_))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

    message = '\nRestart file {} ihas been read.\n{}'.format(file)
    user_feedback(message, prog_report, logfID, *text_widget)
    file.close()  # Close file when done

    return ic, inp_err


def parse_radiation_enclosure(lines, line_number, enc, inp_err, logfID, prog_report, *text_widget):
    """Reads initial conditions definitions from the input file."""

    surf_num = 0  # Surfaces counter
    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*radiation', str_, re.IGNORECASE):
            break

        tokens = re.findall(r'\S+', str_)
        n_tokens = len(tokens)
        if n_tokens < 5:
            message = (('\nERROR: Invalid radiation enclosure at line {} in the input file:\n{}'
                        '\nMore than 4 parameters are required, {} were found.').
                       format(line_number + 1, str_, len(tokens)))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1
        else:
            enc.append(Enclosure())
            if surf_num == 0:
                enc[-1].nsurf = n_tokens - 3
                surf_num += 1
            else:
                if (n_tokens-3) != enc[-1].nsurf:
                    message = '\nWARNING: Radiation enclosure surface number mismatch.\n{}'
                    user_feedback(message, prog_report, logfID, *text_widget)
                surf_num += 1

            enc[-1].label = tokens[0]

            if not float(tokens[1]) or float(tokens[1]) > 0.0 or float(tokens[1]) > 1.0:
                message = ('\nERROR: Invalid emissivity at line {} in the input file:\n{}'.
                           format(line_number + 1, str_))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
            else:
                enc[-1].emiss = tokens[1]

            if is_float(tokens[2]) and float(tokens[2]) > 0.0:
                enc[-1].A = tokens[2]
            else:
                message = ('\nERROR: Invalid area at line {} in the input file:\n{}'.
                           format(line_number + 1, str_))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

            for index in range(len(tokens[3:n_tokens])):
                if is_float(tokens[index]) and 1.0 >= float(tokens[index]) >= 0.0:
                    enc[-1].F.append(tokens[index])
                else:
                    message = ('\nERROR: Invalid view factor at line {} in the input file:\n{}'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1
    return line_number, enc, inp_err


def parse_sources(lines, line_number, src, inp_err, logfID, prog_report, *text_widget):
    """Reads source definitions from the input file."""

    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*sources', str_, re.IGNORECASE):
            break

        tokens = re.findall(r'\S+', str_)
        n_tokens = len(tokens)
        if n_tokens < 3:
            message = (('\nERROR: Invalid source command at line {} in the input file:\n{}'
                        '\nMore than 3 parameters are required, {} were found.').
                       format(line_number + 1, str_, len(tokens)))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1
        else:
            if tokens[0] == 'qdot':
                if n_tokens < 3:
                    message = (('\nERROR: Invalid Qdot command at line {} in the input file:\n{}'
                                '\nMore than 3 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1
                else:
                    src.append(Source())
                    src[-1].type = tokens[0]
                    src[-1].ntype = 1
                    if is_float(tokens[1]):
                        src[-1].qdot = float(tokens[1])  # Numerical heat flux source
                    else:
                        src[-1].strqdot = tokens[1]  # Function name for heat flux source
                    for index in range(len(tokens[2:n_tokens])):
                        src[-1].nds.append(tokens[index+2])
            elif tokens[0] == 'Qsrc':
                if n_tokens < 3:
                    message = (('\nERROR: Invalid Qsrc command at line {} in the input file:\n{}'
                                '\nMore than 3 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1
                else:
                    src.append(Source())
                    src[-1].type = tokens[0]
                    src[-1].ntype = 2
                    if is_float(tokens[1]):
                        src[-1].Q = float(tokens[1])  # Numerical heat source
                    else:
                        src[-1].strQ = tokens[1]  # Function name for heat source
                    for index in range(len(tokens[2:n_tokens])):
                        src[-1].nds.append(tokens[index+2])
            elif tokens[0] == 'tstatQ':
                if n_tokens < 5:
                    message = (('\nERROR: Invalid TstatQ command at line {} in the input file:\n{}'
                                '\nMore than 5 parameters are required, {} were found.').
                               format(line_number + 1, str_, len(tokens)))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1
                else:
                    src.append(Source())
                    src[-1].type = tokens[0]
                    src[-1].ntype = 3
                    if is_float(tokens[1]):
                        src[-1].Q = float(tokens[1])  # Numerical heat source
                    else:
                        print(f"Error: Invalid TSTATQ data at line {line_number + 1}")
                        logfID.write(f"\nERROR: Invalid TSTATQ data at line {line_number + 1} in the input file:"
                                     f"\n{str_}")
                        message = ('\nERROR: Invalid TstatQ data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1
                    src[-1].tstat = tokens[2]  # Thermostatic node
                    if is_float(tokens[3]):
                        src[-1].Ton = float(tokens[3])  # Numerical Temperature on
                    else:
                        message = ('\nERROR: Invalid Ton data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1
                    if is_float(tokens[4]):
                        src[-1].Toff = float(tokens[4])  # Numerical Temperature off
                    else:
                        message = ('\nERROR: Invalid Toff data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1
                    for index in range(len(tokens[5:n_tokens])):
                        src[-1].nds.append(tokens[index+5])
            else:
                message = ('\nERROR: Unknown type of source at line {} in the input file:\n{}'.
                           format(line_number + 1, str_))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
    return line_number, src, inp_err


def parse_functions(lines, line_number, func, inp_err, logfID, prog_report, *text_widget):
    """
    Reads a functions block from the input file.

    Args:
        lines: File object to read from.
        line_number: Current line number.
        inp_err: Input error flag.
        func: List of functions (function is a class).

    """
    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*functions', str_, re.IGNORECASE):  # Case-insensitive regex
            break

        tokens = re.findall(r'\S+', str_)  # Find all tokens
        if len(tokens) == 3:
            func_block = ' '.join(tokens[0:2])
        else:
            func_block = ' '.join(tokens[0:3])

        if func_block.lower() == 'begin constant':
            func.append(Function())
            func[-1].name = '_'.join(tokens[2:])
            func[-1].indvar = 0
            func[-1].type = 0
            while line_number < len(lines):
                line_number += 1
                str_, line_number = nextline(lines, line_number)

                if re.search(r'end.*constant', str_, re.IGNORECASE):
                    break
                else:
                    tokens = re.findall(r'\S+', str_)
                    if is_float(tokens[0]):
                        func[-1].data = float(tokens[0])  # Convert to float
                    else:
                        message = ('\nERROR: Invalid function data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

        elif func_block.lower() == 'begin time table':
            func.append(Function())
            func[-1].name = '_'.join(tokens[3:])
            func[-1].indvar = 1
            func[-1].type = 1
            func[-1].data = []  # declaration of an empty array
            while line_number < len(lines):
                line_number += 1
                str_, line_number = nextline(lines, line_number)

                if re.search(r'end.*time.*table', str_, re.IGNORECASE):
                    break
                else:
                    tokens = re.findall(r'\S+', str_)
                    if is_float(tokens[0]) and float(tokens[1]):
                        func[-1].data.append([float(tokens[0]), float(tokens[1])])  # Convert to float
                    else:
                        message = ('\nERROR: Invalid function data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

        elif func_block.lower() == 'begin time spline':
            func.append(Function())
            func[-1].name = '_'.join(tokens[3:])
            func[-1].indvar = 1
            func[-1].type = 2
            func[-1].data = []
            while line_number < len(lines):
                line_number += 1
                str_, line_number = nextline(lines, line_number)

                if re.search(r'end.*time.*spline', str_, re.IGNORECASE):
                    break
                else:
                    tokens = re.findall(r'\S+', str_)
                    if is_float(tokens[0]) and float(tokens[1]):
                        func[-1].data.append = [float(tokens[0]), float(tokens[1])]  # Convert to float
                    else:
                        message = ('\nERROR: Invalid function data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

        elif func_block.lower() == 'begin time polynomial':
            func.append(Function())
            func[-1].name = '_'.join(tokens[3:])
            func[-1].indvar = 1
            func[-1].type = 3
            func[-1].range = []
            func[-1].data = []
            while line_number < len(lines):
                line_number += 1
                str_, line_number = nextline(lines, line_number)

                if re.search(r'end.*time.*polynomial', str_, re.IGNORECASE):
                    break
                else:
                    tokens = re.findall(r'\S+', str_)
                    if tokens[0].lower() == "range":
                        if is_float(tokens[0]) and float(tokens[1]):
                            func[-1].range = [float(tokens[0]), float(tokens[1])]  # Convert to float
                        else:
                            message = ('\nERROR: Invalid function data at line {} in the input file:\n{}.'.
                                       format(line_number + 1, str_))
                            user_feedback(message, prog_report, logfID, *text_widget)
                            inp_err = 1
                    elif tokens[0].lower() == "data":
                        for index in range(len(tokens[1:])):
                            if is_float(tokens[index]):
                                func[-1].data.append = float(tokens[index])  # Convert to float
                            else:
                                message = ('\nERROR: Invalid function data at line {} in the input file:\n{}.'.
                                           format(line_number + 1, str_))
                                user_feedback(message, prog_report, logfID, *text_widget)
                                inp_err = 1

        elif func_block.lower() == 'begin composite':
            func.append(Function())
            func[-1].name = '_'.join(tokens[2:])
            func[-1].indvar = 1
            func[-1].type = 4
            func[-1].data = []
            while line_number < len(lines):
                line_number += 1
                str_, line_number = nextline(lines, line_number)

                if re.search(r'end.*composite', str_, re.IGNORECASE):
                    break
                else:
                    tokens = re.findall(r'\S+', str_)
                    for index in range(len(tokens[1:])):
                        func[-1].data.append = tokens[index]  # Convert to float
        else:
            message = ('\nERROR: Unknown functions block command at line {} in the input file:\n{}.'.
                       format(line_number + 1, str_))
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1

    return line_number, func, inp_err


def parse_material(lines, line_number, mat, inp_err, logfID, Toff, prog_report, *text_widget):
    """Reads a material property block from the input file."""

    while line_number < len(lines):
        line_number += 1
        str_, line_number = nextline(lines, line_number)

        if re.search(r'end.*material', str_, re.IGNORECASE):
            break

        tokens = re.findall(r'\S+', str_)
        n_tokens = len(tokens)

        if n_tokens > 0:  # Check if tok is not empty
            mat.append(Material())
            if tokens[0].upper() == 'STATE':
                state = tokens[1].upper()
                if state == 'SOLID' or state == 'LIQUID' or state == 'GAS':
                    mat[-1].state = state
                else:
                    message = ('\nERROR: Invalid material state at line {} in the input file:\n{}.'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

            elif tokens[0].upper() == 'DENSITY':
                dens = tokens[1].upper()

                if dens == 'TABLE' or dens == 'SPLINE' or dens == 'POLYNOMIAL':
                    mat[-1].rhotype = dens
                    mat[-1].rhounits = ['(K)', '(kg/m^3)']
                    mat[-1].rhodata = []  # Initialize as a list
                    while line_number < len(lines):
                        str_, line_number = nextline(lines, line_number)
                        end_keyword = f'end.*density.*{dens.lower()}'  # Construct end keyword dynamically
                        if not re.search(end_keyword, str_, re.IGNORECASE):
                            tokens = re.findall(r'\S+', str_)
                            if is_float(tokens[0]) and float(tokens[1]):
                                mat[-1].rhodata.append([float(tokens[0]) + Toff, float(tokens[1])])
                            else:
                                message = ('\nERROR: Invalid density at line {} in the input file:\n{}.'.
                                           format(line_number + 1, str_))
                                user_feedback(message, prog_report, logfID, *text_widget)
                                inp_err = 1
                        else:
                            # Convert to numpy array after reading all data
                            mat[-1].rhodata = np.array(mat[-1].rhodata)
                            break
                elif dens == 'IDEAL':
                    pass

                else:
                    mat[-1].rhotype = 'CONST'
                    mat[-1].rhounits = ['(K)', '(kg/m^3)']
                    if is_float(tokens[2]):
                        mat[-1].rhodata = np.array([Toff, float(tokens[2])])  # NumPy array
                    else:
                        message = ('\nERROR: Invalid density data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

            elif tokens[0].upper() == 'CONDUCTIVITY':
                cond = tokens[1].upper()
                if cond == 'TABLE' or cond == 'SPLINE' or cond == 'POLYNOMIAL':
                    mat[-1].ktype = cond
                    mat[-1].kunits = ['(K)', '(W/m-K)']
                    mat[-1].kdata = []  # Initialize as a list
                    while line_number < len(lines):
                        str_, line_number = nextline(lines, line_number)
                        end_keyword = f'end.*conductivity.*{cond.lower()}'  # Construct end keyword dynamically
                        if not re.search(end_keyword, str_, re.IGNORECASE):
                            if not re.search(end_keyword, str_, re.IGNORECASE):
                                tokens = re.findall(r'\S+', str_)
                                if is_float(tokens[0]) and float(tokens[1]):
                                    mat[-1].kdata.append([float(tokens[0]) + Toff, float(tokens[1])])
                                else:
                                    message = ('\nERROR: Invalid conductivity data at line {} in the input file:\n{}.'.
                                               format(line_number + 1, str_))
                                    user_feedback(message, prog_report, logfID, *text_widget)
                                    inp_err = 1
                            else:
                                # Convert to numpy array after reading all data
                                mat[-1].kdata = np.array(mat[-1].kdata)
                                break
                else:
                    mat[-1].ktype = 'CONST'
                    mat[-1].kunits = ['(K)', '(W/m-K)']
                    if is_float(tokens[2]):
                        mat[-1].kdata = np.array([Toff, float(tokens[2])])  # NumPy array
                    else:
                        message = ('\nERROR: Invalid conductivity data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

            elif tokens[0].upper() == 'SPECIFIC' or tokens[0].upper() == 'C_V':
                cv = tokens[2].upper()
                mat[-1].cvunits = ['(K)', '(J/kg-K)']
                if cv == 'TABLE' or cv == 'SPLINE' or cv == 'POLYNOMIAL':
                    mat[-1].cvtype = cv
                    mat[-1].cvdata = []
                    while line_number < len(lines):
                        str_, line_number = nextline(lines, line_number)
                        end_key = f'end.*{"specific heat" if tokens[0].upper() == "SPECIFIC" else "c_v"}.*{cv.lower()}'
                        if not re.search(end_key, str_, re.IGNORECASE):
                            tokens = re.findall(r'\S+', str_)
                            if is_float(tokens[0]) and float(tokens[1]):
                                mat[-1].cvdata.append([float(tokens[0]) + Toff, float(tokens[1])])
                            else:
                                message = ('\nERROR: Invalid C_v data at line {} in the input file:\n{}.'.
                                           format(line_number + 1, str_))
                                user_feedback(message, prog_report, logfID, *text_widget)
                                inp_err = 1
                        else:
                            # Convert to numpy array after reading all data
                            mat[-1].cvdata = np.array(mat[-1].cvdata)
                            break
                else:
                    mat[-1].cvtype = 'CONST'
                    if is_float(tokens[3]):
                        mat[-1].cvdata = np.array([Toff, float(tokens[3])])  # NumPy array
                    else:
                        message = ('\nERROR: Invalid C_v data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

            elif tokens[0].upper() == 'C_P':
                cp = tokens[2].upper()
                mat[-1].cpunits = ['(K)', '(J/kg-K)']
                if cp == 'TABLE' or cp == 'SPLINE' or cp == 'POLYNOMIAL':
                    mat[-1].cptype = cp
                    mat[-1].cpdata = []
                    while line_number < len(lines):
                        str_, line_number = nextline(lines, line_number)
                        end_keyword = f'end.*c_p.*{cp.lower()}'
                        if not re.search(end_keyword, str_, re.IGNORECASE):
                            tokens = re.findall(r'\S+', str_)
                            if is_float(tokens[0]) and float(tokens[1]):
                                mat[-1].cvdata.append([float(tokens[0]) + Toff, float(tokens[1])])
                            else:
                                message = ('\nERROR: Invalid C_p data at line {} in the input file:\n{}.'.
                                           format(line_number + 1, str_))
                                user_feedback(message, prog_report, logfID, *text_widget)
                                inp_err = 1
                        else:
                            # Convert to numpy array after reading all data
                            mat[-1].cpdata = np.array(mat[-1].cpdata)
                            break
                else:
                    mat[-1].cptype = 'CONST'
                    if is_float(tokens[3]):
                        mat[-1].cpdata = np.array([Toff, float(tokens[3])])  # NumPy array
                    else:
                        message = ('\nERROR: Invalid C_p data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

            elif tokens[0].upper() == 'VISCOSITY':
                mu = tokens[2].upper()
                mat[-1].muunits = ['(K)', '(kg/m-s)']
                if mu == 'TABLE' or mu == 'SPLINE' or mu == 'POLYNOMIAL':
                    mat[-1].mutype = mu
                    mat[-1].mudata = []
                    while line_number < len(lines):
                        str_, line_number = nextline(lines, line_number)
                        end_keyword = f'end.*viscosity.*{mu.lower()}'
                        if not re.search(end_keyword, str_, re.IGNORECASE):
                            tokens = re.findall(r'\S+', str_)
                            if is_float(tokens[0]) and float(tokens[1]):
                                mat[-1].mudata.append([float(tokens[0]) + Toff, float(tokens[1])])
                            else:
                                message = ('\nERROR: Invalid viscosity data at line {} in the input file:\n{}.'.
                                           format(line_number + 1, str_))
                                user_feedback(message, prog_report, logfID, *text_widget)
                                inp_err = 1
                        else:
                            # Convert to numpy array after reading all data
                            mat[-1].mudata = np.array(mat[-1].mudata)
                            break
                else:
                    mat[-1].mutype = 'CONST'
                    if is_float(tokens[2]):
                        mat[-1].mudata = np.array([Toff, float(tokens[2])])  # NumPy array
                    else:
                        message = ('\nERROR: Invalid viscosity data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

            elif tokens[0].upper() == 'BETA':
                beta = tokens[2].upper()
                mat[-1].betaunits = ['(K)', '(1/K)']
                if beta == 'TABLE' or beta == 'SPLINE' or beta == 'POLYNOMIAL':
                    mat[-1].betatype = beta
                    mat[-1].betadata = []
                    while line_number < len(lines):
                        str_, line_number = nextline(lines, line_number)
                        end_keyword = f'end.*beta.*{beta.lower()}'
                        if not re.search(end_keyword, str_, re.IGNORECASE):
                            tokens = re.findall(r'\S+', str_)
                            if is_float(tokens[0]) and float(tokens[1]):
                                mat[-1].betadata.append([float(tokens[0]) + Toff, float(tokens[1])])
                            else:
                                message = ('\nERROR: Invalid Beta data at line {} in the input file:\n{}.'.
                                           format(line_number + 1, str_))
                                user_feedback(message, prog_report, logfID, *text_widget)
                                inp_err = 1
                        else:
                            # Convert to numpy array after reading all data
                            mat[-1].betadata = np.array(mat[-1].betadata)
                            break
                else:
                    mat[-1].betatype = 'CONST'
                    if is_float(tokens[2]):
                        mat[-1].betadata = np.array([Toff, float(tokens[2])])  # NumPy array
                    else:
                        message = ('\nERROR: Invalid Beta data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

            elif tokens[0].upper() == 'PR':
                Pr = tokens[2].upper()
                mat[-1].Prunits = ['(K)', '']
                if Pr == 'TABLE' or Pr == 'SPLINE' or Pr == 'POLYNOMIAL':
                    mat[-1].Prtype = beta
                    mat[-1].Prdata = []
                    while line_number < len(lines):
                        str_, line_number = nextline(lines, line_number)
                        end_keyword = f'end.*Pr.*{Pr.lower()}'
                        if not re.search(end_keyword, str_, re.IGNORECASE):
                            tokens = re.findall(r'\S+', str_)
                            if is_float(tokens[0]) and float(tokens[1]):
                                mat[-1].Prdata.append([float(tokens[0]) + Toff, float(tokens[1])])
                            else:
                                message = ('\nERROR: Invalid Pr number data at line {} in the input file:\n{}.'.
                                           format(line_number + 1, str_))
                                user_feedback(message, prog_report, logfID, *text_widget)
                                inp_err = 1
                        else:
                            # Convert to numpy array after reading all data
                            mat[-1].betadata = np.array(mat[-1].betadata)
                            break
                else:
                    mat[-1].Prtype = 'CONST'
                    if is_float(tokens[2]):
                        mat[-1].Prdata = np.array([Toff, float(tokens[2])])  # NumPy array
                    else:
                        message = ('\nERROR: Invalid Pr number data at line {} in the input file:\n{}.'.
                                   format(line_number + 1, str_))
                        user_feedback(message, prog_report, logfID, *text_widget)
                        inp_err = 1

            elif tokens[0].upper() == 'GAS':
                mat[-1].Runits = ['K', '']
                if is_float(tokens[2]):
                    mat[-1].R = float(tokens[2])
                else:
                    message = ('\nERROR: Invalid gas constant data at line {} in the input file:\n{}.'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

            elif tokens[0].upper() == 'REFERENCE':
                mat[-1].ref = ' '.join(tokens[1:])

            elif tokens[0].upper() == 'END':
                if not re.search(r'end.*material', str_, re.IGNORECASE):
                    message = ('\nERROR: Invalid END command at line {} in the input file:\n{}.'.
                               format(line_number + 1, str_))
                    user_feedback(message, prog_report, logfID, *text_widget)
                    inp_err = 1

            else:
                message = ('\nERROR: Invalid material command at line {} in the input file:\n{}.'.
                           format(line_number + 1, str_))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1

        else:
            if not re.search(r'end.*material', str_, re.IGNORECASE):
                message = ('\nERROR: Invalid material command at line {} in the input file:\n{}.'.
                           format(line_number + 1, str_))
                user_feedback(message, prog_report, logfID, *text_widget)
                inp_err = 1
    return line_number, mat, inp_err


def read_input_file(fid, logfID, prog_report, *text_widget):
    """
     Description:

       This function will parse the input file.

     Input:
       fid = file ID for the opened input file

     Output:
       inp_err = input error flag
                  0 - no errors during input file read
                  1 - errors occurred during input
       spar   = solution parameters structure
       nd     = node data structure
       el     = element/conductor data structure
       bc     = boundary condition data structure
       src    = source data structure
       ic     = initial condition structure
       enc    = radiation enclosure structure
       mat    = material property structure

     Functions Called:
       nextline = fetch the next line from the input file

    """
    inp_err = 0  # Input error flag
    spar = SolutionParameters()  # Solution Parameters
    nd = []  # list of Node data
    el = []  # list of Element data
    bc = []  # list of Boundary conditions
    src = []  # list of Source data
    ic = []  # list of Initial conditions
    enc = []  # list of Radiation enclosure
    mat = []  # list of Material properties
    func = []  # list of Functions

    lines = fid.readlines()  # store each line of the file fid in the list "lines"

    mat = matlib()
    line_number = 0
    tot_lines = len(lines)
    while line_number < tot_lines:  # decoding of the input file line by line
        str_, line_number = nextline(lines, line_number)

        if re.search(r'eof', str_, re.IGNORECASE):
            break

        elif re.search(r'begin.*solution', str_, re.IGNORECASE):
            line_number, spar, inp_err = parse_solution_parameters(lines, line_number, spar, inp_err, logfID,
                                                                   prog_report, *text_widget)

        elif re.search(r'begin.*nodes', str_, re.IGNORECASE):
            line_number, nd, inp_err = parse_nodes(lines, line_number, nd, inp_err, logfID, prog_report, *text_widget)

        elif re.search(r'begin.*conductors', str_, re.IGNORECASE):
            line_number, el, inp_err = parse_conductors(lines, line_number, el, inp_err, logfID,
                                                        prog_report, *text_widget)

        elif re.search(r'begin.*boundary.*conditions', str_, re.IGNORECASE):
            line_number, bc, inp_err = parse_boundary_conditions(lines, line_number, bc, inp_err, logfID,
                                                                 prog_report, *text_widget)

        elif re.search(r'begin.*radiation', str_, re.IGNORECASE):
            line_number, enc, inp_err = parse_radiation_enclosure(lines, line_number, enc, inp_err, logfID,
                                                                  prog_report, *text_widget)

        elif re.search(r'begin.*initial.*conditions', str_, re.IGNORECASE):
            line_number, ic, inp_err = parse_initial_conditions(lines, line_number, ic, inp_err, logfID,
                                                                prog_report, *text_widget)

        elif re.search(r'begin.*sources', str_, re.IGNORECASE):
            line_number, src, inp_err = parse_sources(lines, line_number, src, inp_err, logfID,
                                                      prog_report, *text_widget)

        elif re.search(r'begin.*functions', str_, re.IGNORECASE):
            line_number, func, inp_err = parse_functions(lines, line_number, func, inp_err, logfID,
                                                         prog_report, *text_widget)

        elif re.search(r'begin.*material', str_, re.IGNORECASE):
            line_number, mat, inp_err = parse_material(lines, line_number, mat, inp_err, logfID, spar.Toff,
                                                       prog_report, *text_widget)

        else:
            message = '\nERROR: Unable to parse line {} : {}\n'.format(line_number + 1, str_)
            user_feedback(message, prog_report, logfID, *text_widget)
            inp_err = 1

        line_number += 1

    return inp_err, spar, nd, el, bc, src, ic, func, enc, mat
