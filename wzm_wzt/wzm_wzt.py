"""
wzm_wzt.py
Testing correlation structure calculations using ABC transporter Wzm-Wzt.

Handles the primary functions
"""

def build_all_plugins(phase='training'):
    """
    Builds all th plugins (six per distribution) for the Wzm-Wzt transporter data

    Parameters
    ----------
    phase : str, Optional, default: 'training'
        determines which set of plugins to build (phase of the BRER simulations)

    Returns
    -------
    plugins : list
        list of six plugin objects, all of which handle the training, convergence, or production
    """

    if phase == 'training':
        quote='training!'
    else:
        quote='not training!'
    return quote


if __name__ == "__main__":
    # Do something if this file is invoked on its own
    print(build_all_plugins())