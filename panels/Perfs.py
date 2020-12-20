from modules.Panel import Panel
from modules.Config import Config
import pyuipc
from modules.fsconvert import *
from modules.Const import Const
import logging

class Perfs(Panel):

    def __init__(self, client):
        logging.debug("Perfs class initialized")
        Panel.__init__(self,client)
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

    def run(self, event):
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

        if (not(event.isEmpty())):

            if (event.getTopic()=="j/npanel/e/s" and event.getPayload()=="1"):
                self.draw();
                logging.debug("Redraw")