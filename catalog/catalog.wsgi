#!/usr/bin/python

import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/catalog")

from catalog import app as application
application.secret_key = 'DPXw,YJ9>g$yyuR?'
