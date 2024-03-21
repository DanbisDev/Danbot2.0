import random
from collections import defaultdict
import pprint

import discord


def debug_print(obj):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)


class CollectionTile:
    def __init__(self, name: str, points: float, recurrence: int, collection: list[str]):
        self.name = name
        self.points = points
        self.recurrence = recurrence
        self.collection = collection
        self.completion_count = defaultdict(int)
        self.team_drops = defaultdict(lambda: defaultdict(int))

    def is_completed(self, drop_name, player):
        print("Checking copmletion on " + str(drop_name))
        self.team_drops[player.team.name.lower()][drop_name.lower()] = (
                self.team_drops[player.team.name.lower()][drop_name.lower()] + 1)

        for sub_collection in self.collection:
            found = 0
            for item in sub_collection.split('/'):
                if self.team_drops[player.team.name.lower()][item.lower()] > 0:
                    found = found + self.team_drops[player.team.name.lower()][item.lower()]
            if found <= self.completion_count[player.team.name.lower()]:
                return False
        return True


class NicheTile:
    def __init__(self, name: str, points: float, recurrence: int):
        self.name = name
        self.points = points
        self.recurrence = recurrence
        self.completion_count = defaultdict(int)


class TileRequest:
    def __init__(self, tile, image_url: str, team, player):
        self.tile = tile
        self.image_url = image_url
        self.team = team
        self.player = player


class DropTile:
    def __init__(self, name: str, drops: list[str], points: float, recurrence: int):
        self.name = name
        self.drops = drops
        self.points = points
        self.recurrence = recurrence
        self.completion_count = defaultdict(int)

    def is_completed(self, drop_name, player):
        return drop_name.lower() in [drop.lower() for drop in self.drops]


class KcTile:
    def __init__(self, name: str, boss_name: str, points: float, recurrence: int, kc_required: int):
        self.name = name
        self.points = points
        self.boss_name = boss_name
        self.recurrence = recurrence
        self.kc_required = kc_required
        self.completion_count = defaultdict(int)

    def is_completed(self, team):
        return team.killcount[self.boss_name.lower()] >= self.kc_required + self.kc_required * self.completion_count[
            team.name.lower()]


class Player:
    def __init__(self, name: str, team):
        self.name = name
        self.points_gained = 0.0
        self.gp_gained = 0
        self.team = team
        self.deaths = 0
        self.killcount = defaultdict(int)
        self.drops = defaultdict(lambda: (0, 0))

    def add_death(self):
        self.deaths = self.deaths + 1
        self.team.add_deaths()

    def add_gp(self, value: int):
        self.gp_gained = self.gp_gained + value
        self.team.add_gp(value)

    def add_kc(self, bossname):
        self.killcount[bossname.lower()] = self.killcount[bossname.lower()] + 1
        self.team.killcount[bossname.lower()] = self.team.killcount[bossname.lower()] + 1

    def add_drop(self, drop_name, quantity, value):
        self.drops[drop_name.lower()] = (
            self.drops[drop_name.lower()][0] + quantity, self.drops[drop_name.lower()][1] + value)
        self.team.add_drops(drop_name, quantity, value)

    def __str__(self):
        return self.name


class Team:
    def __init__(self, name: str):
        self.name = name
        self.members = {}
        self.points = 0.0
        self.channel = 0
        self.deaths = 0
        self.killcount = defaultdict(int)
        self.drops = defaultdict(lambda: (0, 0))
        self.gp_gained = 0
        self.image_urls = defaultdict(lambda: defaultdict(list[str]))

    def get_images(self, tile):
        if type(tile) is DropTile:
            for drop in tile.drops:
                if self.image_urls[tile.name.lower()][drop.lower()] is not []:
                    return [self.image_urls[tile.name.lower()][drop.lower()].pop()]
        if type(tile) is KcTile:
            return [self.image_urls[tile.name.lower()][tile.boss_name.lower()][-1]]
        if type(tile) is CollectionTile:
            images = []
            for sub_collection in tile.collection:
                for item in sub_collection.split('/'):
                    if len(self.image_urls[tile.name.lower()][item.lower()]) > 0:
                        images.append(self.image_urls[tile.name.lower()][item.lower()].pop())
                        continue
            return images

    def add_member(self, player_name: str):
        player = Player(player_name, self)
        self.members[player_name.lower()] = player

    def remove_member(self, player_name: str):
        del self.players[player_name.lower()]

    def set_channel(self, channel_id: int):
        self.channel = channel_id

    def add_gp(self, value):
        self.gp_gained = self.gp_gained + value

    def add_deaths(self):
        self.deaths = self.deaths + 1

    def add_drops(self, drop_name, quantity, value):
        self.drops[drop_name.lower()] = (
            self.drops[drop_name.lower()][0] + quantity, self.drops[drop_name.lower()][1] + value)


class Request:
    def __init__(self, tile, team, player_name, image_url):
        self.tile = tile
        self.team = team
        self.image_url = image_url
        self.player_name = player_name

