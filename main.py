import time
import asyncio
import websocket
import json
import random
import threading

statuses = ["online", "dnd", "idle"]  # invisible, offline


def recv_nowait(ws):
    try:
        return ws.messages.get_nowait()
    except asyncio.queues.QueueEmpty:
        pass

class user_connection:
    def __init__(self, token, presence=None, browser=None, heartbeat=False):
        self.token = token

        self.presence = presence
        if self.presence is None:
            self.presence = json.loads(random.choice(presence_data))

        self.browser = browser
        if self.browser is None:
            self.browser = random.choice(["Chrome","Firefox","Discord iOS"])

        for i in range(len(self.presence["activities"])):
            new_created_at = random.randint(int(time.time()*1000) - 5 * 60 * 60 * 1000, int(time.time()*1000))
            new_start = random.randint(new_created_at, int(time.time()*1000))
            if "created_at" in self.presence["activities"][i]:
                if self.presence["activities"][i]["created_at"] > time.time() - 5 * 60 * 60 * 1000:
                    self.presence["activities"][i]["created_at"] = new_created_at
            if "timestamps" in self.presence["activities"][i]:
                if "created_at" in self.presence["activities"][i]["timestamps"]:
                    if self.presence["activities"][i]["timestamps"]["created_at"] > time.time() - 5 * 60 * 60 * 1000:
                        self.presence["activities"][i]["timestamps"]["created_at"] = new_created_at
                if "start" in self.presence["activities"][i]["timestamps"]:
                    if "end" in self.presence["activities"][i]["timestamps"]:
                        # start | end
                        difference = int(self.presence["activities"][i]["timestamps"]["end"] - self.presence["activities"][i]["timestamps"]["start"])
                        if self.presence["activities"][i]["timestamps"]["end"] > time.time():
                            new_start = random.randint(int(time.time()*1000) - difference, int(time.time()*1000))
                            self.presence["activities"][i]["timestamps"]["start"] = new_start
                            self.presence["activities"][i]["timestamps"]["end"] = new_start + difference
                    else:
                        # start
                        if self.presence["activities"][i]["timestamps"]["start"] > time.time() - 5 * 60 * 60 * 1000:
                            self.presence["activities"][i]["timestamps"]["start"] = new_start
            if "party" in self.presence["activities"][i]:
                if "created_at" in self.presence["activities"][i]["party"]:
                    if self.presence["activities"][i]["party"]["created_at"] > time.time() - 5 * 60 * 60 * 1000:
                        self.presence["activities"][i]["party"]["created_at"] = new_created_at
                if "start" in self.presence["activities"][i]["party"]:
                    if "end" in self.presence["activities"][i]["party"]:
                        # start | end
                        difference = int(self.presence["activities"][i]["party"]["end"] - self.presence["activities"][i]["party"]["start"])
                        if self.presence["activities"][i]["party"]["end"] > time.time():
                            new_start = random.randint(int(time.time()*1000) - difference, int(time.time()*1000))
                            self.presence["activities"][i]["party"]["start"] = new_start
                            self.presence["activities"][i]["party"]["end"] = new_start + difference
                    else:
                        # start
                        if self.presence["activities"][i]["party"]["start"] > time.time() - 5 * 60 * 60 * 1000:
                            self.presence["activities"][i]["party"]["start"] = new_start
        
        self.running = True
        
        self.ws = websocket.WebSocket()
        self.ws.connect("wss://gateway.discord.gg/?v=6&encoding=json")

        result = json.loads(self.ws.recv())
        self.latest_sequence_number = result["s"]
        self.heartbeat_interval = result["d"]["heartbeat_interval"] / 1000
        self.next_heartbeat = time.time() + self.heartbeat_interval

        presence_str = '{"status":"'+str(self.presence["status"])+'","since":0,"activities":'+json.dumps(self.presence["activities"])+',"afk":false}'
        message = '{"op":2,"d":{"token":"'+self.token+'","capabilities":509,"properties":{"os":"Windows","browser":"'+self.browser+'","device":"","system_locale":"en-US","browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36","browser_version":"100.0.4896.75","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":125308,"client_event_source":null},"presence":'+presence_str+',"compress":false,"client_state":{"guild_hashes":{},"highest_last_message_id":"0","read_state_version":0,"user_guild_settings_version":-1,"user_settings_version":-1}}}'
        self.ws.send(message)

        result = json.loads(self.ws.recv())
        self.user = [user["username"] + "#" + user["discriminator"] for user in result["d"]["users"]]
        self.latest_sequence_number = result["s"]

        message = '{"op":4,"d":{"guild_id":null,"channel_id":null,"self_mute":true,"self_deaf":false,"self_video":false}}'
        self.ws.send(message)

        # self.set_status(status)

        if heartbeat:
            self.heartbeat_thread = threading.Thread(target=self.heartbeats)
            self.heartbeat_thread.start()

        # self.reciever_thread = threading.Thread(target=self.reciever)
        # self.reciever_thread.start()


    def heartbeat(self):
        try:
            message = '{"op":1,"d":'+str(self.latest_sequence_number)+'}'
            self.ws.send(message)
            self.next_heartbeat = time.time() + self.heartbeat_interval

            return True
        except:
            return False

    def heartbeats(self):
        while self.running:
            current_time = time.time()
            if current_time >= self.next_heartbeat:
                self.heartbeat()
            else:
                time.sleep(self.next_heartbeat - current_time)

    def reciever(self):
        while self.running:
            try:
                result = json.loads(self.ws.recv())
            except:
                self.close()
                return

            self.latest_sequence_number = result["s"]
            # print(result)

    def set_status(self, status):
        try:
            self.status = status
            message = '{"op":3,"d":{"status":"'+status+'","since":0,"activities":[],"afk":false}}'
            self.ws.send(message)
        except:
            pass

    def close(self):
        self.running = False
        try:
            self.ws.close()
        except:
            pass



