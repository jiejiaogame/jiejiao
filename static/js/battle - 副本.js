// static/js/battle.js - 最终修复版（状态图标使用 Emoji 文字，持续10秒）
let leftTeam = [], rightTeam = [];
let originalLeftTeam = [], originalRightTeam = [];
window.isFighting = false;
window.skipRequested = false;
window.currentAnimationPromise = null;
let battleCallback = null;
let battleWinner = null;

// ========== 技能视频映射表 ==========
let skillVideoMap = {};

async function loadSkillAnimations() {
    try {
        const res = await fetch('/skill_animations');
        const data = await res.json();
        skillVideoMap = data;
        console.log('技能动画配置加载完成', Object.keys(skillVideoMap).length, '个技能');
    } catch (e) {
        console.warn('技能动画配置加载失败，使用静态默认值', e);
        skillVideoMap = {
            "万宝朝宗": "wanbaochao.mp4",
            "龙虎如意": "longhu.mp4",
            "混元拂尘": "hunyuanfuchen.mp4",
            "玄甲护体": "xuanjia.mp4",
            "混元金斗": "hunyuanjindou.mp4",
            "金蛟剪": "jinjiaojian.mp4",
            "缚龙索": "fulongsuo.mp4",
            "定海珠": "dinghaizhu.mp4",
            "遁龙桩": "dunlongzhuang.mp4",
            "太极符印": "taijifuyin.mp4",
            "杨枝甘露": "yangzhiganlu.mp4",
            "五火七禽扇": "wuhuoqiqin.mp4",
            "降魔杵": "xiangmochu.mp4",
            "斩仙剑": "zhanxianjian.mp4",
            "九龙神火罩": "jiulongshenhuo.mp4",
            "照妖鉴": "zhaoyaojian.mp4",
            "风雷双翼": "fengleishuangyi.mp4",
            "八九玄功": "bajiuxuangong.mp4",
            "乾坤圈": "qiankunquan.mp4",
            "攒心钉": "zanxinding.mp4",
            "金光阵": "jinguangzhen.mp4",
            "开山斧": "kaishanfu.mp4",
            "飞头术": "feitoushu.mp4",
            "魅惑": "meihuo.mp4",
            "雌雄双鞭": "cixiongshuangbian.mp4",
            "金攥提炉枪": "jinzuan tiluqiang.mp4",
            "铁嘴神鹰": "tiezuishishenying.mp4",
            "混元锤": "hunyuanchui.mp4",
            "六魂幡": "liuhunfan.mp4",
            "牛黄": "niuhuang.mp4",
            "戮魂幡": "luhunfan.mp4",
            "五色石": "wuseshi.mp4",
            "百胜刀": "baishengdao.mp4",
            "仁德": "rende.mp4",
            "打神鞭": "dashenbian.mp4",
            "阴阳镜": "yinyangjing.mp4",
            "五火神焰扇": "wuhuoshenyan.mp4",
            "降魔宝杵": "xiangmobaochu.mp4",
            "玲珑宝塔": "linglongbaota.mp4",
            "吴钩剑": "wugoujian.mp4"
        };
    }
}

// ========== 音效系统 ==========
let audioContext = null;
function playSound(url, volume = 0.5) {
    if (!url) return;
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    fetch(url)
        .then(res => res.arrayBuffer())
        .then(buffer => audioContext.decodeAudioData(buffer))
        .then(decoded => {
            const source = audioContext.createBufferSource();
            source.buffer = decoded;
            const gainNode = audioContext.createGain();
            gainNode.gain.value = volume;
            source.connect(gainNode);
            gainNode.connect(audioContext.destination);
            source.start();
        })
        .catch(e => console.warn("音效加载失败:", url, e));
}

function getHeroId(heroName, heroObj) {
    if (heroObj && heroObj.id) return heroObj.id;
    const map = {
        "多宝道人": "duobao",
        "金灵圣母": "jinling",
        "无当圣母": "wudang",
        "龟灵圣母": "guiling",
        "云霄仙子": "yunxiao",
        "琼霄仙子": "qiongxiao",
        "碧霄仙子": "bixiao",
        "赵公明": "zhaogongming",
        "妲己": "daji",
        "文殊广法天尊": "wenshujun",
        "普贤真人": "puxian",
        "慈航道人": "cihang",
        "清虚道德真君": "qingxu",
        "道行天尊": "daoxing",
        "玉鼎真人": "yuding",
        "太乙真人": "taiyi",
        "云中子": "yunzhongzi",
        "雷震子": "leizhenzi",
        "杨戬": "yangjian",
        "哪吒": "nezha",
        "黄天化": "huangtianhua",
        "金光圣母": "jinguang",
        "巨灵神": "juling",
        "申公豹": "shenggong",
        "闻仲": "wenpeng",
        "黄飞虎": "huangfeihu",
        "崇黑虎": "chongheihu",
        "乌云仙": "wuyunxian",
        "长耳定光仙": "changxian",
        "金大升": "jintai",
        "余化": "yuwenhua",
        "韩智仙": "hanzhixian",
        "苏护": "suihu",
        "姬发": "jifayou",
        "姜子牙": "jiangziya",
        "申元": "shenyuan",
        "杨任": "yangren",
        "韦护": "weihu",
        "李靖": "lidong",
        "金吒": "jinna",
        "木吒": "muzha",
        "凡人修士": "mortal"
    };
    return map[heroName] || heroName.toLowerCase().replace(/[^a-z]/g, '');
}

