"""This module contains the inline* functions, which allows easy inlining of C/C++ functions."""

# Copyright (C) 2008-2010 Kent-Andre Mardal
# Copyright (C) 2008-2010 Martin Sandve Alnes
#
# This file is part of Instant.
#
# Instant is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Instant is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Instant. If not, see <http://www.gnu.org/licenses/>.
#
# Alternatively, Instant may be distributed under the terms of the BSD license.

from .output import instant_assert, instant_warning, instant_error
from .build import build_module, build_module_vtk, build_module_vmtk


def get_func_name(c_code):
    # TODO: Something more robust? Regexp?
    try:
        func = c_code[:c_code.index('(')]
        ret, func_name = func.split()
    except:
        instant_error("Failed to extract function name from c_code.")
    return func_name


def inline(c_code, **kwargs):
    """This is a short wrapper around the build_module function in instant.

    It creates a module given that
    the input is a valid C function. It is only possible
    to inline one C function each time.

    Usage:

    >>> from instant import inline
    >>> add_func = inline("double add(double a, double b){ return a+b; }")
    >>> print "The sum of 3 and 4.5 is ", add_func(3, 4.5)
    """
    instant_assert("code" not in kwargs, "Cannot specify code twice.")
    kwargs["code"] = c_code
    func_name = get_func_name(c_code)
    module = build_module(**kwargs)
    if hasattr(module, func_name):
        return getattr(module, func_name)
    else:
        instant_warning("Didn't find function '%s', returning module." % func_name)
    return module


def inline_module(c_code, **kwargs):
    """This is a short wrapper around the build_module function in instant.

    It creates a module given that
    the input is a valid C function. It is only possible
    to inline one C function each time.

    Usage:

    >>> from instant import inline
    >>> add_func = inline("double add(double a, double b){ return a+b; }")
    >>> print "The sum of 3 and 4.5 is ", add_func(3, 4.5)
    """
    instant_assert("code" not in kwargs, "Cannot specify code twice.")
    kwargs["code"] = c_code
    module = build_module(**kwargs)
    return module



def inline_with_numpy(c_code, **kwargs):
    '''This is a short wrapper around the build_module function in instant.

    It creates a module given that
    the input is a valid C function. It is only possible
    to inline one C function each time. The difference between
    this function and the inline function is that C-arrays can be used.
    The following example illustrates that.

    Usage:

    >>> import numpy
    >>> import time
    >>> from instant import inline_with_numpy
    >>> c_code = """
        double sum (int n1, double* array1){
            double tmp = 0.0;
            for (int i=0; i<n1; i++) {
                tmp += array1[i];
            }
            return tmp;
        }
        """
    >>> sum_func = inline_with_numpy(c_code,  arrays = [['n1', 'array1']])
    >>> a = numpy.arange(10000000); a = numpy.sin(a)
    >>> sum_func(a)
    '''

    import numpy
    instant_assert("code" not in kwargs, "Cannot specify code twice.")
    kwargs["code"] = c_code
    kwargs["init_code"]      = kwargs.get("init_code", "")      + "\nimport_array();\n"
    kwargs["system_headers"] = kwargs.get("system_headers", []) + ["numpy/arrayobject.h"]
    kwargs["include_dirs"]   = kwargs.get("include_dirs", [])   + ["%s" %numpy.get_include()]
    func_name = get_func_name(c_code)
    module = build_module(**kwargs)
    if hasattr(module, func_name):
        return getattr(module, func_name)
    else:
        instant_warning("Didn't find function '%s', returning module." % func_name)
    return module

def inline_module_with_numpy(c_code, **kwargs):
    '''This is a short wrapper around the build_module function in instant.

    It creates a module given that
    the input is a valid C function. It is only possible
    to inline one C function each time. The difference between
    this function and the inline function is that C-arrays can be used.
    The following example illustrates that.

    Usage:

    >>> import numpy
    >>> import time
    >>> from instant import inline_with_numpy
    >>> c_code = """
        double sum (int n1, double* array1){
            double tmp = 0.0;
            for (int i=0; i<n1; i++) {
                tmp += array1[i];
            }
            return tmp;
        }
        """
    >>> sum_func = inline_with_numpy(c_code,  arrays = [['n1', 'array1']])
    >>> a = numpy.arange(10000000); a = numpy.sin(a)
    >>> sum_func(a)
    '''
    import numpy
    instant_assert("code" not in kwargs, "Cannot specify code twice.")
    kwargs["code"] = c_code
    kwargs["init_code"]      = kwargs.get("init_code", "")      + "\nimport_array();\n"
    kwargs["system_headers"] = kwargs.get("system_headers", []) + ["numpy/arrayobject.h"]
    kwargs["include_dirs"]   = kwargs.get("include_dirs", [])   + ["%s" % numpy.get_include()]
    module = build_module(**kwargs)
    return module


def inline_vtk(c_code, cache_dir=None):

    module = build_module_vtk(c_code)
    func_name = get_func_name(c_code)
    if hasattr(module, func_name):
        return getattr(module, func_name)
    else:
        instant_warning("Didn't find function '%s', returning module." % func_name)
    return module

def inline_vmtk(c_code, cache_dir=None):

    module = build_module_vmtk(c_code)
    func_name = get_func_name(c_code)
    if hasattr(module, func_name):
        return getattr(module, func_name)
    else:
        instant_warning("Didn't find function '%s', returning module." % func_name)
    return module
