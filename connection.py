import telnetlib
import threading
import time

from commands import commands
from status import StatusOk, StatusError, StatusParam
from telnet_lib import send, HOST, second_arg, change_mode, commandMap, read_line, parse_line


class ReadThread(threading.Thread):
    """ This thread reads the lines coming back from telnet """

    def __init__(self, c):
        self.c = c
        threading.Thread.__init__(self)

    def run(self):
        while True:
            success = self.c.read()
            if not success:
                time.sleep(5)

class Connection:
    tn = None
    results = {}

    def __init__(self, host):
        self.lock = threading.Lock()
        self.read_thread = ReadThread(self)
        self.read_thread.daemon = True
        self.read_thread.start()
        self.counter = 0
        self.host = host

    def get_and_increment_counter(self):
        with self.lock:
            self.counter += 1
        return self.counter

    def get_tn(self):
        return self.tn

    def is_connected(self):
        return self.tn is not None

    def get_status(self):
        response = [
            self.send("POWER"),
            self.send("VOLUME"),
            self.send("MUTE"),
            self.send("INPUT"),
            self.send("LISTENING_MODE"),
            self.send("PLAYING_LISTENING_MODE"),
            self.send("TUNER_FRQ"),
            self.send("TUNER_PRESENT")
        ]
        return StatusOk(response)

    def read(self):
        if not self.is_connected():
            return False

        raw = read_line(self.tn)
        parsed = parse_line(raw)
        count = self.get_and_increment_counter()
        if parsed[0] not in self.results or self.results[parsed[0]][0] < count:
            self.results[parsed[0]] = count, parsed[1]
        return True

    def send(self, command):
        raw_command = None
        raw_response = None

        for i in commands:
            if commands[i][0] == command:
                raw_command = commands[i][1]
                raw_response = i

        if raw_command is None:
            return None

        count = self.get_and_increment_counter()
        send(self.tn, raw_command)

        loop_count = 0

        while loop_count < 20:
            if raw_response in self.results and self.results[raw_response][0] > count:
                return StatusParam(command, self.results[raw_response][1])
            else:
                loop_count += 1
                time.sleep(0.2)

        return None

    @staticmethod
    def create_connection(debug=False):
        try:
            tn = telnetlib.Telnet(HOST)
            if debug:
                tn.set_debuglevel(100)
            time.sleep(1)
        except:
            tn = None
            print "connect error"
        return tn

    def run_command(self, command_list):
        if not self.is_connected():
            self.tn = self.create_connection()

        if self.tn is None:
            return StatusError(StatusParam("POWER", "OFFLINE"))

        command = command_list[0]

        if command == "status":
            return self.get_status()
        elif command == 'power':
            s = commandMap.get(command_list[1], None)
            return self.send(s)
        elif command.startswith("select"):
            s = second_arg(command).rjust(2, "0") + "GFI"
            return self.send(s)
        elif command.startswith("display"):
            s = second_arg(command).rjust(5, "0") + "GCI"  # may need to pad with zeros.
            return self.send(s)
        elif command.startswith("mode"):
            return change_mode(self.tn, command)
        elif commandMap.get(command, None):
            s = commandMap.get(command, None)
            return self.send(s)
        elif command != "":
            return self.send(command)  # try original one
        else:
            return "Invalid command"

    def read_response(self, count):
        if not self.is_connected():
            return count, "ERROR", "NOT CONNECTED"

        tn = self.get_tn()
        return
