#!C:/Python27/python.exe -u
# -*- coding: UTF-8 -*-

print("Content-Type: text/html")
print

import cgitb
# Log errors to file
# cgitb.enable(display=0, logdir="/cgi-bin/GitHub_Hanger")
cgitb.enable()

print

import os
import cgi
import json
import pprint
import logging
from configobj import ConfigObj


def initialize_logging(log_file_path, logfmt, datefmt):
    logger = logging.getLogger(__name__)
    logging_level = 10

    handler = logging.FileHandler(log_file_path)
    handler.setLevel(logging_level)

    formatter = logging.Formatter(logfmt, datefmt)

    handler.setFormatter(formatter)

    logger.setLevel(logging_level)
    logger.addHandler(handler)

    return logger


class PrettyLog():
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return pprint.pformat(self.obj)


## Loading configurations
CONFIG_PATH = "config.ini"

config = ConfigObj(CONFIG_PATH, interpolation=False)

LOG_FILE_PATH = config['Logging']['LOG_PATH']
LOG_FORMAT = config['Logging']['LOG_FORMAT']
LOG_DATE_FORMAT = config['Logging']['DATE_FORMAT']
## Finished loading configurations

logger = initialize_logging(LOG_FILE_PATH, LOG_FORMAT, LOG_DATE_FORMAT)

logger.info("Beginning Hanger")

form = cgi.FieldStorage()
pprint.pprint(form)

json_payload = form.getvalue('payload', -1)

if json_payload is not -1:
    payload = json.loads(json_payload)
    logger.debug(PrettyLog(payload))

    import subprocess
    import sys

    from tempfile import NamedTemporaryFile

    # Create a temp file with payload and pass it to processor
    with NamedTemporaryFile(delete=False) as f:
        f.write(os.environ['HTTP_X_GITHUB_EVENT'] + '\n')
        f.write(json_payload + '\n')

        # import os
        # command = './hookprocessor.py ' + f.name
        # os.system("at now <<< " + command)

        # import os
        # command = './hookprocessor.py ' + f.name
        # os.system("batch <<< " + command)

        DETACHED_PROCESS = 0x00000008
        p = subprocess.Popen(
            [sys.executable, './hookprocessor.py', f.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            creationflags=DETACHED_PROCESS)
else:
    print("<br/>\r")
    print("No json payload was receieved!<br/>\r")
    logger.error(form)

logger.info("Kan 3ndk hook w ra7 :D")
