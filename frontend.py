def get_html():
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>截教 · 碧游宫</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
    <link rel="icon" href="data:;base64,iVBORw0KGgo=">
    <link rel="stylesheet" href="/static/css/battle.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; user-select: none; }
        body { background: #0a0f1a; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; height: 100vh; overflow: hidden; }
        .app { display: flex; flex-direction: column; height: 100%; position: relative; transition: background-image 0.3s ease; }
        .top-bar { position: absolute; top: 15px; left: 15px; right: 15px; display: flex; justify-content: space-between; z-index: 10003; background: rgba(0,0,0,0.5); backdrop-filter: blur(8px); border-radius: 50px; padding: 8px 20px; color: white; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .user-avatar { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #d99e3e; cursor: pointer; object-fit: cover; background: #2c3e2f; }
        .user-name { font-weight: bold; }
        .user-resources { display: flex; gap: 20px; align-items: center; }
        .resource-item { background: #2c3e2f; padding: 5px 12px; border-radius: 30px; font-size: 14px; color: #ffd966; }
        .music-control { display: inline-flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.5); border-radius: 30px; padding: 4px 12px; cursor: pointer; }
        .music-control span { font-size: 16px; color: gold; }
        .music-control input { display: none; }
        .top-buttons { display: flex; gap: 10px; }
        .top-buttons button { background: #2c3e2f; border: none; padding: 5px 15px; border-radius: 30px; color: white; cursor: pointer; }
        .main-content { flex: 1; margin-top: 70px; padding: 20px; overflow-y: auto; }
        .tab-bar { display: flex; gap: 15px; margin-bottom: 20px; background: rgba(0,0,0,0.4); padding: 10px; border-radius: 50px; backdrop-filter: blur(5px); }
        .tab-btn { background: #2c3e2f; border: none; padding: 8px 25px; border-radius: 40px; cursor: pointer; font-size: 16px; color: white; }
        .tab-btn.active { background: #d99e3e; color: #1e2a2e; font-weight: bold; }
        .tab-pane { display: none; }
        .tab-pane.active { display: block; }
        .map-container { background: rgba(0,0,0,0.5); border-radius: 20px; padding: 20px; backdrop-filter: blur(8px); }
        .node-chain { display: flex; justify-content: center; align-items: center; flex-wrap: wrap; margin: 30px 0 20px; }
        .node-card { background: #2c3e2f; border-radius: 16px; padding: 12px; width: 140px; text-align: center; cursor: pointer; transition: 0.1s; border: 1px solid #d99e3e; margin-bottom: 15px; }
        .node-card:hover { transform: scale(1.02); background: #3a5a3a; }
        .node-name { font-weight: bold; color: gold; }
        .node-power { font-size: 12px; color: #ccc; }
        .node-reward { font-size: 12px; color: #ffaa66; }
        .connector { font-size: 24px; color: gold; }
        .formation-area { display: flex; flex-direction: column; align-items: center; }
        .formation-header { display: flex; justify-content: center; gap: 20px; margin-bottom: 20px; align-items: center; }
        .formation-select { background: #2c3e2f; padding: 5px 15px; border-radius: 30px; border: 1px solid gold; color: white; }
        .formation-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; width: 400px; margin: 0 auto; background: rgba(0,0,0,0.6); border-radius: 20px; padding: 20px; }
        .formation-slot { background: rgba(30,40,30,0.8); border-radius: 12px; aspect-ratio: 1; display: flex; align-items: center; justify-content: center; cursor: pointer; }
        .formation-slot.disabled-slot { background: #2a2a2a; cursor: not-allowed; opacity: 0.5; }
        .formation-hero { text-align: center; }
        .formation-hero img { width: 60px; height: 60px; border-radius: 8px; object-fit: cover; }
        .formation-hero-name { font-size: 10px; color: white; }
        .empty-slot { color: #aaa; font-size: 12px; }
        .gem-grid { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 20px; }
        .gem-card { background: #2c3e2f; border-radius: 12px; padding: 8px; width: 110px; text-align: center; color: #ffd966; transition: 0.1s; }
        .gem-card:hover { transform: scale(1.02); background: #3a5a3a; }
        .hero-card { background: #2c3e2f; border-radius: 12px; padding: 12px; width: 150px; text-align: center; color: #ffd966; }
        .hero-card img { width: 100px; height: 100px; border-radius: 12px; object-fit: cover; margin-bottom: 8px; }
        .hero-card button { padding: 4px 12px; font-size: 12px; margin: 4px; color: #111; }
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: transparent; display: flex; align-items: center; justify-content: center; z-index: 100000; }
        .modal-content { background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px); border-radius: 20px; padding: 20px; max-width: 90vw; max-height: 85vh; overflow: auto; border: 1px solid gold; color: #f0f0f0; box-shadow: 0 0 30px rgba(0,0,0,0.5); }
        .modal-content h3, .modal-content h4 { color: gold; }
        .modal-content p, .modal-content span, .modal-content div, .modal-content td { color: #f0f0f0; }
        .modal-content input, .modal-content select, .modal-content textarea { background: #2c3e2f; color: white; border: 1px solid #d99e3e; }
        .modal-content button { background: #d99e3e; color: #1e2a2e; }
        #recruitShopModal .modal-content { background: rgba(0, 0, 0, 0.7); }
        .attr-row { display: flex; justify-content: space-between; margin: 8px 0; }
        .gem-slot { display: inline-block; width: 70px; height: 80px; background: #2c3e2f; border: 1px solid gold; border-radius: 8px; margin: 5px; cursor: pointer; text-align: center; vertical-align: top; padding: 5px; }
        .gem-slot img { width: 40px; height: 40px; object-fit: contain; }
        .gem-slot button { font-size: 10px; padding: 2px 4px; margin-top: 4px; }
        .friend-panel { position: fixed; top: 80px; left: 20px; width: 320px; background: #f5f0e8 !important; border-radius: 20px; border: 1px solid #c9b27c; z-index: 10003; padding: 12px; color: #3a2a1a; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .friend-panel h4 { color: #5a3a1a; }
        .friend-item { background: #fef9e6; border-radius: 12px; padding: 8px 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .friend-item:hover { background: #f3e9ce; }
        .self-item { background: #e2dccd; border: 1px solid #b38f40; }
        .friend-avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 1px solid #c9b27c; }
        .friend-name { font-weight: bold; flex: 1; margin-left: 8px; }
        .friend-status { font-size: 11px; color: #5a7a5a; }
        .friend-actions button { background: #d9c48b; border: none; padding: 4px 10px; border-radius: 20px; font-size: 12px; cursor: pointer; }
        .modal-friend-actions { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-top: 20px; }
        .modal-friend-actions button { background: #d9c48b; padding: 8px 16px; font-size: 14px; border: none; border-radius: 30px; cursor: pointer; }
        .log-panel { position: absolute; bottom: 20px; right: 20px; width: 320px; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); border-radius: 12px; color: #0f0; font-family: monospace; font-size: 12px; cursor: move; z-index: 10002; border: 1px solid gold; display: flex; flex-direction: column; }
        .log-header { cursor: move; background: #1e2a2e; padding: 5px; border-radius: 12px 12px 0 0; font-weight: bold; }
        .log-content { height: 180px; overflow-y: auto; padding: 5px; }
        .log-input { display: flex; border-top: 1px solid #555; padding: 5px; }
        .log-input input { flex: 1; background: #2c3e2f; color: white; border: none; padding: 5px; border-radius: 20px; user-select: text; -webkit-user-select: text; }
        .log-input button { margin-left: 5px; padding: 4px 12px; }
        button { background: #d99e3e; border: none; padding: 8px 25px; font-size: 16px; border-radius: 40px; font-weight: bold; cursor: pointer; color: #111; }
        select, input { background: #2c3e2f; color: white; border: 1px solid #d99e3e; padding: 5px; border-radius: 8px; }
        .hero-grid { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }
        .recruit-card { width: 140px; text-align: center; background: #2c3e2f; border-radius: 16px; padding: 10px; cursor: pointer; }
        .recruit-card img { width: 100px; height: 100px; border-radius: 8px; object-fit: cover; }
        .branch-card { background: rgba(30, 40, 30, 0.9); margin: 5px; padding: 8px; border-radius: 12px; display: flex; align-items: center; gap: 10px; color: #ffd966; }
        .branch-card button { background: #d99e3e; border: none; padding: 4px 12px; border-radius: 20px; cursor: pointer; color: #1e2a2e; font-weight: bold; }
        .branch-card button:disabled { opacity: 0.5; cursor: not-allowed; }
        .power-value { background: rgba(0,0,0,0.7); padding: 2px 10px; border-radius: 20px; display: inline-block; }
        .city-layout { display: flex; gap: 20px; flex-wrap: wrap; }
        .city-column { background: rgba(0, 0, 0, 0.5); border-radius: 20px; padding: 15px; backdrop-filter: blur(4px); color: #ffd966; }
        .city-column h3, .city-column h4 { color: gold; }
        .city-column p, .city-column span, .city-column div { color: #ffd966; }
        .branch-column { flex: 1; min-width: 260px; }
        .task-column { flex: 2; min-width: 360px; }
        .info-column { flex: 1; min-width: 220px; }
        #ownPalaceInfo { color: #ffd966; }
        #ownPalaceInfo p, #ownPalaceInfo span, #ownPalaceInfo div { color: #ffd966; }
        #occupierDisplay img { border: 1px solid gold; border-radius: 50%; }
        #selfReleaseBtn { background: #8a5a5a; color: white; }
        .task-item { background: #2c3e2f; border-radius: 12px; padding: 10px; margin-bottom: 12px; }
        .task-progress { font-size: 12px; color: #ffaa66; }
        .claim-task-btn { background: #d99e3e; border: none; padding: 4px 12px; border-radius: 20px; cursor: pointer; font-size: 12px; }
        .claim-task-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .shop-qty-control { display: flex; justify-content: center; gap: 10px; margin: 10px 0; }
        .shop-qty-control button { background: #5a7a5a; width: 28px; height: 28px; border-radius: 50%; font-weight: bold; }
        .pray-panel-in-modal { margin-top: 20px; border-top: 1px solid #d99e3e; padding-top: 15px; }
        .pray-buttons { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
        .pray-btn { background: #2c3e2f; border: 1px solid #d99e3e; border-radius: 40px; padding: 8px 16px; width: 100px; text-align: center; cursor: pointer; transition: 0.1s; }
        .pray-btn:hover { transform: scale(1.02); background: #3a5a3a; }
        .pray-btn.disabled { opacity: 0.5; pointer-events: none; }
        .rank-table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #f0f0f0; }
        .rank-table th, .rank-table td { padding: 8px; text-align: left; border-bottom: 1px solid #555; color: #f0f0f0; }
        .rank-table th { background: #2c3e2f; color: gold; }
        .my-rank-info { margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.5); border-radius: 12px; text-align: center; font-weight: bold; color: gold; }
        #preloadProgressBar { position: fixed; top: 70px; left: 0; width: 100%; height: 4px; background: rgba(0,0,0,0.5); z-index: 10004; display: none; }
        #preloadProgressFill { width: 0%; height: 100%; background: linear-gradient(90deg, #d99e3e, gold); transition: width 0.3s; }
        
        /* ========== 手机版适配（宽度 ≤ 768px） ========== */
@media (max-width: 768px) {
    .top-bar {
        display: grid;
        grid-template-areas: 
            "info resources"
            "buttons buttons";
        gap: 6px;
        position: relative;
        top: 0;
        left: 0;
        right: 0;
        border-radius: 0;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(12px);
        padding: 6px 10px;
        margin-bottom: 8px;
    }
    .user-info {
        grid-area: info;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .user-avatar {
        width: 32px;
        height: 32px;
        flex-shrink: 0;
    }
    .user-name {
        font-size: 14px;
        font-weight: bold;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 120px;
    }
    .user-resources {
        grid-area: resources;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 6px;
    }
    .resource-item {
        font-size: 11px;
        padding: 2px 6px;
        background: #2c3e2f;
        border-radius: 20px;
        white-space: nowrap;
    }
    .music-control {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #2c3e2f;
        border-radius: 30px;
        width: 34px;
        height: 34px;
        cursor: pointer;
    }
    .music-control span {
        font-size: 18px;
        color: gold;
    }
    .music-control input {
        display: none;
    }
    .top-buttons {
        grid-area: buttons;
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        gap: 6px;
        padding-bottom: 4px;
    }
    .top-buttons button {
        font-size: 10px;
        padding: 4px 8px;
        background: #2c3e2f;
        border-radius: 30px;
        color: white;
        white-space: nowrap;
        flex-shrink: 0;
    }
    #blessingTimer {
        display: none !important;
    }

    .main-content {
        margin-top: 0;
        padding: 8px 8px 80px 8px;
        overflow-y: auto;
        height: calc(100vh - 110px);
    }
    .tab-bar {
        gap: 6px;
        padding: 4px;
        margin-bottom: 8px;
        justify-content: center;
        flex-wrap: wrap;
    }
    .tab-btn {
        font-size: 11px;
        padding: 3px 10px;
    }

    .formation-area {
        width: 100%;
    }
    .formation-header {
        flex-direction: column;
        gap: 8px;
        align-items: stretch;
        margin-bottom: 12px;
    }
    .formation-header label {
        font-size: 12px;
    }
    .formation-select {
        font-size: 12px;
        padding: 3px 10px;
        width: 100%;
    }
    .formation-header button {
        font-size: 11px;
        padding: 4px 8px;
        margin: 2px 0;
    }
    .formation-grid {
        width: 100%;
        gap: 6px;
        padding: 10px;
        transform: scale(0.85);
        transform-origin: top center;
        margin-bottom: 10px;
    }
    .formation-slot {
        width: auto;
        height: auto;
        min-height: 70px;
    }
    .formation-hero img {
        width: 35px;
        height: 35px;
    }
    .formation-hero-name {
        font-size: 8px;
    }

    .map-container {
        width: 100%;
        overflow-x: auto;
    }
    .node-chain {
        flex-wrap: nowrap;
        overflow-x: auto;
        justify-content: flex-start;
        gap: 6px;
        padding-bottom: 8px;
    }
    .node-card {
        width: 95px;
        padding: 6px;
        flex-shrink: 0;
    }
    .node-name {
        font-size: 11px;
    }
    .node-power, .node-reward {
        font-size: 9px;
    }

    .gem-grid {
        transform: scale(0.9);
        transform-origin: top center;
        gap: 8px;
    }
    .gem-card {
        width: 70px;
        padding: 4px;
    }
    .gem-card strong {
        font-size: 9px;
    }

    .city-layout {
        flex-direction: column;
        gap: 10px;
    }
    .city-column {
        width: 100%;
        padding: 8px;
    }
    .branch-card {
        padding: 5px;
        gap: 5px;
    }
    .branch-card button {
        padding: 2px 6px;
        font-size: 9px;
    }

    /* 战斗画面 - 紧凑布局 */
    .battle-panel {
        overflow-y: auto;
        justify-content: flex-start;
        padding: 5px 5px 120px 5px;
        -webkit-overflow-scrolling: touch;
    }
    .health-bars {
        position: relative;
        z-index: 30;
        padding: 8px 12px;
        flex-direction: row;
        gap: 20px;
        background: rgba(0, 0, 0, 0.85);
        border-radius: 12px;
        margin-bottom: 10px;
        justify-content: center;
        border: 1px solid gold;
        backdrop-filter: blur(4px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
    .team-health {
        font-size: 12px;
        flex: 1;
        text-align: center;
        max-width: 160px;
        background: rgba(30, 40, 30, 0.95);
        border-radius: 10px;
        padding: 5px 8px;
        border: 1px solid #d99e3e;
        color: #ffd966;
        font-weight: bold;
        text-shadow: 0 0 2px #000;
    }
    .team-health .total-bar {
        width: 100%;
        height: 8px;
        background: #3a2a2a;
        border-radius: 4px;
        margin-top: 4px;
        overflow: hidden;
    }
    .team-health .total-fill {
        height: 100%;
        background: #5cb85c;
        transition: width 0.2s;
    }
    .power-value {
        font-size: 10px;
        padding: 2px 6px;
        background: rgba(0, 0, 0, 0.7);
        border-radius: 20px;
        color: #ffaa66;
    }
    .battlefield {
        padding: 0;
        flex-direction: column;
        align-items: center;
        gap: 15px;
        overflow-x: visible;
        min-height: auto;
    }
    /* 我方阵营 - 紧贴血量条 */
    .grid-container.left-grid-container {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-left: 0;
        margin-top: 0px;
    }
    .left-grid-container .grid-title {
        font-size: 12px;
        text-align: left;
        margin-left: 10px;
        margin-bottom: 5px;
        transform: translateY(-8px);
        color: gold;
        font-weight: bold;
        text-shadow: 0 0 2px black;
    }
    .left-grid-container .grid-3x3 {
        transform: scale(0.85);
        transform-origin: top left;
    }
    /* 敌方阵营 - 上移一个人物高度，使双方紧凑 */
    .grid-container.right-grid-container {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        margin-right: 0;
        margin-top: -150px;      /* 上移 150px，约一个人物高度 */
        margin-bottom: 0;
    }
    .right-grid-container .grid-title {
        font-size: 12px;
        text-align: right;
        margin-right: 10px;
        margin-bottom: 5px;
        transform: translateY(-8px);
        color: gold;
        font-weight: bold;
        text-shadow: 0 0 2px black;
    }
    .right-grid-container .grid-3x3 {
        transform: scale(0.85);
        transform-origin: top right;
    }
    .grid-slot {
        width: 60px;
        height: 80px;
    }
    .hero-avatar-mini {
        max-width: 130%;
        max-height: 130%;
        bottom: -5px;
        left: 50%;
        transform: translateX(-50%);
    }
    .right-grid .hero-avatar-mini {
        transform: translateX(-50%) scaleX(-1);
    }
    .hero-name-mini {
        bottom: 18px;
        font-size: 7px;
    }
    .hero-hp-mini {
        bottom: 2px;
        font-size: 6px;
    }
    .grid-row-1 {
        margin-bottom: -12px;
    }
    .grid-row-2 {
        margin-bottom: -12px;
    }
    .skill-video-placeholder {
        width: 180px;
        height: 101px;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 10300;
    }
    .skill-name-display {
        font-size: 12px;
        top: 40%;
        left: 50%;
        transform: translate(-50%, -50%);
        white-space: nowrap;
        z-index: 10015;
        padding: 2px 8px;
    }
    /* 逃跑按钮随敌方上移 */
    .controls {
        position: relative;
        z-index: 10003;
        margin-top: -150px;
        margin-left: 5px;
        margin-right: auto;
        width: fit-content;
        background: rgba(0,0,0,0.7);
        padding: 4px 10px;
        border-radius: 30px;
        backdrop-filter: blur(4px);
        box-shadow: 0 0 6px rgba(0,0,0,0.5);
    }
    .controls .skip-btn {
        display: none;
    }
    .controls .escape-btn {
        display: inline-block;
        padding: 4px 16px;
        font-size: 13px;
        background: #8b3c2c;
        color: white;
        border: none;
        border-radius: 30px;
        font-weight: bold;
        cursor: pointer;
    }
    .controls button:not(.escape-btn) {
        display: none;
    }
    .enemy-avatars {
        top: 5px;
        right: 5px;
        padding: 2px 5px;
        background: rgba(0,0,0,0.5);
        border-radius: 20px;
        z-index: 25;
    }
    .enemy-avatar-item {
        width: 30px;
    }
    .enemy-avatar-item img {
        width: 24px;
        height: 24px;
    }
    .enemy-hp {
        font-size: 8px;
    }

    .log-panel {
        width: calc(100% - 20px);
        right: 10px;
        bottom: 10px;
        left: 10px;
        margin: 0;
        z-index: 10002;
    }
    .log-header {
        font-size: 11px;
        padding: 3px;
    }
    .log-content {
        height: 120px;
        font-size: 10px;
    }
    .log-content p {
        color: #ffaa66;
    }
    .log-input input {
        font-size: 11px;
        padding: 4px;
    }
    .log-input button {
        padding: 2px 8px;
        font-size: 11px;
    }

    #recruitShopModal .modal-content {
        width: 90vw;
        max-width: 90vw;
        max-height: 85vh;
        padding: 8px;
    }
    #recruitShopModal .hero-grid {
        gap: 6px;
        max-height: 45vh;
        overflow-y: auto;
    }
    #recruitShopModal .recruit-card {
        width: 90px;
        padding: 4px;
    }
    #recruitShopModal .recruit-card img {
        width: 60px;
        height: 60px;
    }
    #recruitShopModal .recruit-card button {
        font-size: 9px;
        padding: 2px 5px;
    }
    #recruitShopModal .pray-buttons {
        gap: 6px;
    }
    #recruitShopModal .pray-btn {
        width: 60px;
        padding: 3px 5px;
        font-size: 9px;
    }
    #recruitShopModal .pray-panel-in-modal {
        margin-top: 10px;
        padding-top: 8px;
    }

    .friend-panel {
        width: 90vw;
        left: 5vw;
        top: 60px;
    }
    .modal-content {
        width: 95vw;
        max-width: 95vw;
    }
    .hero-card {
        width: 105px;
    }
    .pray-btn {
        width: 70px;
        padding: 5px 8px;
        font-size: 10px;
    }
    .empty-slot {
        font-size: 10px;
    }

    /* 宝石分解底部留白 */
    #tab-gems {
        padding-bottom: 120px;
    }
}
    </style>
</head>
<body>
<div class="app" id="app" style="background-size: cover; background-position: center;">
    <div id="preloadProgressBar">
        <div id="preloadProgressFill"></div>
    </div>
    <div class="top-bar">
        <div class="user-info">
            <img id="userAvatar" class="user-avatar" src="/static/images/avatars/hero.png" onerror="this.src='/static/images/avatars/hero.png'" onclick="showAvatarModal()">
            <div style="display: flex; align-items: center;">
                <span id="userName" class="user-name">加载中...</span>
            </div>
        </div>
        <div class="user-resources">
            <div class="resource-item">💰 金币: <span id="userGold">0</span></div>
            <div class="resource-item">💎 钻石: <span id="userIngots">0</span></div>
            <div class="music-control" id="musicControlIcon" onclick="showVolumeModal()">
                <span>🎵</span>
            </div>
        </div>
        <div class="top-buttons">
            <button onclick="showPowerRank()">🏆 天骄榜</button>
            <button onclick="openRecruitShop()">🏛️ 万仙殿</button>
            <button onclick="openMyHeroes()">⚔️ 我的武将</button>
            <button onclick="toggleFriendPanel()">👥 好友</button>
            <button onclick="logout()">🚪 注销</button>
        </div>
    </div>

    <div class="main-content" id="mainContent">
        <div class="tab-bar">
            <button class="tab-btn active" data-tab="map">🗺️ 仙岛</button>
            <button class="tab-btn" data-tab="formation">⚔️ 演武场</button>
            <button class="tab-btn" data-tab="gems">💎 八卦炉</button>
            <button class="tab-btn" data-tab="city">🏠 碧游宫</button>
        </div>
        <div id="tab-map" class="tab-pane active">
            <div class="map-container">
                <div style="display:flex; justify-content:space-between; align-items:center;"><h3 style="color:gold;">📖 仙岛闯关</h3><select id="challengeSelect" style="background:#2c3e2f; color:white; padding:5px 10px; border-radius:20px;"><option>加载中...</option></select></div>
                <div id="nodeChain" class="node-chain"></div>
            </div>
        </div>
        <div id="tab-formation" class="tab-pane">
            <div class="formation-area">
                <div class="formation-header">
                    <label>选择阵法：</label>
                    <select id="formationType" class="formation-select">
                        <option value="normal">普通阵（无加成）</option>
                        <option value="attack">攻击阵（力量+10%）</option>
                        <option value="intelligence">智力阵（智力+10%）</option>
                        <option value="defense">防御阵（生命+10%）</option>
                        <option value="speed">敏捷阵（速度+10%）</option>
                    </select>
                    <button onclick="saveFormationWithType()">保存阵型</button>
                    <button onclick="clearCurrentFormation()" style="background:#8a5a5a;">🗑️ 清除阵容</button>
                </div>
                <div id="formationGrid" class="formation-grid"></div>
                <p style="color:#aaa; margin-top:20px;">点击亮色格子选择武将，最多5人，可替换</p>
            </div>
        </div>
        <div id="tab-gems" class="tab-pane">
            <div style="background: rgba(0,0,0,0.5); border-radius: 20px; padding: 15px; margin-bottom: 20px;">
                <h3 style="color: gold; margin-top: 0;">💎 宝石商店（1钻石/个）</h3>
                <div id="gemShopContainer" class="gem-grid" style="justify-content: center;"></div>
            </div>
            <h3 style="color:gold;">宝石背包</h3><div id="gemBag" class="gem-grid"></div>
            <h3 style="color:gold;">宝石融合</h3>
            <div>选择两颗宝石进行融合（相同星级）</div>
            <div id="fusionSelect" style="display:flex; gap:20px; margin:10px 0;"></div>
            <div id="fusionRuleHint" style="font-size:12px; margin-top:5px; padding:8px; border-radius:8px; background:rgba(0,0,0,0.5); color:#aaa;"></div>
            <h3 style="color:gold;">宝石分解（仅双属性宝石）</h3><select id="decomposeSelect"></select><button onclick="decomposeGem()">分解</button>
        </div>
        <div id="tab-city" class="tab-pane">
            <div class="city-layout">
                <div class="city-column branch-column">
                    <h4 style="color: gold; margin-top: 0;">🏯 我的分舵</h4>
                    <div id="branchList" style="max-height: 400px; overflow-y: auto; color:#ffd966;"></div>
                </div>
                <div class="city-column task-column">
                    <h3 style="color: gold; margin-top: 0;">📋 每日修行</h3>
                    <div id="dailyTasksPanel"></div>
                </div>
                <div class="city-column info-column">
                    <h4 style="color: gold; margin-top: 0;">🏰 碧游宫</h4>
                    <div id="ownPalaceInfo">
                        <p>等级: <span id="playerLevel">0</span></p>
                        <p>经验: <span id="playerExp">0</span></p>
                        <div id="occupierDisplay">
                            <div style="display:flex; align-items:center; gap:10px; margin:10px 0;">
                                <img id="occupierAvatar" src="/static/images/avatars/hero.png" style="width:45px; border-radius:50%;">
                                <span id="occupierName">无</span>
                            </div>
                            <button id="selfReleaseBtn" style="display:none;" onclick="selfRelease()">🔓 解救自己</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="log-panel" id="logPanel">
        <div class="log-header"><strong>📜 战报 & 聊天 (可拖动)</strong></div>
        <div class="log-content" id="logContent">等待战斗...</div>
        <div class="log-input"><input type="text" id="chatInput" placeholder="输入消息 (支持 @好友 私聊)"><button id="sendChatBtn">发送</button></div>
    </div>

    <div id="battlePanel" class="battle-panel">
        <div id="enemyAvatars" class="enemy-avatars"></div>
        <div class="health-bars">
            <div class="team-health"><div>🔥 我方 <span class="power-value" id="leftPower">0</span> 战力</div><div class="total-bar"><div class="total-fill" id="leftTotalFill"></div></div></div>
            <div class="team-health"><div>⚡ 敌方 <span class="power-value" id="rightPower">0</span> 战力</div><div class="total-bar"><div class="total-fill" id="rightTotalFill"></div></div></div>
        </div>
        <div class="battlefield">
            <div class="grid-container left-grid-container"><div class="grid-title">🔥 截教阵营</div><div class="grid-3x3 left-grid" id="leftGrid"></div></div>
            <div class="grid-container right-grid-container"><div class="grid-title">⚡ 敌方阵营</div><div class="grid-3x3 right-grid" id="rightGrid"></div></div>
        </div>
        <div class="controls">
            <button id="skipFightBtn" class="skip-btn">⏩ 跳过战斗</button>
            <button id="escapeBtn" class="escape-btn">🏃 逃跑</button>
        </div>
    </div>

    <div id="authModal" class="modal" style="display: flex; z-index: 10002;"><div class="modal-content" style="width: 320px;"><h3 id="authTitle">登录</h3><div id="authForm"><input type="text" id="authUsername" placeholder="用户名" maxlength="5" style="width:100%; margin:5px 0;"><br><input type="password" id="authPassword" placeholder="密码" style="width:100%; margin:5px 0;"><br><div id="authEmailGroup" style="display:none;"><input type="email" id="authEmail" placeholder="邮箱" style="width:100%; margin:5px 0;"></div><button id="authSubmitBtn" style="width:100%; margin:5px 0;">登录</button><button id="switchAuthBtn" style="width:100%; background: #3a5a3a;">没有账号？去注册</button></div></div></div>
    <div id="avatarModal" class="modal" style="display:none;"><div class="modal-content"><h3>选择头像</h3><div id="avatarList" class="hero-grid"></div><button onclick="closeAvatarModal()">关闭</button></div></div>
    <div id="recruitShopModal" class="modal" style="display:none;">
        <div class="modal-content">
            <h3>🏛️ 万仙殿</h3>
            <div id="recruitShopInfo"></div>
            <div id="recruitHeroes" class="hero-grid"></div>
            <div style="text-align:center;">
                <button onclick="refreshRecruitShop()">刷新 (100金币)</button>
                <span id="nextRefreshTime"></span>
            </div>
            <div class="pray-panel-in-modal">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="color: gold; margin: 0;">🙏 烧香祈愿 · 每次消耗1000金币</h4>
                    <span id="prayRemainCount" style="background: #2c3e2f; padding: 2px 10px; border-radius: 20px;">今日剩余: --</span>
                </div>
                <div class="pray-buttons">
                    <div class="pray-btn" data-type="wealth"><div>💰 求财</div><small style="font-size: 10px;">50%得金币</small></div>
                    <div class="pray-btn" data-type="love"><div>💕 求缘</div><small style="font-size: 10px;">50%得武将</small></div>
                    <div class="pray-btn" data-type="chance"><div>🍀 求机缘</div><small style="font-size: 10px;">30%得经验药水</small></div>
                </div>
                <div id="prayResult" style="margin-top: 12px; font-size: 12px; color: #ffaa66; text-align: center;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                <span id="recruitBlessingTimer" style="background: #2c3e2f; padding: 4px 10px; border-radius: 20px; font-size: 12px; color: #ffaa66;">⏳ 祝福剩余 --:--</span>
                <button onclick="closeRecruitShop()">关闭</button>
            </div>
        </div>
    </div>
    <div id="myHeroesModal" class="modal" style="display:none;">
        <div class="modal-content" style="position: relative;">
            <button onclick="closeMyHeroes()" style="position: absolute; top: 10px; right: 15px; background: #8a5a5a; border: none; font-size: 20px; cursor: pointer; padding: 2px 10px; border-radius: 20px;">✕</button>
            <h3 style="margin-top: 0;">我的武将</h3>
            <div id="myHeroesList" class="hero-grid"></div>
        </div>
    </div>
    <div id="heroDetailModal" class="modal" style="display:none;"><div class="modal-content"><div id="heroDetailContent"></div><button onclick="closeHeroDetail()">关闭</button></div></div>

    <div id="friendPanel" class="friend-panel" style="display:none;">
        <div style="display:flex; justify-content:space-between; align-items:center;"><h4 style="margin:0;">👥 好友列表</h4><button onclick="toggleFriendPanel()" style="padding:2px 8px;">🗕</button></div>
        <div style="max-height:400px; overflow-y:auto; margin-top:10px;">
            <div class="friend-item self-item"><div style="display:flex; align-items:center; gap:10px;"><img src="/static/images/avatars/hero.png" class="friend-avatar" id="selfAvatar"><span style="font-weight:bold;">我（<span id="selfName"></span>）</span></div><button onclick="soloPracticeFromFriend()" style="background:#5a7a5a;">🏋️ 自我切磋</button></div>
            <div id="friendListContainer"></div><div id="noFriendsMsg" style="color:#aaa; text-align:center; padding:10px; display:none;">暂无好友，去添加吧~</div>
        </div>
        <div style="margin-top:10px; display:flex; gap:5px;"><input id="addFriendInput" placeholder="输入用户名" style="flex:1; background:#f0ede8; color:#333;"><button onclick="sendFriendRequest()" style="background:#b38f40;">添加</button></div>
    </div>

    <div id="powerRankModal" class="modal" style="display:none;">
        <div class="modal-content" style="width: 500px; max-height: 80vh; overflow-y: auto;">
            <h3>🏆 天骄榜</h3>
            <div id="rankList" style="margin: 15px 0;"></div>
            <div id="myRankInfo" class="my-rank-info"></div>
            <button onclick="closePowerRank()" style="margin-top: 10px;">关闭</button>
        </div>
    </div>
</div>

<script src="/static/js/battle.js"></script>
<script>
// ========== 全局变量 ==========
let ws = null;
let currentUser = null;
let myFormation = [];
let currentFormationType = 'normal';
let currentChallengeId = null;
let isLoginMode = true;
let branchTimer = null;
let friendsList = [];
let blacklist = [];
let heroIdMap = {};

// ========== 图片缓存池 ==========
const imageCache = new Map();
let preloadTotal = 0;
let preloadLoaded = 0;
let preloadInProgress = false;
let preloadUrls = [];

async function collectPreloadUrls() {
    const urls = new Set();
    if (currentUser) {
        try {
            const res = await fetch(`/my_heroes?username=${currentUser}`);
            const data = await res.json();
            if (data.heroes) {
                for (const hero of data.heroes) {
                    urls.add(`/static/images/heroes/${hero.id}.png`);
                    urls.add(`/static/images/heroes/${hero.id}_attack.png`);
                    urls.add(`/static/images/heroes/${hero.id}_hit.png`);
                }
            }
        } catch(e) { console.warn('获取武将列表失败', e); }
    }
    const bgList = ['/static/images/bg/challenge_jinao.jpg','/static/images/bg/challenge_sanxian.jpg','/static/images/bg/lianxianzhen.jpg','/static/images/bg/bagualu.jpg','/static/images/bg/biyougong.jpg','/static/images/bg/wanxiandian.jpg','/static/images/bg/battle_bg.jpg'];
    for (const bg of bgList) urls.add(bg);
    const gemList = ['strength.png','intelligence.png','speed.png','hp.png','double.png'];
    for (const gem of gemList) urls.add(`/static/images/gems/${gem}`);
    urls.add('/static/images/avatars/hero.png');
    urls.add('/static/images/heroes/hero.png');
    return Array.from(urls);
}

function preloadImage(url) {
    return new Promise((resolve) => {
        if (imageCache.has(url)) { resolve(imageCache.get(url)); return; }
        const img = new Image();
        img.onload = () => { imageCache.set(url, img); resolve(img); };
        img.onerror = () => { imageCache.set(url, null); resolve(null); };
        img.src = url;
    });
}

function showPreloadProgress(percent) {
    const bar = document.getElementById('preloadProgressBar');
    const fill = document.getElementById('preloadProgressFill');
    if (bar && fill) { bar.style.display = 'block'; fill.style.width = percent + '%'; }
}
function hidePreloadProgress() { const bar = document.getElementById('preloadProgressBar'); if (bar) bar.style.display = 'none'; }

async function startPreload() {
    if (preloadInProgress) return;
    preloadInProgress = true;
    preloadUrls = await collectPreloadUrls();
    preloadTotal = preloadUrls.length;
    preloadLoaded = 0;
    console.log(`开始预加载 ${preloadTotal} 张图片...`);
    showPreloadProgress(0);
    const batchSize = 10;
    for (let i = 0; i < preloadUrls.length; i += batchSize) {
        const batch = preloadUrls.slice(i, i + batchSize);
        await Promise.all(batch.map(async (url) => {
            await preloadImage(url);
            preloadLoaded++;
            const percent = Math.floor((preloadLoaded / preloadTotal) * 100);
            showPreloadProgress(percent);
        }));
        await new Promise(r => setTimeout(r, 50));
    }
    console.log('图片预加载完成');
    setTimeout(hidePreloadProgress, 1000);
    preloadInProgress = false;
}

function getCachedImageUrl(url) { return (imageCache.has(url) && imageCache.get(url)) ? imageCache.get(url).src : url; }
function setCachedBackground(bgUrl) {
    const appDiv = document.getElementById('app');
    if (imageCache.has(bgUrl) && imageCache.get(bgUrl)) { appDiv.style.backgroundImage = `url(${imageCache.get(bgUrl).src})`; }
    else { appDiv.style.backgroundImage = `url(${bgUrl})`; preloadImage(bgUrl).then(img => { if (img) appDiv.style.backgroundImage = `url(${img.src})`; }); }
    appDiv.style.backgroundSize = 'cover'; appDiv.style.backgroundPosition = 'center'; appDiv.style.backgroundAttachment = 'fixed';
}

// ========== 音乐系统 ==========
let bgMusic = null, battleMusic = null, winSound = null, loseSound = null, currentMusic = null, isFightingMusic = false;
function initMusic() {
    bgMusic = new Audio('/static/music/bg01.mp3'); bgMusic.loop = true; bgMusic.volume = 0.7;
    battleMusic = new Audio('/static/music/battle.mp3'); battleMusic.loop = true; battleMusic.volume = 0.7;
    winSound = new Audio('/static/music/fightwin.mp3'); winSound.loop = false; winSound.volume = 0.7;
    loseSound = new Audio('/static/music/fightlose.mp3'); loseSound.loop = false; loseSound.volume = 0.7;
    window.playBgMusic = playBgMusic; window.playBattleMusic = playBattleMusic; window.playWinSound = playWinSound; window.playLoseSound = playLoseSound;
}
function playBgMusic() { if (currentMusic === bgMusic) return; stopAllMusic(); bgMusic.currentTime = 0; bgMusic.play().catch(e=>console.log); currentMusic = bgMusic; isFightingMusic = false; }
function playBattleMusic() { if (currentMusic === battleMusic) return; stopAllMusic(); battleMusic.currentTime = 0; battleMusic.play().catch(e=>console.log); currentMusic = battleMusic; isFightingMusic = true; }
function playWinSound() { if (currentMusic === winSound) return; stopAllMusic(); winSound.currentTime = 0; winSound.play().catch(e=>console.log); currentMusic = winSound; winSound.onended = () => { if (currentMusic === winSound) playBgMusic(); }; }
function playLoseSound() { if (currentMusic === loseSound) return; stopAllMusic(); loseSound.currentTime = 0; loseSound.play().catch(e=>console.log); currentMusic = loseSound; loseSound.onended = () => { if (currentMusic === loseSound) playBgMusic(); }; }
function stopAllMusic() { if (bgMusic) { bgMusic.pause(); bgMusic.currentTime = 0; } if (battleMusic) { battleMusic.pause(); battleMusic.currentTime = 0; } if (winSound) { winSound.pause(); winSound.currentTime = 0; } if (loseSound) { loseSound.pause(); loseSound.currentTime = 0; } currentMusic = null; }

// 弹出音量调节模态框
function showVolumeModal() {
    let currentVol = 70;
    const mainSlider = document.getElementById('volumeSlider');
    if (mainSlider) currentVol = mainSlider.value;
    let modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content" style="width: 260px; text-align: center;">
            <h4 style="color: gold;">🔊 音量调节</h4>
            <input type="range" id="tempVolumeSlider" min="0" max="100" value="${currentVol}" style="width: 100%; margin: 15px 0;">
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button id="volConfirmBtn" style="background: #d99e3e;">确定</button>
                <button onclick="this.closest('.modal').remove()" style="background: #8a5a5a;">取消</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    const tempSlider = document.getElementById('tempVolumeSlider');
    const confirmBtn = document.getElementById('volConfirmBtn');
    confirmBtn.onclick = async () => {
        let newVol = tempSlider.value;
        if (mainSlider) mainSlider.value = newVol;
        let vol = newVol / 100;
        if (bgMusic) bgMusic.volume = vol;
        if (battleMusic) battleMusic.volume = vol;
        if (winSound) winSound.volume = vol;
        if (loseSound) loseSound.volume = vol;
        if (currentUser) {
            await fetch('/set_volume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: currentUser, volume: newVol })
            });
        }
        modal.remove();
    };
}

// ========== 背景切换 ==========
function setBackgroundByTab(tab) {
    let bgUrl = '';
    switch (tab) { case 'map': bgUrl = '/static/images/bg/challenge_jinao.jpg'; break; case 'formation': bgUrl = '/static/images/bg/lianxianzhen.jpg'; break; case 'gems': bgUrl = '/static/images/bg/bagualu.jpg'; break; case 'city': bgUrl = '/static/images/bg/biyougong.jpg'; break; case 'recruit': bgUrl = '/static/images/bg/wanxiandian.jpg'; break; default: bgUrl = ''; }
    if (bgUrl) setCachedBackground(bgUrl);
}
function updateChallengeBackground() {
    let selectedId = document.getElementById('challengeSelect')?.value;
    let bgUrl = '';
    if (selectedId === 'jinao') bgUrl = '/static/images/bg/challenge_jinao.jpg';
    else if (selectedId === 'sanxian') bgUrl = '/static/images/bg/challenge_sanxian.jpg';
    if (bgUrl) setCachedBackground(bgUrl);
}

// ========== 辅助函数 ==========
function addLog(msg, color = null) {
    let logDiv = document.getElementById('logContent');
    let p = document.createElement('p');
    p.innerHTML = msg;
    if (color) { p.style.color = color; p.style.fontWeight = 'bold'; p.style.fontSize = '14px'; p.style.textShadow = '0 0 2px black'; }
    logDiv.appendChild(p); logDiv.scrollTop = logDiv.scrollHeight;
}
function makeDraggable(el) {
    let header = el.querySelector('.log-header') || el;
    let pos1=0,pos2=0,pos3=0,pos4=0;
    header.onmousedown = dragMouseDown;
    function dragMouseDown(e) { e.preventDefault(); pos3=e.clientX; pos4=e.clientY; document.onmouseup=closeDrag; document.onmousemove=elementDrag; }
    function elementDrag(e) { e.preventDefault(); pos1=pos3-e.clientX; pos2=pos4-e.clientY; pos3=e.clientX; pos4=e.clientY; el.style.top=(el.offsetTop-pos2)+"px"; el.style.left=(el.offsetLeft-pos1)+"px"; el.style.bottom="auto"; el.style.right="auto"; }
    function closeDrag() { document.onmouseup=null; document.onmousemove=null; }
}
function closeModal(btn) { let modal = btn.closest('.modal'); if (modal) modal.remove(); }
// ========== 英雄ID映射 ==========
async function loadHeroIdMap() { let r = await fetch(`/my_heroes?username=${currentUser}`); let d = await r.json(); if (d.heroes) { for (let h of d.heroes) heroIdMap[h.name] = h.id; } }

// ========== 祝福倒计时 ==========
let blessingTimerInterval = null;
async function updateBlessingTimer() {
    if (!currentUser) return;
    try {
        const res = await fetch(`/pray/status?username=${currentUser}`);
        const data = await res.json();
        const timerSpan = document.getElementById('recruitBlessingTimer');
        if (timerSpan) {
            if (data.success && data.hasBuff && data.remain_seconds > 0) {
                const minutes = Math.floor(data.remain_seconds / 60);
                const seconds = data.remain_seconds % 60;
                timerSpan.innerText = `⏳ 祝福剩余 ${minutes}:${seconds.toString().padStart(2,'0')}`;
                timerSpan.style.display = 'inline-block';
            } else { timerSpan.innerText = `✨ 无祝福状态`; timerSpan.style.display = 'inline-block'; }
        }
    } catch(e) { console.warn(e); }
}
function startBlessingTimer() { if (blessingTimerInterval) clearInterval(blessingTimerInterval); blessingTimerInterval = setInterval(() => updateBlessingTimer(), 1000); updateBlessingTimer(); }

// ========== 天骄榜 ==========
async function showPowerRank() {
    let resp = await fetch(`/rank/power?username=${currentUser}`);
    let data = await resp.json();
    if (data.success) {
        let rankHtml = '<table class="rank-table"><tr><th>排名</th><th>玩家</th><th>战力</th></tr>';
        data.rank.forEach((item, idx) => { rankHtml += `<tr><td>${idx+1}</td><td>${item.username}</td><td>${item.power}</tr></tr>`; });
        rankHtml += '</table>';
        document.getElementById('rankList').innerHTML = rankHtml;
        document.getElementById('myRankInfo').innerHTML = `我的战力: ${data.my_power || 0} &nbsp; 排名: ${data.my_rank || '未上榜'}`;
        document.getElementById('powerRankModal').style.display = 'flex';
    } else alert("加载排行榜失败");
}
function closePowerRank() { document.getElementById('powerRankModal').style.display = 'none'; }

// ========== 好友申请日志带按钮 ==========
function addFriendRequestLog(fromUser, msg) {
    let logDiv = document.getElementById('logContent');
    let p = document.createElement('p');
    p.style.borderBottom = '1px solid #555'; p.style.padding = '5px'; p.style.margin = '5px 0'; p.style.backgroundColor = 'rgba(0,0,0,0.3)';
    p.innerHTML = `${msg} <button onclick="acceptFriendRequest('${fromUser}')" style="background:#5a8a5a; margin-left:10px; padding:2px 8px;">✅ 同意</button> <button onclick="rejectFriendRequest('${fromUser}')" style="background:#8a5a5a; margin-left:5px; padding:2px 8px;">❌ 拒绝</button>`;
    logDiv.appendChild(p); logDiv.scrollTop = logDiv.scrollHeight;
}
async function acceptFriendRequest(fromUser) {
    let resp = await fetch('/api/friend/accept', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, from: fromUser }) });
    let data = await resp.json();
    if (data.success) { addLog(`✅ 已添加 ${fromUser} 为好友`); loadFriendList(); if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ act: "friend_list_update", target: fromUser })); } else alert(data.msg);
}
async function rejectFriendRequest(fromUser) {
    let resp = await fetch('/api/friend/reject', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, from: fromUser }) });
    let data = await resp.json();
    if (data.success) addLog(`❌ 已拒绝 ${fromUser} 的好友申请`); else alert(data.msg);
}

// ========== 登录/注册 ==========
async function checkAuth() {
    let saved = localStorage.getItem('jijiao_user');
    if (saved) { let data = JSON.parse(saved); await doAuth('login', data.username, data.password); }
    else document.getElementById('authModal').style.display = 'flex';
}
async function doAuth(mode, username, password, email = '') {
    if (mode === 'register' && username.length > 5) { alert("用户名不能超过5个汉字或字符"); return; }
    let url = mode === 'login' ? '/login' : '/register';
    let body = mode === 'login' ? {username, password} : {username, password, email};
    let resp = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    let data = await resp.json();
    if (data.success) {
        if (mode === 'login') localStorage.setItem('jijiao_user', JSON.stringify({ username, password }));
        else alert(`注册成功！${data.gift_hero ? `赠送武将：${data.gift_hero}` : ''}`);
        currentUser = username;
        document.getElementById('authModal').style.display = 'none';
        document.getElementById('userName').innerText = currentUser;
        await loadUserResources(); await loadUserAvatar(); await setSelfInfo();
        await loadHeroIdMap();
        connectWebSocket();
        loadChallengeList(); loadFormation(); loadCityInfo(); loadFriendList(); loadBlacklist(); checkSelfOccupied();
        await loadPendingRequests();
        initMusic();
        let volResp = await fetch(`/user_info?username=${currentUser}`);
        let volData = await volResp.json();
        if (volData.success && volData.volume !== undefined) {
            let mainSlider = document.getElementById('volumeSlider');
            if (mainSlider) mainSlider.value = volData.volume;
            let vol = volData.volume / 100;
            if (bgMusic) bgMusic.volume = vol; if (battleMusic) battleMusic.volume = vol; if (winSound) winSound.volume = vol; if (loseSound) loseSound.volume = vol;
        }
        playBgMusic();
        startBlessingTimer();
        startPreload().catch(console.warn);
    } else alert(data.msg);
}
document.getElementById('authSubmitBtn').onclick = () => {
    let u = document.getElementById('authUsername').value, p = document.getElementById('authPassword').value;
    if (!u || !p) { alert("用户名/密码不能为空"); return; }
    if (!isLoginMode) { let e = document.getElementById('authEmail').value; if (!e) { alert("邮箱不能为空"); return; } doAuth('register', u, p, e); }
    else doAuth('login', u, p);
};
document.getElementById('switchAuthBtn').onclick = () => { isLoginMode = !isLoginMode; document.getElementById('authTitle').innerText = isLoginMode ? '登录' : '注册'; document.getElementById('authEmailGroup').style.display = isLoginMode ? 'none' : 'block'; document.getElementById('authSubmitBtn').innerText = isLoginMode ? '登录' : '注册'; document.getElementById('switchAuthBtn').innerText = isLoginMode ? '没有账号？去注册' : '已有账号？去登录'; };

async function loadUserResources() { let r = await fetch(`/user_resources?username=${currentUser}`); let d = await r.json(); if (d.success) { document.getElementById('userGold').innerText = d.gold; document.getElementById('userIngots').innerText = d.ingots; } }
async function loadUserAvatar() { let r = await fetch(`/user_info?username=${currentUser}`); let d = await r.json(); if (d.success && d.avatar) document.getElementById('userAvatar').src = `/static/images/avatars/${d.avatar}`; else document.getElementById('userAvatar').src = '/static/images/avatars/hero.png'; }

// ========== WebSocket ==========
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    ws = new WebSocket(`${protocol}${location.host}/ws`);
    ws.onopen = () => { console.log("WebSocket 已连接"); ws.send(JSON.stringify({ act: "login", uid: currentUser })); };
    ws.onerror = (err) => { console.error("WebSocket 错误", err); addLog("❌ 聊天服务器连接失败，5秒后重试", "red"); setTimeout(connectWebSocket, 30000); };
    ws.onclose = () => { console.log("WebSocket 关闭，尝试重连..."); setTimeout(connectWebSocket, 30000); };
    ws.onmessage = (e) => {
        let data = JSON.parse(e.data);
        if (data.type === "login_ok") console.log("登录成功");
        else if (data.type === "chat_msg") addLog(data.text);
        else if (data.type === "friend_request") addFriendRequestLog(data.from, data.msg || `📨 ${data.from} 请求添加你为好友`);
        else if (data.type === "friend_list_update") loadFriendList();
        else if (data.type === "battle_result") {
            document.getElementById('leftPower').innerText = data.left_power || 0; document.getElementById('rightPower').innerText = data.right_power || 0;
            if (window.skipRequested) { if (typeof applyFinalHp === 'function') applyFinalHp(data.log, data.winner); if (typeof hideBattlePanel === 'function') hideBattlePanel(); window.isFighting = false; window.skipRequested = false; }
            else { if (typeof showBattlePanel === 'function') showBattlePanel(data.left_team, data.right_team, data.log, data.winner, data.left_power, data.right_power, () => { }); }
        } else if (data.type === "escape_result") { addLog("🏃 你逃跑了，战斗结束"); window.isFighting = false; if (typeof hideBattlePanel === 'function') hideBattlePanel(); }
        else if (data.type === "gm_broadcast") addLog(data.text, 'red');
        else if (data.type === "muted") { addLog(data.text, 'orange'); alert(data.text); }
        else if (data.type === "unmuted") addLog(data.text, 'green');
        else if (data.type === "kicked") { addLog(data.text, 'red'); alert(data.text); if (ws) ws.close(); setTimeout(() => { window.location.href = '/'; }, 2000); }
    };
}
function sendChatMessage() {
    let msg = document.getElementById('chatInput').value.trim();
    if (!msg) return;
    addLog(`💬 ${currentUser}: ${msg}`);
    if (ws && ws.readyState === WebSocket.OPEN) { ws.send(JSON.stringify({ act: "chat", msg })); document.getElementById('chatInput').value = ''; }
    else addLog("❌ 未连接到聊天服务器");
}
document.getElementById('sendChatBtn').onclick = sendChatMessage;
document.getElementById('chatInput').onkeypress = e => { if (e.key === 'Enter') sendChatMessage(); };

// ========== 标签页 ==========
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active')); btn.classList.add('active');
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active')); document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
            setBackgroundByTab(btn.dataset.tab);
            if (btn.dataset.tab === 'formation') loadFormation();
            if (btn.dataset.tab === 'gems') { loadGems(); renderGemShop(); }
            if (btn.dataset.tab === 'city') { loadCityInfo(); loadDailyTasks(); }
            if (btn.dataset.tab === 'map') { loadChallengeList(); updateChallengeBackground(); }
        };
    });
    document.getElementById('formationType').onchange = async () => {
        let newType = document.getElementById('formationType').value;
        let typeName = document.getElementById('formationType').options[document.getElementById('formationType').selectedIndex].text;
        addLog(`✨ 切换阵法：${typeName}`);
        currentFormationType = newType;
        let r = await fetch(`/get_formation?username=${currentUser}&formation_type=${newType}`);
        let d = await r.json();
        myFormation = d.formation || [];
        renderFormationGrid();
        await fetch('/save_formation_type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, formation_type: newType }) });
    };
}

// ========== 副本模块 ==========
async function loadChallengeList() {
    let r = await fetch('/challenge/list'); let d = await r.json();
    if (d.success) {
        let s = document.getElementById('challengeSelect'); s.innerHTML = '';
        for (let c of d.challenges) { let o = document.createElement('option'); o.value = c.id; o.textContent = `${c.name} (推荐Lv.${c.min_level})`; s.appendChild(o); }
        if (d.challenges.length) { currentChallengeId = d.challenges[0].id; s.value = currentChallengeId; loadChallengeNodes(currentChallengeId); updateChallengeBackground(); }
        s.onchange = () => { currentChallengeId = s.value; loadChallengeNodes(currentChallengeId); updateChallengeBackground(); };
    } else document.getElementById('nodeChain').innerHTML = '<p>副本加载失败</p>';
}
async function loadChallengeNodes(challengeId) {
    let r = await fetch(`/challenge/nodes?challenge_id=${challengeId}`); let d = await r.json();
    if (!d.success) { document.getElementById('nodeChain').innerHTML = '<p>副本节点加载失败</p>'; return; }
    let nodes = d.nodes; let container = document.getElementById('nodeChain'); container.innerHTML = '';
    for (let i = 0; i < nodes.length; i++) {
        let n = nodes[i]; let heroAvatars = '';
        for (let hid of (n.main_hero_ids || [])) heroAvatars += `<img src="/static/images/heroes/${hid}.png" onerror="this.src='/static/images/heroes/hero.png'" style="width:40px; height:40px; border-radius:50%; margin:2px; border:1px solid gold;">`;
        let div = document.createElement('div'); div.className = 'node-card'; div.onclick = () => challengeNode(n.node_id);
        div.innerHTML = `<div style="display:flex; justify-content:center; margin-bottom:8px;">${heroAvatars || '<span style="font-size:12px;">无主将</span>'}</div><div class="node-name">第${n.node_id}关</div><div class="node-power">战力: ${n.power}</div><div class="node-reward">💰${n.gold} ⭐${n.exp}</div>`;
        container.appendChild(div);
        if (i < nodes.length - 1) { let arr = document.createElement('div'); arr.className = 'connector'; arr.innerText = '→'; container.appendChild(arr); }
    }
}
async function challengeNode(nodeId) {
    let r = await fetch('/challenge/challenge', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, challenge_id: currentChallengeId, node_id: nodeId }) });
    let d = await r.json();
    if (d.success) {
        if (typeof showBattlePanel === 'function') showBattlePanel(d.left_team, d.right_team, d.log, d.winner, d.left_power, d.right_power, async (winner) => { addLog(`🎉 挑战成功！获得经验${d.exp}，金币${d.gold}${d.gem ? '，获得宝石：' + d.gem.name : ''}`); await loadUserResources(); loadDailyTasks(); });
    } else { addLog(`❌ 挑战失败：${d.msg}`); if (d.left_team && d.right_team && typeof showBattlePanel === 'function') showBattlePanel(d.left_team, d.right_team, d.log, d.winner, d.left_power, d.right_power, () => { }); }
}

// ========== 演武场 ==========
async function loadFormation() { let r = await fetch(`/get_formation?username=${currentUser}`); let d = await r.json(); myFormation = d.formation || []; renderFormationGrid(); }
function renderFormationGrid() {
    let slotsMap = { normal: [0,1,2,3,4], attack: [0,2,4,6,8], intelligence: [1,3,5,7,8], defense: [1,2,5,7,8], speed: [0,1,3,4,6] };
    let availableSlots = slotsMap[currentFormationType] || slotsMap.normal;
    let container = document.getElementById('formationGrid'); container.innerHTML = '';
    for (let i = 0; i < 9; i++) {
        let isAvailable = availableSlots.includes(i);
        let hero = myFormation.find(f => f.position === i);
        let slotDiv = document.createElement('div'); slotDiv.className = 'formation-slot';
        if (!isAvailable) { slotDiv.classList.add('disabled-slot'); slotDiv.innerHTML = '<div class="empty-slot">🔒</div>'; }
        else if (hero) { let heroId = heroIdMap[hero.name] || hero.name; slotDiv.innerHTML = `<div class="formation-hero"><img src="/static/images/heroes/${heroId}.png" onerror="this.src='/static/images/heroes/hero.png'"><div class="formation-hero-name">${hero.name}</div></div>`; slotDiv.onclick = () => removeFromFormation(i); }
        else { slotDiv.innerHTML = '<div class="empty-slot">⚡</div>'; slotDiv.onclick = () => selectHeroForSlot(i); }
        container.appendChild(slotDiv);
    }
}
async function selectHeroForSlot(realPosition) {
    let slotsMap = { normal: [0,1,2,3,4], attack: [0,2,4,6,8], intelligence: [1,3,5,7,8], defense: [1,2,5,7,8], speed: [0,1,3,4,6] };
    let activeSlots = slotsMap[currentFormationType] || slotsMap.normal;
    if (!activeSlots.includes(realPosition)) { addLog("❌ 该位置不可用，请选择激活的格子"); return; }
    let r = await fetch(`/my_heroes?username=${currentUser}`); let d = await r.json(); let heroes = d.heroes; heroes.sort((a,b)=>b.level - a.level);
    let modal = document.createElement('div'); modal.className = 'modal';
    modal.innerHTML = `<div class="modal-content"><h3>选择武将</h3><div class="gem-grid" id="heroSelectList">${heroes.map(h => `<div class="hero-card" data-name="${h.name}" data-id="${h.id}"><img src="/static/images/heroes/${h.id}.png" onerror="this.src='/static/images/heroes/hero.png'"><div>${h.name}</div><div>Lv.${h.level} ★${h.star}</div></div>`).join('')}</div><button onclick="this.parentElement.parentElement.remove()">取消</button></div>`;
    document.body.appendChild(modal);
    document.querySelectorAll('#heroSelectList .hero-card').forEach(card => { card.onclick = () => { let heroName = card.dataset.name; let existingIndex = myFormation.findIndex(f => f.name === heroName); if (existingIndex !== -1) myFormation.splice(existingIndex, 1); myFormation.push({ name: heroName, position: realPosition }); saveFormation(); modal.remove(); }; });
}
function removeFromFormation(realPosition) { let index = myFormation.findIndex(f => f.position === realPosition); if (index !== -1) { myFormation.splice(index, 1); saveFormation(); } }
async function saveFormation() { let r = await fetch('/save_formation', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, formation: myFormation, formation_type: currentFormationType }) }); let d = await r.json(); if (d.success) { renderFormationGrid(); addLog("💾 阵容已保存"); } else alert(d.msg); }
async function saveFormationWithType() { currentFormationType = document.getElementById('formationType').value; addLog(`✨ 应用阵法：${document.getElementById('formationType').options[document.getElementById('formationType').selectedIndex].text}`); await saveFormation(); }
function clearCurrentFormation() { if (confirm("确定清空当前阵法下的所有站位吗？此操作不会影响其他阵法，但会清除当前已放置的武将。")) { myFormation = []; saveFormation(); addLog("🗑️ 已清空当前阵法的所有武将"); } }

// ========== 宝石商店 ==========
const shopGems = [{ type: 'strength', name: '力量宝石', icon: 'strength.png' }, { type: 'intelligence', name: '智力宝石', icon: 'intelligence.png' }, { type: 'speed', name: '敏捷宝石', icon: 'speed.png' }, { type: 'hp', name: '生命宝石', icon: 'hp.png' }];
function renderGemShop() {
    let container = document.getElementById('gemShopContainer'); if (!container) return;
    let html = '';
    for (let gem of shopGems) {
        html += `<div class="gem-card" style="width: 150px;"><img src="/static/images/gems/${gem.icon}" onerror="this.src='/static/images/gems/gem.png'" style="width: 50px;"><div class="gem-name">${gem.name}</div><div>★1星 +随机1-2</div><div>价格: 1 💎/个</div><div class="shop-qty-control"><button class="shop-qty-down" data-type="${gem.type}">-</button><span id="shop_qty_${gem.type}" style="min-width: 30px;">1</span><button class="shop-qty-up" data-type="${gem.type}">+</button></div><button class="shop-buy-btn" data-type="${gem.type}" style="background: #d99e3e; width: 100%;">购买</button></div>`;
    }
    container.innerHTML = html;
    document.querySelectorAll('.shop-qty-up').forEach(btn => { btn.onclick = (e) => { let type = btn.dataset.type; let span = document.getElementById(`shop_qty_${type}`); let val = parseInt(span.innerText) || 1; if (val < 99) span.innerText = val + 1; }; });
    document.querySelectorAll('.shop-qty-down').forEach(btn => { btn.onclick = (e) => { let type = btn.dataset.type; let span = document.getElementById(`shop_qty_${type}`); let val = parseInt(span.innerText) || 1; if (val > 1) span.innerText = val - 1; }; });
    document.querySelectorAll('.shop-buy-btn').forEach(btn => { btn.onclick = async () => { let type = btn.dataset.type; let qtySpan = document.getElementById(`shop_qty_${type}`); let quantity = parseInt(qtySpan.innerText) || 1; let resp = await fetch('/shop/buy_gem', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, gem_type: type, quantity: quantity }) }); let data = await resp.json(); if (data.success) { addLog(`✅ 购买成功，获得 ${quantity} 颗${type}宝石`); await loadUserResources(); await loadGems(); await loadDailyTasks(); } else alert(data.msg); }; });
}

// ========== 宝石系统 ==========
async function loadGems() {
    renderGemShop();
    let r = await fetch(`/user_items?username=${currentUser}`); let d = await r.json(); let items = d.items || [];
    let bagDiv = document.getElementById('gemBag'); bagDiv.innerHTML = '';
    items.forEach(g => {
        let iconFile = 'gem.png'; let nameText = g.name || '宝石'; let detailText = '';
        if (g.id === 'exp_potion' || g.name === '经验药水' || (g.id && g.id.includes('exp_potion'))) { iconFile = '/static/images/items/exp_potion.png'; nameText = '经验药水'; detailText = `经验+${g.value || 200}`; }
        else if (g.double_attr) { iconFile = 'double.png'; detailText = `双属性 +${g.value}/${g.double_attr.value}`; }
        else { const attrMap = { strength: '力量', intelligence: '智力', speed: '敏捷', hp: '生命' }; const attrCn = attrMap[g.attr] || g.attr; nameText = `${attrCn}宝石`; detailText = `★${g.star} +${g.value}`; const iconMap = { strength: 'strength.png', intelligence: 'intelligence.png', speed: 'speed.png', hp: 'hp.png' }; iconFile = iconMap[g.attr] || 'gem.png'; }
        let div = document.createElement('div'); div.className = 'gem-card';
        div.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center;"><img src="/static/images/gems/${iconFile}" onerror="this.src='/static/images/gems/gem.png'" style="width:40px; height:40px; object-fit:contain;"><strong style="font-size:12px;">${nameText}</strong><span style="font-size:11px;">${detailText}</span><span style="font-size:10px;">数量: ${g.count}</span><button class="discard-gem-btn" data-id="${g.id}" style="margin-top:4px; padding:2px 8px; font-size:11px; background:#8a5a5a;">🗑️ 丢弃</button></div>`;
        bagDiv.appendChild(div);
    });
    document.querySelectorAll('.discard-gem-btn').forEach(btn => { btn.onclick = async (e) => { e.stopPropagation(); let gemId = btn.dataset.id; if (confirm("确定要丢弃一颗该宝石吗？")) { let resp = await fetch('/discard_gem', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, gem_id: gemId }) }); let data = await resp.json(); if (data.success) { addLog(`🗑️ 已丢弃一颗${btn.parentElement.querySelector('strong')?.innerText || '宝石'}`); await loadGems(); } else alert(data.msg); } }; });
    let fusionDiv = document.getElementById('fusionSelect');
    fusionDiv.innerHTML = `<div><select id="gem1"><option value="">选择宝石1</option></select></div><div><select id="gem2"><option value="">选择宝石2</option></select></div><button id="doFuseBtn">融合</button>`;
    let gem1Select = document.getElementById('gem1'), gem2Select = document.getElementById('gem2');
    let normalGems = items.filter(g => !g.double_attr && !(g.id === 'exp_potion' || g.name === '经验药水'));
    function fillGemSelect(selectElement) { selectElement.innerHTML = '<option value="">选择宝石</option>'; normalGems.forEach(g => { let attrName = g.attr === 'strength' ? '力量宝石' : (g.attr === 'intelligence' ? '智力宝石' : (g.attr === 'speed' ? '敏捷宝石' : '生命宝石')); selectElement.innerHTML += `<option value="${g.id}" data-star="${g.star}" data-attr="${g.attr}">${attrName} ★${g.star} +${g.value} (x${g.count})</option>`; }); }
    fillGemSelect(gem1Select); fillGemSelect(gem2Select);
    function updateFusionHint() {
        let val1 = gem1Select.value, val2 = gem2Select.value; let hintDiv = document.getElementById('fusionRuleHint');
        if (!val1 || !val2) { hintDiv.innerHTML = '请选择两颗宝石'; hintDiv.style.color = '#aaa'; return; }
        if (val1 === val2) { let opt1 = gem1Select.options[gem1Select.selectedIndex]; let countMatch = opt1.text.match(/x(\\d+)/); let count = countMatch ? parseInt(countMatch[1]) : 1; if (count < 2) { hintDiv.innerHTML = '❌ 该宝石数量不足2，无法融合'; hintDiv.style.color = '#ff6666'; return; } }
        let opt1 = gem1Select.options[gem1Select.selectedIndex], opt2 = gem2Select.options[gem2Select.selectedIndex];
        let star1 = parseInt(opt1.dataset.star), star2 = parseInt(opt2.dataset.star), attr1 = opt1.dataset.attr, attr2 = opt2.dataset.attr;
        if (star1 !== star2) { hintDiv.innerHTML = '❌ 星级不同，无法融合'; hintDiv.style.color = '#ff6666'; return; }
        if (star1 > 4) { hintDiv.innerHTML = '❌ 5星及以上宝石无法融合'; hintDiv.style.color = '#ff6666'; return; }
        if (attr1 === attr2) { let rates = {1:90,2:70,3:60,4:40}; let rate = rates[star1]; hintDiv.innerHTML = `✅ 同属性融合：${star1}星+${star1}星 → ${star1+1}星（成功率${rate}%）`; hintDiv.style.color = '#aaffaa'; }
        else { hintDiv.innerHTML = `⚠️ 不同属性融合：${star1}星+${star1}星 → ${Math.max(1, star1-1)}星双属性（成功率50%）`; hintDiv.style.color = '#ffaa66'; }
    }
    gem1Select.onchange = updateFusionHint; gem2Select.onchange = updateFusionHint;
    document.getElementById('doFuseBtn').onclick = async () => {
        let gemId1 = gem1Select.value, gemId2 = gem2Select.value; if (!gemId1 || !gemId2) { alert("请选择两颗宝石"); return; }
        if (gemId1 === gemId2) { let opt1 = gem1Select.options[gem1Select.selectedIndex]; let countMatch = opt1.text.match(/x(\\d+)/); let count = countMatch ? parseInt(countMatch[1]) : 1; if (count < 2) { alert("该宝石数量不足2，无法使用同一宝石融合"); return; } }
        let resp = await fetch('/fuse_gems', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, gem_id1: gemId1, gem_id2: gemId2 }) }); let data = await resp.json();
        if (data.success) { addLog(`✨ ${data.msg}`); await loadGems(); await loadUserResources(); } else alert(data.msg);
    };
    let decomposeSelect = document.getElementById('decomposeSelect'); decomposeSelect.innerHTML = '<option value="">请选择</option>';
    items.filter(g => g.double_attr).forEach(g => { decomposeSelect.innerHTML += `<option value="${g.id}">${g.name} 双属性 (x${g.count})</option>`; });
}
async function decomposeGem() { let gemId = document.getElementById('decomposeSelect').value; if (!gemId) { alert("请选择宝石"); return; } let r = await fetch('/decompose_gem', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, gem_id: gemId }) }); let d = await r.json(); if (d.success) { addLog(`✨ 分解成功，获得两颗2星宝石`); await loadGems(); } else alert(d.msg); }

// ========== 武将系统 ==========
async function openMyHeroes() { if (!currentUser) { alert("请先登录"); return; } let r = await fetch(`/my_heroes?username=${currentUser}`); let d = await r.json(); let cont = document.getElementById('myHeroesList'); if (!cont) { console.error("myHeroesList 元素不存在"); return; } cont.innerHTML = ''; for (let h of d.heroes) { let skillName = '未知技能'; try { let detailResp = await fetch(`/hero_detail?username=${currentUser}&hero=${h.name}`); let detail = await detailResp.json(); if (detail.success && detail.skill_name) skillName = detail.skill_name; } catch(e) { console.warn(e); } let div = document.createElement('div'); div.className = 'hero-card'; div.innerHTML = `<img src="/static/images/heroes/${h.id}.png" onerror="this.src='/static/images/heroes/hero.png'"><div><strong>${h.name}</strong></div><div>Lv.${h.level} ★${h.star}</div><div style="font-size: 11px; color: #ffaa66;">✨ ${skillName}</div><div><button onclick="showHeroDetail('${h.name}')">详情</button><button onclick="dismissHero('${h.name}')">遣散</button></div>`; cont.appendChild(div); } let modal = document.getElementById('myHeroesModal'); if (modal) modal.style.display = 'flex'; }
async function showHeroDetail(heroName) {
    let r = await fetch(`/hero_detail?username=${currentUser}&hero=${heroName}`); let d = await r.json(); if (!d.success) { alert("无法获取详情"); return; }
    let html = `<div style="text-align:center;"><img src="/static/images/heroes/${d.id}.png" onerror="this.src='/static/images/heroes/hero.png'" style="width:120px;"><h3>${d.name} ★${d.star} Lv.${d.level}</h3><p>经验: ${d.exp}</p><p>自由属性点: ${d.free_points}</p><p>战力: ${d.power}</p><p><strong>技能：</strong><span title="${d.skill_desc || '无'}">${d.skill_name || '无'}</span></p><div class="attr-row"><span>❤️ 生命: ${d.final_attrs.hp}</span><button onclick="allocatePoint('${heroName}','hp')" ${d.free_points <= 0 ? 'disabled' : ''}>+</button></div><div class="attr-row"><span>⚔️ 力量: ${d.final_attrs.strength}</span><button onclick="allocatePoint('${heroName}','strength')" ${d.free_points <= 0 ? 'disabled' : ''}>+</button></div><div class="attr-row"><span>🔮 智力: ${d.final_attrs.intelligence}</span><button onclick="allocatePoint('${heroName}','intelligence')" ${d.free_points <= 0 ? 'disabled' : ''}>+</button></div><div class="attr-row"><span>🏃 敏捷: ${d.final_attrs.speed}</span><button onclick="allocatePoint('${heroName}','speed')" ${d.free_points <= 0 ? 'disabled' : ''}>+</button></div><hr><div>经验药水: <input type="number" id="potionAmount" min="1" value="1" style="width:60px;"><button onclick="useExpPotion('${heroName}')">使用</button></div><h4>宝石镶嵌</h4><div id="gemSlots" style="display:flex; flex-wrap:wrap;"></div><button onclick="dismissHero('${heroName}')" style="margin-top:10px;">遣散</button></div>`;
    let modal = document.getElementById('heroDetailModal'); document.getElementById('heroDetailContent').innerHTML = html; modal.style.display = 'flex';
    let gemSlots = document.getElementById('gemSlots'); gemSlots.innerHTML = '';
    for (let i = 0; i < 5; i++) {
        let gem = d.gems[i]; let slotDiv = document.createElement('div'); slotDiv.className = 'gem-slot';
        if (gem) { let gemAttrName = gem.attr === 'strength' ? '⚔️力量' : (gem.attr === 'intelligence' ? '🔮智力' : (gem.attr === 'speed' ? '🏃敏捷' : '❤️生命')); slotDiv.innerHTML = `<div><img src="/static/images/gems/${gem.attr || 'gem'}.png" onerror="this.style.display='none'" style="width:40px;"><div style="font-size:10px;">${gemAttrName}+${gem.value}</div><button class="unequip-gem-btn" data-slot="${i}" style="font-size:10px; padding:2px 4px;">💎 卸下</button></div>`; }
        else { slotDiv.innerHTML = `<div><div style="width:40px; height:40px; background:#2c3e2f; border-radius:8px; margin:0 auto;"></div><div style="font-size:10px;">空</div><button class="equip-gem-btn" data-slot="${i}" style="font-size:10px; padding:2px 6px;">🔧 镶嵌</button></div>`; }
        gemSlots.appendChild(slotDiv);
    }
    document.querySelectorAll('.equip-gem-btn').forEach(btn => { btn.onclick = (e) => { e.stopPropagation(); let slot = parseInt(btn.dataset.slot); selectGemForSlot(heroName, slot); }; });
    document.querySelectorAll('.unequip-gem-btn').forEach(btn => { btn.onclick = (e) => { e.stopPropagation(); let slot = parseInt(btn.dataset.slot); unequipGem(heroName, slot); }; });
}
async function unequipGem(heroName, slot) { if (!confirm("卸下宝石需要消耗500金币，确定吗？")) return; let r = await fetch('/unequip_gem', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, hero_name: heroName, slot: slot }) }); let d = await r.json(); if (d.success) { addLog("💎 卸下宝石，消耗500金币"); showHeroDetail(heroName); loadUserResources(); loadGems(); } else alert(d.msg); }
async function useExpPotion(heroName) { let amt = parseInt(document.getElementById('potionAmount').value) || 1; let r = await fetch('/use_exp_potion', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, hero_name: heroName, amount: amt }) }); let d = await r.json(); if (d.success) { addLog(d.msg); showHeroDetail(heroName); } else alert(d.msg); }
async function allocatePoint(heroName, attr) { let r = await fetch('/allocate_point', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, hero_name: heroName, attr: attr }) }); let d = await r.json(); if (d.success) { addLog(`✨ ${heroName} 的${attr} +1`); showHeroDetail(heroName); } else alert(d.msg); }
async function dismissHero(heroName) { if (!confirm(`确定遣散 ${heroName} 吗？`)) return; let r = await fetch('/dismiss_hero', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, hero_name: heroName }) }); let d = await r.json(); if (d.success) { addLog(`🗑️ 遣散成功，获得 ${d.refund_exp} 经验药水`); closeMyHeroes(); openMyHeroes(); loadFormation(); } else alert(d.msg); }
async function selectGemForSlot(heroName, slot) {
    let r = await fetch(`/user_items?username=${currentUser}`); let d = await r.json(); let gems = d.items || [];
    if (gems.length === 0) { alert("背包无宝石"); return; }
    let modal = document.createElement('div'); modal.className = 'modal';
    let gemsHtml = '<div id="gemSelectList" class="gem-grid" style="max-height:400px; overflow-y:auto;">';
    for (let g of gems) {
        let iconFile = 'gem.png';
        if (g.double_attr) iconFile = 'double.png';
        else { if (g.attr === 'strength') iconFile = 'strength.png'; else if (g.attr === 'intelligence') iconFile = 'intelligence.png'; else if (g.attr === 'speed') iconFile = 'speed.png'; else if (g.attr === 'hp') iconFile = 'hp.png'; }
        let nameText = g.double_attr ? `${g.name}+${g.double_attr.attr}` : g.name;
        gemsHtml += `<div class="gem-card" data-id="${g.id}" style="cursor:pointer;"><div style="display:flex; flex-direction:column; align-items:center;"><img src="/static/images/gems/${iconFile}" style="width:48px; height:48px; object-fit:contain;" onerror="this.style.display='none'"><strong style="font-size:12px;">${nameText}</strong><span style="font-size:11px;">★${g.star} +${g.value}</span><span style="font-size:10px;">数量: ${g.count}</span></div></div>`;
    }
    gemsHtml += '</div>';
    modal.innerHTML = `<div class="modal-content"><h3>选择宝石镶嵌到 ${heroName} 的槽位 ${slot+1}</h3>${gemsHtml}<button onclick="this.parentElement.parentElement.remove()" style="margin-top:15px;">取消</button></div>`;
    document.body.appendChild(modal);
    document.querySelectorAll('#gemSelectList .gem-card').forEach(card => { card.onclick = async () => { let gemId = card.dataset.id; let eq = await fetch('/equip_gem', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, hero_name: heroName, gem_id: gemId, slot: slot }) }); let eqd = await eq.json(); if (eqd.success) { addLog(`💎 为 ${heroName} 镶嵌了宝石`); modal.remove(); showHeroDetail(heroName); loadGems(); } else alert(eqd.msg); }; });
}
function closeHeroDetail() { document.getElementById('heroDetailModal').style.display = 'none'; }
function closeMyHeroes() { let modal = document.getElementById('myHeroesModal'); if (modal) modal.style.display = 'none'; }

