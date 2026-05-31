// static/js/battle.js - 最终稳定版（平均等级显示，移除个体等级，修复金吒ID）
let leftTeam = [], rightTeam = [];
let originalLeftTeam = [], originalRightTeam = [];
window.isFighting = false;
window.skipRequested = false;
window.currentAnimationPromise = null;
let battleCallback = null;
let battleWinner = null;

// ========== 音效预加载缓存 ==========
let audioContext = null;
const soundCache = new Map();
let preloadProgress = { loaded: 0, total: 0 };
let preloadComplete = false;
let preloadPromise = null;

function getAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContext;
}

async function preloadSounds(urls, onProgress) {
    const toLoad = urls.filter(url => !soundCache.has(url));
    preloadProgress.total = toLoad.length;
    preloadProgress.loaded = 0;
    const fetchPromises = toLoad.map(async (url) => {
        try {
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            soundCache.set(url, { arrayBuffer, decoded: false, buffer: null });
            preloadProgress.loaded++;
            if (onProgress) onProgress(preloadProgress.loaded, preloadProgress.total);
        } catch (e) { console.warn(`预加载音效失败: ${url}`, e); }
    });
    await Promise.all(fetchPromises);
}

async function decodeAllSounds() {
    const ctx = getAudioContext();
    if (ctx.state === 'suspended') { await ctx.resume(); }
    console.log('AudioContext 已激活，音效将按需解码');
}

function playSound(url, volume = 0.5) {
    if (!url) return;
    const ctx = getAudioContext();
    const cached = soundCache.get(url);
    if (cached && cached.decoded && cached.buffer) {
        const source = ctx.createBufferSource();
        source.buffer = cached.buffer;
        const gainNode = ctx.createGain();
        gainNode.gain.value = volume;
        source.connect(gainNode);
        gainNode.connect(ctx.destination);
        source.start();
        return;
    }
    if (!cached || !cached.arrayBuffer) {
        fetch(url)
            .then(res => res.arrayBuffer())
            .then(buffer => ctx.decodeAudioData(buffer))
            .then(decoded => {
                soundCache.set(url, { decoded: true, buffer: decoded });
                const source = ctx.createBufferSource();
                source.buffer = decoded;
                const gainNode = ctx.createGain();
                gainNode.gain.value = volume;
                source.connect(gainNode);
                gainNode.connect(ctx.destination);
                source.start();
            })
            .catch(e => console.warn("音效加载失败:", url, e));
        return;
    }
    ctx.decodeAudioData(cached.arrayBuffer.slice(0))
        .then(decoded => {
            cached.buffer = decoded;
            cached.decoded = true;
            delete cached.arrayBuffer;
            const source = ctx.createBufferSource();
            source.buffer = decoded;
            const gainNode = ctx.createGain();
            gainNode.gain.value = volume;
            source.connect(gainNode);
            gainNode.connect(ctx.destination);
            source.start();
        })
        .catch(e => console.warn(`解码音效失败: ${url}`, e));
}

async function getAllSoundUrls() {
    const heroIds = new Set();
    const allHeroes = await fetch(`/my_heroes?username=${currentUser}`).then(r => r.json()).catch(() => ({ heroes: [] }));
    if (allHeroes.heroes) { allHeroes.heroes.forEach(h => heroIds.add(h.id)); }
    const commonIds = ['duobao', 'jinling', 'yunxiao', 'zhaogongming', 'daji', 'jiangziya'];
    commonIds.forEach(id => heroIds.add(id));
    const urls = [];
    for (const id of heroIds) {
        urls.push(`/static/sounds/heroes/${id}_attack.wav`);
        urls.push(`/static/sounds/heroes/${id}_hit.wav`);
    }
    const commonSounds = [
        '/static/sounds/attack_physical.wav', '/static/sounds/attack_magic.wav',
        '/static/sounds/heal.wav', '/static/sounds/crit.wav',
        '/static/sounds/victory.wav', '/static/sounds/defeat.wav'
    ];
    urls.push(...commonSounds);
    return [...new Set(urls)];
}

