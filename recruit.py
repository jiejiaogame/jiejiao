# recruit.py - 完整版（支持占领满10分钟招募、权重商店、武将过滤enabled）
import os
import random
import sqlite3
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from core import get_user, update_user_items, DB_PATH, is_occupied_by

router = APIRouter(prefix="/recruit", tags=["recruit"])

_broadcast_all = None

def set_broadcast_all_func(func):
    global _broadcast_all
    _broadcast_all = func

# ---------- 加载自定义武将（5星满属性）----------
def load_heroes_from_json():
    """从 data/custom_heroes.json 读取武将列表，只返回 enabled=True 的武将"""
    try:
        with open("data/custom_heroes.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            heroes = data.get("heroes", [])
            # 过滤：只保留 enabled 为 True 的（默认 True 如果字段不存在）
            heroes = [h for h in heroes if h.get("enabled", True)]
    except FileNotFoundError:
        # 默认武将（已启用）
        default_heroes = [
            {"id": "duobao", "name": "多宝道人", "star5_hp": 48, "star5_strength": 22,
             "star5_intelligence": 28, "star5_speed": 24, "skill_desc": "万宝朝宗", "weight": 100, "enabled": True},
            {"id": "jinling", "name": "金灵圣母", "star5_hp": 45, "star5_strength": 25,
             "star5_intelligence": 26, "star5_speed": 22, "weight": 90, "enabled": True},
            {"id": "wudang", "name": "无当圣母", "star5_hp": 44, "star5_strength": 24,
             "star5_intelligence": 27, "star5_speed": 23, "weight": 90, "enabled": True},
            {"id": "guiling", "name": "龟灵圣母", "star5_hp": 50, "star5_strength": 23,
             "star5_intelligence": 24, "star5_speed": 20, "weight": 85, "enabled": True},
            {"id": "yunxiao", "name": "云霄仙子", "star5_hp": 46, "star5_strength": 21,
             "star5_intelligence": 30, "star5_speed": 25, "weight": 95, "enabled": True},
            {"id": "qiongxiao", "name": "琼霄仙子", "star5_hp": 45, "star5_strength": 22,
             "star5_intelligence": 29, "star5_speed": 24, "weight": 95, "enabled": True},
            {"id": "bixiao", "name": "碧霄仙子", "star5_hp": 44, "star5_strength": 23,
             "star5_intelligence": 28, "star5_speed": 26, "weight": 95, "enabled": True},
            {"id": "zhaogongming", "name": "赵公明", "star5_hp": 52, "star5_strength": 28,
             "star5_intelligence": 22, "star5_speed": 21, "weight": 80, "enabled": True},
        ]
        os.makedirs("data", exist_ok=True)
        with open("data/custom_heroes.json", "w", encoding="utf-8") as f:
            json.dump({"heroes": default_heroes}, f, ensure_ascii=False, indent=2)
        heroes = default_heroes
    return heroes

def select_weighted_hero(heroes_list):
    """根据权重随机选一个武将，并决定实际星级（1-4星）"""
    total_weight = sum(h.get("weight", 50) for h in heroes_list)
    if total_weight == 0:
        hero = random.choice(heroes_list)
    else:
        rand = random.randint(1, total_weight)
        cumulative = 0
        for h in heroes_list:
            cumulative += h.get("weight", 50)
            if rand <= cumulative:
                hero = h
                break
        else:
            hero = heroes_list[0]
    # 星级分配：1星10%，2星20%，3星40%，4星30%
    possible = [1, 2, 3, 4]
    weights = [0.1, 0.2, 0.4, 0.3]
    actual_star = random.choices(possible, weights=weights)[0]
    return hero, actual_star

def generate_recruit_shop(username):
    """生成3个不同的武将（不重复）"""
    all_heroes = load_heroes_from_json()
    if len(all_heroes) < 3:
        selected = random.choices(all_heroes, k=3)
    else:
        selected = []
        while len(selected) < 3:
            hero, star = select_weighted_hero(all_heroes)
            if hero["name"] not in [h[0]["name"] for h in selected]:
                selected.append((hero, star))
    shop = {}
    for hero, star in selected:
        cost = {1: 100, 2: 150, 3: 200, 4: 500}.get(star, 100)
        shop[hero["name"]] = {
            "star": star,
            "cost": cost,
            "type": "normal",
            "hero_id": hero["id"],
            "skill_desc": hero.get("skill_desc", "")
        }
    return shop

@router.get("/shop")
async def get_recruit_shop(username: str):
    user = get_user(username)
    if not user:
        return {"error": "用户不存在"}
    recruit_shop = user.get("recruit_shop")
    refresh_time = user.get("recruit_refresh_time")
    now = datetime.now()
    need_refresh = False
    if not recruit_shop:
        need_refresh = True
    elif refresh_time:
        try:
            refresh_dt = datetime.fromisoformat(refresh_time)
            if now >= refresh_dt:
                need_refresh = True
        except:
            need_refresh = True
    else:
        need_refresh = True
    if need_refresh:
        recruit_shop = generate_recruit_shop(username)
        new_refresh_time = (now + timedelta(minutes=20)).isoformat()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET recruit_shop=?, recruit_refresh_time=? WHERE username=?",
                  (json.dumps(recruit_shop, ensure_ascii=False), new_refresh_time, username))
        conn.commit()
        conn.close()
        refresh_time = new_refresh_time
    else:
        if isinstance(recruit_shop, str):
            recruit_shop = json.loads(recruit_shop)
    return {
        "shop": recruit_shop,
        "next_refresh": refresh_time,
        "gold": user.get("gold", 0)
    }

