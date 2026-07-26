"""
    Thermal Solver Network Input File Generation
    This function generates the input file used by the TNSolver

    To be Done:
    complete the definition of
     - initial conditions
     - radiation enclosures
     - functions
     - user defined material

     check the consistency of the temperatures

     revise the transient options

    Luca Lombardi
    Rev 0: First Draft

"""
from pint import UnitRegistry

from datetime import date, datetime
from TNSolver_GUI.Thermal_Network_TAB.gUtility import (material_list, angle_units, time_unit, htc_unit, length_units_SI,
                                                       area_unit_SI, volume_unit_SI, density_unit_SI, heat_flux_unit,
                                                       specific_heat_unit, velocity_unit, temperature_unit,
                                                       volumetric_power_unit, power_unit, thermal_conductivity_unit)
from TNSolver_code.utility_functions import setunits


def unit_conversion(to_unit, from_unit, unit_table, from_value):
    u_reg = UnitRegistry

    from_index = unit_table[0].index(from_unit)
    to_index = unit_table[1].index(to_unit)

    from_value = float(from_value)
    from_magnitude = u_reg.Quantity(from_value, unit_table[1][from_index])

    to_magnitude = from_magnitude.to(unit_table[1][to_index])

    return to_magnitude.magnitude


def unit_conversion2(to_unit, from_unit, from_value):
    u_reg = UnitRegistry

    from_value = float(from_value)
    from_magnitude = u_reg.Quantity(from_value, from_unit)

    to_magnitude = from_magnitude.to(to_unit)

    return to_magnitude.magnitude