def create_connection(connections, token, presence=None, browser=None, description="new user"):
    while True:
        try:
            connection = user_connection(token, presence, browser)
            break
        except:
            pass
    connections.append(connection)
    print(description + ": " + str(connection.user))

def create_connections(connections, tokens):
    print(333333333333)
    for token in tokens:
        while True:
            try:
                threading.Thread(target=create_connection, args=(connections, token)).start()
            except:
                print("no more threads")
                time.sleep(1)
            else:
                break


def heartbeat_batch(tokens):
    connections = []
    threading.Thread(target=create_connections, args=(connections, tokens)).start()

    while True:
        print(len(connections))
        for connection in connections:
            if time.time() >= connection.next_heartbeat:
                if connection.heartbeat():
                    print("heartbeat: " + str(connection.user))
                else:
                    connections.remove(connection)
                    print("closed: " + str(connection.user))



# while and len(tokens):
#     tokens_split, tokens = tokens[:100], tokens[100:]
#     threading.Thread(target=heartbeat_batch, args=(tokens_split,)).start()

# heartbeat_batch(tokens)


def reset_connection(connections, connection):
    token = connection.token
    presence = connection.presence
    browser = connection.browser
    
    create_connection(connections, token, presence, browser, "reset")

    connection.close()


def main_batch(tokens):
    connections = []
    threading.Thread(target=create_connections, args=(connections, tokens)).start()

    while time.time() < 1663797638:
        for connection in connections:
            if time.time() >= connection.next_heartbeat - 5:
                connections.remove(connection)
                threading.Thread(target=reset_connection, args=(connections, connection)).start()


print(0000000000)

presence_data = open("presences.txt", "r", encoding="utf8").read().split("\n")
print("a")
while "" in presence_data: presence_data.pop(presence_data.index(""))
print("b")
# presences = [{"status": json.loads(d)["status"], "activities": json.loads(d)["activities"]} for d in presence_data]
print("c")

token_data = open("tokens.txt", "r", encoding="utf8").read().split("\n")
print("d")
while "" in token_data: token_data.pop(token_data.index(""))
print("e")
tokens = [d.split(":")[3] for d in token_data if d.count(":") > 2 and d.endswith("True")]
print("f")
random.shuffle(tokens)
print("g")


print(11111111111)
main_batch(tokens)
print(22222222222)