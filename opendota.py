import requests

BASE = "https://api.opendota.com/api"

HEROES = {
    1:"Anti-Mage",2:"Axe",3:"Bane",4:"Bloodseeker",5:"Crystal Maiden",
    6:"Drow Ranger",7:"Earthshaker",8:"Juggernaut",9:"Mirana",10:"Morphling",
    11:"Shadow Fiend",12:"Phantom Lancer",13:"Puck",14:"Pudge",15:"Razor",
    16:"Sand King",17:"Storm Spirit",18:"Sven",19:"Tiny",20:"Vengeful Spirit",
    21:"Windranger",22:"Zeus",23:"Kunkka",25:"Lina",26:"Lion",
    27:"Shadow Shaman",28:"Slardar",29:"Tidehunter",30:"Witch Doctor",31:"Lich",
    32:"Riki",33:"Enigma",34:"Tinker",35:"Sniper",36:"Necrophos",
    37:"Warlock",38:"Beastmaster",39:"Queen of Pain",40:"Venomancer",41:"Faceless Void",
    42:"Wraith King",43:"Death Prophet",44:"Phantom Assassin",45:"Pugna",46:"Templar Assassin",
    47:"Viper",48:"Luna",49:"Dragon Knight",50:"Dazzle",51:"Clockwerk",
    52:"Leshrac",53:"Nature's Prophet",54:"Lifestealer",55:"Dark Seer",56:"Clinkz",
    57:"Omniknight",58:"Enchantress",59:"Huskar",60:"Night Stalker",61:"Broodmother",
    62:"Bounty Hunter",63:"Weaver",64:"Jakiro",65:"Batrider",66:"Chen",
    67:"Spectre",68:"Ancient Apparition",69:"Doom",70:"Ursa",71:"Spirit Breaker",
    72:"Gyrocopter",73:"Alchemist",74:"Invoker",75:"Silencer",76:"Outworld Destroyer",
    77:"Lycan",78:"Brewmaster",79:"Shadow Demon",80:"Lone Druid",81:"Chaos Knight",
    82:"Meepo",83:"Treant Protector",84:"Ogre Magi",85:"Undying",86:"Rubick",
    87:"Disruptor",88:"Nyx Assassin",89:"Naga Siren",90:"Keeper of the Light",91:"Io",
    92:"Visage",93:"Slark",94:"Medusa",95:"Troll Warlord",96:"Centaur Warrunner",
    97:"Magnus",98:"Timbersaw",99:"Bristleback",100:"Tusk",101:"Skywrath Mage",
    102:"Abaddon",103:"Elder Titan",104:"Legion Commander",105:"Techies",106:"Ember Spirit",
    107:"Earth Spirit",108:"Underlord",109:"Terrorblade",110:"Phoenix",111:"Oracle",
    112:"Winter Wyvern",113:"Arc Warden",114:"Monkey King",120:"Pangolier",121:"Dark Willow",
    123:"Grimstroke",126:"Void Spirit",128:"Snapfire",129:"Mars",135:"Dawnbreaker",
    136:"Marci",137:"Primal Beast",138:"Muerta"
}

