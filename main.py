#!/usr/bin/python
import xmpp
import sys
import os
import re
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
    sys.stdout.write("%s: %s\n" % (str(msg.getFrom()), str(msg.getBody())))

class CheckMessages(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn
        self.user_length = 0
        self.first_run = True

    def StepOn(self):
        try:
            self.conn.Process(1)
            if self.first_run:
                #Give the roster some time to populate correctly. Need a more elegant solution to this
                time.sleep(2) 
                self.first_run = False
            roster = self.conn.getRoster()
            roster_list = roster.getItems()

            if self.user_length != len(alive_users):
                sys.stdout.write("***Friends List***\n")
                for user in alive_users:
                    if roster.getName(user) != None:
                        sys.stdout.write("%s\n" % roster.getName(user))
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
        sys.stderr.write("Not connected\n")
        sys.exit(0)
    if cl.auth(username,passwd,"xiff") == None:
        sys.stderr.write("Authentication failed\n")
        sys.exit(0)
    if cl.isConnected():
        cl.sendInitPresence(requestRoster=1)

        cl.RegisterHandler('presence', presenceCB)
        cl.RegisterHandler('message', messageCB)

        incoming_thread = CheckMessages(cl)
        incoming_thread.setDaemon(True)
        incoming_thread.start()

        to_jid = '' #jid for the user receiving the message
        time.sleep(2.1) #Extremely inelegant solution to making the first prompt appear after the friends list populates. Fix later
        while True:
            sys.stdout.write("%s: " % username)
            out_message = raw_input()
            out_message = re.split('(/\w+) (\w+)', out_message)
            roster = cl.getRoster()
            roster_list = roster.getItems()
            try:
                if out_message[1] == '/w':
                    to_jid = out_message[2]
                    out_message = out_message[3]
            except IndexError:
                try:
                    if out_message[0] != '':
                        out_message = out_message[0]
                        to_jid = roster.getName(to_jid)
                    else:
                        out_message = ''
                        to_jid = None
                except IndexError:
                    out_message = ''
                    to_jid = None

            if to_jid:
                for user in alive_users:
                    if roster.getName(user) == to_jid:
                        to_jid = user
                        valid_jid = True
                    else:
                        valid_jid = False
                if valid_jid:
                    message = xmpp.Message(to_jid, out_message)
                    message.setAttr('type', 'chat')
                    cl.send(message)
                else:
                    sys.stderr.write("User not found...\n")
    else:
        sys.stderr.write("Error connecting to server...\n")

if __name__ == '__main__': 
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\nLogging off...\n")
