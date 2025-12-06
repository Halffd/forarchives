import os

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Angular dist directory
ANGULAR_DIST = os.path.join(PROJECT_ROOT, "dist/forarchives/browser")

# Static files directory
STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")

# Templates directory
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates")