let currentSkillNameElement = null;
function showSkillName(skillName, duration = 2000) {
    if (currentSkillNameElement) {
        currentSkillNameElement.remove();
        currentSkillNameElement = null;
    }
    let container = document.getElementById('battlePanel');
    if (!container) return;
    let div = document.createElement('div');
    div.className = 'skill-name-display';
    div.innerText = skillName;
    container.appendChild(div);
    currentSkillNameElement = div;
    setTimeout(() => {
        if (div && div.parentNode) {
            div.remove();
            if (currentSkillNameElement === div) currentSkillNameElement = null;
        }
    }, duration);
}

function showDamageNumber(targetElement, damage, isHeal = false) {
    let rect = targetElement.getBoundingClientRect();
    let div = document.createElement('div');
    div.className = 'float-damage';
    div.innerText = isHeal ? `+${damage}` : `-${damage}`;
    div.style.color = isHeal ? '#0f0' : '#f00';
    div.style.fontSize = '32px';
    div.style.fontWeight = 'bold';
    div.style.textShadow = '2px 2px 0 #000';
    div.style.left = (rect.left + rect.width / 2 - 20) + 'px';
    div.style.top = rect.top + 'px';
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 800);
}

// ========== 状态图标（使用 Emoji + 文字，持续10秒） ==========
function showStatusIcon(targetElement, statusType, duration = 10000) {
    if (!targetElement) return;
    let container = targetElement.closest('.hero-card-mini');
    if (!container) container = targetElement;
    // 移除同类型旧图标
    let oldTip = container.querySelector(`.status-tip-${statusType}`);
    if (oldTip) oldTip.remove();
    
    let tip = document.createElement('div');
    tip.className = `status-tip-${statusType}`;
    tip.style.position = 'absolute';
    tip.style.top = '-30px';
    tip.style.left = '50%';
    tip.style.transform = 'translateX(-50%)';
    tip.style.backgroundColor = 'rgba(0,0,0,0.7)';
    tip.style.color = '#ffaa66';
    tip.style.padding = '2px 8px';
    tip.style.borderRadius = '20px';
    tip.style.fontSize = '12px';
    tip.style.fontWeight = 'bold';
    tip.style.whiteSpace = 'nowrap';
    tip.style.zIndex = '1000';
    tip.style.pointerEvents = 'none';
    
    let text = '';
    switch (statusType) {
        case 'stun': text = '😵 眩晕'; break;
        case 'poison': text = '☠️ 中毒'; break;
        case 'shield': text = '🛡️ 护盾'; break;
        case 'strength_up': text = '⚡ 攻击提升'; break;
        default: text = statusType;
    }
    tip.innerText = text;
    container.appendChild(tip);
    setTimeout(() => {
        if (tip && tip.parentNode) tip.remove();
    }, duration);
}

function applySkillEffect(skillType, targetElement, casterElement, skillName = '') {
    switch (skillType) {
        case 'magic':
            let flash = document.createElement('div');
            flash.style.position = 'fixed';
            flash.style.top = '0';
            flash.style.left = '0';
            flash.style.width = '100%';
            flash.style.height = '100%';
            flash.style.backgroundColor = 'rgba(255,100,0,0.3)';
            flash.style.pointerEvents = 'none';
            flash.style.zIndex = '10009';
            document.body.appendChild(flash);
            setTimeout(() => flash.remove(), 200);
            break;
        case 'control':
            {
                let container = targetElement.closest('.hero-card-mini') || targetElement;
                setTimeout(() => showStatusIcon(container, 'stun', 10000), 50);
            }
            break;
        case 'debuff':
            if (skillName && (skillName.includes('毒') || skillName.includes('蛊'))) {
                targetElement.classList.add('poison-smoke');
                setTimeout(() => targetElement.classList.remove('poison-smoke'), 1000);
                let container = targetElement.closest('.hero-card-mini') || targetElement;
                setTimeout(() => showStatusIcon(container, 'poison', 10000), 50);
            }
            break;
        case 'heal':
            targetElement.classList.add('heal-glow');
            setTimeout(() => targetElement.classList.remove('heal-glow'), 400);
            break;
        case 'buff':
            {
                let container = targetElement.closest('.hero-card-mini') || targetElement;
                setTimeout(() => showStatusIcon(container, 'strength_up', 10000), 50);
            }
            break;
        case 'shield':
            {
                let container = targetElement.closest('.hero-card-mini') || targetElement;
                setTimeout(() => showStatusIcon(container, 'shield', 10000), 50);
            }
            break;
        default: break;
    }
}

