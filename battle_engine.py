# battle_engine.py - 最终版（支持中毒持续伤害、增益、群体单条日志；多目标技能统一群体动画）
import random
import copy
import re
from typing import List, Dict, Any, Tuple

from skill_engine import (
    resolve_skill, apply_skill, select_targets, can_act,
    is_skill_blocked_by_silence, update_status_duration
)

# ========== 等级与经验计算 ==========
EXP_BASE = 100
EXP_GROWTH = 20
EXP_POW = 1.5

def calc_level(exp: int) -> Tuple[int, int, int]:
    level = 1
    while True:
        need = int(EXP_BASE + EXP_GROWTH * (level - 1) + EXP_POW * (level ** 1.5))
        if exp < need:
            return level, exp, need
        exp -= need
        level += 1
        if level >= 100:
            return 100, 0, 0

def get_final_attrs(hero: Dict) -> Dict:
    star = hero.get('star', 1)
    level = hero.get('level', 1)
    base = hero.get('base_attrs', {})
    bonus = hero.get('bonus_attrs', {})

    auto_hp = star * 0.5 * (level - 1)
    auto_str = star * 0.2 * (level - 1)
    auto_int = star * 0.2 * (level - 1)
    auto_spd = star * 0.15 * (level - 1)

    final = {
        'hp': base.get('hp', 30) + bonus.get('hp', 0) + auto_hp,
        'strength': base.get('strength', 10) + bonus.get('strength', 0) + auto_str,
        'intelligence': base.get('intelligence', 10) + bonus.get('intelligence', 0) + auto_int,
        'speed': base.get('speed', 20) + bonus.get('speed', 0) + auto_spd
    }
    for k in final:
        final[k] = int(final[k])
    return final

def calculate_hero_power(hero: Dict) -> int:
    final = get_final_attrs(hero)
    base = (final['hp'] * 0.2) + (final['strength'] * 2.5) + (final['intelligence'] * 2.5) + (final['speed'] * 1.5)
    skill = hero.get('skill')
    skill_type = skill.get('type', 'physical') if skill else 'none'
    multiplier = {
        'physical': 1.2,
        'magic': 1.2,
        'hybrid': 1.3,
        'control': 0.9,
        'support': 0.7,
        'none': 1.0
    }.get(skill_type, 1.0)
    return int(base * multiplier)

def calculate_team_power(team: List[Dict]) -> int:
    return sum(calculate_hero_power(hero) for hero in team)

