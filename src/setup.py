"""
/// @file setup.py
/// @author Austin Vandegriffe
/// @date 2020-04-20
/// @brief Precompile the crawler into a PYD, this allows for the source
///         code to be hidden.
/// @pre Requires crawler.py in the SAME directory.
/// @style K&R, "one true brace style" (OTBS), and '_' variable naming
/////////////////////////////////////////////////////////////////////
/// @references
/// ## N/A
"""

import sys

if len(sys.argv) == 1:
    # This file was called withing "python setup.py"
    ## and must now be called properly. To skip this
    ## execution, call "python setup.py build_ext --inplace"
    ## as we are about to.
    import os
    os.system("python setup.py build_ext --inplace")
else:
    # Proper execution of this file using build flags
    from distutils.core import setup
    from distutils.extension import Extension
    from Cython.Distutils import build_ext
    ext_modules = [
        Extension("cas_query",  ["crawler.py"]),
    ]

    setup(
        name = 'cas_query',
        cmdclass = {'build_ext': build_ext},
        ext_modules = ext_modules
    )