function getHeroAvatarDiv(team, heroName) {
    let gridId = team === 'left' ? 'leftGrid' : 'rightGrid';
    let container = document.getElementById(gridId);
    if (!container) return null;
    let rows = container.querySelectorAll('.grid-row');
    for (let row of rows) {
        let slots = row.querySelectorAll('.grid-slot');
        for (let slot of slots) {
            let heroDiv = slot.querySelector('.hero-card-mini');
            if (heroDiv && heroDiv.querySelector('.hero-name-mini')?.innerText === heroName) {
                return heroDiv.querySelector('.hero-avatar-mini');
            }
        }
    }
    return null;
}

function highlightHero(heroAvatar, duration = 500) {
    if (!heroAvatar) return;
    heroAvatar.classList.add('glow-effect');
    setTimeout(() => heroAvatar.classList.remove('glow-effect'), duration);
}

// ========== 单体攻击动画（隐藏父容器，飞行终点偏移） ==========
async function animateSingleAttack(attackerId, attackerAvatar, targetAvatar, damage, skillType, isHeal, targetId, skillName) {
    if (window.skipRequested) return;
    if (skillName) showSkillName(skillName, 2000);
    if (!attackerAvatar || !targetAvatar) return;

    // 视频播放
    let videoPlace = null;
    let videoFile = skillVideoMap[skillName];
    if (videoFile) {
        videoPlace = document.getElementById('skillVideoPlaceholder');
        if (!videoPlace) {
            videoPlace = document.createElement('div');
            videoPlace.id = 'skillVideoPlaceholder';
            videoPlace.className = 'skill-video-placeholder';
            document.body.appendChild(videoPlace);
        }
        videoPlace.innerHTML = '';
        let video = document.createElement('video');
        video.src = `/static/videos/${videoFile}`;
        video.autoplay = true;
        video.loop = false;
        video.muted = true;
        video.playsInline = true;
        video.onerror = (e) => { console.error(`视频加载失败: ${videoFile}`, e); if (videoPlace) videoPlace.style.display = 'none'; };
        video.oncanplay = () => { video.play().catch(err => { console.warn(`视频自动播放失败: ${videoFile}`, err); if (videoPlace) videoPlace.style.display = 'none'; }); };
        videoPlace.appendChild(video);
        videoPlace.style.display = 'flex';
        await new Promise(r => setTimeout(r, 400));
    }

    const startRect = attackerAvatar.getBoundingClientRect();
    const targetRect = targetAvatar.getBoundingClientRect();
    
    // 攻击者原始头像透明
    const originalOpacity = attackerAvatar.style.opacity;
    attackerAvatar.style.opacity = '0';

    // 克隆攻击者头像
    const clone = attackerAvatar.cloneNode(true);
    clone.style.position = 'fixed';
    clone.style.left = startRect.left + 'px';
    clone.style.top = startRect.top + 'px';
    clone.style.width = startRect.width + 'px';
    clone.style.height = startRect.height + 'px';
    clone.style.zIndex = '10000';
    clone.style.transition = 'transform 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1)';
    clone.style.backgroundImage = `url('/static/images/heroes/${attackerId}_attack.png')`;
    clone.style.backgroundSize = 'contain';
    clone.style.backgroundRepeat = 'no-repeat';
    clone.style.backgroundPosition = 'center';
    document.body.appendChild(clone);

    // 隐藏原始头像的父容器（避免白块）
    const attackerCard = attackerAvatar.closest('.hero-card-mini');
    const originalCardDisplay = attackerCard ? attackerCard.style.display : null;
    if (attackerCard) {
        attackerCard.style.display = 'none';
    }

    // 计算飞行终点（偏移60px）
    const attackerCenter = { x: startRect.left + startRect.width/2, y: startRect.top + startRect.height/2 };
    const targetCenter = { x: targetRect.left + targetRect.width/2, y: targetRect.top + targetRect.height/2 };
    const dirX = targetCenter.x - attackerCenter.x;
    const dirY = targetCenter.y - attackerCenter.y;
    const length = Math.hypot(dirX, dirY);
    if (length > 0.01) {
        const unitX = dirX / length;
        const unitY = dirY / length;
        const offset = 60;
        let endX = targetCenter.x - unitX * offset;
        let endY = targetCenter.y - unitY * offset;
        let destX = endX - startRect.width/2;
        let destY = endY - startRect.height/2;
        destX = Math.max(0, Math.min(window.innerWidth - startRect.width, destX));
        destY = Math.max(0, Math.min(window.innerHeight - startRect.height, destY));
        const deltaX = destX - startRect.left;
        const deltaY = destY - startRect.top;
        let transformStr = `translate(${deltaX}px, ${deltaY}px) scale(1.1) rotateX(8deg)`;
        clone.style.transform = transformStr;
    }

    await new Promise(r => setTimeout(r, 500));
    if (window.skipRequested) {
        clone.remove();
        attackerAvatar.style.opacity = originalOpacity;
        if (attackerCard) attackerCard.style.display = originalCardDisplay;
        if (videoPlace) videoPlace.style.display = 'none';
        return;
    }

    // 受击特效：替换目标头像的 src 为受击图
    const originalTargetSrc = targetAvatar.src;
    targetAvatar.src = `/static/images/heroes/${targetId}_hit.png`;
    playSound(`/static/sounds/heroes/${attackerId}_attack.wav`, 0.6);
    playSound(`/static/sounds/heroes/${targetId}_hit.wav`, 0.6);
    if (!isHeal) showDamageNumber(targetAvatar, damage);
    if (skillType) applySkillEffect(skillType, targetAvatar, attackerAvatar, skillName);

    await new Promise(r => setTimeout(r, 900));
    if (window.skipRequested) {
        clone.remove();
        attackerAvatar.style.opacity = originalOpacity;
        if (attackerCard) attackerCard.style.display = originalCardDisplay;
        targetAvatar.src = originalTargetSrc;
        if (videoPlace) videoPlace.style.display = 'none';
        return;
    }

    // 清理
    clone.remove();
    attackerAvatar.style.opacity = originalOpacity;
    if (attackerCard) attackerCard.style.display = originalCardDisplay;
    targetAvatar.src = originalTargetSrc;
    if (videoPlace) videoPlace.style.display = 'none';
}

