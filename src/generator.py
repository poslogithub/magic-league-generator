import calendar
import datetime
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
    

class Generator():

    TZ_UTC = gettz("UTC")
    MONTHLY_RESET_HOUR = 20
    MYTHIC_RARE_RATE = 1 / 7.4

    def __init__(self, pool):
        self.cards = pool.cards
    
    def add_card(self, set, rarity, picked_cards):
        cards = self.get_cards(set=set, rarity=rarity)
        n = len(cards)
        while True:
            card = cards[random.randrange(0, n)]
            if card not in picked_cards:
                picked_cards.append(card)
                return picked_cards
    
    def open_monthly_boosters(self, user_id, set):
        # 月次乱数初期化
        random.seed(self.get_monthly_seed(user_id))

        # 月初からの週数に応じて剥くパック数を決定
        pack_num = self.get_monthly_pack_num()
        
        # 決定した数だけパックを剥く
        cards = []
        for _ in range(pack_num):
            cards += self.open_booster(set)
        
        return cards

    def open_booster(self, set):
        cards = []

        # レア/神話レア
        cards = self.add_card(
            set=set, 
            rarity=Rarity.MYTHIC_RARE if random.random() < self.MYTHIC_RARE_RATE else Rarity.RARE, 
            picked_cards=cards)

        # アンコモン
        for _ in range(3):
            cards = self.add_card(set=set, rarity=Rarity.UNCOMMON, picked_cards=cards)
        
        # コモン
        for _ in range(10):
            cards = self.add_card(set=set, rarity=Rarity.COMMON, picked_cards=cards)

        return cards

    def get_cards(self, name="", pretty_name="", cost=None, color_identity=None, card_type="", sub_types="",
                    abilities=None, set="", rarity="", collectible=True, set_number=0, mtga_id=0, 
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
            if sub_types and card.sub_types != sub_types:
                continue
            if abilities and card.abilities != abilities:
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

    def validate_decklist(self, user_id, set, decklist):
        pool = self.open_monthly_boosters(user_id, set)
        decklist_pool = self.cards_to_decklist_cards(pool, True)
        decklist_deck = self.decklist_to_decklist_cards(decklist, True)
        invalid_cards = {}
        for deck_key in decklist_deck:
            if deck_key in decklist_pool.keys():
                num_diff = int(decklist_pool[deck_key]) - int(decklist_deck[deck_key])
                if num_diff < 0:
                    invalid_cards[deck_key] = abs(num_diff)
            else:
                invalid_cards[deck_key] = decklist_deck[deck_key]
        return invalid_cards

    @classmethod
    def decklist_to_decklist_cards(cls, decklist, name_only=False):
        decklist_cards = {}
        decklist_lines = decklist.splitlines()
        for line in decklist_lines:
            print(line)
            if re.match(r'^[0-9]', line):
                num = int(line.split()[0])
                if name_only:
                    decklist_card_str = line.split()[1]
                else:
                    decklist_card_str = " ".join(line.split()[1:])
                if decklist_cards.get(decklist_card_str):   # デッキとサイドボードに分かれている可能性があるため
                    decklist_cards[decklist_card_str] += num
                else:
                    decklist_cards[decklist_card_str] = num
        return decklist_cards

    @classmethod
    def get_monthly_pack_num(cls):
        # 月初からの週数に応じて剥くパック数を決定
        monthly_dt = cls.get_monthly_datetime()
        now = datetime.datetime.now(tz=cls.TZ_UTC)
        td = now - monthly_dt
        if td.days < 7:
            pack_num = 4
        elif td.days < 14:
            pack_num = 6
        elif td.days < 21:
            pack_num = 9
        else:
            pack_num = 12
        return pack_num

    @classmethod
    def get_monthly_datetime(cls):
        now = datetime.datetime.now(cls.TZ_UTC)
        tomorrow = now + datetime.timedelta(days=1)
        if tomorrow.day == 1 and now.hour >= cls.MONTHLY_RESET_HOUR:
            dt = datetime.datetime(now.year, now.month, now.day, cls.MONTHLY_RESET_HOUR, tzinfo=cls.TZ_UTC)
        else:
            dt = datetime.datetime(now.year, now.month - 1, calendar.monthrange(now.year, now.month - 1)[1], cls.MONTHLY_RESET_HOUR, tzinfo=cls.TZ_UTC)
        return dt

    @classmethod
    def get_monthly_seed(cls, user_id):
        return cls.get_hashed_int(
            user_id=user_id, 
            timestamp=cls.get_monthly_datetime().timestamp())

    @classmethod
    def get_hashed_int(cls, user_id, timestamp):
        hash_str = user_id + "@" + str(timestamp)
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
    def decklist_cards_to_decklist(cls, decklist_cards, name_only=False):
        decklist = "デッキ\n"
        for key in decklist_cards.keys():
            if name_only:
                decklist += str(decklist_cards[key]) + " " + key.split()[0] + "\n"
            else:
                decklist += str(decklist_cards[key]) + " " + key + "\n"
        return decklist
