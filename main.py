import sys

# Reconfigure stdout/stderr to UTF-8 to prevent encoding errors on Windows console
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

from promptcli.cli import main

if __name__ == "__main__":
    main()