// ========== 群体攻击动画 ==========
async function animateMultiAttack(attackerId, attackerAvatar, targetsInfo, skillType, skillName) {
    if (window.skipRequested) return;
    if (skillName) showSkillName(skillName, 2000);
    if (!attackerAvatar) return;
    const originalSrc = attackerAvatar.src;
    const rect = attackerAvatar.getBoundingClientRect();

    const isEnemy = attackerAvatar.closest('.right-grid') !== null;
    let targetGrid = isEnemy ? document.querySelector('.left-grid') : document.querySelector('.right-grid');
    let centerX, centerY;
    if (targetGrid) {
        const targetRect = targetGrid.getBoundingClientRect();
        centerX = targetRect.left + (targetRect.width / 2) - (rect.width / 2);
        centerY = targetRect.top + (targetRect.height / 2) - (rect.height / 2);
    } else {
        centerX = window.innerWidth / 2 - rect.width / 2;
        centerY = window.innerHeight / 2 - rect.height / 2 - 50;
    }

    let transformStr = `translate(${centerX - rect.left}px, ${centerY - rect.top}px) scale(1.3)`;
    if (isEnemy) transformStr += ` scaleX(-1)`;
    attackerAvatar.style.transition = 'transform 0.5s ease-in-out';
    attackerAvatar.style.transform = transformStr;
    await new Promise(r => setTimeout(r, 500));
    if (window.skipRequested) return;

    attackerAvatar.src = `/static/images/heroes/${attackerId}_attack.png`;

    let videoPlace = null;
    let videoFile = skillVideoMap[skillName];
    if (videoFile) {
        videoPlace = document.getElementById('skillVideoPlaceholder');
        if (!videoPlace) {
            videoPlace = document.createElement('div');
            videoPlace.id = 'skillVideoPlaceholder';
            videoPlace.className = 'skill-video-placeholder';
            document.body.appendChild(videoPlace);
        }
        videoPlace.innerHTML = '';
        let video = document.createElement('video');
        video.src = `/static/videos/${videoFile}`;
        video.autoplay = true;
        video.loop = false;
        video.muted = true;
        video.playsInline = true;
        video.onerror = (e) => {
            console.error(`视频加载失败: ${videoFile}`, e);
            if (videoPlace) videoPlace.style.display = 'none';
        };
        video.oncanplay = () => {
            video.play().catch(err => {
                console.warn(`视频自动播放失败: ${videoFile}`, err);
                if (videoPlace) videoPlace.style.display = 'none';
            });
        };
        videoPlace.appendChild(video);
        videoPlace.style.display = 'flex';
    }

    playSound(`/static/sounds/heroes/${attackerId}_attack.wav`, 0.6);

    for (let i = 0; i < targetsInfo.length; i++) {
        if (window.skipRequested) break;
        const t = targetsInfo[i];
        t.avatar.classList.add('hit-shake');
        showDamageNumber(t.avatar, t.damage);
        applySkillEffect(skillType, t.avatar, attackerAvatar, skillName);
        playSound(`/static/sounds/heroes/${t.id}_hit.wav`, 0.5);
        await new Promise(r => setTimeout(r, 500));
        t.avatar.classList.remove('hit-shake');
    }

    if (videoPlace) videoPlace.style.display = 'none';
    attackerAvatar.src = originalSrc;
    attackerAvatar.style.transform = '';
    await new Promise(r => setTimeout(r, 500));
    attackerAvatar.style.transition = '';
}

