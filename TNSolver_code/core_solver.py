import os
import numpy as np
import datetime
import re
import math
from .utility_functions import verdate, setunits, QCF, functionF, plotfunc, user_feedback
from .read_functions import read_input_file, Element, Node, InitialCondition, is_float
from .evaluate_properties import evalfunc, rhoCvprop
from .output_files_writing import write_rst, write_csv_el, write_csv_nd, wrt_time, write_mat, write_out
from .element_matrix import elmat_radiation, elmat_outflow, elmat_conduction, elmat_convection, elmat_advection
from .element_preprocessor import elpre_radiation
from .element_postprocessor import elpost_radiation


def tn_solver(base_file_name, prog_report=1, *text_widget):  # quiet is now a keyword argument with a default value
    """
    TN_Solver - A Thermal Network Solver.

    Args:
        base_file_name: Base name of the input file (e.g., 'my_model').
        prog_report: it will manage how to provide a progress reporting to the user, options are:
            0 = no progress reports, fully silent
            1 = progress reports on the screen, file log created
            2 = progress reports on the GUI, file log created
        *text_widget: optional argument used by the GUI to provide a widget for the progress reports
    Returns:
        A tuple containing T, Q, nd, and el.
    """

    global scrout, logfID, Toff, g, sigma  # Declare globals

    # Splash screen
    if prog_report == 1:
        print('\n**********************************************************')
        print('*                                                        *')
        print('*      TNSolver - A Thermal Network Solver               *')
        print('*                                                        *')
        print(f'* {verdate():>40}               *')  # Right aligned
        print('*                                                        *')
        print('**********************************************************')

    # Open input and log files
    input_file = base_file_name + '.inp'
    try:
        with open(input_file, 'r') as fid:  # Use context manager for input file
            logfile = base_file_name + '.log'
            with open(logfile, 'w') as logfID:  # Use context manager for log file
                logfID.write('\n**********************************************************\n')
                logfID.write('*                                                        *\n')
                logfID.write('*      TNSolver - A Thermal Network Solver              *\n')
                logfID.write('*                                                        *\n')
                logfID.write(f'* {verdate():>40}*\n')  #Right aligned
                logfID.write('*                                                        *\n')
                logfID.write('**********************************************************\n')

                now = datetime.datetime.now()
                message = '\nModel run started at {}, on {}\n'.format(now.strftime("%I:%M %p"),
                                                                      now.strftime("%B %d, %Y"))
                user_feedback(message, prog_report, logfID, *text_widget)

                message = '\nReading the input file: {}\n'.format(os.path.abspath(input_file))
                user_feedback(message, prog_report, logfID, *text_widget)

                inp_err, spar, nd, el, bc, src, ic, func, enc, mat = read_input_file(fid, logfID, prog_report,
                                                                                     *text_widget)

                if inp_err:
                    message = '\nTNSolver: Errors reading the input file.\nPlease correct them and try again.\n\n'
                    user_feedback(message, prog_report, logfID, *text_widget)
                    return None, None, None, None  # Return None values to indicate failure

                # Set global constants
                Toff = spar.Toff
                g = spar.gravity
                sigma = spar.sigma

                # Initialize the thermal model
                message = '\nInitializing the thermal network model ...\n'
                user_feedback(message, prog_report, logfID, *text_widget)

                T, Q, spar, nd, el, bc, src, ic, func, enc, mat = init(spar, nd, el, bc, src, ic, func,
                                                                       enc, mat, logfID, prog_report, *text_widget)

                # Solve the thermal model
                if spar.steady:  # Accessing dictionary elements
                    message = '\nStarting solution of a steady thermal network model ...\n'
                    user_feedback(message, prog_report, logfID, *text_widget)
                else:
                    message = '\nStarting solution of a transient thermal network model ...\n'
                    user_feedback(message, prog_report, logfID, *text_widget)

                T, Q, spar, nd, el, src, func = tnsdriver(fid, T, Q, spar, nd, el, bc, src, func, mat,
                                                          logfID, prog_report, *text_widget)
                # Write output files
                with open(base_file_name + '_py.out', 'w') as fid:  # Use context manager
                    write_out(fid, spar, nd, el, bc, src, ic, enc, mat)
                message = '\nResults have been written to: {}\n'.format(base_file_name + '.out')
                user_feedback(message, prog_report, logfID, *text_widget)

                with open(base_file_name + '_nd_py.csv', 'w') as fid:
                    write_csv_nd(fid, spar, nd)
                message = '\nNode results have been written to: {}\n'.format(base_file_name + '_nd.csv')
                user_feedback(message, prog_report, logfID, *text_widget)

                with open(base_file_name + '_cond_py.csv', 'w') as fid:
                    write_csv_el(fid, spar, nd, el)
                message = '\nConductor results have been written to: {}\n'.format(base_file_name + '_cond.csv')
                user_feedback(message, prog_report, logfID, *text_widget)

                with open(base_file_name + '_py.rst', 'w') as fid:
                    write_rst(fid, spar.time, nd)
                message = '\nRestart has been written to: {}\n'.format(base_file_name + '.rst')
                user_feedback(message, prog_report, logfID, *text_widget)

                message = '\nAll done ...\n\n'
                user_feedback(message, prog_report, logfID, *text_widget)

        return T, Q, nd, el, spar

    except FileNotFoundError as e:
        message = '\nError: {}\n'.format(e)
        user_feedback(message, prog_report, logfID, *text_widget)
        return None, None, None, None  # Return None values to indicate failure
    except Exception as e:  # Catch other potential exceptions
        message = '\nAn error occurred: {}\n'.format(e)
        user_feedback(message, prog_report, logfID, *text_widget)
        return None, None, None, None