class Bingo:
    def __init__(self):
        self.teams = {}
        self.game_tiles = {}
        self.requests = []

    def new_request(self, tile_name, team_name,player_name, proof_url):
        self.requests.append(Request(self.game_tiles[tile_name.lower()], self.teams[team_name.lower()], player_name, proof_url))

    def new_team(self, name):
        self.teams[name.lower()] = Team(name)

    def delete_team(self, name: str):
        del self.teams[name.lower()]

    def new_drops_tile(self, name, drops, points, recurrence):
        self.game_tiles[name.lower()] = DropTile(name, drops, points, recurrence)

    def new_niche_tile(self, name, points, recurrence):
        self.game_tiles[name.lower()] = NicheTile(name, points, recurrence)

    def get_player(self, player_name):
        for team in self.teams.values():
            if player_name.lower() in team.members:
                return team.members[player_name.lower()]
        return None

    def get_team_names(self):
        team_names = []
        for key in self.teams.keys():
            team_names.append(str(key))
        return team_names

    def get_player_names(self):
        player_names = []
        for team in self.teams.values():
            for key in team.members.keys():
                player_names.append(str(key))
        return player_names

    def get_tile_names(self):
        tile_names = []
        for key, value in self.game_tiles.items():
            tile_names.append(value.name)
        return tile_names

    def get_tile(self, item_name: str):
        for key, value in self.game_tiles.items():
            if type(value) is DropTile:
                if item_name.lower() in [drop.lower() for drop in value.drops]:
                    return value
            if type(value) is CollectionTile:
                for sub_collection in value.collection:
                    for subc_item in sub_collection.split('/'):
                        if item_name.lower() in subc_item.lower():
                            return value
            if type(value) is KcTile:
                if item_name.lower() in value.boss_name.lower():
                    return value
            if type(value) is NicheTile:
                if item_name.lower() is value.name.lower():
                    return value

    def delete_tile(self, name):
        del self.game_tiles[name.lower()]

    def award_tile(self, tile_name: str, team_name: str, player_name: str):
        try:
            tile = self.game_tiles[tile_name.lower()]
            team = self.teams[team_name.lower()]
            player = team.members[player_name.lower()]

            if tile.completion_count[team_name.lower()] < int(tile.recurrence):
                team.points = team.points + int(tile.points)
                player.points_gained = player.points_gained + int(tile.points)
                tile.completion_count[team_name.lower()] = tile.completion_count[team_name.lower()] + 1

                embed = discord.Embed(
                    title="Tile completed!",
                    description=tile.name,
                    color=discord.Colour.green()
                )
                embed.add_field(name="Points Gained", value=f"{tile.points} points", inline=True)
                embed.add_field(name="Player Name", value=f"{player.name}", inline=True)

                if type(tile) is not NicheTile:
                    image_urls = player.team.get_images(tile)

                    embed.set_image(url=image_urls[0])
                    if type(tile) is not KcTile:
                        embed.add_field(name="All images",
                                        value=str(image_urls).replace('\'', '').replace('[', '').replace(']', ''))

                return embed
            else:
                tile.completion_count[team_name.lower()] = tile.completion_count[team_name.lower()] + 1

                descriptions = [f"{player.name} forgot we’ve already done that tile, or are you just showing off?",
                               f"Going for a repeat performance, are we {player.name}?",
                               f"{player.name} really loves that tile I guess...",
                               f"What team are you on {player.name}?",
                               f"Bro wyd. We've done this tile {tile.completion_count[team_name.lower()]} already {player.name}."
                ]

                embed = discord.Embed(
                    title="Time wasted! You've already done this tile...",
                    description=random.choice(descriptions),
                    color=discord.Colour.dark_grey()
                )

                if type(tile) is not NicheTile:
                    image_urls = player.team.get_images(tile)

                    embed.set_image(url=image_urls[0])

                return embed
        except Exception as e:
            print(e)

    def add_drop_tile(self, tile_name: str, drops: list[str], points: int, recurrence: int):
        self.game_tiles[tile_name.lower()] = DropTile(tile_name, drops, points, recurrence)

    def add_kc_tile(self, tile_name, boss_name, point_value, recurrence, kc_required):
        self.game_tiles[tile_name.lower()] = KcTile(tile_name, boss_name, int(point_value), int(recurrence),
                                                    int(kc_required))

    def add_collection_tile(self, tile_name: str, point_value: int, recurrence: int, collection: str):
        self.game_tiles[tile_name.lower()] = CollectionTile(tile_name, point_value, recurrence, collection.split(','))

    def __str__(self):
        output = "Teams\n"
        for team in self.teams.values():
            player_info = [
                f"\t\t{player.name} ({player.points_gained} points and {player.gp_gained} gold). This player has died {player.deaths} times\n"
                for player in team.members.values()]
            player_names = "".join(player_info)
            output += f"\t{team.name} ({team.points} points):\n{player_names}\n"

        output += "\nTiles\n"
        for tile in self.game_tiles.values():
            output += f"\t{tile.name}: Worth {tile.points} points {tile.recurrence} times\n"

        return output