function updateEnemyPlayerAvatar(avatarUrl, playerName) {
    let container = document.getElementById('enemyAvatars');
    if (!container) return;
    container.innerHTML = '';
    let div = document.createElement('div');
    div.className = 'enemy-avatar-item';
    div.innerHTML = `<img src="${avatarUrl}" onerror="this.src='/static/images/heroes/hero.png'"><div class="enemy-hp">${playerName}</div>`;
    container.appendChild(div);
}

// ========== 血量与UI（包含实时更新单元格） ==========
function applyFinalHp(log, winner) {
    leftTeam = JSON.parse(JSON.stringify(originalLeftTeam));
    rightTeam = JSON.parse(JSON.stringify(originalRightTeam));
    for (let entry of log) {
        if (entry.type === 'attack' || (entry.type === 'skill' && !entry.is_multi)) {
            let targetTeam = (entry.target_team === 'left') ? leftTeam : rightTeam;
            let hero = targetTeam.find(h => h.name === entry.target);
            if (hero) hero.hp = Math.min(hero.maxHp, Math.max(0, entry.hp_left));
        } else if (entry.type === 'skill' && entry.is_multi && entry.targets) {
            for (let t of entry.targets) {
                let targetTeam = (t.team === 'left') ? leftTeam : rightTeam;
                let hero = targetTeam.find(h => h.name === t.name);
                if (hero) hero.hp = Math.min(hero.maxHp, Math.max(0, t.hp_left));
            }
        }
    }
    renderGrids();
    updateTotalHpBars();
    if (typeof addLog === 'function') addLog(`🏆 战斗结束，胜者: ${winner === 'left' ? '我方' : '敌方'}`);
}

// 实时更新单个武将的血条（不重建网格）
function updateHeroHpBar(team, heroName, currentHp, maxHp) {
    let gridId = team === 'left' ? 'leftGrid' : 'rightGrid';
    let container = document.getElementById(gridId);
    if (!container) return;
    let heroDiv = null;
    let rows = container.querySelectorAll('.grid-row');
    for (let row of rows) {
        let slots = row.querySelectorAll('.grid-slot');
        for (let slot of slots) {
            let card = slot.querySelector('.hero-card-mini');
            if (card && card.querySelector('.hero-name-mini')?.innerText === heroName) {
                heroDiv = card;
                break;
            }
        }
        if (heroDiv) break;
    }
    if (heroDiv) {
        let hpSpan = heroDiv.querySelector('.hero-hp-mini');
        let fillBar = heroDiv.querySelector('.hero-hp-fill');
        if (hpSpan) hpSpan.innerText = `❤️ ${currentHp}/${maxHp}`;
        if (fillBar) {
            let percent = (currentHp / maxHp) * 100;
            fillBar.style.width = percent + '%';
        }
        if (currentHp <= 0) {
            heroDiv.classList.add('dead');
            if (!heroDiv.querySelector('.dead-text')) {
                let deadText = document.createElement('div');
                deadText.className = 'dead-text';
                deadText.innerText = '💀';
                heroDiv.appendChild(deadText);
            }
        } else {
            heroDiv.classList.remove('dead');
            let deadText = heroDiv.querySelector('.dead-text');
            if (deadText) deadText.remove();
        }
    }
}