// ========== 每日任务 ==========
async function loadDailyTasks() {
    let resp = await fetch(`/daily_tasks?username=${currentUser}`); let data = await resp.json();
    if (!data.success) { document.getElementById('dailyTasksPanel').innerHTML = '<p>任务加载失败</p>'; return; }
    let tasks = data.tasks;
    const taskNames = { login:'每日登录', self_pvp:'自我切磋', friend_pvp:'好友切磋', challenge:'副本挑战', shop:'八卦炉商店购物' };
    const taskReward = { login:'100金币', self_pvp:'200金币', friend_pvp:'1钻石', challenge:'5钻石', shop:'10钻石' };
    let html = '';
    for (let [id, info] of Object.entries(tasks)) {
        let status = ''; if (info.claimed) status = '✅ 已领取'; else if (info.completed) status = '✔️ 可领取'; else status = `⏳ ${info.current}/${info.need}`;
        let btnDisabled = (!info.completed || info.claimed);
        html += `<div class="task-item"><div style="display: flex; justify-content: space-between; align-items: center;"><div><strong>${taskNames[id]}</strong><br><span class="task-progress">🎁 ${taskReward[id]}</span></div><div style="text-align: right;"><div>${status}</div><button class="claim-task-btn" data-task="${id}" ${btnDisabled ? 'disabled' : ''}>领取</button></div></div></div>`;
    }
    document.getElementById('dailyTasksPanel').innerHTML = html;
    document.querySelectorAll('.claim-task-btn').forEach(btn => { btn.onclick = async () => { let taskId = btn.dataset.task; let resp = await fetch('/claim_task', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, task_id: taskId }) }); let data = await resp.json(); if (data.success) { addLog(`✨ ${data.msg}`); await loadDailyTasks(); await loadUserResources(); } else alert(data.msg); }; });
}

