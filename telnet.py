#!/usr/bin/python

import sys
import telnetlib
import os
import time
import urllib
import threading
import socket
from modes_display import modeDisplayMap
from modes_set import modeSetMap, inverseModeSetMap

from optparse import OptionParser

# HOST = "10.0.1.32"      
HOST = "192.168.1.52"

_mode = None

inputMap = {
	"41" : "Pandora",
	"44" : "Media Server",
	"45" : "Favorites",
	"17" : "iPod/USB",
	"05" : "TV",
	"01" : "CD",
	"13" : "USB-DAC",
	"02" : "TUNER",	
	"00" : "PHONO",
	"12" : "MULTI CH IN",
	"33" : "ADAPTER PORT",
	"48" : "MHL",
	"31" : "HDMI" # cyclic
	}

commandMap = { "on" : "PO",
	"off": "PF",
	"up": "VU",
	"+": "VU",
	"down": "VD",
	"-": "VD",
	"mute": "MO",
	"unmute": "MF",

	"volume": "?V",
	
	"tone" : "9TO", # cyclic
	"tone off" : "0TO",
	"tone on" : "1TO",
	"treble up" : "TI",
	"treble down" : "TD",
	"treble reset" : "06TR",
	"bass up" : "BI",
	"bass down" : "BD",
	"bass reset" : "06BA",

	"mcacc" : "MC0", # cyclic

	# phase control is recommended to be on:
	"phase" : "IS9", # cyclic

        # cycle through stereo modes:
        "stereo" : "0001SR",
        "unplugged" : "0109SR",
        "extended" : "0112SR",

	"mode" : "?S",

	"loud" : "9ATW", # cyclic

        # switch inputs:
	"bd" : "25FN",
        "dvd" : "04FN",
	"sat" : "06FN",
	"video" : "10FN",
	"hdmi1" : "19FN",
	"hdmi2" : "20FN",
	"hdmi3" : "21FN",
	"hdmi4" : "22FN",
	"hdmi5" : "23FN",
	"hdmi6" : "24FN",
	"hdmi7" : "34FN",
	"net" : "26FN", # cyclic
        "cd" : "01FN",
	"iradio" : "38FN",
	"tv" : "15FN",
        "radio" : "02FN",
        "tuner" : "02FN",
        "phono" : "00FN", # invalid command
	"hdmi" : "31FN", # cyclic
        "pandora" : "41FN",
	

        # TODO: could have a pandora mode, radio mode, etc.
	# Pandora ones:
        "start" : "30NW",
        "next" : "13NW",
	"pause" : "11NW",
	"play" : "10NW",
	"previous" : "12NW",
	"stop" : "20NW",
	"clear" : "33NW",
	"repeat" : "34NW",
	"random" : "35NW",
	"menu" : "36NW",

        "info" : "?GAH",
	"list" : "?GAI",
	"top menu" : "19IP",

	# Tuner ones:
	"nextpreset" : "TPI",
	"prevpreset" : "TPD",
	"mpx" : "05TN",

         }


def print_help():
    l = commandMap.keys()
    l.sort()
    for x in l:
	print x


def send(tn, s):
    tn.write(s + b"\r\n")
    return readline(tn)

def readline(tn):
    s = tn.read_until(b"\r\n")
    return s[:-2]

def decodeFL(s):
    if not s.startswith('FL'):
          return None
    s = s[2:] #  the FL
    s = s[2:] # skip first two
    i = 0
    url = ""
    while i < len(s):
          url += "%"
          url += s[i:i+2]
          i += 2
    # print "Url is", url
    return urllib.unquote(url)

def parseError(s):
    if s == "E02" : return "NOT AVAILABLE NOW"
    if s == "E03" : return "INVALID COMMAND"
    if s == "E04" : return "COMMAND ERROR"
    if s == "E06" : return "PARAMETER ERROR"
    if s == "B00" : return "BUSY"
    return None

def decodeAST(s):
    if not s.startswith('AST'):
	return None
    s = s[3:]
    print "Audio input signal:", decode_ais( s[0:2] )
    print "Audio input frequency:", decode_aif( s[2:4] )
    # The manual starts counting at 1, so to fix this off-by-one, we do:
    s = '-' + s
    # channels...
    print "Input Channels:",
    if int(s[5]): print "Left, ",
    if int(s[6]): print "Center, ",
    if int(s[7]): print "Right, ",
    if int(s[8]): print "SL, ",
    if int(s[9]): print "SR, ",
    if int(s[10]): print "SBL, ",
    if int(s[11]): print "S, ",
    if int(s[12]): print "SBR, ",
    if int(s[13]): print "LFE, ",
    if int(s[14]): print "FHL, ",
    if int(s[15]): print "FHR, ",
    if int(s[16]): print "FWL, ",
    if int(s[17]): print "FWR, ",
    if int(s[18]): print "XL, ",
    if int(s[19]): print "XC, ",
    if int(s[20]): print "XR, ",
    print ""
    print "Output Channels:",
    if int(s[26]): print "Left, ",
    if int(s[27]): print "Center, ",
    if int(s[28]): print "Right, ",
    if int(s[29]): print "SL, ",
    if int(s[30]): print "SR, ",
    if int(s[31]): print "SBL, ",
    if int(s[32]): print "S, ",
    if int(s[33]): print "SBR, ",
    if int(s[34]): print "LFE, ",
    if int(s[35]): print "FHL, ",
    if int(s[36]): print "FHR, ",
    if int(s[37]): print "FWL, ",
    if int(s[38]): print "FWR, ",
    print ""
    sys.stdout.flush()
    return True