async function startPreload(onProgress) {
    if (preloadPromise) return preloadPromise;
    const urls = await getAllSoundUrls();
    preloadPromise = preloadSounds(urls, onProgress);
    await preloadPromise;
    preloadComplete = true;
    return preloadPromise;
}

async function unlockAndDecodeSounds() {
    const ctx = getAudioContext();
    if (ctx.state === 'suspended') { await ctx.resume(); }
    console.log('音效解码完成，已就绪');
}

async function ensureBattleSoundsReady(attackerId, targetId) {
    const neededUrls = [
        `/static/sounds/heroes/${attackerId}_attack.wav`,
        `/static/sounds/heroes/${targetId}_hit.wav`
    ];
    const ctx = getAudioContext();
    if (ctx.state === 'suspended') { await ctx.resume(); }
    for (const url of neededUrls) {
        const cached = soundCache.get(url);
        if (cached && !cached.decoded && cached.arrayBuffer) {
            try {
                const buffer = await ctx.decodeAudioData(cached.arrayBuffer.slice(0));
                cached.buffer = buffer;
                cached.decoded = true;
                delete cached.arrayBuffer;
            } catch (e) { console.warn(`解码失败: ${url}`, e); }
        }
    }
}

// ========== 技能视频映射 ==========
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
            "万宝朝宗": "wanbaochao.mp4", "龙虎如意": "longhu.mp4", "混元拂尘": "hunyuanfuchen.mp4",
            "玄甲护体": "xuanjia.mp4", "混元金斗": "hunyuanjindou.mp4", "金蛟剪": "jinjiaojian.mp4",
            "缚龙索": "fulongsuo.mp4", "定海珠": "dinghaizhu.mp4", "遁龙桩": "dunlongzhuang.mp4",
            "太极符印": "taijifuyin.mp4", "杨枝甘露": "yangzhiganlu.mp4", "五火七禽扇": "wuhuoqiqin.mp4",
            "降魔杵": "xiangmochu.mp4", "斩仙剑": "zhanxianjian.mp4", "九龙神火罩": "jiulongshenhuo.mp4",
            "照妖鉴": "zhaoyaojian.mp4", "风雷双翼": "fengleishuangyi.mp4", "八九玄功": "bajiuxuangong.mp4",
            "乾坤圈": "qiankunquan.mp4", "攒心钉": "zanxinding.mp4", "金光阵": "jinguangzhen.mp4",
            "开山斧": "kaishanfu.mp4", "飞头术": "feitoushu.mp4", "魅惑": "meihuo.mp4",
            "雌雄双鞭": "cixiongshuangbian.mp4", "金攥提炉枪": "jinzuan tiluqiang.mp4", "铁嘴神鹰": "tiezuishishenying.mp4",
            "混元锤": "hunyuanchui.mp4", "六魂幡": "liuhunfan.mp4", "牛黄": "niuhuang.mp4",
            "戮魂幡": "luhunfan.mp4", "五色石": "wuseshi.mp4", "百胜刀": "baishengdao.mp4",
            "仁德": "rende.mp4", "打神鞭": "dashenbian.mp4", "阴阳镜": "yinyangjing.mp4",
            "五火神焰扇": "wuhuoshenyan.mp4", "降魔宝杵": "xiangmobaochu.mp4", "玲珑宝塔": "linglongbaota.mp4",
            "吴钩剑": "wugoujian.mp4"
        };
    }
}

