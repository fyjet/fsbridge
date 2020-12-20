from modules.Panel import Panel
from modules.Config import Config
import pyuipc
from modules.fsconvert import *
from modules.Const import Const
import logging

class Trim(Panel):

    def __init__(self, client):
        logging.debug("Perfs class initialized")
        Panel.__init__(self,client)
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

    def run(self, event):
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

        if (not(event.isEmpty())):

            if (event.getTopic()=="j/npanel/e/s" and event.getPayload()=="1"):
                self.draw();
                logging.debug("Redraw")

            if event.getTopic()==Config.topic_keys:

                if event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim-100)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim-100)])
                    if (self.__editCur=="RUD"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim-100)])
                    event.clear()

                if event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim+100)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim+100)])
                    if (self.__editCur=="RUD"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim+100)])
                    event.clear()

                if event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim-1000)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim-1000)])
                    if (self.__editCur=="RUD"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim-1000)])
                    event.clear()

                if event.getPayload()==str(Const.ENC2UP): # INC2 UP
                    if (self.__editCur=="ELEV"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],eTrim+1000)])
                    if (self.__editCur=="AIL"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],aTrim+1000)])
                    if (self.__editCur=="RUD"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],rTrim+1000)])
                    event.clear()

                if event.getPayload()==str(Const.RSK3): #ELEV
                    self.__editCur="ELEV"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.RSK5): #AIL
                    self.__editCur="AIL"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.RSK7): #RUDDER
                    self.__editCur="RUD"
                    self.draw()
                    event.clear()