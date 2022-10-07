import types, json, requests, time, socket, threading

class irc_:
    users = {}
    def __send(self, socket, message):
        socket.send(bytes(message, "utf-8"))

    def new_user(self, name, nick):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.connect(("127.0.0.1", 6667)) # self.ip and self.port are breaking :( TODO
        self.__send(s, ("USER %s_ubridge ubridge ubridge %s_ubridge\n" % (name, name)))
        self.__send(s, ("NICK %s\n" % nick))
        time.sleep(0.5)
        self.__send(s, ("JOIN #%s\n" % self.channel)) 
        self.users[name] = s
        # start listening
        t = threading.Thread(target=self.__read, args=(name, s))
        t.start()
    
    def form(self, mjson :json):
        r = ""
        if "message_reference" in mjson:
            r = mjson["referenced_message"]["author"]["username"]+": "
        r = r + (mjson["content"])
        return r

    def send(self, msg_array):
        for msg in msg_array:
            name = msg["author"]["username"] 
            # make sure it's a plaintext message
            assert(int(msg["type"] == 0)) 
            print(msg) # DEBUG
            if name not in self.users:
                self.new_user(name, name) #[TODO] getting nicks are painful
            
            self.__send(self.users[name], ("PRIVMSG #%s :%s\n" % (self.channel, self.form(msg))))
            time.sleep(1)

    def __read(self, user, socket):
        while True:
            buff = socket.recv(1024)
            m = str(buff, "utf-8").split(' ')
            # ignore bridged messages 
            if m[0].split("!")[-1].split("_")[-1].split("@")[0] == "ubridge":
                print("Ignoring echo")
                continue
            if m[0] == "PING":
                print("Ping/Pong") 
                self.__send(socket, "PONG %s\n" %(m[1]))
                continue
            if m[1] == "PRIVMSG": #[TODO]
                print("Recived private message -", m[2], m) # DEBUG
                continue
            print(m) # DEBUG

    def __init__(self, ip, port, channel):
        self.ip = ip
        self.port = port
        self.channel = channel

class Mirror: 
    def __init__(self, irc :str, d :str):
        self.irc = irc
        self.discord = d
        self.last_message = None 
 
class API:
    m_map = {}

    def create_webhook(self, c_id, u_name):
        r = requests.post(
            "https://discord.com/api/channels/%s/webhooks"%(c_id),
            headers={"Authorization": "Bot %s"%(self.token)},
            params={"name": u_name}
        )
        print(r) #DEBUG
    

    def pull(self, c_id :str):
        stub = None
        if self.m_map[c_id].last_message:
            stub = {"after": self.m_map[c_id].last_message}
        
        r = requests.get(
            "https://discord.com/api/channels/%s/messages"%(c_id),
            headers={"Authorization": "Bot %s"%(self.token)}, 
            params=stub
        )
        msg_array = json.loads(str(r.content, "utf-8"))
        # update last message
        if len(msg_array):
            self.m_map[c_id].last_message = msg_array[0]["id"]             
            self.m_map[c_id].irc.send(reversed(msg_array)) # discord does latest-first

        print("State", r.status_code) #DEBUG
    
    def set_host(self, ip, port):
        self.ip = ip
        self.port = port

    def load(self, id_map):
        for [i, d] in id_map.items():
            self.m_map[d] = Mirror(irc_(self.ip, self.port, i), d)

    def run(self):
        while True:
            for [c, m] in self.m_map.items():
                self.pull(c)
            time.sleep(self.refresh_interval)

    def connect(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
    

def config(api :API):
    cfg = json.load(open("config.json"))
    
    # give token
    api.token = cfg["token"]

    # load address(es)
    api.set_host(cfg["server"], cfg["port"])

    # get channel(s) mapping
    for [i, d] in cfg["channels"].items():
        print("#"+i, "<--> (Discord)", d)
    
    # load channels
    api.load(cfg["channels"])

    # set refresh
    api.refresh_interval = cfg["refresh"]
    
if __name__ == "__main__":
    _api = API()
    config(_api)
    _api.run()
