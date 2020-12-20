from modules.Panel import Panel
from modules.Config import Config
import pyuipc
from modules.fsconvert import *
from modules.Const import Const
import logging

class RtuCom(Panel):

    def __init__(self, client):
        Panel.__init__(self,client)
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

    def run(self, event):

        if (self.__editCur!=self.__oldEditCur):
            self.draw();
            self.__oldEditCur=self.__editCur;

        pyuipcOffsets = pyuipc.prepare_data(self.__OFFSETS)
        results = pyuipc.read(pyuipcOffsets)
        actFreq1 = vhf_bcd2float(results[0])
        stbFreq1 = vhf_bcd2float(results[1])
        actFreq2 = vhf_bcd2float(results[2])
        stbFreq2 = vhf_bcd2float(results[3])
        adfFreq = adf_bcd2float(results[4],results[5])
        xpdrCode = int(str(xpdr_bcd2int(results[6])),8)

        # COM1 Active at LSK3
        if actFreq1!=self.__oldActFreq1:
            self.mqttpublish(Config.topic_display, "T,03,99,0,3,"+str('{0:.3f}'.format(actFreq1)))
            self.__oldActFreq1=actFreq1

        # COM1 Stand by at LSK4
        if stbFreq1!=self.__oldStbFreq1:
            if (self.__editCur=="COM1"):
                self.mqttpublish(Config.topic_display, "T,04,98,0,3,"+str('{0:.3f}'.format(stbFreq1)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,Com1StbFq/Psh SW>")
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
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,Com2StbFq/Psh SW>")
            else:
                self.mqttpublish(Config.topic_display, "T,34,99,1,3,"+str('{0:.3f}'.format(stbFreq2)))
            self.__oldStbFreq2=stbFreq2

        # ADF at LSK7
        if adfFreq!=self.__oldAdfFreq:
            if (self.__editCur=="ADF"):
                self.mqttpublish(Config.topic_display, "T,07,98,0,3,"+str('{0:0>6.1f}'.format(adfFreq)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,           ADFFq>")
            else:
                self.mqttpublish(Config.topic_display, "T,07,99,1,3,"+str('{0:0>6.1f}'.format(adfFreq)))
            self.__oldAdfFreq=adfFreq

        # XPDR at RSK7
        if xpdrCode!=self.__oldXpdrCode:
            if (self.__editCur=="XPDR"):
                self.mqttpublish(Config.topic_display, "T,37,98,0,3,"+str('{0:0>4.0f}'.format(int(oct(xpdrCode)))))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,       XPDR code>")
            else:
                self.mqttpublish(Config.topic_display, "T,37,99,1,3,"+str('{0:0>4.0f}'.format(int(oct(xpdrCode)))))
            self.__oldXpdrCode=xpdrCode

        if (not(event.isEmpty())):

            if (event.getTopic()=="j/npanel/e/s" and event.getPayload()=="1"):
                self.draw();
                logger.debug("Redraw")

            if event.getTopic()==Config.topic_keys:

                if event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1-0.025))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2-0.025))])
                    if (self.__editCur=="ADF"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],adf_float2bcd(adfFreq-0.5)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],adf_float2bcd(adfFreq-0.5)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],xpdr_int2bcd(int(oct(xpdrCode-1))))])

                if event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1+0.025))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2+0.025))])
                    if (self.__editCur=="ADF"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],adf_float2bcd(adfFreq+0.5)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],adf_float2bcd(adfFreq+0.5)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],xpdr_int2bcd(int(oct(xpdrCode+1))))])
                    event.clear()

                if event.getPayload()==str(Const.BTENC): # SW
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(actFreq1))])
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],vhf_float2bcd(stbFreq1))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(actFreq2))])
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vhf_float2bcd(stbFreq2))])
                    event.clear()

                if event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1-1))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2-1))])
                    if (self.__editCur=="ADF"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],adf_float2bcd(adfFreq-10)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],adf_float2bcd(adfFreq-10)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],xpdr_int2bcd(int(oct(xpdrCode-64))))])
                    event.clear()

                if event.getPayload()==str(Const.ENC2UP): # INC2 UP
                    if (self.__editCur=="COM1"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],vhf_float2bcd(stbFreq1+1))])
                    if (self.__editCur=="COM2"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],vhf_float2bcd(stbFreq2+1))])
                    if (self.__editCur=="ADF"):
                        pyuipc.write([(self.__OFFSETS[4][0],self.__OFFSETS[4][1],adf_float2bcd(adfFreq+10)[0])])
                        pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],adf_float2bcd(adfFreq+10)[1])])
                    if (self.__editCur=="XPDR"):
                        pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],xpdr_int2bcd(int(oct(xpdrCode+64))))])
                    event.clear()

                if event.getPayload()==str(Const.RSK4): #COM2
                    self.__editCur="COM2"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.LSK4): #COM1
                    self.__editCur="COM1"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.LSK7): #ADF
                    self.__editCur="ADF"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.RSK7): #XPDR
                    self.__editCur="XPDR"
                    self.draw()
                    event.clear()
