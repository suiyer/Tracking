"""
    sync.py
    ~~~~~~

    Utility for creating synchronous wrappers for asynchronous methods.

    This makes a number of assumptions about how the asynchronous methods are designed...
    These assumptions should be documented.  :-)
"""

import inspect
import tornado.ioloop

IO_LOOP = tornado.ioloop.IOLoop()

def async(fn):
    """ Function decorator marks the function as asynchronous. """
    fn.async = True
    return fn

class SyncProxy(object):
    """ Proxy exposes synchronous versions of asynchronous methods on a delegate object """

    def __init__(self, delegate, exception_constructors=None):
        self._delegate = delegate
        self._exception_constructors = exception_constructors or {}
        self._result = None
        self._exception = None

    def __getattr__(self, name):
        method = getattr(self._delegate, name)
        if method and hasattr(method, '__call__') and getattr(method, 'async', False):
            return self._wrap_async(method)
        return method

    def _wrap_async(self, method):
        """ Wraps a method marked @async """
        callback_args = dict()
        callback_args['callback'] = self._success_callback
        for name in inspect.getargspec(method)[0]:
            if name in self._exception_constructors:
                callback_args[name] = self._wrap_ex(self._exception_constructors[name])

        def sync(*args, **kwargs):
            kwargs.update(callback_args)
            method(*args, **kwargs)
            IO_LOOP.start()
            # the following doesn't get executed until a callback invokes io_loop.stop()
            (result, self._result) = (self._result, None)
            (exception, self._exception) = (self._exception, None)
            if exception is not None:
                raise exception
            return result
        return sync

    def _wrap_ex(self, exception_constructor):
        def exception_callback(*args, **kwargs):
            self._exception = exception_constructor(*args, **kwargs)
            IO_LOOP.stop()
        return exception_callback

    def _success_callback(self, *args):
        self._result = args[0] if len(args) == 1 else args
        IO_LOOP.stop()

def sync_proxy(async_type, exception_constructors=None):
    """ Factory for synchronous proxies of a type with asynchronous methods """
    def constructor(*args, **kwargs):
        # the asynchronous class constructor must have an optional 'io_loop' parameter
        kwargs['io_loop'] = IO_LOOP
        delegate = async_type(*args, **kwargs)
        return SyncProxy(delegate=delegate, exception_constructors=exception_constructors)
    return constructor
