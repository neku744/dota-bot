import re
import os
from groq import Groq
from opendota import get_hero_name, get_player_items, get_gold_graph, get_benchmark_value

def clean_markdown(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s?', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask(prompt: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.7
    )
    return clean_markdown(response.choices[0].message.content)

def analyze_match(match: dict, player_index: int, benchmarks: dict = {}) -> str:
    p = match["players"][player_index]
    hero = get_hero_name(p.get("hero_id", 0))
    team = "Radiant" if player_index < 5 else "Dire"
    won = (team == "Radiant" and match.get("radiant_win")) or \
          (team == "Dire" and not match.get("radiant_win"))
    dur = round(match.get("duration", 0) / 60)

    kills = p.get("kills", 0)
    deaths = p.get("deaths", 0)
    assists = p.get("assists", 0)
    gpm = round(p.get("gold_per_min", 0))
    xpm = round(p.get("xp_per_min", 0))
    lh = p.get("last_hits", 0)
    dn = p.get("denies", 0)
    hero_dmg = round(p.get("hero_damage", 0))
    tower_dmg = round(p.get("tower_damage", 0))
    taken_dmg = round(p.get("damage_taken", 0))
    healing = round(p.get("hero_healing", 0))
    nw = round(p.get("net_worth", 0) / 1000)
    purchase = p.get("purchase") or {}
    wards = purchase.get("ward_observer", 0) + purchase.get("ward_sentry", 0)
    stacks = p.get("camps_stacked", 0)
    stuns = round(p.get("stuns", 0))
    buybacks = p.get("buyback_count", 0)
    lh_pm = round(lh / max(1, dur), 1)
    items = get_player_items(p)
    gold_graph = get_gold_graph(p, dur)

    avg_gpm = round(get_benchmark_value(benchmarks, "gold_per_min"))
    avg_xpm = round(get_benchmark_value(benchmarks, "xp_per_min"))
    avg_lh = round(get_benchmark_value(benchmarks, "last_hits"))
    bench_info = ""
    if avg_gpm:
        bench_info = f"""
Середні показники по герою {hero} (50-й перцентиль):
GPM: {avg_gpm} (у гравця: {gpm}, різниця: {gpm - avg_gpm:+})
XPM: {avg_xpm} (у гравця: {xpm}, різниця: {xpm - avg_xpm:+})
Last hits: {avg_lh} (у гравця: {lh}, різниця: {lh - avg_lh:+})"""

    items_str = ", ".join(items) if items else "немає даних"

    prompt = f"""Ти — топ-тренер Dota 2 з 10+ роками досвіду. Проаналізуй гравця детально.

Матч #{match.get('match_id')} | {dur} хв | {"ПЕРЕМОГА" if won else "ПОРАЗКА"}
Герой: {hero} ({team})
K/D/A: {kills}/{deaths}/{assists}
GPM: {gpm} | XPM: {xpm}
Last hits: {lh} ({lh_pm}/хв) | Denies: {dn}
Дамаг по героях: {hero_dmg} | По вежах: {tower_dmg}
Отриманий дамаг: {taken_dmg} | Лікування: {healing}
Net worth: {nw}k
Варди: {wards} | Стаки: {stacks} | Stuns: {stuns}с | Buybacks: {buybacks}
Предмети: {items_str}
{bench_info}

Графік золота:
{gold_graph}

Напиши аналіз українською мовою ТІЛЬКИ простим текстом без зірочок і решіток:

ЗАГАЛЬНЕ ВРАЖЕННЯ
[3 речення з цифрами]

ПОМИЛКИ ТА ЗОНИ РОСТУ
[КРИТИЧНО / Є ПРОБЛЕМА / Є КУДИ РОСТИ] — Назва — Фаза: Лейнінг/Мід-гейм/Лейт-гейм
[Пояснення з цифрами + порада]
[4-6 помилок]

АНАЛІЗ ІНВЕНТАРЮ
[Чи правильний білд для {hero}? Що варто змінити?]

ЩО ЗРОБЛЕНО ДОБРЕ
[2-3 сильні сторони з цифрами]

ГОЛОВНА ПОРАДА
[Одна найважливіша порада]"""

    return ask(prompt)

