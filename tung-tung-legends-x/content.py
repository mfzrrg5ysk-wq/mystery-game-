"""Tung Tung TungLegendss X -- original, offline game content."""

TITLE = "Tung Tung TungLegendss X"
VERSION = "1.0.0"
REALM_SIZE = 100
REALMS = [
    ("Bamboo Outskirts", "Every legend starts with a very loud stick.", (134, 198, 96), "forest"),
    ("Neon Night Market", "The market never sleeps. Neither do the drums.", (255, 126, 145), "city"),
    ("Sunken Drumlands", "Something is knocking beneath the water.", (92, 208, 224), "water"),
    ("Ember Foundry", "Forge a rhythm that can split the furnace.", (255, 164, 78), "forge"),
    ("Candy Catacombs", "Sweet loot. Extremely unreasonable guardians.", (236, 157, 235), "candy"),
    ("Clockwork Citadel", "Time is a resource. Spend it loudly.", (242, 214, 125), "city"),
    ("Frozen Echo", "Even the ice remembers your last hit.", (151, 211, 255), "ice"),
    ("Storm Monastery", "One thousand strikes. One perfect thunderclap.", (178, 158, 255), "storm"),
    ("Moonwood Sanctuary", "The oldest tungs grow under a crooked moon.", (133, 236, 185), "forest"),
    ("Void Arcade", "Insert rhythm. Challenge the impossible.", (208, 132, 255), "space"),
    ("Astral Drum Throne", "The throne belongs to whoever keeps the beat.", (255, 219, 130), "space"),
    ("Legend's Last Knock", "The campaign ends. Your legend does not.", (218, 255, 100), "space"),
]

# Name, hire cost, base DPS, flavor. Milestones every 25 levels double output.
HEROES = [
    ("Stick Intern", 15, 1.6, "Unpaid. Unstoppable."),
    ("Bamboo Brawler", 100, 9, "Two hands. One job."),
    ("Drum Courier", 650, 53, "Same-day knock delivery."),
    ("Night Watcher", 4200, 300, "The original midnight shift."),
    ("Tung Engineer", 28000, 1800, "Optimizes the bonk."),
    ("Echo Monk", 190000, 11000, "Quiet mind. Loud stick."),
    ("Bass Buccaneer", 1300000, 72000, "Pirates every single beat."),
    ("Furnace Captain", 9000000, 450000, "Heat-treated determination."),
    ("Tempo Witch", 65000000, 3000000, "A suspiciously catchy spell."),
    ("Thunder Marshal", 480000000, 21000000, "Arrested for excessive rhythm."),
    ("Void Conductor", 3600000000, 145000000, "Conducts an empty orchestra."),
    ("Moonwood Titan", 28000000000, 1000000000, "The forest hits back."),
    ("Astral Drummer", 220000000000, 7300000000, "Audible from another dimension."),
    ("Chrono Sovereign", 1800000000000, 53000000000, "Always one beat ahead."),
    ("The First Tung", 15000000000000, 390000000000, "Before the name. Before the knock."),
    ("Legend X", 130000000000000, 2900000000000, "The final hire. The first real legend."),
]

