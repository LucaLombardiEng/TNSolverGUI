import sys
from pathlib import Path

# Add the project directory to sys.path so Python registers package structures properly
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import scipy.sparse as sparse
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

from TNSolver_code.core_solver import tn_solver

# T, Q, nd, el = tn_solver('Test_Gui/Test_Material/test_01_solid_conduction')
# T, Q, nd, el = tn_solver('Test_Gui/Test_Material/test_02_solid_conduction_function')
T, Q, nd, el = tn_solver('Test_Gui/Test_Material/test_02_solid_conduction_function_trans')

print('Done!')
