"""Pure game simulation: no display, audio, network, or dependencies required."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import time

from content import (REALMS, REALM_SIZE, HEROES, ITEMS, EGGS, PET_NAMES, RARITIES,
                     ABILITIES, SOUL_UPGRADES, ACHIEVEMENTS, ENEMY_NAMES, BOSS_NAMES)

CAP = 1e250
METRICS = ("kills", "clicks", "bosses", "hatches", "fusions", "rebirths", "ascensions", "best_zone")

def num(x):
    """Readable idle-game numbers, without float overflow or undefined suffixes."""
    x = float(x)
    if not math.isfinite(x): return "MAX"
    if x < 1000: return str(int(x)) if x >= 100 else f"{x:.1f}".rstrip("0").rstrip(".")
    suffix = ["", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc"]
    p = int(math.log10(max(1, x)) // 3)
    if p < len(suffix): return f"{x / 10 ** (3*p):.2f}".rstrip("0").rstrip(".") + suffix[p]
    return f"{x:.2e}"

def power(base, exponent):
    return math.exp(min(math.log(CAP), math.log(base) * exponent))

def bounded(value, default=0, maximum=CAP):
    if not isinstance(value, (float, int)) or isinstance(value, bool): return default
    if not math.isfinite(value): return default
    return max(0, min(maximum, value))

def save_directory():
    root = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return root / "tung-tung-legends-x"

class Game:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.coins = 0.0
        self.gems = 65
        self.shards = 0
        self.souls = 0
        self.soul_power = 0
        self.astrals = 0
        self.zone = 1
        self.max_zone = 1
        self.run_best = 1
        self.zone_kills = 0
        self.heroes = [0 for _ in HEROES]
        self.tap_level = 0
        self.pets = []
        self.equipped_pets = []
        self.next_pet_id = 1
        self.pity = [0 for _ in EGGS]
        self.items = {"knocker": 1}
        self.equipment = {"weapon": "knocker", "charm": None, "engine": None, "relic": None}
        self.upgrades = {x[0]: 0 for x in SOUL_UPGRADES}
        self.stats = {key: 0 for key in METRICS}
        self.stats["best_zone"] = 1
        self.claimed = []
        self.contracts = []
        self.contract_tier = 0
        self.cooldowns = {key: 0.0 for key in ABILITIES}
        self.buffs = {key: 0.0 for key in ABILITIES}
        self.auto_progress = True
        self.settings = {"sound": True, "music": False, "motion": True, "particles": True,
                         "fps": 60, "volume": .3, "tutorial": True}
        self.playtime = 0.0
        self.run_coins = 0.0
        self.run_kills = 0
        self.messages = []
        self.events = []
        self.failed_boss = None
        self.offline_report = None
        self.last_saved = time.time()
        self._cached_stats = None
        self.new_enemy()
        self.make_contracts()

    def notify(self, message):
        self.messages.append(message)
        self.messages = self.messages[-8:]

    def invalidate(self):
        self._cached_stats = None

    def realm(self):
        return min(len(REALMS) - 1, (self.zone - 1) // REALM_SIZE)

    def is_boss(self): return self.zone % 10 == 0

    def enemy_name(self):
        if self.is_boss(): return BOSS_NAMES[self.realm()]
        return ENEMY_NAMES[(self.zone + self.zone_kills) % len(ENEMY_NAMES)]

    def health_at(self, zone):
        return min(CAP, 12 * power(1.112, zone - 1) * (9 if zone % 10 == 0 else 1))

    def reward_at(self, zone):
        return min(CAP, 4 * power(1.105, zone - 1) * (9 if zone % 10 == 0 else 1))

    def new_enemy(self):
        self.max_hp = self.health_at(self.zone)
        self.hp = self.max_hp
        self.boss_time = 30.0 + self.upgrades["time"] * 2

    def pet_slots(self): return 3 + self.upgrades["slots"]

    def pet_multiplier(self, pet):
        return RARITIES[pet["rarity"]][2] * power(1.48, pet["egg"]) * power(1.55, pet["stars"] - 1) * (1.5 if pet["shiny"] else 1)

    def pet_name(self, pet): return PET_NAMES[pet["egg"]][pet["rarity"]]

    def combat_stats(self):
        if self._cached_stats is not None: return self._cached_stats
        pet_mult = 1.0
        selected = set(self.equipped_pets[:self.pet_slots()])
        for pet in self.pets:
            if pet["id"] in selected: pet_mult *= self.pet_multiplier(pet)
        pet_mult = min(pet_mult, 1e60)
        gear = {k: 0.0 for k in ("click", "idle", "gold", "boss")}
        for item in ITEMS:
            if item["id"] in self.equipment.values():
                rank = self.items.get(item["id"], 0)
                for k in gear: gear[k] += item[k] * (1 + .12 * (rank - 1))
        rebirth = 1 + .12 * self.soul_power
        astral = power(2, self.astrals)
        common = min(CAP, pet_mult * rebirth * astral)
        hero_base = 0.0
        for level, (_, _, dps, _) in zip(self.heroes, HEROES):
            hero_base = min(CAP, hero_base + dps * level * power(2, level // 25))
        click_base = min(CAP, (1 + self.tap_level * 1.5) + hero_base * .045)
        click = min(CAP, click_base * common * (1 + gear["click"]) * (1 + .2*self.upgrades["click"]))
        idle = min(CAP, hero_base * common * (1 + gear["idle"]) * (1 + .2*self.upgrades["idle"]))
        gold = min(1e100, (1 + gear["gold"]) * (1 + self.upgrades["gold"]*.15) * pet_mult**.2)
        boss = 1 + gear["boss"] + self.upgrades["boss"] * .2
        crit = min(.45, .05 + self.astrals * .005)
        self._cached_stats = dict(click=click, idle=idle, gold=gold, boss=boss, pet=pet_mult,
                                  rebirth=rebirth, astral=astral, crit=crit)
        return self._cached_stats

    def click_damage(self):
        return min(CAP, self.combat_stats()["click"] * (3 if self.buffs["frenzy"] > 0 else 1))

    def idle_damage(self):
        return min(CAP, self.combat_stats()["idle"] * (3 if self.buffs["overdrive"] > 0 else 1))

    def tap_cost(self): return min(CAP, 8 * power(1.17, self.tap_level))

    def buy_taps(self, amount=1):
        count = 0
        while count < min(amount, 1000) and self.tap_level < 3000:
            cost = self.tap_cost()
            if self.coins + 1e-8 < cost: break
            self.coins = max(0, self.coins - cost)
            self.tap_level += 1
            count += 1
        if count: self.invalidate()
        return count

    def hero_cost(self, index, offset=0):
        return min(CAP, HEROES[index][1] * power(1.13, self.heroes[index] + offset))

    def hero_buy_cost(self, index, amount):
        n = min(amount, 3000 - self.heroes[index])
        if n <= 0: return CAP
        if n == 1: return self.hero_cost(index)
        # A geometric sum is exact enough here and avoids 1000 UI iterations.
        return min(CAP, self.hero_cost(index) * (power(1.13, n)-1) / .13)

    def buy_hero(self, index, amount=1):
        if not 0 <= index < len(HEROES): return 0
        count = 0
        while count < min(amount, 1000) and self.heroes[index] < 3000:
            cost = self.hero_cost(index)
            if self.coins + 1e-8 < cost: break
            self.coins = max(0, self.coins-cost)
            self.heroes[index] += 1
            count += 1
        if count:
            self.invalidate()
            self.events.append(("buy", index))
        return count

    def click(self):
        self.stats["clicks"] += 1
        crit = self.rng.random() < self.combat_stats()["crit"]
        damage = min(CAP, self.click_damage() * (3 if crit else 1))
        if self.is_boss(): damage = min(CAP, damage * self.combat_stats()["boss"])
        self.events.append(("hit", damage, crit))
        self.damage(damage)
        return damage

    def damage(self, amount):
        amount = bounded(amount)
        # Excess damage spills to the next target. Bound work per simulation step.
        count = 0
        while amount > 0 and count < 30:
            if amount < self.hp:
                self.hp -= amount
                break
            amount -= self.hp
            self.defeat()
            count += 1

    def defeat(self):
        boss = self.is_boss()
        s = self.combat_stats()
        reward = min(CAP, self.reward_at(self.zone) * s["gold"] * (3 if self.buffs["gold"] > 0 else 1))
        self.coins = min(CAP, self.coins + reward)
        self.run_coins = min(CAP, self.run_coins + reward)
        self.stats["kills"] += 1
        self.run_kills += 1
        self.zone_kills += 1
        if boss:
            self.stats["bosses"] += 1
            self.gems += 3 + self.realm()
            self.shards += 1 + self.realm() // 2
            self.events.append(("boss", self.zone))
            if self.zone == 1200:
                self.notify("CAMPAIGN COMPLETE! Endless realms are now ahead.")
        self.events.append(("kill", reward, boss))
        required = 1 if boss else 5
        if self.zone_kills >= required:
            self.max_zone = max(self.max_zone, self.zone + 1)
            if self.auto_progress:
                self.zone += 1
                self.run_best = max(self.run_best, self.zone)
                self.stats["best_zone"] = max(self.stats["best_zone"], self.zone)
                self.zone_kills = 0
                if self.zone % 100 == 1:
                    self.gems += 25 + self.realm()*5
                    self.notify(f"New realm: {REALMS[self.realm()][0]}!")
            else: self.zone_kills = 0
        self.new_enemy()

    def move_zone(self, zone):
        if not 1 <= zone <= self.max_zone: return False
        self.zone = zone
        self.run_best = max(self.run_best, zone)
        self.stats["best_zone"] = max(self.stats["best_zone"], zone)
        self.zone_kills = 0
        self.new_enemy()
        return True

    def update(self, dt):
        if not math.isfinite(dt) or dt <= 0: return
        dt = min(dt, 1.0)
        self.playtime += dt
        for key in self.cooldowns:
            self.cooldowns[key] = max(0.0, self.cooldowns[key] - dt)
            self.buffs[key] = max(0.0, self.buffs[key] - dt)
        damage = self.idle_damage() * dt
        if self.upgrades["auto"]: damage += self.click_damage() * 4 * dt
        if self.buffs["echo"] > 0: damage += self.click_damage() * 5 * dt
        if self.is_boss(): damage *= self.combat_stats()["boss"]
        self.damage(min(CAP, damage))
        if self.is_boss():
            self.boss_time -= dt
            if self.boss_time <= 0:
                self.failed_boss = self.zone
                self.zone = max(1, self.zone - 1)
                self.auto_progress = False
                self.zone_kills = 0
                self.new_enemy()
                self.notify("Boss escaped. Farm here, upgrade, then retry.")
                self.events.append(("fail", self.failed_boss))

    def available_abilities(self):
        result = ["slam"]
        for item in ITEMS:
            if item["id"] in self.equipment.values() and item["ability"]:
                if item["ability"] not in result: result.append(item["ability"])
        return result

    def cast(self, ability):
        if ability not in self.available_abilities() or self.cooldowns[ability] > 0: return False
        _, cooldown, duration, _ = ABILITIES[ability]
        self.cooldowns[ability] = cooldown
        self.buffs[ability] = duration
        click, idle = self.click_damage(), self.idle_damage()
        damage = {"slam": click*12, "thunder": click*25 + idle*8,
                  "rift": (click*30 + idle*12) * (2 if self.is_boss() else 1)}.get(ability, 0)
        if self.is_boss(): damage *= self.combat_stats()["boss"]
        if damage: self.damage(min(CAP, damage))
        self.events.append(("cast", ability))
        return True

    def hatch(self, egg=0):
        if not 0 <= egg < len(EGGS): return None
        if self.stats["best_zone"] < EGGS[egg][2]:
            self.notify(f"Reach lifetime stage {EGGS[egg][2]} to unlock this egg.")
            return None
        if len(self.pets) >= 240:
            self.notify("Pet inventory full. Fuse duplicates or recycle pets.")
            return None
        if self.gems < EGGS[egg][1]: return None
        self.gems -= EGGS[egg][1]
        self.pity[egg] += 1
        weights = [x[1] for x in RARITIES]
        luck = self.upgrades["luck"]
        for i in range(1, 6): weights[i] *= 1 + luck*.08*i
        rarity = self.rng.choices(range(6), weights=weights)[0]
        if self.pity[egg] % 120 == 0: rarity = 5
        elif self.pity[egg] % 40 == 0: rarity = max(4, rarity)
        elif self.pity[egg] % 10 == 0: rarity = max(3, rarity)
        pet = dict(id=self.next_pet_id, egg=egg, rarity=rarity, stars=1, shiny=self.rng.random()<.025)
        self.next_pet_id += 1
        self.pets.append(pet)
        self.stats["hatches"] += 1
        self.auto_equip()
        self.events.append(("hatch", pet.copy()))
        self.notify(f"Hatched {'Shiny ' if pet['shiny'] else ''}{self.pet_name(pet)}! {self.pet_multiplier(pet):.2f}x")
        return pet

    def auto_equip(self):
        best = sorted(self.pets, key=self.pet_multiplier, reverse=True)
        self.equipped_pets = [p["id"] for p in best[:self.pet_slots()]]
        self.invalidate()

    def equip_pet(self, pet_id):
        if pet_id in self.equipped_pets:
            self.equipped_pets.remove(pet_id)
        else:
            if not any(p["id"] == pet_id for p in self.pets): return False
            if len(self.equipped_pets) >= self.pet_slots():
                self.notify("Formation full. Unequip a pet or use Equip Best.")
                return False
            self.equipped_pets.append(pet_id)
        self.invalidate()
        return True

    def fuse(self, pet_id):
        pet = next((p for p in self.pets if p["id"] == pet_id), None)
        if not pet or pet["stars"] >= 8: return False
        matches = [p for p in self.pets if all(p[k] == pet[k] for k in ("egg", "rarity", "stars", "shiny"))]
        if len(matches) < 3:
            self.notify("Fusion needs 3 matching species, stars, and shiny status.")
            return False
        others = [p for p in matches if p["id"] != pet_id][:2]
        consumed = {p["id"] for p in others}
        self.pets = [p for p in self.pets if p["id"] not in consumed]
        pet["stars"] += 1
        self.stats["fusions"] += 1
        self.auto_equip()
        self.notify(f"Fused {self.pet_name(pet)} to {pet['stars']} stars!")
        return True

    def recycle_pet(self, pet_id):
        pet = next((p for p in self.pets if p["id"] == pet_id), None)
        if not pet: return False
        self.shards += max(1, (pet["rarity"]+1) * pet["stars"] * (2 if pet["shiny"] else 1))
        self.pets.remove(pet)
        self.auto_equip()
        return True

    def buy_item(self, item_id):
        item = next((i for i in ITEMS if i["id"] == item_id), None)
        if not item or item_id in self.items: return False
        if self.stats["best_zone"] < item["zone"] or self.gems < item["price"]: return False
        self.gems -= item["price"]
        self.items[item_id] = 1
        self.equipment[item["slot"]] = item_id
        self.invalidate()
        return True

    def equip_item(self, item_id):
        item = next((i for i in ITEMS if i["id"] == item_id), None)
        if not item or item_id not in self.items: return False
        self.equipment[item["slot"]] = item_id
        self.invalidate()
        return True

    def item_cost(self, item_id): return math.ceil(3 * self.items.get(item_id, 1)**1.6)

    def upgrade_item(self, item_id):
        if item_id not in self.items or self.items[item_id] >= 50: return False
        cost = self.item_cost(item_id)
        if self.shards < cost: return False
        self.shards -= cost
        self.items[item_id] += 1
        self.invalidate()
        return True

    def soul_cost(self, key):
        entry = next(x for x in SOUL_UPGRADES if x[0] == key)
        return math.ceil(entry[2] * power(entry[3], self.upgrades[key]))

    def buy_soul_upgrade(self, key):
        entry = next((x for x in SOUL_UPGRADES if x[0] == key), None)
        if not entry or self.upgrades[key] >= entry[4]: return False
        cost = self.soul_cost(key)
        if self.souls < cost: return False
        self.souls -= cost
        self.upgrades[key] += 1
        self.invalidate()
        if key == "slots": self.auto_equip()
        return True

    def rebirth_reward(self):
        if self.run_best < 50: return 0
        return max(1, int(5 * power(self.run_best / 50, 1.65)))

    def reset_run(self):
        self.coins = min(CAP, 30 * self.upgrades["start"] * power(2, self.upgrades["start"]))
        self.heroes = [0 for _ in HEROES]
        self.tap_level = 0
        self.zone = self.max_zone = self.run_best = 1
        self.zone_kills = self.run_kills = 0
        self.run_coins = 0
        self.auto_progress = True
        self.failed_boss = None
        self.cooldowns = {key: 0.0 for key in ABILITIES}
        self.buffs = {key: 0.0 for key in ABILITIES}
        self.invalidate()
        self.new_enemy()

    def rebirth(self):
        reward = self.rebirth_reward()
        if not reward: return False
        self.souls += reward
        self.soul_power += reward
        self.stats["rebirths"] += 1
        self.reset_run()
        self.notify(f"REBORN! +{reward} souls. Pets, equipment and gems kept.")
        self.events.append(("rebirth", reward))
        return True

    def ascension_reward(self):
        if self.run_best < 300: return 0
        return max(1, int(power(self.run_best / 300, 1.5)))

    def ascend(self):
        reward = self.ascension_reward()
        if not reward: return False
        self.astrals += reward
        self.stats["ascensions"] += 1
        self.souls = self.soul_power = 0
        self.upgrades = {x[0]: 0 for x in SOUL_UPGRADES}
        self.reset_run()
        self.auto_equip()
        self.notify(f"ASCENDED! +{reward} astrals. Each astral doubles all damage.")
        self.events.append(("ascend", reward))
        return True

    def make_contracts(self):
        metric_specs = [("kills", "Farm tungs", 60), ("clicks", "Land manual knocks", 80),
                        ("bosses", "Defeat bosses", 4), ("hatches", "Hatch pets", 2)]
        self.contracts = []
        for offset in range(3):
            metric, label, base = metric_specs[(self.contract_tier + offset) % len(metric_specs)]
            goal = int(base * (1 + self.contract_tier*.25))
            self.contracts.append(dict(metric=metric, label=label, start=self.stats[metric],
                                       goal=goal, claimed=False, gems=20+self.contract_tier*3))

    def claim_contract(self, index):
        if not 0 <= index < len(self.contracts): return False
        c = self.contracts[index]
        if c["claimed"] or self.stats[c["metric"]] - c["start"] < c["goal"]: return False
        c["claimed"] = True
        self.gems += c["gems"]
        self.shards += 3 + self.contract_tier
        if all(c["claimed"] for c in self.contracts):
            self.contract_tier += 1
            self.make_contracts()
            self.notify("Contract board refreshed. Higher rewards are waiting.")
        return True

    def claim_achievement(self, ach_id):
        ach = next((a for a in ACHIEVEMENTS if a[0] == ach_id), None)
        if not ach or ach_id in self.claimed or self.stats[ach[2]] < ach[3]: return False
        self.claimed.append(ach_id)
        self.gems += ach[4]
        self.notify(f"Achievement: {ach[1]}! +{ach[4]} gems.")
        return True

    def ready_rewards(self):
        return sum(a[0] not in self.claimed and self.stats[a[2]] >= a[3] for a in ACHIEVEMENTS) + sum(
            not c["claimed"] and self.stats[c["metric"]]-c["start"] >= c["goal"] for c in self.contracts)

    def offline(self, seconds):
        seconds = min(8*3600, bounded(seconds))
        if seconds < 30: return
        s = self.combat_stats()
        damage = s["idle"] + (s["click"]*4 if self.upgrades["auto"] else 0)
        farm_zone = self.zone - 1 if self.is_boss() else self.zone
        farm_zone = max(1, farm_zone)
        efficiency = .25 + self.upgrades["offline"]*.05
        kills = min(1000000, int(seconds * efficiency * damage / self.health_at(farm_zone)))
        reward = min(CAP, kills * self.reward_at(farm_zone) * s["gold"])
        self.coins = min(CAP, self.coins + reward)
        self.run_coins = min(CAP, self.run_coins + reward)
        self.run_kills += kills
        self.stats["kills"] += kills
        self.offline_report = dict(seconds=int(seconds), kills=kills, coins=reward, efficiency=efficiency)

    def serialize(self):
        keys = ("coins", "gems", "shards", "souls", "soul_power", "astrals", "zone", "max_zone", "run_best",
                "zone_kills", "heroes", "tap_level", "pets", "equipped_pets", "next_pet_id", "pity", "items",
                "equipment", "upgrades", "stats", "claimed", "contracts", "contract_tier", "cooldowns", "buffs",
                "auto_progress", "settings", "playtime", "run_coins", "run_kills", "hp", "boss_time", "failed_boss")
        data = {key: getattr(self, key) for key in keys}
        data["saved_at"] = time.time()
        data["version"] = 1
        return data

    def save(self, directory=None):
        directory = Path(directory) if directory else save_directory()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "save.json"
        payload = self.serialize()
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        wrapper = {"checksum": hashlib.sha256(text.encode()).hexdigest(), "data": payload}
        temporary = directory / "save.tmp"
        with temporary.open("w", encoding="utf-8") as f:
            json.dump(wrapper, f, separators=(",", ":"), allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        if path.exists():
            # Never replace a good backup with a corrupt primary save.
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
                previous_text = json.dumps(previous["data"], sort_keys=True, separators=(",", ":"), allow_nan=False)
                valid = hashlib.sha256(previous_text.encode()).hexdigest() == previous["checksum"]
            except (ValueError, KeyError, TypeError):
                valid = False
            target = "save.backup.json" if valid else f"save.corrupt.{time.time_ns()}.json"
            shutil.copy2(path, directory / target)
        os.replace(temporary, path)
        self.last_saved = payload["saved_at"]
        return path

    @classmethod
    def load(cls, directory=None, apply_offline=True):
        directory = Path(directory) if directory else save_directory()
        errors = []
        for filename in ("save.json", "save.backup.json"):
            path = directory / filename
            if not path.exists(): continue
            try:
                if path.stat().st_size > 2000000: raise ValueError("save file too large")
                wrapper = json.loads(path.read_text(encoding="utf-8"))
                data = wrapper["data"]
                text = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
                if hashlib.sha256(text.encode()).hexdigest() != wrapper["checksum"]:
                    raise ValueError("save checksum mismatch")
                game = cls.from_data(data)
                if apply_offline: game.offline(max(0, time.time()-bounded(data.get("saved_at", time.time()))))
                if errors: game.notify("Recovered progress from the backup save.")
                return game
            except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
                errors.append(str(exc))
        game = cls()
        if errors: game.notify("Save unreadable. Original files kept for recovery.")
        return game

    @classmethod
    def from_data(cls, data):
        if not isinstance(data, dict) or data.get("version") != 1: raise ValueError("unsupported save")
        game = cls()
        for key in ("coins", "run_coins", "playtime"):
            setattr(game, key, float(bounded(data.get(key, 0))))
        for key in ("gems", "shards", "souls", "soul_power", "astrals", "tap_level", "run_kills", "contract_tier"):
            setattr(game, key, int(bounded(data.get(key, 0), maximum=1000000000)))
        for key in ("zone", "max_zone", "run_best"):
            setattr(game, key, max(1, int(bounded(data.get(key, 1), maximum=1000000000))))
        game.max_zone = max(game.max_zone, game.zone, game.run_best)
        game.heroes = [int(bounded(x, maximum=3000)) for x in data.get("heroes", [])[:len(HEROES)]]
        game.heroes += [0]*(len(HEROES)-len(game.heroes))
        game.tap_level = min(game.tap_level, 3000)
        for key in game.upgrades:
            limit = next(u[4] for u in SOUL_UPGRADES if u[0] == key)
            game.upgrades[key] = int(bounded(data.get("upgrades", {}).get(key, 0), maximum=limit))
        for key in METRICS:
            game.stats[key] = int(bounded(data.get("stats", {}).get(key, 0), maximum=1e15))
        game.stats["best_zone"] = max(game.zone, game.stats["best_zone"])
        game.items = {i["id"]: int(bounded(data.get("items", {}).get(i["id"], 0), maximum=50))
                      for i in ITEMS if data.get("items", {}).get(i["id"], 0) > 0}
        game.items.setdefault("knocker", 1)
        for slot in game.equipment:
            value = data.get("equipment", {}).get(slot)
            valid = next((i for i in ITEMS if i["id"]==value and i["slot"]==slot), None)
            game.equipment[slot] = value if valid and value in game.items else ("knocker" if slot=="weapon" else None)
        ids = set()
        game.pets = []
        for p in data.get("pets", [])[:240]:
            if not isinstance(p, dict): continue
            pid = max(1, int(bounded(p.get("id"), 1, 1000000000)))
            if pid in ids: continue
            ids.add(pid)
            game.pets.append(dict(id=pid, egg=int(bounded(p.get("egg"), maximum=len(EGGS)-1)),
                                  rarity=int(bounded(p.get("rarity"), maximum=5)),
                                  stars=max(1, int(bounded(p.get("stars"), 1, 8))), shiny=bool(p.get("shiny", False))))
        game.next_pet_id = max(ids, default=0)+1
        game.equipped_pets = list(dict.fromkeys(x for x in data.get("equipped_pets", []) if x in ids))[:game.pet_slots()]
        game.pity = [int(bounded(x, maximum=1e9)) for x in data.get("pity", [])[:len(EGGS)]]
        game.pity += [0]*(len(EGGS)-len(game.pity))
        game.claimed = [a[0] for a in ACHIEVEMENTS if a[0] in data.get("claimed", [])]
        game.auto_progress = bool(data.get("auto_progress", True))
        game.zone_kills = int(bounded(data.get("zone_kills", 0), maximum=4))
        for key in game.cooldowns:
            game.cooldowns[key] = float(bounded(data.get("cooldowns", {}).get(key, 0), maximum=ABILITIES[key][1]))
            game.buffs[key] = float(bounded(data.get("buffs", {}).get(key, 0), maximum=ABILITIES[key][2]))
        settings = data.get("settings", {})
        for key in ("sound", "music", "motion", "particles", "tutorial"):
            game.settings[key] = bool(settings.get(key, game.settings[key]))
        game.settings["fps"] = 30 if settings.get("fps") == 30 else 60
        game.settings["volume"] = float(bounded(settings.get("volume", .3), .3, 1))
        game.make_contracts()
        saved_contracts = data.get("contracts", [])
        if isinstance(saved_contracts, list) and len(saved_contracts)==3:
            for c, original in zip(game.contracts, saved_contracts):
                if isinstance(original, dict) and original.get("metric") in METRICS:
                    c["metric"] = original["metric"]
                    c["label"] = str(original.get("label", c["label"]))[:60]
                    c["start"] = int(bounded(original.get("start", 0), maximum=1e15))
                    c["goal"] = max(1, int(bounded(original.get("goal", 1), 1, 1e9)))
                    c["claimed"] = bool(original.get("claimed", False))
                    c["gems"] = int(bounded(original.get("gems", 20), 20, 1000000))
        game.new_enemy()
        game.hp = max(.001, min(game.max_hp, bounded(data.get("hp", game.max_hp), game.max_hp)))
        game.boss_time = max(.01, bounded(data.get("boss_time", game.boss_time), game.boss_time, game.boss_time))
        failed = data.get("failed_boss")
        game.failed_boss = int(failed) if isinstance(failed, int) and 1<=failed<=game.max_zone else None
        game.invalidate()
        return game