// ========== 碧游宫 ==========
async function loadCityInfo() {
    let r = await fetch(`/user_info?username=${currentUser}`); let d = await r.json(); if (d.success) { document.getElementById('playerLevel').innerText = d.level; document.getElementById('playerExp').innerText = d.exp; }
    let occ = await fetch(`/get_occupier?username=${currentUser}`); let occd = await occ.json();
    if (occd.occupier) { let occUser = await fetch(`/user_info?username=${occd.occupier}`); let occUserData = await occUser.json(); document.getElementById('occupierName').innerHTML = `<strong>${occd.occupier}</strong> (占领者)`; document.getElementById('occupierAvatar').src = `/static/images/avatars/${occUserData.avatar || 'hero.png'}`; document.getElementById('selfReleaseBtn').style.display = 'inline-block'; }
    else { document.getElementById('occupierName').innerHTML = '未被占领'; document.getElementById('occupierAvatar').src = `/static/images/avatars/${d.avatar || 'hero.png'}`; document.getElementById('selfReleaseBtn').style.display = 'none'; }
    loadBranchList(); loadDailyTasks();
}
async function selfRelease() { let r = await fetch('/self_release', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser }) }); let d = await r.json(); if (d.success) { addLog(d.msg); loadCityInfo(); loadFriendList(); } else alert(d.msg); }
async function loadBranchList() {
    let r = await fetch(`/api/occupied_list?username=${currentUser}`); let d = await r.json(); let container = document.getElementById('branchList');
    if (!d.list || d.list.length === 0) { container.innerHTML = '<div>暂无分舵</div>'; if (branchTimer) clearInterval(branchTimer); branchTimer = null; return; }
    let html = '';
    for (let b of d.list) { let remainText = b.expired ? '已到期' : `${Math.floor(b.remain_seconds/60)}分${b.remain_seconds%60}秒`; let canRecruit = b.remain_seconds <= 0; let recruitBtn = canRecruit ? `<button onclick="viewFriendRecruit('${b.name}')">🏛️ 参观万仙殿</button>` : `<button disabled style="opacity:0.5;">⏳ ${Math.floor(b.remain_seconds/60)}分${b.remain_seconds%60}秒后可招募</button>`; html += `<div class="branch-card"><img src="/static/images/heroes/${b.avatar}" style="width:40px;border-radius:50%;cursor:pointer;" onclick="visitFriendPalace('${b.name}')"><div style="flex:1;">${b.name}</div><div>⏰ ${remainText}</div>${recruitBtn}<button onclick="releaseFriend('${b.name}')">释放</button></div>`; }
    container.innerHTML = html; if (branchTimer) clearInterval(branchTimer); branchTimer = setInterval(() => { if (document.getElementById('tab-city').style.display === 'block') loadBranchList(); }, 1000);
}
function checkSelfOccupied() { loadCityInfo(); }

