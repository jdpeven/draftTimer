import json
from datetime import datetime, timedelta

current_draft_order = 0

class Player():
    def __init__(self, name):
        global current_draft_order
        self.name = name
        self.draft_order = current_draft_order + 1
        self.timestamps = []
        self.delays = []
        self.total_delay = timedelta(seconds=0)
        current_draft_order += 1

    def add_timestamp(self, timestamp):
        self.timestamps.append(timestamp)

    def add_delay(self, delay):
        self.delays.append(delay)
        self.total_delay = self.total_delay + delay
    
    def __str__(self):
        return '{0}: {1}'.format(self.name, self.timestamps)

    def __lt__(self, object):
        return self.total_delay < object.total_delay

players = {}
previous_draft_time = None

def get_data(filename="./discordLog.json"):
    f = open(filename, "r")
    data = json.loads(f.read())
    f.close()
    return data

def get_messages(data: dict):
    return data["messages"]

def get_current_drafter(message: dict):
    both_player_names = [mentions["name"] for mentions in message["mentions"]]
    #print(both_player_names)
    # First or last person in draft will only have 1 mention since they're also next
    if len(both_player_names) == 1:
        return both_player_names[0]

    # The order in the mentions in randomized, so we have to see who's name came up first in the content
    first_player_index = message["content"].find(both_player_names[0])
    second_player_index = message["content"].find(both_player_names[1])
    current_drafter = both_player_names[0] if first_player_index < second_player_index else both_player_names[1]
    return current_drafter

def remove_decimal_from_timestamp(timestamp: str):
    # input: "2021-06-12T02:01:14.424+00:00"
    # output: "2021-06-12T02:01:14+00:00"
    dot_index = timestamp.find(".")
    plus_index = timestamp.find("+")
    end_index = len(timestamp)
    new_timestamp = timestamp[0: dot_index] + timestamp[plus_index: end_index]
    #print(new_timestamp)
    return new_timestamp

def convert_timestamp(timestamp: str):
    # "2021-06-12T02:01:14.424+00:00"
    iso_format = remove_decimal_from_timestamp(timestamp)
    d = datetime.fromisoformat(iso_format)
    return d

def add_timestamp_to_drafter(message: dict, player_name: str):
    if player_name in players.keys():
        player = players[player_name]
    else:
        player = Player(player_name)
        players[player_name] = player
    #print ("Adding " + message["timestamp"] + " to drafter " + player_name)
    timestamp_str = message["timestamp"]

    player.add_timestamp(convert_timestamp(timestamp_str))

def add_delay_to_drafter(drafter: str):
    global previous_draft_time
    player = players.get(drafter)
    current_draft_time = player.timestamps[-1]
    if previous_draft_time == None:
        previous_draft_time = current_draft_time
    else:
        diff = current_draft_time - previous_draft_time
        player.add_delay(diff)
        previous_draft_time = current_draft_time
        

def parse_message(message: dict):
    drafter = get_current_drafter(message)
    add_timestamp_to_drafter(message, drafter)
    add_delay_to_drafter(drafter)

def compare_top_bottom(players_list: list, drop_slowest_n=0):
    top_list = []
    bottom_list = []
    for player in players_list:
        if player.draft_order <= 10:
            top_list.append(player)
        else:
            bottom_list.append(player)
    top_list.sort()
    bottom_list.sort()
    for _ in range(0, drop_slowest_n):
        top_list.pop()
        bottom_list.pop()

    # There's some fancy one-liner in python to do this but I'm tired and lazy
    top_total = timedelta(seconds=0)
    for t_player in top_list:
        top_total += t_player.total_delay
    bot_total = timedelta(seconds=0)
    for b_player in bottom_list:
        bot_total += b_player.total_delay
    
    top_avg = top_total/len(top_list)
    bot_avg = bot_total/len(bottom_list)

    print("Top players: {0}, total: {1}, avg: {2} \nBottom players: {3}, total: {4}, avg: {5}".format(
        len(top_list),
        top_total, 
        top_avg, 
        len(bottom_list),
        bot_total, 
        bot_avg))

def print_info():
    players_list = [player for player in players.values()]
    players_list.sort()
    players_list.reverse()
    for player in players_list:
        #print("{0}({1}): {2}, {3}".format(player.name, player.draft_order, player.total_delay, [str(delta) for delta in player.delays]))
        print("{0}({1}): {2}".format(player.name, player.draft_order, player.total_delay))
    compare_top_bottom(players_list)
    
def main():
    data = get_data()
    messages = get_messages(data)
    for message in messages:
        parse_message(message)

    print_info()

if __name__ == "__main__":
    main()
    #remove_decimal_from_timestamp("2021-06-12T02:01:14.424+00:00")