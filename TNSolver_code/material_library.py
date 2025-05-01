import numpy as np


# Material Property Library Initialization
class Material:
    def __init__(self):
        self.name = ''
        self.state = None
        self.ref = None
        self.ktype = None
        self.kunits = None
        self.kdata = None
        self.krange = None
        self.rhotype = None
        self.rhounits = None
        self.rhodata = None
        self.rhorange = None
        self.cptype = None
        self.cpunits = None
        self.cpdata = None
        self.cprange = None
        self.cvtype = None
        self.cvunits = None
        self.cvdata = None
        self.cvrange = None
        self.mutype = None
        self.muunits = None
        self.mudata = None
        self.murange = None
        self.betatype = None
        self.betaunits = None
        self.betadata = None
        self.betarange = None
        self.Prtype = None
        self.Prunits = None
        self.Prdata = None
        self.Prrange = None
        self.R = None
        self.Runits = None


def matlib():
    mat_state_dict = {'SOLID': 1,
                      'LIQUID': 2,
                      'GAS': 3}

    data_type_dict = {'CONST': 1,
                      'TABLE': 2,
                      'SPLINE': 3,
                      'POLY': 4,
                      'USER': 5}
    mat = [air_def(mat_state_dict, data_type_dict), water_def(mat_state_dict, data_type_dict),
           steel_def(mat_state_dict, data_type_dict), fir_def(mat_state_dict, data_type_dict)]

    return mat


def air_def(state, d_type):
    # Create the air material
    air = Material()
    air.name = 'air'
    air.state = state['GAS']
    air.ref = ("Table A.6, page 718, in:\n"
               "J. H. Lienhard, IV and J. H. Lienhard, V. A Heat Transfer Textbook.\n"
               "  Phlogiston Press, Cambridge, Massachusetts, fourth edition, 2012.\n"
               "  version 2.02, available at: http://ahtt.mit.edu\n")
    air.ktype = d_type['SPLINE']
    air.kunits = ['(K)', '(W/m-K)']
    air.kdata = np.array([[100.0, 0.00941],
                          [150.0, 0.01406],
                          [200.0, 0.01836],
                          [250.0, 0.02241],
                          [260.0, 0.02329],
                          [280.0, 0.02473],
                          [300.0, 0.02623],
                          [320.0, 0.02753],
                          [340.0, 0.02888],
                          [350.0, 0.02984],
                          [400.0, 0.03328],
                          [450.0, 0.03656]])
    air.rhotype = d_type['SPLINE']
    air.rhounits = ['(K)', '(kg/m^3)']
    air.rhodata = np.array([[100.0, 3.605],
                            [150.0, 2.368],
                            [200.0, 1.769],
                            [250.0, 1.412],
                            [260.0, 1.358],
                            [280.0, 1.261],
                            [300.0, 1.177],
                            [320.0, 1.103],
                            [340.0, 1.038],
                            [350.0, 1.008],
                            [400.0, 0.8821],
                            [450.0, 0.7840]])
    air.cptype = d_type['SPLINE']
    air.cpunits = ['(K)', '(J/kg-K)']
    air.cpdata = np.array([[100.0, 1039.0],
                           [150.0, 1012.0],
                           [200.0, 1007.0],
                           [250.0, 1006.0],
                           [260.0, 1006.0],
                           [280.0, 1006.0],
                           [300.0, 1007.0],
                           [320.0, 1008.0],
                           [340.0, 1009.0],
                           [350.0, 1009.0],
                           [400.0, 1014.0],
                           [450.0, 1021.0]])
    air.cvtype = d_type['SPLINE']
    air.cvunits = ['(K)', '(J/kg-K)']
    air.cvdata = np.array([[100.0, 728.1930],
                           [150.0, 717.5362],
                           [200.0, 716.1623],
                           [250.0, 716.4042],
                           [260.0, 716.6014],
                           [280.0, 717.1636],
                           [300.0, 717.9716],
                           [320.0, 719.0505],
                           [340.0, 720.4217],
                           [350.0, 721.2220],
                           [400.0, 726.4106],
                           [450.0, 733.5475]])
    air.mutype = d_type['SPLINE']
    air.muunits = ['(K)', '(kg/m-s)']
    air.mudata = np.array([[100.0, 0.711e-5],
                           [150.0, 1.035e-5],
                           [200.0, 1.333e-5],
                           [250.0, 1.606e-5],
                           [260.0, 1.649e-5],
                           [280.0, 1.747e-5],
                           [300.0, 1.857e-5],
                           [320.0, 1.935e-5],
                           [340.0, 2.025e-5],
                           [350.0, 2.090e-5],
                           [400.0, 2.310e-5],
                           [450.0, 2.517e-5]])
    air.betatype = d_type['SPLINE']
    air.betaunits = ['(K)', '(1/K)']
    air.betadata = np.array([[100.0, 10.000e-3],
                             [150.0, 6.667e-3],
                             [200.0, 5.000e-3],
                             [250.0, 4.000e-3],
                             [260.0, 3.846e-3],
                             [280.0, 3.571e-3],
                             [300.0, 3.333e-3],
                             [320.0, 3.125e-3],
                             [340.0, 2.941e-3],
                             [350.0, 2.857e-3],
                             [400.0, 2.500e-3],
                             [450.0, 2.222e-3]])
    air.Prtype = d_type['SPLINE']
    air.Prunits = ['(K)', '(dimensionless)']
    air.Prdata = np.array([[100.0, 0.784],
                           [150.0, 0.745],
                           [200.0, 0.731],
                           [250.0, 0.721],
                           [260.0, 0.712],
                           [280.0, 0.711],
                           [300.0, 0.713],
                           [320.0, 0.708],
                           [340.0, 0.707],
                           [350.0, 0.707],
                           [400.0, 0.704],
                           [450.0, 0.703]])
    return air


