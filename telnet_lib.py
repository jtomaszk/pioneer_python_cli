#!/usr/bin/python

import sys
import urllib
import re

from commands import response_on_off
from modes_display import modeDisplayMap
from modes_set import inverseModeSetMap, modeSetMap
from decimal import Decimal

HOST = "192.168.1.52"

_mode = None

inputMap = {
    "41": "Pandora",
    "44": "Media Server",
    "45": "Favorites",
    "17": "iPod/USB",
    "05": "TV",
    "01": "CD",
    "13": "USB-DAC",
    "02": "TUNER",
    "00": "PHONO",
    "12": "MULTI CH IN",
    "33": "ADAPTER PORT",
    "48": "MHL",
    "31": "HDMI"  # cyclic
}

commandMap = {
    "on": "PO",
    "off": "PF",
    "up": "VU",
    "+": "VU",
    "down": "VD",
    "-": "VD",
    "mute": "MO",
    "unmute": "MF",

    "volume": "?V",

    "tone": "9TO",  # cyclic
    "tone off": "0TO",
    "tone on": "1TO",
    "treble up": "TI",
    "treble down": "TD",
    "treble reset": "06TR",
    "bass up": "BI",
    "bass down": "BD",
    "bass reset": "06BA",

    "mcacc": "MC0",  # cyclic

    # phase control is recommended to be on:
    "phase": "IS9",  # cyclic

    # cycle through stereo modes:
    "stereo": "0001SR",
    "unplugged": "0109SR",
    "extended": "0112SR",

    "mode": "?S",

    "loud": "9ATW",  # cyclic

    # switch inputs:
    "bd": "25FN",
    "dvd": "04FN",
    "sat": "06FN",
    "video": "10FN",
    "hdmi1": "19FN",
    "hdmi2": "20FN",
    "hdmi3": "21FN",
    "hdmi4": "22FN",
    "hdmi5": "23FN",
    "hdmi6": "24FN",
    "hdmi7": "34FN",
    "net": "26FN",  # cyclic
    "cd": "01FN",
    "iradio": "38FN",
    "tv": "15FN",
    "radio": "02FN",
    "tuner": "02FN",
    "phono": "00FN",  # invalid command
    "hdmi": "31FN",  # cyclic
    "pandora": "41FN",

    # TODO: could have a pandora mode, radio mode, etc.
    # Pandora ones:
    "start": "30NW",
    "next": "13NW",
    "pause": "11NW",
    "play": "10NW",
    "previous": "12NW",
    "stop": "20NW",
    "clear": "33NW",
    "repeat": "34NW",
    "random": "35NW",
    "menu": "36NW",

    "info": "?GAH",
    "list": "?GAI",
    "top menu": "19IP",

    # Tuner ones:
    "nextpreset": "TPI",
    "prevpreset": "TPD",
    "mpx": "05TN",
}


def send(tn, s):
    tn.write(s + b"\r\n")


def read_line(tn):
    s = tn.read_until(b"\r\n")
    return s[:-2]


def decode_fl(s):
    if not s.startswith('FL'):
        return None
    s = s[2:]  # the FL
    s = s[2:]  # skip first two
    i = 0
    url = ""
    while i < len(s):
        url += "%"
        url += s[i:i + 2]
        i += 2
    # print "Url is", url
    return urllib.unquote(url)


def parse_error(s):
    if s == "E02": return "NOT AVAILABLE NOW"
    if s == "E03": return "INVALID COMMAND"
    if s == "E04": return "COMMAND ERROR"
    if s == "E06": return "PARAMETER ERROR"
    if s == "B00": return "BUSY"
    return None


def decode_ast(s):
    if not s.startswith('AST'):
        return None
    s = s[3:]
    print "Audio input signal:", decode_ais(s[0:2])
    print "Audio input frequency:", decode_aif(s[2:4])
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
    if s == "00": return "32kHz"
    if s == "01": return "44.1kHz"
    if s == "02": return "48kHz"
    if s == "03": return "88.2kHz"
    if s == "04": return "96kHz"
    if s == "05": return "176.4kHz"
    if s == "06": return "192kHz"
    if s == "07": return "---"
    return None


def decode_ais(s):
    if "00" <= s <= "02": return "ANALOG"
    if s == "03" or s == "04": return "PCM"
    if s == "05": return "DOLBY DIGITAL"
    if s == "06": return "DTS"
    if s == "07": return "DTS-ES Matrix"
    if s == "08": return "DTS-ES Discrete"
    if s == "09": return "DTS 96/24"
    if s == "10": return "DTS 96/24 ES Matrix"
    if s == "11": return "DTS 96/24 ES Discrete"
    if s == "12": return "MPEG-2 AAC"
    if s == "13": return "WMA9 Pro"
    if s == "14": return "DSD->PCM"
    if s == "15": return "HDMI THROUGH"
    if s == "16": return "DOLBY DIGITAL PLUS"
    if s == "17": return "DOLBY TrueHD"
    if s == "18": return "DTS EXPRESS"
    if s == "19": return "DTS-HD Master Audio"
    if "20" <= s <= "26": return "DTS-HD High Resolution"
    if s == "27": return "DTS-HD Master Audio"
    return None


