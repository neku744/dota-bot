import os
import re
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler,
                           CallbackQueryHandler, filters, ContextTypes)

from opendota import (fetch_match, fetch_player_matches, fetch_player_profile,
                      fetch_hero_benchmarks, get_hero_name)
from analyzer import analyze_match, analyze_hero_tips, analyze_compare, generate_profile_summary
from database import init_db, save_match, get_user_matches, get_user_stats

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Тимчасове сховище даних між кроками (очищається при перезапуску)
user_matches = {}      # {user_id: match_data}
compare_data = {}      # {user_id: {"match1": ..., "step": ...}}


# ──────────────────────────────────────────
# ДОПОМІЖНІ ФУНКЦІЇ
# ──────────────────────────────────────────

def send_long(text: str, max_len: int = 4096) -> list:
    """Розбиває довгий текст на частини для Telegram"""
    parts = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    parts.append(text)
    return parts


def build_player_keyboard(match: dict) -> InlineKeyboardMarkup:
    """Будує клавіатуру для вибору гравця"""
    keyboard = []
    for i, p in enumerate(match["players"]):
        team = "[R]" if i < 5 else "[D]"
        hero = get_hero_name(p.get("hero_id", 0))
        won = (i < 5 and match.get("radiant_win")) or (i >= 5 and not match.get("radiant_win"))
        result = "W" if won else "L"
        label = f"{team} {hero} {p.get('kills',0)}/{p.get('deaths',0)}/{p.get('assists',0)} [{result}]"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"player_{i}")])
    return InlineKeyboardMarkup(keyboard)


# ──────────────────────────────────────────
# КОМАНДИ
# ──────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я аналізую матчі в Dota 2 за допомогою AI.\n\n"
        "Доступні команди:\n"
        "Просто надішли Match ID — аналіз конкретного матчу\n"
        "/profile — твоя статистика з збережених матчів\n"
        "/hero [герой] — поради по герою\n"
        "/compare [id1] [id2] — порівняти два матчі\n"
        "/history — останні проаналізовані матчі\n\n"
        "Надішли Match ID щоб почати:"
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показує збережені матчі користувача"""
    user_id = update.effective_user.id
    rows = get_user_matches(user_id, limit=10)
    if not rows:
        await update.message.reply_text(
            "Ще немає збережених матчів.\nПроаналізуй хоча б один матч — надішли Match ID."
        )
        return

    lines = ["Твої останні матчі:\n"]
    for r in rows:
        match_id, hero, result, gpm, xpm, k, d, a, dur, ts = r
        res_icon = "W" if result == "win" else "L"
        lines.append(f"[{res_icon}] {hero} | {k}/{d}/{a} | GPM:{gpm} | {dur}хв | #{match_id}")

    await update.message.reply_text("\n".join(lines))


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика гравця з БД"""
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    if not stats or stats.get("total", 0) == 0:
        await update.message.reply_text(
            "Немає даних. Спочатку проаналізуй кілька матчів — надішли Match ID."
        )
        return

    rows = get_user_matches(user_id, limit=5)
    msg = await update.message.reply_text("Аналізую твій профіль...")

    winrate = round(stats["wins"] / max(1, stats["total"]) * 100)
    header = (
        f"Профіль гравця\n"
        f"Матчів: {stats['total']} | Winrate: {winrate}%\n"
        f"Середній GPM: {stats['avg_gpm']} | XPM: {stats['avg_xpm']}\n"
        f"Середній K/D/A: {stats['avg_kills']}/{stats['avg_deaths']}/{stats['avg_assists']}\n"
        f"{'='*30}\n\n"
    )

    try:
        summary = generate_profile_summary(stats, rows)
        await msg.edit_text(header + summary)
    except Exception as e:
        await msg.edit_text(header + f"Помилка AI аналізу: {e}")


async def cmd_hero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поради по герою"""
    args = context.args
    if not args:
        await update.message.reply_text(
            "Вкажи героя. Приклад:\n/hero Invoker\n/hero Pudge\n/hero Crystal Maiden"
        )
        return

    hero_name = " ".join(args)
    msg = await update.message.reply_text(f"Готую поради по {hero_name}...")

    try:
        tips = analyze_hero_tips(hero_name)
        header = f"Поради по герою: {hero_name}\n{'='*30}\n\n"
        full = header + tips
        parts = send_long(full)
        await msg.edit_text(parts[0])
        for part in parts[1:]:
            await update.message.reply_text(part)
    except Exception as e:
        await msg.edit_text(f"Помилка: {e}")


async def cmd_compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Порівняти два матчі"""
    args = context.args
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await update.message.reply_text(
            "Вкажи два Match ID через пробіл. Приклад:\n/compare 8779517931 8780123456"
        )
        return

    msg = await update.message.reply_text("Завантажую обидва матчі...")
    user_id = update.effective_user.id

    try:
        match1 = fetch_match(args[0])
        match2 = fetch_match(args[1])
    except Exception as e:
        await msg.edit_text(f"Помилка завантаження: {e}")
        return

    # Зберігаємо матчі і просимо вибрати гравця з першого
    compare_data[user_id] = {"match1": match1, "match2": match2, "step": 1}
    await msg.edit_text(
        f"Матч 1 (#{match1['match_id']}) та Матч 2 (#{match2['match_id']}) завантажено.\n\n"
        "Обери СВОГО гравця з першого матчу:",
        reply_markup=build_player_keyboard(match1)
    )


