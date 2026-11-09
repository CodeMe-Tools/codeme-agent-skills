#!/usr/bin/env python3
"""codeme-fix-loop skill execution entrypoint."""
import sys
from codeme_agent_skills.cli import main

if __name__ == "__main__":
    sys.exit(main(["fix-loop"] + sys.argv[1:]))