def tnsdriver(fid, T, Q, spar, nd, el, bc, src, func, mat, logfID, prog_report, *text_widget):
    """
    Solves the thermal network.

    Args:
        T: Initial nodal temperatures (NumPy array).
        Q: Initial element heat flows (NumPy array).
        spar: Simulation parameters (dictionary).
        nd: List of node dictionaries.
        el: List of element dictionaries.
        bc: List of boundary condition dictionaries.
        src: List of source dictionaries.
        func: Dictionary of functions.
        mat: List of material dictionaries.
        logfID: Log file ID
        prog_report: code for the progress report
        *text_widget: Terminal widget (optional)

    Returns:
        T, Q, spar, nd, el, src, func (updated).
    """

    global time, scrout  # Access global variables

    nnd = len(nd)
    nel = len(el)
    nsrc = len(src)
    nbc = len(bc)

    units, _ = setunits(spar.units)  # Get units (assuming setunits is defined)

    # Initialize linear system
    A = np.zeros((nnd, nnd))
    b = np.zeros((nnd, 1))
    lhs = np.zeros((2, 2))
    rhs = np.zeros((2, 1))

    if spar.steady:
        n_time_steps = 1
        time = 0.0
        spar.time = time
        dt = 0.0
        transient = False
    else:
        transient = True
        time = spar.begin_time
        spar.time = time
        if spar.time_step == spar.time_step:  # Check if the time step != NaN (NaN == NaN = False)
            dt = spar.time_step
            n_time_steps = int((spar.end_time - spar.begin_time) / spar.time_step)
        elif spar.number_time_steps == spar.number_time_steps:  # Check if number_time_steps != NaN
            n_time_steps = int(spar.number_time_steps)
            dt = (spar.end_time - spar.begin_time) / spar.number_time_steps
        else:
            message = '\nTNSolver - You must set a time step or number of steps\n'
            user_feedback(message, prog_report, logfID, *text_widget)
        Q = np.zeros(nel)
        for e in range(nel):
            el[e].Q = Q[e]
        filename = re.split(r'\.', fid.name)[0] + '_timedata_py.csv'
        fplt = open(filename, 'w')
        wrt_time(fplt, 0, time, nd, el, Toff)
        next_out = spar.print_interval
        nt = 0
        timeT = np.zeros((n_time_steps + 1, nnd + 1))  # Preallocate for efficiency
        timeQ = np.zeros((n_time_steps + 1, nel + 1))  # Preallocate for efficiency
        timeT[nt, 0] = time
        timeT[nt, 1:nnd + 1] = T - spar.Toff
        timeQ[nt, 0] = time
        timeQ[nt, 1:nel + 1] = Q

    # Time step loop - n_time_steps = 1 for steady problem
    for n in range(n_time_steps):
        if transient:
            time += dt
            if n == n_time_steps - 1:
                time = spar.end_time
            spar.time = time
            message = '\nTaking a time step to: {} {}\n'.format(time, units["time"])
            user_feedback(message, prog_report, logfID, *text_widget)
            for nn in range(nnd):
                nd[nn].Told = nd[nn].T

        # Update sources
        for i in range(nsrc):
            if src[i].ntype is not None:
                if src[i].ntype == 1:  # Constant source
                    if src[i].fncqdot is not None:  # Check if 'fncqdot' exists
                        src[i].qdot = evalfunc(func[src[i].fncqdot], time)
                    qdot = src[i].qdot
                    for j in range(len(src[i].nd)):
                        vol = nd[src[i].nd[j]].vol
                        src[i].Sc[j] = qdot * vol

                elif src[i].ntype == 2:  # Constant total source
                    if src[i].fncQ is not None:  # Check if 'fncQ' exists
                        src[i].Q = evalfunc(func[src[i].fncQ], time)
                    for j in range(len(src[i].nd)):
                        src[i].Sc[j] = src[i].Q

                elif src[i].ntype == 3:  # Thermostat controlled source
                    for j in range(len(src[i].nd)):
                        if nd[src[i].tnd].T < src[i].Ton and nd[src[i].tnd].T < src[i].Toff:
                            src[i].Sc[j] = src[i].Q
                        else:
                            src[i].Sc[j] = 0.0

                else:
                    message = '\nTNSolver: Oops - unknown source type in assembly.\n'
                    user_feedback(message, prog_report, logfID, *text_widget)

        # Update BCs
        for bcn in range(nbc):
            if bc[bcn].fncTinf is not None:
                bc[bcn].Tinf = evalfunc(func[bc[bcn].fncTinf], time)
                for j in range(len(bc[bcn].nd)):
                    index = int(bc[bcn].nd[j])
                    eqn = nd[index - 1].eqn  # Corrected indexing
                    nd[eqn].T = bc[bcn].Tinf + spar.Toff
                    T[eqn] = nd[eqn].T

            if bc[bcn].fncq is not None:
                bc[bcn].q = evalfunc(func[bc[bcn].fncq], time)

            if bc[bcn].fncq is not None:
                bc[bcn].A = evalfunc(func[bc[bcn].fncq], time)

        # Nonlinear loop
        converged = False
        iter_number = 0
        message = '\n    Nonlinear Solve\n  Iteration     Residual\n  --------- ------------\n'
        user_feedback(message, prog_report, logfID, *text_widget)

        while not converged:
            iter_number += 1

            # Update node parameters
            if transient:
                for nn in range(nnd):
                    if nd[nn].matID is not None:  # Check if 'matID' exists
                        if nd[nn].matID > 0:
                            ndT = (nd[nn].T + nd[nn].Told) / 2.0
                            rho, cv = rhoCvprop(mat[nd[nn].matID], ndT)
                            nd[nn].rhocv = rho * cv
                    if nd[nn].mfncID is not None:
                        nd[nn].rhocv = evalfunc(func[nd[nn].mfncID], time)
                    if nd[nn].vfncID is not None:
                        nd[nn].vol = evalfunc(func[nd[nn].vfncID], time)

            # Update element parameters
            for e in range(nel):
                nd1 = el[e].elnd[0]
                nd2 = el[e].elnd[1]
                Tel = np.array([nd[nd1].T, nd[nd2].T])
                el[e] = el[e].elpre(el[e], mat, Tel, logfID, prog_report, *text_widget)

            A[:, :] = 0.0  # reset after each iteration
            b[:] = 0.0  # reset after each iteration

            # Add capacitance term
            if transient:
                for nn in range(nnd):
                    if nd[nn].vol > 0:
                        row = nd[nn].eqn
                        cap = (nd[nn].rhocv * nd[nn].vol) / dt
                        A[row, row] += cap
                        b[row] += cap * (nd[nn].Told - nd[nn].T)

            # Add elements/conductors
            for e in range(nel):
                lhs[:, :] = 0.0
                rhs[:] = 0.0

                nd1 = el[e].elnd[0]
                nd2 = el[e].elnd[1]
                eq1 = nd[nd1].eqn
                eq2 = nd[nd2].eqn
                row = np.array([eq1, eq2])
                col = np.array([eq1, eq2])
                # Evaluate the element matrix for this conductor
                Tel = np.array([nd[nd1].T, nd[nd2].T])
                lhs, rhs = el[e].elmat(el[e], Tel, rhs)  # Call elmat method
                # Add to the global matrix and right-hand-side
                A[row[:, None], col] += lhs
                b[row] += rhs

            # Add source terms
            for i in range(nsrc):
                for j in range(len(src[i].nd)):
                    eqn = nd[src[i].nd[j]].eqn
                    b[eqn] += src[i].Sc[j]

            # Apply Neumann BCs
            for i in range(spar.nNBC):
                bcn = spar.Neumann[i]
                if bc[bcn].type == 'heat_flux':  # Check if type exists
                    for j in range(len(bc[bcn].nd)):
                        index = int(bc[bcn].nd[j])
                        eqn = nd[index].eqn
                        q = bc[bcn].q
                        Area = bc[bcn].A
                        b[eqn] += q * Area

            # Apply Dirichlet BCs
            for i in range(spar.nDBC):
                bcn = spar.Dirichlet[i]
                for j in range(len(bc[bcn].nd)):
                    index = int(bc[bcn].nd[j])
                    eqn = nd[index].eqn
                    A[eqn, :] = 0.0
                    A[eqn, eqn] = 1.0
                    b[eqn] = 0.0

            # Calculate residual
            # Non-dimensional L2 residual, handle potential division by zero
            residual = np.linalg.norm(b, 2) / np.linalg.norm(T, 2) if np.linalg.norm(T,
                                                                                     2) != 0 else np.inf

            message = '\n  {:6d}    {:g}'.format(iter_number, residual)
            user_feedback(message, prog_report, logfID, *text_widget)
            if residual < spar.convergence_residual:
                converged = True

            # Solve linear system
            try:
                dT = np.linalg.solve(A, b)  # Use NumPy's linear solver
            except np.linalg.LinAlgError as e:  # Catch singular matrix errors
                message = ('ERROR: Singular matrix: {}, thermal model is most likely missing a boundary condition.'
                           .format(e))
                user_feedback(message, prog_report, logfID, *text_widget)

            for nn in range(nnd):
                max_change = spar.max_change
                if abs(dT[nn, 0]) > max_change * nd[nn].T:
                    nd[nn].T += np.sign(dT[nn, 0]) * (max_change * nd[nn].T)
                else:
                    nd[nn].T += dT[nn, 0]  # Apply dT to update the solution
                T[nn] = nd[nn].T

            if iter_number > spar.max_iter_number:
                message = ('\nWARNING: Nonlinear iterations exceeded limit of {}'.format(spar.max_iter_number))
                user_feedback(message, prog_report, logfID, *text_widget)
                break

        # Post-process solution (heat flow rates)
        for e in range(nel):
            nd1 = el[e].elnd[0]
            nd2 = el[e].elnd[1]
            Tel = np.array([nd[nd1].T, nd[nd2].T])

            el[e], Q[e] = el[e].elpost(el[e], Tel)  # Call elpost method

        for i in range(nsrc):
            src[i].Qtot = 0.0
            for j in range(len(src[i].nd)):
                if src[i].ntype is not None:  # Check if ntype exists
                    if src[i].ntype == 1:
                        src[i].Qtot += src[i].qdot * nd[src[i].nd[j] - 1].vol  # Corrected indexing
                    elif src[i].ntype == 2 or src[i].ntype == 3:
                        src[i].Qtot += src[i].Q
                    else:
                        message = 'TNSolver: Oops - unknown source type in post processing.'
                        user_feedback(message, prog_report, logfID, *text_widget)

        # Output if necessary
        if transient and n + 1 >= next_out:
            nt += 1
            timeT[nt, 0] = time
            timeT[nt, 1:nnd + 1] = T - spar.Toff
            timeQ[nt, 0] = time
            timeQ[nt, 1:nel + 1] = Q
            wrt_time(fplt, n, time, nd, el, spar.Toff)
            next_out += spar.print_interval
            next_out = min(next_out, n_time_steps - 1)

    # Convert temperatures to I/O units
    if transient:
        fplt.close()  # Close the file
        message = ('\nTime data written to: {}'.format(filename))
        user_feedback(message, prog_report, logfID, *text_widget)

        T = timeT
        for n in range(nnd):
            nd[n].T = T[-1, n + 1]  # Corrected indexing
            nd[n].Told = nd[n].Told - spar.Toff
        Q = timeQ

    else:
        T = T - spar.Toff
        for n in range(nnd):
            nd[n].T = T[n]

    return T, Q, spar, nd, el, src, func


