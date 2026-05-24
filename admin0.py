# admin.py - 完整GM后台（清除占领使用 release_user，支持权重编辑、聊天记录查看）
import json
import os
import sqlite3
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from core import get_user, hash_pwd, update_user_items, DB_PATH, release_user

router = APIRouter(prefix="/admin", tags=["admin"])

GM_USERNAME = "GM01"
GM_PASSWORD_HASH = hash_pwd("gm123456")

# ---------- 辅助函数 ----------
def is_gm(username: str, password: str) -> bool:
    if username != GM_USERNAME:
        return False
    user = get_user(username)
    return user and user["password"] == GM_PASSWORD_HASH

def load_custom_heroes():
    path = "data/custom_heroes.json"
    if not os.path.exists(path):
        default = {"heroes": []}
        os.makedirs("data", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_custom_heroes(data):
    with open("data/custom_heroes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_challenges():
    path = "data/challenges.json"
    if not os.path.exists(path):
        default = {"challenges": []}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_challenges(data):
    with open("data/challenges.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_skills():
    path = "data/skills.json"
    if not os.path.exists(path):
        default = {"skills": []}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_skills(data):
    with open("data/skills.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, gold, ingots, reg_time FROM users WHERE username != 'GM01' ORDER BY reg_time DESC")
    rows = c.fetchall()
    conn.close()
    return [{"username": r[0], "gold": r[1], "ingots": r[2], "reg_time": r[3]} for r in rows]

def get_online_users():
    from core import users_ws
    return list(users_ws.keys())

def get_all_heroes():
    custom = load_custom_heroes()
    return custom.get("heroes", [])

def get_all_skills():
    skills = load_skills()
    return skills.get("skills", [])

# ---------- HTML 页面 ----------
@router.get("/gm")
async def gm_panel(username: str, password: str):
    if not is_gm(username, password):
        raise HTTPException(status_code=403, detail="无权限")

    heroes = get_all_heroes()
    users = get_all_users()
    online = get_online_users()
    challenges = load_challenges()
    skills = get_all_skills()
    import json as jsonlib
    challenges_json = jsonlib.dumps(challenges.get("challenges", []))

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>截教GM后台</title>
    <style>
        body {{ background: #0a0f1a; color: #eee; font-family: monospace; padding: 20px; }}
        h1 {{ color: gold; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #555; padding: 8px; text-align: left; }}
        th {{ background: #2c3e2f; }}
        input, select, button {{ padding: 5px 10px; margin: 5px; }}
        .tab {{ display: flex; gap: 15px; margin-bottom: 20px; }}
        .tab-btn {{ background: #2c3e2f; border: none; padding: 8px 20px; cursor: pointer; }}
        .tab-btn.active {{ background: gold; color: black; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .skill-row {{ margin-bottom: 15px; border:1px solid #555; padding:10px; border-radius:8px; }}
        .modal {{ position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; display:none; justify-content:center; align-items:center; }}
        .modal-content {{ background:#2c3e2f; padding:20px; border-radius:20px; width:80%; max-width:800px; max-height:80%; overflow:auto; }}
        .weight-input {{ width: 60px; }}
        .chat-log-btn {{ background: #5a7a5a; }}
    </style>
</head>
<body>
<h1>🔧 截教GM后台</h1>
<div class="tab">
    <button class="tab-btn active" data-tab="players">👥 玩家管理</button>
    <button class="tab-btn" data-tab="heroes">⚔️ 武将管理</button>
    <button class="tab-btn" data-tab="challenges">🏆 副本管理</button>
    <button class="tab-btn" data-tab="skills">✨ 技能模板</button>
    <button class="tab-btn" data-tab="chatlog">📜 聊天记录</button>
</div>

<!-- 玩家管理 -->
<div id="tab-players" class="tab-content active">
    <h3>在线玩家: {len(online)}</h3>
    <table id="playerTable">
        <thead>
            <tr><th>用户名</th><th>金币</th><th>元宝</th><th>注册时间</th><th>聊天记录</th><th>清除占领</th><th>操作</th></tr>
        </thead>
        <tbody>
    """
    for u in users:
        html += f"""
            <tr>
                <td>{u['username']}</td>
                <td><input type="number" id="gold_{u['username']}" value="{u['gold']}" step="100"></td>
                <td><input type="number" id="ingots_{u['username']}" value="{u['ingots']}" step="100"></td>
                <td>{u['reg_time'][:16] if u['reg_time'] else '-'}</td>
                <td><button onclick="viewChatLog('{u['username']}')" class="chat-log-btn">📜 查看</button></td>
                <td><button onclick="clearOccupation('{u['username']}')" style="background:#8a5a5a;">🗑️ 清除占领</button></td>
                <td><button onclick="updatePlayer('{u['username']}')">保存</button></td>
            </tr>
        """
    html += """
        </tbody>
    </table>
</div>

<!-- 武将管理 -->
<div id="tab-heroes" class="tab-content">
    <h3>自定义武将（5星满属性）</h3>
    <button onclick="showAddHeroForm()">➕ 添加武将</button>
    <table id="heroTable">
        <thead>
            <tr><th>ID</th><th>名称</th><th>生命</th><th>力量</th><th>智力</th><th>敏捷</th><th>技能</th><th>权重</th><th>状态</th><th>操作</th></tr>
        </thead>
        <tbody>
    """
    for h in heroes:
        skill_info = f"{h.get('skill', {}).get('display_name', '无')} (原:{h.get('skill', {}).get('base_id', '')})"
        enabled_status = "✅" if h.get("enabled", True) else "❌"
        weight = h.get("weight", 50)
        html += f"""
            <tr data-id="{h['id']}">
                <td>{h['id']}</td>
                <td>{h['name']}</td>
                <td>{h['star5_hp']}</td>
                <td>{h['star5_strength']}</td>
                <td>{h['star5_intelligence']}</td>
                <td>{h['star5_speed']}</td>
                <td>{skill_info}</td>
                <td>
                    <input type="number" id="weight_{h['id']}" value="{weight}" class="weight-input" step="1" min="1">
                    <button onclick="updateHeroWeight('{h['id']}')">保存权重</button>
                </td>
                <td id="status_{h['id']}">{enabled_status}</td>
                <td>
                    <button onclick="deleteHero('{h['id']}')">删除</button>
                    <button onclick="toggleHero('{h['id']}')">{"禁用" if h.get("enabled", True) else "启用"}</button>
                </td>
            </tr>
        """
    html += """
        </tbody>
    </table>
    <div id="addHeroForm" style="display:none; margin-top:20px; background:#2c3e2f; padding:15px; border-radius:12px;">
        <h4>新增武将</h4>
        <input id="hero_id" placeholder="ID(英文)"> <input id="hero_name" placeholder="名称">
        <input id="hero_hp" placeholder="生命"> <input id="hero_str" placeholder="力量">
        <input id="hero_int" placeholder="智力"> <input id="hero_spd" placeholder="敏捷">
        <select id="hero_skill_id"><option value="">无技能</option>
    """
    for s in skills:
        html += f"<option value='{s['id']}'>{s['name']}</option>"
    html += """
        </select>
        <input id="skill_display_name" placeholder="技能显示名称(可选)">
        <input id="skill_target_count" placeholder="目标数量覆盖(可选)" size="5">
        <input id="skill_duration" placeholder="持续回合覆盖(可选)" size="5">
        <input id="skill_coeff" placeholder="伤害系数覆盖(可选)" size="5">
        <input id="hero_weight" placeholder="权重" value="50">
        <button onclick="addHero()">保存</button> <button onclick="hideAddHeroForm()">取消</button>
    </div>
</div>

<!-- 副本管理 -->
<div id="tab-challenges" class="tab-content">
    <h3>副本列表（每个副本固定7节点）</h3>
    <button onclick="showAddChallengeForm()">➕ 添加副本</button>
    <div id="challengeList">
    """
    for idx, chal in enumerate(challenges.get("challenges", [])):
        html += f"""
        <div style="margin-bottom:10px; border:1px solid #555; padding:10px; border-radius:8px;">
            <b>{chal['name']}</b>
            <button onclick="editChallenge({idx})" style="margin-left:10px;">✏️ 编辑</button>
            <button onclick="deleteChallenge({idx})">🗑️ 删除</button>
        </div>
        """
    html += """
    </div>
    <div id="addChallengeForm" style="display:none; margin-top:20px; background:#2c3e2f; padding:15px; border-radius:12px;">
        <h4>新增副本</h4>
        <input id="challenge_name" placeholder="副本名称">
        <div id="nodes"></div>
        <button onclick="addChallenge()">保存</button> <button onclick="hideAddChallengeForm()">取消</button>
    </div>
</div>

<!-- 技能模板管理 -->
<div id="tab-skills" class="tab-content">
    <h3>技能模板库</h3>
    <button onclick="showAddSkillForm()">➕ 添加技能模板</button>
    <div id="skillsList">
    """
    for s in skills:
        html += f"""
        <div class="skill-row">
            <b>{s['name']}</b> (ID: {s['id']})<br>
            类型: {s.get('type','')} &nbsp; 目标: {s.get('target_type','')}<br>
            伤害公式: {s.get('damage_formula','')} &nbsp; 效果: {json.dumps(s.get('effects',[]), ensure_ascii=False)}<br>
            <button onclick="deleteSkill('{s['id']}')">删除</button>
        </div>
        """
    html += """
    </div>
    <div id="addSkillForm" style="display:none; margin-top:20px; background:#2c3e2f; padding:15px; border-radius:12px;">
        <h4>添加技能模板</h4>
        <textarea id="skill_json" rows="10" cols="80" placeholder='{"id": "new_skill", "name": "新技能", "type":"magic", "target_type":"single_enemy", "damage_formula":"intelligence * 1.5", "effects":[]}'></textarea><br>
        <button onclick="addSkill()">保存</button> <button onclick="hideAddSkillForm()">取消</button>
    </div>
</div>

<!-- 聊天记录标签页 -->
<div id="tab-chatlog" class="tab-content">
    <h3>GM 聊天记录（玩家 @GM01 或 GM01 发送的消息）</h3>
    <button onclick="viewFullChatLog()">📜 查看完整聊天记录</button>
    <div id="chatLogPreview" style="margin-top:20px; background:#1e2a2e; padding:10px; border-radius:8px; max-height:500px; overflow:auto;">
        <p>点击按钮查看完整记录</p>
    </div>
</div>

<!-- 编辑副本模态框 -->
<div id="editChallengeModal" class="modal">
    <div class="modal-content">
        <h3 id="editChallengeTitle">编辑副本</h3>
        <input id="editChallengeName" placeholder="副本名称" style="width:100%; margin-bottom:10px;">
        <div id="editNodesContainer"></div>
        <button onclick="saveEditedChallenge()">保存</button>
        <button onclick="closeEditChallengeModal()">取消</button>
    </div>
</div>

<script>
    const allChallenges = """ + challenges_json + """;

    function showTab(tab) {
        document.querySelectorAll('.tab-content').forEach(div => div.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`tab-${tab}`).classList.add('active');
        event.target.classList.add('active');
    }
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => showTab(btn.dataset.tab);
    });

    async function updatePlayer(username) {
        let gold = document.getElementById(`gold_${username}`).value;
        let ingots = document.getElementById(`ingots_${username}`).value;
        let resp = await fetch('/admin/update_player', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, gold, ingots})
        });
        let data = await resp.json();
        alert(data.msg);
    }

    async function clearOccupation(username) {
        if(!confirm(`确定清除 ${username} 的占领状态吗？`)) return;
        let resp = await fetch('/admin/clear_occupation', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username})
        });
        let data = await resp.json();
        if(data.success) {
            alert(`已清除 ${username} 的占领状态`);
            location.reload();
        } else {
            alert(data.msg);
        }
    }

    async function updateHeroWeight(heroId) {
        let weight = document.getElementById(`weight_${heroId}`).value;
        let resp = await fetch('/admin/update_hero_weight', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({hero_id: heroId, weight: weight})
        });
        let data = await resp.json();
        if(data.success) {
            alert("权重已更新");
        } else {
            alert(data.msg);
        }
    }

    async function deleteHero(heroId) {
        if(!confirm('确定删除？')) return;
        let resp = await fetch('/admin/delete_hero', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({hero_id: heroId})
        });
        let data = await resp.json();
        if(data.success) location.reload();
        else alert(data.msg);
    }

    async function toggleHero(heroId) {
        let resp = await fetch('/admin/toggle_hero', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({hero_id: heroId})
        });
        let data = await resp.json();
        if(data.success) location.reload();
        else alert(data.msg);
    }

    function showAddHeroForm() { document.getElementById('addHeroForm').style.display = 'block'; }
    function hideAddHeroForm() { document.getElementById('addHeroForm').style.display = 'none'; }
    async function addHero() {
        let skill_base_id = document.getElementById('hero_skill_id').value;
        let skill_display = document.getElementById('skill_display_name').value;
        let skill_config = null;
        if(skill_base_id) {
            skill_config = {base_id: skill_base_id};
            if(skill_display) skill_config.display_name = skill_display;
            let target_count = document.getElementById('skill_target_count').value;
            if(target_count) skill_config.target_count = parseInt(target_count);
            let duration = document.getElementById('skill_duration').value;
            if(duration) skill_config.duration = parseInt(duration);
            let coeff = document.getElementById('skill_coeff').value;
            if(coeff) skill_config.damage_coefficient = parseFloat(coeff);
        }
        let hero = {
            id: document.getElementById('hero_id').value.trim(),
            name: document.getElementById('hero_name').value.trim(),
            star5_hp: parseInt(document.getElementById('hero_hp').value),
            star5_strength: parseInt(document.getElementById('hero_str').value),
            star5_intelligence: parseInt(document.getElementById('hero_int').value),
            star5_speed: parseInt(document.getElementById('hero_spd').value),
            weight: parseInt(document.getElementById('hero_weight').value) || 50,
            skill: skill_config,
            enabled: true
        };
        if(!hero.id || !hero.name) { alert('ID和名称不能为空'); return; }
        let resp = await fetch('/admin/add_hero', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(hero)
        });
        let data = await resp.json();
        if(data.success) location.reload();
        else alert(data.msg);
    }

    // 副本管理：新增
    function showAddChallengeForm() {
        document.getElementById('addChallengeForm').style.display = 'block';
        let nodesDiv = document.getElementById('nodes');
        nodesDiv.innerHTML = '';
        for(let i=1;i<=7;i++) {
            nodesDiv.innerHTML += `
                <div style="border:1px solid #555; margin:10px 0; padding:10px;">
                    <b>节点${i}</b><br>
                    主将ID(多个逗号分隔): <input id="node_main_${i}" placeholder="duobao"><br>
                    战力: <input id="node_power_${i}" placeholder="3000" size="5"><br>
                    经验: <input id="node_exp_${i}" placeholder="100" size="5"><br>
                    金币: <input id="node_gold_${i}" placeholder="500" size="5"><br>
                    宝石掉落概率(0-1): <input id="node_drop_rate_${i}" placeholder="0.3" size="5">
                </div>
            `;
        }
    }
    function hideAddChallengeForm() { document.getElementById('addChallengeForm').style.display = 'none'; }
    async function addChallenge() {
        let name = document.getElementById('challenge_name').value.trim();
        if(!name) { alert('请输入副本名称'); return; }
        let nodes = [];
        for(let i=1;i<=7;i++) {
            let mainIds = document.getElementById(`node_main_${i}`).value;
            let ids = mainIds.split(',').map(s=>s.trim()).filter(s=>s);
            let power = parseInt(document.getElementById(`node_power_${i}`).value) || 0;
            let exp = parseInt(document.getElementById(`node_exp_${i}`).value) || 0;
            let gold = parseInt(document.getElementById(`node_gold_${i}`).value) || 0;
            let drop_rate = parseFloat(document.getElementById(`node_drop_rate_${i}`).value) || 0;
            nodes.push({node_id: i, main_hero_ids: ids, power: power, exp: exp, gold: gold, drop_rate: drop_rate});
        }
        let resp = await fetch('/admin/add_challenge', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, nodes})
        });
        let data = await resp.json();
        if(data.success) location.reload();
        else alert(data.msg);
    }
    async function deleteChallenge(index) {
        if(!confirm('确定删除该副本？')) return;
        let resp = await fetch('/admin/delete_challenge', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({index})
        });
        let data = await resp.json();
        if(data.success) location.reload();
        else alert(data.msg);
    }

    // 副本编辑
    let editingChallengeIndex = -1;
    function editChallenge(index) {
        editingChallengeIndex = index;
        let chal = allChallenges[index];
        document.getElementById('editChallengeName').value = chal.name;
        let nodesContainer = document.getElementById('editNodesContainer');
        nodesContainer.innerHTML = '';
        for (let i=1; i<=7; i++) {
            let node = chal.nodes[i-1] || {main_hero_ids: [], power: 0, exp: 0, gold: 0, drop_rate: 0.3};
            nodesContainer.innerHTML += `
                <div style="border:1px solid #555; margin:10px 0; padding:10px;">
                    <b>节点${i}</b><br>
                    主将ID(多个逗号分隔): <input id="edit_node_main_${i}" value="${(node.main_hero_ids || []).join(',')}" style="width:100%;"><br>
                    战力: <input id="edit_node_power_${i}" value="${node.power}" size="5"><br>
                    经验: <input id="edit_node_exp_${i}" value="${node.exp}" size="5"><br>
                    金币: <input id="edit_node_gold_${i}" value="${node.gold}" size="5"><br>
                    宝石掉落概率(0-1): <input id="edit_node_drop_rate_${i}" value="${node.drop_rate}" size="5">
                </div>
            `;
        }
        document.getElementById('editChallengeModal').style.display = 'flex';
    }
    function closeEditChallengeModal() {
        document.getElementById('editChallengeModal').style.display = 'none';
    }
    async function saveEditedChallenge() {
        let name = document.getElementById('editChallengeName').value.trim();
        if (!name) { alert("副本名称不能为空"); return; }
        let nodes = [];
        for (let i=1; i<=7; i++) {
            let mainIds = document.getElementById(`edit_node_main_${i}`).value;
            let ids = mainIds.split(',').map(s=>s.trim()).filter(s=>s);
            let power = parseInt(document.getElementById(`edit_node_power_${i}`).value) || 0;
            let exp = parseInt(document.getElementById(`edit_node_exp_${i}`).value) || 0;
            let gold = parseInt(document.getElementById(`edit_node_gold_${i}`).value) || 0;
            let drop_rate = parseFloat(document.getElementById(`edit_node_drop_rate_${i}`).value) || 0;
            nodes.push({node_id: i, main_hero_ids: ids, power: power, exp: exp, gold: gold, drop_rate: drop_rate});
        }
        let resp = await fetch('/admin/update_challenge', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({index: editingChallengeIndex, name: name, nodes: nodes})
        });
        let data = await resp.json();
        if (data.success) {
            location.reload();
        } else {
            alert(data.msg);
        }
    }

    // 技能模板管理
    function showAddSkillForm() { document.getElementById('addSkillForm').style.display = 'block'; }
    function hideAddSkillForm() { document.getElementById('addSkillForm').style.display = 'none'; }
    async function addSkill() {
        let skillJson = document.getElementById('skill_json').value;
        try {
            let skill = JSON.parse(skillJson);
            let resp = await fetch('/admin/add_skill', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(skill)
            });
            let data = await resp.json();
            if(data.success) location.reload();
            else alert(data.msg);
        } catch(e) { alert('JSON格式错误'); }
    }
    async function deleteSkill(skillId) {
        if(!confirm('确定删除该技能模板？')) return;
        let resp = await fetch('/admin/delete_skill', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({skill_id: skillId})
        });
        let data = await resp.json();
        if(data.success) location.reload();
        else alert(data.msg);
    }

    // 聊天记录查看
    function viewChatLog(username) {
        window.open('/admin/gm_chat_log?username=GM01&password=gm123456', '_blank');
    }
    function viewFullChatLog() {
        window.open('/admin/gm_chat_log?username=GM01&password=gm123456', '_blank');
    }
