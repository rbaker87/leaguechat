#!/usr/bin/python
import time
import threading
import signal
import sys
from messages import *

class CheckMessages(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn
        self.user_length = 0
        self.first_run = True
        self.alive_users = []

    def presenceCB(self,conn,msg):
        #Needs to work with logging in and off
        #Currently only adds to the list
        if str(msg.getFrom()) not in self.alive_users:
            self.alive_users.append(str(msg.getFrom()))
        print msg.getStatus()

    def messageCB(self,conn,msg):
        roster = self.conn.getRoster()
        received_from = 'Blank'
        for user in self.alive_users:
            if str(user) == str(msg.getFrom()):
                received_from = roster.getName(user)
        sys.stdout.write("\n%s: %s\n\n" % (received_from, str(msg.getBody())))

    def StepOn(self):
        try:
            self.conn.Process(1)
            if self.first_run:
                #Give the roster some time to populate correctly. Need a more elegant solution to this
                time.sleep(2) 
                self.first_run = False
            roster = self.conn.getRoster()
            roster_list = roster.getItems()

            if self.user_length != len(self.alive_users):
                sys.stdout.write("***Friends List***\n")
                for user in self.alive_users:
                    if roster.getName(user) != None:
                        sys.stdout.write("%s\n" % roster.getName(user))
            self.user_length = len(self.alive_users)

        except KeyboardInterrupt:
            return 0
        return 1

    def run(self):
        while self.StepOn():
            pass
