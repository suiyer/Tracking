"""
    dictutil.py
    ~~~~~~

    Utility methods and classes for working with dict() objects.
"""

class O(dict):
    """
    Wraps a dictionary such that its properties can be get and set as if it were a regular Python object.
    """
    @classmethod
    def recursive(cls, json):
        if isinstance(json, dict):
            return O([(k,O.recursive(v)) for (k,v) in json.items()])
        elif isinstance(json, list):
            return [O.recursive(v) for v in json]
        else:
            return json

    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, name, value):
        self[name] = value
