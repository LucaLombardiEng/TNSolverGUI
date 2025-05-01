import numpy as np
from scipy.interpolate import interp1d, pchip_interpolate, PchipInterpolator


def fluidprop(mat, T):
    """
    Evaluate fluid properties.

    Args:
        mat: Material properties (dictionary or object with fluid data).
        T: Temperature (NumPy array or list).

    Returns:
        k: Thermal conductivity.
        rho: Density.
        cp: Specific heat.
        mu: Dynamic viscosity.
        Pr: Prandtl number.  All returned as numpy arrays.
    """

    if isinstance(T, np.ndarray):
        n = len(T)
    else:
        n = 1
    k = np.full(n, np.nan)
    rho = np.full(n, np.nan)
    cp = np.full(n, np.nan)
    mu = np.full(n, np.nan)
    Pr = np.full(n, np.nan)

    # Helper function to evaluate property based on type
    def eval_prop(prop_data, prop_type, T):
        if prop_type == 1:  # Constant
            return np.full(len(T), prop_data[1]) # or prop_data[1] if it's a scalar.
        elif prop_type == 2:  # Table - piecewise linear
            T = np.maximum(prop_data[0, 0], T)
            T = np.minimum(prop_data[-1, 0], T)
            return interp1d(prop_data[:, 0], prop_data[:, 1], kind='linear')(T)
        elif prop_type == 3:  # Monotonic spline
            T = np.maximum(prop_data[0, 0], T)
            T = np.minimum(prop_data[-1, 0], T)
            return pchip_interpolate(prop_data[:, 0], prop_data[:, 1], T)
        elif prop_type == 4:  # Polynomial
            return np.polyval(prop_data, T)
        else:
            raise ValueError(f"Invalid property type: {prop_type}")

    k = eval_prop(mat.kdata, mat.ktype, T)
    rho = eval_prop(mat.rhodata, mat.rhotype, T)
    cp = eval_prop(mat.cpdata, mat.cptype, T)
    mu = eval_prop(mat.mudata, mat.mutype, T)
    Pr = eval_prop(mat.Prdata, mat.Prtype, T)

    return k, rho, cp, mu, Pr


def betaprop(mat, T):
    """
    Evaluate the material properties (thermal expansion coefficient).

    Args:
        mat: A dictionary or object containing material data.  It should
             have at least the following keys/attributes:
            'beta_type': An integer indicating the type of beta data (1-4).
            'beta_data': The data itself. The format depends on 'beta type'.
                        See the code for details.
        T: A NumPy array or list of temperatures.

    Returns:
        A NumPy array of thermal expansion coefficients corresponding to T.
    """

    if isinstance(T, np.ndarray):
        n = len(T)
    else:
        n = 1
    beta = np.full(n, np.nan)  # Initialize with NaN

    # Thermal expansion coefficient

    beta_type = mat.betatype  # Accessing like a dictionary.  Adjust if it's an object.
    beta_data = mat.betadata

    if beta_type == 1:  # Constant
        beta[:] = beta_data[1]  # Or beta_data[1] if beta_data is a list or array
    elif beta_type == 2:  # Table - piecewise linear
        T = np.maximum(beta_data[0, 0], T)
        T = np.minimum(beta_data[-1, 0], T)
        beta = interp1d(beta_data[:, 0], beta_data[:, 1], kind='linear')(T)
    elif beta_type == 3:  # Monotonic spline (pchip)
        T = np.maximum(beta_data[0, 0], T)
        T = np.minimum(beta_data[-1, 0], T)
        beta = pchip_interpolate(beta_data[:, 0], beta_data[:, 1], T)  # Use pchip_interpolate directly
    elif beta_type == 4:  # Polynomial
        beta = np.polyval(beta_data, T)  # beta_data should be the polynomial coefficients
    else:
        raise ValueError("Invalid beta type. Must be 1, 2, 3 or 4.")  # Handle invalid type.  Important!

    return beta


def kprop(mat, T):
    """
    Calculates thermal conductivity (k) based on material properties and temperature.

    Args:
        mat: A dictionary or object containing material properties.  Must have
             'ktype' and 'kdata' fields.  'kdata' structure depends on 'ktype'.
        T: A numpy array or list of temperatures.

    Returns:
        A numpy array of thermal conductivities corresponding to the input temperatures.
        Returns NaN values for any input temperature outside the defined ranges
        for interpolation methods.
    """

    if isinstance(T, np.ndarray):
        n = len(T)
    else:
        n = 1
    k = np.full(n, np.nan, dtype=float)  # Initialize k with NaN values

    # Thermal conductivity

    if mat.ktype == 1:  # Constant
        k[:] = mat.kdata[1]
    elif mat.ktype == 2:  # Table - piecewise linear
        k = interp1d(mat.kdata[:, 0], mat.kdata[:, 1], T, kind='linear', fill_value=np.nan)(T)
    elif mat.ktype == 3:  # Monotonic spline (pchip)
        pchip = PchipInterpolator(mat.kdata[:, 0], mat.kdata[:, 1])
        k = pchip(T)
    elif mat.ktype == 4:  # Polynomial
        k = np.polyval(mat.kdata, T)
    else:
      print("ERROR: Invalid k_type specified")

    return k


