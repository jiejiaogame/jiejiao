# core.py - 完整版（含战力字段、音量字段、祈愿祝福、每日任务、宝石、占领等）
import asyncio
import sqlite3
import json
import hashlib
import random
import copy
from datetime import datetime, timedelta

DB_PATH = "honghuang.db"

# ---------- 密码哈希 ----------
def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

# ---------- 数据库初始化 ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        email TEXT,
        reg_time TEXT,
        gold INTEGER DEFAULT 1000,
        ingots INTEGER DEFAULT 100,
        heroes TEXT DEFAULT '[]',
        star_heroes TEXT DEFAULT '{}',
        hero_exp TEXT DEFAULT '{}',
        hero_level TEXT DEFAULT '{}',
        hero_free_points TEXT DEFAULT '{}',
        hero_bonus_attrs TEXT DEFAULT '{}',
        hero_gems TEXT DEFAULT '{}',
        items TEXT DEFAULT '{}',
        avatar TEXT DEFAULT 'hero.png',
        challenge_level INTEGER DEFAULT 0,
        challenge_date TEXT,
        recruit_shop TEXT,
        recruit_refresh_time TEXT,
        last_login_date TEXT,
        daily_gold INTEGER DEFAULT 0,
        daily_pvp_count INTEGER DEFAULT 0,
        formation TEXT DEFAULT '[]',
        formation_type TEXT DEFAULT 'normal',
        occupied_by TEXT,
        occupied_time TEXT,
        formations TEXT DEFAULT '{}',
        daily_tasks TEXT DEFAULT '{}',
        pray_count INTEGER DEFAULT 0,
        pray_date TEXT,
        temp_buff_expire TEXT,
        power INTEGER DEFAULT 0,
        volume INTEGER DEFAULT 70
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS friendships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1 TEXT NOT NULL,
        user2 TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        updated_at TEXT,
        UNIQUE(user1, user2)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_invites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user TEXT NOT NULL,
        to_user TEXT NOT NULL,
        room_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        expires_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS private_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user TEXT NOT NULL,
        to_user TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        is_read INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_rank (
        username TEXT PRIMARY KEY,
        avatar TEXT,
        daily_gold INTEGER DEFAULT 0,
        update_date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
        username TEXT NOT NULL,
        blocked_user TEXT NOT NULL,
        created_at TEXT,
        PRIMARY KEY (username, blocked_user)
    )''')
    
    # 确保新字段存在（兼容旧数据库）
    existing_columns = [col[1] for col in c.execute("PRAGMA table_info(users)")]
    new_columns = {
        "hero_exp": "TEXT DEFAULT '{}'",
        "hero_level": "TEXT DEFAULT '{}'",
        "hero_free_points": "TEXT DEFAULT '{}'",
        "hero_bonus_attrs": "TEXT DEFAULT '{}'",
        "hero_gems": "TEXT DEFAULT '{}'",
        "items": "TEXT DEFAULT '{}'",
        "formation": "TEXT DEFAULT '[]'",
        "formation_type": "TEXT DEFAULT 'normal'",
        "recruit_shop": "TEXT",
        "recruit_refresh_time": "TEXT",
        "occupied_by": "TEXT",
        "occupied_time": "TEXT",
        "daily_pvp_count": "INTEGER DEFAULT 0",
        "daily_gold": "INTEGER DEFAULT 0",
        "challenge_level": "INTEGER DEFAULT 0",
        "challenge_date": "TEXT",
        "last_login_date": "TEXT",
        "formations": "TEXT DEFAULT '{}'",
        "daily_tasks": "TEXT DEFAULT '{}'",
        "pray_count": "INTEGER DEFAULT 0",
        "pray_date": "TEXT",
        "temp_buff_expire": "TEXT",
        "power": "INTEGER DEFAULT 0",
        "volume": "INTEGER DEFAULT 70"
    }
    for col, col_type in new_columns.items():
        if col not in existing_columns:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
    
    c.execute("SELECT username FROM users WHERE username='GM01'")
    if not c.fetchone():
        gm_hash = hash_pwd("gm123456")
        now = datetime.now().isoformat()
        c.execute("""INSERT INTO users 
            (username, password, email, reg_time, gold, ingots, heroes, star_heroes, avatar, challenge_level)
            VALUES (?, ?, ?, ?, 100000, 1000, '[]', '{}', 'hero.png', 0)""",
            ("GM01", gm_hash, "admin@honghuang.com", now))
        c.execute("PRAGMA journal_mode=WAL")
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成（含天骄榜、音量字段）")

# ---------- 用户查询与更新 ----------
def get_user(username: str):
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    user_dict = {}
    for idx, col in enumerate(columns):
        value = row[idx] if idx < len(row) else None
        if value is None:
            if col in ("heroes", "star_heroes", "hero_exp", "hero_level", "hero_free_points", "hero_bonus_attrs", "hero_gems", "items", "recruit_shop", "formation", "formation_type", "formations", "daily_tasks"):
                value = "{}" if col not in ("heroes", "formation") else "[]"
            else:
                value = 0 if col in ("gold", "ingots", "challenge_level", "daily_gold", "daily_pvp_count", "pray_count", "power", "volume") else ""
        user_dict[col] = value
    conn.close()
    for field in ["heroes", "star_heroes", "hero_exp", "hero_level", "hero_free_points", "hero_bonus_attrs", "hero_gems", "items", "recruit_shop", "formation", "formations", "daily_tasks"]:
        if field in user_dict and isinstance(user_dict[field], str):
            try:
                user_dict[field] = json.loads(user_dict[field])
            except:
                if field == "heroes" or field == "formation":
                    user_dict[field] = []
                else:
                    user_dict[field] = {}
    return user_dict

def update_user_items(username: str, gold_delta: int, ingots_delta: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET gold = gold + ?, ingots = ingots + ? WHERE username=?", (gold_delta, ingots_delta, username))
    conn.commit()
    conn.close()

def save_user_items(username: str, items: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET items = ? WHERE username=?", (json.dumps(items, ensure_ascii=False), username))
    conn.commit()
    conn.close()

def create_user(username: str, password: str, email: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False
    hashed = hash_pwd(password)
    now = datetime.now().isoformat()
    heroes = json.dumps([])
    star_heroes = json.dumps({})
    hero_exp = json.dumps({})
    hero_level = json.dumps({})
    hero_free_points = json.dumps({})
    hero_bonus_attrs = json.dumps({})
    hero_gems = json.dumps({})
    items = json.dumps({})
    formation = json.dumps([])
    formations = json.dumps({})
    daily_tasks = json.dumps({})
    c.execute("""INSERT INTO users 
        (username, password, email, reg_time, gold, ingots, heroes, star_heroes, hero_exp, hero_level,
         hero_free_points, hero_bonus_attrs, hero_gems, items, avatar, challenge_level, daily_gold, daily_pvp_count, formation, formations, daily_tasks)
        VALUES (?, ?, ?, ?, 1000, 100, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)""",
        (username, hashed, email, now, heroes, star_heroes, hero_exp, hero_level,
         hero_free_points, hero_bonus_attrs, hero_gems, items, "hero.png", formation, formations, daily_tasks))
    conn.commit()
    conn.close()
    return True

def is_valid_email(email: str) -> bool:
    import re
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def filter_msg(msg: str) -> str:
    return msg

# ---------- 房间与全局变量 ----------
rooms = {}
users_ws = {}
room_timers = {}

_broadcast = None
_broadcast_room_state = None
_send_hand = None

def set_web_functions(broadcast_func, broadcast_state_func, send_hand_func, users_ws_dict):
    global _broadcast, _broadcast_room_state, _send_hand, users_ws
    _broadcast = broadcast_func
    _broadcast_room_state = broadcast_state_func
    _send_hand = send_hand_func
    users_ws = users_ws_dict

async def remove_player_from_room(room_id: str, username: str):
    pass

# ---------- 每日重置任务 ----------
async def daily_reset():
    while True:
        now = datetime.now()
        next_midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
        wait = (next_midnight - now).total_seconds()
        await asyncio.sleep(wait)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("UPDATE users SET challenge_level = 0, challenge_date = ?", (today,))
        c.execute("UPDATE users SET daily_pvp_count = 0")
        c.execute("DELETE FROM daily_rank")
        c.execute("UPDATE users SET daily_tasks = '{}'")
        conn.commit()
        conn.close()
        print("每日重置完成")

# ---------- 禁用配置（占位）----------
def load_disabled_config():
    return {"heroes": [], "cards": [], "seals": []}

def save_disabled_config(config):
    pass

# ---------- 武将经验与等级 ----------
def calc_level_by_exp(exp: int) -> tuple:
    level = 1
    while True:
        need = int(100 + 20*(level-1) + 1.5*(level**1.5))
        if exp < need:
            return level, exp, need
        exp -= need
        level += 1
        if level >= 100:
            return 100, 0, 0

def add_hero_exp(username: str, hero_name: str, exp_gain: int):
    user = get_user(username)
    if not user:
        return
    hero_exp = user.get("hero_exp", {})
    hero_level = user.get("hero_level", {})
    current_exp = hero_exp.get(hero_name, 0)
    new_exp = current_exp + exp_gain
    new_level, _, _ = calc_level_by_exp(new_exp)
    old_level = hero_level.get(hero_name, 1)
    hero_exp[hero_name] = new_exp
    hero_level[hero_name] = new_level
    free_points = user.get("hero_free_points", {})
    current_points = free_points.get(hero_name, 0)
    gained_points = ((new_level // 10) - (old_level // 10)) * 5
    if gained_points > 0:
        free_points[hero_name] = current_points + gained_points
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET hero_exp=?, hero_level=?, hero_free_points=? WHERE username=?",
              (json.dumps(hero_exp), json.dumps(hero_level), json.dumps(free_points), username))
    conn.commit()
    conn.close()

def allocate_free_point(username: str, hero_name: str, attr: str) -> bool:
    user = get_user(username)
    free_points = user.get("hero_free_points", {})
    points = free_points.get(hero_name, 0)
    if points <= 0:
        return False
    bonus_attrs = user.get("hero_bonus_attrs", {})
    if hero_name not in bonus_attrs:
        bonus_attrs[hero_name] = {"strength": 0, "intelligence": 0, "speed": 0, "hp": 0}
    if attr in bonus_attrs[hero_name]:
        bonus_attrs[hero_name][attr] += 1
    else:
        bonus_attrs[hero_name][attr] = 1
    free_points[hero_name] = points - 1
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET hero_free_points=?, hero_bonus_attrs=? WHERE username=?",
              (json.dumps(free_points), json.dumps(bonus_attrs), username))
    conn.commit()
    conn.close()
    return True

# ---------- 加载武将数据库 ----------
def load_heroes_db():
    try:
        with open("data/custom_heroes.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return {"heroes": []}

# ---------- 宝石系统 ----------
GEM_TYPES = {
    "strength": "力量宝石",
    "intelligence": "智力宝石",
    "speed": "敏捷宝石",
    "hp": "生命宝石"
}

def create_gem(attr: str, star: int, value: int = None) -> dict:
    if value is None:
        ranges = {1: (1,2), 2: (3,5), 3: (6,9), 4: (10,14), 5: (15,20)}
        min_v, max_v = ranges.get(star, (1,1))
        value = random.randint(min_v, max_v)
    return {
        "id": f"gem_{attr}_{star}_{value}_{random.randint(1000,9999)}",
        "name": GEM_TYPES.get(attr, "宝石"),
        "attr": attr,
        "star": star,
        "value": value,
        "double_attr": None,
        "count": 1
    }

def create_double_gem(attr1: str, value1: int, attr2: str, value2: int, star: int) -> dict:
    return {
        "id": f"gem_{attr1}_{attr2}_{star}_{random.randint(1000,9999)}",
        "name": GEM_TYPES.get(attr1, "宝石"),
        "attr": attr1,
        "value": value1,
        "double_attr": {"attr": attr2, "value": value2},
        "star": star,
        "count": 1
    }

def generate_random_gem() -> dict:
    attr = random.choice(list(GEM_TYPES.keys()))
    star = random.choices([1,2,3,4,5], weights=[0.4,0.3,0.2,0.08,0.02])[0]
    return create_gem(attr, star)

def add_gem_to_user(username: str, gem: dict):
    user = get_user(username)
    items = user.get("items", {})
    gem_id = gem["id"]
    if gem_id in items:
        items[gem_id]["count"] += 1
    else:
        items[gem_id] = gem
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET items = ? WHERE username=?", (json.dumps(items, ensure_ascii=False), username))
    conn.commit()
    conn.close()

def fuse_gems(username: str, gem_id1: str, gem_id2: str) -> dict:
    user = get_user(username)
    items = user.get("items", {})
    gem1 = items.get(gem_id1)
    gem2 = items.get(gem_id2)
    
    if not gem1 or not gem2:
        return {"success": False, "msg": "宝石不存在"}
    if gem1.get("double_attr") or gem2.get("double_attr"):
        return {"success": False, "msg": "双属性宝石无法融合"}

    star1 = gem1.get("star", 1)
    star2 = gem2.get("star", 1)
    attr1 = gem1.get("attr")
    attr2 = gem2.get("attr")

    if gem_id1 == gem_id2:
        if gem1.get("count", 1) < 2:
            return {"success": False, "msg": "同一宝石数量不足，无法取两个个体"}
        gem2 = copy.deepcopy(gem1)
        gem2["count"] = 1
        gem1["count"] -= 2
        if gem1["count"] <= 0:
            items.pop(gem_id1)
        else:
            items[gem_id1] = gem1
    else:
        if gem1.get("count", 1) == 1:
            items.pop(gem_id1)
        else:
            gem1["count"] -= 1
            items[gem_id1] = gem1
        if gem2.get("count", 1) == 1:
            items.pop(gem_id2)
        else:
            gem2["count"] -= 1
            items[gem_id2] = gem2

    if star1 != star2:
        return {"success": False, "msg": f"星级不同无法融合（{star1}星 ≠ {star2}星）"}
    if star1 < 1 or star1 > 4:
        return {"success": False, "msg": "只能融合1-4星宝石"}

    if attr1 == attr2:
        success_rates = {1: 0.9, 2: 0.7, 3: 0.6, 4: 0.4}
        success_rate = success_rates.get(star1, 0.5)
        if random.random() < success_rate:
            new_star = star1 + 1
            new_gem = create_gem(attr1, new_star)
            items[new_gem["id"]] = new_gem
            save_user_items(username, items)
            return {
                "success": True, 
                "msg": f"融合成功！消耗两颗{star1}星{attr1}宝石，获得{new_star}星{attr1}宝石 +{new_gem['value']}（成功率{int(success_rate*100)}%）"
            }
        else:
            save_user_items(username, items)
            return {
                "success": False, 
                "msg": f"融合失败，两颗{star1}星{attr1}宝石消失了（成功率{int(success_rate*100)}%）"
            }
    else:
        success_rate = 0.5
        if random.random() < success_rate:
            new_star = max(1, star1 - 1)
            new_gem = create_double_gem(attr1, gem1["value"], attr2, gem2["value"], new_star)
            items[new_gem["id"]] = new_gem
            save_user_items(username, items)
            return {
                "success": True, 
                "msg": f"融合成功！消耗两颗{star1}星宝石（{attr1}+{attr2}），获得{new_star}星双属性宝石（+{gem1['value']}{attr1} +{gem2['value']}{attr2}）"
            }
        else:
            save_user_items(username, items)
            return {
                "success": False, 
                "msg": f"融合失败，两颗{star1}星宝石（{attr1}+{attr2}）消失了"
            }

def decompose_gem(username: str, gem_id: str) -> dict:
    user = get_user(username)
    items = user.get("items", {})
    gem = items.get(gem_id)
    if not gem:
        return {"success": False, "msg": "宝石不存在"}
    if not gem.get("double_attr"):
        return {"success": False, "msg": "只有双属性宝石才能分解"}
    attr1 = gem["attr"]
    val1 = gem["value"]
    attr2 = gem["double_attr"]["attr"]
    val2 = gem["double_attr"]["value"]
    new_gem1 = create_gem(attr1, 2, val1)
    new_gem2 = create_gem(attr2, 2, val2)
    if gem.get("count", 1) > 1:
        gem["count"] -= 1
        items[gem_id] = gem
    else:
        items.pop(gem_id, None)
    items[new_gem1["id"]] = new_gem1
    items[new_gem2["id"]] = new_gem2
    save_user_items(username, items)
    return {"success": True, "msg": "分解成功", "gems": [new_gem1, new_gem2]}

def equip_gem(username: str, hero_name: str, gem_id: str, slot: int) -> dict:
    user = get_user(username)
    items = user.get("items", {})
    gem = items.get(gem_id)
    if not gem:
        return {"success": False, "msg": "宝石不存在"}
    
    hero_gems = user.get("hero_gems", {})
    if hero_name not in hero_gems:
        hero_gems[hero_name] = [None] * 5
    if slot < 0 or slot >= 5:
        return {"success": False, "msg": "无效槽位"}
    if hero_gems[hero_name][slot] is not None:
        return {"success": False, "msg": "该槽位已有宝石，请先卸下"}
    
    if gem.get("count", 1) > 1:
        gem["count"] -= 1
        new_gem = copy.deepcopy(gem)
        new_gem["id"] = f"{gem['id']}_{random.randint(10000, 99999)}"
        new_gem["count"] = 1
        items[gem_id] = gem
        items[new_gem["id"]] = new_gem
        used_gem_id = new_gem["id"]
    else:
        used_gem_id = gem_id
        items.pop(gem_id)
    
    hero_gems[hero_name][slot] = used_gem_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET hero_gems=?, items=? WHERE username=?", 
              (json.dumps(hero_gems), json.dumps(items), username))
    conn.commit()
    conn.close()
    return {"success": True, "msg": "镶嵌成功", "gem": items.get(used_gem_id, new_gem)}

# ---------- 占领机制 ----------
def occupy_user(occupier: str, target: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("UPDATE users SET occupied_by=?, occupied_time=? WHERE username=?", (occupier, now, target))
    conn.commit()
    conn.close()

def release_user(target: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET occupied_by=NULL, occupied_time=NULL WHERE username=?", (target,))
    conn.commit()
    conn.close()

def is_occupied(username: str) -> bool:
    user = get_user(username)
    occ = user.get("occupied_by")
    return occ not in (None, '')

def get_occupier(username: str) -> str or None:
    user = get_user(username)
    occ = user.get("occupied_by")
    return occ if occ not in (None, '') else None

def is_occupied_by(occupier: str, target: str) -> bool:
    user = get_user(target)
    occ = user.get("occupied_by")
    return occ == occupier and occ not in (None, '')

# ---------- 布阵 ----------
def save_formation(username: str, formation_type: str, formation: list):
    user = get_user(username)
    formations = user.get("formations", {})
    if not isinstance(formations, dict):
        formations = {}
    formations[formation_type] = formation
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET formations = ? WHERE username=?", (json.dumps(formations), username))
    conn.commit()
    conn.close()

def get_formation(username: str, formation_type: str = "normal") -> list:
    user = get_user(username)
    formations = user.get("formations", {})
    return formations.get(formation_type, [])

def save_formation_legacy(username: str, formation: list):
    save_formation(username, "normal", formation)

def get_formation_legacy(username: str) -> list:
    return get_formation(username, "normal")

def save_formation_type(username: str, formation_type: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET formation_type=? WHERE username=?", (formation_type, username))
    conn.commit()
    conn.close()

def get_formation_type(username: str) -> str:
    user = get_user(username)
    ft = user.get("formation_type", "normal")
    if isinstance(ft, str):
        return ft
    return "normal"

# ---------- 黑名单操作 ----------
def add_blacklist(username: str, blocked: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO blacklist (username, blocked_user, created_at) VALUES (?, ?, ?)",
              (username, blocked, now))
    conn.commit()
    conn.close()

def remove_blacklist(username: str, blocked: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM blacklist WHERE username=? AND blocked_user=?", (username, blocked))
    conn.commit()
    conn.close()

def get_blacklist(username: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT blocked_user FROM blacklist WHERE username=?", (username,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ---------- 每日任务系统 ----------
DAILY_TASKS_CONFIG = {
    "login": {"name": "每日登录", "desc": "今日登录游戏", "reward_ingots": 0, "reward_gold": 100, "need_count": 1},
    "self_pvp": {"name": "自我切磋", "desc": "进行1次自我切磋", "reward_ingots": 0, "reward_gold": 200, "need_count": 1},
    "friend_pvp": {"name": "好友切磋", "desc": "完成5次好友切磋（或匹配）", "reward_ingots": 1, "reward_gold": 0, "need_count": 5},
    "challenge": {"name": "副本挑战", "desc": "通关任意副本5次", "reward_ingots": 5, "reward_gold": 0, "need_count": 5},
    "shop": {"name": "商店购物", "desc": "在宝石商店购买1次", "reward_ingots": 10, "reward_gold": 0, "need_count": 1}
}

def get_daily_tasks_progress(username: str) -> dict:
    user = get_user(username)
    tasks = user.get("daily_tasks", {})
    if isinstance(tasks, str):
        tasks = json.loads(tasks)
    today = datetime.now().strftime("%Y-%m-%d")
    if tasks.get("date") != today:
        tasks = {
            "date": today,
            "login": {"current": 0, "claimed": False},
            "self_pvp": {"current": 0, "claimed": False},
            "friend_pvp": {"current": 0, "claimed": False},
            "challenge": {"current": 0, "claimed": False},
            "shop": {"current": 0, "claimed": False}
        }
        tasks["login"]["current"] = 1
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET daily_tasks=? WHERE username=?", (json.dumps(tasks), username))
        conn.commit()
        conn.close()
    return tasks

def update_task_progress(username: str, task_id: str, increment: int = 1):
    tasks = get_daily_tasks_progress(username)
    if tasks[task_id]["claimed"]:
        return
    need = DAILY_TASKS_CONFIG[task_id]["need_count"]
    tasks[task_id]["current"] = min(tasks[task_id]["current"] + increment, need)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET daily_tasks=? WHERE username=?", (json.dumps(tasks), username))
    conn.commit()
    conn.close()

# ---------- 祈愿系统 ----------
def get_pray_status(username: str) -> dict:
    user = get_user(username)
    if not user:
        return {"remainCount": 0, "hasBuff": False, "buffExpire": None}
    today = datetime.now().strftime("%Y-%m-%d")
    pray_date = user.get("pray_date", "")
    pray_count = user.get("pray_count", 0)
    if pray_date != today:
        pray_count = 0
    remain = max(0, 10 - pray_count)
    buff_expire = user.get("temp_buff_expire")
    has_buff = False
    expire_str = None
    if buff_expire:
        try:
            expire_time = datetime.fromisoformat(buff_expire)
            if datetime.now() < expire_time:
                has_buff = True
                expire_str = buff_expire
        except:
            pass
    return {"remainCount": remain, "hasBuff": has_buff, "buffExpire": expire_str}

def update_pray_count(username: str):
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    c = conn.cursor()
    try:
        c.execute("SELECT pray_count, pray_date FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if not row:
            return
        pray_count, pray_date = row
        today = datetime.now().strftime("%Y-%m-%d")
        if pray_date != today:
            pray_count = 0
        pray_count += 1
        c.execute("UPDATE users SET pray_count=?, pray_date=? WHERE username=?", (pray_count, today, username))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"update_pray_count error: {e}")
    finally:
        conn.close()

def set_temp_buff(username: str, duration_hours: int = 1):
    expire_time = datetime.now() + timedelta(hours=duration_hours)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET temp_buff_expire=? WHERE username=?", (expire_time.isoformat(), username))
    conn.commit()
    conn.close()

def has_temp_buff(username: str) -> bool:
    user = get_user(username)
    buff_expire = user.get("temp_buff_expire")
    if not buff_expire:
        return False
    try:
        expire_time = datetime.fromisoformat(buff_expire)
        return datetime.now() < expire_time
    except:
        return False

# ---------- 战力更新（天骄榜）----------
def update_user_power(username: str):
    """重新计算用户最高5武将战力之和，更新数据库 power 字段"""
    from web import load_heroes_db
    from battle_engine import calculate_hero_power
    user = get_user(username)
    if not user:
        return
    heroes_list = user.get("heroes", [])
    if not heroes_list:
        power = 0
    else:
        heroes_db = load_heroes_db()
        hero_map = {h["name"]: h for h in heroes_db["heroes"]}
        hero_powers = []
        for hero_name in heroes_list:
            hero_info = hero_map.get(hero_name)
            if not hero_info:
                continue
            star = user.get("star_heroes", {}).get(hero_name, 1)
            level = user.get("hero_level", {}).get(hero_name, 1)
            bonus = user.get("hero_bonus_attrs", {}).get(hero_name, {})
            temp_hero = {
                "star": star,
                "level": level,
                "base_attrs": {
                    "hp": hero_info["star5_hp"],
                    "strength": hero_info["star5_strength"],
                    "intelligence": hero_info["star5_intelligence"],
                    "speed": hero_info["star5_speed"]
                },
                "bonus_attrs": bonus,
                "skill": hero_info.get("skill")
            }
            # 宝石加成暂不计入战力（简化），若要精确可扩展
            power_val = calculate_hero_power(temp_hero)
            hero_powers.append(power_val)
        hero_powers.sort(reverse=True)
        power = sum(hero_powers[:5])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET power = ? WHERE username = ?", (power, username))
    conn.commit()
    conn.close()

# ---------- 音量持久化 ----------
def save_volume(username: str, volume: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET volume = ? WHERE username = ?", (volume, username))
    conn.commit()
    conn.close()

def get_volume(username: str) -> int:
    user = get_user(username)
    return user.get("volume", 70) if user else 70

# ---------- 初始化 ----------
init_db()