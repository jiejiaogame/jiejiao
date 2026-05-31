# web.py - 最终完整版（占领无倒计时，祈愿无祝福）
import asyncio
import json
import random
import sqlite3
import os
import copy
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from core import (
    rooms, users_ws, get_user, filter_msg, remove_player_from_room,
    set_web_functions, load_disabled_config, DB_PATH,
    update_user_items, daily_reset, hash_pwd, create_user, is_valid_email,
    add_hero_exp, allocate_free_point, generate_random_gem, add_gem_to_user,
    fuse_gems, decompose_gem, equip_gem, occupy_user, release_user,
    is_occupied, get_occupier, save_formation, get_formation,
    save_formation_type, get_formation_type,
    add_blacklist, remove_blacklist, get_blacklist, is_occupied_by,
    save_user_items, create_gem, get_daily_tasks_progress, update_task_progress,
    get_pray_status, update_pray_count, set_temp_buff, has_temp_buff, load_heroes_db,
    update_user_power, save_volume, get_volume
)
from frontend import get_html
from admin import router as admin_router
import recruit
from friend import (
    get_friends, get_pending_requests, get_sent_requests,
    send_friend_request, accept_friend_request, reject_friend_request,
    delete_friend
)
from battle_engine import auto_battle, calculate_team_power, calculate_hero_power
from challenge import router as challenge_router


# ---------- 禁言字典 ----------
muted_users = {}

# ---------- 占领倒计时监控任务（已注释，不再使用）----------
# async def check_occupation_expiry():
#     try:
#         while True:
#             await asyncio.sleep(1)
#             now = datetime.now()
#             conn = sqlite3.connect(DB_PATH)
#             c = conn.cursor()
#             c.execute("SELECT username, occupied_by, occupied_time FROM users WHERE occupied_by IS NOT NULL AND occupied_time IS NOT NULL")
#             rows = c.fetchall()
#             for target, occupier, time_str in rows:
#                 if not time_str:
#                     continue
#                 try:
#                     occupied_dt = datetime.fromisoformat(time_str)
#                     elapsed = (now - occupied_dt).total_seconds()
#                     if elapsed >= 600:
#                         release_user(target)
#                         # 通知占领者
#                         if occupier in users_ws:
#                             try:
#                                 await users_ws[occupier].send_text(json.dumps({
#                                     "type": "occupy_expired",
#                                     "target": target
#                                 }))
#                             except:
#                                 pass
#                         # 通知被占领者
#                         if target in users_ws:
#                             try:
#                                 await users_ws[target].send_text(json.dumps({
#                                     "type": "occupy_released",
#                                     "by": occupier
#                                 }))
#                             except:
#                                 pass
#                 except Exception as e:
#                     print(f"检查占领到期错误: {e}")
#             conn.close()
#     except asyncio.CancelledError:
#         print("占领倒计时监控任务已取消")
#         raise

# ---------- 生命周期（支持优雅关闭，并设置异常处理器）----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 仅保留后台任务，移除异常处理器设置
    daily_task = asyncio.create_task(daily_reset())
    print("✅ 每日重置任务已启动")
    yield
    daily_task.cancel()
    try:
        await daily_task
    except asyncio.CancelledError:
        pass
    print("✅ 所有后台任务已停止")

app = FastAPI(title="截教卡牌对战", lifespan=lifespan)

# 静态文件挂载
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/ad", StaticFiles(directory="ad"), name="ad")

# 注册路由
app.include_router(admin_router)
app.include_router(recruit.router)
app.include_router(challenge_router)

# ---------- 全局广播函数 ----------
async def broadcast_all(msg_dict):
    for u, ws in users_ws.items():
        try:
            await ws.send_text(json.dumps(msg_dict))
        except:
            pass

recruit.set_broadcast_all_func(broadcast_all)
async def broadcast(room_id: str, msg: dict):
    if room_id not in rooms:
        return
    room = rooms[room_id]
    for uid in room["uids"]:
        if uid in users_ws:
            try:
                await users_ws[uid].send_text(json.dumps(msg))
            except:
                pass

async def broadcast_room_state(room_id: str):
    if room_id not in rooms:
        return
    room = rooms[room_id]
    players_info = []
    for u in room["uids"]:
        players_info.append({
            "name": u,
            "ready": room["ready"].get(u, False),
            "hero": room.get("selected_heroes", {}).get(u, None)
        })
    await broadcast(room_id, {
        "type": "room_state",
        "players": players_info,
        "mode": room["mode"],
        "room_id": room_id,
        "owner": room.get("owner"),
        "selecting": room.get("selecting_hero", False),
        "hero_pool": room.get("available_heroes", []),
        "selected_heroes": room.get("selected_heroes", {})
    })

async def send_hand(room_id: str, username: str):
    pass

set_web_functions(broadcast, broadcast_room_state, send_hand, users_ws)

# ---------- 辅助函数 ----------
def load_heroes_db():
    with open("data/custom_heroes.json", "r", encoding="utf-8") as f:
        return json.load(f)

FORMATION_BONUS = {
    "normal": {},
    "attack": {"strength": 1.1},
    "intelligence": {"intelligence": 1.1},
    "defense": {"hp": 1.1},
    "speed": {"speed": 1.1}
}

FORMATION_SLOTS = {
    "normal": [0, 1, 2, 3, 4],
    "attack": [0, 2, 4, 6, 8],
    "intelligence": [1, 3, 5, 7, 8],
    "defense": [1, 2, 5, 7, 8],
    "speed": [0, 1, 3, 4, 6]
}

