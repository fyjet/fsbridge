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
import fsconvert
import pyuipc
from Event import Event
import configparser
from logging.config import fileConfig

#Configuration
config = configparser.ConfigParser()
config.read("fsbridge.ini")

#Logger
fileConfig("logging.ini")
logger = logging.getLogger()

# Default mode at startup
actMode="Home"
APStatus=0
logger.info("Starting fsbridge")

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

class Const:
    LSK1=1
    LSK2=2
    LSK3=3
    LSK4=4
    LSK5=5
    LSK6=6
    LSK7=7
    LSK8=8
    
    LCK1=11
    LCK2=12
    LCK3=13
    LCK4=14
    LCK5=15
    LCK6=16
    LCK7=17
    LCK8=18
    
    RCK1=21
    RCK2=22
    RCK3=23
    RCK4=24
    RCK5=25
    RCK6=26
    RCK7=27
    RCK8=28
    
    RSK1=31
    RSK2=32
    RSK3=33
    RSK4=34
    RSK5=35
    RSK6=36
    RSK7=37
    RSK8=38
    
    ENC1DN=50
    ENC1UP=51
    ENC2DN=52
    ENC2UP=53
    
    BTMAIN=57
    BTENC=58
    BTAP=59

class Config:
    """ MQTT topics events mapping to esp32 in/out """
    topic_prefix="j/npanel"   
    topic_keys=topic_prefix+"/e/k"
    topic_display=topic_prefix+"/c/d"

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server """
    
    logger.info("Connected to MQTT server (result code "+str(rc)+")")
    client.subscribe(Config.topic_prefix+"/#")

def on_message(client, userdata, msg):
    
    """ The callback for when a PUBLISH message is received from the server """
    
    logger.debug("Message received "+msg.topic+" "+str(msg.payload))
    event.set(msg.topic, msg.payload)

    return
        
class Panel(object):
    """Parent object for all panels"""
    
    def __init__(self, client, action):
        self.client=client
        self.event=event
        # logger.debug("Panel class initialized")
        
    def mqttpublish(self, topic, payload):
        global alivetime

        self.client.publish(topic,payload)
        alivetime=time.time()   # the keepalive ticker


class Home(Panel):  
    """home panel class"""
    
    def __init__(self, client, event):
        logger.debug("Home class initialized")
        Panel.__init__(self,client, event)
        self.draw()
               
    def draw(self):
        global hasAP
        self.mqttpublish(Config.topic_display, "N,MAIN MENU")
        self.mqttpublish(Config.topic_display, "B,02,COM")
        self.mqttpublish(Config.topic_display, "B,04,NAV")
        self.mqttpublish(Config.topic_display, "B,06,AUDIO")
        
        if (hasAP):
            self.mqttpublish(Config.topic_display, "B,32,AP")
        self.mqttpublish(Config.topic_display, "B,34,TRIM")
        self.mqttpublish(Config.topic_display, "B,36,PERF")
        
        
    def run(self):
        global actMode, APStatus 
        
        if (not(self.event.isEmpty())):
            
            if (self.event.getTopic()=="j/npanel/e/s" and self.event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")
                
            if self.event.getTopic()==Config.topic_keys:
                if self.event.getPayload()==str(Const.LSK2):
                    actMode="RtuCom"
                if self.event.getPayload()==str(Const.LSK4):
                    actMode="RtuNav"
                if self.event.getPayload()==str(Const.LSK6):
                    actMode="Audio"
                if self.event.getPayload()==str(Const.RSK2):
                    actMode="AP"
                if self.event.getPayload()==str(Const.RSK4): # LSK6
                    actMode="Trim"
                if self.event.getPayload()==str(Const.RSK6): # RSK4
                    actMode="Perfs"
                if self.event.getPayload()==str(Const.BTAP): # AP
                    APStatus=APStatus^1
            self.event.clear()

class RtuCom(Panel):
    
    def __init__(self, client, event):
        logger.debug("RtuCom class initialized")
        Panel.__init__(self,client, event)
        #               COM1ACT       COM1STB       COM2ACT       COM2STB       ADFMSB        ADFLSB        XPDR
        self.__OFFSETS=[(0x034E,'H'), (0x311A,'H'), (0x3118,'H'), (0x311C,'H'), (0x034C,'H'), (0x0356,'H'), (0x0354,'H')]
        self.__editCur="COM1"
        self.__oldEditCur=""
        
    def draw(self):
        self.__oldActFreq1=0
        self.__oldStbFreq1=0
        self.__oldActFreq2=0
        self.__oldStbFreq2=0
        self.__oldAdfFreq=0
        self.__oldXpdrCode=0
        
        self.mqttpublish(Config.topic_display, "N,RTU COM")
        self.mqttpublish(Config.topic_display, "T,02,97,0,3,COM1")
        self.mqttpublish(Config.topic_display, "T,32,97,0,3,COM2")
        self.mqttpublish(Config.topic_display, "T,06,97,0,3,ADF")
        self.mqttpublish(Config.topic_display, "T,36,97,0,3,XPDR")
        
    def run(self):
        global actMode, APStatus
        
        if (self.__editCur!=self.__oldEditCur):
            self.draw();
            self.__oldEditCur=self.__editCur;
        
        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        actFreq1=fsconvert.vhf_bcd2float(results[0])
        stbFreq1=fsconvert.vhf_bcd2float(results[1])
        actFreq2=fsconvert.vhf_bcd2float(results[2])
        stbFreq2=fsconvert.vhf_bcd2float(results[3])
        adfFreq=fsconvert.adf_bcd2float(results[4],results[5])
        xpdrCode=int(str(fsconvert.xpdr_bcd2int(results[6])),8)
        
        # COM1 Active at LSK3
        if actFreq1!=self.__oldActFreq1:
            self.mqttpublish(Config.topic_display, "T,03,99,0,3,"+str('{0:.3f}'.format(actFreq1)))
            self.__oldActFreq1=actFreq1
        
        # COM1 Stand by at LSK4
        if stbFreq1!=self.__oldStbFreq1:
            if (self.__editCur=="COM1"):
                self.mqttpublish(Config.topic_display, "T,04,98,0,3,"+str('{0:.3f}'.format(stbFreq1)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2,Com1StbFq/Psh SW>")
            else:
                self.mqttpublish(Config.topic_display, "T,04,99,1,3,"+str('{0:.3f}'.format(stbFreq1)))
            self.__oldStbFreq1=stbFreq1
        
        # COM2 Active at RSK3
        if actFreq2!=self.__oldActFreq2:
            self.mqttpublish(Config.topic_display, "T,33,99,0,3,"+str('{0:.3f}'.format(actFreq2)))
            self.__oldActFreq2=actFreq2
            
        # COM2 Stand by at RSK4
        if stbFreq2!=self.__oldStbFreq2:
            if (self.__editCur=="COM2"):
                self.mqttpublish(Config.topic_display, "T,34,98,0,3,"+str('{0:.3f}'.format(stbFreq2)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2,Com2StbFq/Psh SW>")
            else:
                self.mqttpublish(Config.topic_display, "T,34,99,1,3,"+str('{0:.3f}'.format(stbFreq2)))
            self.__oldStbFreq2=stbFreq2
        
        # ADF at LSK7
        if adfFreq!=self.__oldAdfFreq:
            if (self.__editCur=="ADF"):
                self.mqttpublish(Config.topic_display, "T,07,98,0,3,"+str('{0:0>6.1f}'.format(adfFreq)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2,           ADFFq>")
            else:
                self.mqttpublish(Config.topic_display, "T,07,99,1,3,"+str('{0:0>6.1f}'.format(adfFreq)))
            self.__oldAdfFreq=adfFreq
        
        # XPDR at RSK7
        if xpdrCode!=self.__oldXpdrCode:
            if (self.__editCur=="XPDR"):
                self.mqttpublish(Config.topic_display, "T,37,98,0,3,"+str('{0:0>4.0f}'.format(int(oct(xpdrCode)))))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2,       XPDR code>")
            else:
                self.mqttpublish(Config.topic_display, "T,37,99,1,3,"+str('{0:0>4.0f}'.format(int(oct(xpdrCode)))))
            self.__oldXpdrCode=xpdrCode
        
        if (not(self.event.isEmpty())):
            
            if (self.event.getTopic()=="j/npanel/e/s" and self.event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")
                
            if self.event.getTopic()==Config.topic_keys:
                
                if self.event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1-0.025))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2-0.025))])
                    if (self.__editCur=="ADF"): 
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.adf_float2bcd(adfFreq-0.5)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],fsconvert.adf_float2bcd(adfFreq-0.5)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],fsconvert.xpdr_int2bcd(int(oct(xpdrCode-1))))])
                        
                if self.event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1+0.025))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2+0.025))])
                    if (self.__editCur=="ADF"):    
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.adf_float2bcd(adfFreq+0.5)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],fsconvert.adf_float2bcd(adfFreq+0.5)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],fsconvert.xpdr_int2bcd(int(oct(xpdrCode+1))))])
                        
                if self.event.getPayload()==str(Const.BTENC): # SW
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(actFreq1))])
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],fsconvert.vhf_float2bcd(stbFreq1))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(actFreq2))])
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],fsconvert.vhf_float2bcd(stbFreq2))])
                    
                if self.event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1-1))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2-1))])
                    if (self.__editCur=="ADF"):    
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.adf_float2bcd(adfFreq-10)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],fsconvert.adf_float2bcd(adfFreq-10)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],fsconvert.xpdr_int2bcd(int(oct(xpdrCode-64))))])
                        
                if self.event.getPayload()==str(Const.ENC2UP): # INC2 UP
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1+1))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2+1))])
                    if (self.__editCur=="ADF"):    
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.adf_float2bcd(adfFreq+10)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],fsconvert.adf_float2bcd(adfFreq+10)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],fsconvert.xpdr_int2bcd(int(oct(xpdrCode+64))))])
                
                if self.event.getPayload()==str(Const.RSK4): #COM2
                    self.__editCur="COM2"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.LSK4): #COM1
                    self.__editCur="COM1"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.LSK7): #ADF
                    self.__editCur="ADF"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.RSK7): #XPDR
                    self.__editCur="XPDR"
                    self.draw()
                
                if self.event.getPayload()==str(Const.BTMAIN): #return to home
                    actMode="Home"
                if self.event.getPayload()==str(Const.BTAP): # AP
                    APStatus=APStatus^1
            self.event.clear()

class RtuNav(Panel):
    
    def __init__(self, client, event):
        logger.debug("RtuCom class initialized")
        Panel.__init__(self,client, event)
        #               NAV1ACT       NAV1STB       NAV2ACT       NAV2STB       NAV1OBS        NAV2HDG
        self.__OFFSETS=[(0x0350,'H'), (0x311E,'H'), (0x0352,'H'), (0x3120,'H'), (0x0C4E,'H'), (0x0C5E,'H')]
        self.__editCur="NAV1"
        self.__oldEditCur=""
        
    def draw(self):
        self.__oldActFreq1=0
        self.__oldStbFreq1=0
        self.__oldActFreq2=0
        self.__oldStbFreq2=0
        self.__oldHdgNav1=0
        self.__oldHdgNav2=0
        
        self.mqttpublish(Config.topic_display, "N,RTU NAV")
        self.mqttpublish(Config.topic_display, "T,02,97,0,3,NAV1")
        self.mqttpublish(Config.topic_display, "T,32,97,0,3,NAV2")
        self.mqttpublish(Config.topic_display, "T,06,97,0,3,OBS1")
        self.mqttpublish(Config.topic_display, "T,36,97,0,3,OBS2")
        
    def run(self):
        global actMode, APStatus
        
        if (self.__editCur!=self.__oldEditCur):
            self.draw();
            self.__oldEditCur=self.__editCur;
        
        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        actFreq1=fsconvert.vhf_bcd2float(results[0])
        stbFreq1=fsconvert.vhf_bcd2float(results[1])
        actFreq2=fsconvert.vhf_bcd2float(results[2])
        stbFreq2=fsconvert.vhf_bcd2float(results[3])
        HdgNav1=results[4]
        HdgNav2=results[5]
        
        # NAV1 Active at LSK3
        if actFreq1!=self.__oldActFreq1:
            self.mqttpublish(Config.topic_display, "T,03,99,0,3,"+str('{0:.3f}'.format(actFreq1)))
            self.__oldActFreq1=actFreq1
        
        # NAV1 Stand by  at LSK4
        if stbFreq1!=self.__oldStbFreq1:
            if (self.__editCur=="NAV1"):
                self.mqttpublish(Config.topic_display, "T,04,98,0,3,"+str('{0:.3f}'.format(stbFreq1)))
            else:
                self.mqttpublish(Config.topic_display, "T,04,99,1,3,"+str('{0:.3f}'.format(stbFreq1)))
            self.__oldStbFreq1=stbFreq1
        
        # NAV2 Active at RSK3
        if actFreq2!=self.__oldActFreq2:
            self.mqttpublish(Config.topic_display, "T,33,99,0,3,"+str('{0:.3f}'.format(actFreq2)))
            self.__oldActFreq2=actFreq2
            
        # NAV2 Stand by at RSK4
        if stbFreq2!=self.__oldStbFreq2:
            if (self.__editCur=="NAV2"):
                self.mqttpublish(Config.topic_display, "T,34,98,0,3,"+str('{0:.3f}'.format(stbFreq2)))
            else:
                self.mqttpublish(Config.topic_display, "T,34,99,1,3,"+str('{0:.3f}'.format(stbFreq2)))
            self.__oldStbFreq2=stbFreq2
        
        # NAV1 HDG at LSK7
        if HdgNav1!=self.__oldHdgNav1:
            if (self.__editCur=="HDG1"):
                self.mqttpublish(Config.topic_display, "T,07,98,0,3,"+str('{0:0>3.0f}'.format(HdgNav1)))
            else:
                self.mqttpublish(Config.topic_display, "T,07,99,1,3,"+str('{0:0>3.0f}'.format(HdgNav1)))
            self.__oldHdgNav1=HdgNav1
        
        # NAV2 HDG at RSK17
        if HdgNav2!=self.__oldHdgNav2:
            if (self.__editCur=="HDG2"):
                self.mqttpublish(Config.topic_display, "T,37,98,0,3,"+str('{0:0>3.0f}'.format(HdgNav2)))
            else:
                self.mqttpublish(Config.topic_display, "T,37,99,1,3,"+str('{0:0>3.0f}'.format(HdgNav2)))
            self.__oldHdgNav2=HdgNav2
        
        if (not(self.event.isEmpty())):
            
            if (self.event.getTopic()=="j/npanel/e/s" and self.event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")

            if self.event.getTopic()==Config.topic_keys:
                
                if self.event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1-0.025))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2-0.025))])
                    if (self.__editCur=="HDG1"): 
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1-1))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1-1))])
                        
                if self.event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1+0.025))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2+0.025))])
                    if (self.__editCur=="HDG1"): 
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1+1))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1+1))])
                            
                if self.event.getPayload()==str(Const.BTENC): # SW
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(actFreq1))])
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],fsconvert.vhf_float2bcd(stbFreq1))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(actFreq2))])
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],fsconvert.vhf_float2bcd(stbFreq2))])
                    
                if self.event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1-1))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2-1))])
                    if (self.__editCur=="HDG1"): 
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1-10))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1-10))])
                            
                if self.event.getPayload()==str(Const.ENC2UP): # INC2 UP
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.vhf_float2bcd(stbFreq1+1))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.vhf_float2bcd(stbFreq2+1))])
                    if (self.__editCur=="HDG1"): 
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1+10))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],fsconvert.bearing(HdgNav1+10))])
                        
                if self.event.getPayload()==str(Const.RSK4): #NAV2
                    self.__editCur="NAV2"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.LSK1): #NAV1
                    self.__editCur="NAV1"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.LSK7): #HDG1
                    self.__editCur="HDG1"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.RSK7): #HDG2
                    self.__editCur="HDG2"
                    self.draw()
                
                if self.event.getPayload()==str(Const.BTMAIN): #return to home
                    actMode="Home"
                if self.event.getPayload()==str(Const.BTAP): # AP
                    APStatus=APStatus^1
            self.event.clear()


class Audio(Panel):
    
    def __init__(self, client, event):
        logger.debug("Audio class initialized")
        Panel.__init__(self,client, event)
        #               AUDIO
        self.__OFFSETS=[(0x3122,'b')]
        self.draw()
        
    def draw(self):
        self.__oldCom1=-1
        self.__oldCom2=-1
        self.__oldBoth=-1
        self.__oldNav1=-1
        self.__oldNav2=-1
        self.__oldMarker=-1
        self.__oldDme=-1
        self.__oldAdf1=-1
        
        self.mqttpublish(Config.topic_display, "N,AUDIO")
        
    def run(self):
        global actMode, APStatus
        
        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        com1=results[0]&128
        com2=results[0]&64
        both=results[0]&32
        nav1=results[0]&16
        nav2=results[0]&8
        marker=results[0]&4
        dme=results[0]&2
        adf1=results[0]&1
        
        # com1 select
        if com1!=self.__oldCom1:
            if (com1==0):
                self.mqttpublish(Config.topic_display, "T,02,97,1,4,CM1")
            else:
                self.mqttpublish(Config.topic_display, "T,02,97,1,5,CM1")
            self.__oldCom1=com1
            
        # com2 select
        if com2!=self.__oldCom2:
            if (com2==0):
                self.mqttpublish(Config.topic_display, "T,12,97,1,4,CM2")
            else:
                self.mqttpublish(Config.topic_display, "T,12,97,1,5,CM2")
            self.__oldCom2=com2
            
        # receive both com1 and com1
        if both!=self.__oldBoth:
            if (both==0):
                self.mqttpublish(Config.topic_display, "T,22,97,1,4,BTH")
            else:
                self.mqttpublish(Config.topic_display, "T,22,97,1,5,BTH")
            self.__oldBoth=both
            
        # nav1
        if nav1!=self.__oldNav1:
            if (nav1==0):
                self.mqttpublish(Config.topic_display, "T,04,97,1,4,NV1")
            else:
                self.mqttpublish(Config.topic_display, "T,04,97,1,5,NV1")
            self.__oldNav1=nav1
            
        # nav1
        if nav2!=self.__oldNav2:
            if (nav2==0):
                self.mqttpublish(Config.topic_display, "T,14,97,1,4,NV2")
            else:
                self.mqttpublish(Config.topic_display, "T,14,97,1,5,NV2")
            self.__oldNav2=nav2
            
        # marker
        if marker!=self.__oldMarker:
            if (marker==0):
                self.mqttpublish(Config.topic_display, "T,24,97,1,4,MKR")
            else:
                self.mqttpublish(Config.topic_display, "T,24,97,1,5,MKR")
            self.__oldMarker=marker
            
        # dme
        if dme!=self.__oldDme:
            if (dme==0):
                self.mqttpublish(Config.topic_display, "T,34,97,1,4,DME")
            else:
                self.mqttpublish(Config.topic_display, "T,34,97,1,5,DME")
            self.__oldDme=dme
            
        # adf1
        if adf1!=self.__oldAdf1:
            if (adf1==0):
                self.mqttpublish(Config.topic_display, "T,06,97,1,4,ADF")
            else:
                self.mqttpublish(Config.topic_display, "T,06,97,1,5,ADF")
            self.__oldAdf1=adf1
            
        if (not(self.event.isEmpty())):
            
            if (self.event.getTopic()=="j/npanel/e/s" and self.event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")

            if self.event.getTopic()==Config.topic_keys:
                if self.event.getPayload()==str(Const.LSK2): # com1
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^192)])
                
                if self.event.getPayload()==str(Const.LCK2): # com2
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^192)])
                
                if self.event.getPayload()==str(Const.RCK2): # both
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^32)])
                
                if self.event.getPayload()==str(Const.LSK4): # nav1
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^16)])
                
                if self.event.getPayload()==str(Const.LCK4): # nav2
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^8)])
                    
                if self.event.getPayload()==str(Const.RCK4): # marker
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^4)])
                    
                if self.event.getPayload()==str(Const.RSK4): # dme
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^2)])
                    
                if self.event.getPayload()==str(Const.LSK6): # adf
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^1)])
                
                if self.event.getPayload()==str(Const.BTMAIN): #return to home
                    actMode="Home"
                if self.event.getPayload()==str(Const.BTAP): # AP
                    APStatus=APStatus^1
            self.event.clear()
    
class AP(Panel):
    
    def __init__(self, client, event):
        logger.debug("AP class initialized")
        Panel.__init__(self,client, event)
        #               ALTITUDE       HEADING       VERTSPEED   COURSE(NAV1OBS) IAS          LockALT       LockIAS       LockHDG       LockAT        LockNAV       LockBC         LockAPP       LockATT       LockYD
        self.__OFFSETS=[(0x07D4,'d'), (0x07CC,'H'), (0x07F2,'h'), (0x0C4E,'H'), (0x07E2,'h'), (0x07D0,'u'), (0x07DC,'u'), (0x07C8,'u'), (0x0810,'u'), (0x07C4,'u'), (0x00804,'u'), (0x0800,'u'), (0x07D8,'u'), (0x0808,'u')]
        self.__editCur="ALT"
        self.__oldEditCur=""
        
    def draw(self):
        self.__oldAltitude=-1
        self.__oldHeading=-1
        self.__oldVertSpeed=-1
        self.__oldCourse=-1
        self.__oldIAS=-1
        self.__oldLockALT=-1
        self.__oldLockIAS=-1
        self.__oldLockHDG=-1
        self.__oldLockAT=-1
        self.__oldLockNAV=-1
        self.__oldLockBC=-1
        self.__oldLockAPP=-1
        self.__oldLockATT=-1
        self.__oldLockYD=-1
        
        self.mqttpublish(Config.topic_display, "N,AUTOPILOT")
        self.mqttpublish(Config.topic_display, "T,02,97,0,2,ALT")
        self.mqttpublish(Config.topic_display, "T,12,97,0,2,IAS")
        self.mqttpublish(Config.topic_display, "T,22,97,0,2,HDG")
        self.mqttpublish(Config.topic_display, "T,32,97,0,2,CRS")
        self.mqttpublish(Config.topic_display, "T,05,97,0,2,VSPD")
        
    def run(self):
        global actMode, APStatus
        
        if (self.__editCur!=self.__oldEditCur):
            self.draw();
            self.__oldEditCur=self.__editCur;
        
        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        altitude=results[0]/19975 # in feet
        heading=results[1]/182    # in deg
        vertSpeed=results[2]      # in feet/min
        Course=results[3]         # in deg
        IAS=results[4]            # in kts
        lockALT=results[5]
        lockIAS=results[6]
        lockHDG=results[7]
        lockAT=results[8]
        lockNAV=results[9]
        lockBC=results[10]
        lockAPP=results[11]
        lockATT=results[12]
        lockYD=results[13]
        
        # ALT at LSK3
        if altitude!=self.__oldAltitude:
            if (self.__editCur=="ALT"):
                self.mqttpublish(Config.topic_display, "T,03,98,0,2,"+str('{0:0>5.0f}'.format(altitude//100*100)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2, Set ALT>")
            else:
                self.mqttpublish(Config.topic_display, "T,03,99,1,2,"+str('{0:0>5.0f}'.format(altitude//100*100)))
            self.__oldAltitude=altitude
        
        # IAS at LCK3
        if IAS!=self.__oldIAS:
            if (self.__editCur=="IAS"):
                self.mqttpublish(Config.topic_display, "T,13,98,0,3,"+str('{0:0>3.0f}'.format(IAS)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2, Set IAS>")
            else:
                self.mqttpublish(Config.topic_display, "T,13,99,1,3,"+str('{0:0>3.0f}'.format(IAS)))
            self.__oldIAS=IAS
        
        # HDG at RSK3
        if heading!=self.__oldHeading:
            if (self.__editCur=="HDG"):
                self.mqttpublish(Config.topic_display, "T,23,98,0,3,"+str('{0:0>3.0f}'.format(heading)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2, Set HDG>")
            else:
                self.mqttpublish(Config.topic_display, "T,23,99,1,3,"+str('{0:0>3.0f}'.format(heading)))
            self.__oldHeading=heading
        
        # VERTICAL SPEED at LSK6
        if vertSpeed!=self.__oldVertSpeed:
            if (self.__editCur=="VERTSPEED"):
                self.mqttpublish(Config.topic_display, "T,06,98,0,2,"+str('{0:05.0f}'.format(vertSpeed)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2,Set Vspd>")
            else:
                self.mqttpublish(Config.topic_display, "T,06,99,1,2,"+str('{0:05.0f}'.format(vertSpeed)))
            self.__oldVertSpeed=vertSpeed
        
        # Course at RSK6
        if Course!=self.__oldCourse:
            if (self.__editCur=="COURSE"):
                self.mqttpublish(Config.topic_display, "T,33,98,0,3,"+str('{0:0>3.0f}'.format(Course)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,2, Set CRS>")
            else:
                self.mqttpublish(Config.topic_display, "T,33,99,1,3,"+str('{0:0>3.0f}'.format(Course)))
            self.__oldCourse=Course
        
        # LockALT
        if lockALT!=self.__oldLockALT:
            if (lockALT==0):
                self.mqttpublish(Config.topic_display, "T,04,97,1,4,ALT")
            else:
                self.mqttpublish(Config.topic_display, "T,04,97,1,5,ALT")
            self.__oldLockALT=lockALT
            
        # LockIAS
        if lockIAS!=self.__oldLockIAS:
            if (lockIAS==0):
                self.mqttpublish(Config.topic_display, "T,14,97,1,4,IAS")
            else:
                self.mqttpublish(Config.topic_display, "T,14,97,1,5,IAS")
            self.__oldLockIAS=lockIAS
        
        # LockAT
        if lockAT!=self.__oldLockAT:
            if (lockAT==0):
                self.mqttpublish(Config.topic_display, "T,15,97,1,4,A/T")
            else:
                self.mqttpublish(Config.topic_display, "T,15,97,1,5,A/T")
            self.__oldLockAT=lockAT
            
        # LockHDG
        if lockHDG!=self.__oldLockHDG:
            if (lockHDG==0):
                self.mqttpublish(Config.topic_display, "T,24,97,1,4,HDG")
            else:
                self.mqttpublish(Config.topic_display, "T,24,97,1,5,HDG")
            self.__oldLockHDG=lockHDG
        
        # LockNAV
        if lockNAV!=self.__oldLockNAV:
            if (lockNAV==0):
                self.mqttpublish(Config.topic_display, "T,34,97,1,4,NAV")
            else:
                self.mqttpublish(Config.topic_display, "T,34,97,1,5,NAV")
            self.__oldLockNAV=lockNAV
        
        # LockBC
        if lockBC!=self.__oldLockBC:
            if (lockBC==0):
                self.mqttpublish(Config.topic_display, "T,35,97,1,4,BC")
            else:
                self.mqttpublish(Config.topic_display, "T,35,97,1,5,BC")
            self.__oldLockBC=lockBC
            
        # LockAPP
        if lockAPP!=self.__oldLockAPP:
            if (lockAPP==0):
                self.mqttpublish(Config.topic_display, "T,36,97,1,4,APP")
            else:
                self.mqttpublish(Config.topic_display, "T,36,97,1,5,APP")
            self.__oldLockAPP=lockAPP
            
        # LockATT
        if lockATT!=self.__oldLockATT:
            if (lockATT==0):
                self.mqttpublish(Config.topic_display, "T,17,97,1,4,ATT")
            else:
                self.mqttpublish(Config.topic_display, "T,17,97,1,5,ATT")
            self.__oldLockATT=lockATT
            
        # LockYD
        if lockYD!=self.__oldLockYD:
            if (lockYD==0):
                self.mqttpublish(Config.topic_display, "T,27,97,1,4,Y/D")
            else:
                self.mqttpublish(Config.topic_display, "T,27,97,1,5,Y/D")
            self.__oldLockYD=lockYD
        
        if (not(self.event.isEmpty())):
            
            if (self.event.getTopic()=="j/npanel/e/s" and self.event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")

            if self.event.getTopic()==Config.topic_keys:
                
                if self.event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude-99)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.bearing(heading-1)*182)])
                    if (self.__editCur=="VERTSPEED"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed-100)])
                    if (self.__editCur=="COURSE"): 
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.bearing(Course-1))])
                        
                if self.event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude+101)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.bearing(heading+1)*182)])
                    if (self.__editCur=="VERTSPEED"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed+100)])
                    if (self.__editCur=="COURSE"): 
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.bearing(Course+1))])
                            
                if self.event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude-999)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.bearing(heading-10)*182)])
                    if (self.__editCur=="VERTSPEED"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed-100)])
                    if (self.__editCur=="COURSE"): 
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.bearing(Course-10))])
                            
                if self.event.getPayload()=="str(Const.ENC2UP)": # INC2 UP
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude+1001)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],fsconvert.bearing(heading+10)*182)])
                    if (self.__editCur=="VERTSPEED"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed+100)])
                    if (self.__editCur=="COURSE"): 
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],fsconvert.bearing(Course+10))])
                        
                if self.event.getPayload()==str(Const.LSK3): #ALT
                    self.__editCur="ALT"
                    self.draw()
                
                if self.event.getPayload()==str(Const.LSK4): # LockAlt
                    lockALT=lockALT^1
                    pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],lockALT)])
                        
                if self.event.getPayload()==str(Const.LCK3): #IAS
                    self.__editCur="IAS"
                    self.draw()
                
                if self.event.getPayload()==str(Const.LCK4): # LockIAS
                    lockIAS=lockIAS^1
                    pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],lockIAS)])
                
                if self.event.getPayload()==str(Const.LCK5): # LockAT
                    lockAT=lockAT^1
                    pyuipc.write([(self.__OFFSETS[8][0],self.__OFFSETS[8][1],lockAT)])
                    
                if self.event.getPayload()==str(Const.RCK3): #HDG
                    self.__editCur="HDG"
                    self.draw()
                
                if self.event.getPayload()==str(Const.RCK4): # LockHDG
                    lockHDG=lockHDG^1
                    pyuipc.write([(self.__OFFSETS[7][0],self.__OFFSETS[7][1],lockHDG)])
                    
                if self.event.getPayload()==str(Const.LSK6): #VERTSPEED
                    self.__editCur="VERTSPEED"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.RSK3): #COURSE
                    self.__editCur="COURSE"
                    self.draw()
                
                if self.event.getPayload()==str(Const.RSK4): # LockNAV
                    lockNAV=lockNAV^1
                    pyuipc.write([(self.__OFFSETS[9][0],self.__OFFSETS[9][1],lockNAV)])
                    
                if self.event.getPayload()==str(Const.RSK5): # LockBC
                    lockBC=lockBC^1
                    pyuipc.write([(self.__OFFSETS[10][0],self.__OFFSETS[10][1],lockBC)])
                    
                if self.event.getPayload()==str(Const.RSK6): # LockAPP
                    lockAPP=lockAPP^1
                    pyuipc.write([(self.__OFFSETS[11][0],self.__OFFSETS[11][1],lockAPP)])
                    #pyuipc.write([(0x800,'u',lockAPP)]) #Specific to APP offset, must write at two offsets
                    
                if self.event.getPayload()==str(Const.LCK7): # LockATT
                    lockATT=lockATT^1
                    pyuipc.write([(self.__OFFSETS[12][0],self.__OFFSETS[12][1],lockATT)])
                
                if self.event.getPayload()==str(Const.RCK7): # LockYD
                    lockYD=lockYD^1
                    pyuipc.write([(self.__OFFSETS[13][0],self.__OFFSETS[13][1],lockYD)])
                    
                if self.event.getPayload()==str(Const.BTMAIN): #return to home
                    actMode="Home"
                
                if self.event.getPayload()==str(Const.BTAP): # AP
                    APStatus=APStatus^1
            self.event.clear()

class Perfs(Panel):
    
    def __init__(self, client, event):
        logger.debug("Perfs class initialized")
        Panel.__init__(self,client, event)
        #               WEIGHT        OAT
        self.__OFFSETS=[(0x30C8,'f'), (0x0E8C,'H'), (0x2EF8,'f')]
        self.draw()
        
    def draw(self):
        self.__oldWeight=-1
        self.__oldOAT=-1
        self.__oldCG=-1
        
        self.mqttpublish(Config.topic_display, "N,PERFS")
        self.mqttpublish(Config.topic_display, "T,02,97,0,2,WEIGHT")
        self.mqttpublish(Config.topic_display, "T,32,97,0,2,OAT")
        self.mqttpublish(Config.topic_display, "T,04,97,0,2,CG")
        
    def run(self):
        global actMode, APStatus
        
        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        weight=results[0]*32 # in lbs
        OAT=results[1]/256    # in degC
        CG=results[2] #in percents
        
        # WEIGHT at LSK3
        if weight!=self.__oldWeight:
            self.mqttpublish(Config.topic_display, "T,03,99,0,2,"+str(round(weight)))
            self.__oldWeight=weight
            
        # OAT at RSK3
        if OAT!=self.__oldOAT:
            self.mqttpublish(Config.topic_display, "T,33,99,0,2,"+str(round(OAT)))
            self.__oldOAT=OAT
            
        # CG at LSK6
        if CG!=self.__oldCG:
            self.mqttpublish(Config.topic_display, "T,05,99,0,2,"+str('{0:.2f}'.format(CG)))
            self.__oldCG=CG
        
        if (not(self.event.isEmpty())):
            
            if (self.event.getTopic()=="j/npanel/e/s" and self.event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")
                    
            if self.event.getPayload()==str(Const.BTMAIN): #return to home
                actMode="Home"
            if self.event.getPayload()==str(Const.BTAP): # AP
                    APStatus=APStatus^1
            self.event.clear()
            
class Trim(Panel):
    
    def __init__(self, client, event):
        logger.debug("Perfs class initialized")
        Panel.__init__(self,client, event)
        self.__editCur="ELEV"
        self.__oldEditCur=""
        #               ELEVATOR      AILERON       RUDDER
        self.__OFFSETS=[(0x0BC0,'h'), (0x0C02,'h'), (0x0C04,'h')]
        
    def draw(self):
        self.__oldETrim=-1
        self.__oldATrim=-1
        self.__oldRTrim=-1
        
        self.mqttpublish(Config.topic_display, "N,TRIMS")
        self.mqttpublish(Config.topic_display, "T,03,97,0,2,ELEVATOR")
        self.mqttpublish(Config.topic_display, "T,05,97,0,2,AILERON")
        self.mqttpublish(Config.topic_display, "T,07,97,0,2,RUDDER")
        
    def run(self):
        global actMode, APStatus
        
        if (self.__editCur!=self.__oldEditCur):
            self.draw();
            self.__oldEditCur=self.__editCur;
        
        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        eTrim=results[0]
        aTrim=results[1]
        rTrim=results[2]
        
        # ELEVATOR at RSK3
        if eTrim!=self.__oldETrim:
            if (self.__editCur=="ELEV"):
                self.mqttpublish(Config.topic_display, "S,33,98,0,"+str(round(eTrim/280)))
            else:
                self.mqttpublish(Config.topic_display, "S,33,99,1,"+str(round(eTrim/280)))
            self.__oldETrim=eTrim
            
        # AILERON at RSK5
        if aTrim!=self.__oldATrim:
            if (self.__editCur=="AIL"):
                self.mqttpublish(Config.topic_display, "S,35,98,0,"+str(round(aTrim/280)))
            else:
                self.mqttpublish(Config.topic_display, "S,35,99,1,"+str(round(aTrim/280)))
            self.__oldATrim=aTrim
        
        # RUDDER at RSK7
        if rTrim!=self.__oldRTrim:
            if (self.__editCur=="RUD"):
                self.mqttpublish(Config.topic_display, "S,37,98,0,"+str(round(rTrim/280)))
            else:
                self.mqttpublish(Config.topic_display, "S,37,99,1,"+str(round(rTrim/280)))
            self.__oldRTrim=rTrim
        
        if (not(self.event.isEmpty())):
            
            if (self.event.getTopic()=="j/npanel/e/s" and self.event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")

            if self.event.getTopic()==Config.topic_keys:
                
                if self.event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim-100)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim-100)])
                    if (self.__editCur=="RUD"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim-100)])
                        
                if self.event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim+100)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim+100)])
                    if (self.__editCur=="RUD"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim+100)])
                            
                if self.event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim-1000)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim-1000)])
                    if (self.__editCur=="RUD"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim-1000)])
                            
                if self.event.getPayload()==str(Const.ENC2UP): # INC2 UP
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim+1000)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim+1000)])
                    if (self.__editCur=="RUD"): 
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim+1000)])
                        
                if self.event.getPayload()==str(Const.RSK3): #ELEV
                    self.__editCur="ELEV"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.RSK5): #AIL
                    self.__editCur="AIL"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.RSK7): #RUDDER
                    self.__editCur="RUD"
                    self.draw()
                    
                if self.event.getPayload()==str(Const.BTMAIN): #return to home
                    actMode="Home"
                if self.event.getPayload()==str(Const.BTAP): # AP
                    APStatus=APStatus^1
            self.event.clear()


def setup():
    global pyuipcOffsets, oldActMode, alivetime, client, event, oldAPStatus, OFFSETS
    
    # Connect to flight simulator via FSUIPC (pyuipc)
    try:
        pyuipcConnection = pyuipc.open(0)
    except pyuipc.FSUIPCException:
        logger.critical("Unable to connect FSUIPC: check Flight Sim is running first. Exit")
        sys.exit(1);
    logger.info("Connected to FSUIPC")

    # MQTT borcker connection on localhost
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    logger.debug("Trying to connect to MQTT server "+config.get('MQTT','server')+" on port "+config.get('MQTT','port'))
    client.connect(config.get('MQTT','server'), config.getint('MQTT','port'), 60)
    client.loop_start()
    logger.info("Connectes to MQTT server "+config.get('MQTT','server'))
    
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
        logger.info("Changing mode to "+actMode)
        
        if actMode=="Home":
            panel=Home(client,event)
        if actMode=="RtuCom":
            panel=RtuCom(client,event)
        if actMode=="RtuNav":
            panel=RtuNav(client,event)
        if actMode=="Audio":
            panel=Audio(client,event)
        if actMode=="AP":
            panel=AP(client,event)
        if actMode=="Perfs":
            panel=Perfs(client,event)
        if actMode=="Trim":
            panel=Trim(client,event)
        oldActMode=actMode
        
    # loop that updates panel
    panel.run()
        
    # de/activate autopilot
    if (APStatus!=oldAPStatus):
        if (APStatus==0):
            client.publish(Config.topic_display, "L,0")
            # Beep when AP is disabled
            client.publish(Config.topic_display, "X")
        else:
            client.publish(Config.topic_display, "L,1")
        pyuipc.write([(OFFSETS[0][0],OFFSETS[0][1],APStatus)])
        oldAPStatus=APStatus
        
    # keepalive to esp32 module every 2 seconds, just say "i'm here"
    
    if ((time.time() - alivetime) > 2):
        logger.debug("Send keep alive to esp32 module")
        client.publish(Config.topic_prefix+"/c/reqstatus", "1")
        alivetime=time.time()
    

if __name__ == "__main__":
    
    setup()
        
    while True:
        loop()