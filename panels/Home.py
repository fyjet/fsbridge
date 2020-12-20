from modules.Panel import Panel
from modules.Config import Config
import pyuipc
from modules.fsconvert import *
from modules.Const import Const
import logging
import __main__

class Home(Panel):
    """home panel class"""

    def __init__(self, client):
        logging.debug("Home class initialized")
        Panel.__init__(self,client)
        self.draw()

    def draw(self):
        self.mqttpublish(Config.topic_display, "N,MAIN MENU")
        self.mqttpublish(Config.topic_display, "B,02,COM")
        self.mqttpublish(Config.topic_display, "B,04,NAV")
        self.mqttpublish(Config.topic_display, "B,06,AUDIO")

        if (__main__.hasAP):
            self.mqttpublish(Config.topic_display, "B,32,AUTOPIL")
        self.mqttpublish(Config.topic_display, "B,34,TRIM")
        self.mqttpublish(Config.topic_display, "B,36,PERFS")


    def run(self, event):

        if (not(event.isEmpty())):

            if (event.getTopic()=="j/npanel/e/s" and event.getPayload()=="1"):
                self.draw();
                logging.debug("Redraw")

            if event.getTopic()==Config.topic_keys:
                if event.getPayload()==str(Const.LSK2):
                    __main__.actMode="RtuCom"
                    event.clear()
                if event.getPayload()==str(Const.LSK4):
                    __main__.actMode="RtuNav"
                    event.clear()
                if event.getPayload()==str(Const.LSK6):
                    __main__.actMode="Audio"
                    event.clear()
                if event.getPayload()==str(Const.RSK2):
                    __main__.actMode="AP"
                    event.clear()
                if event.getPayload()==str(Const.RSK4): # LSK6
                    __main__.actMode="Trim"
                    event.clear()
                if event.getPayload()==str(Const.RSK6): # RSK4
                    __main__.actMode="Perfs"
                    event.clear()