def log_gm_message(username: str, msg: str, is_to_gm: bool = False):
    if username != "GM01" and not is_to_gm:
        return
    try:
        with open("gm_chat.log", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if username == "GM01":
                f.write(f"[{timestamp}] GM01 -> 全局: {msg}\n")
            elif is_to_gm:
                f.write(f"[{timestamp}] {username} -> GM01: {msg}\n")
    except Exception as e:
        print(f"记录GM日志失败: {e}")

def get_user_team(username: str, formation_type: str = "normal") -> list:
    formation = get_formation(username, formation_type)
    user = get_user(username)
    heroes = user.get("heroes", [])
    star_heroes = user.get("star_heroes", {})
    hero_level = user.get("hero_level", {})
    hero_exp = user.get("hero_exp", {})
    hero_bonus_attrs = user.get("hero_bonus_attrs", {})
    hero_gems = user.get("hero_gems", {})
    items = user.get("items", {})
    heroes_db = load_heroes_db()
    
    active_slots = FORMATION_SLOTS.get(formation_type, FORMATION_SLOTS["normal"])
    formation = [f for f in formation if f.get("position") in active_slots]
    formation = formation[:5]
    
    team = []
    for slot in formation:
        hero_name = slot.get("name")
        pos = slot.get("position")
        if hero_name not in heroes:
            continue
        base_info = next((h for h in heroes_db["heroes"] if h["name"] == hero_name), None)
        if not base_info:
            continue
        level = hero_level.get(hero_name, 1)
        bonus = hero_bonus_attrs.get(hero_name, {})
        
        base_hp = base_info["star5_hp"]
        base_str = base_info["star5_strength"]
        base_int = base_info["star5_intelligence"]
        base_spd = base_info["star5_speed"]
        
        hp = base_hp + bonus.get("hp", 0) + int(base_hp * 0.05 * (level-1))
        strength = base_str + bonus.get("strength", 0) + int(base_str * 0.02 * (level-1))
        intelligence = base_int + bonus.get("intelligence", 0) + int(base_int * 0.02 * (level-1))
        speed = base_spd + bonus.get("speed", 0) + int(base_spd * 0.015 * (level-1))
        
        gems_list = hero_gems.get(hero_name, [])
        for gem_id in gems_list:
            gem = items.get(gem_id)
            if gem:
                attr = gem.get("attr")
                val = gem.get("value", 0)
                if attr == "hp": hp += val
                elif attr == "strength": strength += val
                elif attr == "intelligence": intelligence += val
                elif attr == "speed": speed += val
                if gem.get("double_attr"):
                    attr2 = gem["double_attr"]["attr"]
                    val2 = gem["double_attr"]["value"]
                    if attr2 == "hp": hp += val2
                    elif attr2 == "strength": strength += val2
                    elif attr2 == "intelligence": intelligence += val2
                    elif attr2 == "speed": speed += val2
        
        bonus_map = FORMATION_BONUS.get(formation_type, {})
        if "hp" in bonus_map:
            hp = int(hp * bonus_map["hp"])
        if "strength" in bonus_map:
            strength = int(strength * bonus_map["strength"])
        if "intelligence" in bonus_map:
            intelligence = int(intelligence * bonus_map["intelligence"])
        if "speed" in bonus_map:
            speed = int(speed * bonus_map["speed"])
        
        if hp <= 0:
            hp = base_hp
        
        final_attrs = {
            "hp": hp,
            "strength": strength,
            "intelligence": intelligence,
            "speed": speed
        }
        
        if has_temp_buff(username):
            for k in final_attrs:
                final_attrs[k] = int(final_attrs[k] * 1.1)
        
        team.append({
            "id": base_info.get("id", hero_name),
            "name": hero_name,
            "position": pos,
            "level": level,
            "exp": hero_exp.get(hero_name, 0),
            "star": star_heroes.get(hero_name, 1),
            "hp": final_attrs["hp"],
            "maxHp": final_attrs["hp"],
            "final_attrs": final_attrs,
            "skill": base_info.get("skill")
        })
    while len(team) < 5:
        team.append({
            "id": "mortal",
            "name": "凡人修士",
            "position": len(team),
            "level": 1,
            "hp": 100,
            "maxHp": 100,
            "star": 1,
            "final_attrs": {"hp": 100, "strength": 10, "intelligence": 10, "speed": 20},
            "skill": {"base_id": "control", "display_name": "祈求"}
        })
    return team

def get_user_power(username: str) -> int:
    formation_type = get_formation_type(username)
    team = get_user_team(username, formation_type)
    heroes_for_power = []
    for t in team:
        heroes_for_power.append({
            "star": t["star"],
            "level": t["level"],
            "base_attrs": {
                "hp": t["final_attrs"]["hp"],
                "strength": t["final_attrs"]["strength"],
                "intelligence": t["final_attrs"]["intelligence"],
                "speed": t["final_attrs"]["speed"]
            },
            "bonus_attrs": {},
            "skill": t.get("skill")
        })
    return calculate_team_power(heroes_for_power)
# ---------- HTTP 路由 ----------
@app.get("/")
async def index():
    return HTMLResponse(get_html())

@app.post("/register")
async def register(req: Request):
    data = await req.json()
    u = data.get("username")
    p = data.get("password")
    e = data.get("email")
    if not u or not p or not e:
        return {"success": False, "msg": "所有字段都不能为空"}
    if len(u) > 5:
        return {"success": False, "msg": "用户名不能超过5个汉字或字符"}
    if not is_valid_email(e):
        return {"success": False, "msg": "邮箱格式不正确"}
    if create_user(u, p, e):
        heroes_db = load_heroes_db()
        one_star_heroes = [h for h in heroes_db["heroes"] if h.get("star5_hp", 0) < 40]
        gift_hero = None
        if one_star_heroes:
            gift_hero = random.choice(one_star_heroes)
            user = get_user(u)
            heroes = user.get("heroes", [])
            star_heroes = user.get("star_heroes", {})
            heroes.append(gift_hero["name"])
            star_heroes[gift_hero["name"]] = 1
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE users SET heroes=?, star_heroes=?, gold=gold+500 WHERE username=?", 
                      (json.dumps(heroes), json.dumps(star_heroes), u))
            conn.commit()
            conn.close()
        update_user_power(u)
        return {"success": True, "msg": "注册成功", "gift_hero": gift_hero["name"] if gift_hero else None}
    else:
        return {"success": False, "msg": "用户名已存在"}

@app.post("/login")
async def login(req: Request):
    data = await req.json()
    u = data.get("username")
    p = data.get("password")
    user = get_user(u)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    if user["password"] != hash_pwd(p):
        return {"success": False, "msg": "密码错误"}
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    last_login = user.get("last_login_date")
    reward = 0
    if last_login != today:
        reward = 500
        c.execute("UPDATE users SET gold = gold + ?, last_login_date = ? WHERE username = ?", (reward, today, u))
        conn.commit()
        get_daily_tasks_progress(u)
    conn.close()
    update_user_power(u)
    return {"success": True, "msg": "登录成功", "is_admin": (u == "GM01"), "daily_reward": reward}

@app.get("/user_resources")
async def user_resources(username: str):
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    return {"success": True, "gold": user["gold"], "ingots": user.get("ingots", 0)}

@app.get("/user_info")
async def user_info(username: str):
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    max_level = 0
    hero_levels = user.get("hero_level", {})
    if hero_levels:
        max_level = max(hero_levels.values())
    return {
        "success": True,
        "username": username,
        "avatar": user.get("avatar", "hero.png"),
        "level": max_level if max_level else 1,
        "exp": 0,
        "volume": user.get("volume", 70)
    }

@app.get("/my_heroes")
async def my_heroes(username: str):
    user = get_user(username)
    if not user:
        return {"error": "用户不存在"}
    heroes = user.get("heroes", [])
    star_heroes = user.get("star_heroes", {})
    hero_level = user.get("hero_level", {})
    hero_exp = user.get("hero_exp", {})
    heroes_db = load_heroes_db()
    hero_map = {h["name"]: h["id"] for h in heroes_db["heroes"]}
    result = []
    for h in heroes:
        result.append({
            "name": h,
            "id": hero_map.get(h, h),
            "star": star_heroes.get(h, 1),
            "level": hero_level.get(h, 1),
            "exp": hero_exp.get(h, 0)
        })
    return {"heroes": result}

