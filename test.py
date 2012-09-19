#!/usr/bin/python
import xmpp
import sys
import os
import signal
import time
import threading

try:
    username = sys.argv[1]
    passwd = 'AIR_%s' % sys.argv[2]
    out_message = ''
    alive_users = []
except IndexError:
    sys.exit("\nEnter a username and password\n")

def presenceCB(conn,msg):
    #Needs to work with logging in and off
    #Currently only adds to the list
    if str(msg.getFrom()) not in alive_users:
        alive_users.append(str(msg.getFrom()))

def messageCB(conn,msg):
    print "\n"
    print "Sender: " + str(msg.getFrom())
    print "Content: " + str(msg.getBody())
    print "\n"

class CheckMessages(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn
        self.user_length = 0

    def StepOn(self):
        try:
            self.conn.Process(1)
            roster = self.conn.getRoster()
            roster_list = roster.getItems()

            if self.user_length != len(alive_users):
                for user in alive_users:
                    print roster.getName(user)
            self.user_length = len(alive_users)

        except KeyboardInterrupt:
            return 0
        return 1

    def run(self):
        while self.StepOn():
            pass

def main():
    cl = xmpp.Client('pvp.net', debug=[])
    if cl.connect(server=('chat.na1.lol.riotgames.com',5223)) == "":
        print "not connected"
        sys.exit(0)
    if cl.auth(username,passwd,"xiff") == None:
        print "authentication failed"
        sys.exit(0)
    cl.sendInitPresence(requestRoster=1)

    cl.RegisterHandler('presence', presenceCB)
    cl.RegisterHandler('message', messageCB)

    incoming_thread = CheckMessages(cl)
    incoming_thread.setDaemon(True)
    incoming_thread.start()

    while True:
        out_message = raw_input()
        message = xmpp.Message("sum19504585@pvp.net", out_message)
        message.setAttr('type', 'chat')
        cl.send(message)

if __name__ == '__main__': 
    try:
        main()
    except KeyboardInterrupt:
        print "Logging off..."
