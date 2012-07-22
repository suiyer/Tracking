"""
    __init__.py
    ~~~~~~

    Utility methods for interacting with the Bazaarvoice Platform API
"""

import dateutil.parser
import logging

log = logging.getLogger(__name__)

def parse_timestamp(string):
    """ Converts an ISO timestamp string to a Python datetime object with timezone. """
    return dateutil.parser.parse(string)

def escape(value):
    """ Escapes a value for use within a filter string """
    if type(value) is list:
        return ','.join(map(escape, value))
    else:
        return str(value).replace(',', r'\,')
