import os
import sys
import argparse
import runpy


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", default=False)
    args, unknown = parser.parse_known_args()

    unknown_arguments = {}
    # Run an action
    runpy.run_module(
        args.action,
        init_globals=unknown_arguments,
        run_name="'__main__'",
        alter_sys=True,
    )
