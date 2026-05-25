# skill_engine.py - 技能模块化引擎（支持差值伤害、群体衰减）
import json
import random
import re
from typing import Dict, List, Any, Optional, Tuple

# ---------- 加载技能模板库 ----------
def load_skills_db() -> Dict:
    try:
        with open("data/skills.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"skills": []}

# ---------- 技能解析 ----------
def resolve_skill(hero_skill_config: Dict) -> Optional[Dict]:
    if not hero_skill_config or "base_id" not in hero_skill_config:
        return None
    base_id = hero_skill_config["base_id"]
    skills_db = load_skills_db()
    base = next((s for s in skills_db["skills"] if s["id"] == base_id), None)
    if not base:
        return None

    import copy
    skill = copy.deepcopy(base)

    if "display_name" in hero_skill_config:
        skill["display_name"] = hero_skill_config["display_name"]
    else:
        skill["display_name"] = skill.get("name", base_id)

    for key in ["target_count", "duration", "damage_coefficient", "heal_coefficient", "shield_coefficient"]:
        if key in hero_skill_config:
            skill[key] = hero_skill_config[key]

    return skill

# ---------- 判断是否为群体技能 ----------
def is_multi_target_skill(skill: Dict) -> bool:
    if not skill:
        return False
    target_type = skill.get("target_type", "")
    multi_types = ["all_enemy", "all_ally", "random_enemy", "front_row", "back_row"]
    if target_type in multi_types:
        return True
    if skill.get("target_count", 1) > 1:
        return True
    return False

# ---------- 数值计算辅助 ----------
def calculate_damage(caster: Dict, target: Dict, formula: str, skill: Dict = None, round_num: int = 1, battle_context: Dict = None) -> Tuple[int, bool]:
    """
    伤害计算公式：
    - 物理单体：力量差值 * 1.2 + 15，最小5
    - 法术单体：智力差值 * 1.2 + 15，最小5
    - 物理群体：力量差值 * 0.8 + 15，最小5
    - 法术群体：智力差值 * 0.6 + 15，最小5
    """
    caster_final = caster.get("final", {}).copy()
    target_final = target.get("final", {}).copy()
    
    # 应用增益/减益状态
    if battle_context:
        caster_id = caster.get("id", caster.get("name"))
        status = battle_context.get("status", {}).get(caster_id, {})
        if "strength_up" in status:
            caster_final["strength"] = int(caster_final.get("strength", 10) * 1.2)
        if "intelligence_up" in status:
            caster_final["intelligence"] = int(caster_final.get("intelligence", 10) * 1.2)
        if "strength_down" in status:
            caster_final["strength"] = int(caster_final.get("strength", 10) * 0.8)
        if "intelligence_down" in status:
            caster_final["intelligence"] = int(caster_final.get("intelligence", 10) * 0.8)
    
    # 判断是否为群体技能
    is_multi = False
    if skill:
        is_multi = is_multi_target_skill(skill)
    
    damage = 0
    
    # 物理伤害（基于力量差值）
    if "strength" in formula.lower():
        diff = caster_final.get("strength", 10) - target_final.get("strength", 10)
        if is_multi:
            # 物理群体：差值 * 0.8 + 15
            damage = diff * 0.8 + 15
        else:
            # 物理单体：差值 * 1.2 + 15
            damage = diff * 1.2 + 15
    
    # 法术伤害（基于智力差值）
    elif "intelligence" in formula.lower():
        diff = caster_final.get("intelligence", 10) - target_final.get("intelligence", 10)
        if is_multi:
            # 法术群体：差值 * 0.6 + 15
            damage = diff * 0.6 + 15
        else:
            # 法术单体：差值 * 1.2 + 15
            damage = diff * 1.2 + 15
    
    # 混合伤害（力量+智力差值）
    elif "hybrid" in formula.lower():
        strength_diff = caster_final.get("strength", 10) - target_final.get("strength", 10)
        int_diff = caster_final.get("intelligence", 10) - target_final.get("intelligence", 10)
        damage = (strength_diff + int_diff) * 0.8 + 15
        if is_multi:
            damage = damage * 0.8
    
    else:
        damage = 10
    
    damage = max(5, int(damage))
    
    # 暴击处理
    is_crit = False
    if skill:
        crit_rate = skill.get("crit_rate", 0)
        crit_round_start = skill.get("crit_round_start", 1)
        if crit_rate > 0 and round_num >= crit_round_start:
            if random.random() < crit_rate:
                damage = int(damage * 2)
                is_crit = True
    
    return damage, is_crit

def calculate_heal(caster: Dict, target: Dict, formula: str) -> int:
    caster_final = caster.get("final", {})
    if "intelligence" in formula:
        coeff = float(formula.split("*")[1]) if "*" in formula else 1.0
        heal = caster_final.get("intelligence", 10) * coeff
    else:
        heal = 10
    return max(1, int(heal))

def calculate_shield(caster: Dict, formula: str) -> int:
    caster_final = caster.get("final", {})
    if "strength" in formula:
        coeff = float(formula.split("*")[1]) if "*" in formula else 1.0
        shield = caster_final.get("strength", 10) * coeff
    elif "intelligence" in formula:
        coeff = float(formula.split("*")[1]) if "*" in formula else 1.0
        shield = caster_final.get("intelligence", 10) * coeff
    else:
        shield = 10
    return max(1, int(shield))

def apply_effect(effect: Dict, caster: Dict, target: Dict, battle_context: Dict):
    if random.random() > effect.get("probability", 1.0):
        return
    effect_type = effect["type"]
    duration = effect.get("duration", 1)
    if "status" not in battle_context:
        battle_context["status"] = {}
    target_id = target.get("id", target.get("name"))
    if target_id not in battle_context["status"]:
        battle_context["status"][target_id] = {}
    battle_context["status"][target_id][effect_type] = duration

def apply_damage(target: Dict, damage: int):
    shield = target.get("shield", 0)
    if shield > 0:
        absorb = min(shield, damage)
        target["shield"] = shield - absorb
        damage -= absorb
    target["current_hp"] -= damage
    if target["current_hp"] < 0:
        target["current_hp"] = 0

# ---------- 执行技能核心 ----------
def apply_skill(skill: Dict, caster: Dict, targets: List[Dict], battle_context: Dict, round_num: int = 1) -> List[str]:
    logs = []
    skill_type = skill.get("type", "physical")
    
    if skill_type in ["physical", "magic", "hybrid"]:
        for t in targets:
            dmg, is_crit = calculate_damage(caster, t, skill.get("damage_formula", "strength"), skill, round_num, battle_context)
            apply_damage(t, dmg)
            crit_text = "（暴击！）" if is_crit else ""
            logs.append(f"{skill.get('display_name', skill.get('name'))} 对 {t.get('name')} 造成 {dmg} 伤害{crit_text}")
            for eff in skill.get("effects", []):
                apply_effect(eff, caster, t, battle_context)
    elif skill_type == "heal":
        for t in targets:
            heal = calculate_heal(caster, t, skill.get("heal_formula", "intelligence * 1.0"))
            t["current_hp"] = min(t["current_hp"] + heal, t.get("max_hp", t.get("final", {}).get("hp", 100)))
            logs.append(f"{skill.get('display_name', skill.get('name'))} 治疗 {t.get('name')} {heal} 生命")
            for eff in skill.get("effects", []):
                apply_effect(eff, caster, t, battle_context)
    elif skill_type == "shield":
        for t in targets:
            shield_val = calculate_shield(caster, skill.get("shield_formula", "strength * 1.0"))
            t["shield"] = shield_val
            logs.append(f"{skill.get('display_name', skill.get('name'))} 为 {t.get('name')} 附加 {shield_val} 护盾")
            for eff in skill.get("effects", []):
                apply_effect(eff, caster, t, battle_context)
    elif skill_type == "buff":
        for t in targets:
            logs.append(f"{skill.get('display_name', skill.get('name'))} 对 {t.get('name')} 施加增益")
            for eff in skill.get("effects", []):
                apply_effect(eff, caster, t, battle_context)
    elif skill_type == "debuff":
        for t in targets:
            logs.append(f"{skill.get('display_name', skill.get('name'))} 对 {t.get('name')} 施加减益")
            for eff in skill.get("effects", []):
                apply_effect(eff, caster, t, battle_context)
    elif skill_type == "control":
        for t in targets:
            dmg, is_crit = calculate_damage(caster, t, skill.get("damage_formula", "strength"), skill, round_num, battle_context)
            apply_damage(t, dmg)
            crit_text = "（暴击！）" if is_crit else ""
            logs.append(f"{skill.get('display_name', skill.get('name'))} 对 {t.get('name')} 造成 {dmg} 伤害{crit_text}并附加控制")
            for eff in skill.get("effects", []):
                apply_effect(eff, caster, t, battle_context)
    else:
        logs.append(f"未知技能类型: {skill_type}")
    return logs

# ---------- 回合结束状态更新（含中毒伤害） ----------
def update_status_duration(battle_context: Dict, units: List[Dict] = None) -> List[Dict]:
    """
    减少状态持续时间，并返回中毒扣血日志（如果 units 提供）
    """
    poison_logs = []
    if "status" not in battle_context:
        return poison_logs
    to_remove = []
    for target_id, states in battle_context["status"].items():
        for state_type, duration in list(states.items()):
            if duration <= 1:
                del states[state_type]
            else:
                states[state_type] = duration - 1
        if not states:
            to_remove.append(target_id)
    for tid in to_remove:
        del battle_context["status"][tid]
    
    # 中毒伤害处理
    if units:
        for unit in units:
            uid = unit.get("id", unit.get("name"))
            status = battle_context.get("status", {}).get(uid, {})
            if "poison" in status:
                poison_damage = 10
                if unit.get("shield", 0) > 0:
                    absorb = min(unit["shield"], poison_damage)
                    unit["shield"] -= absorb
                    poison_damage -= absorb
                unit["current_hp"] -= poison_damage
                if unit["current_hp"] < 0:
                    unit["current_hp"] = 0
                poison_logs.append({'type': 'status', 'text': f"{unit['name']} 中毒，受到 {poison_damage} 伤害"})
    return poison_logs

def can_act(unit: Dict, battle_context: Dict) -> Tuple[bool, str]:
    unit_id = unit.get("id", unit.get("name"))
    status = battle_context.get("status", {}).get(unit_id, {})
    if "stun" in status:
        return False, "眩晕"
    if "silence" in status:
        return True, "沉默"
    return True, ""

def is_skill_blocked_by_silence(unit: Dict, battle_context: Dict) -> bool:
    unit_id = unit.get("id", unit.get("name"))
    status = battle_context.get("status", {}).get(unit_id, {})
    return "silence" in status

# ---------- 辅助函数：选择目标 ----------
def select_targets(skill: Dict, caster: Dict, allies: List[Dict], enemies: List[Dict], 
                   battle_context: Dict) -> List[Dict]:
    target_type = skill.get("target_type", "single_enemy")
    count = skill.get("target_count", 1)
    if target_type == "self":
        return [caster]
    if target_type == "ally_lowest_hp":
        if not allies:
            return []
        sorted_allies = sorted(allies, key=lambda x: x.get("current_hp", 0))
        return sorted_allies[:count] if count > 1 else [sorted_allies[0]]
    if target_type == "ally_all":
        return allies[:]
    if target_type == "single_enemy":
        if not enemies:
            return []
        return [min(enemies, key=lambda x: x.get("current_hp", 0))]
    if target_type == "single_enemy_lowest_hp":
        if not enemies:
            return []
        return [min(enemies, key=lambda x: x.get("current_hp", 0))]
    if target_type == "single_enemy_highest_int":
        if not enemies:
            return []
        return [max(enemies, key=lambda x: x.get("final", {}).get("intelligence", 0))]
    if target_type == "random_enemy":
        if not enemies:
            return []
        if count == 1:
            return [random.choice(enemies)]
        else:
            return random.sample(enemies, min(count, len(enemies)))
    if target_type == "front_row":
        front = [e for e in enemies if e.get("position", 0) < 3]
        return front if front else enemies[:2]
    if target_type == "back_row":
        back = [e for e in enemies if e.get("position", 0) >= 3]
        return back if back else enemies[2:]
    if target_type == "all_enemy":
        return enemies[:]
    return [enemies[0]] if enemies else []