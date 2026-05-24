# add_gems_to_gm.py - 为 GM01 生成 100 个各种宝石（堆叠）
import sqlite3
import json
import random
from core import DB_PATH

# 宝石基础定义
GEM_TYPES = [
    {"attr": "strength", "name": "力量宝石"},
    {"attr": "intelligence", "name": "智力宝石"},
    {"attr": "speed", "name": "敏捷宝石"},
    {"attr": "hp", "name": "生命宝石"}
]
STARS = [1, 2, 3, 4, 5]
COUNT_PER_TYPE_STAR = 100  # 每种星级每种属性生成100个（合并成一个堆叠项）

def create_gem(attr: str, star: int, count: int) -> dict:
    """创建可堆叠的宝石数据"""
    ranges = {1: (1,2), 2: (3,5), 3: (6,9), 4: (10,14), 5: (15,20)}
    min_val, max_val = ranges.get(star, (1,1))
    value = random.randint(min_val, max_val)
    gem_id = f"gem_{attr}_{star}_{value}_batch"
    return {
        "id": gem_id,
        "attr": attr,
        "name": GEM_TYPES[[t["attr"] for t in GEM_TYPES].index(attr)]["name"],
        "star": star,
        "value": value,
        "double_attr": None,
        "count": count
    }

def add_gems_to_gm():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 获取 GM01 的 items
    c.execute("SELECT items FROM users WHERE username='GM01'")
    row = c.fetchone()
    if not row:
        print("GM01 用户不存在")
        return
    items = json.loads(row[0]) if row[0] else {}
    # 生成宝石
    for gem_type in GEM_TYPES:
        for star in STARS:
            gem = create_gem(gem_type["attr"], star, COUNT_PER_TYPE_STAR)
            gem_id = gem["id"]
            if gem_id in items:
                items[gem_id]["count"] += COUNT_PER_TYPE_STAR
            else:
                items[gem_id] = gem
    # 更新数据库
    c.execute("UPDATE users SET items = ? WHERE username='GM01'", (json.dumps(items, ensure_ascii=False),))
    conn.commit()
    conn.close()
    print(f"✅ 已为 GM01 添加宝石，每种属性各星级 {COUNT_PER_TYPE_STAR} 个，共 {len(GEM_TYPES)*len(STARS)} 种堆叠项。")

if __name__ == "__main__":
    add_gems_to_gm()