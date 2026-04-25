import sqlite3
from datetime import datetime

DB_FILE = "dota_bot.db"

def init_db():
    """Ініціалізує базу даних при запуску"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            match_id TEXT NOT NULL,
            hero TEXT,
            result TEXT,
            gpm INTEGER,
            xpm INTEGER,
            kills INTEGER,
            deaths INTEGER,
            assists INTEGER,
            duration INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_match(user_id: int, match_id: str, hero: str, result: str,
               gpm: int, xpm: int, kills: int, deaths: int, assists: int, duration: int):
    """Зберігає матч в БД"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Не зберігаємо дублікати
    cur.execute("SELECT id FROM matches WHERE user_id=? AND match_id=?", (user_id, match_id))
    if cur.fetchone():
        conn.close()
        return
    cur.execute("""
        INSERT INTO matches (user_id, match_id, hero, result, gpm, xpm, kills, deaths, assists, duration, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, match_id, hero, result, gpm, xpm, kills, deaths, assists, duration,
          datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_user_matches(user_id: int, limit: int = 10) -> list:
    """Повертає останні матчі користувача з БД"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT match_id, hero, result, gpm, xpm, kills, deaths, assists, duration, timestamp
        FROM matches WHERE user_id=?
        ORDER BY id DESC LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_stats(user_id: int) -> dict:
    """Загальна статистика користувача"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) as wins,
            AVG(gpm) as avg_gpm,
            AVG(xpm) as avg_xpm,
            AVG(kills) as avg_kills,
            AVG(deaths) as avg_deaths,
            AVG(assists) as avg_assists
        FROM matches WHERE user_id=?
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] == 0:
        return {}
    return {
        "total": row[0],
        "wins": row[1] or 0,
        "avg_gpm": round(row[2] or 0),
        "avg_xpm": round(row[3] or 0),
        "avg_kills": round(row[4] or 0, 1),
        "avg_deaths": round(row[5] or 0, 1),
        "avg_assists": round(row[6] or 0, 1),
    }