def decode_vst(s):
    if not s.startswith("VST"):
	return None
    s = s[3:]
    s = '=' + s

    return True

def decode_aif(s):
    if s=="00": return "32kHz"
    if s=="01": return "44.1kHz"
    if s=="02": return "48kHz"
    if s=="03": return "88.2kHz"
    if s=="04": return "96kHz"
    if s=="05": return "176.4kHz"
    if s=="06": return "192kHz"
    if s=="07": return "---"
    return None

def decode_ais(s):
    if s>="00" and s<="02": return "ANALOG"
    if s=="03" or s=="04": return "PCM"
    if s=="05": return "DOLBY DIGITAL"
    if s=="06": return "DTS"
    if s=="07": return "DTS-ES Matrix"
    if s=="08": return "DTS-ES Discrete"
    if s=="09": return "DTS 96/24"
    if s=="10": return "DTS 96/24 ES Matrix"
    if s=="11": return "DTS 96/24 ES Discrete"
    if s=="12": return "MPEG-2 AAC"
    if s=="13": return "WMA9 Pro"
    if s=="14": return "DSD->PCM"
    if s=="15": return "HDMI THROUGH"
    if s=="16": return "DOLBY DIGITAL PLUS"
    if s=="17": return "DOLBY TrueHD"
    if s=="18": return "DTS EXPRESS"
    if s=="19": return "DTS-HD Master Audio"
    if s>="20" and s<="26": return "DTS-HD High Resolution"
    if s=="27": return "DTS-HD Master Audio"
    return None

def db_level(s):
    n = int(s)
    db = 6 - n
    return "%ddB" % db

def decodeTone(s):
    if s.startswith("TR"):
	return "treble at " + db_level(s[2:4])
    if s.startswith("BA"):
	return "bass at " + db_level(s[2:4])
    if s == "TO0":
	return "tone off"
    if s == "TO1":
	return "tone on"
    return None

sourceMap = {"00" : "Intenet Radio",
	"01" : "Media Server",
	"06" : "SiriusXM",
	"07" : "Pandora",
	"10" : "AirPlay",
	"11" : "Digital Media Renderer (DMR)"
	}

typeMap = {"20" : "Track",
	"21" : "Artist",
	"22" : "Album",
	"23" : "Time",
	"24" : "Genre",
	"25" : "Chapter Number",
	"26" : "Format",
	"27" : "Bitrate",
	"28" : "Category",
	"29" : "Composer1",
	"30" : "Composer2",
	"31" : "Buffer",
	"32" : "Channel"
	}

screenTypeMap = {
	"00" : "Message",
	"01" : "List",
	"02" : "Playing (Play)",
	"03" : "Playing (Pause)",
	"04" : "Playing (Fwd)",
	"05" : "Playing (Rev)",
	"06" : "Playing (Stop)",
	"99" : "Invalid"
	}

def decodeGeh(s):
    if s.startswith("GDH"):
	bytes = s[3:]
	return "items " + bytes[0:5] + " to " + bytes[5:10] + " of total " + bytes[10:]
    if s.startswith("GBH"):
	return "max list number: " + s[2:]
    if s.startswith("GCH"):
	return screenTypeMap.get(s[3:5], "unknown")  + " - " + s
    if s.startswith('GHH'):
	source = s[2:]
	return "source: " + sourceMap.get(source, "unknown")
    if not s.startswith('GEH'):
	return None
    s = s[3:]
    line = s[0:2]
    focus = s[2]
    type = typeMap.get(s[3:5], "unknown (%s)" %s[3:5])
    info = s[5:]
    return type + ": " + info

# We really want two threads: one with the output, another with the commands.

def read_loop(c):
    sys.stdout.flush()

    count = 0
    while True:
      count += 1
      c.read_response(count)

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
         ret = run_command(c, command)
         print ret

      