async function playBattleLogWithDelay(log, winner) {
    if (window.currentAnimationPromise) {
        window.skipRequested = true;
        await window.currentAnimationPromise;
    }
    if (!log || log.length === 0) {
        if (typeof addLog === 'function') addLog(`⚡ 战斗结束，胜者: ${winner === 'left' ? '我方' : '敌方'}`);
        setTimeout(() => {
            if (battleCallback) battleCallback(winner);
            hideBattlePanel();
        }, 2000);
        return;
    }
    leftTeam = JSON.parse(JSON.stringify(originalLeftTeam));
    rightTeam = JSON.parse(JSON.stringify(originalRightTeam));
    // 仅初始渲染一次
    renderGrids();
    updateTotalHpBars();
    window.skipRequested = false;
    window.isFighting = true;

    window.currentAnimationPromise = (async () => {
        for (let i = 0; i < log.length; i++) {
            if (window.skipRequested || !window.isFighting) {
                if (typeof addLog === 'function') addLog("⏩ 战斗已中断，直接结算...");
                let videoPlace = document.getElementById('skillVideoPlaceholder');
                if (videoPlace) videoPlace.style.display = 'none';
                if (typeof window.playBgMusic === 'function') window.playBgMusic();
                applyFinalHp(log, winner);
                if (battleCallback) battleCallback(winner);
                hideBattlePanel();
                window.isFighting = false;
                window.currentAnimationPromise = null;
                window.skipRequested = false;
                return;
            }
            let entry = log[i];
            if (entry.type === 'attack' || entry.type === 'skill') {
                if (entry.type === 'attack') {
                    let attackerName = entry.attacker;
                    let targetName = entry.target;
                    let damage = entry.damage || 0;

                    if (typeof addLog === 'function') addLog(`${attackerName} 攻击 ${targetName} 造成 ${damage} 伤害${entry.dead ? '，目标死亡！' : ''}`);

                    let attackerAvatar = getHeroAvatarDiv(entry.attacker_team, attackerName);
                    let targetAvatar = getHeroAvatarDiv(entry.target_team, targetName);
                    highlightHero(attackerAvatar, 500);

                    let attackerId = getHeroId(attackerName, {});
                    if (attackerAvatar && targetAvatar) {
                        let targetId = getHeroId(targetName, {});
                        await animateSingleAttack(attackerId, attackerAvatar, targetAvatar, damage, 'physical', false, targetId, '');
                    } else {
                        await new Promise(r => setTimeout(r, 1400));
                    }

                    // 更新血量数据
                    let targetTeam = (entry.target_team === 'left') ? leftTeam : rightTeam;
                    let hero = targetTeam.find(h => h.name === targetName);
                    if (hero) {
                        hero.hp = Math.min(hero.maxHp, Math.max(0, entry.hp_left));
                        updateHeroHpBar(entry.target_team, targetName, hero.hp, hero.maxHp);
                    }
                } else if (entry.type === 'skill') {
                    let attackerName = entry.attacker;
                    let skillName = entry.skill;
                    let skillType = entry.skill_type;

                    if (entry.is_multi && entry.targets) {
                        let attackerAvatar = getHeroAvatarDiv(entry.attacker_team, attackerName);
                        let attackerId = getHeroId(attackerName, {});

                        // 更新血量
                        for (let t of entry.targets) {
                            let targetTeam = (t.team === 'left') ? leftTeam : rightTeam;
                            let hero = targetTeam.find(h => h.name === t.name);
                            if (hero) {
                                hero.hp = Math.min(hero.maxHp, Math.max(0, t.hp_left));
                                updateHeroHpBar(t.team, t.name, hero.hp, hero.maxHp);
                            }
                        }

                        const isNonDamage = (skillType === 'buff' || skillType === 'heal' || skillType === 'shield');
                        if (isNonDamage) {
                            showSkillName(skillName, 2000);
                            for (let t of entry.targets) {
                                let avatar = getHeroAvatarDiv(t.team, t.name);
                                if (avatar) {
                                    let container = avatar.closest('.hero-card-mini') || avatar;
                                    setTimeout(() => {
                                        if (skillType === 'buff') showStatusIcon(container, 'strength_up', 10000);
                                        else if (skillType === 'shield') showStatusIcon(container, 'shield', 10000);
                                    }, 100);
                                }
                            }
                            await new Promise(r => setTimeout(r, 1500));
                        } else {
                            let targetsWithAvatar = [];
                            for (let t of entry.targets) {
                                let avatar = getHeroAvatarDiv(t.team, t.name);
                                if (avatar) {
                                    targetsWithAvatar.push({
                                        name: t.name,
                                        id: getHeroId(t.name, {}),
                                        avatar: avatar,
                                        hp_left: t.hp_left,
                                        damage: t.damage,
                                        dead: t.dead
                                    });
                                }
                            }
                            if (attackerAvatar && targetsWithAvatar.length) {
                                await animateMultiAttack(attackerId, attackerAvatar, targetsWithAvatar, skillType, skillName);
                            } else {
                                await new Promise(r => setTimeout(r, 1800));
                            }
                        }
                    } else {
                        let targetName = entry.target;
                        let damage = entry.damage || 0;
                        let isHeal = (skillType === 'heal');
                        let isBuff = (skillType === 'buff');
                        let isShield = (skillType === 'shield');

                        if (typeof addLog === 'function') {
                            if (isBuff) addLog(`${attackerName} 使用 ${skillName} 为 ${targetName} 施加增益`);
                            else if (isHeal) addLog(`${attackerName} 使用 ${skillName} 治疗 ${targetName} ${damage} 生命`);
                            else if (isShield) addLog(`${attackerName} 使用 ${skillName} 为 ${targetName} 附加护盾`);
                            else addLog(`${attackerName} 使用 ${skillName} 对 ${targetName} 造成 ${damage} 伤害${entry.dead ? '，目标死亡！' : ''}`);
                        }

                        let attackerAvatar = getHeroAvatarDiv(entry.attacker_team, attackerName);
                        let targetAvatar = getHeroAvatarDiv(entry.target_team, targetName);
                        highlightHero(attackerAvatar, 500);

                        if (isBuff || isHeal || isShield) {
                            showSkillName(skillName, 2000);
                            if (targetAvatar) {
                                let container = targetAvatar.closest('.hero-card-mini') || targetAvatar;
                                setTimeout(() => {
                                    if (isBuff) showStatusIcon(container, 'strength_up', 10000);
                                    else if (isShield) showStatusIcon(container, 'shield', 10000);
                                }, 100);
                            }
                            await new Promise(r => setTimeout(r, 1000));
                            // 治疗/护盾后更新血量
                            let targetTeam = (entry.target_team === 'left') ? leftTeam : rightTeam;
                            let hero = targetTeam.find(h => h.name === targetName);
                            if (hero && (isHeal || isShield)) {
                                hero.hp = Math.min(hero.maxHp, Math.max(0, entry.hp_left));
                                updateHeroHpBar(entry.target_team, targetName, hero.hp, hero.maxHp);
                            }
                        } else {
                            let attackerId = getHeroId(attackerName, {});
                            if (attackerAvatar && targetAvatar) {
                                let targetId = getHeroId(targetName, {});
                                await animateSingleAttack(attackerId, attackerAvatar, targetAvatar, damage, skillType, isHeal, targetId, skillName);
                            } else {
                                await new Promise(r => setTimeout(r, 1400));
                            }
                            // 更新血量
                            let targetTeam = (entry.target_team === 'left') ? leftTeam : rightTeam;
                            let hero = targetTeam.find(h => h.name === targetName);
                            if (hero && !isBuff && !isShield && !isHeal) {
                                hero.hp = Math.min(hero.maxHp, Math.max(0, entry.hp_left));
                                updateHeroHpBar(entry.target_team, targetName, hero.hp, hero.maxHp);
                            }
                        }
                    }
                }
            } else if (entry.type === 'status') {
                if (typeof addLog === 'function') addLog(entry.text);
            }
            if ((window.skipRequested || !window.isFighting) && i < log.length - 1) break;
            if (i < log.length - 1 && !window.skipRequested) await new Promise(r => setTimeout(r, 500));
        }
        if (!window.skipRequested && window.isFighting) {
            if (typeof addLog === 'function') addLog(`🏆 战斗结束，胜者: ${winner === 'left' ? '我方' : '敌方'}`);
            if (battleCallback) battleCallback(winner);
            if (winner === 'left') {
                if (typeof window.playWinSound === 'function') window.playWinSound();
            } else {
                if (typeof window.playLoseSound === 'function') window.playLoseSound();
            }
            applyFinalHp(log, winner);
            hideBattlePanel();
        } else {
            hideBattlePanel();
        }
        window.isFighting = false;
        window.currentAnimationPromise = null;
        window.skipRequested = false;
    })();
    await window.currentAnimationPromise;
}

