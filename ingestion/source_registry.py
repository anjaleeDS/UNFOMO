"""
All sources in one place. To add or remove a source, edit sources.yaml — no Python changes needed.
"""
import os
import yaml

_here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_here, "sources.yaml")) as f:
    SOURCES: list[dict] = yaml.safe_load(f)
