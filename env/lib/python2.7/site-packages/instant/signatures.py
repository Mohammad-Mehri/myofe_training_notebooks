"""This module contains helper functions for working with checksums."""

# Copyright (C) 2008 Martin Sandve Alnes
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

from six import string_types
import io
import hashlib
from .output import instant_assert, instant_debug, instant_error

def compute_checksum(text="", filenames=[]):
    """
    Get the checksum value of filename
    modified based on Python24\Tools\Scripts\md5.py
    """
    instant_assert(isinstance(text, string_types), "Expecting string.")
    instant_assert(isinstance(filenames, (list, tuple)), "Expecting sequence.")
    
    m = hashlib.new('sha1')
    if text:
        m.update(text.encode('utf-8'))
    
    for filename in sorted(filenames): 
        instant_debug("Adding file '%s' to checksum." % filename)
        try:
            fp = io.open(filename, 'rb')
        except IOError as e:
            instant_error("Can't open file '%s': %s" % (filename, e))
        
        try:
            while True:
                data = fp.read()
                if not data:
                    break
                m.update(data)
        except IOError as e:
            instant_error("I/O error reading '%s': %s" % (filename, e))
        
        fp.close() 
    
    return m.hexdigest().lower()


def _test():
    signature = "(Test signature)"
    files = ["signatures.py", "__init__.py"]
    print()
    print("Signature:", repr(signature))
    print("Checksum:", compute_checksum(signature, []))
    print()
    print("Files:", files)
    print("Checksum:", compute_checksum("", files))
    print()

if __name__ == "__main__":
    _test()

