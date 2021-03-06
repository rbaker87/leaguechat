var socket = null;
var showTimeStamp = false;
var addressWs = "ws://pylol.com/leaguechat";
var invite_message = "Sorry, I cannot accept your game invite at this time. I am using the PyLoL chat client.";
var logBox = null;
var friendBox = null;
var friendRequestBox = null;
var gameBox = null;
var chatBox = null;
var messageBox = null;
var userBox = null;
var passBox = null;
var activeFriend = null;
var intervalID = null;
var newMessages = 0;
var pageTitle = 'PyLoL';
var prev_overlay = '';
var in_overlay = new Boolean(false);
var windowFocused = new Boolean(true);
var friendStatus = new Object();
var friendGame = new Object();
var friendTime = new Object();
var showTimeStamps = new Boolean(true);
var isconnected = new Boolean(false);

function sanitizeMsg(msg) {
    msg = msg.replace(/</g, "&lt;");
    msg = msg.replace(/>/g, "&gt;");
    return msg;
}

function urlify(text) {
    var urlRegex = /(([a-zA-Z]+:\/\/)?(([a-zA-Z0-9\-]+\.)+([a-z]{2}|aero|arpa|biz|com|coop|edu|gov|info|int|jobs|mil|museum|name|nato|net|org|pro|travel|local|internal))(:[0-9]{1,5})?(\/[a-zA-Z0-9_\-\.~]+)*(\/([a-zA-Z0-9_\-\.]*)(\?[a-zA-Z0-9+_\-\.%=&amp;]*)?)?(#[a-zA-Z0-9!$&'()*+.=-_~:@/?]*)?)(\s+|$)/g;
    return text.replace(urlRegex, function(url) {
        if ((url.indexOf("http://") == -1) && (url.indexOf("https://") == -1)) {
            return '<a href="http://' + url + '" target="_blank">' + url + '</a>';
        }
        else {
            return '<a href="' + url + '" target="_blank">' + url + '</a>';
        }
    })
}

function setGameTime(friendtime) {
    epoch_time = new Date() / 1000;
    friendtime = (epoch_time - friendtime) / 60;
    return Math.floor(friendtime);
}

function getTimeStamp() {
    d=new Date();
    t=d.toLocaleTimeString();
    return t;
}

function playSound(soundfile) {
    document.getElementById("dummy").innerHTML="<embed src=\""+soundfile+"\" hidden=\"true\" autostart=\"true\" loop=\"false\" />";
}

function keepAlive() {
    socket.send("Keep alive");
}

function getElementsByClassName(classname, node) {
    if(!node) node = document.getElementsByTagName("body")[0];
    var a = [];
    var re = new RegExp('\\b' + classname + '\\b');
    var els = node.getElementsByTagName("*");
    for(var i=0,j=els.length; i<j; i++)
        if(re.test(els[i].className))a.push(els[i]);
    return a;
}

$(window).focus(function() {
    document.title = pageTitle;
    newMessages = 0;
    windowFocused = true;
});
$(window).blur(function() {
    windowFocused = false;
});

function addToLog(log) {
    if (showTimeStamps == true) {
        logBox.innerHTML += "<"+getTimeStamp()+"> " + log + '<br>';
    }
    else {
        logBox.innerHTML += log + '<br>';
    }
    logBox.scrollTop = (logBox.scrollHeight - logBox.offsetHeight);
}

function addToFriendLog(log) {
    if (showTimeStamps == true) {
        friendRequestBox.innerHTML += "<"+getTimeStamp()+"> " + log + '<br>';
    }
    else {
        friendRequestBox.innerHTML += log + '<br>';
    }
    friendRequestBox.scrollTop = (friendRequestBox.scrollHeight - friendRequestBox.offsetHeight);
}

function addToGameLog(log) {
    if (showTimeStamps == true) {
        gameBox.innerHTML += "<"+getTimeStamp()+"> " + log + '<br>';
    }
    else {
        gameBox.innerHTML += log + '<br>';
    }
    gameBox.scrollTop = (gameBox.scrollHeight - gameBox.offsetHeight);
}

function addToChat(log, friend) {
    tempChatBox = document.getElementById(friend+'_chat');
    if (showTimeStamps == true) {
        tempChatBox.innerHTML += "<"+getTimeStamp()+"> " + urlify(log) + '<br>';
    }
    else {
        tempChatBox.innerHTML += log + '<br>';
    }
    tempChatBox.scrollTop = (tempChatBox.scrollHeight - tempChatBox.offsetHeight);
}

function setActiveFriend(friend) {
    if (activeFriend != null) {
        document.getElementById(activeFriend+'_chat').style.display = 'none';
    }
    if ((document.getElementById(friend).style.backgroundColor != 'rgb(238, 238, 238)') && (document.getElementById(friend).style.backgroundColor != 'rgb(204, 204, 204)') && (document.getElementById(friend).style.backgroundColor != '')){
        colorFade(friend, 'background', '00ccee', 'cccccc', 25, 30);
    }
    activeFriend = friend;
    var elements = new Array();
    elements = getElementsByClassName('friendentry').concat(getElementsByClassName('offlineentry'));
    for(i in elements) {
        elements[i].style.backgroundColor = '#eee';
    }
    document.getElementById(friend).style.backgroundColor = '#ccc';
    document.getElementById('active_friendheader').innerHTML = friend;
    if (document.getElementById(friend+'_chat') == null) {
        document.getElementById('friendholder').innerHTML += "<div id='"+friend+"_chat' class='chatwindow'></div>"; 
    }
    document.getElementById(friend+'_chat').style.display = 'block';
    chatBox = document.getElementById(friend+'_chat');
    chatBox.scrollTop = (chatBox.scrollHeight - chatBox.offsetHeight);
    document.getElementById('message').focus();
}

function updateFriends(log) {
    if ((friendStatus[log] != undefined) && (friendStatus[log] != '')) {
        friend_status = ' : ' + friendStatus[log];
    }
    else {
        friend_status = '';
    }
    if (friendGame[log] != undefined) {
        friend_game = friendGame[log];
    }
    else {
        friend_game = '';
    }

    friendBox.innerHTML += "<div class='friendentry' id='"+log+"' onmouseover='displayOverlay(\""+log+"\");' onmouseout='removeOverlay(\""+log+"\");' onclick='setActiveFriend(\""+log+"\");'>" + log + friend_status + '<br>' + friend_game + '</div>';
}

function displayOverlay(friend) {
    if (in_overlay == false) {
        prev_overlay = document.getElementById(friend).innerHTML;
    }
    if (friendGame[friend].indexOf("In Game as") != -1){
        document.getElementById(friend).innerHTML = "In game for " + setGameTime(friendTime[friend]) + " minutes<br><br>";
    }
    in_overlay = true;
}

function removeOverlay(friend) {
    if (in_overlay == true) {
        document.getElementById(friend).innerHTML = prev_overlay;
    }
    in_overlay = false;
}

function updateOffline(friend) {
    offlineBox.innerHTML += "<div class='offlineentry' id='"+friend+"' onclick='setActiveFriend(\""+friend+"\");'>" + friend + '<br>Offline</div>';
}

function clearFriends() {
  friendBox.innerHTML = '';
  offlineBox.innerHTML = '';
}

function send() {
  messageBox = document.getElementById('message');
  if (!socket) {
    addToLog('Not connected');
    isconnected = false;
    document.getElementById('logButton').style.background = "url('/media/login.png') no-repeat top left";
    clearFriends();
    return;
  }

  if (messageBox.value != '') {
      socket.send("#:#outmessage#:# #:#" + activeFriend + "#:# " + messageBox.value);
      out_msg = sanitizeMsg(messageBox.value);
      addToChat('<b>'+userBox.value+'</b>' + ': ' + out_msg, activeFriend);
      messageBox.value = '';
  }
}

function connect() {
  if (isconnected == false) {
      if ('WebSocket' in window) {
        socket = new WebSocket(addressWs);
      } else if ('MozWebSocket' in window) {
        socket = new MozWebSocket(addressWs);
      } else {
        return;
      }

      socket.onopen = function () {
        document.getElementById('logButton').style.background = "url('/media/logout.png') no-repeat top left";
        isconnected = true;
        document.getElementById('message').focus();
        socket.binaryType = 'blob';
        socket.send('username' + userBox.value);
        socket.send('password' + passBox.value);
        intervalID = window.setInterval(keepAlive, 10000);
      };
      socket.onmessage = function (event) {
        if (event.data.indexOf("#:#clearfriends#:#") != -1) {
            clearFriends();
        }
        if (event.data.indexOf("#:#error#:#") != -1) {
            addToLog(event.data.slice(11));
        }
        if (event.data.indexOf("#:#warning#:#") != -1) {
            addToLog(event.data.slice(13));
        }
        if (event.data.indexOf("#:#message#:#") != -1) {
            if (activeFriend == null) {
                setActiveFriend(event.data.slice(13,event.data.indexOf(':', 13)))
            }
            friend = event.data.slice(13,event.data.indexOf(':', 13));
            if (document.getElementById(friend+'_chat') == null) {
                document.getElementById('friendholder').innerHTML += "<div id='"+friend+"_chat' class='chatwindow'></div>"; 
                document.getElementById(friend+'_chat').style.display = 'none';
            }

            addToChat('<b>'+event.data.slice(13, event.data.indexOf(':', 13))+'</b>'+sanitizeMsg(event.data.slice(event.data.indexOf(':', 13))), friend);

            playSound('./media/pm_receive.mp3');
            if (activeFriend != friend) {
                colorFade(friend, 'background', 'eeeeee', '00ccee', 25, 30);
            }
            if (windowFocused == false) {
                newMessages += 1;
                document.title = pageTitle + ' (' + newMessages + ')';
            }
        }
        if (event.data.indexOf("#:#statusupdate#:#") != -1) {
            friend = event.data.slice(18,event.data.indexOf(':', 18));
            oldStatus = '';
            if (friendStatus[friend] != undefined) {
                oldStatus = friendStatus[friend];
            }
            friendStatus[friend] = event.data.slice(event.data.indexOf(':', 18)+1);
            if (oldStatus != friendStatus[friend]) {
                addToLog(friend + " set status to '" + sanitizeMsg(friendStatus[friend]) + "'");
            }
            if (friendStatus[friend].length != 0){
                document.getElementById(friend).innerHTML = friend + " : " + friendStatus[friend];
            }
            else {
                document.getElementById(friend).innerHTML = friend;
            }
        }
        if (event.data.indexOf("#:#gameupdate#:#") != -1) {
            friend = event.data.slice(16,event.data.indexOf(':', 16));
            oldGame = '';
            if (friendGame[friend] != undefined) {
                oldGame = friendGame[friend];
            }
            friendGame[friend] = event.data.slice(event.data.indexOf(':', 16)+1);
            if (oldGame != friendGame[friend]) {
                addToLog(friend + " is now " + sanitizeMsg(friendGame[friend]));
            }
            if (friendStatus[friend].length != 0){
                document.getElementById(friend).innerHTML = friend + " : " + friendStatus[friend] + "<br>" + friendGame[friend];
            }
            else {
                document.getElementById(friend).innerHTML = friend + "<br>" + friendGame[friend];
            }
        }
        if (event.data.indexOf("#:#gametimeupdate#:#") != -1) {
            friend = event.data.slice(20,event.data.indexOf(':', 20));
            friendTime[friend] = event.data.slice(event.data.indexOf(':', 20)+1);
            friendTime[friend] = parseInt(friendTime[friend]);
        }
        if (event.data.indexOf("#:#gameinvite#:#") != -1) {
            friend = event.data.slice(16,event.data.indexOf(':', 16));
            invite_label = event.data.slice(event.data.indexOf(':', 18)+1);
            addToGameLog(friend + " : " + invite_label);
            playSound('./media/buddy_invite.mp3');
            socket.send("#:#outmessage#:# #:#" + friend + "#:# " + invite_message);
        }
        if (event.data.indexOf("#:#friendupdate#:#") != -1) {
            updateFriends(event.data.slice(18));
        }
        if (event.data.indexOf("#:#friendupdateoff#:#") != -1) {
            updateOffline(event.data.slice(21));
        }
        if (event.data.indexOf("#:#removefriend#:#") != -1) {
            friend = event.data.slice(18);
            friendGame[friend] = "Offline";
            addToLog(friend + " is now Offline");
        }
      };
      socket.onerror = function () {
        document.getElementById('logButton').style.background = "url('/media/login.png') no-repeat top left";
        document.getElementById('username').focus();
        isconnected = false;
        clearFriends();
        addToLog('Error');
      };
      socket.onclose = function (event) {
        document.getElementById('logButton').style.background = "url('/media/login.png') no-repeat top left";
        document.getElementById('username').focus();
        isconnected = false;
        clearFriends();
        addToLog('Session closed...');
        socket.send("Kill session");
      };
    }
    else {
        document.getElementById('logButton').style.background = "url('/media/login.png') no-repeat top left";
        isconnected = false;
        clearFriends();
        socket.send("Kill session");
        socket.close();
    }
}

window.onbeforeunload = function () {
    socket.send("Kill session");
    socket.close();
}

function init() {
  var scheme = window.location.protocol == 'https:' ? 'wss://' : 'ws://';
  var defaultAddress = scheme + window.location.host + '/leaguechat';

  logBox = document.getElementById('log');
  friendBox = document.getElementById('friends');
  offlineBox = document.getElementById('offlinefriends');
  friendRequestBox = document.getElementById('friendrequests');
  gameBox = document.getElementById('gameinvites');
  messageBox = document.getElementById('message');
  userBox = document.getElementById('username');
  passBox = document.getElementById('password');
  document.getElementById('username').focus();

  addressWs = defaultAddress;

  if ('MozWebSocket' in window) {
    addToLog('Use MozWebSocket');
  } else if (!('WebSocket' in window)) {
    addToLog('WebSocket is not available');
  }
}