def analyze_hero_tips(hero_name: str) -> str:
    prompt = f"""Ти — топ-тренер Dota 2. Дай детальні поради по герою {hero_name} українською мовою.
Тільки простий текст без зірочок і решіток.

РОЛЬ В КОМАНДІ
[яку роль виконує герой]

ФАЗИ ГРИ
Лейнінг: [що робити]
Мід-гейм: [що робити]
Лейт-гейм: [що робити]

ОПТИМАЛЬНИЙ БІЛД
Стартові предмети: [список]
Ранні предмети: [список]
Основні предмети: [список]
Сітуативні: [список]

ОСНОВНІ ПОМИЛКИ НОВАЧКІВ
[3-4 типові помилки]

ГОЛОВНА ПОРАДА
[найважливіша порада]"""

    return ask(prompt)

def analyze_compare(match1: dict, match2: dict, p1_idx: int, p2_idx: int) -> str:
    p1 = match1["players"][p1_idx]
    p2 = match2["players"][p2_idx]

    def fmt(p, match, idx):
        hero = get_hero_name(p.get("hero_id", 0))
        team = "Radiant" if idx < 5 else "Dire"
        won = (team == "Radiant" and match.get("radiant_win")) or \
              (team == "Dire" and not match.get("radiant_win"))
        dur = round(match.get("duration", 0) / 60)
        return (f"Герой: {hero} | {'Перемога' if won else 'Поразка'} | {dur} хв\n"
                f"K/D/A: {p.get('kills',0)}/{p.get('deaths',0)}/{p.get('assists',0)}\n"
                f"GPM: {round(p.get('gold_per_min',0))} | XPM: {round(p.get('xp_per_min',0))}\n"
                f"LH: {p.get('last_hits',0)} | Net worth: {round(p.get('net_worth',0)/1000)}k")

    prompt = f"""Ти — топ-тренер Dota 2. Порівняй два матчі гравця українською мовою.
Тільки простий текст без зірочок і решіток.

МАТЧ 1 (#{match1.get('match_id')}):
{fmt(p1, match1, p1_idx)}

МАТЧ 2 (#{match2.get('match_id')}):
{fmt(p2, match2, p2_idx)}

ПОРІВНЯННЯ ПОКАЗНИКІВ
[різниця по кожному параметру]

ЩО ПОКРАЩИЛОСЬ
[конкретні показники з цифрами]

ЩО ПОГІРШИЛОСЬ
[конкретні показники з цифрами]

ВИСНОВОК
[є прогрес чи ні, на що звернути увагу]"""

    return ask(prompt)

def generate_profile_summary(stats: dict, recent_matches: list) -> str:
    matches_str = "\n".join([
        f"- {m[1]} | {m[2]} | GPM:{m[3]} XPM:{m[4]} KDA:{m[5]}/{m[6]}/{m[7]}"
        for m in recent_matches[:5]
    ])

    prompt = f"""Ти — тренер Dota 2. Проаналізуй статистику гравця українською мовою.
Тільки простий текст без зірочок і решіток.

Загальна статистика:
Матчів: {stats.get('total',0)} | Перемог: {stats.get('wins',0)} | Winrate: {round(stats.get('wins',0)/max(1,stats.get('total',1))*100)}%
Середній GPM: {stats.get('avg_gpm',0)} | XPM: {stats.get('avg_xpm',0)}
Середній K/D/A: {stats.get('avg_kills',0)}/{stats.get('avg_deaths',0)}/{stats.get('avg_assists',0)}

Останні матчі:
{matches_str}

Дай коротке резюме: сильні сторони, слабкі сторони, головна порада."""

    return ask(prompt)