ITEMS = {
    1:"Blink Dagger",2:"Blades of Attack",3:"Broadsword",4:"Chainmail",5:"Claymore",
    6:"Helm of Iron Will",7:"Javelin",8:"Mithril Hammer",9:"Platemail",10:"Quelling Blade",
    11:"Ring of Protection",12:"Gauntlets of Strength",13:"Slippers of Agility",
    14:"Mantle of Intelligence",15:"Iron Branch",16:"Belt of Strength",17:"Band of Elvenskin",
    18:"Robe of the Magi",19:"Circlet",20:"Ogre Axe",21:"Blade of Alacrity",
    22:"Staff of Wizardry",23:"Ultimate Orb",24:"Gloves of Haste",25:"Morbid Mask",
    26:"Ring of Regen",27:"Sobi Mask",28:"Boots of Speed",29:"Gem of True Sight",
    30:"Cloak",31:"Talisman of Evasion",32:"Ghost Scepter",33:"Clarity",34:"Flask",
    35:"Dust of Appearance",36:"Town Portal Scroll",37:"Smoke of Deceit",
    40:"Oblivion Staff",41:"Perseverance",42:"Point Booster",43:"Energy Booster",
    44:"Vitality Booster",45:"Reaver",46:"Robe of the Magi",50:"Null Talisman",
    51:"Wraith Band",52:"Bracer",53:"Soul Ring",54:"Arcane Boots",55:"Phase Boots",
    56:"Power Treads",57:"Tranquil Boots",58:"Boots of Travel",63:"Maelstrom",
    64:"Helm of the Dominator",65:"Mask of Madness",66:"Satanic",67:"Mjollnir",
    68:"Crystalys",69:"Daedalus",72:"Dragon Lance",73:"Falcon Blade",74:"Diffusal Blade",
    75:"Ethereal Blade",76:"Soul Booster",77:"Hood of Defiance",78:"Pipe of Insight",
    79:"Blade Mail",80:"Sange",81:"Yasha",82:"Kaya",83:"Sange and Yasha",84:"Kaya and Sange",
    85:"Yasha and Kaya",88:"Manta Style",89:"Lothar's Edge",90:"Sphere",91:"Mystic Staff",
    92:"Scythe of Vyse",93:"Orchid Malevolence",96:"Rod of Atos",97:"Force Staff",
    98:"Hurricane Pike",100:"Shiva's Guard",102:"Bloodstone",103:"Linken's Sphere",
    104:"Butterfly",105:"Radiance",106:"Skull Basher",107:"Battle Fury",108:"Monkey King Bar",
    109:"Black King Bar",110:"Assault Cuirass",112:"Heart of Tarrasque",116:"Eul's Scepter",
    119:"Aghanim's Scepter",121:"Refresher Orb",123:"Vanguard",125:"Crimson Guard",
    127:"Mekansm",128:"Guardian Greaves",131:"Aeon Disk",133:"Dagon",135:"Necronomicon",
    137:"Octarine Core",145:"Nullifier",147:"Dragon Lance",152:"Quass and Blade",
    168:"Witch Blade",180:"Gleipnir",185:"Eternal Shroud",188:"Boots of Bearing",
    190:"Phylactery",192:"Pavise",194:"Fallen Sky",197:"Revenant's Brooch",
    200:"Disperser",201:"Harpoon",202:"Parasma",203:"Dawnbreaker's Beacon",
    204:"Arcanist's Armor",206:"Sniper's Rifle",208:"Overwhelming Blink",
    210:"Swift Blink",212:"Arcane Blink"
}

def get_hero_name(hero_id: int) -> str:
    return HEROES.get(hero_id, f"Hero #{hero_id}")

def get_item_name(item_id: int) -> str:
    return ITEMS.get(item_id, None)

def fetch_match(match_id: str) -> dict:
    """Завантажує повні дані матчу"""
    resp = requests.get(f"{BASE}/matches/{match_id}", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if "players" not in data:
        raise ValueError("Матч не знайдено або профіль приватний")
    return data

def fetch_player_matches(steam_id: str, limit: int = 10) -> list:
    """Останні матчі гравця"""
    resp = requests.get(f"{BASE}/players/{steam_id}/matches?limit={limit}", timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_player_profile(steam_id: str) -> dict:
    """Профіль гравця"""
    resp = requests.get(f"{BASE}/players/{steam_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_hero_benchmarks(hero_id: int) -> dict:
    """Середні показники по герою (GPM, XPM тощо)"""
    try:
        resp = requests.get(f"{BASE}/benchmarks?hero_id={hero_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}

def get_player_items(player: dict) -> list:
    """Витягує список предметів гравця"""
    items = []
    for slot in ["item_0","item_1","item_2","item_3","item_4","item_5"]:
        item_id = player.get(slot, 0)
        if item_id:
            name = get_item_name(item_id)
            if name:
                items.append(name)
    return items

def get_gold_graph(player: dict, duration_min: int) -> str:
    """Будує текстовий графік золота по хвилинах"""
    gold_t = player.get("gold_t", [])
    if not gold_t:
        return "Дані недоступні"

    lines = []
    step = max(1, len(gold_t) // 10)
    for i in range(0, min(len(gold_t), duration_min + 1), step):
        gold = gold_t[i]
        bar_len = min(20, gold // 500)
        bar = "█" * bar_len
        lines.append(f"{i:>2}хв | {bar} {gold}")
    return "\n".join(lines)

def get_benchmark_value(benchmarks: dict, field: str, percentile: float = 0.5) -> float:
    """Повертає значення бенчмарку для заданого поля"""
    try:
        result = benchmarks.get("result", {})
        data = result.get(field, [])
        # Знаходимо найближчий перцентиль
        for item in data:
            if abs(item.get("percentile", 0) - percentile) < 0.1:
                return item.get("value", 0)
        return 0
    except Exception:
        return 0
