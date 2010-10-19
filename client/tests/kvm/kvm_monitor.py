"""
Interfaces to the QEMU monitor.

@copyright: 2008-2010 Red Hat Inc.
"""

import socket, time, threading, logging
import kvm_utils
try:
    import json
except ImportError:
    logging.warning("Could not import json module. "
                    "QMP monitor functionality disabled.")


class MonitorError(Exception):
    pass


class MonitorConnectError(MonitorError):
    pass


class MonitorSendError(MonitorError):
    pass


class MonitorLockError(MonitorError):
    pass


class MonitorProtocolError(MonitorError):
    pass


class MonitorNotSupportedError(MonitorError):
    pass


class QMPCmdError(MonitorError):
    def __str__(self):
        return ("QMP command '%s' failed (arguments: %r, error message: %r)" %
                tuple(self.args))


class Monitor:
    """
    Common code for monitor classes.
    """

    def __init__(self, name, filename):
        """
        Initialize the instance.

        @param name: Monitor identifier (a string)
        @param filename: Monitor socket filename
        @raise MonitorConnectError: Raised if the connection fails
        """
        self.name = name
        self.filename = filename
        self._lock = threading.RLock()
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.setblocking(False)

        try:
            self._socket.connect(filename)
        except socket.error:
            raise MonitorConnectError("Could not connect to monitor socket")


    def __del__(self):
        # Automatically close the connection when the instance is garbage
        # collected
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self._socket.close()


    # The following two functions are defined to make sure the state is set
    # exclusively by the constructor call as specified in __getinitargs__().

    def __getstate__(self):
        pass


    def __setstate__(self, state):
        pass


    def __getinitargs__(self):
        # Save some information when pickling -- will be passed to the
        # constructor upon unpickling
        return self.name, self.filename, True


    def _acquire_lock(self, timeout=20):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._lock.acquire(False):
                return True
            time.sleep(0.05)
        return False


    def _recvall(self):
        s = ""
        while True:
            try:
                data = self._socket.recv(1024)
            except socket.error:
                break
            if not data:
                break
            s += data
        return s


