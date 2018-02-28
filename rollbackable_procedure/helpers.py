import inspect


def getargs(func):
    """
    Return the args and kwargs of a function. i.e.
        >>> def d(a, b, c, d=1, e=2):
        ...     pass
        >>>
        >>> print getargs(d)
        Out: (['a', 'b', 'c'], {'e': 2, 'd': 1})
        >>>
    """
    argspec = inspect.getargspec(func)
    defaults = argspec.defaults or []
    args = list(argspec.args[:len(argspec.args)-len(defaults)])
    kwargs = dict(zip(argspec.args[len(args):], defaults))
    return args, kwargs
