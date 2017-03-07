import telnetlib

import time

from commands import commands
from status import StatusOk, StatusError, StatusParam
from telnet_lib import send, HOST, second_arg, change_mode, commandMap, read_line, parse_line


class Connection:
    tn = None
    commands_reversed = {}

    def __init__(self, host):
        for i in commands:
            self.commands_reversed[commands[i]] = i
        self.host = host

    def get_tn(self):
        return self.tn

    def is_connected(self):
        return self.tn is not None

    def get_status(self):
        # s = send(self.tn, "")
        response = [
            self.send_query_and_convert("POWER"),
            self.send_query_and_convert("VOLUME"),
            self.send_query_and_convert("MUTE"),
            self.send_query_and_convert("INPUT"),
            self.send_query_and_convert("LISTENING_MODE"),
            self.send_query_and_convert("PLAYING_LISTENING_MODE"),
            self.send_query_and_convert("TUNER_FRQ"),
            self.send_query_and_convert("TUNER_PRESENT")
        ]
        return StatusOk(response)

    def send_query_and_convert(self, command):
        raw_command = "?" + self.commands_reversed[command]
        raw = send(self.tn, raw_command)
        parsed = parse_line(raw) 
        return StatusParam(command, parsed)

    def send_and_convert(self, raw_command):
        raw = send(self.tn, raw_command)
        parsed = parse_line(raw)  
        return StatusParam(raw_command, parsed)

    def connect(self):
        try:
            tn = telnetlib.Telnet(HOST)
            tn.set_debuglevel(100)
            time.sleep(1)
            s = self.tn.read_very_eager()
            print "very eager: ", s
        except:
            tn = None
            print "connect error"
        return tn

    def run_command(self, command_list):
        if not self.is_connected():
            self.tn = self.connect()

        if self.tn is None:
            return StatusError(StatusParam("POWER", "OFFLINE"))

        command = command_list[0]

        if command == "status":
            return self.get_status()
        elif command == 'power':
            s = commandMap.get(command_list[1], None)
            return self.send_and_convert(s)
        elif command.startswith("select"):
            s = second_arg(command).rjust(2, "0") + "GFI"
            return self.send_query_and_convert(s)
        elif command.startswith("display"):
            s = second_arg(command).rjust(5, "0") + "GCI"  # may need to pad with zeros.
            return self.send_query_and_convert(s)
        elif command.startswith("mode"):
            return change_mode(tn, command)
        elif commandMap.get(command, None):
            s = commandMap.get(command, None)
            return self.send_query_and_convert(s)
        elif command != "":
            return self.send_query_and_convert(command)  # try original one
        else:
            return "Invalid command"

    def read_response(self, count):
        if not self.is_connected():
            return count, "ERROR", "NOT CONNECTED"

        tn = self.get_tn()
        return read_line(tn)