def init(spar, nd, el, bc, src, ic, func, enc, mat, logfID, prog_report, *text_widget):
    """
         Description:

           This function will initialize the model.

         Input:

           spar   = solution parameters class
           nd[]   = node data list
           el[]   = element/conductor data list
           bc[]   = boundary condition data list
           src[]  = source data list
           ic[]   = initial condition data list
           func[] = function data list
           enc[]  = radiation enclosure data list
           mat[]  = material property data list
           logfID = log file ID
           prog_report: code for the progress report
           *text_widget: Terminal widget (optional)

         Output:

           T() = initial temperature numpy vector
           Q() = initial total heat flux numpy vector
           spar = solution parameters class
           nd[] = node data list updated
           el[] = element/conductor data list updated
           bc[]   = boundary condition data list updated
           src[]  = source data list updated
           ic[]   = initial condition data list updated
           func[] = function data list updated
           enc[]  = radiation enclosure data list updated
           mat[]  = material property data list updated

         Functions Called:

           None

         History:

           Who    Date   Version  Note
           ---  -------- -------  -----------------------------------------------
           Luca 02/03/25 0.0.0    First release
        """

    initial_time = spar.begin_time

    nnd = len(nd)
    nel = len(el)
    nbc = len(bc)
    nsrc = len(src)
    nfunc = len(func)
    nenc = len(enc)
    nmat = len(mat)

    # plot functions shall be redefined somehow... for the moment not an issue
    if nfunc > 0 and spar.plot_function == 'no':
        for n in range(nfunc):
            plotfunc(func[n])

    if nenc > 0:
        for i in range(nenc):
            # Run a quality check on the supplied view factor matrix
            row_sum, sym_check = QCF(enc[i].A, enc[i].F)
            for n in range(len(row_sum)):
                if abs(1.0 - row_sum[n]) > 100.0 * np.finfo(float).eps:  # Use np.finfo for machine epsilon
                    message = ('\nWARNING: Row sum = {}, for surface {} in enclosure {}, is not equal to 1.0.\n'.
                               format(row_sum[n], enc[i]["label"][n], i + 1))
                    user_feedback(message, prog_report, logfID, *text_widget)
            for n in range(len(sym_check)):
                if abs(sym_check[n]) > 100.0 * np.finfo(float).eps:
                    message = ('\nWARNING: Symmetry check = {}, for surface {} in enclosure {}, is not equal to 0.0.\n'.
                               format(sym_check[n], enc[i]["label"][n], i + 1))
                    user_feedback(message, prog_report, logfID, *text_widget)
            # Calculate the function-F values for this view factor matrix
            sF = functionF(enc[i].emiss, enc[i].F)

            # Generate the radiation conductors
            m = 0
            for j in range(enc[i].nsurf - 1):
                for k in range(j + 1, enc[i].nsurf):
                    nel += 1
                    m += 1
                    el.append(Element())
                    el.label = f"{enc[i].label[j]}-{enc[i].label[k]}"
                    el.type = 'radiation'
                    el.nd1 = enc[i].label[j]
                    el.nd2 = enc[i].label[k]
                    el.sF = sF[j, k]
                    el.A = enc[i].A[j]
                    el.elst = 3
                    el.elmat = elmat_radiation
                    el.elpre = elpre_radiation
                    el.elpost = elpost_radiation
                    enc[i].eln[m - 1] = nel - 1
        nel = len(el)

    # Create the array of all the unique node labels in the model
    nd_labels = [nd[n].label for n in range(nnd)]  # node labels
    nndl = nnd
    for e in range(nel):  # element labels
        nndl += 1
        nd_labels.append(el[e].nd1)
        nndl += 1
        nd_labels.append(el[e].nd2)
    for i in range(nbc):  # BC node labels
        for j in range(len(bc[i].nds)):
            nndl += 1
            nd_labels.append(bc[i].nds[j])
    for i in range(nsrc):  # Source node labels
        for j in range(len(src[i].nds)):
            nndl += 1
            nd_labels.append(src[i].nds[j])

    nd_labels = sorted(list(set(nd_labels)), key=natural_sort_key)  # Sort with natural sorting, no repetitions
    #  Add the referenced nodes that were not parsed from a node block
    for label in nd_labels:
        ndx = matchnd(nd, label)
        if ndx == -1:
            nd.append(Node())
            nd[-1].label = label
            nd[-1].mat = 'N/A'
            nd[-1].vol = 0.0

    nnd = len(nd)

    # Locate the internal node number for each element node
    for e in range(nel):
        ndx = matchnd(nd, el[e].nd1)
        if ndx != -1:
            el[e].elnd[0] = ndx
        else:
            message = '\nERROR: Node {} not found for element {}.\n'.format(el[e].nd1, el[e].label)
            user_feedback(message, prog_report, logfID, *text_widget)
        ndx = matchnd(nd, el[e].nd2)
        if ndx != -1:
            el[e].elnd[1] = ndx
        else:
            message = '\nERROR: Node {} not found for element {}.\n'.format(el[e].nd2, el[e].label)
            user_feedback(message, prog_report, logfID, *text_widget)

    T = np.zeros(nnd)
    Q = np.zeros(nel)

    # Assign an equation number to each node and set initial temperature
    for n in range(nnd):
        nd[n].eqn = n
        nd[n].T = spar.Toff
        T[n] = nd[n].T
        if len(nd[n].mat) == 0:
            nd[n].mat = 'N/A'
        if not is_float(nd[n].vol):
            nd[n].vol = 0.0

    # Locate the internal node number and functions for each source
    for i in range(nsrc):
        for j in range(len(src[i].nds)):
            ndx = matchnd(nd, src[i].nds[j])
            if ndx != -1:
                # src[i].nd[j] = ndx
                src[i].nd.append(ndx)
            else:
                message = '\nERROR: Node {} not found for source {}.\n'.format(src[i].nds[j], src[i])
                user_feedback(message, prog_report, logfID, *text_widget)

        if src[i].ntype == 3:  # thermostat node
            ndx = matchnd(nd, src[i].tstat)
            if ndx != -1:
                src[i].tnd = ndx
                src[i].Toff = src[i].Toff + spar.Toff
                src[i].Ton = src[i].Ton + spar.Toff
            else:
                message = '\nERROR: Thermostat node {} not found for source {}.\n'.format(src[i].tstat, src[i])
                user_feedback(message, prog_report, logfID, *text_widget)

        if len(src[i].strqdot) != 0:  # User defined function Q_dot
            ndx = matchfunc(func, src[i].strqdot)
            if ndx != -1:
                src[i].fncqdot = ndx
            else:
                message = ('\nERROR: Cannot find matching function {} for source{}.\n'.
                           format(src[i].strqdot, src[i].type))
                user_feedback(message, prog_report, logfID, *text_widget)

        if len(src[i].strQ) != 0:  # User defined function Q
            ndx = matchfunc(func, src[i].strQ)
            if ndx != -1:
                src[i].fncQ = ndx
            else:
                message = ('\nERROR: Cannot find matching function {} for source{}.\n'.
                           format(src[i].strQ, src[i].type))
                user_feedback(message, prog_report, logfID, *text_widget)

        if src[i].fncqdot is not None:  # User function Q_dot exists
            src[i].qdot = evalfunc(func[src[i].fncqdot], initial_time)

        if src[i].fncQ is not None:  # User function Q exists
            src[i].Q = evalfunc(func[src[i].fncQ], initial_time)

    # Find the material number for each node and element, as required
    for n in range(nnd):
        if len(nd[n].mat) != 0 and nd[n].mat != 'N/A':
            ndx = matchmat(mat, nd[n].mat)
            if ndx != -1:
                nd[n].matID = ndx
            else:
                ndx = matchfunc(func, nd[n].mat)
                if ndx != -1:
                    nd[n].mfncID = ndx
            if ndx == -1:
                message = '\nERROR: Cannot find matching material or function for node {} material.\n'.format(nd[n].mat)
                user_feedback(message, prog_report, logfID, *text_widget)

        if nd[n].strvol:
            ndx = matchfunc(func, nd[n].strvol)
            if ndx != -1:
                nd[n].vfncID = ndx
            else:
                message = '\nERROR: Cannot find matching function for node {} volume.\n'.format(nd[n].strvol)
                user_feedback(message, prog_report, logfID, *text_widget)

    # compile the element matID field with material definition pointing to the corresponding material list
    for e in range(nel):
        if len(el[e].mat) != 0:
            for j in range(nmat):
                if el[e].mat.lower() == mat[j].name.lower():
                    el[e].matID = j
                    break

    # Find the Dirichlet and Neumann BC's
    for i in range(nbc):
        bc[i].nd = np.zeros(len(bc[i].nds))
        for j in range(len(bc[i].nds)):  # Determine internal node numbers
            for n in range(nnd):
                if bc[i].nds[j] == nd[n].label:
                    bc[i].nd[j] = n

        if bc[i].type == 'fixed_T':
            spar.Dirichlet.append(i)
            if len(bc[i].strTinf) != 0:
                ndx = matchfunc(func, bc[i].strTinf)
                if ndx != -1:
                    bc[i].fncTinf = ndx
                else:
                    message = '\nERROR: Cannot find matching function {} for BC temperature.\n'.format(bc[i].strTinf)
                    user_feedback(message, prog_report, logfID, *text_widget)
                bc[i].Tinf = evalfunc(func[bc[i].fncTinf], initial_time)

        else:
            spar.Neumann.append(i)
            if len(bc[i].strq) != 0:
                ndx = matchfunc(func, bc[i].strq)
                if ndx != -1:
                    bc[i].fncq = ndx
                else:
                    message = '\nERROR: Cannot find matching function {} for BC q.\n'.format(bc[i].strq)
                    user_feedback(message, prog_report, logfID, *text_widget)
                bc[i].q = evalfunc(func[bc[i].fncq], initial_time)  # Evaluate BC heat flux

            if bc[i].strA:
                ndx = matchfunc(func, bc[i].strA)
                if ndx != -1:
                    bc[i].fncA = ndx
                else:
                    message = '\nERROR: Cannot find matching function {} for BC area.\n'.format(bc[i].strA)
                    user_feedback(message, prog_report, logfID, *text_widget)
                bc[i].A = evalfunc(func[bc[i].fncA], initial_time)  # Evaluate BC area

    spar.nDBC = len(spar.Dirichlet)
    spar.nNBC = len(spar.Neumann)

    # Set the initial conditions
    nic = len(ic)
    if nic == 0:
        ic.append(InitialCondition())
        ic[0].nd = (list(range(0, nnd)))
        ic[0].Tinit = [0.0] * nnd
    else:
        for i in range(nic):
            if ic[i].nds[0] == 'all':
                Tinit = ic[i].Tinit
                ic[i].nd = list(range(0, nnd))
                ic[i].Tinit = [Tinit] * nnd
                # ic[i].Tinit = np.array(ic[i].Tinit)  # transform the list to an array
            else:
                if len(ic[i].Tinit) == 1:
                    Tinit = ic[i].Tinit[0]
                    for j in range(len(ic[i].nds)):
                        ndx = matchnd(nd, ic[i].nds[j])
                        ic[i].nd.append(ndx)
                        ic[i].Tinit.append(Tinit)
                    # ic[i].Tinit = np.array(ic[i].Tinit)  # transform the list to an array
                else:
                    for j in range(len(ic[i].nds)):
                        ndx = matchnd(nd, ic[i].nds[j])
                        ic[i].nd.append(ndx)

    # Now set the initial temperature state
    for i in range(nic):
        for j in range(len(ic[i].nd)):
            eqn = nd[ic[i].nd[j]].eqn
            nd[eqn].T = ic[i].Tinit[j] + spar.Toff
            T[eqn] = nd[eqn].T

    # Apply BC values to the initial temperature state
    for i in range(spar.nDBC):
        nbc = spar.Dirichlet[i]
        for j in range(len(bc[nbc].nd)):
            index = int(bc[nbc].nd[j])
            eqn = nd[index].eqn
            nd[eqn].T = bc[nbc].Tinf + spar.Toff
            T[eqn] = nd[eqn].T

    for e in range(nel):
        nd1 = el[e].elnd[0]
        nd2 = el[e].elnd[1]
        Tel = np.array([nd[nd1].T, nd[nd2].T])

        el[e] = el[e].elpre(el[e], mat, Tel, logfID, prog_report, *text_widget)
        el[e], Q[e] = el[e].elpost(el[e], Tel)

    return T, Q, spar, nd, el, bc, src, ic, func, enc, mat