def water_def(state, d_type):
    # Create the water material
    water = Material()
    water.name = 'water'
    water.state = state['LIQUID']
    water.ref = ("Table A.3, page 713, in:\n"
                 "J. H. Lienhard, IV and J. H. Lienhard, V. A Heat Transfer Textbook.\n"
                 "Phlogiston Press, Cambridge, Massachusetts, fourth edition, 2012.\n"
                 "version 2.02, available at: http://ahtt.mit.edu\n")
    water.ktype = d_type['SPLINE']
    water.kunits = ['(K)', '(W/m-K)']
    water.kdata = np.array([[273.15, 0.5610],
                            [275.0, 0.5645],
                            [285.0, 0.5835],
                            [295.0, 0.6017],
                            [305.0, 0.6184],
                            [320.0, 0.6396],
                            [340.0, 0.6605],
                            [360.0, 0.6737],
                            [373.15, 0.6791]])
    water.rhotype = d_type['SPLINE']
    water.rhounits = ['(K)', '(kg/m^3)']
    water.rhodata = np.array([[273.15, 999.8],
                              [275.0,  999.9],
                              [285.0,  999.5],
                              [295.0,  997.8],
                              [305.0,  995.0],
                              [320.0,  989.3],
                              [340.0,  979.5],
                              [360.0,  967.4],
                              [373.15, 958.3]])
    water.cvtype = d_type['SPLINE']
    water.cvunits = ['(K)', '(J/kg-K)']
    water.cvdata = np.array([[273.15, 4220.0],
                             [275.0,  4214.0],
                             [285.0,  4193.0],
                             [295.0,  4183.0],
                             [305.0,  4180.0],
                             [320.0,  4181.0],
                             [340.0,  4189.0],
                             [360.0,  4202.0],
                             [373.15, 4216.0]])
    water.cptype = d_type['SPLINE']
    water.cpunits = ['(K)', '(J/kg-K)']
    water.cpdata = np.array([[273.15, 4220.0],
                             [275.0,  4214.0],
                             [285.0,  4193.0],
                             [295.0,  4183.0],
                             [305.0,  4180.0],
                             [320.0,  4181.0],
                             [340.0,  4189.0],
                             [360.0,  4202.0],
                             [373.15, 4216.0]])
    water.mutype = d_type['SPLINE']
    water.muunits = ['(K)', '(kg/m-s)']
    water.mudata = np.array([[273.15, 1.787E-3],
                             [275.0,  1.682E-3],
                             [285.0,  1.239E-3],
                             [295.0,  9.579E-4],
                             [305.0,  7.669E-4],
                             [320.0,  5.770E-4],
                             [340.0,  4.220E-4],
                             [360.0,  3.261E-4],
                             [373.15, 2.817E-4]])
    water.betatype = d_type['SPLINE']
    water.betaunits = ['(K)', '(1/K)']
    water.betadata = np.array([[280.0,  4.360E-5],
                               [285.0,  0.000112],
                               [295.0,  0.000226],
                               [305.0,  0.000319],
                               [320.0,  0.000436],
                               [340.0,  0.000565],
                               [360.0,  0.000679],
                               [373.15, 0.000751]])
    water.Prtype = d_type['SPLINE']
    water.Prunits = ['(K)', '(dimensionless)']
    water.Prdata = np.array([[273.15, 13.47],
                             [275.0,  12.55],
                             [285.0,   8.91],
                             [295.0,   6.66],
                             [305.0,   5.18],
                             [320.0,   3.77],
                             [340.0,   2.68],
                             [360.0,   2.03],
                             [373.15,  1.75]])
    return water


