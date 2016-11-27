#!/usr/bin/python
import sys
import logging
import os
logging.basicConfig(stream=sys.stderr)
path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, path)

from server import app as application
