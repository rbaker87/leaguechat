#!/usr/bin/python
import xmpp
import sys
import re
import time
from chatutils import CheckMessages

try:
    username = sys.argv[1]
    passwd = 'AIR_%s' % sys.argv[2]
    out_message = ''
except IndexError:
    sys.exit("\nEnter a username and password\n")

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

        incoming_thread = CheckMessages(cl)
        incoming_thread.setDaemon(True)
        incoming_thread.start()

        cl.RegisterHandler('presence', incoming_thread.presenceCB)
        cl.RegisterHandler('message', incoming_thread.messageCB)

        to_jid = None #jid for the user receiving the message
        time.sleep(2.1) #Extremely inelegant solution to making the first prompt appear after the friends list populates. Fix later
        while True:
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
                        try:
                            to_jid = roster.getName(to_jid)
                        except (KeyError, TypeError):
                            to_jid = None
                    else:
                        out_message = ''
                        to_jid = None
                except IndexError:
                    out_message = ''
                    to_jid = None

            if to_jid:
                for user in incoming_thread.alive_users:
                    if str(roster.getName(user)).lower() == str(to_jid).lower():
                        to_jid = user
                        valid_jid = True
                        break
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
