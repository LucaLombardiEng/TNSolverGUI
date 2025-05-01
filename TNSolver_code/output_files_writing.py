import numpy as np
import datetime
from .utility_functions import setunits, verdate

def write_rst(fid, time, nd):
    """Writes the current solution state to the restart file.

    Args:
        fid: File object.
        time: Current time (float or int).
        nd: A list of dictionaries, where each dictionary represents a node
            and contains at least 'label' (string) and 'T' (float or int) keys.
    """

    fid.write(f" time = {time}\n")  # Use f-string for formatting

    for node in nd:  # Iterate through the list of dictionaries
        fid.write(f"  {node.label}  {node.T}\n")  # Use f-string


def write_csv_el(fid, spar, nd, el):
    """Writes convection/source/velocity data to a CSV file.

    Args:
        fid: File object.
        spar: A dictionary or object containing simulation parameters,
              including the 'units' key/attribute.
        nd: A list of dictionaries, where each dictionary represents a node
            and contains at least a 'T' key.
        el: A list of dictionaries or objects, where each element represents
            an element and contains 'label', 'type', 'nd1', 'nd2', 'elnd',
            'Q', 'U', and 'A' keys/attributes.
    """

    units, _ = setunits(spar.units)

    fid.write(f'"label","type","nd_i","nd_j","T_i ({units['T']})","T_j ({units['T']})","Q ({units['Q']})",'
              f'"U ({units['h']})","A ({units['A']})"\n')

    for e in el:  # Iterate through list of dictionaries/objects
        # Accessing dictionary elements. Changed indexing.
        fid.write(f'"{e.label}","{e.type}","{e.nd1}","{e.nd2}",{nd[e.elnd[0] - 1].T},'
                  f'{nd[e.elnd[1]-1].T},{e.Q},{e.U},{e.A}\n')


def write_csv_nd(fid, spar, nd):
    """Writes node data to a CSV file.

    Args:
        fid: File object.
        spar: A dictionary or object containing simulation parameters,
              including the 'units' key/attribute.
        nd: A list of dictionaries or objects, where each dictionary/object
            represents a node and contains 'label', 'mat', 'vol', and 'T'
            keys/attributes.
    """

    units, _ = setunits(spar.units)  # Accessing dictionary

    fid.write(f'"label","material","volume ({units['V']})","temperature ({units['T']})"\n')

    for n in nd:  
        fid.write(f'"{n.label}","{n.mat}",{n.vol},{n.T}\n')   # Accessing dictionary elements


def wrt_time(fid, stepn, time, nd, el, Toff):
    """Writes a time step to the CSV file.

    Args:
        fid: File object.
        stepn: Time step number (int).
        time: Current time (float or int).
        nd: A list of dictionaries or objects, where each element represents a node
            and contains at least a 'label' and 'T' key/attribute.
        el: A list of dictionaries or objects, where each element represents an element
            and contains at least a 'label', 'Q', and 'U' key/attribute.
    """

    if stepn == 0:
        # Write the header
        fid.write(' time,')
        for n in nd:
            fid.write(f' T_{n.label},')
        for e in el:
            fid.write(f' Q_{e.label},')
        for e in el:
            fid.write(f' U_{e.label},')
        fid.write(f'\n')

    # Write the data for this time step
    fid.write(f' {time},')
    for n in nd:
        fid.write(f' {n.T - Toff},')
    for e in el:
        fid.write(f' {e.Q},')
    for e in el:
        fid.write(f' {e.U},')
    fid.write(f'\n')


