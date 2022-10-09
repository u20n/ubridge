import socket, json, threading, time

class irc_: # channel
    users = {}
    parrot = None 

    def __send(self, socket, message):
        socket.send(bytes(message, "utf-8"))

    def __form_m(self, mjson):
        r = ""
        if "message_reference" in mjson:
            r = mjson["referenced_message"]["author"]["username"]+": "
        r = r + (mjson["content"])
        return r
    
    def __parse_m(self, marray):
        user = marray[0].split('!')[0][1:]
        m = " ".join(marray[3:])[1:-2] # remove the leading ':' and trailing '\r\n' 
        # [TODO]: need to differentiate between dm and all
        self.bridge.push(self.channel, user, m)

    def __listen(self, user, socket):
        print(user) # DEBUG
        while True:
            buff = socket.recv(1024)
            m = str(buff, "utf-8").split(' ')
            print(m) # DEBUG 
            if m[0] == "PING":
                print("ping/pong") 
                self.__send(socket, "PONG %s\n" %(m[1]))
                continue
            if len(m) > 2 and m[1] == "PRIVMSG" and m[2] == user: 
                self.__parse_m(m) 
                continue
   
    def create_user(self, name, nick):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.connect((self.ip, self.port))
        self.__send(s, ("USER %s ubridge ubridge %s\n" % (name, name)))
        if nick is not name:
            time.sleep(0.2)
            self.__send(s, ("NICK %s\n" % nick))
        time.sleep(0.2)
        self.__send(s, ("JOIN %s\n" % self.channel)) 
        # start listening
        t = threading.Thread(target=self.__listen, args=(name, s))
        t.start()
        return s

    def push(self, name, msg): # we can deduce name, and reduce complexity here
        name = msg["author"]["username"]
        # make sure it's a plaintext message
        if int(msg["type"]) != 0:
            print(msg) # DEBUG
        assert(int(msg["type"] == 0))  
        if name not in self.users:
            self.users[name] = self.create_user(name, name)
            self.__send(self.users[name], ("PRIVMSG %s :%s\n" % (self.channel, self.__form_m(msg))))
        time.sleep(0.2)

    def __init__(self, ip, port, channel, bridge):
        self.ip = ip
        self.port = port
        self.channel = channel
        self.bridge = bridge
        # form parrot
        print(self.channel)
        self.parrot = self.create_user(self.channel, "ubridge")
