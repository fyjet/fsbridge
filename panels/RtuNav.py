from modules.Panel import Panel
from modules.Config import Config
import pyuipc
from modules.fsconvert import *
from modules.Const import Const
import logging

class RtuNav(Panel):

    def __init__(self, client):
        logging.debug("RtuCom class initialized")
        Panel.__init__(self,client)
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

    def run(self, event):
        global actMode, APStatus

        if (self.__editCur!=self.__oldEditCur):
            self.draw();
            self.__oldEditCur=self.__editCur;

        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        actFreq1 = vhf_bcd2float(results[0])
        stbFreq1 = vhf_bcd2float(results[1])
        actFreq2 = vhf_bcd2float(results[2])
        stbFreq2 = vhf_bcd2float(results[3])
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
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,Nav1StbFq/Psh SW>")
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
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,Nav2StbFq/Psh SW>")
            else:
                self.mqttpublish(Config.topic_display, "T,34,99,1,3,"+str('{0:.3f}'.format(stbFreq2)))
            self.__oldStbFreq2=stbFreq2

        # NAV1 HDG at LSK7
        if HdgNav1!=self.__oldHdgNav1:
            if (self.__editCur=="HDG1"):
                self.mqttpublish(Config.topic_display, "T,07,98,0,3,"+str('{0:0>3.0f}'.format(HdgNav1)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,           OBS1Hdg>")
            else:
                self.mqttpublish(Config.topic_display, "T,07,99,1,3,"+str('{0:0>3.0f}'.format(HdgNav1)))
            self.__oldHdgNav1=HdgNav1

        # NAV2 HDG at RSK17
        if HdgNav2!=self.__oldHdgNav2:
            if (self.__editCur=="HDG2"):
                self.mqttpublish(Config.topic_display, "T,37,98,0,3,"+str('{0:0>3.0f}'.format(HdgNav2)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,           OBS2Hdb>")
            else:
                self.mqttpublish(Config.topic_display, "T,37,99,1,3,"+str('{0:0>3.0f}'.format(HdgNav2)))
            self.__oldHdgNav2=HdgNav2

        if (not(event.isEmpty())):

            if (event.getTopic()=="j/npanel/e/s" and event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")

            if event.getTopic()==Config.topic_keys:

                if event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1-0.025))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2-0.025))])
                    if (self.__editCur=="HDG1"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],bearing(HdgNav1-1))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],bearing(HdgNav1-1))])
                    event.clear()

                if event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1+0.025))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2+0.025))])
                    if (self.__editCur=="HDG1"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],bearing(HdgNav1+1))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],bearing(HdgNav1+1))])
                    event.clear()

                if event.getPayload()==str(Const.BTENC): # SW
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(actFreq1))])
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],vhf_float2bcd(stbFreq1))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(actFreq2))])
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vhf_float2bcd(stbFreq2))])
                    event.clear()

                if event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1-1))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2-1))])
                    if (self.__editCur=="HDG1"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],bearing(HdgNav1-10))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],bearing(HdgNav1-10))])
                    event.clear()

                if event.getPayload()==str(Const.ENC2UP): # INC2 UP
                    if (self.__editCur=="NAV1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1+1))])
                    if (self.__editCur=="NAV2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2+1))])
                    if (self.__editCur=="HDG1"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],bearing(HdgNav1+10))])
                    if (self.__editCur=="HDG2"):
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[4][1],bearing(HdgNav1+10))])
                    event.clear()

                if event.getPayload()==str(Const.RSK4): #NAV2
                    self.__editCur="NAV2"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.LSK1): #NAV1
                    self.__editCur="NAV1"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.LSK7): #HDG1
                    self.__editCur="HDG1"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.RSK7): #HDG2
                    self.__editCur="HDG2"
                    self.draw()
                    event.clear()