function getHeroId(heroName, heroObj) {
    if (heroObj && heroObj.id) return heroObj.id;
    const map = {
        "多宝道人": "duobao", "金灵圣母": "jinling", "无当圣母": "wudang", "龟灵圣母": "guiling",
        "云霄仙子": "yunxiao", "琼霄仙子": "qiongxiao", "碧霄仙子": "bixiao", "赵公明": "zhaogongming",
        "妲己": "daji", "文殊广法天尊": "wenshujun", "普贤真人": "puxian", "慈航道人": "cihang",
        "清虚道德真君": "qingxu", "道行天尊": "daoxing", "玉鼎真人": "yuding", "太乙真人": "taiyi",
        "云中子": "yunzhongzi", "雷震子": "leizhenzi", "杨戬": "yangjian", "哪吒": "nezha",
        "黄天化": "huangtianhua", "金光圣母": "jinguang", "巨灵神": "juling", "申公豹": "shenggong",
        "闻仲": "wenpeng", "黄飞虎": "huangfeihu", "崇黑虎": "chongheihu", "乌云仙": "wuyunxian",
        "长耳定光仙": "changxian", "金大升": "jintai", "余化": "yuwenhua", "韩智仙": "hanzhixian",
        "苏护": "suihu", "姬发": "jifayou", "姜子牙": "jiangziya", "申元": "shenyuan",
        "杨任": "yangren", "韦护": "weihu", "李靖": "lidong", "金吒": "jinzha", "木吒": "muzha",
        "凡人修士": "mortal"
    };
    return map[heroName] || heroName.toLowerCase().replace(/[^a-z]/g, '');
}

let currentSkillNameElement = null;
function showSkillName(skillName, duration = 2000) {
    if (currentSkillNameElement) { currentSkillNameElement.remove(); currentSkillNameElement = null; }
    let container = document.getElementById('battlePanel');
    if (!container) return;
    let div = document.createElement('div');
    div.className = 'skill-name-display';
    div.innerText = skillName;
    container.appendChild(div);
    currentSkillNameElement = div;
    setTimeout(() => { if (div && div.parentNode) div.remove(); if (currentSkillNameElement === div) currentSkillNameElement = null; }, duration);
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

function showStatusIcon(targetElement, statusType, duration = 5000) {
    if (!targetElement) return;
    let container = targetElement.closest('.hero-card-mini');
    if (!container) container = targetElement;
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
    setTimeout(() => { if (tip && tip.parentNode) tip.remove(); }, duration);
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
            { let container = targetElement.closest('.hero-card-mini') || targetElement;
              setTimeout(() => showStatusIcon(container, 'stun', 5000), 50); }
            break;
        case 'debuff':
            if (skillName && (skillName.includes('毒') || skillName.includes('蛊'))) {
                targetElement.classList.add('poison-smoke');
                setTimeout(() => targetElement.classList.remove('poison-smoke'), 1000);
                let container = targetElement.closest('.hero-card-mini') || targetElement;
                setTimeout(() => showStatusIcon(container, 'poison', 5000), 50);
            }
            break;
        case 'heal':
            targetElement.classList.add('heal-glow');
            setTimeout(() => targetElement.classList.remove('heal-glow'), 400);
            break;
        case 'buff':
            { let container = targetElement.closest('.hero-card-mini') || targetElement;
              setTimeout(() => showStatusIcon(container, 'strength_up', 5000), 50); }
            break;
        case 'shield':
            { let container = targetElement.closest('.hero-card-mini') || targetElement;
              setTimeout(() => showStatusIcon(container, 'shield', 5000), 50); }
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

async function animateSingleAttack(attackerId, attackerAvatar, targetAvatar, damage, skillType, isHeal, targetId, skillName) {
    if (window.skipRequested) return;
    if (skillName) showSkillName(skillName, 2000);
    if (!attackerAvatar || !targetAvatar) return;
    await ensureBattleSoundsReady(attackerId, targetId);
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
        let currentVideoSrc = `/static/videos/${videoFile}`;
        let fallbackVideoSrc = '/static/videos/season.mp4';
        let video = document.createElement('video');
        const tryPlay = (src) => {
            video.src = src;
            video.autoplay = true;
            video.loop = false;
            video.muted = true;
            video.playsInline = true;
            video.onerror = () => {
                if (src === currentVideoSrc) {
                    console.warn(`技能视频 ${videoFile} 加载失败，尝试使用默认视频 season.mp4`);
                    tryPlay(fallbackVideoSrc);
                } else {
                    console.error(`默认视频 season.mp4 也加载失败`);
                    if (videoPlace) videoPlace.style.display = 'none';
                }
            };
            video.oncanplay = () => {
                video.play().catch(err => {
                    console.warn(`视频自动播放失败: ${src}`, err);
                    if (videoPlace) videoPlace.style.display = 'none';
                });
            };
        };
        tryPlay(currentVideoSrc);
        videoPlace.appendChild(video);
        videoPlace.style.display = 'flex';
        await new Promise(r => setTimeout(r, 400));
    }
    const startRect = attackerAvatar.getBoundingClientRect();
    const targetRect = targetAvatar.getBoundingClientRect();
    const originalOpacity = attackerAvatar.style.opacity;
    attackerAvatar.style.opacity = '0';
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
    const attackerCard = attackerAvatar.closest('.hero-card-mini');
    const originalCardDisplay = attackerCard ? attackerCard.style.display : null;
    if (attackerCard) attackerCard.style.display = 'none';
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
        clone.remove(); attackerAvatar.style.opacity = originalOpacity;
        if (attackerCard) attackerCard.style.display = originalCardDisplay;
        if (videoPlace) videoPlace.style.display = 'none';
        return;
    }
    const originalTargetSrc = targetAvatar.src;
    targetAvatar.src = `/static/images/heroes/${targetId}_hit.png`;
    playSound(`/static/sounds/heroes/${attackerId}_attack.wav`, 0.6);
    playSound(`/static/sounds/heroes/${targetId}_hit.wav`, 0.6);
    if (!isHeal) showDamageNumber(targetAvatar, damage);
    if (skillType) applySkillEffect(skillType, targetAvatar, attackerAvatar, skillName);
    await new Promise(r => setTimeout(r, 900));
    if (window.skipRequested) {
        clone.remove(); attackerAvatar.style.opacity = originalOpacity;
        if (attackerCard) attackerCard.style.display = originalCardDisplay;
        targetAvatar.src = originalTargetSrc;
        if (videoPlace) videoPlace.style.display = 'none';
        return;
    }
    clone.remove();
    attackerAvatar.style.opacity = originalOpacity;
    if (attackerCard) attackerCard.style.display = originalCardDisplay;
    targetAvatar.src = originalTargetSrc;
    if (videoPlace) videoPlace.style.display = 'none';
}