@app.get("/hero_detail")
async def hero_detail(username: str, hero: str):
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    heroes_db = load_heroes_db()
    hero_info = next((h for h in heroes_db["heroes"] if h["name"] == hero), None)
    if not hero_info:
        return {"success": False, "msg": "武将不存在"}
    star = user.get("star_heroes", {}).get(hero, 1)
    level = user.get("hero_level", {}).get(hero, 1)
    exp = user.get("hero_exp", {}).get(hero, 0)
    bonus = user.get("hero_bonus_attrs", {}).get(hero, {})
    free_points = user.get("hero_free_points", {}).get(hero, 0)
    hero_gems = user.get("hero_gems", {}).get(hero, [None]*5)
    items = user.get("items", {})
    gems_detail = []
    for gid in hero_gems:
        if gid and gid in items:
            gem = items[gid]
            gems_detail.append({
                "id": gid,
                "name": gem.get("name"),
                "attr": gem.get("attr"),
                "value": gem.get("value"),
                "star": gem.get("star")
            })
        else:
            gems_detail.append(None)
    base = hero_info
    final_attrs = {
        "hp": base["star5_hp"] + bonus.get("hp", 0) + int(base["star5_hp"] * 0.05 * (level-1)),
        "strength": base["star5_strength"] + bonus.get("strength", 0) + int(base["star5_strength"] * 0.02 * (level-1)),
        "intelligence": base["star5_intelligence"] + bonus.get("intelligence", 0) + int(base["star5_intelligence"] * 0.02 * (level-1)),
        "speed": base["star5_speed"] + bonus.get("speed", 0) + int(base["star5_speed"] * 0.015 * (level-1))
    }
    for gem in gems_detail:
        if gem:
            if gem["attr"] == "hp":
                final_attrs["hp"] += gem["value"]
            elif gem["attr"] == "strength":
                final_attrs["strength"] += gem["value"]
            elif gem["attr"] == "intelligence":
                final_attrs["intelligence"] += gem["value"]
            elif gem["attr"] == "speed":
                final_attrs["speed"] += gem["value"]
    
    temp_hero = {
        "star": star,
        "level": level,
        "base_attrs": {
            "hp": base["star5_hp"],
            "strength": base["star5_strength"],
            "intelligence": base["star5_intelligence"],
            "speed": base["star5_speed"]
        },
        "bonus_attrs": bonus,
        "skill": hero_info.get("skill")
    }
    power = calculate_hero_power(temp_hero)
    
    skill_name = "无"
    skill_desc = "无"
    if hero_info.get("skill"):
        try:
            with open("data/skills.json", "r", encoding="utf-8") as f:
                skills_data = json.load(f)
                base_id = hero_info["skill"].get("base_id")
                if base_id:
                    template = next((s for s in skills_data.get("skills", []) if s["id"] == base_id), None)
                    if template:
                        skill_desc = template.get("description", "暂无描述")
        except:
            pass
        skill_name = hero_info["skill"].get("display_name", hero_info["skill"].get("name", "未知技能"))
    
    return {
        "success": True,
        "id": hero_info.get("id"),
        "name": hero,
        "star": star,
        "level": level,
        "exp": exp,
        "free_points": free_points,
        "bonus_attrs": bonus,
        "gems": gems_detail,
        "final_attrs": final_attrs,
        "base_attrs": {
            "hp": base["star5_hp"],
            "strength": base["star5_strength"],
            "intelligence": base["star5_intelligence"],
            "speed": base["star5_speed"]
        },
        "power": power,
        "skill_name": skill_name,
        "skill_desc": skill_desc
    }

@app.post("/allocate_point")
async def allocate_point(req: Request):
    data = await req.json()
    username = data.get("username")
    hero_name = data.get("hero_name")
    attr = data.get("attr")
    if allocate_free_point(username, hero_name, attr):
        update_user_power(username)
        return {"success": True}
    else:
        return {"success": False, "msg": "没有可用属性点"}

@app.post("/dismiss_hero")
async def dismiss_hero(req: Request):
    data = await req.json()
    username = data.get("username")
    hero_name = data.get("hero_name")
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    heroes = user.get("heroes", [])
    if hero_name not in heroes:
        return {"success": False, "msg": "没有该武将"}
    hero_exp = user.get("hero_exp", {}).get(hero_name, 0)
    refund_exp = hero_exp // 2
    heroes.remove(hero_name)
    star_heroes = user.get("star_heroes", {})
    if hero_name in star_heroes:
        del star_heroes[hero_name]
    hero_exp_dict = user.get("hero_exp", {})
    if hero_name in hero_exp_dict:
        del hero_exp_dict[hero_name]
    hero_level_dict = user.get("hero_level", {})
    if hero_name in hero_level_dict:
        del hero_level_dict[hero_name]
    hero_bonus = user.get("hero_bonus_attrs", {})
    if hero_name in hero_bonus:
        del hero_bonus[hero_name]
    hero_free = user.get("hero_free_points", {})
    if hero_name in hero_free:
        del hero_free[hero_name]
    hero_gems = user.get("hero_gems", {})
    items = user.get("items", {})
    gems_list = hero_gems.get(hero_name, [])
    for gem_id in gems_list:
        if gem_id:
            if gem_id in items:
                items[gem_id]["count"] = items[gem_id].get("count", 1) + 1
            else:
                items[gem_id] = {"id": gem_id, "count": 1, "name": "宝石"}
    if hero_name in hero_gems:
        del hero_gems[hero_name]
    exp_item_id = "exp_potion"
    if exp_item_id in items:
        items[exp_item_id]["count"] += refund_exp
    else:
        items[exp_item_id] = {"name": "经验药水", "value": 100, "count": refund_exp}
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET heroes=?, star_heroes=?, hero_exp=?, hero_level=?, hero_bonus_attrs=?, hero_free_points=?, hero_gems=?, items=? WHERE username=?",
              (json.dumps(heroes), json.dumps(star_heroes), json.dumps(hero_exp_dict),
               json.dumps(hero_level_dict), json.dumps(hero_bonus), json.dumps(hero_free),
               json.dumps(hero_gems), json.dumps(items), username))
    conn.commit()
    conn.close()
    update_user_power(username)
    return {"success": True, "msg": f"遣散成功，获得 {refund_exp} 经验药水", "refund_exp": refund_exp}
