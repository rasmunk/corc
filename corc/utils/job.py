# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import subprocess


def __format_output__(result, format_output_str=False):
    command_results = {}
    if hasattr(result, "args"):
        command_results.update({"command": " ".join((getattr(result, "args")))})
    if hasattr(result, "returncode"):
        command_results.update({"returncode": getattr(result, "returncode")})
    if hasattr(result, "stderr"):
        command_results.update({"error": getattr(result, "stderr")})
    if hasattr(result, "stdout"):
        command_results.update({"output": getattr(result, "stdout")})
    if hasattr(result, "wait"):
        command_results.update({"wait": getattr(result, "wait")})
    if hasattr(result, "communicate"):
        command_results.update({"communicate": getattr(result, "communicate")})
    if hasattr(result, "kill"):
        command_results.update({"kill": getattr(result, "kill")})

    if format_output_str:
        for key, value in command_results.items():
            if key == "returncode" or key == "stderr" or key == "stdout":
                command_results[key] = str(value)
    return command_results


def run_popen(cmd, format_output_str=False, **run_kwargs):
    result = subprocess.Popen(cmd, **run_kwargs)
    return __format_output__(result, format_output_str=format_output_str)


def check_call(cmd, format_output_str=False, **kwargs):
    result = subprocess.check_call(cmd, **kwargs)
    return __format_output__(result, format_output_str=format_output_str)


def run(cmd, format_output_str=False, **run_kwargs):
    result = subprocess.run(cmd, **run_kwargs)
    return __format_output__(result, format_output_str=format_output_str)
