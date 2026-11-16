"""Isolated prototype: nonblocking hash-command input state machine."""
class CommandEntry:
    def __init__(self, timeout=1.5):
        self.timeout = timeout
        self.buffer = None
        self.deadline = 0.0

    def expire(self, now):
        if self.buffer is not None and now >= self.deadline:
            command = self.buffer.casefold()
            self.buffer = None
            return command or None
        return None

    def feed(self, key, now):
        """Return (consumed, completed command). Caller polls expire while idle."""
        expired = self.expire(now)
        if expired is not None:
            return False, expired
        if self.buffer is None:
            if key != '#':
                return False, None
            self.buffer = ''
            self.deadline = now + self.timeout
            return True, None
        if key in ('\x1b', '\x03'):
            self.buffer = None
            return True, None
        if key in ('\r', '\n'):
            command = self.buffer.casefold()
            self.buffer = None
            return True, command or None
        if key in ('\b', '\x7f'):
            self.buffer = self.buffer[:-1]
        elif len(key) == 1 and key.isascii() and key.isalnum():
            self.buffer = (self.buffer + key)[:32]
        self.deadline = now + self.timeout
        return True, None
