import os
import configparser as cfp

# initialize useful dirs/files
CONF = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config"))
# useful for doing customization without affecting version control
conf_app = os.path.join(CONF, "app.conf")
# default values packaged in the version control
conf_def = os.path.join(CONF, "default.conf")

# initialize config
config = cfp.ConfigParser()

# read configuration ("app.conf" or "default.conf")
# look for app.conf
def get_configuration():
	if os.path.exists(conf_app):
		config.read(conf_app)
	else:
		config.read(conf_def)

	return config

#print(config["SECTORS"]["technology"])