</script>
</body>
</html>
    """
    return HTMLResponse(html)

# ---------- API 实现 ----------
@router.post("/update_player")
async def update_player(req: Request):
    data = await req.json()
    username = data.get("username")
    gold = data.get("gold")
    ingots = data.get("ingots")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET gold=?, ingots=? WHERE username=?", (gold, ingots, username))
    conn.commit()
    conn.close()
    return {"success": True, "msg": "更新成功"}

@router.post("/clear_occupation")
async def clear_occupation(req: Request):
    data = await req.json()
    username = data.get("username")
    if not username:
        return {"success": False, "msg": "参数不足"}
    # 使用 core 中的 release_user，确保设置为 NULL 而不是空字符串
    release_user(username)
    return {"success": True, "msg": f"已清除 {username} 的占领状态"}

@router.post("/add_hero")
async def add_hero(req: Request):
    hero = await req.json()
    heroes_data = load_custom_heroes()
    if any(h["id"] == hero["id"] for h in heroes_data["heroes"]):
        return {"success": False, "msg": "武将ID已存在"}
    heroes_data["heroes"].append(hero)
    save_custom_heroes(heroes_data)
    return {"success": True, "msg": "添加成功"}

@router.post("/delete_hero")
async def delete_hero(req: Request):
    data = await req.json()
    hero_id = data["hero_id"]
    heroes_data = load_custom_heroes()
    heroes_data["heroes"] = [h for h in heroes_data["heroes"] if h["id"] != hero_id]
    save_custom_heroes(heroes_data)
    return {"success": True, "msg": "删除成功"}

@router.post("/toggle_hero")
async def toggle_hero(req: Request):
    data = await req.json()
    hero_id = data.get("hero_id")
    heroes_data = load_custom_heroes()
    for h in heroes_data["heroes"]:
        if h["id"] == hero_id:
            h["enabled"] = not h.get("enabled", True)
            save_custom_heroes(heroes_data)
            return {"success": True, "msg": "切换成功"}
    return {"success": False, "msg": "武将不存在"}

@router.post("/update_hero_weight")
async def update_hero_weight(req: Request):
    data = await req.json()
    hero_id = data.get("hero_id")
    weight = data.get("weight")
    try:
        weight = int(weight)
    except:
        return {"success": False, "msg": "权重必须是整数"}
    heroes_data = load_custom_heroes()
    for h in heroes_data["heroes"]:
        if h["id"] == hero_id:
            h["weight"] = weight
            save_custom_heroes(heroes_data)
            return {"success": True, "msg": "权重已更新"}
    return {"success": False, "msg": "武将不存在"}

@router.post("/add_challenge")
async def add_challenge(req: Request):
    data = await req.json()
    name = data.get("name")
    nodes = data.get("nodes")
    if not name or not nodes or len(nodes) != 7:
        return {"success": False, "msg": "副本名称和7个节点必填"}
    challenges = load_challenges()
    for chal in challenges["challenges"]:
        if chal["name"] == name:
            return {"success": False, "msg": "副本名称已存在"}
    challenges["challenges"].append({"name": name, "nodes": nodes})
    save_challenges(challenges)
    return {"success": True, "msg": "添加成功"}

@router.post("/delete_challenge")
async def delete_challenge(req: Request):
    data = await req.json()
    index = data.get("index")
    challenges = load_challenges()
    if 0 <= index < len(challenges["challenges"]):
        challenges["challenges"].pop(index)
        save_challenges(challenges)
        return {"success": True, "msg": "删除成功"}
    return {"success": False, "msg": "索引无效"}

@router.post("/update_challenge")
async def update_challenge(req: Request):
    data = await req.json()
    index = data.get("index")
    name = data.get("name")
    nodes = data.get("nodes")
    if index is None or not name or not nodes or len(nodes) != 7:
        return {"success": False, "msg": "参数错误"}
    challenges = load_challenges()
    if index < 0 or index >= len(challenges["challenges"]):
        return {"success": False, "msg": "索引无效"}
    for i, chal in enumerate(challenges["challenges"]):
        if i != index and chal["name"] == name:
            return {"success": False, "msg": "副本名称已存在"}
    challenges["challenges"][index] = {"name": name, "nodes": nodes}
    save_challenges(challenges)
    return {"success": True, "msg": "更新成功"}

@router.post("/add_skill")
async def add_skill(req: Request):
    skill = await req.json()
    if not skill.get("id") or not skill.get("name"):
        return {"success": False, "msg": "技能ID和名称不能为空"}
    skills_data = load_skills()
    if any(s["id"] == skill["id"] for s in skills_data["skills"]):
        return {"success": False, "msg": "技能ID已存在"}
    skills_data["skills"].append(skill)
    save_skills(skills_data)
    return {"success": True, "msg": "添加成功"}

@router.post("/delete_skill")
async def delete_skill(req: Request):
    data = await req.json()
    skill_id = data.get("skill_id")
    skills_data = load_skills()
    skills_data["skills"] = [s for s in skills_data["skills"] if s["id"] != skill_id]
    save_skills(skills_data)
    return {"success": True, "msg": "删除成功"}

# ---------- 聊天记录查看接口 ----------
@router.get("/gm_chat_log")
async def get_gm_chat_log(username: str, password: str):
    if not is_gm(username, password):
        raise HTTPException(status_code=403, detail="无权限")
    log_path = "gm_chat.log"
    if not os.path.exists(log_path):
        return HTMLResponse("<h3>暂无聊天记录</h3><button onclick='window.close()'>关闭</button>")
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>GM聊天记录</title>
    <style>body{{background:#0a0f1a;color:#eee;padding:20px;font-family:monospace;}}</style>
    </head>
    <body>
    <h1>GM 聊天记录</h1>
    <pre>{content}</pre>
    <button onclick="window.close()">关闭</button>
    </body>
    </html>
    """
    return HTMLResponse(html)