def db_level(s):
    n = int(s)
    db = 6 - n
    return "%ddB" % db


def decode_tone(s):
    if s.startswith("TR"):
        return "treble at " + db_level(s[2:4])
    if s.startswith("BA"):
        return "bass at " + db_level(s[2:4])
    if s == "TO0":
        return "tone off"
    if s == "TO1":
        return "tone on"
    return None


sourceMap = {"00": "Intenet Radio",
             "01": "Media Server",
             "06": "SiriusXM",
             "07": "Pandora",
             "10": "AirPlay",
             "11": "Digital Media Renderer (DMR)"
             }

typeMap = {"20": "Track",
           "21": "Artist",
           "22": "Album",
           "23": "Time",
           "24": "Genre",
           "25": "Chapter Number",
           "26": "Format",
           "27": "Bitrate",
           "28": "Category",
           "29": "Composer1",
           "30": "Composer2",
           "31": "Buffer",
           "32": "Channel"
           }

screenTypeMap = {
    "00": "Message",
    "01": "List",
    "02": "Playing (Play)",
    "03": "Playing (Pause)",
    "04": "Playing (Fwd)",
    "05": "Playing (Rev)",
    "06": "Playing (Stop)",
    "99": "Invalid"
}


def decode_geh(s):
    if s.startswith("GDH"):
        bytes = s[3:]
        return "items " + bytes[0:5] + " to " + bytes[5:10] + " of total " + bytes[10:]
    if s.startswith("GBH"):
        return "max list number: " + s[2:]
    if s.startswith("GCH"):
        return screenTypeMap.get(s[3:5], "unknown") + " - " + s
    if s.startswith('GHH'):
        source = s[2:]
        return "source: " + sourceMap.get(source, "unknown")
    if not s.startswith('GEH'):
        return None
    s = s[3:]
    line = s[0:2]
    focus = s[2]
    type = typeMap.get(s[3:5], "unknown (%s)" % s[3:5])
    info = s[5:]
    return type + ": " + info


def change_mode(tn, command):
    l = command.split(" ")
    if len(l) < 2:
        return None
    mode_string = " ".join(l[1:])
    m = inverseModeSetMap.get(mode_string, None)
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

def translate_mode(s):
    if not s.startswith('LM'):
        return None
    s = s[2:]
    m = modeDisplayMap.get(s, None)
    return m or "Unknown"


def raw_to_simple(cmd_raw):
    val = re.sub('[^A-Z]', '', cmd_raw)
    if val.startswith('F'):
        return val[:2]
    return val


def parse_line(cmd_raw):
    err = parse_error(cmd_raw)
    if err:
        return "ERROR: ", err

    s = raw_to_simple(cmd_raw)

    if s in response_on_off:
        return s, on_off_value(cmd_raw)

    if s.startswith('FR'):
        band_map = {
            'A': 'AM',
            'F': 'FM',
        }
        band = band_map[cmd_raw[2:3]]
        freq = Decimal(cmd_raw[3:]) / 100
        return s, str(freq) + " " + band
    
    tone = decode_tone(cmd_raw)
    if tone:
        return s, tone

    geh = decode_geh(cmd_raw)
    if geh:
        return s, geh
    fl = decode_fl(cmd_raw)
    if fl:
        return s, "%s\r" % fl
    if s.startswith('FN'):
        return s, inputMap.get(cmd_raw[2:], "unknown (%s)" % cmd_raw)
    elif s.startswith('ATE'):
        num = cmd_raw[3:]
        if "00" <= num <= "16":  # Phase control:
            return s, num + "ms"
        elif num == "97":
            return s, "AUTO"
        elif num == "98":
            return s, "UP"
        elif num == "99":
            return s, "DOWN"
        else:
            return s, "unknown"
    m = translate_mode(s)
    if m:  # Listening mode is
        return s, "%s (%s)" % (m, s)
    elif s.startswith('AST') and decode_ast(cmd_raw):
        return s, None
    elif s.startswith('SR'):
        code = cmd_raw[2:]
        v = modeSetMap.get(code, None)
        if v:  # mode is
            return s, "%s (%s)" % (v, cmd_raw)
    return s, cmd_raw


def on_off_value(s):
    return "ON" if s.endswith("0") else "OFF"