@app.post("/save_formation")
async def save_formation_route(req: Request):
    data = await req.json()
    username = data.get("username")
    formation = data.get("formation", [])
    formation_type = data.get("formation_type", "normal")
    if len(formation) > 5:
        return {"success": False, "msg": "最多上阵5名武将"}
    positions = [f["position"] for f in formation]
    if len(set(positions)) != len(positions):
        return {"success": False, "msg": "站位重复"}
    user = get_user(username)
    owned_heroes = user.get("heroes", [])
    for f in formation:
        if f["name"] not in owned_heroes:
            return {"success": False, "msg": f"武将 {f['name']} 不存在"}
    active_slots = FORMATION_SLOTS.get(formation_type, FORMATION_SLOTS["normal"])
    formation = [f for f in formation if f.get("position") in active_slots]
    save_formation(username, formation_type, formation)
    save_formation_type(username, formation_type)
    return {"success": True}

@app.post("/save_formation_type")
async def save_formation_type_route(req: Request):
    data = await req.json()
    username = data.get("username")
    formation_type = data.get("formation_type")
    if not username or not formation_type:
        return {"success": False, "msg": "参数不足"}
    save_formation_type(username, formation_type)
    return {"success": True}

@app.get("/get_formation")
async def get_formation_route(username: str):
    formation_type = get_formation_type(username)
    formation = get_formation(username, formation_type)
    heroes_db = load_heroes_db()
    hero_id_map = {h["name"]: h["id"] for h in heroes_db["heroes"]}
    for f in formation:
        f["id"] = hero_id_map.get(f["name"], f["name"])
    return {"formation": formation, "formation_type": formation_type}

@app.post("/match_pvp")
async def match_pvp(req: Request):
    data = await req.json()
    username = data.get("username")
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    my_power = get_user_power(username)
    online_players = [u for u in users_ws.keys() if u != username]
    candidates = []
    for p in online_players:
        p_power = get_user_power(p)
        if abs(p_power - my_power) < 500:
            candidates.append(p)
    formation_type = get_formation_type(username)
    player_team = get_user_team(username, formation_type)
    daily_pvp_count = user.get("daily_pvp_count", 0)
    exp_gain = 0
    if daily_pvp_count < 10:
        exp_gain = 50
    if candidates:
        opponent = random.choice(candidates)
        opponent_formation = get_formation_type(opponent)
        opponent_team = get_user_team(opponent, opponent_formation)
        result = auto_battle(player_team, opponent_team)
        if exp_gain:
            for hero in player_team:
                add_hero_exp(username, hero["name"], 50)
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE users SET daily_pvp_count = daily_pvp_count + 1 WHERE username = ?", (username,))
            conn.commit()
            conn.close()
        update_task_progress(username, "friend_pvp", 1)
        return {
            "success": True,
            "type": "player",
            "opponent": opponent,
            "winner": result["winner"],
            "exp_gain": exp_gain,
            "log": result["log"],
            "left_team": result.get("left_team", []),
            "right_team": result.get("right_team", []),
            "left_power": result.get("left_power", 0),
            "right_power": result.get("right_power", 0)
        }
    else:
        from challenge import generate_enemy_team
        power = int(my_power * random.uniform(0.8, 1.2))
        bot_team = generate_enemy_team([], power)
        result = auto_battle(player_team, bot_team)
        if exp_gain:
            for hero in player_team:
                add_hero_exp(username, hero["name"], 50)
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE users SET daily_pvp_count = daily_pvp_count + 1 WHERE username = ?", (username,))
            conn.commit()
            conn.close()
        update_task_progress(username, "friend_pvp", 1)
        return {
            "success": True,
            "type": "bot",
            "winner": result["winner"],
            "exp_gain": exp_gain,
            "log": result["log"],
            "left_team": result.get("left_team", []),
            "right_team": result.get("right_team", []),
            "left_power": result.get("left_power", 0),
            "right_power": result.get("right_power", 0)
        }

@app.post("/match_pvp_with_friend")
async def match_pvp_with_friend(req: Request):
    data = await req.json()
    username = data.get("username")
    friend = data.get("friend")
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    friends = get_friends(username)
    if friend not in [f["name"] for f in friends]:
        return {"success": False, "msg": "不是好友"}
    formation_type = get_formation_type(username)
    player_team = get_user_team(username, formation_type)
    friend_formation = get_formation_type(friend)
    friend_team = get_user_team(friend, friend_formation)
    result = auto_battle(player_team, friend_team)
    daily_pvp_count = user.get("daily_pvp_count", 0)
    exp_gain = 0
    if daily_pvp_count < 10:
        exp_gain = 50
        for hero in player_team:
            add_hero_exp(username, hero["name"], 50)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET daily_pvp_count = daily_pvp_count + 1 WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    update_task_progress(username, "friend_pvp", 1)
    return {
        "success": True,
        "winner": result["winner"],
        "exp_gain": exp_gain,
        "log": result["log"],
        "left_team": result.get("left_team", []),
        "right_team": result.get("right_team", []),
        "left_power": result.get("left_power", 0),
        "right_power": result.get("right_power", 0)
    }

@app.post("/solo_practice")
async def solo_practice(req: Request):
    data = await req.json()
    username = data.get("username")
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    formation_type = get_formation_type(username)
    player_team = get_user_team(username, formation_type)
    mirror_team = copy.deepcopy(player_team)
    result = auto_battle(player_team, mirror_team)
    daily_pvp_count = user.get("daily_pvp_count", 0)
    exp_gain = 0
    if daily_pvp_count < 10:
        exp_gain = 25
        for hero in player_team:
            add_hero_exp(username, hero["name"], exp_gain)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET daily_pvp_count = daily_pvp_count + 1 WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    update_task_progress(username, "self_pvp", 1)
    return {
        "success": True,
        "winner": result["winner"],
        "log": result["log"],
        "left_team": result.get("left_team", []),
        "right_team": result.get("right_team", []),
        "left_power": result.get("left_power", 0),
        "right_power": result.get("right_power", 0),
        "exp_gain": exp_gain,
        "msg": "自我切磋完成"
    }

@app.post("/occupy_friend")
async def occupy_friend(req: Request):
    data = await req.json()
    username = data.get("username")
    friend = data.get("friend")
    friends = get_friends(username)
    friend_names = [f["name"] for f in friends]
    if friend not in friend_names:
        return {"success": False, "msg": "不是好友"}
    occ = is_occupied(friend)
    if occ:
        return {"success": False, "msg": "该好友已被占领"}
    formation_type = get_formation_type(username)
    player_team = get_user_team(username, formation_type)
    opponent_formation = get_formation_type(friend)
    friend_team = get_user_team(friend, opponent_formation)
    result = auto_battle(player_team, friend_team)
    if result["winner"] == "left":
        occupy_user(username, friend)
        # 实时通知双方占领状态变化
        if username in users_ws:
            try:
                await users_ws[username].send_text(json.dumps({
                    "type": "occupy_change",
                    "target": friend,
                    "occupied": True,
                    "by": username
                }))
            except:
                pass
        if friend in users_ws:
            try:
                await users_ws[friend].send_text(json.dumps({
                    "type": "occupy_change",
                    "target": friend,
                    "occupied": True,
                    "by": username
                }))
            except:
                pass
        return {"success": True, "msg": f"占领成功！{friend} 已成为你的分舵"}
    else:
        return {"success": False, "msg": "占领失败"}