def write_mat(fid, mat, matID=None):
    """
    Print the material library.

    Args:
        fid: Opened file handle (1 for screen, or file object).
        mat: Material library (list of Material objects).
        matID: List of material IDs to print (optional, prints all if None).
    """

    SOLID = 1
    LIQUID = 2
    GAS = 3

    CONST = 1
    TABLE = 2
    SPLINE = 3
    POLY = 4
    USER = 5

    state = ['solid', 'liquid', 'gas']
    type_ = ['constant', 'table', 'monotonic spline', 'polynomial', 'user']

    if matID is None:
        matID = list(range(len(mat)))

    for n in matID:
        material = mat[n]
        if isinstance(fid, int) and fid == 1:
            print("\n")
            print(f"Name = {material.name}")
            if material.state is not None:
                print(f"State = {state[material.state - 1]}")

                if material.ktype is not None:
                    print("\nThermal Conductivity")
                    print(f"  Type = {type_[material.ktype - 1]}")
                    if material.ktype != POLY and material.ktype != USER:
                        print(f"  {material.kunits[0]:6s}      {material.kunits[1]:6s}")
                        if material.kdata is not None:
                            for row in material.kdata:
                                print(f"  {row[0]:7.1f}  {row[1]:10g}")

                if material.rhotype is not None:
                    print("\nDensity")
                    print(f"  Type = {type_[material.rhotype - 1]}")
                    if material.rhotype != POLY and material.rhotype != USER:
                        print(f"  {material.rhounits[0]:6s}      {material.rhounits[1]:6s}")
                        if material.rhodata is not None:
                            for row in material.rhodata:
                                print(f"  {row[0]:7.1f}  {row[1]:10g}")

                if material.cptype is not None:
                    print("\nConstant Pressure Specific Heat")
                    print(f"  Type = {type_[material.cptype - 1]}")
                    if material.cptype != POLY and material.cptype != USER:
                        print(f"  {material.cpunits[0]:6s}      {material.cpunits[1]:6s}")
                        if material.cpdata is not None:
                            for row in material.cpdata:
                                print(f"  {row[0]:7.1f}  {row[1]:#10g}")

                if material.cvtype is not None:
                    print("\nConstant Volume Specific Heat")
                    print(f"  Type = {type_[material.cvtype - 1]}")
                    if material.cvtype != POLY and material.cvtype != USER:
                        print(f"  {material.cvunits[0]:6s}      {material.cvunits[1]:6s}")
                        if material.cvdata is not None:
                            for row in material.cvdata:
                                print(f"  {row[0]:7.1f}  {row[1]:#10g}")

                if material.state == LIQUID or material.state == GAS:
                    if material.mutype is not None:
                        print("\nViscosity")
                        print(f"  Type = {type_[material.mutype - 1]}")
                        if material.mutype != POLY and material.mutype != USER:
                            print(f"  {material.muunits[0]:6s}      {material.muunits[1]:6s}")
                            if material.mudata is not None:
                                for row in material.mudata:
                                    print(f"  {row[0]:7.1f}  {row[1]:10g}")

                    if material.betatype is not None:
                        print("\nVolumetric Thermal Expansion Coefficient, beta")
                        print(f"  Type = {type_[material.betatype - 1]}")
                        if material.betatype != POLY and material.betatype != USER:
                            print(f"  {material.betaunits[0]:6s}      {material.betaunits[1]:6s}")
                            if material.betadata is not None:
                                for row in material.betadata:
                                    print(f"  {row[0]:7.1f}  {row[1]:10g}")

                    if material.Prtype is not None:
                        print("\nPrandtl number, Pr")
                        print(f"  Type = {type_[material.Prtype - 1]}")
                        if material.Prtype != POLY and material.Prtype != USER:
                            print(f"  {material.Prunits[0]:6s}      {material.Prunits[1]:6s}")
                            if material.Prdata is not None:
                                for row in material.Prdata:
                                    print(f"  {row[0]:7.1f}  {row[1]:10g}")

                print("\nReference:")
                print(material.ref)

        else: #file output
            fid.write("\n")
            fid.write(f"Name = {material.name}\n")
            if material.state is not None:
                fid.write(f"State = {state[material.state - 1]}\n")

                if material.ktype is not None:
                    fid.write("\nThermal Conductivity\n")
                    fid.write(f"  Type = {type_[material.ktype - 1]}\n")
                    if material.ktype != POLY and material.ktype != USER:
                        fid.write(f"  {material.kunits[0]:6s}      {material.kunits[1]:6s}\n")
                        if material.kdata is not None:
                            for row in material.kdata:
                                fid.write(f"  {row[0]:7.1f}  {row[1]:10g}\n")
                    #rest of the if statements are very similar and therefore omitted for brevity.

                if material.rhotype is not None:
                    fid.write("\nDensity\n")
                    fid.write(f"  Type = {type_[material.rhotype - 1]}\n")
                    if material.rhotype != POLY and material.rhotype != USER:
                        fid.write(f"  {material.rhounits[0]:6s}      {material.rhounits[1]:6s}\n")
                        if material.rhodata is not None:
                            for row in material.rhodata:
                                fid.write(f"  {row[0]:7.1f}  {row[1]:10g}\n")

                if material.cptype is not None:
                    fid.write("\nConstant Pressure Specific Heat")
                    fid.write(f"  Type = {type_[material.cptype - 1]}")
                    if material.cptype != POLY and material.cptype != USER:
                        fid.write(f"  {material.cpunits[0]:6s}      {material.cpunits[1]:6s}")
                        if material.cpdata is not None:
                            for row in material.cpdata:
                                 fid.write(f"  {row[0]:7.1f}  {row[1]:#10g}")

                if material.cvtype is not None:
                    fid.write("\nConstant Volume Specific Heat")
                    fid.write(f"  Type = {type_[material.cvtype - 1]}")
                    if material.cvtype != POLY and material.cvtype != USER:
                        fid.write(f"  {material.cvunits[0]:6s}      {material.cvunits[1]:6s}")
                        if material.cvdata is not None:
                            for row in material.cvdata:
                                 fid.write(f"  {row[0]:7.1f}  {row[1]:#10g}")

                if material.state == LIQUID or material.state == GAS:
                    if material.mutype is not None:
                        fid.write("\nViscosity")
                        fid.write(f"  Type = {type_[material.mutype - 1]}")
                        if material.mutype != POLY and material.mutype != USER:
                            fid.write(f"  {material.muunits[0]:6s}      {material.muunits[1]:6s}")
                            if material.mudata is not None:
                                for row in material.mudata:
                                     fid.write(f"  {row[0]:7.1f}  {row[1]:10g}")

                    if material.betatype is not None:
                        fid.write("\nVolumetric Thermal Expansion Coefficient, beta")
                        fid.write(f"  Type = {type_[material.betatype - 1]}")
                        if material.betatype != POLY and material.betatype != USER:
                            fid.write(f"  {material.betaunits[0]:6s}      {material.betaunits[1]:6s}")
                            if material.betadata is not None:
                                for row in material.betadata:
                                     fid.write(f"  {row[0]:7.1f}  {row[1]:10g}")

                    if material.Prtype is not None:
                        fid.write("\nPrandtl number, Pr")
                        fid.write(f"  Type = {type_[material.Prtype - 1]}")
                        if material.Prtype != POLY and material.Prtype != USER:
                            fid.write(f"  {material.Prunits[0]:6s}      {material.Prunits[1]:6s}")
                            if material.Prdata is not None:
                                for row in material.Prdata:
                                    fid.write(f"  {row[0]:7.1f}  {row[1]:10g}")

                fid.write("\nReference:")
                fid.write(material.ref)


