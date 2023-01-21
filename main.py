import json

import irc, discord

class bridge_: # 1:1 bridge:server
    c_map = {}
    def last(self, channel_id, new_id=None): # returns and takes an id
        j = json.load(open("last.log.json"))
        if new_id or channel_id not in j:
            j[channel_id] = new_id

        with open("last.log.json", 'w') as o:
            o.write(json.dumps(j, indent=4))
        return j[channel_id]

    def push(self, channel, name, msg): 
        if channel in self.c_map:
            self.c_map[channel].push(name, msg)
    
    def load(self, channel_map):
        for [i, d] in channel_map:
            # spawn new irc_ and discord_ instances 
            self.c_map[i] = discord.discord_(self.cfg["token"], d, self)
            self.c_map[d] = irc.irc_(self.cfg["server"], self.cfg["port"], i, self)
            print("(irc)", i, "<--> (discord)", d) 

    def __init__(self, cfg):
        self.cfg = cfg
        
def config():
    cfg = json.load(open("config.json")) 
    b = bridge_(cfg) # create bridge
    b.load(cfg["channels"].items()) # load channel mapping
 
if __name__ == "__main__":
    bridge = config()