def change_mode(tn, command):
    l = command.split(" ")
    if len(l) < 2:
	return None
    modestring = " ".join(l[1:])
    m = inverseModeSetMap.get(modestring, None)
    if m:
	send(tn, m + "SR")
	return True
    print "Unknown " + command
    return None

def second_arg(cmd):
    l = cmd.split(" ")
    if len(l) < 2:
        return ""
    return l[1].strip()

# Listening mode, in the order they appear in the spreadsheet. 
# looks like PDF doc has different ones (it's from 2010)
# These come from the list of listening mode requests, which is shorter than
# the list of displayed modes (above)

def translateMode(s):
    if not s.startswith('LM'):
	return None
    s = s[2:]
    m = modeDisplayMap.get(s, None)
    return m or "Unknown"



class ReadThread(threading.Thread):
      """ This thread reads the lines coming back from telnet """
      def __init__(self, c):
	self.c = c
	threading.Thread.__init__(self)
      def run(self):
	read_loop(self.c)

class Status(dict):
    def __init__(self, status, result):
       dict.__init__(self, ok=self.ok, status=status, result=result)
       self.status = status
       self.result = result

class StatusOk(Status):
    ok = True
       
class StatusError(Status):
    ok = False 

class Connection:
    tn = None
    def __init__(self, host):
        self.host = host
    def get_tn(self):
        return self.tn
    def is_connected(self):
        return self.tn is not None
    def get_status(self):
        #s = send(self.tn, "?BA")
        s = send(self.tn, "?L")
        s = self.parse_line(s)
        return StatusOk("ba", s)
#      send(tn, "?TR")
#      send(tn, "?TO")
#      send(tn, "?L")
#      send(tn, "?AST")

    def connect(self):
        try:
            self.tn = telnetlib.Telnet(HOST)
            self.tn.set_debuglevel(100)
            time.sleep(1)
            s = self.tn.read_very_eager()
            print "very eager: ", s
        except:
            print "connect error"          
        return self.tn
    def run_command(self, command):
        tn = self.tn
        if not self.is_connected():
            tn = self.connect()

        if self.tn is None:
            return StatusError("error", "error connect")

        if command == "status":
            return self.get_status()
        elif command.startswith("select"):
            s = second_arg(command).rjust(2,"0") + "GFI"
            return send(tn, s)
        elif command.startswith("display"):
            s = second_arg(command).rjust(5, "0") + "GCI" # may need to pad with zeros.
	    return send(tn, s)
        elif command.startswith("mode"):
            return change_mode(tn, command)
        elif commandMap.get(command, None):
            s = commandMap.get(command, None)
            return send(tn, s)
        elif command <> "":
            return send(tn, command) # try original one
        else:
            return "Invalid command"

    def read_response(self, count):
        if not self.is_connected():
            return count, "ERROR", "NOT CONNECTED"
    
        tn = self.get_tn()

        s = readline(tn)

    def parse_line(self, s):
        err = parseError(s)
        if err:
            return count, "ERROR: ", err
       
        tone = decodeTone(s)
        if tone:
	    return tone

        geh = decodeGeh(s)
        if geh:
	    return geh
        fl = decodeFL(s)
        if fl:
            return "%s\r" % fl
        if s.startswith('FN'):
            input = inputMap.get(s[2:], "unknown (%s)" % s)
            return "Input is", input
        if s.startswith('ATW'):
            return "loudness is ", "on" if s == "ATW1" else "off"
        if s.startswith('ATC'):
            return "eq is ", "on" if s == "ATC1" else "off"
        if s.startswith('ATD'):
            return "standing wave is ", "on" if s == "ATD1" else "off"
        if s.startswith('ATE'):
            num = s[3:]
            if num >= "00" and num <= "16":
                return "Phase control: " + num + "ms"
            elif num == "97":
	        return "Phase control: AUTO"
            elif num == "98":
	        return "Phase control: UP"
            elif num == "99":
                return "Phase control: DOWN"
            else:
                return "Phase control: unknown"
        m = translateMode(s)
        if m:
      	    return "Listening mode is %s (%s)" % (m, s)	
        elif s.startswith('AST') and decodeAST(s):
	    return None
        elif s.startswith('SR'):
	    code = s[2:]
	    v = modeSetMap.get(code, None)
	    if v:
	        return "mode is %s (%s)" % (v, s)
    # default:
        return count, s



# TODO: add command-line options to control, for example, displaying the info from the screen;
# also, for one-off commands.

if __name__ == "__main__":

      parser = OptionParser()
      
      (options, args) = parser.parse_args()
      if len(args) > 0:
	 HOST = args[0]

      c = Connection(HOST)

#      send(tn, "?P") # to wake up

      readThread = ReadThread(c)
      readThread.daemon = True
      readThread.start()

      # the main thread does the writing, everyting exits when it does:
      write_loop(c)