async function animateMultiAttack(attackerId, attackerAvatar, targetsInfo, skillType, skillName) {
    if (window.skipRequested) return;
    if (skillName) showSkillName(skillName, 2000);
    if (!attackerAvatar) return;
    await ensureBattleSoundsReady(attackerId, targetsInfo[0]?.id || '');
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
        let currentVideoSrc = `/static/videos/${videoFile}`;
        let fallbackVideoSrc = '/static/videos/season.mp4';
        let video = document.createElement('video');
        const tryPlay = (src) => {
            video.src = src;
            video.autoplay = true;
            video.loop = false;
            video.muted = true;
            video.playsInline = true;
            video.onerror = () => {
                if (src === currentVideoSrc) {
                    console.warn(`技能视频 ${videoFile} 加载失败，尝试使用默认视频 season.mp4`);
                    tryPlay(fallbackVideoSrc);
                } else {
                    console.error(`默认视频 season.mp4 也加载失败`);
                    if (videoPlace) videoPlace.style.display = 'none';
                }
            };
            video.oncanplay = () => {
                video.play().catch(err => {
                    console.warn(`视频自动播放失败: ${src}`, err);
                    if (videoPlace) videoPlace.style.display = 'none';
                });
            };
        };
        tryPlay(currentVideoSrc);
        videoPlace.appendChild(video);
        videoPlace.style.display = 'flex';
    }
    playSound(`/static/sounds/heroes/${attackerId}_attack.wav`, 0.6);
    for (let i = 0; i < targetsInfo.length; i++) {
        if (window.skipRequested) break;
        const t = targetsInfo[i];
        await ensureBattleSoundsReady(attackerId, t.id);
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
    let imgSrc = avatarUrl ? avatarUrl : '/static/images/avatars/hero.png';
    div.innerHTML = `<img src="${imgSrc}" onerror="this.src='/static/images/heroes/hero.png'"><div class="enemy-hp">${playerName || '敌方'}</div>`;
    container.appendChild(div);
}

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

