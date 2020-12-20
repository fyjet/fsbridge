"""
    Bridge for flight simulator (tested with fs2004 and fsX) to MQTT

    Sends and receive commands over mqtt topics/values, remote device is an esp32

    esp32 wroom pin mapping
    TODO

    Steps to run:
    1. run mosquitto
    2. run FSX or FS4
    3. plug ESP
    4. run fsbridge:
        python fsbridge.py
        or simply fsbridge.py
"""
import paho.mqtt.client as mqtt
import sys,logging, time
from modules.fsconvert import *
import pyuipc
from modules.Event import Event
from modules.Panel import Panel
import configparser
from logging.config import fileConfig
from modules.Config import Config
from modules.Const import Const

from panels.RtuCom import RtuCom
from panels.RtuNav import RtuNav
from panels.Home import Home
from panels.Audio import Audio
from panels.AP import AP
from panels.Trim import Trim
from panels.Perfs import Perfs

#Configuration
config = configparser.ConfigParser()
config.read("fsbridge.ini")

#Logger
fileConfig("logging.ini")
logging.getLogger()

# Default mode at startup
actMode="Home"
APStatus=0
logging.info("Starting fsbridge")

"""
Pyuipc variables type
  - b: a 1-byte unsigned value, to be converted into a Python int
  - c: a 1-byte signed value, to be converted into a Python int
  - h: a 2-byte signed value, to be converted into a Python int
  - H: a 2-byte unsigned value, to be converted into a Python int
  - d: a 4-byte signed value, to be converted into a Python int
  - u: a 4-byte unsigned value, to be converted into a Python long
  - l: an 8-byte signed value, to be converted into a Python long
  - L: an 8-byte unsigned value, to be converted into a Python long
  - f: an 8-byte floating point value, to be converted into a Python double
  - F: a 4-byte floating point value, to be converted into a Python double

"""

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server """

    logging.info("Connected to MQTT server (result code "+str(rc)+")")
    client.subscribe(Config.topic_prefix+"/#")

def on_message(client, userdata, msg):

    """ The callback for when a PUBLISH message is received from the server """

    logging.debug("Message received "+msg.topic+" "+str(msg.payload))
    event.set(msg.topic, msg.payload)

    return

def setup():
    global pyuipcOffsets, oldActMode, alivetime, client, event, oldAPStatus, OFFSETS

    # Connect to flight simulator via FSUIPC (pyuipc)
    try:
        pyuipcConnection = pyuipc.open(0)
    except pyuipc.FSUIPCException:
        logging.critical("Unable to connect FSUIPC: check Flight Sim is running first. Exit")
        sys.exit(1);
    logging.info("Connected to FSUIPC")

    # MQTT borcker connection on localhost
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    logging.debug("Trying to connect to MQTT server "+config.get('MQTT','server')+" on port "+config.get('MQTT','port'))
    client.connect(config.get('MQTT','server'), config.getint('MQTT','port'), 60)
    client.loop_start()
    logging.info("Connectes to MQTT server "+config.get('MQTT','server'))

    oldActMode=""
    alivetime=time.time()   # the keepalive ticker
    event=Event()
    oldAPStatus=-1
    #        AP STATUS    HAS AP
    OFFSETS=[(0x07BC,'u'),(0x0764,'u')]
    pyuipcOffsets = pyuipc.prepare_data(OFFSETS)

def loop():
    global pyuipcOffsets, oldActMode, actMode, client, alivetime, hasAP, oldAPStatus, panel, APStatus

    results = pyuipc.read(pyuipcOffsets)
    APStatus=results[0]
    hasAP=results[1]

    if (oldActMode!=actMode):
        # Instanciate panel class child, specific to each panel
        logging.info("Changing mode to "+actMode)

        if actMode=="Home":
            panel=Home(client)
        if actMode=="RtuCom":
            panel=RtuCom(client)
        if actMode=="RtuNav":
            panel=RtuNav(client)
        if actMode=="Audio":
            panel=Audio(client)
        if actMode=="AP":
            panel=AP(client)
        if actMode=="Perfs":
            panel=Perfs(client)
        if actMode=="Trim":
            panel=Trim(client)
        oldActMode=actMode

    # loop that updates panel
    panel.run(event)
    if event.getPayload()==str(Const.BTMAIN): #return to home
        actMode="Home"
        event.clear()
    if event.getPayload()==str(Const.BTAP): # AP
        APStatus=APStatus^1
        event.clear()

    # de/activate autopilot
    if (APStatus!=oldAPStatus):
        if (APStatus==0):
            client.publish(Config.topic_display, "X")
            client.publish(Config.topic_display, "L,0")
            # Beep when AP is disabled
            client.publish(Config.topic_display, "X")
        else:
            client.publish(Config.topic_display, "L,1")
        pyuipc.write([(OFFSETS[0][0],OFFSETS[0][1],APStatus)])
        oldAPStatus=APStatus

    # keepalive to esp32 module every 2 seconds, just say "i'm here"

    if ((time.time() - alivetime) > 2):
        logging.debug("Send keep alive to esp32 module")
        client.publish(Config.topic_prefix+"/c/reqstatus", "1")
        alivetime=time.time()


if __name__ == "__main__":

    setup()

    while True:
        loop()