def write_out(fid, spar, nd, el, bc, src, ic, enc, mat):
    u, conv = setunits(spar.units)

    fid.write('\n**********************************************************\n')
    fid.write('* *\n')
    fid.write('* TNSolver - A Thermal Network Solver            *\n')
    fid.write('* *\n')
    fid.write(f'* {" "*33} {" "*33} *\n') #replace verdate with spaces as no verdate variable
    fid.write('* *\n')
    fid.write('**********************************************************\n')

    endtime = datetime.datetime.now()
    fid.write(f'\nModel run finished at {endtime.strftime("%I:%M %p")}, on {endtime.strftime("%B %d, %Y")}\n')

    fid.write('\n*** Solution Parameters ***\n\n')
    fid.write(f'  Title: {spar.title}\n\n')
    fid.write(f'  Type                         =  {spar.type}\n')
    fid.write(f'  Units                        =  {spar.units}\n')
    fid.write(f'  Temperature units            =  {spar.Temp_units}\n')
    fid.write(f'  Nonlinear convergence        =  {spar.convergence_residual}\n')
    fid.write(f'  Maximum nonlinear iterations =  {spar.max_iter_number}\n')
    fid.write(f'  Gravity                      =  {spar.gravity} ({u['a']})\n')
    fid.write(f'  Stefan-Boltzmann constant    =  {spar.sigma} ({u['sigma']})\n')

    nnd = len(nd)
    fid.write('\n*** Nodes ***\n\n')
    fid.write('                      Volume   Temperature\n')
    fid.write(f'   Label    Material    ({u['V']})      ({u['T']})\n')
    fid.write(' --------- ---------- ---------- -----------\n')
    for n in range(nnd):
        fid.write(f'{nd[n].label:10} {nd[n].mat:10} {nd[n].vol:10g} {nd[n].T:11g}\n')

    nel = len(el)
    fid.write('\n*** Conductors ***\n\n')
    fid.write('                                            Q_ij\n')
    fid.write(f'    Label         Type     Node i    Node j     ({u['Q']})\n')
    fid.write(' ---------- ------------- ---------- ---------- ----------\n')
    for e in range(nel):
        fid.write(f' {el[e].label:10} {el[e].type:13} {el[e].nd1:10} {el[e].nd2:10} {el[e].Q:10g}\n')

    nsrc = len(src)
    if nsrc > 0:
        fid.write('\n*** Sources ***\n\n')
        fid.write(f'           Q_i\n')
        fid.write(f'    Type      ({u['Q']})      Node(s)\n')
        fid.write(' ---------- ---------- --------------------\n')
        for i in range(nsrc):
            fid.write(f' {src[i].type:10} {src[i].Qtot:10g} ')
            for node_label in src[i].nds:
                fid.write(f' {node_label}')
            fid.write('\n')

    nbc = len(bc)
    if nbc > 0:
        fid.write('\n*** Boundary Conditions ***\n\n')
        fid.write('    Type    Parameter(s)     Node(s)\n')
        fid.write(' ---------- ------------------ --------------------\n')
        for i in range(nbc):
            if bc[i].type.lower() == 'fixed_t':
                fid.write(f' {bc[i].type:10} {bc[i].Tinf:8g}          ')
            elif bc[i].type.lower() == 'heat_flux':
                fid.write(f' {bc[i].type:10} {bc[i].q:8g} {bc[i].A:8g} ')
            for node_label in bc[i].nds:
                fid.write(f' {node_label}')
            fid.write('\n')

    nic = len(ic)
    if nic > 0:
        fid.write('\n*** Initial Conditions ***\n\n')
        fid.write(' Temperature     Node (s)\n')
        fid.write(' ----------- --------------------\n')
        for i in range(nic):
            fid.write(f' {ic[i].Tinit[0]:10g} ')
            for node_index in ic[i].nd:
                fid.write(f' {nd[node_index].label}')
            fid.write('\n')

    nenc = len(enc)
    if nenc > 0:
        for i in range(nenc):
            fid.write(f'\n*** Radiation Enclosure Number {i + 1} ***\n\n')
            fid.write('    Surface    Emissivity      Area   View Factors\n')
            fid.write(' ----------- ---------- ----------- -------------------\n')
            for k in range(len(enc[i].label)):
                fid.write(f' {enc[i].label[k]:11} {enc[i].emiss[k]:10g}  {enc[i].A[k]:10g} ')
                for j in range(len(enc[i].F[k])):
                    fid.write(f' {enc[i].F[k][j]:6.4f}')
                fid.write('\n')
            fid.write('\n    Generated Radiation Conductors for this Enclosure\n\n')
            fid.write(f'    Label         Type     Node i    Node j    script-F      Area\n')
            fid.write(' ---------- ------------- ---------- ---------- ---------- ----------\n')
            for k in range(len(enc[i].eln)):
                e = enc[i].eln[k]
                fid.write(
                    f' {el[e].label:10} {el[e].type:13} {el[e].nd1:10} {el[e].nd2:10} {el[e].sF:10g} {el[e].A:10g}\n')

    fid.write('\n*** Conductor Parameters ***\n')

    types = []
    for e in range(nel):
        types.append(el[e].elst)
    types = list(set(types))

    for i in range(len(types)):
        current_type = types[i]
        if current_type == 3:  # Radiation
            fid.write('\nradiation: Surface to Surface Radiation\n\n')
            fid.write(f'           h_r\n')
            fid.write(f'    label    ({u['h']})\n')
            fid.write(' ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].hr:10g}\n')
        elif current_type == 4:  # Surface Radiation
            fid.write('\nsurfrad: Surface Radiation\n\n')
            fid.write(f'           h_r\n')
            fid.write(f'    label    ({u['h']})\n')
            fid.write(' ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].hr:10g}\n')
        elif current_type == 6:  # EFC cylinder
            fid.write('\nEFCcyl: External Forced Convection - Cylinder\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Re Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Re:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 7:  # ENC Horizontal cylinder
            fid.write('\nENChcyl: External Natural Convection - Horizontal Cylinder\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 8:  # EFC diamond
            fid.write('\nEFCdiamond: External Forced Convection - Diamond\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Re Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Re:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 9:  # ENC Horizontal plate up
            fid.write('\nENChplateup: External Natural Convection - Horizontal Plate Up\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 10:  # ENC Horizontal plate down
            fid.write('\nENChplatedown: External Natural Convection - Horizontal Plate Down\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 11:  # ENC Vertical plate
            fid.write('\nENCvplate: External Natural Convection - Vertical Plate\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 12:  # ENC Inclined up plate
            fid.write('\nENCiplateup: External Natural Convection - Inclined Plate Up\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 13:  # ENC Inclined down plate
            fid.write('\nENCiplatedown: External Natural Convection - Inclined Plate Down\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 16:  # IFC Duct
            fid.write('\nIFCduct: Internal Forced Convection - Duct\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Re Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Re:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 17:  # EFC Plate
            fid.write('\nEFCplate: External Forced Convection - Flat Plate\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Re Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Re:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 18:  # ENC Sphere
            fid.write('\nENCsphere: External Natural Convection - Sphere\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 19:  # EFC sphere
            fid.write('\nEFCsphere: External Forced Convection - Sphere\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Re Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Re:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 20:  # EFC impinging jet
            fid.write('\nEFCimpjet: External Forced Convection - Impinging Round Jet\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Re Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Re:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 21:  # INC Vertical Enclosure
            fid.write('\nINCvenc: Internal Natural Convection - Vertical Rectangular Enclosure\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    fid.write(f' {el[e].label:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 22:  # Forced Convection User Function
            fid.write('\nFCuser: Forced Convection User Function\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    function   Re Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    function_str = str(el[e].function) if el[e].function else "None"
                    fid.write(f' {el[e].label:10} {function_str:10} {el[e].Re:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')
        elif current_type == 23:  # Natural Convection User Function
            fid.write('\nNCuser: Natural Convection User Function\n\n')
            fid.write(f'                                     h\n')
            fid.write(f'    label    function   Ra Number  Nu Number  ({u['h']})\n')
            fid.write(' ---------- ---------- ---------- ---------- ----------\n')
            for e in range(nel):
                if el[e].elst == current_type:
                    function_str = str(el[e].function) if el[e].function else "None"
                    fid.write(f' {el[e].label:10} {function_str:10} {el[e].Ra:10g} {el[e].Nu:10g} {el[e].htc:10g}\n')

    elnd = [[0] * nnd for _ in range(nel)]
    for e in range(nel):
        elnd[e][el[e].elnd[0]] = 1
        elnd[e][el[e].elnd[1]] = 1

    ndel = [[0] * nel for _ in range(nnd)]
    for e in range(nel):
        ndel[el[e].elnd[0]][e] = 1
        ndel[el[e].elnd[1]][e] = 1

    ndnd = [[0] * nnd for _ in range(nnd)]
    for n in range(nnd):
        for e in range(nel):
            if ndel[n][e] == 1:
                for nn in range(nnd):
                    if elnd[e][nn] == 1:
                        ndnd[n][nn] = 1

    fid.write('\n*** Control Volume Energy Balances ***\n')

    for n in range(nnd):
        fid.write(f'\nEnergy balance for node: {nd[n].label}\n\n')
        fid.write('    nd_i    -  conductor -      nd_j       T_i       T_j      Q_ij   direction\n')
        conels = [e for e in range(nel) if ndel[n][e] == 1]
        for i in range(len(conels)):
            e = conels[i]
            if el[e].elnd[0] == n:
                if el[e].Q < 0.0:
                    direction = 'in'
                else:
                    direction = 'out'
            elif el[e].elnd[1] == n:
                if el[e].Q < 0.0:
                    direction = 'out'
                else:
                    direction = 'in'

            fid.write(f'{el[e].nd1:10} - {el[e].label:10} - {el[e].nd2:10}, {nd[el[e].elnd[0]].T:10g}'
                      f' {nd[el[e].elnd[1]].T:10g} {el[e].Q:10g}    {direction}\n')

    matIDs = []
    for e in range(nel):
        if el[e].matID != '':
            matIDs.append(el[e].matID)
    for n in range(nnd):
        if nd[n].matID != '':
            matIDs.append(nd[n].matID)

    if matIDs:
        matIDs = list(set(matIDs))
        fid.write('\n*** Material Library Properties Used in the Model ***\n')
        write_mat(fid, mat, matIDs)


