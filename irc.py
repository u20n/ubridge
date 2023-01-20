import socket, json, threading, time

class irc_: # channel
    users = {}
    parrot = None 

    def __send(self, socket, message):
        socket.send(bytes(message, "utf-8"))
        time.sleep(0.2)

    def __form_m(self, mjson):
        r = ""
        if "message_reference" in mjson:
            r = mjson["referenced_message"]["author"]["username"]+": "
        r = r + (mjson["content"])
        return r
    
    def __parse_m(self, marray):
        user = marray[0].split('!')[0][1:]
        # TODO: do mentions here
        m = " ".join(marray[3:])[1:-2] # remove the leading ':' and trailing '\r\n' 
        return m, user

    def __parse_cm(self, marray): # parse channel message (e.g. parrot only)
        m, user = self.__parse_m(marray)
        self.bridge.push(self.channel, user, m)
    
    def __parse_dm(self, marray):
        pass # TODO: dms (on discord side)

    def __listen(self, user, socket):
        while True:
            buff = socket.recv(1024)
            m = str(buff, "utf-8").split(' ')
            print(m) # DEBUG
            if m[0] == '':
                print("received zero length packet, assuming connection closed")
                self.users[user] = None
                socket.close()
                return
            if m[0] == "PING": 
                self.__send(socket, ("PONG %s\n" % m[1]) )
                continue
            if len(m) > 2 and m[1] == "PRIVMSG" and m[0].split('!')[0][1:] not in self.users:
                if m[2] == user:
                    self.__parse_dm(m) 
                    continue
                elif m[2] == self.channel and user == "ubridge":
                    self.__parse_cm(m)
                    continue
   
    def create_user(self, name):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.connect((self.ip, self.port))
        self.__send(s, ("NICK %s\n" % name))
        self.__send(s, ("USER %s 0 * :%s\n" % (name, name))) 
        self.__send(s, ("JOIN %s\n" % self.channel))  
        # start listening
        t = threading.Thread(target=self.__listen, args=(name, s))
        t.start()
        return s

    def push(self, name, msg): # we can deduce name, and reduce complexity here
        # plaintext only
        if int(msg["type"]) != 0:
               print("illegal message type: %s, ignoring" % msg["type"])
               return
        name = msg["author"]["username"] 
        if name not in self.users: 
            self.users[name] = self.create_user(name)  
        self.__send(self.users[name], ("PRIVMSG %s :%s\n" % (self.channel, self.__form_m(msg)))) 

    def __init__(self, ip, port, channel, bridge):
        self.ip = ip
        self.port = port
        self.channel = channel
        self.bridge = bridge
        # form parrot
        self.parrot = self.create_user("ubridge")
