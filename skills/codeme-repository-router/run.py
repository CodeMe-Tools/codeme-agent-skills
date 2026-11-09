#!/usr/bin/env python3
"""codeme-repository-router skill execution entrypoint."""
import sys
from codeme_agent_skills.cli import router_main

if __name__ == "__main__":
    sys.exit(router_main(sys.argv[1:]))
