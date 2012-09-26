import xmpp
import time
import threading
import signal
import re
from mod_pywebsocket import msgutil

class CheckMessages(threading.Thread):
    def __init__(self, conn, message_sender):
        threading.Thread.__init__(self)
        self.conn = conn
        self.user_length = 0
        self.alive_users = []
        self.first_run = True
        self.message_sender = message_sender

    def presenceCB(self,conn,msg):
        if str(msg.getType()) != "unavailable":
            if str(msg.getFrom()) not in self.alive_users:
                self.alive_users.append(str(msg.getFrom()))
        else:
            self.alive_users.remove(str(msg.getFrom()))

    def messageCB(self,conn,msg):
        roster = self.conn.getRoster()
        received_from = 'Blank'
        for user in self.alive_users:
            if str(user) == str(msg.getFrom()):
                received_from = roster.getName(user)
        self.message_sender.send_nowait("#:#message#:#%s: %s" % (str(received_from), str(msg.getBody())))

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
                self.message_sender.send_nowait("#:#clearfriends#:#")
                for user in self.alive_users:
                    if roster.getName(user) != None:
                        self.message_sender.send_nowait("#:#friendupdate#:#%s" % roster.getName(user))
            self.user_length = len(self.alive_users)

        except KeyboardInterrupt:
            return 0
        return 1

    def run(self):
        while self.StepOn():
            pass

def web_socket_do_extra_handshake(request):
    pass  # Always accept.


def web_socket_transfer_data(request):
    try:
        from messages_en import *   #Eventually support other localizations
        line = request.ws_stream.receive_message()
        if str(line).startswith('username'):
            username = str(line)[8:]
        line = request.ws_stream.receive_message()
        if str(line).startswith('password'):
            passwd = 'AIR_' + str(line)[8:]
        out_message = ''
        cl = xmpp.Client('pvp.net', debug=[])
        if cl.connect(server=('chat.na1.lol.riotgames.com',5223)) == "":
            request.ws_stream.send_message(CONN_ERROR, binary=False)
        if cl.auth(username,passwd,"xiff") == None:
            request.ws_stream.send_message(AUTH_ERROR, binary=False)
        if cl.isConnected():
            cl.sendInitPresence(requestRoster=1)

            message_sender = msgutil.MessageSender(request)

            incoming_thread = CheckMessages(cl, message_sender)
            incoming_thread.setDaemon(True)
            incoming_thread.start()

            cl.RegisterHandler('presence', incoming_thread.presenceCB)
            cl.RegisterHandler('message', incoming_thread.messageCB)

            to_jid = None #jid for the user receiving the message
            time.sleep(2.1) #Extremely inelegant solution to making the first prompt appear after the friends list populates. Fix later
            while True:
                line = request.ws_stream.receive_message()
                out_message = str(line)
                if out_message != "Keep alive":
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
                            request.ws_stream.send_message(USER_WARNING, binary=False)
        else:
            request.ws_stream.send_message(CONN_ERROR, binary=False)
    except IOError: #Something was causing apache to overload... Meh?
        return
# vi:sts=4 sw=4 et