// ========== 核心战斗动画 + 日志文字输出 ==========
async function playBattleLogWithDelay(log, winner) {
    if (window.currentAnimationPromise) {
        window.skipRequested = true;
        await window.currentAnimationPromise;
    }
    if (!log || log.length === 0) {
        if (typeof addLog === 'function') addLog(`⚡ 战斗结束，胜者: ${winner === 'left' ? '我方' : '敌方'}`);
        setTimeout(() => { if (battleCallback) battleCallback(winner); hideBattlePanel(); }, 2000);
        return;
    }
    leftTeam = JSON.parse(JSON.stringify(originalLeftTeam));
    rightTeam = JSON.parse(JSON.stringify(originalRightTeam));
    renderGrids();
    updateTotalHpBars();
    window.skipRequested = false;
    window.isFighting = true;

    window.currentAnimationPromise = (async () => {
        try {
            for (let i = 0; i < log.length; i++) {
                if (window.skipRequested || !window.isFighting) {
                    if (typeof addLog === 'function') addLog("⏩ 战斗已中断，直接结算...");
                    let videoPlace = document.getElementById('skillVideoPlaceholder');
                    if (videoPlace) videoPlace.style.display = 'none';
                    if (typeof window.playBgMusic === 'function') window.playBgMusic();
                    applyFinalHp(log, winner);
                    if (battleCallback) battleCallback(winner);
                    hideBattlePanel();
                    return;
                }
                let entry = log[i];
                if (entry.type === 'attack' || entry.type === 'skill') {
                    if (entry.type === 'attack') {
                        let attackerName = entry.attacker;
                        let targetName = entry.target;
                        let damage = entry.damage || 0;
                        if (typeof addLog === 'function') {
                            addLog(`${attackerName} 攻击 ${targetName} 造成 ${damage} 伤害${entry.dead ? '，目标死亡！' : ''}`);
                        }
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
                        let attackerId = getHeroId(attackerName, {});
                        
                        if (typeof addLog === 'function') {
                            if (entry.is_multi && entry.targets) {
                                let totalDamage = entry.targets.reduce((sum, t) => sum + (t.damage || 0), 0);
                                if (skillType === 'heal') {
                                    addLog(`${attackerName} 使用 ${skillName} 治疗了多名队友`);
                                } else if (skillType === 'buff') {
                                    addLog(`${attackerName} 使用 ${skillName} 为全体施加增益`);
                                } else if (skillType === 'shield') {
                                    addLog(`${attackerName} 使用 ${skillName} 为全体附加护盾`);
                                } else {
                                    addLog(`${attackerName} 使用 ${skillName} 对多名敌人造成 ${totalDamage} 总伤害`);
                                }
                            } else {
                                let targetName = entry.target;
                                let damage = entry.damage || 0;
                                let isHeal = (skillType === 'heal');
                                let isBuff = (skillType === 'buff');
                                let isShield = (skillType === 'shield');
                                if (isHeal) {
                                    addLog(`${attackerName} 使用 ${skillName} 治疗 ${targetName} ${damage} 生命`);
                                } else if (isBuff) {
                                    addLog(`${attackerName} 使用 ${skillName} 为 ${targetName} 施加增益`);
                                } else if (isShield) {
                                    addLog(`${attackerName} 使用 ${skillName} 为 ${targetName} 附加护盾`);
                                } else {
                                    addLog(`${attackerName} 使用 ${skillName} 对 ${targetName} 造成 ${damage} 伤害${entry.dead ? '，目标死亡！' : ''}`);
                                }
                            }
                        }
                        if (entry.is_multi && entry.targets) {
                            let attackerAvatar = getHeroAvatarDiv(entry.attacker_team, attackerName);
                            const isNonDamage = (skillType === 'buff' || skillType === 'heal' || skillType === 'shield');
                            if (isNonDamage) {
                                if (attackerAvatar) {
                                    const originalAttackerSrc = attackerAvatar.src;
                                    attackerAvatar.src = `/static/images/heroes/${attackerId}_attack.png`;
                                    playSound(`/static/sounds/heroes/${attackerId}_attack.wav`, 0.6);
                                    setTimeout(() => {
                                        if (attackerAvatar) attackerAvatar.src = originalAttackerSrc;
                                    }, 1200);
                                }
                                showSkillName(skillName, 2000);
                                if (skillType === 'heal') {
                                    for (let t of entry.targets) {
                                        let targetId = getHeroId(t.name, {});
                                        playSound(`/static/sounds/heroes/${targetId}_hit.wav`, 0.6);
                                        let avatar = getHeroAvatarDiv(t.team, t.name);
                                        if (avatar) showDamageNumber(avatar, t.damage, true);
                                    }
                                } else {
                                    for (let t of entry.targets) {
                                        let targetId = getHeroId(t.name, {});
                                        playSound(`/static/sounds/heroes/${targetId}_hit.wav`, 0.5);
                                    }
                                }
                                for (let t of entry.targets) {
                                    let avatar = getHeroAvatarDiv(t.team, t.name);
                                    if (avatar) {
                                        let container = avatar.closest('.hero-card-mini') || avatar;
                                        setTimeout(() => {
                                            if (skillType === 'buff') showStatusIcon(container, 'strength_up', 5000);
                                            else if (skillType === 'shield') showStatusIcon(container, 'shield', 5000);
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
                            for (let t of entry.targets) {
                                let targetTeam = (t.team === 'left') ? leftTeam : rightTeam;
                                let hero = targetTeam.find(h => h.name === t.name);
                                if (hero) {
                                    hero.hp = Math.min(hero.maxHp, Math.max(0, t.hp_left));
                                    updateHeroHpBar(t.team, t.name, hero.hp, hero.maxHp);
                                }
                            }
                        } else {
                            let targetName = entry.target;
                            let damage = entry.damage || 0;
                            let isHeal = (skillType === 'heal');
                            let isBuff = (skillType === 'buff');
                            let isShield = (skillType === 'shield');
                            let attackerAvatar = getHeroAvatarDiv(entry.attacker_team, attackerName);
                            let targetAvatar = getHeroAvatarDiv(entry.target_team, targetName);
                            highlightHero(attackerAvatar, 500);
                            if (isBuff || isHeal || isShield) {
                                if (attackerAvatar) {
                                    const originalAttackerSrc = attackerAvatar.src;
                                    attackerAvatar.src = `/static/images/heroes/${attackerId}_attack.png`;
                                    playSound(`/static/sounds/heroes/${attackerId}_attack.wav`, 0.6);
                                    setTimeout(() => {
                                        if (attackerAvatar) attackerAvatar.src = originalAttackerSrc;
                                    }, 1200);
                                }
                                showSkillName(skillName, 2000);
                                if (isHeal) {
                                    let targetId = getHeroId(targetName, {});
                                    playSound(`/static/sounds/heroes/${targetId}_hit.wav`, 0.6);
                                    if (targetAvatar) showDamageNumber(targetAvatar, damage, true);
                                } else {
                                    let targetId = getHeroId(targetName, {});
                                    playSound(`/static/sounds/heroes/${targetId}_hit.wav`, 0.5);
                                }
                                if (targetAvatar) {
                                    let container = targetAvatar.closest('.hero-card-mini') || targetAvatar;
                                    setTimeout(() => {
                                        if (isBuff) showStatusIcon(container, 'strength_up', 5000);
                                        else if (isShield) showStatusIcon(container, 'shield', 5000);
                                    }, 100);
                                }
                                await new Promise(r => setTimeout(r, 1000));
                                let targetTeam = (entry.target_team === 'left') ? leftTeam : rightTeam;
                                let hero = targetTeam.find(h => h.name === targetName);
                                if (hero && (isHeal || isShield)) {
                                    hero.hp = Math.min(hero.maxHp, Math.max(0, entry.hp_left));
                                    updateHeroHpBar(entry.target_team, targetName, hero.hp, hero.maxHp);
                                }
                            } else {
                                if (attackerAvatar && targetAvatar) {
                                    let targetId = getHeroId(targetName, {});
                                    await animateSingleAttack(attackerId, attackerAvatar, targetAvatar, damage, skillType, false, targetId, skillName);
                                } else {
                                    await new Promise(r => setTimeout(r, 1400));
                                }
                                let targetTeam = (entry.target_team === 'left') ? leftTeam : rightTeam;
                                let hero = targetTeam.find(h => h.name === targetName);
                                if (hero) {
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
        } finally {
            if (!window.skipRequested && window.isFighting) {
                if (typeof addLog === 'function') addLog(`🏆 战斗结束，胜者: ${winner === 'left' ? '我方' : '敌方'}`);
                if (battleCallback) battleCallback(winner);
                if (winner === 'left') { if (typeof window.playWinSound === 'function') window.playWinSound(); }
                else { if (typeof window.playLoseSound === 'function') window.playLoseSound(); }
                applyFinalHp(log, winner);
                hideBattlePanel();
            } else {
                hideBattlePanel();
            }
            window.isFighting = false;
            window.currentAnimationPromise = null;
            window.skipRequested = false;
        }
    })();
    await window.currentAnimationPromise;
}

function showBattlePanel(leftTeamData, rightTeamData, logs, winner, leftPower, rightPower, callback, enemyPlayerName = null, enemyAvatar = null) {
    if (!leftTeamData || !rightTeamData) { if (callback) callback(winner); return; }
    for (let h of leftTeamData) if (h.maxHp > 0) h.hp = h.maxHp;
    for (let h of rightTeamData) if (h.maxHp > 0) h.hp = h.maxHp;
    updateEnemyPlayerAvatar(enemyAvatar, enemyPlayerName);
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

function renderGrids() {
    renderOneGrid('leftGrid', leftTeam);
    renderOneGrid('rightGrid', rightTeam);
    
    // 计算平均等级
    function calcAvgLevel(team) {
        if (!team.length) return 0;
        let total = 0;
        let count = 0;
        for (let hero of team) {
            total += hero.level || 1;
            count++;
        }
        return Math.floor(total / count);
    }
    let leftAvg = calcAvgLevel(leftTeam);
    let rightAvg = calcAvgLevel(rightTeam);
    
    // 更新阵营标题
    let leftTitle = document.querySelector('.left-grid-container .grid-title');
    let rightTitle = document.querySelector('.right-grid-container .grid-title');
    if (leftTitle) {
        leftTitle.innerHTML = `🔥 截教阵营 ${leftAvg > 0 ? `平均Lv.${leftAvg}` : ''}`;
    }
    if (rightTitle) {
        rightTitle.innerHTML = `⚡ 敌方阵营 ${rightAvg > 0 ? `平均Lv.${rightAvg}` : ''}`;
    }
}

function renderOneGrid(gridId, team) {
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
                // 不显示个体等级
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

// 暴露全局方法
window.showBattlePanel = showBattlePanel;
window.hideBattlePanel = hideBattlePanel;
window.applyFinalHp = applyFinalHp;
window.updateHeroHpBar = updateHeroHpBar;
window.startPreload = startPreload;
window.unlockAndDecodeSounds = unlockAndDecodeSounds;

// 页面加载后预加载音效（不自动解码）
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        loadSkillAnimations().then(() => initBattleControls());
        if (window.currentUser) { startPreload().catch(console.warn); }
    });
} else {
    loadSkillAnimations().then(() => initBattleControls());
    if (window.currentUser) { startPreload().catch(console.warn); }
}
document.body.addEventListener('click', () => { unlockAndDecodeSounds(); }, { once: true });