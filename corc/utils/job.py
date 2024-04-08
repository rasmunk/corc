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