RARITIES = [
    ("Common", 58, 1.12, (154, 178, 183)),
    ("Uncommon", 24, 1.25, (141, 221, 139)),
    ("Rare", 12, 1.48, (107, 194, 255)),
    ("Epic", 5, 1.9, (199, 151, 255)),
    ("Legendary", .9, 2.9, (255, 213, 108)),
    ("Mythic", .1, 4.6, (255, 128, 173)),
]
EGGS = [
    ("Bamboo Egg", 30, 1, (151, 225, 134)),
    ("Neon Egg", 65, 100, (252, 141, 208)),
    ("Ocean Egg", 115, 200, (102, 221, 233)),
    ("Furnace Egg", 180, 300, (255, 173, 91)),
    ("Astral Egg", 280, 600, (186, 169, 255)),
    ("Legend X Egg", 420, 1000, (219, 255, 112)),
]
PET_NAMES = [
    ["Twiglet", "Bamboozle", "Drum Duck", "Echo Fox", "Crown Stump", "Worldroot"],
    ["Glow Slug", "Neon Noodle", "Bass Bat", "Pixel Panther", "Disco Dragon", "Night Emperor"],
    ["Bubble Bun", "Clam Jam", "Tide Turtle", "Reef Raptor", "Pearl Phoenix", "Abyss Whale"],
    ["Coal Cub", "Cinder Crab", "Anvil Ant", "Forge Falcon", "Molten Lion", "Inferno Wyrm"],
    ["Star Sprout", "Moon Moth", "Comet Cat", "Orbit Owl", "Nebula Serpent", "Astral Leviathan"],
    ["Xling", "Rune Rabbit", "Legend Lynx", "Throne Tiger", "Infinity Griffin", "The Last Echo"],
]