def auto_battle(team_left: List[Dict], team_right: List[Dict], max_rounds: int = 20) -> Dict:
    left = copy.deepcopy(team_left)
    right = copy.deepcopy(team_right)

    for h in left:
        if 'final_attrs' in h and h['final_attrs']:
            h['final'] = h['final_attrs']
        else:
            h['final'] = get_final_attrs(h)
        h['max_hp'] = h.get('maxHp', h['final'].get('hp', 0))
        if h['max_hp'] <= 0:
            h['max_hp'] = 100
        h['current_hp'] = h['max_hp']
        h['shield'] = 0
        h['team'] = 'left'
        if 'skill' in h and h['skill']:
            h['skill_obj'] = resolve_skill(h['skill'])
        else:
            h['skill_obj'] = None

    for h in right:
        if 'final_attrs' in h and h['final_attrs']:
            h['final'] = h['final_attrs']
        else:
            h['final'] = get_final_attrs(h)
        h['max_hp'] = h.get('maxHp', h['final'].get('hp', 0))
        if h['max_hp'] <= 0:
            h['max_hp'] = 100
        h['current_hp'] = h['max_hp']
        h['shield'] = 0
        h['team'] = 'right'
        if 'skill' in h and h['skill']:
            h['skill_obj'] = resolve_skill(h['skill'])
        else:
            h['skill_obj'] = None

    battle_context = {'status': {}}
    log = []
    round_num = 0

    def is_alive(hero):
        return hero['current_hp'] > 0

    def get_alive_units():
        return [h for h in left + right if is_alive(h)]

    while round_num < max_rounds:
        round_num += 1
        units = sorted(get_alive_units(), key=lambda x: x['final']['speed'], reverse=True)

        for attacker in units:
            if not is_alive(attacker):
                continue
            uid = attacker.get('id', attacker.get('name'))
            status_dict = battle_context['status'].get(uid, {})
            if 'stun' in status_dict:
                log.append({'type': 'status', 'text': f"{attacker['name']} 处于眩晕，无法行动"})
                continue

            if attacker['team'] == 'left':
                enemies = [h for h in right if is_alive(h)]
            else:
                enemies = [h for h in left if is_alive(h)]
            if not enemies:
                break

            skill = attacker.get('skill_obj')
            can_use_skill = skill and not is_skill_blocked_by_silence(attacker, battle_context)

            if can_use_skill:
                allies = [h for h in get_alive_units() if h['team'] == attacker['team']]
                targets = select_targets(skill, attacker, allies, enemies, battle_context)
                if targets:
                    skill_logs = apply_skill(skill, attacker, targets, battle_context, round_num)
                    # 只要是多个目标，就视为群体技能（一次动画）
                    is_multi = len(targets) > 1

                    if is_multi:
                        # 群体技能：只生成一条日志，包含所有目标信息
                        all_targets_info = []
                        for i, t in enumerate(targets):
                            damage = 0
                            if i < len(skill_logs):
                                damage_match = re.search(r'造成\s*(\d+)\s*伤害', skill_logs[i])
                                damage = int(damage_match.group(1)) if damage_match else 0
                            all_targets_info.append({
                                'name': t['name'],
                                'team': t['team'],
                                'hp_left': t['current_hp'],
                                'damage': damage,
                                'dead': t['current_hp'] <= 0
                            })
                        log.append({
                            'type': 'skill',
                            'round': round_num,
                            'attacker': attacker['name'],
                            'attacker_team': attacker['team'],
                            'skill': skill.get('display_name', skill.get('name')),
                            'skill_type': skill.get('type', 'physical'),
                            'is_multi': True,
                            'targets': all_targets_info,
                            'text': f"{skill.get('display_name', skill.get('name'))} 对多个敌人造成伤害"
                        })
                    else:
                        # 单体技能
                        for idx, msg in enumerate(skill_logs):
                            damage_match = re.search(r'造成\s*(\d+)\s*伤害', msg)
                            damage = int(damage_match.group(1)) if damage_match else 0
                            current_target = targets[idx] if idx < len(targets) else targets[-1]
                            log.append({
                                'type': 'skill',
                                'round': round_num,
                                'attacker': attacker['name'],
                                'attacker_team': attacker['team'],
                                'skill': skill.get('display_name', skill.get('name')),
                                'skill_type': skill.get('type', 'physical'),
                                'text': msg,
                                'target': current_target['name'],
                                'target_team': current_target['team'],
                                'damage': damage,
                                'is_multi': False,
                                'hp_left': current_target['current_hp']
                            })
                            if current_target['current_hp'] <= 0:
                                log[-1]['dead'] = True
                else:
                    log.append({'type': 'chat_msg', 'text': f"{attacker['name']} 没有可用目标"})
            else:
                target = random.choice(enemies)
                damage = max(1, attacker['final']['strength'] + random.randint(-3, 5))
                if target.get('shield', 0) > 0:
                    absorb = min(target['shield'], damage)
                    target['shield'] -= absorb
                    damage -= absorb
                target['current_hp'] -= damage
                if target['current_hp'] < 0:
                    target['current_hp'] = 0
                log.append({
                    'type': 'attack',
                    'round': round_num,
                    'attacker': attacker['name'],
                    'attacker_team': attacker['team'],
                    'target': target['name'],
                    'target_team': target['team'],
                    'damage': damage,
                    'hp_left': target['current_hp']
                })
                if target['current_hp'] <= 0:
                    log[-1]['dead'] = True

            left_alive = sum(1 for h in left if is_alive(h))
            right_alive = sum(1 for h in right if is_alive(h))
            if left_alive == 0 or right_alive == 0:
                break

        # 回合结束：更新状态持续时间并处理中毒伤害
        poison_logs = update_status_duration(battle_context, get_alive_units())
        log.extend(poison_logs)
        
        left_alive = sum(1 for h in left if is_alive(h))
        right_alive = sum(1 for h in right if is_alive(h))
        if left_alive == 0 or right_alive == 0:
            break

    left_alive = sum(1 for h in left if h['current_hp'] > 0)
    right_alive = sum(1 for h in right if h['current_hp'] > 0)
    if left_alive > right_alive:
        winner = 'left'
    elif right_alive > left_alive:
        winner = 'right'
    else:
        winner = 'draw'

    def clean_team(team):
        return [{
            'name': h['name'],
            'hp': h['current_hp'],
            'maxHp': h['max_hp'],
            'position': h.get('position', 0),
            'team': h['team'],
            'id': h.get('id', h['name']),
            'shield': h.get('shield', 0)
        } for h in team]

    left_power = calculate_team_power(left)
    right_power = calculate_team_power(right)

    return {
        'winner': winner,
        'log': log,
        'left_team': clean_team(left),
        'right_team': clean_team(right),
        'left_power': left_power,
        'right_power': right_power
    }