"""This module contains helper functions for configuration using pkg-config."""

# Copyright (C) 2008-2009 Kent-Andre Mardal
# Copyright (C) 2008 Martin Sandve Alnes
# Copyright (C) 2011-2013 Johan Hake
# Copyright (C) 2011 Joachim Berdal Haga
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
# Alternatively, Instant may be distributed under the terms of the BSD
# license.

from six import string_types
import os
from .output import get_status_output
import re

# Global cache variables
_swig_binary_cache = None
_swig_version_cache = None
_pkg_config_installed = None
_header_and_library_cache = {}


def check_and_set_swig_binary(binary="swig", path=""):
    """ Check if a particular swig binary is available"""
    global _swig_binary_cache
    if not isinstance(binary, string_types):
        raise TypeError("expected a 'str' as first argument")
    if not isinstance(path, string_types):
        raise TypeError("expected a 'str' as second argument")
    swig_binary = os.path.join(path, binary)
    if swig_binary == _swig_binary_cache:
        return True

    result, output = get_status_output("%s -version"%swig_binary)
    if result != 0:
        return False

    # Set binary cache
    _swig_binary_cache = swig_binary

    # Reset SWIG version cache
    pattern = "SWIG Version (.*)"
    r = re.search(pattern, output)
    _swig_version_cache = r.groups(0)[0]

    return True


def get_swig_binary():
    "Return any cached swig binary"
    return _swig_binary_cache if _swig_binary_cache else "swig"


def get_swig_version():
    """ Return the current swig version in a 'str'"""
    global _swig_version_cache
    if _swig_version_cache is None:
        # Check for swig installation
        result, output = get_status_output("%s -version"%get_swig_binary())
        if result != 0:
            raise OSError("SWIG is not installed on the system.")
        pattern = "SWIG Version (.*)"
        r = re.search(pattern, output)
        _swig_version_cache = r.groups(0)[0]
    return _swig_version_cache


def check_swig_version(version, same=False):
    """Check the swig version

    Returns True if the version of the installed swig is equal or
    greater than the version passed to the function.

    If same is True, the function returns True if and only if the two versions
    are the same.

    Usage:
    if instant.check_swig_version('1.3.36'):
        print "Swig version is greater than or equal to 1.3.36"
    else:
        print "Swig version is lower than 1.3.36"

    """
    assert isinstance(version, string_types), "Provide the first version number as a 'str'"
    assert len(version.split(".")) == 3, "Provide the version number as three numbers seperated by '.'"

    installed_version = list(map(int, get_swig_version().split('.')))
    handed_version    = list(map(int, version.split('.')))

    # If same is True then just check that all numbers are equal
    if same:
        return all(i == h for i, h in zip(installed_version, handed_version))

    swig_enough = True
    for i, v in enumerate([v for v in installed_version]):
        if handed_version[i] < v:
            break
        elif handed_version[i] == v:
            continue
        else:
            swig_enough = False
        break

    return swig_enough


def header_and_libs_from_pkgconfig(*packages, **kwargs):
    """This function returns list of include files, flags, libraries and
    library directories obtain from a pkgconfig file.

    The usage is:
      (includes, flags, libraries, libdirs) = \
             header_and_libs_from_pkgconfig(*list_of_packages)
    or:
        (includes, flags, libraries, libdirs, linkflags) = \
             header_and_libs_from_pkgconfig(*list_of_packages, \
             returnLinkFlags=True)

    """

    global _pkg_config_installed, _header_and_library_cache
    returnLinkFlags = kwargs.get("returnLinkFlags", False)
    if _pkg_config_installed is None:
        result, output = get_status_output("pkg-config --version ")
        _pkg_config_installed = (result == 0)

    if not _pkg_config_installed:
        raise OSError("The pkg-config package is not installed on the system.")

    env = os.environ.copy()
    try:
        assert env["PKG_CONFIG_ALLOW_SYSTEM_CFLAGS"] == "0"
    except:
        env["PKG_CONFIG_ALLOW_SYSTEM_CFLAGS"] = "1"

    includes = []
    flags = []
    libs = []
    libdirs = []
    linkflags = []
    for pack in packages:
        if not pack in _header_and_library_cache:
            result, output = get_status_output(\
                "pkg-config --exists %s " % pack, env=env)
            if result == 0:
                tmp = get_status_output(\
                    "pkg-config --cflags-only-I %s " % pack, env=env)[1].split()
                _includes = [i[2:] for i in tmp]

                _flags = get_status_output(\
                    "pkg-config --cflags-only-other %s " % pack, env=env)[1].split()

                tmp = get_status_output(\
                    "pkg-config --libs-only-l  %s " % pack, env=env)[1].split()
                _libs = [i[2:] for i in tmp]

                tmp = get_status_output(\
                    "pkg-config --libs-only-L  %s " % pack, env=env)[1].split()
                _libdirs = [i[2:] for i in tmp]

                _linkflags = get_status_output(\
                    "pkg-config --libs-only-other  %s " % pack, env=env)[1].split()

                _header_and_library_cache[pack] = (_includes, _flags, _libs, \
                                                   _libdirs, _linkflags)
            else:
                _header_and_library_cache[pack] = None

        result = _header_and_library_cache[pack]
        if not result:
            raise OSError("The pkg-config file %s does not exist" % pack)

        _includes, _flags, _libs, _libdirs, _linkflags = result
        includes.extend(_includes)
        flags.extend(_flags)
        libs.extend(_libs)
        libdirs.extend(_libdirs)
        linkflags.extend(_linkflags)

    if returnLinkFlags:
        return (includes, flags, libs, libdirs, linkflags)

    return (includes, flags, libs, libdirs)