class HumanMonitor(Monitor):
    """
    Wraps "human monitor" commands.
    """

    def __init__(self, name, filename, suppress_exceptions=False):
        """
        Connect to the monitor socket and find the (qemu) prompt.

        @param name: Monitor identifier (a string)
        @param filename: Monitor socket filename
        @raise MonitorConnectError: Raised if the connection fails and
                suppress_exceptions is False
        @raise MonitorProtocolError: Raised if the initial (qemu) prompt isn't
                found and suppress_exceptions is False
        @note: Other exceptions may be raised.  See cmd()'s
                docstring.
        """
        try:
            Monitor.__init__(self, name, filename)

            self.protocol = "human"

            # Find the initial (qemu) prompt
            s, o = self._read_up_to_qemu_prompt(20)
            if not s:
                raise MonitorProtocolError("Could not find (qemu) prompt "
                                           "after connecting to monitor. "
                                           "Output so far: %r" % o)

            # Save the output of 'help' for future use
            self._help_str = self.cmd("help")

        except MonitorError, e:
            if suppress_exceptions:
                logging.warn(e)
            else:
                raise


    # Private methods

    def _read_up_to_qemu_prompt(self, timeout=20):
        o = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                data = self._socket.recv(1024)
                if not data:
                    break
                o += data
                if o.splitlines()[-1].split()[-1] == "(qemu)":
                    return True, "\n".join(o.splitlines()[:-1])
            except (socket.error, IndexError):
                time.sleep(0.01)
        return False, "\n".join(o.splitlines())


    def _send(self, cmd):
        """
        Send a command without waiting for output.

        @param cmd: Command to send
        @raise MonitorLockError: Raised if the lock cannot be acquired
        @raise MonitorSendError: Raised if the command cannot be sent
        """
        if not self._acquire_lock(20):
            raise MonitorLockError("Could not acquire exclusive lock to send "
                                   "monitor command '%s'" % cmd)

        try:
            try:
                self._socket.sendall(cmd + "\n")
            except socket.error:
                raise MonitorSendError("Could not send monitor command '%s'" %
                                       cmd)

        finally:
            self._lock.release()


    # Public methods

    def cmd(self, command, timeout=20):
        """
        Send command to the monitor.

        @param command: Command to send to the monitor
        @param timeout: Time duration to wait for the (qemu) prompt to return
        @return: Output received from the monitor
        @raise MonitorLockError: Raised if the lock cannot be acquired
        @raise MonitorSendError: Raised if the command cannot be sent
        @raise MonitorProtocolError: Raised if the (qemu) prompt cannot be
                found after sending the command
        """
        if not self._acquire_lock(20):
            raise MonitorLockError("Could not acquire exclusive lock to send "
                                   "monitor command '%s'" % command)

        try:
            # Read any data that might be available
            self._recvall()
            # Send command
            self._send(command)
            # Read output
            s, o = self._read_up_to_qemu_prompt(timeout)
            # Remove command echo from output
            o = "\n".join(o.splitlines()[1:])
            # Report success/failure
            if s:
                return o
            else:
                msg = ("Could not find (qemu) prompt after command '%s'. "
                       "Output so far: %r" % (command, o))
                raise MonitorProtocolError(msg)

        finally:
            self._lock.release()


    def is_responsive(self):
        """
        Make sure the monitor is responsive by sending a command.

        @return: True if responsive, False otherwise
        """
        try:
            self.cmd("info status")
            return True
        except MonitorError:
            return False


    # Command wrappers
    # Notes:
    # - All of the following commands raise exceptions in a similar manner to
    #   cmd().
    # - A command wrapper should use self._help_str if it requires information
    #   about the monitor's capabilities.

    def quit(self):
        """
        Send "quit" without waiting for output.
        """
        self._send("quit")


    def info(self, what):
        """
        Request info about something and return the output.
        """
        return self.cmd("info %s" % what)


    def query(self, what):
        """
        Alias for info.
        """
        return self.info(what)


    def screendump(self, filename):
        """
        Request a screendump.

        @param filename: Location for the screendump
        @return: The command's output
        """
        return self.cmd("screendump %s" % filename)


    def migrate(self, uri, full_copy=False, incremental_copy=False, wait=False):
        """
        Migrate.

        @param uri: destination URI
        @param full_copy: If true, migrate with full disk copy
        @param incremental_copy: If true, migrate with incremental disk copy
        @param wait: If true, wait for completion
        @return: The command's output
        """
        logging.debug("Migrating to: %s" % uri)
        cmd = "migrate"
        if not wait:
            cmd += " -d"
        if full_copy:
            cmd += " -b"
        if incremental_copy:
            cmd += " -i"
        cmd += " %s" % uri
        return self.cmd(cmd)


    def migrate_set_speed(self, value):
        """
        Set maximum speed (in bytes/sec) for migrations.

        @param value: Speed in bytes/sec
        @return: The command's output
        """
        return self.cmd("migrate_set_speed %s" % value)


    def sendkey(self, keystr, hold_time=1):
        """
        Send key combination to VM.

        @param keystr: Key combination string
        @param hold_time: Hold time in ms (should normally stay 1 ms)
        @return: The command's output
        """
        return self.cmd("sendkey %s %s" % (keystr, hold_time))


    def mouse_move(self, dx, dy):
        """
        Move mouse.

        @param dx: X amount
        @param dy: Y amount
        @return: The command's output
        """
        return self.cmd("mouse_move %d %d" % (dx, dy))


    def mouse_button(self, state):
        """
        Set mouse button state.

        @param state: Button state (1=L, 2=M, 4=R)
        @return: The command's output
        """
        return self.cmd("mouse_button %d" % state)


