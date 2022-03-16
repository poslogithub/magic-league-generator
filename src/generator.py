import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.tz import gettz
from hashlib import sha512
import random
import re


class Rarity():
    TOKEN = "Token"
    BASIC = "Basic"
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    MYTHIC_RARE = "Mythic Rare"

class N_IN_PACK():
    BASIC = 1
    COMMON = 10
    UNCOMMON = 3
    RARE = 1

class Mode():
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    RANDOM = "random"
    STATIC = "static"

class Key():
    DECK = "deck"
    SIDEBOARD = "sideboard"
    CREATURE = "creature"
    NONCREATURE = "noncreature"
    LAND = "land"
    BASIC = "basic"
    NONBASIC = "nonbasic"
    MV_1 = "-1"
    MV_2 = "2"
    MV_3 = "3"
    MV_4 = "4"
    MV_5 = "5"
    MV_6 = "6-"


class Generator():

    TZ_UTC = gettz("UTC")
    MONTHLY_RESET_HOUR = 20
    WEEKLY_RESET_HOUR = 8
    DAILY_RESET_HOUR = 8

    MYTHIC_RARE_RATE = 1 / 7.4
    BASIC_LANDS = ["平地", "島", "沼", "山", "森", "Plains", "Island", "Swamp", "Mountain", "Forest"]

    def __init__(self, pool):
        self.cards = pool.cards
        self.sets = self.get_sets()
        self.set_info = {}
        for set in self.sets:
            self.set_info[set] = {}
            cards = self.get_cards(set=set, rarity=Rarity.MYTHIC_RARE)
            self.set_info[set][Rarity.MYTHIC_RARE] = len(cards)
            cards = self.get_cards(set=set, rarity=Rarity.RARE)
            self.set_info[set][Rarity.RARE] = len(cards)
            cards = self.get_cards(set=set, rarity=Rarity.UNCOMMON)
            self.set_info[set][Rarity.UNCOMMON] = len(cards)
            cards = self.get_cards(set=set, rarity=Rarity.COMMON)
            self.set_info[set][Rarity.COMMON] = len(cards)
            cards = self.get_cards(set=set, rarity=Rarity.BASIC)
            self.set_info[set][Rarity.BASIC] = len(cards)
    
    def add_card(self, set, rarity, picked_cards):
        cards = self.get_cards(set=set, rarity=rarity)
        while True:
            card = cards[random.randrange(0, len(cards))]
            if card not in picked_cards:
                picked_cards.append(card)
                return picked_cards
    
    def open_boosters(self, user_id, sets, pack_nums, mode=None, index_dt=None):
        pool = []
        for i in range(len(sets)):
            if sets[i] and pack_nums[i]:
                # 乱数初期化
                random.seed(self.get_seed(user_id, sets[i], mode, index_dt))
                
                # パックを剥く
                cards = []
                for _ in range(pack_nums[i]):
                    cards += self.open_booster(sets[i])
                cards = self.sort_cards_by_set_number(cards)
        
                pool += cards

        return pool

    def open_booster(self, set):
        if set and not self.sealedable(set):
            return None

        cards = []

        # レア/神話レア
        if set and self.set_info[set][Rarity.MYTHIC_RARE] == 0:
            for _ in range(N_IN_PACK.RARE):
                cards = self.add_card(
                    set=set, 
                    rarity=Rarity.RARE, 
                    picked_cards=cards
                )
        else:
            for _ in range(N_IN_PACK.RARE):
                cards = self.add_card(
                    set=set, 
                    rarity=Rarity.MYTHIC_RARE if random.random() < self.MYTHIC_RARE_RATE else Rarity.RARE, 
                    picked_cards=cards
                )

        # アンコモン
        for _ in range(N_IN_PACK.UNCOMMON):
            cards = self.add_card(set=set, rarity=Rarity.UNCOMMON, picked_cards=cards)
        
        # コモン
        for _ in range(N_IN_PACK.COMMON):
            cards = self.add_card(set=set, rarity=Rarity.COMMON, picked_cards=cards)

        # 基本土地
        if set and self.set_info[set][Rarity.BASIC] > 0:
            for _ in range(N_IN_PACK.BASIC):
                cards = self.add_card(set=set, rarity=Rarity.BASIC, picked_cards=cards)

        return cards

    def get_cards(self, name="", pretty_name="", cost=None, color_identity=None, card_type="", sub_type="", super_type="",
                    ability="", set="", rarity="", collectible=True, set_number=0, mtga_id=0, 
                    is_token=False, is_secondary_card=False, is_rebalanced=False):
        cards = []
        for card in self.cards:
            if name and card.name != name:
                continue
            if pretty_name and card.pretty_name != pretty_name:
                continue
            if cost and card.cost != cost:
                continue
            if color_identity and card.color_identity != color_identity:
                continue
            if card_type and card.card_type != card_type:
                continue
            if sub_type and not sub_type in card.sub_types:
                continue
            if super_type and not super_type in card.super_type:
                continue
            if ability and not ability in card.abilities:
                continue
            if set and card.set != set:
                continue
            if rarity and card.rarity != rarity:
                continue
            if card.collectible != collectible:
                continue
            if set_number and card.set_number != set_number:
                continue
            if mtga_id and card.mtga_id != mtga_id:
                continue
            if card.is_token != is_token:
                continue
            if card.is_secondary_card != is_secondary_card:
                continue
            if card.is_rebalanced != is_rebalanced:
                continue
            cards.append(card)
        return cards
    
    def get_sets(self):
        sets = []
        for card in self.get_cards():
            if card.set and card.set not in sets:
                sets.append(card.set)
        return sets

    def validate_decklist(self, decklist, pool):
        decklist_pool = self.cards_to_decklist_cards(pool, True)
        decklist_deck = self.decklist_to_decklist_cards(decklist, True)
        invalid_cards = {}
        for deck_key in decklist_deck:
            if deck_key in self.BASIC_LANDS:
                continue
            elif deck_key in decklist_pool.keys():
                num_diff = int(decklist_pool[deck_key]) - int(decklist_deck[deck_key])
                if num_diff < 0:
                    invalid_cards[deck_key] = abs(num_diff)
            else:
                invalid_cards[deck_key] = decklist_deck[deck_key]
        return invalid_cards
    
    def correct_decklist():
        #TODO
        pass

    def sealedable(self, set):
        if self.set_info[set][Rarity.RARE] < N_IN_PACK.RARE:
            return False
        if self.set_info[set][Rarity.UNCOMMON] < N_IN_PACK.UNCOMMON:
            return False
        if self.set_info[set][Rarity.COMMON] < N_IN_PACK.COMMON:
            return False
        return True

    def decklist_cards_to_cards(self, decklist_cards, name_only=False):
        rst = []
        for key in decklist_cards.keys():
            n = decklist_cards[key]
            if name_only:
                name = key
                set = ""
                set_number = 0
            else:
                name = " ".join(key.split()[0:-2])
                set = key.split()[-2].strip("()")
                set_number = int(key.split()[-1])
            cards = self.get_cards(pretty_name=name, set=set, set_number=set_number)
            if cards:
                for _ in range(n):
                    rst.append(cards[-1])
        return rst

    def strip_invalid_cards_from_decklist(self, decklist, invalid_cards):
        deck, sideboard = self.separate_decklist_to_deck_and_sideboard(decklist)
        deck_cards = self.decklist_to_decklist_cards(deck)
        sideboard_cards = self.decklist_to_decklist_cards(sideboard)
        sideboard_cards, invalid_cards = self.strip_invalid_cards_from_decklist_cards(sideboard_cards, invalid_cards)
        if invalid_cards:
            deck_cards, invalid_cards = self.strip_invalid_cards_from_decklist_cards(deck_cards, invalid_cards)
        deck = self.decklist_cards_to_decklist(deck_cards)
        sideboard = self.decklist_cards_to_decklist(sideboard_cards, is_sideboard=True)
        return deck + "\n" + sideboard
    
    def strip_invalid_cards_from_decklist_cards(self, decklist_cards, invalid_cards):
        for invalid_card in invalid_cards.keys():    # invalid_card: カード名
            for decklist_card in decklist_cards.keys():  # decklist_card: カード名 (セット名) セット番号
                if decklist_card.startswith(invalid_card+" "):
                    if decklist_cards[decklist_card] > invalid_cards[invalid_card]:
                        decklist_cards[decklist_card] -= invalid_cards[invalid_card]
                        invalid_cards[invalid_card] = 0
                        break
                    elif decklist_cards[decklist_card] == invalid_cards[invalid_card]:
                        decklist_cards[decklist_card] = 0
                        invalid_cards[invalid_card] = 0
                        break
                    elif decklist_cards[decklist_card] < invalid_cards[invalid_card]:
                        invalid_cards[invalid_card] -= decklist_cards[decklist_card]
                        decklist_cards[decklist_card] = 0
        
        return decklist_cards, invalid_cards
    
    def get_diff_cards(self, pool, decklist):
        pool_cards = self.cards_to_decklist_cards(pool)
        decklist_cards = self.decklist_to_decklist_cards(decklist, name_only=True)
        diff_cards = self.strip_invalid_cards_from_decklist_cards(pool_cards, decklist_cards)
        return diff_cards

    def add_diff_to_sideboard(self, decklist, pool):
        adding_cards = self.get_diff_cards(self, pool, decklist)
        adding_str = self.decklist_cards_to_decklist(adding_cards, is_sideboard=True)
        if "サイドボード\n" in decklist or "Sideboard\n" in decklist:
            adding_str.replace("サイドボード\n", "")
            adding_str.replace("Sideboard\n", "")
        return decklist + adding_str
    
    @classmethod
    def decklist_to_decklist_cards(cls, decklist, name_only=False):
        decklist_cards = {}
        decklist_lines = decklist.splitlines()
        for line in decklist_lines:
            if re.match(r'^[0-9]', line):
                num = int(line.split()[0])
                if name_only:
                    decklist_card_str = " ".join(line.split()[1:-2])
                else:
                    decklist_card_str = " ".join(line.split()[1:])
                if decklist_cards.get(decklist_card_str):   # デッキとサイドボードに分かれている可能性があるため
                    decklist_cards[decklist_card_str] += num
                else:
                    decklist_cards[decklist_card_str] = num
        return decklist_cards

    @classmethod
    def get_pack_num(cls, mode):
        # 月初からの週数に応じて剥くパック数を決定
        if mode == Mode.MONTHLY:
            td = datetime.now(tz=cls.TZ_UTC) - cls.get_index_datetime(mode)
            if td.days < 7:
                pack_num = 4
            elif td.days < 14:
                pack_num = 6
            elif td.days < 21:
                pack_num = 9
            else:
                pack_num = 12
        else:
            pack_num = 6

        return pack_num

    @classmethod
    def get_index_datetime(cls, mode, index_dt=None):
        now = datetime.now(cls.TZ_UTC)

        if mode == Mode.MONTHLY:
            if (now+timedelta(days=1)).day == 1 and now.hour >= cls.MONTHLY_RESET_HOUR:    # 翌日が1日＝今日が月末日
                dt = datetime(now.year, now.month, now.day, cls.MONTHLY_RESET_HOUR, tzinfo=cls.TZ_UTC)
            else:
                dt = datetime(now.year, now.month - 1, calendar.monthrange(now.year, now.month - 1)[1], cls.MONTHLY_RESET_HOUR, tzinfo=cls.TZ_UTC) # 前月の月末日
        elif mode == Mode.WEEKLY:
            if now.weekday == 6 and now.hour > cls.WEEKLY_RESET_HOUR:    # 当日が日曜の場合
                dt = datetime(now.year, now.month, now.day, cls.WEEKLY_RESET_HOUR, tzinfo=cls.TZ_UTC)
            else:
                dt = datetime(now.year, now.month, now.day, cls.WEEKLY_RESET_HOUR, tzinfo=cls.TZ_UTC) - timedelta(days=now.weekday()+1)
        elif mode == Mode.DAILY:
            if now.hour > cls.DAILY_RESET_HOUR:
                dt = datetime(now.year, now.month, now.day, cls.WEEKLY_RESET_HOUR, tzinfo=cls.TZ_UTC)
            else:
                dt = datetime(now.year, now.month, now.day, cls.WEEKLY_RESET_HOUR, tzinfo=cls.TZ_UTC) - timedelta(days=1)
        elif mode == Mode.STATIC and index_dt:
            dt = index_dt
        else:
            dt = now

        return dt

    @classmethod
    def get_next_index_datetime(cls, mode):
        index_dt = cls.get_index_datetime(mode)

        if mode == Mode.MONTHLY:
            dt = index_dt + relativedelta(months=1)
        elif mode == Mode.WEEKLY:
            dt = index_dt + timedelta(days=7)
        elif mode == Mode.DAILY:
            dt = index_dt + timedelta(days=1)
        elif mode == Mode.RANDOM:
            dt = index_dt
        elif mode == Mode.STATIC:
            dt = None
        else:
            dt = None

        return dt

    @classmethod
    def get_seed(cls, user_id, set, mode, index_dt=None):
        return cls.get_hashed_int(
            user_id=user_id, 
            set=set,
            timestamp=cls.get_index_datetime(mode, index_dt).timestamp()
        )

    @classmethod
    def get_hashed_int(cls, user_id, set, timestamp):
        hash_str = user_id + "@" + set + "@" + str(timestamp)
        hash_bytes = hash_str.encode(encoding="utf-8")
        hashed_bytes = sha512(hash_bytes)
        hashed_int = int(hashed_bytes.hexdigest(), 16)
        return hashed_int
    
    @classmethod
    def cards_to_decklist(cls, cards):
        decklist_cards = cls.cards_to_decklist_cards(cards)
        decklist = cls.decklist_cards_to_decklist(decklist_cards)
        return decklist

    @classmethod
    def cards_to_decklist_cards(cls, cards, name_only=False):
        decklist_cards = {}
        for card in cards:
            if name_only:
                decklist_card_str = card.pretty_name
            else:
                decklist_card_str = card.pretty_name + " (" + card.set + ") " + str(card.set_number)
            if decklist_card_str not in decklist_cards:
                decklist_cards[decklist_card_str] = 1
            else:
                decklist_cards[decklist_card_str] += 1
        return decklist_cards
    
    @classmethod
    def decklist_cards_to_decklist(cls, decklist_cards, name_only=False, is_sideboard=False):
        decklist = ("デッキ" if not is_sideboard else "サイドボード")+"\n"
        for key in decklist_cards.keys():
            if decklist_cards[key] == 0:
                continue
            if name_only:
                decklist += str(decklist_cards[key]) + " " + " ".join(key.split()[0:-2]) + "\n"
            else:
                decklist += str(decklist_cards[key]) + " " + key + "\n"
        return decklist

    @classmethod
    def sort_cards_by_set_number(cls, cards):
        set_numbers = []
        results = []
        for card in cards:
            set_numbers.append(card.set_number)
        set_numbers.sort()
        for set_number in set_numbers:
            for card in cards:
                if card.set_number == set_number:
                    results.append(card)
                    break
        return results
    
    @classmethod
    def separate_decklist_to_deck_and_sideboard(cls, decklist):
        is_deck = True
        deck = "デッキ\n"
        sideboard = "サイドボード\n"
        decklist_lines = decklist.splitlines()
        for line in decklist_lines:
            if line in ["サイドボード", "Sideboard"]:
                is_deck = False
            elif re.match(r'^[0-9]', line):
                if is_deck:
                    deck += line + "\n"
                else:
                    sideboard += line + "\n"
        return deck, sideboard

    def cards_to_decklist_image_array(self, cards):
        rst = {
            Key.CREATURE: {
                Key.MV_1: [],
                Key.MV_2: [],
                Key.MV_3: [],
                Key.MV_4: [],
                Key.MV_5: [],
                Key.MV_6: []
            }, 
            Key.NONCREATURE: {
                Key.MV_1: [],
                Key.MV_2: [],
                Key.MV_3: [],
                Key.MV_4: [],
                Key.MV_5: [],
                Key.MV_6: []
            },
            Key.LAND: {
                Key.BASIC: [],
                Key.NONBASIC: []
            }
        }

        for card in cards:
            if card.is_creature_card:
                key1 = Key.CREATURE
            elif card.is_noncreature_spell_card:
                key1 = Key.NONCREATURE
            elif card.is_land_card:
                key1 = Key.LAND
            if key1 != Key.LAND:
                if card.cmc <= 1:
                    key2 = Key.MV_1
                elif card.cmc == 2:
                    key2 = Key.MV_2
                elif card.cmc == 3:
                    key2 = Key.MV_3
                elif card.cmc == 4:
                    key2 = Key.MV_4
                elif card.cmc == 5:
                    key2 = Key.MV_5
                elif card.cmc >= 6:
                    key2 = Key.MV_6
            else:
                if card.is_basic:
                    key2 = Key.BASIC
                else:
                    key2 = Key.NONBASIC
            rst[key1][key2].append(card)

        return rst

    def decklist_to_decklist_image_array(self, decklist):
        rst = {
            Key.DECK: {},
            Key.SIDEBOARD: {}
        }

        deck, sideboard = self.separate_decklist_to_deck_and_sideboard(decklist)
        deck_cards = self.decklist_cards_to_cards(self.decklist_to_decklist_cards(deck))
        sideboard_cards = self.decklist_cards_to_cards(self.decklist_to_decklist_cards(sideboard))
        rst[Key.DECK] = self.cards_to_decklist_image_array(deck_cards)
        rst[Key.SIDEBOARD] = self.cards_to_decklist_image_array(sideboard_cards)

        return rst