# Each slot carries one item. Unlocks/crafting survive both prestige layers.
ITEMS = [
    dict(id="knocker", name="Wooden Knocker", slot="weapon", zone=1, price=0,
         click=0.30, idle=0, gold=0, boss=0, ability=None, color=(218, 181, 134),
         desc="Boosts click power. Ranks strengthen the bonus."),
    dict(id="twin", name="Twin Bamboo", slot="weapon", zone=20, price=25,
         click=.60, idle=.12, gold=0, boss=0, ability="frenzy", color=(166, 223, 142),
         desc="Frenzy: 3x clicks for 12 seconds."),
    dict(id="storm", name="Storm Hammer", slot="weapon", zone=120, price=100,
         click=1.0, idle=.25, gold=0, boss=.15, ability="thunder", color=(160, 187, 255),
         desc="Thunder: a huge instant damage strike."),
    dict(id="scythe", name="Rift Scythe", slot="weapon", zone=400, price=240,
         click=1.6, idle=.40, gold=0, boss=.50, ability="rift", color=(203, 154, 255),
         desc="Rift Cut: stronger burst against bosses."),
    dict(id="spoon", name="Golden Spoon", slot="charm", zone=40, price=45,
         click=.10, idle=0, gold=.50, boss=0, ability="gold", color=(255, 217, 110),
         desc="Gold Rush: 3x coins for 20 seconds."),
    dict(id="echo", name="Echo Bell", slot="charm", zone=180, price=140,
         click=.25, idle=.40, gold=.20, boss=0, ability="echo", color=(255, 171, 183),
         desc="Echo: free auto-strikes for 15 seconds."),
    dict(id="tempo", name="Tempo Engine", slot="engine", zone=70, price=70,
         click=0, idle=.60, gold=0, boss=0, ability="overdrive", color=(123, 226, 215),
         desc="Overdrive: 3x hero DPS for 20 seconds."),
    dict(id="chrono", name="Chrono Heart", slot="engine", zone=300, price=200,
         click=.25, idle=1.10, gold=.15, boss=.10, ability="overdrive", color=(243, 216, 139),
         desc="A stronger engine with the same Overdrive."),
    dict(id="crown", name="Tung Crown", slot="relic", zone=100, price=95,
         click=.30, idle=.30, gold=.15, boss=.25, ability=None, color=(255, 217, 118),
         desc="Click, idle, gold, and boss damage bonuses."),
    dict(id="void", name="Void Sigil", slot="relic", zone=600, price=320,
         click=.60, idle=.75, gold=.30, boss=.50, ability=None, color=(209, 154, 255),
         desc="Late-game power in every department."),
    dict(id="legend", name="Legend X Core", slot="relic", zone=1000, price=500,
         click=1.0, idle=1.30, gold=.50, boss=.85, ability=None, color=(218, 255, 110),
         desc="The strongest campaign relic. Keep upgrading."),
]
ABILITIES = {
    "slam": ("TUNG SLAM", 14, 0, "12x click burst. Always available."),
    "frenzy": ("FRENZY", 45, 12, "3x click damage for 12 seconds."),
    "thunder": ("THUNDER", 40, 0, "25x click + 8 seconds of hero DPS."),
    "rift": ("RIFT CUT", 55, 0, "30x click + 12s DPS; double on bosses."),
    "gold": ("GOLD RUSH", 70, 20, "3x coins for 20 seconds."),
    "echo": ("ECHO", 65, 15, "Adds 5 auto-clicks per second for 15 seconds."),
    "overdrive": ("OVERDRIVE", 70, 20, "3x hero damage for 20 seconds."),
}
SOUL_UPGRADES = [
    ("click", "Heavy Hands", 2, 1.6, 30, "+20% click power per rank."),
    ("idle", "Endless Rhythm", 2, 1.6, 30, "+20% hero DPS per rank."),
    ("gold", "Golden Beat", 3, 1.7, 25, "+15% coins per rank."),
    ("boss", "Crown Breaker", 3, 1.7, 25, "+20% boss damage per rank."),
    ("slots", "Pet Formation", 12, 3, 2, "+1 equipped pet per rank (max 5)."),
    ("auto", "Auto Knocker", 15, 1, 1, "Permanently enables 4 auto-clicks/sec."),
    ("offline", "Dream Farmer", 4, 1.8, 10, "+5% offline efficiency per rank."),
    ("start", "Head Start", 3, 1.6, 20, "Start rebirths with more coins."),
    ("luck", "Lucky Shell", 6, 1.9, 10, "Moves egg odds toward higher rarities."),
    ("time", "Borrowed Time", 3, 1.7, 15, "+2 seconds on boss timers per rank."),
]
# id, title, metric, goal, gem reward
ACHIEVEMENTS = [
    ("first", "First Knock", "clicks", 1, 10),
    ("hundred", "Knock Knock Knock", "clicks", 100, 25),
    ("thousand", "Persistent Percussion", "clicks", 1000, 50),
    ("clicklord", "The Click Sovereign", "clicks", 10000, 150),
    ("farm100", "Local Farmer", "kills", 100, 25),
    ("farm1k", "Tung Harvester", "kills", 1000, 60),
    ("farm10k", "Industrial Bonking", "kills", 10000, 160),
    ("farm100k", "A Very Loud Career", "kills", 100000, 400),
    ("boss10", "Crown Collector", "bosses", 10, 50),
    ("boss100", "Royal Demolition", "bosses", 100, 160),
    ("pet1", "Best Friend", "hatches", 1, 15),
    ("pet30", "A Small Zoo", "hatches", 30, 100),
    ("pet100", "Hatch Master", "hatches", 100, 250),
    ("fusion", "Better Together", "fusions", 1, 30),
    ("rebirth1", "Back With a Beat", "rebirths", 1, 60),
    ("rebirth10", "Born to Knock", "rebirths", 10, 200),
    ("zone100", "Out of the Woods", "best_zone", 100, 80),
    ("zone300", "Three Realms Deep", "best_zone", 300, 160),
    ("zone600", "Beyond the Clock", "best_zone", 600, 250),
    ("zone1000", "An Actual Legend", "best_zone", 1000, 400),
    ("zone1200", "Campaign Conqueror", "best_zone", 1201, 600),
    ("ascend1", "The Next Dimension", "ascensions", 1, 200),
]

ENEMY_NAMES = ["Tung Sapling", "Wandering Tung", "Knockwood Scout", "Bamboo Bruiser", "Tung Sentinel"]
BOSS_NAMES = ["The Crowned Stump", "Midnight Bonklord", "The Deep Drummer", "Furnace Tyrant",
              "Sugar Sovereign", "Clockwork Colossus", "The Frozen Knock", "Thunder Abbot",
              "Moonwood Ancient", "Void Headliner", "Astral Emperor", "Legend X Prime"]
