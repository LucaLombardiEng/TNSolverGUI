clc
addpath('C:\Users\Luca_Lombardi\Documents\My_Octave\TNSolver\TNSolver_code')
# basefilename = "pure_conduction_01"
# basefilename = "conduction"
basefilename = "conduction_transient"
# basefilename = "convection-radiation"
# basefilename = "convection"
# basefilename = "convection_transient"
# basefilename = "convection2"
# basefilename = "advection"
# basefilename = "advection_only"
[T, Q, nd, el] = tnsolver(basefilename)

