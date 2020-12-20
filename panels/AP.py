from modules.Panel import Panel
from modules.Config import Config
import pyuipc
from modules.fsconvert import *
from modules.Const import Const
import logging

class AP(Panel):

    def __init__(self, client):
        logging.debug("AP class initialized")
        Panel.__init__(self,client)
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

    def run(self,event):
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
                self.mqttpublish(Config.topic_display, "T,38,94,0,1, Set ALT (x1000 ox100>")
            else:
                self.mqttpublish(Config.topic_display, "T,03,99,1,2,"+str('{0:0>5.0f}'.format(altitude//100*100)))
            self.__oldAltitude=altitude

        # IAS at LCK3
        if IAS!=self.__oldIAS:
            if (self.__editCur=="IAS"):
                self.mqttpublish(Config.topic_display, "T,13,98,0,3,"+str('{0:0>3.0f}'.format(IAS)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1, Set IAS (x10 ox1>")
            else:
                self.mqttpublish(Config.topic_display, "T,13,99,1,3,"+str('{0:0>3.0f}'.format(IAS)))
            self.__oldIAS=IAS

        # HDG at RSK3
        if heading!=self.__oldHeading:
            if (self.__editCur=="HDG"):
                self.mqttpublish(Config.topic_display, "T,23,98,0,3,"+str('{0:0>3.0f}'.format(heading)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1, Set HDG (x10 ox1>")
            else:
                self.mqttpublish(Config.topic_display, "T,23,99,1,3,"+str('{0:0>3.0f}'.format(heading)))
            self.__oldHeading=heading

        # VERTICAL SPEED at LSK6
        if vertSpeed!=self.__oldVertSpeed:
            if (self.__editCur=="VERTSPEED"):
                self.mqttpublish(Config.topic_display, "T,06,98,0,2,"+str('{0:05.0f}'.format(vertSpeed)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1,Set Vspd (x1000 ox100>")
            else:
                self.mqttpublish(Config.topic_display, "T,06,99,1,2,"+str('{0:05.0f}'.format(vertSpeed)))
            self.__oldVertSpeed=vertSpeed

        # Course at RSK6
        if Course!=self.__oldCourse:
            if (self.__editCur=="COURSE"):
                self.mqttpublish(Config.topic_display, "T,33,98,0,3,"+str('{0:0>3.0f}'.format(Course)))
                self.mqttpublish(Config.topic_display, "T,38,94,0,1, Set CRS  (x10 ox1>")
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

        if (not(event.isEmpty())):

            if (event.getTopic()=="j/npanel/e/s" and event.getPayload()=="1"):
                self.draw();
                logging.debug("Redraw")

            if event.getTopic()==Config.topic_keys:

                if event.getPayload()==str(Const.ENC1DN): # INC1 DN
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude-99)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],bearing(heading-1)*182)])
                    if (self.__editCur=="VERTSPEED"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed-100)])
                    if (self.__editCur=="COURSE"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],bearing(Course-1))])
                    event.clear()

                if event.getPayload()==str(Const.ENC1UP): # INC1 UP
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude+101)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],bearing(heading+1)*182)])
                    if (self.__editCur=="VERTSPEED"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed+100)])
                    if (self.__editCur=="COURSE"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],bearing(Course+1))])
                    event.clear()

                if event.getPayload()==str(Const.ENC2DN): # INC2 DN
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude-999)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],bearing(heading-10)*182)])
                    if (self.__editCur=="VERTSPEED"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed-100)])
                    if (self.__editCur=="COURSE"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],bearing(Course-10))])
                    event.clear()

                if event.getPayload()==str(Const.ENC2UP): # INC2 UP
                    if (self.__editCur=="ALT"):
                        pyuipc.write([(self.__OFFSETS[0][0],self.__OFFSETS[0][1],(altitude+1001)*19975)])
                    if (self.__editCur=="HDG"):
                        pyuipc.write([(self.__OFFSETS[1][0],self.__OFFSETS[1][1],bearing(heading+10)*182)])
                    if (self.__editCur=="VERTSPEED"):
                        pyuipc.write([(self.__OFFSETS[2][0],self.__OFFSETS[2][1],vertSpeed+100)])
                    if (self.__editCur=="COURSE"):
                        pyuipc.write([(self.__OFFSETS[3][0],self.__OFFSETS[3][1],bearing(Course+10))])
                    event.clear()

                if event.getPayload()==str(Const.LSK3): #ALT
                    self.__editCur="ALT"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.LSK4): # LockAlt
                    lockALT=lockALT^1
                    pyuipc.write([(self.__OFFSETS[5][0],self.__OFFSETS[5][1],lockALT)])
                    event.clear()

                if event.getPayload()==str(Const.LCK3): #IAS
                    self.__editCur="IAS"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.LCK4): # LockIAS
                    lockIAS=lockIAS^1
                    pyuipc.write([(self.__OFFSETS[6][0],self.__OFFSETS[6][1],lockIAS)])
                    event.clear()

                if event.getPayload()==str(Const.LCK5): # LockAT
                    lockAT=lockAT^1
                    pyuipc.write([(self.__OFFSETS[8][0],self.__OFFSETS[8][1],lockAT)])
                    event.clear()

                if event.getPayload()==str(Const.RCK3): #HDG
                    self.__editCur="HDG"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.RCK4): # LockHDG
                    lockHDG=lockHDG^1
                    pyuipc.write([(self.__OFFSETS[7][0],self.__OFFSETS[7][1],lockHDG)])
                    event.clear()

                if event.getPayload()==str(Const.LSK6): #VERTSPEED
                    self.__editCur="VERTSPEED"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.RSK3): #COURSE
                    self.__editCur="COURSE"
                    self.draw()
                    event.clear()

                if event.getPayload()==str(Const.RSK4): # LockNAV
                    lockNAV=lockNAV^1
                    pyuipc.write([(self.__OFFSETS[9][0],self.__OFFSETS[9][1],lockNAV)])
                    event.clear()

                if event.getPayload()==str(Const.RSK5): # LockBC
                    lockBC=lockBC^1
                    pyuipc.write([(self.__OFFSETS[10][0],self.__OFFSETS[10][1],lockBC)])
                    event.clear()

                if event.getPayload()==str(Const.RSK6): # LockAPP
                    lockAPP=lockAPP^1
                    pyuipc.write([(self.__OFFSETS[11][0],self.__OFFSETS[11][1],lockAPP)])
                    #pyuipc.write([(0x800,'u',lockAPP)]) #Specific to APP offset, must write at two offsets
                    event.clear()

                if event.getPayload()==str(Const.LCK7): # LockATT
                    lockATT=lockATT^1
                    pyuipc.write([(self.__OFFSETS[12][0],self.__OFFSETS[12][1],lockATT)])
                    event.clear()

                if event.getPayload()==str(Const.RCK7): # LockYD
                    lockYD=lockYD^1
                    pyuipc.write([(self.__OFFSETS[13][0],self.__OFFSETS[13][1],lockYD)])
                    event.clear()