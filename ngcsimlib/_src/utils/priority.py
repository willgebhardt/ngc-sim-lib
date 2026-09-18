
def priority(value=None):
    """
    This decorator is used while loading contexts. Objects are sorted by
    priority and then loaded from highest to lowest. The default priority is 0.

    Default priorities for base classes
    - Components: 0
    - Processes: -1
    - Context: 10

    A special note for the provided JointProcess class, while it has a default
    priority of -1, as it joins processes together it will update its priority
    to always be lower than all of its joined processes.

    :param value: The priority
    """
    def decorator(fn):
        fn._priority = value
        return fn
    return decorator