function showBattlePanel(leftTeamData, rightTeamData, logs, winner, leftPower, rightPower, callback, enemyPlayerName = null, enemyAvatar = null) {
    if (!leftTeamData || !rightTeamData) {
        if (callback) callback(winner);
        return;
    }
    for (let h of leftTeamData) if (h.maxHp > 0) h.hp = h.maxHp;
    for (let h of rightTeamData) if (h.maxHp > 0) h.hp = h.maxHp;

    if (enemyPlayerName) {
        let avatarUrl = enemyAvatar || `/static/images/heroes/${enemyPlayerName}.png`;
        updateEnemyPlayerAvatar(avatarUrl, enemyPlayerName);
    } else {
        updateEnemyPlayerAvatar('/static/images/heroes/hero.png', '敌方');
    }

    let friendPanel = document.getElementById('friendPanel');
    if (friendPanel) friendPanel.style.display = 'none';

    let validLogs = logs && logs.length ? logs : [{ type: "status", text: "战斗瞬间结束" }];
    leftTeam = JSON.parse(JSON.stringify(leftTeamData));
    rightTeam = JSON.parse(JSON.stringify(rightTeamData));
    originalLeftTeam = JSON.parse(JSON.stringify(leftTeamData));
    originalRightTeam = JSON.parse(JSON.stringify(rightTeamData));
    battleCallback = callback;
    battleWinner = winner;
    renderGrids();
    updateTotalHpBars();
    if (document.getElementById('leftPower')) document.getElementById('leftPower').innerText = leftPower || 0;
    if (document.getElementById('rightPower')) document.getElementById('rightPower').innerText = rightPower || 0;
    if (document.getElementById('mainContent')) document.getElementById('mainContent').style.display = 'none';
    if (document.getElementById('battlePanel')) document.getElementById('battlePanel').style.display = 'flex';
    
    window.isFighting = true;
    window.skipRequested = false;
    if (window.currentAnimationPromise) window.currentAnimationPromise = null;
    
    if (typeof window.playBattleMusic === 'function') window.playBattleMusic();
    
    playBattleLogWithDelay(validLogs, winner);
}