@app.post("/release_friend")
async def release_friend(req: Request):
    data = await req.json()
    username = data.get("username")
    friend = data.get("friend")
    if not is_occupied(friend):
        return {"success": False, "msg": "该好友未被占领"}
    occupier = get_occupier(friend)
    if occupier != username:
        return {"success": False, "msg": "你不是占领者"}
    formation_type = get_formation_type(username)
    player_team = get_user_team(username, formation_type)
    opponent_formation = get_formation_type(friend)
    friend_team = get_user_team(friend, opponent_formation)
    result = auto_battle(player_team, friend_team)
    if result["winner"] == "left":
        release_user(friend)
        return {"success": True, "msg": "解救成功！"}
    else:
        return {"success": False, "msg": "解救失败"}

@app.post("/self_release")
async def self_release(req: Request):
    data = await req.json()
    username = data.get("username")
    occupier = get_occupier(username)
    if not occupier:
        return {"success": False, "msg": "你未被占领"}
    formation_type = get_formation_type(username)
    player_team = get_user_team(username, formation_type)
    opp_formation = get_formation_type(occupier)
    opp_team = get_user_team(occupier, opp_formation)
    result = auto_battle(player_team, opp_team)
    if result["winner"] == "left":
        release_user(username)
        return {"success": True, "msg": "解救成功！"}
    else:
        return {"success": False, "msg": "解救失败"}

@app.post("/rob_occupied")
async def rob_occupied(req: Request):
    data = await req.json()
    username = data.get("username")
    target = data.get("target")
    user_target = get_user(target)
    if not user_target:
        return {"success": False, "msg": "目标不存在"}
    occupier = user_target.get("occupied_by")
    if not occupier:
        return {"success": False, "msg": "该玩家未被占领"}
    if occupier == username:
        return {"success": False, "msg": "你已经是占领者"}
    formation_type = get_formation_type(username)
    attacker_team = get_user_team(username, formation_type)
    defender_team = get_user_team(occupier, get_formation_type(occupier))
    result = auto_battle(attacker_team, defender_team)
    if result["winner"] == "left":
        new_time = datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET occupied_by=?, occupied_time=? WHERE username=?", (username, new_time, target))
        conn.commit()
        conn.close()
        return {"success": True, "msg": f"抢夺成功！你占领了{target}"}
    else:
        return {"success": False, "msg": "抢夺失败"}

@app.get("/friend_palace_info")
async def friend_palace_info(username: str, friend: str):
    user = get_user(friend)
    if not user:
        return {"success": False, "msg": "好友不存在"}
    max_level = 0
    hero_levels = user.get("hero_level", {})
    if hero_levels:
        max_level = max(hero_levels.values())
    branches = 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE occupied_by=?", (friend,))
    branches = c.fetchone()[0]
    conn.close()
    return {
        "success": True,
        "level": max_level if max_level else 1,
        "occupier": user.get("occupied_by"),
        "branches": branches,
        "avatar": user.get("avatar", "hero.png")
    }

@app.post("/fuse_gems")
async def fuse_gems_route(req: Request):
    data = await req.json()
    username = data.get("username")
    gem_id1 = data.get("gem_id1")
    gem_id2 = data.get("gem_id2")
    result = fuse_gems(username, gem_id1, gem_id2)
    if result.get("success"):
        update_user_power(username)
    return result

@app.post("/decompose_gem")
async def decompose_gem_route(req: Request):
    data = await req.json()
    username = data.get("username")
    gem_id = data.get("gem_id")
    result = decompose_gem(username, gem_id)
    if result.get("success"):
        update_user_power(username)
    return result

@app.post("/equip_gem")
async def equip_gem_route(req: Request):
    data = await req.json()
    username = data.get("username")
    hero_name = data.get("hero_name")
    gem_id = data.get("gem_id")
    slot = data.get("slot", 0)
    result = equip_gem(username, hero_name, gem_id, slot)
    if result.get("success"):
        update_user_power(username)
    return result

@app.post("/unequip_gem")
async def unequip_gem(req: Request):
    data = await req.json()
    username = data.get("username")
    hero_name = data.get("hero_name")
    slot = data.get("slot")
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    if user.get("gold", 0) < 500:
        return {"success": False, "msg": "金币不足500"}
    hero_gems = user.get("hero_gems", {})
    gems_list = hero_gems.get(hero_name, [None]*5)
    if slot < 0 or slot >= len(gems_list):
        return {"success": False, "msg": "无效槽位"}
    gem_id = gems_list[slot]
    if not gem_id:
        return {"success": False, "msg": "该槽位没有宝石"}
    items = user.get("items", {})
    if gem_id in items:
        items[gem_id]["count"] = items[gem_id].get("count", 1) + 1
    else:
        items[gem_id] = {"id": gem_id, "count": 1, "name": "宝石"}
    gems_list[slot] = None
    hero_gems[hero_name] = gems_list
    new_gold = user["gold"] - 500
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET gold=?, hero_gems=?, items=? WHERE username=?", 
              (new_gold, json.dumps(hero_gems), json.dumps(items), username))
    conn.commit()
    conn.close()
    update_user_power(username)
    return {"success": True, "msg": "卸下成功，消耗500金币"}

@app.post("/discard_gem")
async def discard_gem(req: Request):
    data = await req.json()
    username = data.get("username")
    gem_id = data.get("gem_id")
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    items = user.get("items", {})
    gem = items.get(gem_id)
    if not gem:
        return {"success": False, "msg": "宝石不存在"}
    if gem.get("count", 1) > 1:
        gem["count"] -= 1
        items[gem_id] = gem
    else:
        items.pop(gem_id)
    save_user_items(username, items)
    return {"success": True, "msg": "已丢弃一颗宝石"}

@app.get("/user_items")
async def user_items(username: str):
    user = get_user(username)
    if not user:
        return {"success": False}
    items = user.get("items", {})
    gem_list = []
    for gem_id, gem in items.items():
        gem_list.append({
            "id": gem_id,
            "name": gem.get("name", "宝石"),
            "star": gem.get("star", 1),
            "value": gem.get("value", 0),
            "count": gem.get("count", 1),
            "double_attr": gem.get("double_attr"),
            "attr": gem.get("attr")
        })
    return {"success": True, "items": gem_list}

@app.get("/get_occupier")
async def get_occupier_route(username: str):
    occupier = get_occupier(username)
    return {"occupier": occupier}

