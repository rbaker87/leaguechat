"""PyLoL - Websocket handlers for interacting with the Riot Jabber servers"""

import xmpp
import threading
from mod_pywebsocket import msgutil
from messages_en import *   #Eventually support other localizations

class CheckMessages(threading.Thread):
    """
    Constantly check for network data in a separate thread.
    """

    def __init__(self, conn, message_sender):
        threading.Thread.__init__(self)
        self.conn = conn
        self.user_length = 0
        self.alive_users = []
        self.message_sender = message_sender

    def presence_update(self, conn, msg):
        """
        Receive and process jabber presence updates.
        """

        if str(msg.getType()) != "unavailable":
            if str(msg.getFrom()) not in self.alive_users:
                self.alive_users.append(str(msg.getFrom()))
            roster = self.conn.getRoster()
            received_from = 'Blank'
            for user in self.alive_users:
                if str(user) == str(msg.getFrom()):
                    received_from = roster.getName(user)
            status_msg = str(msg.getStatus())
            endpoint = status_msg.find("</statusMsg>")
            if endpoint != -1:
                startpoint = status_msg.find("<statusMsg>") + 11
                self.message_sender.send_nowait("#:#statusupdate#:#%s:%s" % (str(received_from), status_msg[startpoint:endpoint]))
                self.message_sender.send_nowait("#:#clearfriends#:#")
                for user in self.alive_users:
                    if roster.getName(user) != None:
                        self.message_sender.send_nowait("#:#friendupdate#:#%s" % roster.getName(user))
        else:
            self.alive_users.remove(str(msg.getFrom()))

    def message_update(self, conn, msg):
        """
        Receive and process jabber messages.
        """

        roster = self.conn.getRoster()
        received_from = 'Blank'
        for user in self.alive_users:
            if str(user) == str(msg.getFrom()):
                received_from = roster.getName(user)
        self.message_sender.send_nowait("#:#message#:#%s: %s" % (str(received_from), str(msg.getBody())))

    def step_on(self):
        """
        Keep the connection alive and process network data on an interval.
        """

        if self.conn.isConnected():
            try:
                self.conn.Process(1)
                roster = self.conn.getRoster()

                if self.user_length != len(self.alive_users):
                    self.message_sender.send_nowait("#:#clearfriends#:#")
                    for user in self.alive_users:
                        if roster.getName(user) != None:
                            self.message_sender.send_nowait("#:#friendupdate#:#%s" % roster.getName(user))
                self.user_length = len(self.alive_users)
            except:
                self.message_sender.send_nowait(CONN_ERROR)
                return 0
        else:
            self.message_sender.send_nowait(CONN_ERROR)
            return 0
        return 1

    def run(self):
        """
        Maintain iteration while the connection exists.
        """

        while self.step_on():
            pass

def web_socket_do_extra_handshake(request):
    """
    Handle initial data on connection.
    """

    pass  # Always accept.


def web_socket_transfer_data(request):
    """
    Loop while connection exists and process data to be sent and received.
    """

    try:
        line = request.ws_stream.receive_message()
        if str(line).startswith('username'):
            username = str(line)[8:]
        line = request.ws_stream.receive_message()
        if str(line).startswith('password'):
            passwd = 'AIR_' + str(line)[8:]
        out_message = ''
        client = xmpp.Client('pvp.net', debug=[])
        if client.connect(server=('chat.na1.lol.riotgames.com', 5223)) == "":
            request.ws_stream.send_message(CONN_ERROR, binary=False)
            return
        if client.auth(username, passwd, "xiff") == None:
            request.ws_stream.send_message(AUTH_ERROR, binary=False)
            return
        if client.isConnected():
            client.sendInitPresence(requestRoster=1)

            message_sender = msgutil.MessageSender(request)

            incoming_thread = CheckMessages(client, message_sender)
            incoming_thread.setDaemon(True)
            incoming_thread.start()

            client.RegisterHandler('presence', incoming_thread.presence_update)
            client.RegisterHandler('message', incoming_thread.message_update)

            request.ws_stream.send_message(CONN_SUCCESS, binary=False)
            to_jid = None #jid for the user receiving the message
            while True:
                line = request.ws_stream.receive_message()
                if client.isConnected():    #Check connection on each loop
                    out_message = str(line)
                    if ((out_message != "Keep alive") and (out_message != "Kill session")):
                        split_out = out_message.split()
                        roster = client.getRoster()
                        try:
                            if split_out[0] == '#:#outmessage#:#':
                                to_jid = split_out[1][3:-3]
                                out_message = ' '.join(split_out[2:])
                        except IndexError:
                            to_jid = None
                            out_message = ''

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
                                client.send(message)
                            else:
                                request.ws_stream.send_message(USER_WARNING, binary=False)
                    if (out_message == "Kill session"):
                        client.disconnect()
                        return
                else:
                    request.ws_stream.send_message(CONN_ERROR, binary=False)
                    return
        else:
            request.ws_stream.send_message(CONN_ERROR, binary=False)
            return
    except IOError: #Something was causing apache to overload... Meh?
        return