class QMPMonitor(Monitor):
    """
    Wraps QMP monitor commands.
    """

    def __init__(self, name, filename, suppress_exceptions=False):
        """
        Connect to the monitor socket, read the greeting message and issue the
        qmp_capabilities command.  Also make sure the json module is available.

        @param name: Monitor identifier (a string)
        @param filename: Monitor socket filename
        @raise MonitorConnectError: Raised if the connection fails and
                suppress_exceptions is False
        @raise MonitorProtocolError: Raised if the no QMP greeting message is
                received and suppress_exceptions is False
        @raise MonitorNotSupportedError: Raised if json isn't available and
                suppress_exceptions is False
        @note: Other exceptions may be raised if the qmp_capabilities command
                fails.  See cmd()'s docstring.
        """
        try:
            Monitor.__init__(self, name, filename)

            self.protocol = "qmp"
            self._greeting = None
            self._events = []

            # Make sure json is available
            try:
                json
            except NameError:
                raise MonitorNotSupportedError("QMP requires the json module "
                                               "(Python 2.6 and up)")

            # Read greeting message
            end_time = time.time() + 20
            while time.time() < end_time:
                for obj in self._read_objects():
                    if "QMP" in obj:
                        self._greeting = obj
                        break
                if self._greeting:
                    break
                time.sleep(0.1)
            else:
                raise MonitorProtocolError("No QMP greeting message received")

            # Issue qmp_capabilities
            self.cmd("qmp_capabilities")

        except MonitorError, e:
            if suppress_exceptions:
                logging.warn(e)
            else:
                raise


    # Private methods

    def _build_cmd(self, cmd, args=None, id=None):
        obj = {"execute": cmd}
        if args is not None:
            obj["arguments"] = args
        if id is not None:
            obj["id"] = id
        return obj


    def _read_objects(self, timeout=5):
        """
        Read lines from monitor and try to decode them.
        Stop when all available lines have been successfully decoded, or when
        timeout expires.  If any decoded objects are asynchronous events, store
        them in self._events.  Return all decoded objects.

        @param timeout: Time to wait for all lines to decode successfully
        @return: A list of objects
        """
        s = ""
        objs = []
        end_time = time.time() + timeout
        while time.time() < end_time:
            s += self._recvall()
            for line in s.splitlines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except:
                    # Found an incomplete or broken line -- keep reading
                    break
                objs += [obj]
            else:
                # All lines are OK -- stop reading
                break
            time.sleep(0.1)
        # Keep track of asynchronous events
        self._events += [obj for obj in objs if "event" in obj]
        return objs


    def _send(self, data):
        """
        Send raw data without waiting for response.

        @param data: Data to send
        @raise MonitorSendError: Raised if the data cannot be sent
        """
        try:
            self._socket.sendall(data)
        except socket.error:
            raise MonitorSendError("Could not send data: %r" % data)


    def _get_response(self, id=None, timeout=20):
        """
        Read a response from the QMP monitor.

        @param id: If not None, look for a response with this id
        @param timeout: Time duration to wait for response
        @return: The response dict, or None if none was found
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            for obj in self._read_objects():
                if isinstance(obj, dict):
                    if id is not None and obj.get("id") != id:
                        continue
                    if "return" in obj or "error" in obj:
                        return obj
            time.sleep(0.1)


    # Public methods

    def cmd(self, cmd, args=None, timeout=20):
        """
        Send a QMP monitor command and return the response.

        Note: an id is automatically assigned to the command and the response
        is checked for the presence of the same id.

        @param cmd: Command to send
        @param args: A dict containing command arguments, or None
        @param timeout: Time duration to wait for response
        @return: The response received
        @raise MonitorLockError: Raised if the lock cannot be acquired
        @raise MonitorSendError: Raised if the command cannot be sent
        @raise MonitorProtocolError: Raised if no response is received
        @raise QMPCmdError: Raised if the response is an error message
                (the exception's args are (cmd, args, data) where data is the
                error data)
        """
        if not self._acquire_lock(20):
            raise MonitorLockError("Could not acquire exclusive lock to send "
                                   "QMP command '%s'" % cmd)

        try:
            # Read any data that might be available
            self._read_objects()
            # Send command
            id = kvm_utils.generate_random_string(8)
            self._send(json.dumps(self._build_cmd(cmd, args, id)) + "\n")
            # Read response
            r = self._get_response(id, timeout)
            if r is None:
                raise MonitorProtocolError("Received no response to QMP "
                                           "command '%s', or received a "
                                           "response with an incorrect id"
                                           % cmd)
            if "return" in r:
                return r["return"]
            if "error" in r:
                raise QMPCmdError(cmd, args, r["error"])

        finally:
            self._lock.release()


    def cmd_raw(self, data, timeout=20):
        """
        Send a raw string to the QMP monitor and return the response.
        Unlike cmd(), return the raw response dict without performing any
        checks on it.

        @param data: The data to send
        @param timeout: Time duration to wait for response
        @return: The response received
        @raise MonitorLockError: Raised if the lock cannot be acquired
        @raise MonitorSendError: Raised if the command cannot be sent
        @raise MonitorProtocolError: Raised if no response is received
        """
        if not self._acquire_lock(20):
            raise MonitorLockError("Could not acquire exclusive lock to send "
                                   "data: %r" % data)

        try:
            self._read_objects()
            self._send(data)
            r = self._get_response(None, timeout)
            if r is None:
                raise MonitorProtocolError("Received no response to data: %r" %
                                           data)
            return r

        finally:
            self._lock.release()


    def cmd_obj(self, obj, timeout=20):
        """
        Transform a Python object to JSON, send the resulting string to the QMP
        monitor, and return the response.
        Unlike cmd(), return the raw response dict without performing any
        checks on it.

        @param obj: The object to send
        @param timeout: Time duration to wait for response
        @return: The response received
        @raise MonitorLockError: Raised if the lock cannot be acquired
        @raise MonitorSendError: Raised if the command cannot be sent
        @raise MonitorProtocolError: Raised if no response is received
        """
        return self.cmd_raw(json.dumps(obj) + "\n")


    def cmd_qmp(self, cmd, args=None, id=None, timeout=20):
        """
        Build a QMP command from the passed arguments, send it to the monitor
        and return the response.
        Unlike cmd(), return the raw response dict without performing any
        checks on it.

        @param obj: The object to send
        @param timeout: Time duration to wait for response
        @return: The response received
        @raise MonitorLockError: Raised if the lock cannot be acquired
        @raise MonitorSendError: Raised if the command cannot be sent
        @raise MonitorProtocolError: Raised if no response is received
        """
        return self.cmd_obj(self._build_cmd(cmd, args, id), timeout)


    def is_responsive(self):
        """
        Make sure the monitor is responsive by sending a command.

        @return: True if responsive, False otherwise
        """
        try:
            self.cmd("query-status")
            return True
        except MonitorError:
            return False


    def get_events(self):
        """
        Return a list of the asynchronous events received since the last
        clear_events() call.

        @return: A list of events (the objects returned have an "event" key)
        @raise MonitorLockError: Raised if the lock cannot be acquired
        """
        if not self._acquire_lock(20):
            raise MonitorLockError("Could not acquire exclusive lock to read "
                                   "QMP events")
        try:
            self._read_objects()
            return self._events[:]
        finally:
            self._lock.release()


    def get_event(self, name):
        """
        Look for an event with the given name in the list of events.

        @param name: The name of the event to look for (e.g. 'RESET')
        @return: An event object or None if none is found
        """
        for e in self.get_events():
            if e.get("event") == name:
                return e


    def clear_events(self):
        """
        Clear the list of asynchronous events.

        @raise MonitorLockError: Raised if the lock cannot be acquired
        """
        if not self._acquire_lock(20):
            raise MonitorLockError("Could not acquire exclusive lock to clear "
                                   "QMP event list")
        self._events = []
        self._lock.release()


    def get_greeting(self):
        """
        Return QMP greeting message.
        """
        return self._greeting


    # Command wrappers
    # Note: all of the following functions raise exceptions in a similar manner
    # to cmd().

    def quit(self):
        """
        Send "quit" and return the response.
        """
        return self.cmd("quit")


    def info(self, what):
        """
        Request info about something and return the response.
        """
        return self.cmd("query-%s" % what)


    def query(self, what):
        """
        Alias for info.
        """
        return self.info(what)


    def screendump(self, filename):
        """
        Request a screendump.

        @param filename: Location for the screendump
        @return: The response to the command
        """
        args = {"filename": filename}
        return self.cmd("screendump", args)


    def migrate(self, uri, full_copy=False, incremental_copy=False, wait=False):
        """
        Migrate.

        @param uri: destination URI
        @param full_copy: If true, migrate with full disk copy
        @param incremental_copy: If true, migrate with incremental disk copy
        @param wait: If true, wait for completion
        @return: The response to the command
        """
        args = {"uri": uri,
                "blk": full_copy,
                "inc": incremental_copy}
        return self.cmd("migrate", args)


    def migrate_set_speed(self, value):
        """
        Set maximum speed (in bytes/sec) for migrations.

        @param value: Speed in bytes/sec
        @return: The response to the command
        """
        args = {"value": value}
        return self.cmd("migrate_set_speed", args)