@app.get("/api/occupied_info")
async def get_occupied_info(username: str, target: str):
    user_target = get_user(target)
    if not user_target:
        return {"success": False, "msg": "目标不存在"}
    occupier = user_target.get("occupied_by")
    # 不再返回倒计时相关信息
    is_occupied_by_me = (occupier == username)
    return {
        "success": True,
        "isOccupiedByMe": is_occupied_by_me,
        "canRecruit": is_occupied_by_me,  # 占领者始终可以招募
        "remainSeconds": 0
    }
@app.get("/avatar_list")
async def avatar_list():
    path = "static/images/avatars"
    avatars = []
    if os.path.exists(path):
        for f in os.listdir(path):
            if f.endswith((".jpg", ".png")):
                avatars.append(f)
    return {"avatars": avatars}

@app.post("/update_avatar")
async def update_avatar(req: Request):
    data = await req.json()
    username = data.get("username")
    avatar = data.get("avatar")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET avatar = ? WHERE username = ?", (avatar, username))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/rank/daily")
async def daily_rank():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, avatar, daily_gold FROM daily_rank WHERE update_date=? ORDER BY daily_gold DESC LIMIT 100", (today,))
    rows = c.fetchall()
    conn.close()
    return {"success": True, "rank": [{"name": r[0], "avatar": r[1], "gold": r[2]} for r in rows]}

