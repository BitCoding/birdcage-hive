# encoding: iso-8859-1

# Copyright (C) 2013 by Bitcoding
# Copyright (C) 20011-2013 by Booksize
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
#

import CP, FILEIO
import time, threading, sys, os, commands
from collections import deque

# BaseAddress
address = "400"
m_version ="0.1"
LOCK = threading.Lock()

#The FIFO-Buffer for incomming commands
class Fifo:
    def __init__(self):
        self.first_a= deque()
        self.first_b= deque()

    def append(self,data,handler):
        self.first_a.append(data)
        self.first_b.append(handler)

    def pop(self):
        try:
            return self.first_a.popleft(), self.first_b.popleft()
        except (IndexError):
            pass

    def hascontent(self):
        if (len(self.first_a) > 0):
            return True
        return False

class Screen:
    CP #Pointer for the CP

    def __init__(self, CP):
        self.screens = []
        self.CP = CP

        CP.sLog.outString("Starting Screens Version: " + m_version)
        return

    def Update(self):
        if LOCK.acquire(False): # Non-blocking
            for t in self.screens:
                if(t[1] == "true"):
                    if(self.GetPid(t[0]) == False):
                        t[5] = t[5] + 1
                        if(t[5] >= 5):
                            t[1] = "false"
                            t[5] = 0
                        else:
                            self._StartScreen(self.GetScreen(t[0]))
                    else:
                        t[5] = 0
            LOCK.release()
        else:
            self.CP.ToLog("Critical", "Couldn't get the lock. Screen::Update")
        return
    def cmd(self, screen , cmd):
        for t in self.screens:
            if(screen == 0):
                if not (t):
                    continue
                pid = self.GetPid(t[0])
                if(pid == False):
                    self.CP.sLog.outString("Screen["+ t[0] +"]: Stopped")
                else:
                    self.CP.sLog.outString("Screen["+ t[0] +"]: Running")
                continue
            if(t[0] ==  screen):
                if(cmd == "stats"):
                    pid = self.GetPid(t[0])
                    if(pid == False):
                        self.CP.sLog.outString("Screen["+ t[0] +"]: Stopped")
                    else:
                        self.CP.sLog.outString("Screen["+ t[0] +"]: Running")
                if(cmd == "stop" or cmd == "restart"):
                    pid = self.GetPid(t[0])
                    t[1] = "false"
                    t[5] = 0
                    if(pid == False):
                        self.CP.sLog.outString("Screen["+ t[0] +"]: isStopped")
                    else:
                        self._StopScreen(pid)
                if(cmd == "start" or cmd == "restart"):
                    pid = self.GetPid(t[0])
                    t[1] = "true"
                    t[5] = 0
                    if(pid == False):
                        self._StartScreen(self.GetScreen(t[0]))
                    else:
                        self.CP.sLog.outString("Screen["+ t[0] +"]: isRunning")
                return
        if(screen == 0):
            return
        self.CP.sLog.outString("Screen[NOT EXIST]")
        return
    def GetPid(self,screen):
        for t in self.screens:
            if(t[0] ==  screen):
                p = os.popen ("sudo -u " + t[2] + " screen -list | grep "+ t[0] +" | cut -f1 -d'.' | sed 's/\W//g'")
                pid = p.read()
                p.close()
                if(pid == ""):
                    return False
                return pid
        return False

    def GetScreen(self,screen):
        for t in self.screens:
            if(t[0] ==  screen):
                return [t[0],t[1],t[2],t[3],t[4],t[5]]
        return ["NULL",0,0,0,0,0]

    def _StartScreen(self,t):
        if(self.GetPid(t[0]) == False):
            os.system ("sudo -u " + t[2] + " screen -A -m -d -S " + t[0] + " " + t[3] + " " + t[4])
            return True
        return False

    def _StopScreen(self,pid):
        if(pid == False):
            return False
        p = os.popen ("kill " + pid)
        out = p.readline()
        p.close()
        return True
        
    def Start(self):
        for r_item in self.screens:
            if(r_item[1] == "true"):
                self._StartScreen(self.GetScreen(r_item[0]))
        return
        
    def Stop(self):
        for r_item in self.screens:
            self._StopScreen(self.GetPid(r_item[0]))
        return

    def InsertService(self, name, autostart, user, sbin, opts):
        self.screens.append([name,autostart,user,sbin,opts,0])
        return
## define Checking-Thread
class Master(threading.Thread):
    check = True;
    wait=True;
    interval = 5;
    CP #Pointer for the CP

    def __init__(self,CP):
        ## Set the CP
        self.CP = CP
        self.initialized = False

        ## Setup the Buffer
        self.buffer = Fifo()

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        self.screen = Screen(self.CP)

    def initfromdrone(self, args, handler):
        return

    def run(self):
        while Master.check:
            self.update()
            self.screen.Update()
            time.sleep(self.interval)

    def config(self, args, CP):
        if (self.initialized == True):
            return
        self.initialized = True

        self.m_args = FILEIO.FileIO().ReadLine("./configs/mod_Screen.conf")
        self.defaultuser = ""
        self.name        = ""
        self.autostart   = "false"
        self.user        = ""
        self.sbin        = ""
        self.opts        = ""
        self.temp = self.m_args.split("\n")
        for self.r_item in self.temp:
            if not (self.r_item):
                continue
            if self.r_item[0] == "#":
                continue
            if ("screen-defaultuser" in self.r_item):
                self.defaultuser = self.r_item.split("=")[1].strip()
                self.user = self.defaultuser
            if ("screen-name" in self.r_item):
                self.name = self.r_item.split("=")[1].strip()
            if ("screen-autostart" in self.r_item):
                self.autostart = self.r_item.split("=")[1].strip()
            if ("screen-user" in self.r_item):
                self.user = self.r_item.split("=")[1].strip()
            if ("screen-sbin" in self.r_item):
                self.sbin = self.r_item.split("=")[1].strip()
            if ("screen-opts" in self.r_item):
                self.opts = self.r_item.split("=")[1].strip()
            if ("screen-instert" in self.r_item):
                self.CP.sLog.outString("Adding Screen:"  + self.name)
                self.screen.InsertService(self.name,self.autostart,self.user,self.sbin,self.opts)
                self.name       = ""
                self.autostart  = "false"
                self.user       = self.defaultuser
                self.sbin       = ""
                self.opts       = ""

                self.screen.Start()
        return

    def command(self,args, handler):
        self.buffer.append(args,handler)
        return

    def update(self):
        while (self.buffer.hascontent() == True):

            args, handler = self.buffer.pop()

            omv = args.split(" ")
            if omv[0] == address:
                #screen
                if omv[1] == "1":
                    self.screen.cmd(0,0)
                if omv[1] == "2":
                    self.screen.cmd(omv[2],omv[3])
        return
    def stop(self):
        self.screen.Stop()
        Master.check = False
        return True

    def pause(self):
        Master.wait = True

    def unpause(self):
        Master.wait = False

#CLI Dictionary
class CLI_Dict:
    def get(self,args):
        try:
            self.maxlen = len(args.split(" ")) - 1
            if (args.split(" ")[0] == "version"):
                print (m_version)
                return
            if (args.split(" ")[0] == "screen-list"):
                return "400 1"
            if (args.split(" ")[0] == "screen"):
                return "400 2 " + args.split(" ")[1] + " " + args.split(" ")[2]
            if (args.split(" ")[0] == "usage"):
                print "version"
                print "screen-list"
                print "screen [name] [option=start/stop/restart/stats]"
            return
        except IndexError:
            print args
            return

#########################################
############# Commands ##################
#########################################
