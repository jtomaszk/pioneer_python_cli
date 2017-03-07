import json
from optparse import OptionParser

from connection import Connection
from telnet_lib import HOST, commandMap


# class ReadThread(threading.Thread):
#     """ This thread reads the lines coming back from telnet """
#
#     def __init__(self, c):
#         self.c = c
#         threading.Thread.__init__(self)
#
#     def run(self):
#         read_loop(self.c)


# We really want two threads: one with the output, another with the commands.
# def read_loop(c):
#     sys.stdout.flush()
#
#     count = 0
#     while True:
#         count += 1
#         response = c.read_response(count)
#         print json.dumps(response)


def print_help():
    l = commandMap.keys()
    l.sort()
    for x in l:
        print x


def write_loop(c):
    while True:
        command = raw_input("command: ").strip()
        if command == "quit" or command == "exit":
            print "Read thread says bye-bye!"
            # sys.exit()
            return
        elif command == "help" or command == "?":
            print_help()
        else:
            response = c.run_command([command])
            print json.dumps(response, sort_keys=True, indent=4)


def main():
    parser = OptionParser()

    (options, args) = parser.parse_args()
    if len(args) > 0:
        c = Connection(args[0])
    else:
        c = Connection(HOST)

    # send(tn, "?P") # to wake up

    # read_thread = ReadThread(c)
    # read_thread.daemon = True
    # read_thread.start()

    # the main thread does the writing, everyting exits when it does:
    write_loop(c)


# TODO: add command-line options to control, for example, displaying the info from the screen;
# also, for one-off commands.

if __name__ == "__main__":
    main()
