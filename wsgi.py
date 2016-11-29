#!/usr/bin/python
import sys
import logging
import os
logging.basicConfig(stream=sys.stderr)
path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, path)

from server import app as application


# <VirtualHost *:80>
# 		ServerName 52.23.153.254
# 		ServerAdmin jdcoppola@gmail.com
# 		WSGIScriptAlias / /var/www/ecommerce_app/flaskapp.wsgi
# 		<Directory /var/www/ecommerce_app/ecommerce_website/>
# 			Order allow,deny
# 			Allow from all
# 		</Directory>
# 		Alias /static /var/www/ecommerce_app/ecommerce_website/static
# 		<Directory /var/www/ecommerce_app/ecommerce_website/static/>
# 			Order allow,deny
# 			Allow from all
# 		</Directory>
# 		ErrorLog ${APACHE_LOG_DIR}/error.log
# 		LogLevel warn
# 		CustomLog ${APACHE_LOG_DIR}/access.log combined
# </VirtualHost>
