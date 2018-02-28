import traceback

from helpers import getargs


class revertable_task(object):
    """A decorator for revertable task.
    Usage example:
        @revertable_task
        def create_dir(self):
            os.mkdir(self.dir_name)

        @create_dir.reverter
        def create_dir(self):
            os.rmdir(self.dir_name)
    """
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self._action_args = getargs(func)
        self.action = func

    def __get__(self, obj, cls):
        self._obj = obj
        return self

    def reverter(self, func):
        """The revert function decorator
        """
        self._revert_args = getargs(func)
        # It's possible that the revert function doesn't include several arguments that found in the action.
        # positional arguments - We are getting the positions of the arguments in action to pass them
        # correctly to the revert
        args_postions_in_action, keyword_args = [], {}
        for arg_name in self._revert_args[0]:
            args_postions_in_action.append(self._action_args[0].index(arg_name))
        # Filtering keyword arguments
        for arg_name, default in self._action_args[1].items():
            if arg_name in self._revert_args[1]:
                keyword_args[arg_name] = default

        # Define the revert function
        def revert(*args, **kwargs):
            # re-composing args and removing self
            args = tuple([args[i-1] for i in args_postions_in_action[1:]])
            # Filtering keyword arguments
            for k in kwargs.keys():
                if k not in self._revert_args[1]:
                    del kwargs[k]
            # Logging action and call revert
            self._obj.log_action(self.revert, args, kwargs)
            print('Running revert: {}:{}(args={}, kwargs={})'.format(
                self.__class__.__name__, self.action.func_name, self._args, self._kwargs))
            return func(self._obj, *args, **kwargs)

        self.revert = revert
        # Changing the name of the function for logging purposes
        self.revert.func_name = 'de_{}'.format(self.action.func_name)
        return self

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._obj.push_task(self, args, kwargs)
        self._obj.log_action(self.action, args, kwargs)
        print('Running action: {}:{}(args={}, kwargs={})'.format(
            self.__class__.__name__, self.action.func_name, self._args, self._kwargs))
        return self.action(self._obj, *args, **kwargs)


class RollbackableProcedure(object):
    """A base object for Rollbackable procedure.
    Usage example in tests.
    """

    def __init__(self):
        self._tasks_perform_stack = []
        self._actions_log = []

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def actions_log(self):
        return self._actions_log

    def log_action(self, action, args=None, kwargs=None):
        """Insert an action with its args and kwargs into the actions log, either revert/action.
        Args:
            :param `FuntionType` action: The action.
            :param `list` or `tuple` (optional) args: The args.
            :param `dict` (optional) args: The kwargs.
        """
        self._actions_log.append([action, args, kwargs])

    def push_task(self, task, args=None, kwargs=None):
        """Push a task with its args and kwargs into the tasks stack.
        Args:
            :param `FuntionType` action: The action.
            :param `list` or `tuple` (optional) args: The args.
            :param `dict` (optional) args: The kwargs.
        """
        self._tasks_perform_stack.append([task, args, kwargs])

    def pop_task(self):
        """Return the last task in the stack"""
        return self._tasks_perform_stack.pop()

    def rollback(self):
        """Rolling back all the tasks in the stack
        """
        # The last task must be inside try since it's possible that the action has no effect.
        # Probably we should find a way to handle this better
        print('Rolling back procedure: {}'.format(self.name))
        i = 0
        while self._tasks_perform_stack:
            task, args, kwargs = self.pop_task()
            try:
                task.revert(*args, **kwargs)
            except:
                if i > 0:
                    print 'Failed to revert: {}:{}; error: {}'.format(
                        self.name, task.revert.func_name, traceback.format_exc(limit=1))
                    raise
                i += 1

    def run(self):
        """Running the procedure
        """
        print('Running procedure: {}'.format(self.name))
        try:
            self.perform()
        except:
            print 'Failed to run procedure: {}; error: {}'.format(
                self.name, traceback.format_exc())
            self.rollback()

    def perform(self):
        raise NotImplementedError('{}::perform function must be implemented'.format(self.__class__))
