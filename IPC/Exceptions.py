import time

class CannotAttachSharedMemory(Exception):
    pass

class CannotAcquireLock(Exception):
    def __init__(self, *args, blocking_pid=0, timestamp=None, **kwargs):
        super().__init__('Cannot acquire lock', *args, *kwargs)
        self.blocking_pid = blocking_pid
        self.timestamp = timestamp or time.monotonic()

class CannotAcquireLockTimeout(CannotAcquireLock):
    def __init__(self, *args, time_passed=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_passed = time_passed

class ParameterMismatch(Exception):
    pass

class AlreadyClosed(Exception):
    pass

class AlreadyExists(Exception):
    pass

class FullDumpMemoryFull(Exception):
    pass

class MissingDependency(Exception):
    pass


class NotImplemeted(Exception):
    pass
