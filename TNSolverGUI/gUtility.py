"""
 This is a collection of general utilities that will be used in the GUI core

 Open Issues:
 The material list shall be connected with the material_library.py section where the material library is defined

"""

working_folder_path = "C:/Users/Luca_Lombardi/Documents/My Python/Test_Gui"

elmsize = 25
nodesize = 25
font = "Arial"
font_size = 10
digits = 3

dxf_color = 'bisque'

color_list = ("red", "green", "dodgerblue", "yellow", "white", "darkviolet", "magenta")

node_type = ('Internal Node', 'Temperature', 'Heat Flux', 'Volumetric heat source', 'Total Heat source',
             'Thermostatic heat source')

elm_type = {'Conduction': ('Linear conduction', 'Cylindrical conduction', 'Spherical conduction'),
            'Convection': ('UDC: assigned HTC',
                           'IFC: pipe/duct',
                           'EFC: Cylinder',
                           'EFC: Diamond/Square',
                           'EFC: Impinging Round jet',
                           'EFC: Flat Plate',
                           'EFC: EFC Sphere',
                           'INC: Vertical rectangular enclosure',
                           'ENC: Horizontal cylinder',
                           'ENC: Horizontal plate facing down',
                           'ENC: Horizontal plate facing up',
                           'ENC: Inclined plate facing down',
                           'ENC: Inclined plate facing up',
                           'ENC: ENC Sphere',
                           'ENC: Vertical flat plate'),
            'Radiation': ('Surface Radiation', 'Radiation'),
            'Advection': ('Advection', 'Outflow')}

material_list = ("user defined", "air", "water", "steel")
fluid_list = ("air", "water")

time_unit = ('ms', 's', 'm', 'h')

angle_units = (('°', 'rad'),
               ('degree', 'rad'))

length_units_SI = (('um', 'mm', 'cm', 'm'),
                   ('micrometer', 'mm', 'cm', 'm'))
area_unit_SI = (('mm\N{SUPERSCRIPT TWO}', 'cm\N{SUPERSCRIPT TWO}', 'm\N{SUPERSCRIPT TWO}'),
                ('mm**2', 'cm**2', 'm**2'))

volume_unit_SI = (('mm\N{SUPERSCRIPT THREE}', 'cm\N{SUPERSCRIPT THREE}', 'm\N{SUPERSCRIPT THREE}'),
                  ('mm**3', 'cm**3', 'm**3'))

temperature_unit = (('°C', '°F', 'K', 'R'),
                    ('degC', 'degF', 'kelvin', 'degR'))

density_unit_SI = (('kg/m\N{SUPERSCRIPT THREE}', 'g/cm\N{SUPERSCRIPT THREE}', 'kg/L', 'g/L'),
                   ('kg/m**3', 'g/cm**3', 'kg/L', 'g/L'))

specific_heat_unit = (('J/kg·°C', 'J/kg·K', 'J/g·°C', 'kJ/kg·°C', 'kJ/g·°C'),
                      ('J/kg/degC', 'J/kg/K', 'J/g/degC', 'kJ/kg/degC', 'kJ/g/degC'))

heat_flux_unit = (('W/m\N{SUPERSCRIPT TWO}', 'kW/m\N{SUPERSCRIPT TWO}', 'W/cm\N{SUPERSCRIPT TWO}',
                   'W/mm\N{SUPERSCRIPT TWO}' ),
                  ('W/m**2', 'kW/m**2', 'W/cm**2', 'W/mm**2'))

volumetric_power_unit = (('W/m\N{SUPERSCRIPT THREE}', 'kW/m\N{SUPERSCRIPT THREE}', 'W/cm\N{SUPERSCRIPT THREE}',
                          'W/mm\N{SUPERSCRIPT THREE}'),
                         ('W/m**3', 'kW/m**3', 'W/cm**3', 'W/mm**3'))

power_unit = (('kW', 'W', 'mW', 'μW'),
              ('kW', 'W', 'mW', 'microW'))

thermal_conductivity_unit = (('W/m·°C', 'W/m·K', 'W/cm·K', 'W/mm·K'),
                             ('W/m/degC', 'W/m/K', 'W/cm/K', 'W/mm/K'))

velocity_unit = (('m/s', 'km/h', 'cm/s', 'mm/s'),
                 ('m/s', 'km/h', 'cm/s', 'mm/s'))

htc_unit = (('W/m\N{SUPERSCRIPT TWO}·°C', 'W/m\N{SUPERSCRIPT TWO}·K', 'W/cm\N{SUPERSCRIPT TWO}·K',
             'W/mm\N{SUPERSCRIPT TWO}·K', 'kW/m\N{SUPERSCRIPT TWO}·K'),
            ('W/m**2/degC', 'W/m**2/K', 'W/cm**2/K', 'W/mm**2/K', 'kW/m**2/K'))


def get_elm_color(elmType):
    match elmType:
        case "Conduction":
            return color_list[0]
        case "Convection":
            return color_list[1]
        case "Radiation":
            return color_list[3]
        case "Advection":
            return color_list[2]
        # If an exact match is not confirmed, this last case will be used if provided
        case _:
            return color_list[6]


def get_node_color(node_type):
    match node_type:
        case "Internal Node":
            return color_list[4]
        case "Temperature":
            return color_list[0]
        case "Heat Flux":
            return color_list[1]
        case "Volumetric heat source":
            return color_list[2]
        case "Total Heat source":
            return color_list[3]
        case "Thermostatic heat source":
            return color_list[5]
        # If an exact match is not confirmed, this last case will be used if provided
        case _:
            return color_list[6]