# ──────────────────────────────────────────
# ОБРОБКА ПОВІДОМЛЕНЬ
# ──────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє Match ID надісланий користувачем"""
    text = update.message.text.strip()

    if not re.match(r'^\d{6,}$', text):
        await update.message.reply_text(
            "Надішли Match ID — це число, наприклад: 8779517931\n"
            "Або скористайся командами /hero, /compare, /profile"
        )
        return

    msg = await update.message.reply_text("Завантажую дані матчу з OpenDota...")
    user_id = update.effective_user.id

    try:
        match = fetch_match(text)
        user_matches[user_id] = match
        dur = round(match["duration"] / 60)
        winner = "Radiant" if match.get("radiant_win") else "Dire"

        await msg.edit_text(
            f"Матч #{match['match_id']} знайдено\n"
            f"Тривалість: {dur} хв | Переміг: {winner}\n\n"
            "Обери свого гравця:",
            reply_markup=build_player_keyboard(match)
        )
    except Exception as e:
        await msg.edit_text(f"Помилка: {str(e)}\nПеревір Match ID та спробуй ще раз.")


# ──────────────────────────────────────────
# CALLBACK КНОПКИ
# ──────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    # ── Вибір гравця для звичайного аналізу ──
    if data.startswith("player_") and user_id not in compare_data:
        player_index = int(data.split("_")[1])
        match = user_matches.get(user_id)
        if not match:
            await query.edit_message_text("Дані матчу не знайдено. Надішли Match ID знову.")
            return

        p = match["players"][player_index]
        hero = get_hero_name(p.get("hero_id", 0))
        team = "Radiant" if player_index < 5 else "Dire"
        won = (team == "Radiant" and match.get("radiant_win")) or \
              (team == "Dire" and not match.get("radiant_win"))
        dur = round(match.get("duration", 0) / 60)

        await query.edit_message_text(
            f"Аналізую гру на {hero}...\n"
            f"K/D/A: {p.get('kills',0)}/{p.get('deaths',0)}/{p.get('assists',0)} | "
            f"{'Перемога' if won else 'Поразка'}\n\n"
            "Зачекай кілька секунд..."
        )

        try:
            # Завантажуємо бенчмарки для порівняння
            benchmarks = fetch_hero_benchmarks(p.get("hero_id", 0))
            analysis = analyze_match(match, player_index, benchmarks)

            # Зберігаємо в БД
            save_match(
                user_id=user_id,
                match_id=str(match.get("match_id")),
                hero=hero,
                result="win" if won else "loss",
                gpm=round(p.get("gold_per_min", 0)),
                xpm=round(p.get("xp_per_min", 0)),
                kills=p.get("kills", 0),
                deaths=p.get("deaths", 0),
                assists=p.get("assists", 0),
                duration=dur
            )

            header = (
                f"Аналіз матчу #{match.get('match_id')}\n"
                f"Герой: {hero} ({team})\n"
                f"{'Перемога' if won else 'Поразка'} | {dur} хв\n"
                f"K/D/A: {p.get('kills',0)}/{p.get('deaths',0)}/{p.get('assists',0)} | "
                f"GPM: {round(p.get('gold_per_min',0))} | LH: {p.get('last_hits',0)}\n"
                f"{'='*30}\n\n"
            )

            parts = send_long(header + analysis)
            await query.edit_message_text(parts[0])
            for part in parts[1:]:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=part)

        except Exception as e:
            await query.edit_message_text(f"Помилка аналізу: {str(e)}")

    # ── Вибір гравця для /compare ──
    elif data.startswith("player_") and user_id in compare_data:
        player_index = int(data.split("_")[1])
        cd = compare_data[user_id]

        if cd["step"] == 1:
            # Зберігаємо вибір з першого матчу, просимо вибрати з другого
            cd["p1_idx"] = player_index
            cd["step"] = 2
            await query.edit_message_text(
                f"Обрано гравця з першого матчу.\n\n"
                "Тепер обери свого гравця з другого матчу:",
                reply_markup=build_player_keyboard(cd["match2"])
            )

        elif cd["step"] == 2:
            # Є обидва вибори — запускаємо порівняння
            p2_idx = player_index
            p1_idx = cd["p1_idx"]
            match1 = cd["match1"]
            match2 = cd["match2"]
            del compare_data[user_id]

            await query.edit_message_text("Порівнюю два матчі...")

            try:
                result = analyze_compare(match1, match2, p1_idx, p2_idx)
                header = (
                    f"Порівняння матчів\n"
                    f"#{match1['match_id']} vs #{match2['match_id']}\n"
                    f"{'='*30}\n\n"
                )
                parts = send_long(header + result)
                await query.edit_message_text(parts[0])
                for part in parts[1:]:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=part)
            except Exception as e:
                await query.edit_message_text(f"Помилка порівняння: {str(e)}")


# ──────────────────────────────────────────
# ЗАПУСК
# ──────────────────────────────────────────

def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CommandHandler("hero", cmd_hero))
    app.add_handler(CommandHandler("compare", cmd_compare))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Бот запущено!")
    app.run_polling()


if __name__ == "__main__":
    main()
