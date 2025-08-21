import os
import sys

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Expose WSGI callable for Passenger (supports BASE_PATH via app.application)
from app import application