// ========== 访问好友碧游宫和万仙殿 ==========
async function visitFriendPalace(friendName) { let existingModal = document.querySelector('.modal'); if (existingModal) existingModal.remove(); let r = await fetch(`/friend_palace_info?username=${currentUser}&friend=${friendName}`); let d = await r.json(); if (!d.success) { alert(d.msg || "无法获取好友碧游宫信息"); return; } let modal = document.createElement('div'); modal.className = 'modal'; modal.innerHTML = `<div class="modal-content" style="text-align:center;"><h3>🏯 ${friendName} 的碧游宫</h3><img src="/static/images/avatars/${d.avatar}" style="width:80px; border-radius:50%; margin:10px auto; display:block;" onerror="this.src='/static/images/avatars/hero.png'"><p>🌟 等级: ${d.level}</p><p>👑 占领者: ${d.occupier || '无'}</p><p>📜 分舵数量: ${d.branches}</p><button onclick="this.closest('.modal').remove()" style="margin-top:15px;">关闭</button></div>`; document.body.appendChild(modal); }
async function viewFriendRecruit(friendName) {
    let info = await fetch(`/api/occupied_info?username=${currentUser}&target=${friendName}`); let data = await info.json();
    if (data.success && data.isOccupiedByMe && !data.canRecruit) { alert(`占领未满10分钟，还需等待 ${data.remainSeconds} 秒才能招募`); return; }
    let r = await fetch(`/recruit/other_shop?username=${currentUser}&target=${friendName}`); let d = await r.json(); if (d.error) { alert(d.error); return; }
    let modal = document.createElement('div'); modal.className = 'modal';
    let shopHtml = '<div class="hero-grid">';
    if (Object.keys(d.shop).length === 0) shopHtml += '<div style="text-align:center; padding:20px;">🏛️ 万仙殿空空如也，暂无武将可招募</div>';
    else { for (let [name, info] of Object.entries(d.shop)) { shopHtml += `<div class="recruit-card" data-name="${name}"><img src="/static/images/heroes/${info.hero_id}.png" onerror="this.src='/static/images/heroes/hero.png'"><div>${name}</div><div>★${info.star}</div><div>💰${info.cost}</div><button class="hire-from-occupied" data-name="${name}">招募</button></div>`; } }
    shopHtml += '</div>';
    modal.innerHTML = `<div class="modal-content"><h3>🏛️ ${d.target || friendName} 的万仙殿${data.isOccupiedByMe ? '（分舵）' : '（参观模式）'}</h3>${shopHtml}<button onclick="this.parentElement.parentElement.remove()" style="margin-top:15px;">关闭</button></div>`;
    document.body.appendChild(modal);
    if (data.isOccupiedByMe && data.canRecruit) { document.querySelectorAll('.hire-from-occupied').forEach(btn => { btn.onclick = async () => { let heroName = btn.dataset.name; let resp = await fetch('/recruit/hire_from_occupied', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, target: friendName, hero_name: heroName }) }); let res = await resp.json(); if (res.success) { addLog(`✨ ${res.msg}`); modal.remove(); await loadUserResources(); await loadGems(); await loadBranchList(); } else alert(res.msg); }; }); }
    else { document.querySelectorAll('.hire-from-occupied').forEach(btn => { btn.disabled = true; btn.style.opacity = '0.5'; btn.innerText = '不可招募'; }); }
}