@app.get("/rank/power")
async def power_rank(username: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, power FROM users WHERE power > 0 ORDER BY power DESC LIMIT 100")
    rows = c.fetchall()
    rank_list = [{"username": r[0], "power": r[1]} for r in rows]
    my_rank = None
    my_power = None
    if username:
        c.execute("SELECT power FROM users WHERE username = ?", (username,))
        user_row = c.fetchone()
        if user_row:
            my_power = user_row[0]
            c.execute("SELECT COUNT(*) FROM users WHERE power > ?", (my_power,))
            my_rank = c.fetchone()[0] + 1
    conn.close()
    return {"success": True, "rank": rank_list, "my_power": my_power, "my_rank": my_rank}

@app.post("/set_volume")
async def set_volume(req: Request):
    data = await req.json()
    username = data.get("username")
    volume = data.get("volume")
    if username and volume is not None:
        save_volume(username, volume)
        return {"success": True}
    return {"success": False}

# ========== 好友系统 API ==========
@app.get("/api/friends")
async def api_friends(username: str):
    return {"success": True, "friends": get_friends(username)}

@app.get("/api/friend/pending")
async def api_pending_requests(username: str):
    pending = get_pending_requests(username)
    return {"success": True, "requests": pending}

@app.post("/api/friend/add")
async def api_add_friend(req: Request):
    data = await req.json()
    res = await send_friend_request(data["from"], data["to"])
    return res

@app.post("/api/friend/accept")
async def api_accept_friend(req: Request):
    data = await req.json()
    return accept_friend_request(data["username"], data["from"])

@app.post("/api/friend/reject")
async def api_reject_friend(req: Request):
    data = await req.json()
    return reject_friend_request(data["username"], data["from"])

@app.post("/api/friend/delete")
async def api_delete_friend(req: Request):
    data = await req.json()
    return delete_friend(data["username"], data["friend"])

@app.get("/api/blacklist")
async def get_blacklist_route(username: str):
    blacklist = get_blacklist(username)
    return {"success": True, "blacklist": blacklist}

@app.post("/api/blacklist/add")
async def add_blacklist_route(req: Request):
    data = await req.json()
    username = data.get("username")
    target = data.get("target")
    if not username or not target:
        return {"success": False, "msg": "参数不足"}
    if username == target:
        return {"success": False, "msg": "不能拉黑自己"}
    add_blacklist(username, target)
    return {"success": True, "msg": f"已将 {target} 加入黑名单"}

@app.post("/api/blacklist/remove")
async def remove_blacklist_route(req: Request):
    data = await req.json()
    username = data.get("username")
    target = data.get("target")
    if not username or not target:
        return {"success": False, "msg": "参数不足"}
    remove_blacklist(username, target)
    return {"success": True, "msg": f"已将 {target} 移出黑名单"}

@app.post("/use_exp_potion")
async def use_exp_potion(req: Request):
    data = await req.json()
    username = data.get("username")
    hero_name = data.get("hero_name")
    amount = data.get("amount", 1)
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    items = user.get("items", {})
    potion = items.get("exp_potion")
    if not potion or potion.get("count", 0) < amount:
        return {"success": False, "msg": "经验药水不足"}
    exp_gain = amount * 100
    add_hero_exp(username, hero_name, exp_gain)
    potion["count"] -= amount
    if potion["count"] <= 0:
        del items["exp_potion"]
    save_user_items(username, items)
    update_user_power(username)
    return {"success": True, "msg": f"使用了{amount}瓶经验药水，{hero_name}获得{exp_gain}经验"}

@app.post("/shop/buy_gem")
async def buy_gem(req: Request):
    data = await req.json()
    username = data.get("username")
    gem_type = data.get("gem_type")
    quantity = data.get("quantity", 1)
    if quantity < 1 or quantity > 99:
        return {"success": False, "msg": "数量必须在1-99之间"}
    
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    
    ingots = user.get("ingots", 0)
    cost = quantity
    if ingots < cost:
        return {"success": False, "msg": f"钻石不足，需要{cost}钻石"}
    
    value = random.randint(1, 2)
    gem = create_gem(gem_type, 1, value)
    gem["count"] = quantity
    
    items = user.get("items", {})
    target_id = None
    for gid, g in items.items():
        if (g.get("attr") == gem_type and g.get("star") == 1 and 
            g.get("double_attr") is None and g.get("value") == value):
            target_id = gid
            break
    if target_id:
        items[target_id]["count"] += quantity
    else:
        gem["id"] = f"gem_{gem_type}_1_{value}_{random.randint(10000,99999)}"
        items[gem["id"]] = gem
    
    new_ingots = ingots - cost
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET ingots=?, items=? WHERE username=?", (new_ingots, json.dumps(items), username))
    conn.commit()
    conn.close()
    
    update_task_progress(username, "shop", 1)
    update_user_power(username)
    return {"success": True, "msg": f"成功购买{quantity}颗{gem_type}宝石"}

@app.get("/daily_tasks")
async def get_daily_tasks(username: str):
    tasks = get_daily_tasks_progress(username)
    from core import DAILY_TASKS_CONFIG
    result = {}
    for task_id, config in DAILY_TASKS_CONFIG.items():
        progress = tasks.get(task_id, {"current": 0, "claimed": False})
        completed = progress["current"] >= config["need_count"]
        result[task_id] = {
            "completed": completed,
            "claimed": progress.get("claimed", False),
            "current": progress["current"],
            "need": config["need_count"],
            "reward_gold": config["reward_gold"],
            "reward_ingots": config["reward_ingots"]
        }
    return {"success": True, "tasks": result}

@app.post("/claim_task")
async def claim_task(req: Request):
    data = await req.json()
    username = data.get("username")
    task_id = data.get("task_id")
    tasks = get_daily_tasks_progress(username)
    from core import DAILY_TASKS_CONFIG
    if task_id not in tasks:
        return {"success": False, "msg": "任务不存在"}
    if tasks[task_id]["claimed"]:
        return {"success": False, "msg": "奖励已领取"}
    config = DAILY_TASKS_CONFIG[task_id]
    if tasks[task_id]["current"] < config["need_count"]:
        return {"success": False, "msg": "任务未完成"}
    
    gold_reward = config["reward_gold"]
    ingots_reward = config["reward_ingots"]
    user = get_user(username)
    new_gold = user["gold"] + gold_reward
    new_ingots = user.get("ingots", 0) + ingots_reward
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET gold=?, ingots=? WHERE username=?", (new_gold, new_ingots, username))
    tasks[task_id]["claimed"] = True
    c.execute("UPDATE users SET daily_tasks=? WHERE username=?", (json.dumps(tasks), username))
    conn.commit()
    conn.close()
    return {"success": True, "msg": f"领取成功，获得{config['reward_gold']}金币、{config['reward_ingots']}钻石"}

@app.get("/skill_animations")
async def get_skill_animations():
    try:
        with open("data/skill_animations.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ========== 祈愿系统（无祝福效果）==========
@app.get("/pray/status")
async def pray_status(username: str):
    status = get_pray_status(username)
    return {"success": True, **status}

@app.post("/pray/burn_incense")
async def burn_incense(req: Request):
    data = await req.json()
    username = data.get("username")
    pray_type = data.get("pray_type")
    
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    c = conn.cursor()
    try:
        c.execute("SELECT gold, heroes, star_heroes, items, pray_count, pray_date FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if not row:
            return {"success": False, "msg": "用户不存在"}
        gold, heroes_json, star_heroes_json, items_json, pray_count, pray_date = row
        gold = int(gold) if gold else 0
        heroes = json.loads(heroes_json) if heroes_json else []
        star_heroes = json.loads(star_heroes_json) if star_heroes_json else {}
        items = json.loads(items_json) if items_json else {}
        
        if gold < 1000:
            return {"success": False, "msg": f"金币不足1000，当前{gold}金币"}
        
        today = datetime.now().strftime("%Y-%m-%d")
        if pray_date != today:
            pray_count = 0
        remain = max(0, 10 - pray_count)
        
        new_gold = gold - 1000
        c.execute("UPDATE users SET gold=? WHERE username=?", (new_gold, username))
        
        # 所有祈愿都按普通随机奖励处理，不再区分特殊祈愿
        reward = None
        msg = ""
        if pray_type == "wealth":
            if random.random() < 0.5:
                value = random.choice([2000, 5000])
                new_gold += value
                c.execute("UPDATE users SET gold=? WHERE username=?", (new_gold, username))
                msg = f"求财成功！获得{value}金币"
                reward = {"type": "gold", "value": value}
            else:
                msg = "求财失败，一无所获"
                reward = {"type": "none"}
        elif pray_type == "love":
            if random.random() < 0.5:
                heroes_data = load_heroes_db()
                available = [h for h in heroes_data.get("heroes", []) if h.get("enabled", True)]
                if not available:
                    msg = "暂无可用武将，请稍后再试"
                    reward = {"type": "none"}
                else:
                    hero = random.choice(available)
                    star = random.choices([2,3,4], weights=[0.5,0.3,0.2])[0]
                    hero_name = hero["name"]
                    if hero_name in heroes:
                        exp_potion_id = "exp_potion"
                        if exp_potion_id in items:
                            items[exp_potion_id]["count"] += 1
                        else:
                            items[exp_potion_id] = {"name": "经验药水", "value": 200, "count": 1}
                        c.execute("UPDATE users SET items=? WHERE username=?", (json.dumps(items), username))
                        msg = f"求缘成功！但你已拥有{hero_name}，转化为1瓶经验药水"
                        reward = {"type": "exp_potion", "value": 200}
                    else:
                        heroes.append(hero_name)
                        star_heroes[hero_name] = star
                        c.execute("UPDATE users SET heroes=?, star_heroes=? WHERE username=?", 
                                  (json.dumps(heroes), json.dumps(star_heroes), username))
                        msg = f"求缘成功！获得{star}星{hero_name}"
                        reward = {"type": "hero", "name": hero_name, "star": star}
            else:
                msg = "求缘失败，一无所获"
                reward = {"type": "none"}
        elif pray_type == "chance":
            if random.random() < 0.3:
                exp_potion_id = "exp_potion"
                if exp_potion_id in items:
                    items[exp_potion_id]["count"] += 1
                else:
                    items[exp_potion_id] = {"name": "经验药水", "value": 200, "count": 1}
                c.execute("UPDATE users SET items=? WHERE username=?", (json.dumps(items), username))
                msg = "求机缘成功！获得1瓶经验药水（200经验）"
                reward = {"type": "exp_potion", "value": 200}
            else:
                msg = "求机缘失败，一无所获"
                reward = {"type": "none"}
        else:
            msg = "无效的祈愿类型"
            reward = {"type": "none"}
        
        pray_count += 1
        c.execute("UPDATE users SET pray_count=?, pray_date=? WHERE username=?", (pray_count, today, username))
        conn.commit()
        conn.close()
        update_user_power(username)
        return {"success": True, "msg": msg, "reward": reward, "gold": new_gold}
    
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"祈愿异常: {e}")
        return {"success": False, "msg": "祈愿失败，请稍后重试"}

# ========== WebSocket（加入单连接踢出逻辑）==========
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    username = None
    room_id = None
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            act = req.get("act")

            if act == "login":
                username = req.get("uid")
                if username and get_user(username):
                    old_ws = users_ws.get(username)
                    if old_ws and old_ws != websocket:
                        try:
                            await old_ws.close(code=1000, reason="新连接代替旧连接")
                        except:
                            pass
                    users_ws[username] = websocket
                    await websocket.send_text(json.dumps({"type": "login_ok"}))
                else:
                    await websocket.send_text(json.dumps({"type": "login_fail"}))
                continue

            if not username:
                continue

            if act == "create_room":
                mode = req.get("mode", "1v1")
                pwd = req.get("password", "")
                room_id = str(random.randint(1000, 9999))
                rooms[room_id] = {
                    "room_id": room_id,
                    "mode": mode,
                    "password": pwd,
                    "uids": [username],
                    "ready": {username: False},
                    "owner": username,
                    "started": False
                }
                await websocket.send_text(json.dumps({"type": "room_created", "roomId": room_id}))
                await broadcast_room_state(room_id)
                continue

            if act == "join_room":
                target = req.get("roomId")
                pwd = req.get("password", "")
                if target not in rooms:
                    await websocket.send_text(json.dumps({"type": "chat_msg", "text": "房间不存在"}))
                    continue
                room = rooms[target]
                if room.get("password") and room["password"] != pwd:
                    await websocket.send_text(json.dumps({"type": "chat_msg", "text": "密码错误"}))
                    continue
                if len(room["uids"]) >= 2:
                    await websocket.send_text(json.dumps({"type": "chat_msg", "text": "房间已满"}))
                    continue
                room["uids"].append(username)
                room["ready"][username] = False
                room_id = target
                await websocket.send_text(json.dumps({"type": "room_joined", "roomId": room_id}))
                await broadcast_room_state(room_id)
                continue

            if act == "ready":
                if room_id in rooms:
                    rooms[room_id]["ready"][username] = req.get("ready", False)
                    await broadcast_room_state(room_id)
                continue

            if act == "start_battle":
                left_team = req.get("left_team", [])
                right_team = req.get("right_team", [])
                skip = req.get("skip", False)
                result = auto_battle(left_team, right_team, max_rounds=20)
                left_power = calculate_team_power(left_team)
                right_power = calculate_team_power(right_team)
                await websocket.send_text(json.dumps({
                    "type": "battle_result",
                    "log": result["log"],
                    "winner": result["winner"],
                    "skip": skip,
                    "left_power": left_power,
                    "right_power": right_power,
                    "left_team": result.get("left_team", []),
                    "right_team": result.get("right_team", [])
                }))
                continue

            if act == "escape":
                if room_id in rooms:
                    await broadcast(room_id, {"type": "chat_msg", "text": f"🏃 {username} 逃跑了！战斗结束"})
                await websocket.send_text(json.dumps({"type": "escape_result", "winner": "opponent"}))
                continue

            if act == "chat":
                msg = req.get("msg", "")
                is_to_gm = msg.strip().startswith("@GM01") or "@GM01" in msg
                log_gm_message(username, msg, is_to_gm)
                
                if username == "GM01" and msg.startswith("@"):
                    parts = msg.split(" ", 1)
                    cmd = parts[0].lower()
                    gm_commands = ["@公告", "@禁言", "@解禁", "@踢人"]
                    if cmd in gm_commands:
                        if cmd == "@公告" and len(parts) > 1:
                            content = parts[1]
                            await broadcast_all({"type": "gm_broadcast", "text": f"🔔 系统公告：{content}"})
                            await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"✅ 公告已发送：{content}"}))
                            continue
                        elif cmd == "@禁言" and len(parts) > 1:
                            sub_parts = parts[1].split()
                            target = sub_parts[0]
                            duration_min = 10
                            if len(sub_parts) > 1:
                                try:
                                    duration_min = int(sub_parts[1])
                                except:
                                    pass
                            if target == "GM01":
                                await websocket.send_text(json.dumps({"type": "chat_msg", "text": "❌ 不能禁言 GM01"}))
                                continue
                            until = time.time() + duration_min * 60
                            muted_users[target] = until
                            if target in users_ws:
                                try:
                                    await users_ws[target].send_text(json.dumps({"type": "muted", "text": f"你被 GM01 禁言 {duration_min} 分钟"}))
                                except:
                                    pass
                            await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"✅ 已禁言 {target} {duration_min} 分钟"}))
                            continue
                        elif cmd == "@解禁" and len(parts) > 1:
                            target = parts[1].strip()
                            if target in muted_users:
                                del muted_users[target]
                                if target in users_ws:
                                    try:
                                        await users_ws[target].send_text(json.dumps({"type": "unmuted", "text": "你已被 GM01 解除禁言"}))
                                    except:
                                        pass
                                await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"✅ 已解禁 {target}"}))
                            else:
                                await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"❌ {target} 未被禁言"}))
                            continue
                        elif cmd == "@踢人" and len(parts) > 1:
                            target = parts[1].strip()
                            if target == "GM01":
                                await websocket.send_text(json.dumps({"type": "chat_msg", "text": "❌ 不能踢出 GM01"}))
                                continue
                            if target in users_ws:
                                try:
                                    await users_ws[target].send_text(json.dumps({"type": "kicked", "text": "你被 GM01 踢出服务器"}))
                                    await users_ws[target].close()
                                    users_ws.pop(target, None)
                                    await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"✅ 已将 {target} 踢出服务器"}))
                                except Exception as e:
                                    await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"❌ 踢出失败: {str(e)}"}))
                            else:
                                await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"❌ 用户 {target} 不在线"}))
                            continue
                
                if username in muted_users:
                    until = muted_users[username]
                    if time.time() < until:
                        remain = int(until - time.time())
                        await websocket.send_text(json.dumps({"type": "chat_msg", "text": f"⛔ 你被禁言中，剩余 {remain} 秒"}))
                        continue
                    else:
                        del muted_users[username]
                
                sender_blacklist = get_blacklist(username)
                for u, ws_conn in users_ws.items():
                    if u == username:
                        continue
                    if u in sender_blacklist:
                        continue
                    receiver_blacklist = get_blacklist(u)
                    if username in receiver_blacklist:
                        continue
                    try:
                        await ws_conn.send_text(json.dumps({"type": "chat_msg", "text": f"💬 {username}: {filter_msg(msg)}"}))
                    except:
                        pass
                continue

            if act == "friend_list_update":
                target = req.get("target")
                if target and target in users_ws:
                    await users_ws[target].send_text(json.dumps({"type": "friend_list_update"}))
                continue

            if act == "leave_room":
                if room_id in rooms:
                    room = rooms[room_id]
                    if username in room["uids"]:
                        room["uids"].remove(username)
                        room["ready"].pop(username, None)
                        await broadcast(room_id, {"type": "chat_msg", "text": f"{username} 离开了房间"})
                        if len(room["uids"]) == 0:
                            rooms.pop(room_id, None)
                        else:
                            await broadcast_room_state(room_id)
                room_id = None
                continue

    except WebSocketDisconnect:
        if username and room_id and room_id in rooms:
            room = rooms[room_id]
            if username in room["uids"]:
                room["uids"].remove(username)
            await broadcast_room_state(room_id)
        if username in users_ws:
            users_ws.pop(username, None)
    except Exception as e:
        print(f"WebSocket异常: {e}")

@app.get("/api/occupied_list")
async def get_occupied_list(username: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, occupied_by, occupied_time FROM users WHERE occupied_by=?", (username,))
    rows = c.fetchall()
    conn.close()
    result = []
    for row in rows:
        occupied_name = row[0]
        # 不再返回剩余时间，前端无需倒计时
        result.append({
            "name": occupied_name,
            "avatar": get_user(occupied_name).get("avatar", "hero.png"),
            "remain_seconds": 0,
            "expired": False
        })
    return {"success": True, "list": result}

@app.get("/api/occupier_info")
async def get_occupier_info(username: str):
    occupier = get_occupier(username)
    if occupier:
        user = get_user(occupier)
        return {"success": True, "occupier": occupier, "avatar": user.get("avatar", "hero.png")}
    return {"success": True, "occupier": None}