@router.post("/refresh")
async def refresh_recruit_shop(req: Request):
    data = await req.json()
    username = data.get("username")
    use_gold = data.get("use_gold", False)
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    gold = user.get("gold", 0)
    now = datetime.now()
    refresh_time = user.get("recruit_refresh_time")
    free_available = False
    if refresh_time:
        try:
            refresh_dt = datetime.fromisoformat(refresh_time)
            if now >= refresh_dt:
                free_available = True
        except:
            free_available = True
    else:
        free_available = True
    if use_gold:
        if gold < 100:
            return {"success": False, "msg": f"金币不足100，当前只有{gold}金币"}
        update_user_items(username, -100, 0)
    else:
        if not free_available:
            return {"success": False, "msg": "免费刷新时间未到，请等待或使用100金币刷新"}
    new_shop = generate_recruit_shop(username)
    new_refresh_time = (now + timedelta(minutes=20)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET recruit_shop=?, recruit_refresh_time=? WHERE username=?",
              (json.dumps(new_shop, ensure_ascii=False), new_refresh_time, username))
    conn.commit()
    conn.close()
    user = get_user(username)
    return {
        "success": True,
        "shop": new_shop,
        "next_refresh": new_refresh_time,
        "gold": user.get("gold", 0)
    }

@router.post("/hire")
async def hire_hero(req: Request):
    data = await req.json()
    username = data.get("username")
    hero_name = data.get("hero_name")
    user = get_user(username)
    if not user:
        return {"success": False, "msg": "用户不存在"}
    recruit_shop = user.get("recruit_shop")
    if isinstance(recruit_shop, str):
        recruit_shop = json.loads(recruit_shop)
    if not recruit_shop or hero_name not in recruit_shop:
        return {"success": False, "msg": "该武将不在招贤馆中"}
    hero_info = recruit_shop[hero_name]
    star = hero_info["star"]
    cost = hero_info["cost"]
    gold = user.get("gold", 0)
    if gold < cost:
        return {"success": False, "msg": f"金币不足，需要{cost}金币"}
    heroes_list = user.get("heroes", [])
    if hero_name in heroes_list:
        return {"success": False, "msg": f"你已经拥有{hero_name}，不能重复招募"}
    new_gold = gold - cost
    heroes_list.append(hero_name)
    star_heroes = user.get("star_heroes", {})
    star_heroes[hero_name] = star
    # 从商店删除已招募的武将
    recruit_shop.pop(hero_name, None)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET gold=?, star_heroes=?, heroes=?, recruit_shop=? WHERE username=?",
              (new_gold, json.dumps(star_heroes, ensure_ascii=False),
               json.dumps(heroes_list, ensure_ascii=False),
               json.dumps(recruit_shop, ensure_ascii=False), username))
    conn.commit()
    conn.close()
    if star >= 4 and _broadcast_all:
        await _broadcast_all({
            "type": "broadcast_notice",
            "message": f"🎉 恭喜 {username} 获得 {star}星 {hero_name}！"
        })
    return {
        "success": True,
        "msg": f"成功招募{star}星{hero_name}",
        "star": star,
        "hero_name": hero_name,
        "gold": new_gold,
        "remaining_shop": recruit_shop
    }