def matchnd(nd, str_):
    for i in range(len(nd)):
        if nd[i].label == str_:
            return i
    return -1


def matchmat(mat, str_):
    for i in range(len(mat)):
        if mat[i].name == str_:
            return i
    return -1


def matchfunc(func, str_):
    for i in range(len(func)):
        if func[i].name == str_:
            return i
    return -1


def natural_sort_key(s, _re=re.compile(r'(\d+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _re.split(s)]


def sortndlabels(ndlabels):
    """Sorts node labels - numeric first, then alpha (case-insensitive)."""

    return sorted(ndlabels, key=natural_sort_key)


# --------------------------------------------------------------------------------------------------------------------
#                                Test
# --------------------------------------------------------------------------------------------------------------------

# T, Q, nd, el = tn_solver('../Test_Gui/pure_conduction_01', False)
# T, Q, nd, el = tn_solver('../Test_Gui/conduction', False)
# T, Q, nd, el = tn_solver('../Test_Gui/conduction.transient', False)
# T, Q, nd, el = tn_solver('../Test_Gui/convection', False)
# T, Q, nd, el = tn_solver('../Test_Gui/convection2', False)
# T, Q, nd, el = tn_solver('../Test_Gui/advection_only', False)
# T, Q, nd, el = tn_solver('../Test_Gui/advection', False)
# T, Q, nd, el = tn_solver('non_existing_input')


