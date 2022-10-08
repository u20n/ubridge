import json, requests, time, socket, threading

class irc_: # channel
    users = {}
    __last_m = None
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
        if m != self.__last_m:
            self.__last_m = m # so we don't have a bunch of parrots 
            self.bridge.push(self.channel, user, m)

    def __listen(self, user, socket):
        while True:
            buff = socket.recv(1024)
            m = str(buff, "utf-8").split(' ')
            if m[0].split("!")[-1].split("_")[-1].split("@")[0] == "ubridge":
                # ignore bridged messages
                continue
            if m[0] == "PING":
                print("ping/pong") 
                self.__send(socket, "PONG %s\n" %(m[1]))
                continue
            if len(m) > 2 and m[1] == "PRIVMSG" and m[2] == self.channel: 
                self.__parse_m(m) 
                continue
   
    def add_user(self, name, nick):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.connect((self.ip, self.port))
        self.__send(s, ("USER %s_ubridge ubridge ubridge %s_ubridge\n" % (name, name)))
        self.__send(s, ("NICK %s\n" % nick))
        time.sleep(0.2)
        self.__send(s, ("JOIN %s\n" % self.channel)) 
        self.users[name] = s
        # start listening
        t = threading.Thread(target=self.__listen, args=(name, s))
        t.start()

    def push(self, name, msg): # we can deduce name, and reduce complexity here
        name = msg["author"]["username"]
        # make sure it's a plaintext message
        assert(int(msg["type"] == 0))  
        if name not in self.users:
            self.add_user(name, name) #[TODO] getting nicks is painful
        
        self.__send(self.users[name], ("PRIVMSG %s :%s\n" % (self.channel, self.__form_m(msg))))
        time.sleep(0.2)

    def __init__(self, ip, port, channel, bridge):
        self.ip = ip
        self.port = port
        self.channel = channel
        self.bridge = bridge

class discord_: # channel
    lm_id = None
    channel_id = None
    w_map = {}
    def __listen(self):
        while True:
            stub = None
            if self.lm_id:
                stub = {"after": self.lm_id} 
            r = requests.get(
                "https://discord.com/api/channels/%s/messages"%(self.channel_id),
                headers={"Authorization": "Bot %s"%(self.token)}, 
                params=stub
            )
            assert(r.status_code == 200)
            msg_array = json.loads(str(r.content, "utf-8"))
            # update last message
            if len(msg_array):
                # discord does latest-first
                self.lm_id = msg_array[0]["id"]
                for msg in reversed(msg_array):
                    if "webhook_id" not in msg: # ignore our dummy accounts
                        self.bridge.push(self.channel_id, None, msg)
            time.sleep(2) # CONFIG: refresh
    
    def __form_w_url(self, wjson):
        return "https://discord.com/api/webhooks/%s/%s" % (wjson["id"], wjson["token"])

    def push(self, name, msg):
        # check if we have any webhooks for this user
        if not name in self.w_map:
            # check with discord for channel webhooks
            r = requests.get(
                "https://discord.com/api/channels/%s/webhooks"%(self.channel_id),
                headers={"Authorization": "Bot %s"%(self.token)}
            )
            existing_w = json.loads(str(r.content, "utf-8"))
            assert(r.status_code == 200)
            
            found_w = False
            for w in existing_w:
                if w["name"] == name:
                    found_w = True
                    self.w_map[name] = self.__form_w_url(w)
                if w["name"] not in self.w_map: # garbage collect [!] (this will wipe other bot's webhooks)
                    r = requests.delete(self.__form_w_url(w))


            if not found_w: # if none for this user, make one
                r = requests.post(
                    "https://discord.com/api/channels/%s/webhooks"%(self.channel_id),
                    headers={
                        "Authorization": "Bot %s"%(self.token),
                        "Content-Type": "application/json"
                    },
                    data=json.dumps({"name": name})
                ) 
                rjson = json.loads(str(r.content, "utf-8"))
                self.w_map[name] = self.__form_w_url(rjson)
        # push message
        r = requests.post(
            self.w_map[name],
            data={"content": msg, "username": name}
        ) 

    def __init__(self, token, channel_id, bridge):
        self.token = token
        self.channel_id = channel_id
        self.bridge = bridge 
        t = threading.Thread(target=self.__listen)
        t.start()

class bridge_: # 1:1 bridge:server
    c_map = {}
    def push(self, channel, name, msg): 
        if channel in self.c_map:
            self.c_map[channel].push(name, msg)
    
    def load(self, channel_map):
        for [i, d] in channel_map:
            # spawn new irc_ and discord_ instances 
            self.c_map[i] = discord_(self.token, d, self)
            self.c_map[d] = irc_(self.ip, self.port, i, self)
            print(i, "<--> (discord)", d) 

    def __init__(self, ip, port, token):
        self.ip = ip
        self.port = port
        self.token = token

def config():
    cfg = json.load(open("config.json")) 
    b = bridge_(cfg["server"], cfg["port"], cfg["token"]) # create bridge
    b.load(cfg["channels"].items()) # load channel mapping
 
if __name__ == "__main__":
    bridge = config()