def steel_def(state, d_type):
    # Create the steel material
    steel = Material()
    steel.name = 'steel'
    steel.state = state['SOLID']
    steel.ref = ("Table A.1, page 702, in:\n"
                 "J. H. Lienhard, IV and J. H. Lienhard, V. A Heat Transfer Textbook.\n"
                 "Phlogiston Press, Cambridge, Massachusetts, fourth edition, 2012.\n"
                 "version 2.02, available at: http://ahtt.mit.edu\n")
    steel.ktype = d_type['SPLINE']
    steel.kunits = ['(K)', '(W/m-K)']
    steel.kdata = np.array([[173.15, 70.0],
                            [273.15, 65.0],
                            [373.15, 61.0],
                            [473.15, 55.0],
                            [573.15, 50.0]])
    steel.rhotype = d_type['CONST']
    steel.rhounits = ['(K)', '(kg/m^3)']
    steel.rhodata = np.array([[293.15, 7830.0], ])
    steel.cvtype = d_type['CONST']
    steel.cvunits = ['(K)', '(J/kg-K)']
    steel.cvdata = np.array([[293.15, 434.0], ])

    return steel


def fir_def(state, d_type):
    # Create the fir material
    fir = Material()
    fir.name = 'fir'
    fir.state = state['SOLID']
    fir.ref = ("Perpendicular to the grain, Table A.2, page 707, in:\n"
               "J. H. Lienhard, IV and J. H. Lienhard, V. A Heat Transfer Textbook.\n"
               "Phlogiston Press, Cambridge, Massachusetts, fourth edition, 2012.\n"
               "version 2.02, available at: http://ahtt.mit.edu\n")
    fir.ktype = d_type['CONST']
    fir.kunits = ['(K)', '(W/m-K)']
    fir.kdata = np.array([288.15, 0.2])
    fir.rhotype = d_type['CONST']
    fir.rhounits = ['(K)', '(kg/m^3)']
    fir.rhodata = np.array([[288.15, 600.0], ])
    fir.cvtype = d_type['CONST']
    fir.cvunits = ['(K)', '(J/kg-K)']
    fir.cvdata = np.array([[288.15, 2720.0], ])

    return fir


# --------------------------------------------------------------------------------------------------------------------
#                                Test
# --------------------------------------------------------------------------------------------------------------------
"""
mat = matlib()

for i in range(len(mat)):
    print(mat[i].name)
"""
