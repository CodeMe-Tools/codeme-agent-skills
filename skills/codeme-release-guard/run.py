#!/usr/bin/env python3
"""codeme-release-guard skill execution entrypoint."""
import sys
from codeme_agent_skills.cli import main

if __name__ == "__main__":
    sys.exit(main(["release-guard"] + sys.argv[1:]))