function hideBattlePanel() {
    if (document.getElementById('battlePanel')) document.getElementById('battlePanel').style.display = 'none';
    if (document.getElementById('mainContent')) document.getElementById('mainContent').style.display = 'block';
    window.isFighting = false;
    window.currentAnimationPromise = null;
    window.skipRequested = false;
}

// ========== 网格渲染（禁止战斗时刷新） ==========
function renderGrids() {
    renderOneGrid('leftGrid', leftTeam);
    renderOneGrid('rightGrid', rightTeam);
}

function renderOneGrid(gridId, team) {
    // 战斗动画期间禁止重建网格，避免元素引用失效
    if (window.isFighting) {
        console.warn('[渲染拦截] 战斗进行中，禁止刷新网格');
        return;
    }
    let container = document.getElementById(gridId);
    if (!container) return;
    
    container.innerHTML = '';
    container.className = 'grid-3x3 ' + (gridId === 'leftGrid' ? 'left-grid' : 'right-grid');
    
    for (let rowIdx = 0; rowIdx < 3; rowIdx++) {
        let rowDiv = document.createElement('div');
        rowDiv.className = `grid-row grid-row-${rowIdx + 1}`;
        for (let colIdx = 0; colIdx < 3; colIdx++) {
            let slot = document.createElement('div');
            slot.className = 'grid-slot';
            rowDiv.appendChild(slot);
        }
        container.appendChild(rowDiv);
    }
    
    let slots = container.querySelectorAll('.grid-slot');
    for (let hero of team) {
        let pos = hero.position;
        if (pos >= 0 && pos < 9) {
            let slot = slots[pos];
            if (slot) {
                let percent = (hero.hp / hero.maxHp) * 100;
                let isDead = hero.hp <= 0;
                let avatarUrl = `/static/images/heroes/${hero.id || hero.name}.png`;
                slot.innerHTML = `
                    <div class="hero-card-mini ${isDead ? 'dead' : ''}">
                        <img class="hero-avatar-mini" src="${avatarUrl}" onerror="this.src='/static/images/heroes/hero.png'">
                        <div class="hero-name-mini">${hero.name}</div>
                        <div class="hero-hp-mini">❤️ ${hero.hp}/${hero.maxHp}</div>
                        <div class="hero-hp-bar"><div class="hero-hp-fill" style="width:${percent}%"></div></div>
                        ${isDead ? '<div class="dead-text">💀</div>' : ''}
                    </div>
                `;
            }
        }
    }
}

function updateTotalHpBars() {
    let leftTotal = leftTeam.reduce((s, h) => s + h.hp, 0);
    let leftMax = leftTeam.reduce((s, h) => s + h.maxHp, 0);
    let rightTotal = rightTeam.reduce((s, h) => s + h.hp, 0);
    let rightMax = rightTeam.reduce((s, h) => s + h.maxHp, 0);
    let leftPercent = leftMax > 0 ? (leftTotal / leftMax) * 100 : 0;
    let rightPercent = rightMax > 0 ? (rightTotal / rightMax) * 100 : 0;
    if (document.getElementById('leftTotalFill')) document.getElementById('leftTotalFill').style.width = leftPercent + '%';
    if (document.getElementById('rightTotalFill')) document.getElementById('rightTotalFill').style.width = rightPercent + '%';
}

function initBattleControls() {
    const skipBtn = document.getElementById('skipFightBtn');
    const escapeBtn = document.getElementById('escapeBtn');
    if (skipBtn) {
        skipBtn.onclick = () => {
            if (window.isFighting) {
                window.skipRequested = true;
                if (typeof addLog === 'function') addLog("⏩ 跳过战斗，直接结算...");
                if (!window.currentAnimationPromise) {
                    if (battleCallback) battleCallback(battleWinner);
                    if (typeof hideBattlePanel === 'function') hideBattlePanel();
                    window.isFighting = false;
                }
            } else {
                if (typeof addLog === 'function') addLog("当前没有进行中的战斗，无法跳过");
            }
        };
    }
    if (escapeBtn) {
        escapeBtn.onclick = () => {
            if (!window.isFighting) {
                if (typeof addLog === 'function') addLog("没有进行中的战斗");
                return;
            }
            if (typeof addLog === 'function') addLog("🏃 你逃跑了，战斗结束");
            window.skipRequested = true;
            window.isFighting = false;
            if (typeof hideBattlePanel === 'function') hideBattlePanel();
            if (typeof window.playBgMusic === 'function') window.playBgMusic();
            if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ act: "escape" }));
            }
        };
    }
}

window.showBattlePanel = showBattlePanel;
window.hideBattlePanel = hideBattlePanel;
window.applyFinalHp = applyFinalHp;
window.updateHeroHpBar = updateHeroHpBar;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        loadSkillAnimations().then(() => initBattleControls());
    });
} else {
    loadSkillAnimations().then(() => initBattleControls());
}