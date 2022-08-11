"""This module contains internal logging utilities."""

# Copyright (C) 2008 Martin Sandve Alnes
# Copyright (C) 2014 Jan Blechta
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
import io, logging, os, platform, sys

# Logging wrappers
_log = logging.getLogger("instant")
_loghandler = logging.StreamHandler()
_log.addHandler(_loghandler)
#_log.setLevel(logging.WARNING)
_log.setLevel(logging.INFO)
#_log.setLevel(logging.DEBUG)

# Choose method for calling external programs. use subprocess by
# default, and os.system on Windows
_default_call_method = 'SUBPROCESS'
if 'Windows' in platform.system() or 'CYGWIN' in platform.system():
    _default_call_method = 'OS_SYSTEM'
_call_method = os.environ.get("INSTANT_SYSTEM_CALL_METHOD",
                              _default_call_method)
_log.debug('Using call method: %s'%_call_method)


def get_log_handler():
    return _loghandler


def get_logger():
    return _log


def set_log_handler(handler):
    global _loghandler
    _log.removeHandler(_loghandler)
    _loghandler = handler
    _log.addHandler(_loghandler)


def set_logging_level(level):
    import inspect
    frame = inspect.currentframe().f_back
    instant_warning("set_logging_level is deprecated but was called "\
                    "from %s, at line %d. Use set_log_level instead." % \
                    (inspect.getfile(frame), frame.f_lineno))
    set_log_level(level)


def set_log_level(level):
    if isinstance(level, string_types):
        level = level.upper()
        assert level in ("INFO", "WARNING", "ERROR", "DEBUG")
        level = getattr(logging, level)
    else:
        assert isinstance(level, int)
    _log.setLevel(level)


# Aliases for calling log consistently:


def instant_debug(*message):
    _log.debug(*message)


def instant_info(*message):
    _log.info(*message)


def instant_warning(*message):
    _log.warning(*message)


def instant_error(*message):
    _log.error(*message)
    text = message[0] % message[1:]
    raise RuntimeError(text)


def instant_assert(condition, *message):
    if not condition:
        _log.error(*message)
        text = message[0] % message[1:]
        raise AssertionError(text)


# Utility functions for file handling:


def write_file(filename, text, mode="w"):
    "Write text to a file and close it."
    try:
        if isinstance(text, bytes):
            text = text.decode("utf8")
        with io.open(filename, mode, encoding="utf8") as f:
            f.write(text)
            f.flush()
    except IOError as e:
        instant_error("Can't open '%s': %s" % (filename, e))


if _call_method == 'SUBPROCESS':

    # NOTE: subprocess in Python 2 is not OFED-fork-safe! Check subprocess.py,
    #       http://bugs.python.org/issue1336#msg146685
    #       OFED-fork-safety means that parent should not
    #       touch anything between fork() and exec(),
    #       which is not met in subprocess module. See
    #       https://www.open-mpi.org/faq/?category=openfabrics#ofa-fork
    #       http://www.openfabrics.org/downloads/OFED/release_notes/OFED_3.12_rc1_release_notes#3.03
    # However, subprocess32 backports the fix from Python 3 to 2.7.
    if os.name == "posix" and sys.version_info[0] < 3:
        try:
            import subprocess32 as subprocess
        except:
            import subprocess
    else:
        import subprocess

    def get_status_output(cmd, input=None, cwd=None, env=None):
        if isinstance(cmd, string_types):
            cmd = cmd.strip().split()
        instant_debug("Running: " + str(cmd))

        # NOTE: This is not OFED-fork-safe! Check subprocess.py,
        #       http://bugs.python.org/issue1336#msg146685
        #       OFED-fork-safety means that parent should not
        #       touch anything between fork() and exec(),
        #       which is not met in subprocess module. See
        #       https://www.open-mpi.org/faq/?category=openfabrics#ofa-fork
        #       http://www.openfabrics.org/downloads/OFED/release_notes/OFED_3.12_rc1_release_notes#3.03
        pipe = subprocess.Popen(cmd, shell=False, cwd=cwd, env=env, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)

        (output, errout) = pipe.communicate(input=input)
        assert not errout

        status = pipe.returncode
        output = output.decode('utf-8') if sys.version_info[0] > 2 else output

        return (status, output)

elif _call_method == 'OS_SYSTEM':
    import tempfile
    from .paths import get_default_error_dir

    def get_status_output(cmd, input=None, cwd=None, env=None):
        # We don't need function with such a generality.
        # We only need output and return code.
        if not isinstance(cmd, string_types) or input is not None or \
            cwd is not None or env is not None:
            raise NotImplementedError(
                'This implementation (%s) of get_status_output does'
                ' not accept \'input\', \'cwd\' and \'env\' kwargs.'
                %_call_method)

        f = tempfile.NamedTemporaryFile(dir=get_default_error_dir(),
                                        delete=True)

        # Execute cmd with redirection
        cmd += ' > ' + f.name + ' 2>&1'
        instant_debug("Running: " + str(cmd))
        # NOTE: Possibly OFED-fork-safe, tests needed!
        status = os.system(cmd)

        output = f.read()
        f.close()

        output = output.decode('utf-8') if sys.version_info[0] > 2 else output
        return (status, output)
else:
    instant_error('Incomprehensible environment variable'
                  ' INSTANT_SYSTEM_CALL_METHOD=%s'%_call_method)
