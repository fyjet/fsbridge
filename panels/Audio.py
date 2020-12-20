from modules.Panel import Panel
from modules.Config import Config
import pyuipc
from modules.fsconvert import *
from modules.Const import Const
import logging

class Audio(Panel):

    def __init__(self, client):
        logging.debug("Audio class initialized")
        Panel.__init__(self,client)
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

    def run(self, event):
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

        if (not(event.isEmpty())):

            if (event.getTopic()=="j/npanel/e/s" and event.getPayload()=="1"):
                self.draw();
                logging.debug("Redraw")

            if event.getTopic()==Config.topic_keys:
                if event.getPayload()==str(Const.LSK2): # com1
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^192)])
                    event.clear()

                if event.getPayload()==str(Const.LCK2): # com2
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^192)])
                    event.clear()

                if event.getPayload()==str(Const.RCK2): # both
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^32)])
                    event.clear()

                if event.getPayload()==str(Const.LSK4): # nav1
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^16)])
                    event.clear()

                if event.getPayload()==str(Const.LCK4): # nav2
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^8)])
                    event.clear()

                if event.getPayload()==str(Const.RCK4): # marker
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^4)])
                    event.clear()

                if event.getPayload()==str(Const.RSK4): # dme
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^2)])
                    event.clear()

                if event.getPayload()==str(Const.LSK6): # adf
                    pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],results[0]^1)])
                    event.clear()
