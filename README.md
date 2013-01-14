LeagueChat
=============

Intelligently interact with the League of Legends jaber network to send/receive messages without the Riot game client.

Usage (terminal client):
    
    ***NOT RECOMMENDED***
    python main.py username password

Usage (server):

    Move localizations to your mod_pywebsocket install directory.
    Move leaguechat_wsh.py to your websocket handlers location.
    Set reqtimeout.conf under your Apache mods-enabled directory to accept a minimum data rate of 1/Byte per second and wait more than 10 seconds between pulses. The client will send the message "Keep alive" once every 10 seconds on top of all data being transfered regularly.
    Restart Apache.

Requirements:

    xmpppy

    mod_pywebsocket