def rhoCpprop(mat, T):
    """
    Evaluates density (rho) and specific heat (cp) material properties.

    Args:
        mat: A dictionary or object containing material properties. Must have
             'rhotype', 'rhodata', 'cptype', and 'cpdata' fields.  The structure
             of 'rhodata' and 'cpdata' depends on the respective type.
        T: A NumPy array or list of temperatures.

    Returns:
        A tuple containing two NumPy arrays: rho and cp, corresponding to the
        input temperatures. Returns NaN values for any input temperature outside the defined ranges
        for interpolation methods.
    """

    if isinstance(T, np.ndarray):
        n = len(T)
    else:
        n = 1
    rho = np.full(n, np.nan, dtype=float)
    cp = np.full(n, np.nan, dtype=float)

    # Density
    if mat.rhotype == 1:  # Constant
        rho[:] = mat.rhodata[1]
    elif mat.rhotype == 2:  # Table - piecewise linear
        rho = interp1d(mat.rhodata[:, 0], mat.rhodata[:, 1], T, kind='linear', fill_value=np.nan)(T)
    elif mat.rhotype == 3:  # Monotonic spline
        pchip_rho = PchipInterpolator(mat.rhodata[:, 0], mat.rhodata[:, 1])
        rho = pchip_rho(T)
    elif mat.rhotype == 4:  # Polynomial
        rho = np.polyval(mat.rhodata, T)
    else:
      raise ValueError("Invalid rhotype specified")


    # Specific heat
    if mat.cptype == 1:  # Constant
        cp[:] = mat.cpdata[1]
    elif mat.cptype == 2:  # Table - piecewise linear
        cp = interp1d(mat.cpdata[:, 0], mat.cpdata[:, 1], T, kind='linear', fill_value=np.nan)(T)
    elif mat.cptype == 3:  # Monotonic spline
        pchip_cp = PchipInterpolator(mat.cpdata[:, 0], mat.cpdata[:, 1])
        cp = pchip_cp(T)
    elif mat.cptype == 4:  # Polynomial
        cp = np.polyval(mat.cpdata, T)
    else:
      raise ValueError("Invalid cptype specified")

    return rho, cp


def rhoCvprop(mat, T):
    """
    Evaluates density (rho) and constant volume specific heat (cv) material properties.

    Args:
        mat: A dictionary or object containing material properties. Must have
             'rhotype', 'rhodata', 'cvtype', and 'cvdata' fields.  The structure
             of 'rhodata' and 'cvdata' depends on the respective type.
        T: A NumPy array or list of temperatures.

    Returns:
        A tuple containing two NumPy arrays: rho and cv, corresponding to the
        input temperatures. Returns NaN values for any input temperature outside the defined ranges
        for interpolation methods.
    """

    if isinstance(T, np.ndarray):
        n = len(T)
    else:
        n = 1
    rho = np.full(n, np.nan, dtype=float)
    cv = np.full(n, np.nan, dtype=float)

    # Density
    if mat.rhotype == 1:  # Constant
        rho[:] = mat.rhodata[0, 1]
    elif mat.rhotype == 2:  # Table - piecewise linear
        rho = interp1d(mat.rhodata[:, 0], mat.rhodata[:, 1], T, kind='linear', fill_value=np.nan)(T)
    elif mat.rhotype == 3:  # Monotonic spline
        pchip_rho = PchipInterpolator(mat.rhodata[:, 0], mat.rhodata[:, 1])
        rho = pchip_rho(T)
    elif mat.rhotype == 4:  # Polynomial
        rho = np.polyval(mat.rhodata, T)
    else:
      raise ValueError("Invalid rhotype specified")

    # Constant volume specific heat
    if mat.cvtype == 1:  # Constant
        cv[:] = mat.cvdata[0, 1]
    elif mat.cvtype == 2:  # Table - piecewise linear
        cv = interp1d(mat.cvdata[:, 0], mat.cvdata[:, 1], T, kind='linear', fill_value=np.nan)(T)
    elif mat.cvtype == 3:  # Monotonic spline
        pchip_cv = PchipInterpolator(mat.cvdata[:, 0], mat.cvdata[:, 1])
        cv = pchip_cv(T)
    elif mat.cvtype == 4:  # Polynomial
        cv = np.polyval(mat.cvdata, T)
    else:
      raise ValueError("Invalid cvtype specified")

    return rho, cv


def evalfunc(func, ind_v):
    """
    Evaluates a function based on its type and data.

    Args:
        func: A dictionary or object containing function properties. Must have
              'type' and 'data' fields. The structure of 'data' depends on 'type'.
        ind_v: The independent variable value(s) at which to evaluate the function.
              Can be a single value or a NumPy array/list.

    Returns:
        The function value(s) at the given independent variable(s). Returns NaN
        if the 'type' is not recognized or if `ind_v` is outside the data range for
        interpolation methods.
    """

    val = np.nan  # Initialize with NaN

    if func.type == 0:
        val = func.data
    elif func.type == 1:  # Linear interpolation
        val = interp1d(func.data[:, 0], func.data[:, 1], ind_v, kind='linear', fill_value=np.nan)(ind_v)
    elif func.type == 2:  # Pchip interpolation
        pchip = PchipInterpolator(func.data[:, 0], func.data[:, 1])
        val = pchip(ind_v)
    else:
        pass

    return val
