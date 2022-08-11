"""This module contains helper functions for working with temp and cache directories."""

# Copyright (C) 2008 Martin Sandve Alnes
# Copyright (C) 2012 Florian Rathgeber
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

# Utilities for directory handling:

from six import string_types
import os
import sys
import errno
import shutil
import tempfile
import time
from .signatures import compute_checksum
from .output import instant_debug, instant_assert

_tmp_dir = None


def get_temp_dir():
    """Return a temporary directory for the duration of this process.

    Multiple calls in the same process returns the same directory.
    Remember to call delete_temp_dir() before exiting."""
    global _tmp_dir
    if _tmp_dir is None:
        datestring = "%d-%d-%d-%02d-%02d" % time.localtime()[:5]
        suffix = datestring + "_instant_" + compute_checksum(get_default_cache_dir())
        _tmp_dir = tempfile.mkdtemp(suffix)
        instant_debug("Created temp directory '%s'." % _tmp_dir)
    return _tmp_dir


def delete_temp_dir():
    """Delete the temporary directory created by get_temp_dir()."""
    global _tmp_dir
    if _tmp_dir and os.path.isdir(_tmp_dir):
        shutil.rmtree(_tmp_dir, ignore_errors=True)
    _tmp_dir = None


def get_instant_dir():
    "Return the default instant directory, creating it if necessary."
    # Place default cache dir in virtualenv or conda prefix
    # if one of them are active, or under user's home directory
    home = os.path.expanduser("~")
    venv = os.environ.get("VIRTUAL_ENV")
    cenv = os.environ.get("CONDA_PREFIX")
    if venv == sys.prefix:
        env = venv
    elif cenv == sys.prefix:
        env = cenv
    else:
        env = home

    instant_dir = os.path.join(env, ".cache", "instant")

    # If placed in home directory, add python version for safety,
    # since C extensions are not compatible across versions.
    # (for python 3, it's possible to use the stable C API,
    # however we don't know if the instant user has done that)
    if env == home:
        ver = "python%d.%d" % sys.version_info[:2]
        instant_dir = os.path.join(instant_dir, ver)

    makedirs(instant_dir)
    return instant_dir


def get_default_cache_dir():
    "Return the default cache directory."
    cache_dir = os.environ.get("INSTANT_CACHE_DIR")
    # Catches the cases where INSTANT_CACHE_DIR is not set or ''
    if not cache_dir:
        cache_dir = os.path.join(get_instant_dir(), "cache")
    makedirs(cache_dir)
    return cache_dir


def get_default_error_dir():
    "Return the default error directory."
    error_dir = os.environ.get("INSTANT_ERROR_DIR")
    # Catches the cases where INSTANT_ERROR_DIR is not set or ''
    if not error_dir:
        error_dir = os.path.join(get_instant_dir(), "error")
    makedirs(error_dir)
    return error_dir


def validate_cache_dir(cache_dir):
    if cache_dir is None:
        return get_default_cache_dir()
    instant_assert(isinstance(cache_dir, string_types), "Expecting cache_dir to be a string.")
    cache_dir = os.path.abspath(cache_dir)
    makedirs(cache_dir)
    return cache_dir


def makedirs(path):
    """
    Creates a directory (tree). If directory already excists it does nothing.
    """
    try:
        os.makedirs(path)
        instant_debug("In instant.makedirs: Creating directory %r" % path)
    except os.error as e:
        if e.errno != errno.EEXIST:
            raise


def _test():
    from .output import set_logging_level
    set_logging_level("DEBUG")
    print("Temp dir:", get_temp_dir())
    print("Instant dir:", get_instant_dir())
    print("Default cache dir:", get_default_cache_dir())
    print("Default error dir:", get_default_error_dir())
    delete_temp_dir()


if __name__ == "__main__":
    _test()