// ========== 招贤馆 ==========
async function openRecruitShop() { if (!currentUser) { alert("请先登录"); return; } let mainContent = document.getElementById('mainContent'); if (mainContent) mainContent.style.display = 'none'; let infoDiv = document.getElementById('recruitShopInfo'); let heroesDiv = document.getElementById('recruitHeroes'); if (!infoDiv || !heroesDiv) { alert("页面错误，请联系管理员"); return; } let r = await fetch(`/recruit/shop?username=${currentUser}`); let d = await r.json(); if (d.error) { alert(d.error); return; } infoDiv.innerHTML = `<p>💰 金币: ${d.gold}</p><p>下次刷新: ${new Date(d.next_refresh).toLocaleTimeString()}</p>`; heroesDiv.innerHTML = ''; if (d.shop && Object.keys(d.shop).length > 0) { for (let [name, info] of Object.entries(d.shop)) { let div = document.createElement('div'); div.className = 'recruit-card'; div.innerHTML = `<img src="/static/images/heroes/${info.hero_id}.png" onerror="this.src='/static/images/heroes/hero.png'" style="width:80px;"><br>${name}<br>★${info.star}<br>💰${info.cost}<br><button onclick="hireHero('${name}')">招募</button>`; heroesDiv.appendChild(div); } } else { heroesDiv.innerHTML = '<div style="color:gold; text-align:center; padding:20px;">暂无武将，请稍后刷新</div>'; } document.getElementById('recruitShopModal').style.display = 'flex'; setBackgroundByTab('recruit'); document.body.style.overflow = 'hidden'; loadPrayStatus(); bindPrayButtons(); updateBlessingTimer(); }
async function hireHero(heroName) { let r = await fetch('/recruit/hire', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, hero_name: heroName }) }); let d = await r.json(); if (d.success) { addLog(`🎉 招募成功！获得 ${d.star}星 ${heroName}`); await loadUserResources(); openRecruitShop(); openMyHeroes(); } else alert(d.msg); }
function closeRecruitShop() { document.getElementById('recruitShopModal').style.display = 'none'; document.body.style.overflow = ''; let mainContent = document.getElementById('mainContent'); if (mainContent) mainContent.style.display = 'block'; let activeTab = document.querySelector('.tab-btn.active')?.dataset.tab; if (activeTab) setBackgroundByTab(activeTab); else setBackgroundByTab('map'); }
async function refreshRecruitShop() { let r = await fetch('/recruit/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, use_gold: true }) }); let d = await r.json(); if (d.success) { addLog(`🔄 刷新招贤馆，消耗100金币`); openRecruitShop(); } else alert(d.msg); }

// ========== 祈愿系统 ==========
async function loadPrayStatus() { if (!currentUser) return; try { const res = await fetch(`/pray/status?username=${currentUser}`); const data = await res.json(); if (data.success) { const remainSpan = document.getElementById('prayRemainCount'); const btns = document.querySelectorAll('.pray-btn'); if (remainSpan) { remainSpan.innerText = `今日剩余: ${data.remainCount}/10`; if (data.hasBuff) { btns.forEach(btn => { btn.classList.add('disabled'); btn.title = '盘古祝福生效中，请等待1小时后再祈愿'; }); remainSpan.style.color = '#ff8888'; remainSpan.title = '盘古祝福生效中，无法祈愿'; } else if (data.remainCount <= 0) { btns.forEach(btn => { btn.classList.remove('disabled'); btn.title = '特殊祈愿（80%概率获得1小时盘古祝福）'; }); remainSpan.style.color = '#ffaa66'; remainSpan.title = '今日正常祈愿次数已用完，接下来进行特殊祈愿'; } else { btns.forEach(btn => { btn.classList.remove('disabled'); btn.title = ''; }); remainSpan.style.color = ''; remainSpan.title = ''; } } } } catch (e) { console.warn('加载祈愿状态失败', e); } }
async function pray(prayType) { if (!currentUser) { alert("请先登录"); return; } const resultDiv = document.getElementById('prayResult'); resultDiv.innerHTML = "⏳ 祈祷中..."; try { const res = await fetch('/pray/burn_incense', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, pray_type: prayType }) }); const data = await res.json(); if (data.success) { resultDiv.innerHTML = `✅ ${data.msg}`; await loadUserResources(); if (data.reward && data.reward.type === 'hero') { const recruitRes = await fetch(`/recruit/shop?username=${currentUser}`); const shopData = await recruitRes.json(); if (!shopData.error) { const heroesDiv = document.getElementById('recruitHeroes'); if (heroesDiv && shopData.shop) { heroesDiv.innerHTML = ''; for (let [name, info] of Object.entries(shopData.shop)) { let div = document.createElement('div'); div.className = 'recruit-card'; div.innerHTML = `<img src="/static/images/heroes/${info.hero_id}.png" onerror="this.src='/static/images/heroes/hero.png'" style="width:80px;"><br>${name}<br>★${info.star}<br>💰${info.cost}<br><button onclick="hireHero('${name}')">招募</button>`; heroesDiv.appendChild(div); } } } } await loadPrayStatus(); startBlessingTimer(); } else { resultDiv.innerHTML = `❌ ${data.msg}`; if (data.msg && data.msg.includes('盘古祝福')) await loadPrayStatus(); } } catch (err) { resultDiv.innerHTML = `⚠️ 网络错误: ${err.message}`; } setTimeout(() => { if (resultDiv.innerHTML !== "⏳ 祈祷中...") setTimeout(() => { resultDiv.innerHTML = ''; }, 3000); }, 2000); }
function bindPrayButtons() { document.querySelectorAll('.pray-btn').forEach(btn => { btn.onclick = () => { const type = btn.dataset.type; pray(type); }; }); }

