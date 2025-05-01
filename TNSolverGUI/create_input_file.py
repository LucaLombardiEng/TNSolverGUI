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

from datetime import date, datetime
from gUtility import material_list
from gUtility import angle_units, htc_unit, length_units_SI, area_unit_SI, volume_unit_SI
from gUtility import density_unit_SI, specific_heat_unit, velocity_unit, temperature_unit
from gUtility import volumetric_power_unit, power_unit, thermal_conductivity_unit
from pint import UnitRegistry
from TNSolver_code.utility_functions import setunits


def unit_conversion(to_unit, from_unit, unit_table, from_value):
    u_reg = UnitRegistry

    from_index = unit_table[0].index(from_unit)
    to_index = unit_table[1].index(to_unit)

    from_value = float(from_value)
    from_magnitude = u_reg.Quantity(from_value, unit_table[1][from_index])

    to_magnitude = from_magnitude.to(unit_table[1][to_index])

    return to_magnitude.magnitude


def TNSolver_input_file_gen(filename, solution, nodes, elements, initialize):
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
        if node["material"] in material_list[1:]:
            f.write("   " + str(node["ID"]) + "\t" +
                    str(node["material"]) + "\t" +
                    str(volume) + "\t! " +
                    str(node["comment"]) + "\n")
        else:
            density = unit_conversion('kg/m**3', node["density"][1], density_unit_SI, node["density"][0])
            Specific_Heat = unit_conversion('J/kg/K', node["specific Heat"][1],
                                            specific_heat_unit, node["specific Heat"][0])

            aux = density * Specific_Heat
            f.write("   " + str(node["ID"]) + "\t" +
                    str(aux) + "\t" +
                    str(volume) + "\t! " +
                    str(node["comment"]) + "\n")

    f.write("End Nodes \n")

    # ---------- Conductors Section  ----------

    f.write(separator)
    f.write("Begin Conductors \n")
    for key in elements.keys():
        element = elements[key]
        if element["subtype"] == "Linear conduction":
            if element["material"] in material_list[1:]:
                aux1 = str(element["material"]).replace(' ', '_') 
                aux2 = " ! material, L, A \n"
            else:
                k = unit_conversion('W/m/K', element["thermal conductivity"][1], thermal_conductivity_unit,
                                    element["thermal conductivity"][0])
                aux1 = str(k)
                aux2 = " ! k, L, A \n"

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
            if element["material"] in material_list[1:]:
                aux1 = str(element["material"]).replace(' ', '_') 
                aux2 = " ! material, ri, ro, L \n"
            else:
                k = unit_conversion('W/m/K', element["thermal conductivity"][1], thermal_conductivity_unit,
                                    element["thermal conductivity"][0])
                aux1 = str(k)
                aux2 = " ! k, ri, ro, L \n"
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
            if element["material"] in material_list[1:]:
                aux1 = str(element["material"]).replace(' ', '_') 
                aux2 = " ! material, ri, ro \n"
            else:
                k = unit_conversion('W/m/K', element["thermal conductivity"][1], thermal_conductivity_unit,
                                    element["thermal conductivity"][0])
                aux1 = str(k)
                aux2 = " ! k, ri, ro \n"
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
            aux2 = " ! HTC, A\n"
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
                    " ! material, velocity, Dh, A\n")
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
                    " ! material, velocity, D, A\n")
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
                    " ! material, velocity, D, A\n")
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
                    " ! material, velocity, D, H, r\n")
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
                    " ! material, velocity, X begin, X end, A\n")
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
                    " ! material, velocity, D\n")
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
                    " ! material, W, H, A\n")
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
                    " ! material, D, A\n")
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
                    " ! material, L=A/P, A\n")
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
                    " ! material, L=A/P, A\n")
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
                    " ! material, H, L=A/P, angle, A\n")
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
                    " ! material, H, L=A/P, angle, A\n")
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
                    " ! material, D\n")
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
                    " ! material, L, A\n")
        elif element["subtype"] == "Surface Radiation":
            area = unit_conversion('m**2', element["area"][1], area_unit_SI, element["area"][0])
            f.write("   " +
                    str(element["ID"]) +
                    "\t surfrad \t" +
                    str(element["inlet node id"]) + "\t" +
                    str(element["exit node id"]) + "\t" +
                    str(element["emissivity"][0]) + "\t" +
                    str(area) + "\t" 
                    " ! emissivity, A\n")
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
                    " !  script-F, A\n")
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
                    " !  material, velocity, A\n")
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
                    " !  material, velocity, A\n")

    f.write("End Conductors \n")

    # ---------- Boundary Conditions Section  ----------

    f.write(separator)
    f.write("Begin Boundary Conditions \n")
    for key in nodes.keys():
        node = nodes[key]
        if node["type"] == "Temperature":
            temperature = unit_conversion('degC', node["temperature"][1], temperature_unit,
                                          node["temperature"][0])
            f.write("   fixed_T\t" +
                    str(temperature) + "\t" +
                    str(node["ID"]) + "\t! " +
                    str(node["comment"]) + "\n")
        elif node["type"] == "Heat Flux":
            area = unit_conversion('m**2', node["area"][1], area_unit_SI, node["area"][0])
            f.write("   heat_flux\t" +
                    str(node["heat flux"][0]) + "\t" +
                    str(area) + "\t" +
                    str(node["ID"]) + "\t! " +
                    str(node["comment"]) + "\n")
    f.write("End Boundary Conditions \n")

    # ---------- Sources Section  ----------

    f.write(separator)
    f.write("Begin Sources \n")
    for key in nodes.keys():
        node = nodes[key]
        if node["type"] == "Volumetric heat source":
            volumetric_power = unit_conversion('W/m**3', node["volumetric power"][1], volumetric_power_unit,
                                               node["volumetric power"][0])
            f.write("   qdot\t" +
                    str(volumetric_power) + "\t" +
                    str(node["ID"]) + "\t! " +
                    str(node["comment"]) + "\n")
        elif node["type"] == "Total Heat source":
            power = unit_conversion('W', node["power"][1], power_unit, node["power"][0])
            f.write("   Qsrc\t" +
                    str(power) + "\t" +
                    str(node["ID"]) + "\t! " +
                    str(node["comment"]) + "\n")
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
                    "! Power, thermostat node, Ton, Toff\n")

        else:
            pass
    f.write("End Sources \n")

    # ----------  Initial Conditions Section  ----------

    f.write(separator)
    f.write("Begin Initial Conditions \n")
    if initialize:
        f.write("  {} all\n".format(solution.initial_temperature))
    else:
        f.write("  20.0 all\n")
    f.write("End Initial Conditions \n")

    # ----------  Radiation Enclosure Section  ----------

    f.write(separator)
    f.write("Begin Radiation Enclosure \n")

    f.write("End Radiation Enclosure \n")

    # ----------  Functions Section  ----------

    f.write(separator)
    f.write("Begin Functions \n")

    f.write("End Functions \n")

    # ----------  Material Section  ----------

    f.write(separator)
    f.write("Begin Material \n")

    f.write("End Material \n")

    f.close()