def TNSolver_input_file_gen(filename, solution, nodes, elements, initialize, functions, materials):

    all_mat_list = list(materials.keys())
    f = open(filename, "w")
    separator = '! -----------------------------------------------------------------------------\n'
    # ---------- Header ----------
    f.write("! File generated automatically by the TNSolver GUI\n")
    today = date.today()
    now = datetime.now()
    f.write("! Date: " + today.strftime("%B %d, %Y") + "\n")
    f.write("! Time: " + now.strftime("%H:%M:%S") + "\n")
    f.write("! Original file: " + filename + "\n")
    # ---------- Solution Parameters Section ----------
    f.write(separator)
    f.write("Begin Solution Parameters\n")
    f.write("   title = " + solution.title + "\n")

    if solution.type == 'Steady State':
        aux = 'steady'
    else:
        aux = 'transient'

    f.write("   type = " + aux + "\n")
    f.write("   units = " + solution.units + "\n")
    f.write("   T units = " + solution.Tunits + "\n")
    f.write("   nonlinear convergence = " + solution.convergence + "\n")
    f.write("   maximum nonlinear iterations = " + solution.iterations + "\n")

    units, _ = setunits(solution.units)

    if solution.type == 'Transient':
        f.write("   begin time = " + solution.begin_time + "\n")
        f.write("   end time = " + solution.end_time + "\n")
        # f.write("   time step = " + solution.time_step)
        f.write("   number of time steps = " + solution.time_steps + "\n")
        f.write("   print Interval = " + solution.print_intervals + "\n")

    f.write("   Stefan-Boltzmann = " + str(solution.StefanBoltzmann) + "\n")
    f.write("   gravity = " + str(solution.gravity) + "\n")
    f.write("   graphviz output = no" + "\n")
    f.write("   plot functions = no" + "\n")
    f.write("End Solution Parameters" + "\n")

    # ---------- Node Section ----------
    f.write(separator)
    f.write("Begin Nodes \n")
    for key in nodes.keys():
        node = nodes[key]
        volume = unit_conversion('m**3', node["volume"][1], volume_unit_SI, node["volume"][0])

        if node["material"].casefold() == 'user defined':
            density = unit_conversion('kg/m**3', node["density"][1], density_unit_SI, node["density"][0])
            Specific_Heat = unit_conversion('J/kg/K', node["specific Heat"][1],
                                            specific_heat_unit, node["specific Heat"][0])

            aux = density * Specific_Heat
            f.write("   " + str(node["ID"]) + "\t" +
                    str(aux) + "\t" +
                    str(volume) + "\t! " +
                    str(node["comment"]) + "\t! volumetric heat capacity [J/(m³·K)] ")
        elif node["material"].casefold() in [item.casefold() for item in all_mat_list]:
            f.write("   " + str(node["ID"]) + "\t" +
                    str(node["material"]) + "\t" +
                    str(volume) + "\t! " +
                    str(node["comment"]) + ", volume [m³]\n")
        else:
            print("node material: " + node["material"])
            f.write("   ! WARNING: the node " + str(node["ID"]) + " does not have a proper material assigned."
                    " Check the database\n")

    f.write("End Nodes \n")

    # ---------- Conductors Section  ----------

    f.write(separator)
    f.write("Begin Conductors \n")
    for key in elements.keys():
        element = elements[key]
        if element["subtype"] == "Linear conduction":

            if element["material"] == 'user defined':
                k = unit_conversion('W/m/K', element["thermal conductivity"][1], thermal_conductivity_unit,
                                    element["thermal conductivity"][0])
                aux1 = str(k)
                aux2 = "\t!k [W/(m·K)], L [m], A [m²]\n"
            elif element["material"].casefold() in [item.casefold() for item in all_mat_list]:
                aux1 = str(element["material"]).replace(' ', '_')
                aux2 = "!material, L [m], A [m²]\n"
            else:
                print("element material: " + element["material"])
                f.write("   ! WARNING: the element " + str(element["ID"]) + " does not have a proper material assigned."
                        " Check the database\n")
                aux1 = "undefined"
                aux2 = "!undefined, L [m], A [m²]\n"

            length = unit_conversion('m', element["width"][1], length_units_SI,
                                     element["width"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])

            f.write("   " +
                    str(element["ID"]) +
                    "\t conduction \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    aux1 + "\t" +
                    str(length) + "\t" +
                    str(area) + "\t" +
                    aux2)
        elif element["subtype"] == "Cylindrical conduction":
            if element["material"] == "user defined":
                k = unit_conversion('W/m/K', element["thermal conductivity"][1], thermal_conductivity_unit,
                                    element["thermal conductivity"][0])
                aux1 = str(k)
                aux2 = "!k [W/(m·K)], ri [m], ro [m], L [m] \n"
            elif element["material"] in all_mat_list:
                aux1 = str(element["material"]).replace(' ', '_')
                aux2 = "!material, ri [m], ro [m], L [m] \n"
            else:
                f.write("   ! WARNING: the element " + str(element["ID"]) + " does not have a proper material assigned."
                        " Check the database\n")
                aux1 = "undefined"
                aux2 = "!undefined, ri [m], ro [m], L [m] \n"

            r_in = unit_conversion('m', element["inner radius"][1], length_units_SI, element["inner radius"][0])
            r_out = unit_conversion('m', element["outer radius"][1], length_units_SI, element["outer radius"][0])
            height = unit_conversion('m', element["height"][1], length_units_SI, element["height"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t cylindrical \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    aux1 + "\t" +
                    str(r_in) + "\t" +
                    str(r_out) + "\t" +
                    str(height) + "\t" +
                    aux2)
        elif element["subtype"] == "Spherical conduction":
            if element["material"] == "user defined":
                k = unit_conversion('W/m/K', element["thermal conductivity"][1], thermal_conductivity_unit,
                                    element["thermal conductivity"][0])
                aux1 = str(k)
                aux2 = "!k [W/(m·K)], ri [m], ro [m]\n"
            elif element["material"] in all_mat_list:
                aux1 = str(element["material"]).replace(' ', '_')
                aux2 = "\t!material, ri [m], ro [m]\n"
            else:
                f.write("   ! WARNING: the element " + str(element["ID"]) + " does not have a proper material assigned."
                        " Check the database\n")
                aux1 = "undefined"
                aux2 = "!undefined, ri [m], ro [m]\n"

            r_in = unit_conversion('m', element["inner radius"][1], length_units_SI, element["inner radius"][0])
            r_out = unit_conversion('m', element["outer radius"][1], length_units_SI, element["outer radius"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t spherical \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    aux1 + "\t" +
                    str(r_in) + "\t" +
                    str(r_out) + "\t" +
                    aux2)
        elif element["subtype"] == "assigned HTC":
            aux2 = "\t!HTC, A\n"
            htc = unit_conversion('W/m**2/K', element["convection htc"][1], htc_unit,
                                  element["convection htc"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t convection \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(htc) + "\t" +
                    str(area) + "\t" +
                    aux2)
        elif element["subtype"] == "pipe/duct":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            DHI = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                  element["characteristic length"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t IFCduct \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(velocity) + "\t" +
                    str(DHI) + "\t" +
                    str(area) + "\t" +
                    "\t!material, velocity[m/s], Dh[m], A[m²]\n")
        elif element["subtype"] == "Cylinder":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            diameter = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                       element["characteristic length"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t EFCcyl \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(velocity) + "\t" +
                    str(diameter) + "\t" +
                    str(area) + "\t" +
                    "\t!material, velocity[m/s], D[m], A[m²]\n")
        elif element["subtype"] == "Diamond/Square":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            length = unit_conversion('m', element["width"][1], length_units_SI, element["width"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t EFCdiamond \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(velocity) + "\t" +
                    str(length) + "\t" +
                    str(area) + "\t" +
                    "\t!material, velocity[m/s], D[m], A[m²]\n")
        elif element["subtype"] == "Impinging Round jet":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            diameter = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                       element["characteristic length"][0])
            height = unit_conversion('m', element["height"][1], length_units_SI, element["height"][0])
            radius = unit_conversion('m', element["radius"][1], length_units_SI, element["radius"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t EFCimpjet \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(velocity) + "\t" +
                    str(diameter) + "\t" +
                    str(height) + "\t" +
                    str(radius) + "\t" +
                    "\t!material, velocity[m/s] D[m], H[m], r[m]\n")
        elif element["subtype"] == "Flat Plate":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            x_begin = unit_conversion('m', element["x begin"][1], length_units_SI, element["x begin"][0])
            x_end = unit_conversion('m', element["x end"][1], length_units_SI, element["x end"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t EFCplate \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(x_begin) + "\t" +
                    str(x_end) + "\t" +
                    str(velocity) + "\t" +
                    str(area) + "\t" +
                    "\t!material, velocity[m/s], X begin[m], X end[m], A[m²]\n")
        elif element["subtype"] == "EFC Sphere":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            diameter = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                       element["characteristic length"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t EFCsphere \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(velocity) + "\t" +
                    str(diameter) + "\t" +
                    "\t!material, velocity[m], D[m]\n")
        elif element["subtype"] == "Vertical rectangular enclosure":
            width = unit_conversion('m', element["width"][1], length_units_SI, element["width"][0])
            height = unit_conversion('m', element["height"][1], length_units_SI, element["height"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t INCvenc \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(width) + "\t" +
                    str(height) + "\t" +
                    str(area) + "\t" +
                    "\t!material, W[m], H[m], A[m²]\n")
        elif element["subtype"] == "ENC Horizontal cylinder":
            diameter = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                       element["characteristic length"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t ENChcyl \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(diameter) + "\t" +
                    str(area) + "\t" +
                    "\t!material, D[m], A[m²]\n")
        elif element["subtype"] == "Horizontal plate facing down":
            length = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                     element["characteristic length"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t ENChplatedown \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(length) + "\t" +
                    str(area) + "\t" +
                    "\t!material, L=A/P[m], A[m²]\n")
        elif element["subtype"] == "Horizontal plate facing up":
            length = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                     element["characteristic length"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t ENChplateup \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(length) + "\t" +
                    str(area) + "\t"
                                "\t!material, L=A/P[m], A[m²]\n")
        elif element["subtype"] == "Inclined plate facing down":
            height = unit_conversion('m', element["height"][1], length_units_SI, element["height"][0])
            length = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                     element["characteristic length"][0])
            angle = unit_conversion('degree', element["angle theta"][1], angle_units, element["angle theta"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t ENCiplatedown \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(height) + "\t" +
                    str(length) + "\t" +
                    str(angle) + "\t" +
                    str(area) + "\t"
                                "\t!material, H[m], L=A/P[m], angle[°], A[m²]\n")
        elif element["subtype"] == "Inclined plate facing up":
            height = unit_conversion('m', element["height"][1], length_units_SI, element["height"][0])
            length = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                     element["characteristic length"][0])
            angle = unit_conversion('degree', element["angle theta"][1], angle_units, element["angle theta"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t ENCiplateup \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(height) + "\t" +
                    str(length) + "\t" +
                    str(angle) + "\t" +
                    str(area) + "\t"
                                "\t!material, H[m], L=A/P[m], angle[°], A[m²]\n")
        elif element["subtype"] == "ENC Sphere":
            diameter = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                       element["characteristic length"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t ENCsphere \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(diameter) + "\t" +
                    "\t!material, D[m]\n")
        elif element["subtype"] == "Vertical flat plate":
            length = unit_conversion('m', element["characteristic length"][1], length_units_SI,
                                     element["characteristic length"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t ENCvplate \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(length) + "\t" +
                    str(area) + "\t"
                                "\t!material, L[m], A[m²]\n")
        elif element["subtype"] == "Surface Radiation":
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t surfrad \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["emissivity"][0]) + "\t" +
                    str(area) + "\t"
                                "\t!emissivity, A[m²]\n")
        elif element["subtype"] == "Radiation":
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t radiation \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["exchange factor 12"]) + "\t" +
                    str(element["exchange factor 21"]) + "\t" +
                    str(area) + "\t"
                                "\t! script-F, A[m²]\n")
        elif element["subtype"] == "Advection":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t advection \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(velocity) + "\t" +
                    str(area) + "\t"
                                "\t! material, velocity[m/s], A[m²]\n")
        elif element["subtype"] == "Outflow":
            velocity = unit_conversion('m/s', element["velocity"][1], velocity_unit, element["velocity"][0])
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t outflow \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["material"]).replace(' ', '_') + "\t" +
                    str(velocity) + "\t" +
                    str(area) + "\t"
                                "\t! material, velocity[m/s], A[m²]\n")
    f.write("End Conductors \n")

    # ---------- Boundary Conditions Section  ----------

    f.write(separator)
    f.write("Begin Boundary Conditions \n")
    for key in nodes.keys():
        node = nodes[key]
        if node["type"] == "Temperature":
            if node["time function"] == "const":
                temperature = unit_conversion('degC', node["temperature"][1], temperature_unit,
                                              node["temperature"][0])
            else:
                temperature = node["temperature"][0]
            f.write("   fixed_T\t" +
                    str(temperature) + "\t" +
                    str(node["ID"]) + "\t! " +
                    str(node["comment"]) + "\t! temperature [°C], node ID\n")
        elif node["type"] == "Heat Flux":
            area = unit_conversion('m**2', node["area"][1], area_unit_SI, node["area"][0])
            if node["time function"] == "const":
                h_flux = unit_conversion('W/m**2', node["heat flux"][1], heat_flux_unit, node["heat flux"][0])
            else:
                h_flux = node["heat flux"][0]
            f.write("   heat_flux\t" +
                    str(h_flux) + "\t" +
                    str(area) + "\t" +
                    str(node["ID"]) + "\t! " +
                    str(node["comment"]) + "\t! heat_flux [W/m²], node ID\n")
    f.write("End Boundary Conditions \n")

    # ---------- Sources Section  ----------

    f.write(separator)
    f.write("Begin Sources \n")
    if nodes.keys():
        for key in nodes.keys():
            node = nodes[key]
            if node["type"] == "Volumetric heat source":
                volumetric_power = unit_conversion('W/m**3', node["volumetric power"][1], volumetric_power_unit,
                                                   node["volumetric power"][0])
                f.write("   qdot\t" +
                        str(volumetric_power) + "\t" +
                        str(node["ID"]) + "\t! " +
                        str(node["comment"]) + "\t! volumetric power [W/m³], node ID\n")
            elif node["type"] == "Total Heat source":
                power = unit_conversion('W', node["power"][1], power_unit, node["power"][0])
                f.write("   Qsrc\t" +
                        str(power) + "\t" +
                        str(node["ID"]) + "\t! " +
                        str(node["comment"]) + "\t! power[W], node ID\n")
            elif node["type"] == "Thermostatic heat source":
                power = unit_conversion('W', node["power"][1], power_unit, node["power"][0])
                temp_on = unit_conversion('degC', node["temperature on"][1], temperature_unit,
                                          node["temperature on"][0])
                temp_off = unit_conversion('degC', node["temperature off"][1], temperature_unit,
                                           node["temperature off"][0])
                f.write("   tstatQ\t" +
                        str(power) + "\t" +
                        str(node["thermostatic node id"]) + "\t" +
                        str(temp_on) + "\t" +
                        str(temp_off) + "\t" +
                        str(node["ID"]) + "\t" +
                        "! Power [W], thermostat node_ID, Ton [°C], Toff [°C], node_ID\n")
            else:
                pass
    else:
        f.write("   ! No sources present in the database.\n")
    f.write("End Sources \n")

    # ----------  Initial Conditions Section  ----------

    f.write(separator)
    f.write("Begin Initial Conditions \n")
    if initialize:
        f.write("  {} all\n".format(solution.initial_temperature))
    else:
        f.write("  20.0 all\ttemperature[°C], all internal nodes\n")
    f.write("End Initial Conditions \n")

    """
     ----------  Radiation Enclosure Section  ----------
    f.write(separator)
    f.write("Begin Radiation Enclosure \n")
    ...
    f.write("End Radiation Enclosure \n")
    """

    # ----------  Functions Section  ----------
    """ functions = {'new': {'abscissa': None,
                             'ordinate': None,
                             'physic_property': None,
                             'property_unit': None,
                             'time_unit': None,
                             'option': None}} """
    fn_list = list(functions.keys())
    if 'new' in fn_list:
        fn_list.remove('new')
    if fn_list:  # check if there are functions stored
        f.write(separator)
        f.write("Begin Functions \n")
        for fn in fn_list:
            if functions[fn]['option'] == 'Constant':
                f.write("  Begin Constant\t" + fn + "\n")
                if functions[fn]['physic_property'] == "temperature":
                    fx = unit_conversion('degC', functions[fn]['property_unit'], temperature_unit,
                                         functions[fn]['ordinate'][0])
                elif functions[fn]['physic_property'] == "heat flux":
                    fx = unit_conversion('W/m**2', functions[fn]['property_unit'], heat_flux_unit,
                                         functions[fn]['ordinate'][0])
                elif functions[fn]['physic_property'] == "volumetric power":
                    fx = unit_conversion('W/m**3', functions[fn]['property_unit'], volumetric_power_unit,
                                         functions[fn]['ordinate'][0])
                elif functions[fn]['physic_property'] == "power":
                    fx = unit_conversion('W', functions[fn]['property_unit'], power_unit,
                                         functions[fn]['ordinate'][0])
                else:
                    print("ERROR: function not defined yet - check: " + fn)
                f.write("    " + str(fx) + "\t!value\n")
                f.write("  End Constant " + fn + "\n")
            elif functions[fn]['option'][:4] == 'Time':
                f.write("  Begin " + functions[fn]['option'] + "\t" + fn + "\n")
                for idx in range(len(functions[fn]['abscissa'])):
                    t = unit_conversion('s', functions[fn]['time_unit'], time_unit,
                                        functions[fn]['abscissa'][idx])
                    if functions[fn]['physic_property'] == "temperature":
                        fx = unit_conversion('degC', functions[fn]['property_unit'], temperature_unit,
                                             functions[fn]['ordinate'][idx])
                    elif functions[fn]['physic_property'] == "heat flux":
                        fx = unit_conversion('W/m**2', functions[fn]['property_unit'], heat_flux_unit,
                                             functions[fn]['ordinate'][idx])
                    elif functions[fn]['physic_property'] == "volumetric power":
                        fx = unit_conversion('W/m**3', functions[fn]['property_unit'], volumetric_power_unit,
                                             functions[fn]['ordinate'][idx])
                    elif functions[fn]['physic_property'] == "power":
                        fx = unit_conversion('W', functions[fn]['property_unit'], power_unit,
                                             functions[fn]['ordinate'][idx])
                    else:
                        print("ERROR: function not defined yet - check: " + fn)
                    f.write("    " + str(t) + "\t" + str(fx) + "\t!time, value\n")
                f.write("  End " + functions[fn]['option'] + "\t" + fn + "\n")
        f.write("End Functions \n")
    else:
        f.write("   ! No user defined functions present in the database.\n")

    # ----------  Material Section  ----------

    f.write(separator)
    mat_list = [x for x in all_mat_list if x not in material_list]
    if mat_list:  # check if there are functions stored on top of the default
        for mat in mat_list:
            f.write("Begin Material\t" + mat.casefold() + "\n")
            prop_keys = materials[mat].keys()
            f.write('\n')
            f.write("  State = " + materials[mat]['State']['value'] + "\n\n")

            if 'Gas_Constant' in prop_keys:
                if materials[mat]['Gas_Constant']['type'] == 'scalar':
                    parameter = float(materials[mat]['Gas_Constant']['value'])
                    f.write("  Gas Constant = " + str(parameter) + "! constant value\n\n")
                else:
                    f.write('  ERROR: The Gas Constant must be defined as a constant!\n\n')
            elif materials[mat]['State']['value'] == 'Gas':
                f.write('  !WARNING: the Gas Constant is not defined!\n\n')

            if 'Mass_Density' in prop_keys:
                if materials[mat]['Mass_Density']['type'] == 'scalar':
                    parameter = float(materials[mat]['Mass_Density']['value'])
                    # The density is supposed to be already converted in the SI units
                    f.write("  Density = " + str(parameter) + "\t! constant value\n\n")
                elif materials[mat]['Mass_Density']['type'] == 'table':
                    f.write("  Density Table\n")
                    for idx in range(len(materials[mat]['Mass_Density']['qualifier_data'])):
                        temp = materials[mat]['Mass_Density']['qualifier_data'][idx]
                        parameter = materials[mat]['Mass_Density']['param_data'][idx]
                        f.write('  ' + str(round(temp, 1)) + '\t' + str(round(parameter, 6)) +
                                '\t!temperature, density\n')
                    f.write('  End Density Table\n\n')
                else:
                    f.write('  ERROR: thermal conductivity must be defined as table, constant or spline!\n\n')
            else:
                f.write('  !WARNING: the Density is not defined!\n\n')

            if 'Thermal_Conductivity' in prop_keys:
                if materials[mat]['Thermal_Conductivity']['type'] == 'scalar':
                    parameter = float(materials[mat]['Thermal_Conductivity']['value'])
                    f.write("  Conductivity = " + str(parameter) + "\t!constant value\n\n")
                elif materials[mat]['Thermal_Conductivity']['type'] == 'table':
                    f.write("  Conductivity Table\n")
                    for idx in range(len(materials[mat]['Thermal_Conductivity']['qualifier_data'])):
                        temp = materials[mat]['Thermal_Conductivity']['qualifier_data'][idx]
                        parameter = materials[mat]['Thermal_Conductivity']['param_data'][idx]
                        f.write('  ' + str(round(temp, 1)) + '\t' + str(round(parameter, 6)) +
                                '\t!temperature, thermal conductivity\n')
                    f.write('  End Conductivity Table\n\n')
                else:
                    f.write('  ERROR: thermal conductivity must be defined as table, constant or spline!\n\n')
            else:
                f.write('  !WARNING: the thermal conductivity is not defined!\n\n')

            if 'Specific_Heat' in prop_keys:
                if materials[mat]['Specific_Heat']['type'] == 'scalar':
                    parameter = float(materials[mat]['Specific_Heat']['value'])
                    if materials[mat]['State']['value'] in ['Solid', 'Liquid']:
                        f.write("  c_v = " + str(parameter) + "\t!constant value\n\n")
                    else:
                        f.write("  c_p = " + str(parameter) + "\t!constant value\n\n")
                elif materials[mat]['Specific_Heat']['type'] == 'table':
                    if materials[mat]['State']['value'] in ['Solid', 'Liquid']:
                        f.write("  c_v Table\n")
                    else:
                        f.write("  c_p Table\n")
                    for idx in range(len(materials[mat]['Specific_Heat']['qualifier_data'])):
                        temp = materials[mat]['Specific_Heat']['qualifier_data'][idx]
                        parameter = materials[mat]['Specific_Heat']['param_data'][idx]
                        f.write('  ' + str(round(temp, 1)) + '\t' + str(round(parameter, 6)) +
                                '\t!temperature, Specific Heat\n')
                    if materials[mat]['State']['value'] in ['Solid', 'Liquid']:
                        f.write('  End c_v Table\n\n')
                    else:
                        f.write('  End c_p Table\n\n')
                else:
                    f.write('  ERROR: specific heat must be defined as table, constant or spline!\n\n')
            elif materials[mat]['State']['value'].lower != 'solid':
                f.write('  !WARNING: the Specific Heat is not defined!\n\n')
            else:
                pass

            if 'Dynamic_Viscosity' in prop_keys:
                if materials[mat]['Dynamic_Viscosity']['type'] == 'scalar':
                    parameter = float(materials[mat]['Dynamic_Viscosity']['value'])
                    f.write("  Viscosity = " + str(parameter) + "\t!constant value\n\n")
                elif materials[mat]['Dynamic_Viscosity']['type'] == 'table':
                    f.write("  Viscosity Table\n")
                    for idx in range(len(materials[mat]['Dynamic_Viscosity']['qualifier_data'])):
                        temp = materials[mat]['Dynamic_Viscosity']['qualifier_data'][idx]
                        parameter = materials[mat]['Dynamic_Viscosity']['param_data'][idx]
                        f.write('  ' + str(round(temp, 1)) + '\t' + str(round(parameter, 6)) +
                                '\t!temperature, dynamic viscosity\n')
                    f.write('  End viscosity Table\n\n')
                else:
                    f.write('  ERROR: Dynamic Viscosity must be defined as table, constant or spline!\n\n')
            elif materials[mat]['State']['value'] != 'Solid':
                f.write('  !WARNING: the Dynamic Viscosity is not defined!\n\n')
            else:
                pass

            if 'Thermal_Expansion' in prop_keys:
                if materials[mat]['Thermal_Expansion']['type'] == 'scalar':
                    parameter = float(materials[mat]['Thermal_Expansion']['value'])
                    f.write("  Beta = " + str(parameter) + "\t!constant value\n\n")
                elif materials[mat]['Thermal_Expansion']['type'] == 'table':
                    f.write("  Beta Table\n")
                    for idx in range(len(materials[mat]['Thermal_Expansion']['qualifier_data'])):
                        temp = materials[mat]['Thermal_Expansion']['qualifier_data'][idx]
                        parameter = materials[mat]['Thermal_Expansion']['param_data'][idx]
                        f.write('  ' + str(round(temp, 1)) + '\t' + str(round(parameter, 6)) +
                                '\t!temperature, thermal expansion\n')
                    f.write('  End Beta Table\n\n')
                else:
                    f.write('  ERROR: Thermal Expansion must be defined as table, constant or spline!\n\n')
            else:
                f.write('  !WARNING: the Thermal Expansion is not defined!\n\n')

            if 'Prandtl_Number' in prop_keys:
                if materials[mat]['Prandtl_Number']['type'] == 'scalar':
                    parameter = float(materials[mat]['Prandtl_Number']['value'])
                    f.write("  Pr = " + str(parameter) + "\t!constant value\n\n")
                elif materials[mat]['Prandtl_Number']['type'] == 'table':
                    f.write("  Pr Table\n")
                    for idx in range(len(materials[mat]['Prandtl_Number']['qualifier_data'])):
                        temp = materials[mat]['Prandtl_Number']['qualifier_data'][idx]
                        parameter = materials[mat]['Prandtl_Number']['param_data'][idx]
                        f.write('  ' + str(round(temp, 1)) + '\t' + str(round(parameter, 6)) +
                                '\t!temperature, Prandtl number\n')
                    f.write('  End Pr Table\n\n')
                else:
                    f.write('  ERROR: Prandtl Number must be defined as table, constant or spline!\n\n')
            elif materials[mat]['State']['value'] != 'Solid':
                f.write('  !WARNING: the Prandtl_Number is not defined!\n\n')
            else:
                pass

            f.write("End Material " + mat.casefold() + "\n\n")
    else:
        f.write("   ! No additional materials imported in the database.\n")
    f.write("! EOF\n")
    f.close()
