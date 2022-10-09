import json, requests, time, threading

burl = lambda content: "https://discord.com/api/%s" % (content)
wurl = lambda id, token: burl("webhooks/%s/%s" % (id, token))
auth = lambda token: {"Authorization": "Bot %s"% (token)}

def rstat(r):
    if (r.status_code and str(r.status_code)[0] != "2"):
        print("[!] (%s) %s" %(r.status_code, r.content))

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
                burl(("channels/%s/messages"%(self.channel_id))),
                headers=auth(self.token), 
                params=stub
            )
            rstat(r)
            msg_array = json.loads(str(r.content, "utf-8")) 
            if len(msg_array):
                # update last message
                self.lm_id = self.bridge.last(self.channel_id, msg_array[0]["id"])
                for msg in reversed(msg_array): # discord does latest-first
                    if "webhook_id" not in msg: # ignore our dummy accounts
                        self.bridge.push(self.channel_id, None, msg)
            time.sleep(2) # CONFIG: refresh
  
    def push(self, name, msg):
        # check if we have any webhooks for this user
        if not name in self.w_map:
            # check with discord for channel webhooks
            r = requests.get(
                burl(("channels/%s/webhooks"%(self.channel_id))),
                headers=auth(self.token)
            )
            rstat(r)
            existing_w = json.loads(str(r.content, "utf-8"))
            
            found_w = False
            for w in existing_w:
                if w["name"] == name:
                    found_w = True
                    self.w_map[name] = wurl(w["id"], w["token"])
                if w["name"] not in self.w_map: # garbage collect [!] (this will wipe other bot's webhooks)
                    r = requests.delete(wurl(w["id"], w["token"]))

            if not found_w: # if none for this user, make one
                r = requests.post(
                    burl(("channels/%s/webhooks"%(self.channel_id))),
                    headers={
                        "Authorization": "Bot %s"%(self.token),
                        "Content-Type": "application/json"
                    },
                    data=json.dumps({"name": name})
                )
                rstat(r)
                rjson = json.loads(str(r.content, "utf-8"))
                self.w_map[name] = wurl(rjson["id"], rjson["token"])
        # push message
        r = requests.post(
            self.w_map[name],
            data={"content": msg, "username": name}
        )
        rstat(r)

    def __init__(self, token, channel_id, bridge):
        self.token = token
        self.channel_id = channel_id
        self.bridge = bridge
        self.lm_id = self.bridge.last(self.channel_id)
        t = threading.Thread(target=self.__listen)
        t.start()