// ========== 好友面板 ==========
async function loadFriendList() { let r = await fetch(`/api/friends?username=${currentUser}`); let d = await r.json(); if (d.success) { friendsList = d.friends || []; renderFriendList(); } }
function renderFriendList() { let container = document.getElementById('friendListContainer'); let noMsg = document.getElementById('noFriendsMsg'); if (!container) return; if (friendsList.length === 0) { container.innerHTML = ''; noMsg.style.display = 'block'; return; } noMsg.style.display = 'none'; container.innerHTML = ''; let displayFriends = friendsList.slice(0,50); for (let f of displayFriends) { let div = document.createElement('div'); div.className = 'friend-item'; div.innerHTML = `<div style="display:flex; align-items:center; gap:8px; flex:1; cursor:pointer;" onclick="showFriendActions('${f.name}')"><img src="/static/images/avatars/${f.avatar || 'hero.png'}" class="friend-avatar" onerror="this.src='/static/images/avatars/hero.png'"><div><div class="friend-name">${f.name}</div><div class="friend-status">${f.online ? '🟢 在线' : '⚫ 离线'}</div></div></div><div class="friend-actions"><button onclick="showFriendActions('${f.name}')">📋</button></div>`; container.appendChild(div); } }
async function setSelfInfo() { let r = await fetch(`/user_info?username=${currentUser}`); let d = await r.json(); if (d.success) { document.getElementById('selfName').innerText = currentUser; document.getElementById('selfAvatar').src = `/static/images/avatars/${d.avatar}`; } }
function showFriendActions(friendName) { document.querySelectorAll('.modal').forEach(m=>m.remove()); let modal = document.createElement('div'); modal.className = 'modal'; modal.innerHTML = `<div class="modal-content" style="max-width:400px;"><h3>⚔️ 与 ${friendName} 互动</h3><div class="modal-friend-actions"><button onclick="closeModal(this); privateChat('${friendName}')">💬 私聊</button><button onclick="closeModal(this); matchWithFriend('${friendName}')">⚔️ 切磋</button><button id="occupyBtn_${friendName}" onclick="closeModal(this); attemptOccupy('${friendName}')">🏰 占领</button><button id="rescueBtn_${friendName}" onclick="closeModal(this); attemptRescue('${friendName}')">🔓 解救</button><button onclick="closeModal(this); visitFriendPalace('${friendName}')">🏯 访问</button><button onclick="closeModal(this); deleteFriendConfirm('${friendName}')">🗑️ 删除</button><button onclick="closeModal(this); addToBlacklist('${friendName}')">🚫 拉黑</button><button id="robBtn_${friendName}" onclick="closeModal(this); robOccupied('${friendName}')">⚔️ 抢夺</button></div><div style="text-align:center;margin-top:20px;"><button onclick="closeModal(this)">关闭</button></div></div>`; document.body.appendChild(modal); updateOccupyRescueButtons(friendName); }
async function updateOccupyRescueButtons(friendName) { let r = await fetch(`/get_occupier?username=${friendName}`); let d = await r.json(); let occupier = d.occupier; let occupyBtn = document.getElementById(`occupyBtn_${friendName}`); let rescueBtn = document.getElementById(`rescueBtn_${friendName}`); let robBtn = document.getElementById(`robBtn_${friendName}`); if (occupyBtn) { if (occupier) { occupyBtn.disabled = true; occupyBtn.title = `${friendName} 已被 ${occupier} 占领`; occupyBtn.style.opacity = '0.5'; } else { occupyBtn.disabled = false; occupyBtn.title = '点击占领'; occupyBtn.style.opacity = '1'; } } if (rescueBtn) { if (occupier === currentUser) rescueBtn.disabled = true; else if (occupier) rescueBtn.disabled = false; else rescueBtn.disabled = true; } if (robBtn) { if (occupier && occupier !== currentUser) { robBtn.disabled = false; robBtn.onclick = () => { closeModal(robBtn); robOccupied(friendName); }; } else { robBtn.disabled = true; } } }
function privateChat(friendName) { let chatInput = document.getElementById('chatInput'); if (chatInput) { chatInput.value = `@${friendName} `; chatInput.focus(); } let modal = document.querySelector('.modal'); if (modal) modal.remove(); addLog(`💬 开始与 ${friendName} 私聊，输入消息后发送（会自动提醒对方）`); }
async function matchWithFriend(friendName) { let m = document.querySelector('.modal'); if (m) m.remove(); let resp = await fetch('/match_pvp_with_friend', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, friend: friendName }) }); let data = await resp.json(); if (data.success) { if (typeof showBattlePanel === 'function') showBattlePanel(data.left_team, data.right_team, data.log, data.winner, data.left_power, data.right_power, async (winner) => { addLog(`⚔️ 与 ${friendName} 切磋${winner === 'left' ? '胜利' : '失败'}，获得经验${data.exp_gain}`); if (data.exp_gain) await loadUserResources(); loadDailyTasks(); }, friendName); } else alert(data.msg); }
async function attemptOccupy(friendName) { let m = document.querySelector('.modal'); if (m) m.remove(); let r = await fetch('/occupy_friend', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, friend: friendName }) }); let d = await r.json(); if (d.success) { addLog(`🏰 占领成功！${friendName} 成为你的分舵`); loadFriendList(); loadCityInfo(); } else alert(d.msg); }
async function attemptRescue(friendName) { let m = document.querySelector('.modal'); if (m) m.remove(); let r = await fetch('/release_friend', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, friend: friendName }) }); let d = await r.json(); if (d.success) { addLog(`🔓 解救成功！${friendName} 恢复自由`); loadFriendList(); loadCityInfo(); } else alert(d.msg); }
async function robOccupied(friendName) { let m = document.querySelector('.modal'); if (m) m.remove(); let r = await fetch('/rob_occupied', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, target: friendName }) }); let d = await r.json(); if (d.success) { addLog(`⚔️ ${d.msg}`); loadFriendList(); loadCityInfo(); } else alert(d.msg); }
async function deleteFriendConfirm(friendName) { if (!confirm(`确定删除好友 ${friendName} 吗？`)) return; let m = document.querySelector('.modal'); if (m) m.remove(); let r = await fetch('/api/friend/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, friend: friendName }) }); let d = await r.json(); if (d.success) { addLog(`已删除好友 ${friendName}`); loadFriendList(); } else alert(d.msg); }
async function addToBlacklist(friendName) { if (!confirm(`确定将 ${friendName} 拉入黑名单吗？\n拉黑后无法进行私聊和任何好友互动。`)) return; let m = document.querySelector('.modal'); if (m) m.remove(); let r = await fetch('/api/blacklist/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, target: friendName }) }); let d = await r.json(); if (d.success) { addLog(`🚫 ${friendName} 已被加入黑名单`); await fetch('/api/friend/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, friend: friendName }) }); loadFriendList(); loadBlacklist(); } else alert(d.msg); }
async function soloPracticeFromFriend() { let r = await fetch('/solo_practice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser }) }); let d = await r.json(); if (d.success) { if (typeof showBattlePanel === 'function') showBattlePanel(d.left_team, d.right_team, d.log, d.winner, d.left_power, d.right_power, (winner) => { addLog(`🧘 自我切磋结束，胜者: ${winner === 'left' ? '玩家' : '镜像'}，获得经验${d.exp_gain}`); if (d.exp_gain) loadUserResources(); loadDailyTasks(); }, currentUser); } else alert(d.msg); }
function toggleFriendPanel() { let p = document.getElementById('friendPanel'); p.style.display = p.style.display === 'none' ? 'block' : 'none'; if (p.style.display === 'block') { loadFriendList(); loadBlacklist(); setSelfInfo(); } }
async function sendFriendRequest() { let to = document.getElementById('addFriendInput').value.trim(); if (!to) return; let r = await fetch('/api/friend/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ from: currentUser, to: to }) }); let d = await r.json(); alert(d.msg); if (d.success) { document.getElementById('addFriendInput').value = ''; loadFriendList(); } }

// ========== 黑名单 ==========
async function loadBlacklist() { let r = await fetch(`/api/blacklist?username=${currentUser}`); let d = await r.json(); if (d.success) { blacklist = d.blacklist || []; let container = document.getElementById('blacklist'); if (!container) return; if (blacklist.length === 0) container.innerHTML = '<div>暂无黑名单</div>'; else { let html = ''; for (let name of blacklist) html += `<div class="friend-item"><span>${name}</span><button onclick="removeFromBlacklist('${name}')" style="background:#3a5a3a;">移除</button></div>`; container.innerHTML = html; } } }
async function removeFromBlacklist(name) { let r = await fetch('/api/blacklist/remove', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, target: name }) }); let d = await r.json(); if (d.success) { addLog(`已将 ${name} 移出黑名单`); await loadBlacklist(); await loadFriendList(); } else alert(d.msg); }

// ========== 头像 ==========
async function showAvatarModal() { let r = await fetch('/avatar_list?t=' + Date.now()); let d = await r.json(); let cont = document.getElementById('avatarList'); cont.innerHTML = ''; for (let av of d.avatars) { let div = document.createElement('div'); div.className = 'recruit-card'; div.innerHTML = `<img src="/static/images/avatars/${av}" style="width:60px;" onerror="this.parentElement.remove()"><div>${av}</div>`; div.onclick = () => selectAvatar(av); cont.appendChild(div); } document.getElementById('avatarModal').style.display = 'flex'; }
async function selectAvatar(avatar) { let r = await fetch('/update_avatar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: currentUser, avatar: avatar }) }); let d = await r.json(); if (d.success) { document.getElementById('userAvatar').src = `/static/images/avatars/${avatar}`; closeAvatarModal(); setSelfInfo(); addLog("👤 头像已更换"); } }
function closeAvatarModal() { document.getElementById('avatarModal').style.display = 'none'; }

function logout() { if (confirm("确定注销？")) { if (branchTimer) clearInterval(branchTimer); localStorage.removeItem('jijiao_user'); location.reload(); } }

// ========== 战斗控制 ==========
function initBattleControls() {
    const skipBtn = document.getElementById('skipFightBtn');
    const escapeBtn = document.getElementById('escapeBtn');
    if (skipBtn) { skipBtn.onclick = () => { if (window.currentAnimationPromise) { window.skipRequested = true; if (typeof addLog === 'function') addLog("⏩ 跳过战斗，直接结算..."); } else { if (typeof addLog === 'function') addLog("当前没有进行中的战斗，无法跳过"); } }; }
    if (escapeBtn) { escapeBtn.onclick = () => { if (!window.currentAnimationPromise && !window.isFighting) { if (typeof addLog === 'function') addLog("没有进行中的战斗"); return; } if (typeof addLog === 'function') addLog("🏃 你逃跑了，战斗结束"); window.skipRequested = true; window.isFighting = false; if (typeof hideBattlePanel === 'function') hideBattlePanel(); playBgMusic(); if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) { ws.send(JSON.stringify({ act: "escape" })); } }; }
}
async function loadPendingRequests() { let resp = await fetch(`/api/friend/pending?username=${currentUser}`); let data = await resp.json(); if (data.success && data.requests) { for (let req of data.requests) { addFriendRequestLog(req.from, `📨 ${req.from} 请求添加你为好友（离线期间）`); } } }

window.onload = async () => {
    await checkAuth();
    makeDraggable(document.getElementById('logPanel'));
    initTabs();
    setBackgroundByTab('map');
    initBattleControls();
    setInterval(() => { if (document.getElementById('friendPanel').style.display === 'block') loadFriendList(); }, 30000);
};
</script>
</body>
</html>'''