# ========== 查看被占领玩家的商店（只读，不可刷新） ==========
@router.get("/other_shop")
async def get_other_shop(req: Request):
    """
    占领者查看被占领玩家的招贤馆商店
    参数：
        username: 占领者
        target: 被占领的玩家
    """
    username = req.query_params.get("username")
    target = req.query_params.get("target")
    if not username or not target:
        return {"error": "参数不足"}
    # 检查占领关系：username 是否占领了 target
    if not is_occupied_by(username, target):
        return {"error": "你没有占领该玩家，不能访问其商店"}
    user = get_user(target)
    if not user:
        return {"error": "目标用户不存在"}
    recruit_shop = user.get("recruit_shop")
    if isinstance(recruit_shop, str):
        recruit_shop = json.loads(recruit_shop)
    # 只返回商店内容，不返回刷新时间（不允许刷新）
    return {
        "success": True,
        "shop": recruit_shop,
        "target": target,
        "gold": user.get("gold", 0)  # 仅是展示，实际招募还是消耗占领者金币
    }

# ========== 占领者从被占领者商店招募（消耗占领者金币，武将归占领者，需占领满10分钟） ==========
@router.post("/hire_from_occupied")
async def hire_from_occupied(req: Request):
    data = await req.json()
    username = data.get("username")   # 占领者
    target = data.get("target")       # 被占领者
    hero_name = data.get("hero_name")
    
    if not username or not target or not hero_name:
        return {"success": False, "msg": "参数不足"}
    
    # 检查占领关系
    if not is_occupied_by(username, target):
        return {"success": False, "msg": "你没有占领该玩家，不能从其商店招募"}
    
    # 获取被占领者的商店
    user_target = get_user(target)
    if not user_target:
        return {"success": False, "msg": "目标用户不存在"}
    
    # 检查占领时间是否满10分钟
    occupied_time_str = user_target.get("occupied_time")
    if not occupied_time_str:
        return {"success": False, "msg": "该玩家未被占领或占领信息异常"}
    try:
        from datetime import datetime
        occupied_dt = datetime.fromisoformat(occupied_time_str)
        elapsed = (datetime.now() - occupied_dt).total_seconds()
        if elapsed < 600:
            remain = int(600 - elapsed)
            return {"success": False, "msg": f"占领未满10分钟，还需等待 {remain} 秒才能招募"}
    except Exception as e:
        return {"success": False, "msg": "占领时间格式错误"}
    
    recruit_shop = user_target.get("recruit_shop")
    if isinstance(recruit_shop, str):
        recruit_shop = json.loads(recruit_shop)
    if not recruit_shop or hero_name not in recruit_shop:
        return {"success": False, "msg": "该武将不在对方商店中"}
    
    hero_info = recruit_shop[hero_name]
    star = hero_info["star"]
    cost = hero_info["cost"]
    
    # 占领者支付金币
    user_occupier = get_user(username)
    if user_occupier.get("gold", 0) < cost:
        return {"success": False, "msg": f"金币不足，需要{cost}金币"}
    
    # 占领者获得武将
    heroes_occ = user_occupier.get("heroes", [])
    if hero_name in heroes_occ:
        return {"success": False, "msg": f"你已经拥有{hero_name}，不能重复招募"}
    heroes_occ.append(hero_name)
    star_heroes_occ = user_occupier.get("star_heroes", {})
    star_heroes_occ[hero_name] = star
    
    # 扣除占领者金币
    new_gold_occ = user_occupier["gold"] - cost
    
    # 从被占领者商店移除该武将
    recruit_shop.pop(hero_name, None)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 更新占领者数据
    c.execute("UPDATE users SET gold=?, heroes=?, star_heroes=? WHERE username=?",
              (new_gold_occ, json.dumps(heroes_occ, ensure_ascii=False),
               json.dumps(star_heroes_occ, ensure_ascii=False), username))
    # 更新被占领者商店
    c.execute("UPDATE users SET recruit_shop=? WHERE username=?",
              (json.dumps(recruit_shop, ensure_ascii=False), target))
    conn.commit()
    conn.close()
    
    if star >= 4 and _broadcast_all:
        await _broadcast_all({
            "type": "broadcast_notice",
            "message": f"🎉 恭喜 {username} 通过占领分舵获得 {star}星 {hero_name}！"
        })
    
    return {
        "success": True,
        "msg": f"成功从 {target} 的商店招募 {star}星 {hero_name}",
        "star": star,
        "hero_name": hero_name
    }