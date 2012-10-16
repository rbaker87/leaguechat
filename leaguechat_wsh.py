"""PyLoL - Websocket handlers for interacting with the Riot Jabber servers"""

import xmpp
import threading
import time
from datetime import datetime
from mod_pywebsocket import msgutil
from messages_en import *   #Eventually support other localizations

#Time between non-blocking message checking
RECEIVE_BUFFER = 0.5

#Maximum allowed time between keepalive requests
WEBSOCKET_TIMEOUT = 60

#User profile settings
STATUS_MSG = "<body>\
    <profileIcon>0</profileIcon>\
    <level>1</level>\
    <wins>0</wins>\
    <leaves>0</leaves>\
    <odinWins>0</odinWins>\
    <odinLeaves>0</odinLeaves>\
    <queueType>RANKED_SOLO_5x5</queueType>\
    <rankedWins>0</rankedWins>\
    <rankedLosses>0</rankedLosses>\
    <rankedRating>0</rankedRating>\
    <tier>BRONZE</tier>\
    <gameStatus>outOfGame</gameStatus>\
    <statusMsg>PyLoL</statusMsg>\
    </body>"

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
        self.first_run = True

    def get_name(self, msg_from):
        roster = self.conn.getRoster()
        received_from = 'Blank'
        for user in self.alive_users:
            if str(user) == str(msg_from):
                received_from = roster.getName(user)
        return str(received_from)

    def presence_update(self, conn, msg):
        """
        Receive and process jabber presence updates.
        """

        if str(msg.getType()) != "unavailable":
            if str(msg.getFrom()) not in self.alive_users:
                self.alive_users.append(str(msg.getFrom()))
            received_from = self.get_name(msg.getFrom())
            if received_from != "None":
                status_msg = str(msg.getStatus())
                endpoint = status_msg.find("</statusMsg>")
                if endpoint != -1:
                    startpoint = status_msg.find("<statusMsg>") + 11
                    self.message_sender.send_nowait("#:#statusupdate#:#%s:%s" % (received_from, status_msg[startpoint:endpoint]))
                else:
                    self.message_sender.send_nowait("#:#statusupdate#:#%s:%s" % (received_from, ''))
                endpoint = status_msg.find("</gameStatus>")
                if endpoint != -1:
                    startpoint = status_msg.find("<gameStatus>") + 12
                    if status_msg[startpoint:endpoint] == 'inGame':
                        self.message_sender.send_nowait("#:#gameupdate#:#%s:%s" % (received_from, 'In Game'))
                    elif status_msg[startpoint:endpoint] == 'inQueue':
                        self.message_sender.send_nowait("#:#gameupdate#:#%s:%s" % (received_from, 'In Queue'))
                    elif status_msg[startpoint:endpoint] == 'outOfGame':
                        self.message_sender.send_nowait("#:#gameupdate#:#%s:%s" % (received_from, 'Online'))
                    elif status_msg[startpoint:endpoint] == 'hostingPracticeGame':
                        self.message_sender.send_nowait("#:#gameupdate#:#%s:%s" % (received_from, 'Hosting a Practice Game'))
                    elif status_msg[startpoint:endpoint] == 'championSelect':
                        self.message_sender.send_nowait("#:#gameupdate#:#%s:%s" % (received_from, 'In Champion Select'))
                    elif status_msg[startpoint:endpoint] == 'spectating':
                        endpoint = status_msg.find("</dropInSpectateGameId>")
                        if endpoint != -1:
                            startpoint = status_msg.find("<dropInSpectateGameId>") + 22
                            if 'featured_game' in status_msg[startpoint:endpoint]:
                                game_name = 'Featured Game'
                            else:
                                game_name = status_msg[startpoint:endpoint]
                        else:
                            game_name = ''
                        self.message_sender.send_nowait("#:#gameupdate#:#%s:%s" % (received_from, 'Spectating %s' % game_name))
                    else:
                        self.message_sender.send_nowait("#:#gameupdate#:#%s:%s" % (received_from, status_msg[startpoint:endpoint]))
        elif str(msg.getType()) == 'unsubscribe':
            self.conn.send(xmpp.Presence(to=msg.getFrom(), frm=msg.getTo(), typ='unsubscribe'))
        elif str(msg.getType()) == 'subscribe':
            pass #Can't handle subscriptions without access to JID names
        elif str(msg.getType()) == "unavailable":
            received_from = self.get_name(msg.getFrom())
            self.message_sender.send_nowait("#:#removefriend#:#%s" % received_from)
            self.alive_users.remove(str(msg.getFrom()))

    def message_update(self, conn, msg):
        """
        Receive and process jabber messages.
        """

        received_from = self.get_name(msg.getFrom())
        status_msg = str(msg.getBody())
        endpoint = status_msg.find("</gameType>")
        if ((endpoint != -1) and (status_msg.find('<inviteId>') != -1)):    #Redundant on the offchance someone uses one of these tags in a real message
            startpoint = status_msg.find("<gameType>") + 10
            self.message_sender.send_nowait("#:#gameinvite#:#%s:%s" % (received_from, status_msg[startpoint:endpoint]))
        else:
            self.message_sender.send_nowait("#:#message#:#%s: %s" % (received_from, str(msg.getBody())))

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
                    for user in roster.getItems():
                        if ((roster.getName(user) != None) and ((str(user)+'/xiff') not in self.alive_users)):
                            self.message_sender.send_nowait("#:#friendupdateoff#:#%s" % roster.getName(user))
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
            keepalive = datetime.now()
            client.sendInitPresence(requestRoster=1)
            pres = xmpp.Presence(show='chat')
            pres.setStatus(STATUS_MSG)
            client.send(pres)

            message_sender = msgutil.MessageSender(request)
            message_receiver = msgutil.MessageReceiver(request)

            incoming_thread = CheckMessages(client, message_sender)
            incoming_thread.setDaemon(True)
            incoming_thread.start()

            client.RegisterHandler('presence', incoming_thread.presence_update)
            client.RegisterHandler('message', incoming_thread.message_update)

            request.ws_stream.send_message(CONN_SUCCESS, binary=False)
            to_jid = None #jid for the user receiving the message
            while True:
                line = message_receiver.receive_nowait()
                if client.isConnected():    #Check connection on each loop
                    if line != None:
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
                    if (datetime.now() - keepalive).seconds > WEBSOCKET_TIMEOUT:
                        client.disconnect()
                        return
                else:
                    try:
                        request.ws_stream.send_message(CONN_ERROR, binary=False)
                    except:     #Don't crap out and leave a zombie process if the xmpp connection drops along with the websocket session
                        pass
                    return

                #Execute keep alive request regardless of the status of the xmpp connection
                if (str(line) == "Keep alive"):
                    keepalive = datetime.now()
                #Throttle message receiving otherwise the non-blocking state of the loop will cause it to execute as fast as possible
                time.sleep(RECEIVE_BUFFER)
        else:
            try:
                request.ws_stream.send_message(CONN_ERROR, binary=False)
            except:     #Don't crap out and leave a zombie process if the xmpp connection drops along with the websocket session
                pass
            return
    except IOError: #Something was causing apache to overload... Meh?
        return
