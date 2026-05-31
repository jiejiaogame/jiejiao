# challenge.py - 副本模块（支持任务进度更新，敌将等级成长）
import os
import json
import random
import sqlite3
from datetime import datetime
from fastapi import APIRouter, Request
from core import get_user, update_user_items, add_hero_exp, add_gem_to_user, DB_PATH, create_gem, generate_enemy_hero
from battle_engine import auto_battle

router = APIRouter(prefix="/challenge", tags=["challenge"])

# ---------- 数据库初始化 ----------
def init_challenge_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_challenge_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        challenge_id TEXT NOT NULL,
        node_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        UNIQUE(username, challenge_id, node_id, date)
    )''')
    conn.commit()
    conn.close()

init_challenge_db()

# ---------- 副本配置加载 ----------
CHALLENGES_FILE = "data/challenges.json"

def load_challenges():
    default_data = {
        "challenges": [
            {
                "id": "jinao",
                "name": "金鳌岛",
                "min_level": 5,
                "nodes": [
                    {"node_id": 1, "main_hero_ids": ["duobao"], "enemy_level": 10, "exp": 100, "gold": 200, "drop_rate": 0.3},
                    {"node_id": 2, "main_hero_ids": ["jinling"], "enemy_level": 15, "exp": 120, "gold": 250, "drop_rate": 0.3},
                    {"node_id": 3, "main_hero_ids": ["wudang"], "enemy_level": 20, "exp": 140, "gold": 300, "drop_rate": 0.3},
                    {"node_id": 4, "main_hero_ids": ["guiling"], "enemy_level": 25, "exp": 160, "gold": 350, "drop_rate": 0.3},
                    {"node_id": 5, "main_hero_ids": ["yunxiao"], "enemy_level": 30, "exp": 180, "gold": 400, "drop_rate": 0.3},
                    {"node_id": 6, "main_hero_ids": ["zhaogongming"], "enemy_level": 35, "exp": 200, "gold": 450, "drop_rate": 0.3},
                    {"node_id": 7, "main_hero_ids": ["duobao", "jinling"], "enemy_level": 40, "exp": 300, "gold": 600, "drop_rate": 0.4}
                ]
            },
            {
                "id": "sanxian",
                "name": "三仙岛",
                "min_level": 20,
                "nodes": [
                    {"node_id": 1, "main_hero_ids": ["yunxiao"], "enemy_level": 35, "exp": 150, "gold": 300, "drop_rate": 0.35},
                    {"node_id": 2, "main_hero_ids": ["qiongxiao"], "enemy_level": 38, "exp": 180, "gold": 350, "drop_rate": 0.35},
                    {"node_id": 3, "main_hero_ids": ["bixiao"], "enemy_level": 41, "exp": 210, "gold": 400, "drop_rate": 0.35},
                    {"node_id": 4, "main_hero_ids": ["yunxiao", "qiongxiao"], "enemy_level": 44, "exp": 240, "gold": 480, "drop_rate": 0.35},
                    {"node_id": 5, "main_hero_ids": ["qiongxiao", "bixiao"], "enemy_level": 47, "exp": 270, "gold": 560, "drop_rate": 0.35},
                    {"node_id": 6, "main_hero_ids": ["yunxiao", "bixiao"], "enemy_level": 50, "exp": 300, "gold": 640, "drop_rate": 0.35},
                    {"node_id": 7, "main_hero_ids": ["yunxiao", "qiongxiao", "bixiao"], "enemy_level": 55, "exp": 400, "gold": 800, "drop_rate": 0.45}
                ]
            }
        ]
    }
    if not os.path.exists(CHALLENGES_FILE):
        os.makedirs("data", exist_ok=True)
        with open(CHALLENGES_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data
    with open(CHALLENGES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_enemy_team(main_hero_ids: list, enemy_level: int) -> list:
    """
    根据主将ID列表和统一等级生成敌方队伍（5人）
    缺位用随机武将补齐
    """
    team = []
    # 生成主将
    for idx, hid in enumerate(main_hero_ids):
        hero = generate_enemy_hero(hid, enemy_level, star=5)
        hero["position"] = idx
        team.append(hero)
    
    # 补齐到5人（随机从所有启用的武将中选取）
    from web import load_heroes_db
    heroes_db = load_heroes_db()
    all_heroes = [h for h in heroes_db["heroes"] if h.get("enabled", True)]
    while len(team) < 5:
        rand_hero = random.choice(all_heroes)
        hero = generate_enemy_hero(rand_hero["id"], enemy_level, star=5)
        hero["position"] = len(team)
        team.append(hero)
    
    return team

def is_node_challenged_today(username: str, challenge_id: str, node_id: int) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM user_challenge_progress WHERE username=? AND challenge_id=? AND node_id=? AND date=?",
              (username, challenge_id, node_id, today))
    row = c.fetchone()
    conn.close()
    return row is not None

def mark_node_challenged(username: str, challenge_id: str, node_id: int):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO user_challenge_progress (username, challenge_id, node_id, date) VALUES (?,?,?,?)",
              (username, challenge_id, node_id, today))
    conn.commit()
    conn.close()

@router.get("/list")
async def challenge_list():
    data = load_challenges()
    challenges = data.get("challenges", [])
    return {"success": True, "challenges": [{"id": c["id"], "name": c["name"], "min_level": c.get("min_level", 1)} for c in challenges]}

@router.get("/nodes")
async def challenge_nodes(challenge_id: str):
    data = load_challenges()
    for c in data.get("challenges", []):
        if c["id"] == challenge_id:
            return {"success": True, "nodes": c["nodes"], "name": c["name"]}
    return {"success": False, "msg": "副本不存在"}

@router.post("/challenge")
async def challenge_node(req: Request):
    body = await req.json()
    username = body.get("username")
    challenge_id = body.get("challenge_id")
    node_id = body.get("node_id")
    
    if not username or not challenge_id or not node_id:
        return {"success": False, "msg": "参数不足"}
    
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    
    data = load_challenges()
    target_challenge = None
    for c in data.get("challenges", []):
        if c["id"] == challenge_id:
            target_challenge = c
            break
    if not target_challenge:
        return {"success": False, "msg": "副本不存在"}
    
    nodes = target_challenge["nodes"]
    if node_id < 1 or node_id > len(nodes):
        return {"success": False, "msg": "无效节点"}
    
    node = nodes[node_id-1]
    
    if is_node_challenged_today(username, challenge_id, node_id):
        return {"success": False, "msg": "今日已挑战过此副本节点，明日再来"}
    
    enemy_level = node.get("enemy_level", 1)
    enemy_team = generate_enemy_team(node.get("main_hero_ids", []), enemy_level)
    
    from web import get_user_team, get_formation_type
    formation_type = get_formation_type(username)
    player_team = get_user_team(username, formation_type)
    
    result = auto_battle(player_team, enemy_team)
    
    if result["winner"] == "left":
        exp_gain = node.get("exp", 100)
        gold_gain = node.get("gold", 500)
        for hero in player_team:
            add_hero_exp(username, hero["name"], exp_gain)
        update_user_items(username, gold_gain, 0)
        
        drop_rate = node.get("drop_rate", 0.3)
        gem = None
        if random.random() < drop_rate:
            attr = random.choice(["strength", "intelligence", "speed", "hp"])
            gem = create_gem(attr, 1)
            add_gem_to_user(username, gem)
        
        mark_node_challenged(username, challenge_id, node_id)
        
        try:
            from core import update_task_progress
            update_task_progress(username, "challenge", 1)
        except ImportError:
            pass
        
        return {
            "success": True,
            "exp": exp_gain,
            "gold": gold_gain,
            "gem": gem,
            "winner": "left",
            "left_team": result.get("left_team", []),
            "right_team": result.get("right_team", []),
            "log": result.get("log", []),
            "left_power": result.get("left_power", 0),
            "right_power": result.get("right_power", 0)
        }
    else:
        return {
            "success": False,
            "msg": "战斗失败，请提升实力再试",
            "left_team": result.get("left_team", []),
            "right_team": result.get("right_team", []),
            "log": result.get("log", []),
            "left_power": result.get("left_power", 0),
            "right_power": result.get("right_power", 0)
        }