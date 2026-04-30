
html_code = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>战棋Demo · HTML5版</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            background: #1a1a2e;
            color: #fff;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        #gameContainer {
            display: flex;
            gap: 20px;
            padding: 20px;
        }
        canvas {
            border-radius: 8px;
            cursor: pointer;
        }
        #panel {
            width: 320px;
            background: #0f3460;
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            height: 560px;
        }
        #turnInfo {
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }
        .player-turn {
            background: #2962ff;
            color: #fff;
        }
        .enemy-turn {
            background: #d50000;
            color: #fff;
        }
        .game-over {
            background: #ff5050;
            color: #fff;
        }
        #unitInfo {
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 6px;
            min-height: 180px;
            font-size: 14px;
            line-height: 1.8;
        }
        #unitInfo .info-line {
            margin: 4px 0;
        }
        #unitInfo .label {
            color: #aaa;
        }
        #buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-family: inherit;
            transition: all 0.2s;
            color: #fff;
        }
        .btn:hover {
            transform: translateY(-2px);
            opacity: 0.9;
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn-end {
            background: #2962ff;
        }
        .btn-attack {
            background: #ff3232;
        }
        .btn-attack.active {
            background: #ff0000;
            box-shadow: 0 0 10px #ff0000;
        }
        .btn-allout {
            background: #ff8c00;
        }
        .btn-allout.active {
            background: #ff6600;
            box-shadow: 0 0 10px #ff6600;
        }
        .btn-dir {
            background: #505064;
            width: 60px;
            padding: 6px;
        }
        .btn:disabled {
            background: #444;
            cursor: not-allowed;
            opacity: 0.5;
        }
        #log {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid #505064;
            border-radius: 6px;
            padding: 10px;
            flex: 1;
            overflow-y: auto;
            font-size: 12px;
            line-height: 1.6;
            max-height: 200px;
        }
        #log .log-entry {
            margin: 2px 0;
            color: #aaa;
        }
        #log .log-entry.damage {
            color: #ff6b6b;
        }
        #log .log-entry.heal {
            color: #00e676;
        }
        #log .log-entry.system {
            color: #ffd700;
        }
        .section-title {
            color: #ffd700;
            font-size: 14px;
            margin: 8px 0 4px;
        }
    </style>
</head>
<body>
    <div id="gameContainer">
        <canvas id="board" width="456" height="560"></canvas>
        <div id="panel">
            <div id="turnInfo">🛡️ 玩家行动 (第1回合)</div>
            <div id="unitInfo">
                <div style="color:#aaa;text-align:center;padding:20px;">点击己方单位开始行动</div>
            </div>
            <div class="section-title">行动指令</div>
            <div id="buttons">
                <button class="btn btn-end" id="btnEnd" onclick="game.endUnitTurn()">结束行动</button>
                <button class="btn btn-attack" id="btnAttack" onclick="game.toggleAttackMode()">普通攻击</button>
                <button class="btn btn-allout" id="btnAllout" onclick="game.toggleAlloutMode()">奋力再击</button>
            </div>
            <div id="buttons-dir" style="display:flex;gap:5px;justify-content:center;">
                <button class="btn btn-dir" onclick="game.changeFacing('up')">↑上</button>
                <button class="btn btn-dir" onclick="game.changeFacing('down')">↓下</button>
                <button class="btn btn-dir" onclick="game.changeFacing('left')">←左</button>
                <button class="btn btn-dir" onclick="game.changeFacing('right')">→右</button>
            </div>
            <div class="section-title">战斗日志</div>
            <div id="log"></div>
        </div>
    </div>
    <script>
        // ==================== 配置 ====================
        const BOARD_W = 8,
            BOARD_H = 10,
            CELL_SIZE = 52;
        const COLORS = {
            BG: '#0a1428',
            BOARD_BG: '#1a2338',
            CELL: '#2a2f45',
            CELL_BORDER: '#3f4559',
            CURRENT_TURN: '#ffd700',
            PLAYER: '#2962ff',
            ENEMY: '#d50000',
            HP_GREEN: '#00e676',
            OBSTACLE: '#1f2128',
            OBSTACLE_BORDER: '#505050',
            MOVE_RANGE: 'rgba(0,100,200,0.5)',
            ATTACK_RANGE: 'rgba(180,40,40,0.5)',
            PLAYER_ACTED: '#4a5a7a',
            ENEMY_ACTED: '#7a4a4a',
        };

        const CLASS_TEMPLATES = {
            infantry: {
                name: '步兵',
                hp: 20,
                atk: 8,
                def: 5,
                ap: 10,
                extraRange: [],
                desc: '基础兵种，攻守平衡',
                maxTargets: 1
            },
            knight: {
                name: '枪兵',
                hp: 16,
                atk: 12,
                def: 4,
                ap: 12,
                extraRange: [[0, 2], [0, 3]],
                desc: '前方+2格冲锋',
                maxTargets: 1
            },
            archer: {
                name: '弓手',
                hp: 14,
                atk: 10,
                def: 4,
                ap: 10,
                extraRange: [[0, 3], [1, 2], [-1, 2]],
                desc: '前方远射',
                maxTargets: 1
            },
            assassin: {
                name: '卫士',
                hp: 15,
                atk: 9,
                def: 6,
                ap: 8,
                extraRange: [[0, -1]],
                desc: '后方+1格',
                maxTargets: 1
            },
            mage: {
                name: '军师',
                hp: 12,
                atk: 8,
                def: 4,
                ap: 10,
                extraRange: [[0, 2], [-1, 2], [1, 2]],
                desc: '前方第2行3格范围攻击（最多2目标）',
                maxTargets: 2
            },
            sword: {
                name: '剑士',
                hp: 18,
                atk: 11,
                def: 5,
                ap: 10,
                extraRange: [[-1, 1], [1, 1]],
                desc: '前方3格横扫',
                maxTargets: 1
            }
        };

        function templateToMap(dx, dy, facing) {
            if (facing === 'up') return [dx, -dy];
            if (facing === 'down') return [-dx, dy];
            if (facing === 'left') return [-dy, -dx];
            if (facing === 'right') return [dy, dx];
            return [dx, dy];
        }

        // ==================== 单位类 ====================
        class Unit {
            constructor(id, cls, x, y, facing, faction) {
                this.id = id;
                this.cls = cls;
                const template = CLASS_TEMPLATES[cls];
                this.name = template.name;
                this.x = x;
                this.y = y;
                this.facing = facing;
                this.faction = faction;

                this.maxHp = template.hp;
                this.hp = template.hp;
                this.atk = template.atk;
                this.defBase = template.def;
                this.apMax = template.ap;
                this.curAp = template.ap;

                this.hasEngaged = false;
                this.dead = false;
                this.acted = false;
                this.hasUsedNormalAttack = false;
                this.hasUsedAlloutAttack = false;

                this.shakeTime = 0;
                this.deathTime = 0;
            }

            defense(units) {
                let bonus = 0;
                const neighbors = [
                    getUnitAt(units, this.x - 1, this.y),
                    getUnitAt(units, this.x + 1, this.y),
                    getUnitAt(units, this.x, this.y - 1),
                    getUnitAt(units, this.x, this.y + 1)
                ];
                for (const u of neighbors) {
                    if (u && u.faction === this.faction) bonus++;
                }
                bonus = Math.min(bonus, 3);
                return this.defBase + bonus;
            }

            attackPower() {
                return this.atk - (this.hasEngaged ? 0 : 2);
            }
        }

        function getUnitAt(units, x, y) {
            for (const u of units) {
                if (u.x === x && u.y === y && !u.dead) return u;
            }
            return null;
        }

        // ==================== 游戏主类 ====================
        class Game {
            constructor() {
                this.canvas = document.getElementById('board');
                this.ctx = this.canvas.getContext('2d');
                this.units = [];
                this.selectedUnit = null;
                this.currentUnit = null;
                this.pendingMode = null;
                this.turnCount = 1;
                this.actionOrder = [];
                this.aiBusy = false;
                this.gameOver = false;
                this.logMessages = [];
                this.obstacles = new Set();
                this.animations = [];
                this.lastTime = performance.now();
                this.animationFrame = null;
                this.aiStepCount = 0;

                // 地形系统
                this.riverCells = new Set();
                this.bridgeCells = new Set();
                this.terrainColors = {};

                this.canvas.addEventListener('click', (e) => this.handleClick(e));

                this.initRiver();
                this.initObstacles();
                this.initTerrain();
                this.initUnits();
                this.startNewRound();
                this.gameLoop();
            }

            // ==================== 地形初始化 ====================
            initRiver() {
                const mid = Math.floor(BOARD_H / 2);
                const y1 = mid - 1;  // 第4行
                const y2 = mid;      // 第5行
                for (let x = 0; x < BOARD_W; x++) {
                    this.riverCells.add(`${x},${y1}`);
                    this.riverCells.add(`${x},${y2}`);
                }
                // 随机2列桥
                const cols = [];
                while (cols.length < 2) {
                    const c = Math.floor(Math.random() * BOARD_W);
                    if (!cols.includes(c)) cols.push(c);
                }
                for (const c of cols) {
                    this.bridgeCells.add(`${c},${y1}`);
                    this.bridgeCells.add(`${c},${y2}`);
                }
            }

            initTerrain() {
                for (let y = 0; y < BOARD_H; y++) {
                    for (let x = 0; x < BOARD_W; x++) {
                        const key = `${x},${y}`;
                        if (this.riverCells.has(key)) {
                            // 河流深蓝
                            this.terrainColors[key] = '#1a3a5c';
                        } else if (this.bridgeCells.has(key)) {
                            // 桥梁木色
                            this.terrainColors[key] = '#8b6f47';
                        } else {
                            // 草地与沙地混合（基于坐标的伪随机，保持一致性）
                            const hash = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
                            const rand = hash - Math.floor(hash);
                            if (rand > 0.55) {
                                this.terrainColors[key] = '#b8a878'; // 沙地
                            } else if (rand > 0.25) {
                                this.terrainColors[key] = '#5a8f5f'; // 浅草地
                            } else {
                                this.terrainColors[key] = '#4a7c4e'; // 深草地
                            }
                        }
                    }
                }
            }

            gameLoop() {
                const now = performance.now();
                const dt = (now - this.lastTime) / 1000;
                this.lastTime = now;

                this.updateAnimations(dt);
                this.render();

                this.animationFrame = requestAnimationFrame(() => this.gameLoop());
            }

            updateAnimations(dt) {
                for (let i = this.animations.length - 1; i >= 0; i--) {
                    const a = this.animations[i];
                    a.time += dt;
                    if (a.time >= a.duration) {
                        this.animations.splice(i, 1);
                    }
                }
            }

            addDamageText(target, dmg) {
                const screenX = target.x * CELL_SIZE + CELL_SIZE / 2;
                const screenY = target.y * CELL_SIZE + CELL_SIZE / 2 - 15;

                this.animations.push({
                    type: 'damage',
                    value: dmg,
                    screenX: screenX,
                    screenY: screenY,
                    time: 0,
                    duration: 1.1
                });
            }

            addAttackEffect(attacker, target) {
                const ax = attacker.x * CELL_SIZE + CELL_SIZE / 2;
                const ay = attacker.y * CELL_SIZE + CELL_SIZE / 2;
                const tx = target.x * CELL_SIZE + CELL_SIZE / 2;
                const ty = target.y * CELL_SIZE + CELL_SIZE / 2;

                this.animations.push({
                    type: 'attackEffect',
                    screenX: (ax + tx) / 2,
                    screenY: (ay + ty) / 2 - 10,
                    time: 0,
                    duration: 0.45
                });
            }

            basePositions() {
                return [
                    ['p1', 'infantry', 0, 8, 'up', 'player'],
                    ['p2', 'knight', 3, 8, 'up', 'player'],
                    ['p3', 'archer', 4, 8, 'up', 'player'],
                    ['p4', 'mage', 5, 8, 'up', 'player'],
                    ['p5', 'assassin', 7, 8, 'up', 'player'],
                    ['p6', 'sword', 2, 8, 'up', 'player'],
                    ['e1', 'infantry', 0, 1, 'down', 'enemy'],
                    ['e2', 'knight', 3, 1, 'down', 'enemy'],
                    ['e3', 'archer', 4, 1, 'down', 'enemy'],
                    ['e4', 'mage', 5, 1, 'down', 'enemy'],
                    ['e5', 'assassin', 7, 1, 'down', 'enemy'],
                    ['e6', 'sword', 2, 1, 'down', 'enemy']
                ];
            }

            initObstacles() {
                const allPos = [];
                for (let x = 0; x < BOARD_W; x++) {
                    for (let y = 0; y < BOARD_H; y++) allPos.push([x, y]);
                }
                const unitPos = this.basePositions().map(p => [p[2], p[3]]);
                const available = allPos.filter(p => {
                    const key = `${p[0]},${p[1]}`;
                    return !unitPos.some(up => up[0] === p[0] && up[1] === p[1])
                        && !this.riverCells.has(key)
                        && !this.bridgeCells.has(key);
                });
                const count = Math.min(6, available.length);
                for (let i = 0; i < count; i++) {
                    const idx = Math.floor(Math.random() * available.length);
                    const [x, y] = available.splice(idx, 1)[0];
                    this.obstacles.add(`${x},${y}`);
                }
            }

            initUnits() {
                this.units = this.basePositions().map(args => new Unit(...args));
            }

            log(msg, type = '') {
                this.logMessages.push({ msg, type });
                if (this.logMessages.length > 50) this.logMessages.shift();
                this.updateLog();
            }

            updateLog() {
                const logEl = document.getElementById('log');
                logEl.innerHTML = this.logMessages.slice(-12).map(entry =>
                    `<div class="log-entry ${entry.type}">${entry.msg}</div>`
                ).join('');
                logEl.scrollTop = logEl.scrollHeight;
            }

            buildActionOrder() {
                const players = this.units.filter(u => u.faction === 'player' && !u.dead);
                const enemies = this.units.filter(u => u.faction === 'enemy' && !u.dead);
                const order = [];
                const maxLen = Math.max(players.length, enemies.length);
                for (let i = 0; i < maxLen; i++) {
                    if (i < players.length) order.push(players[i]);
                    if (i < enemies.length) order.push(enemies[i]);
                }
                return order;
            }

            getNextActiveUnit() {
                for (const u of this.actionOrder) {
                    if (!u.acted && !u.dead) return u;
                }
                return null;
            }

            startNewRound() {
                this.actionOrder = this.buildActionOrder();
                for (const u of this.units) {
                    u.acted = false;
                    u.hasUsedNormalAttack = false;
                    u.hasUsedAlloutAttack = false;
                }
                this.selectedUnit = null;
                this.currentUnit = null;
                this.pendingMode = null;
                this.aiStepCount = 0;
                this.advanceTurn();
            }

            advanceTurn() {
                if (this.gameOver) return;
                const nextUnit = this.getNextActiveUnit();
                if (!nextUnit) {
                    this.turnCount++;
                    this.log(`=== 第${this.turnCount}回合 ===`, 'system');
                    this.startNewRound();
                    return;
                }
                this.currentUnit = nextUnit;
                this.currentUnit.curAp = this.currentUnit.apMax;
                this.currentUnit.hasUsedNormalAttack = false;
                this.currentUnit.hasUsedAlloutAttack = false;

                if (this.currentUnit.faction === 'player') {
                    this.onPlayerTurn();
                } else {
                    this.onEnemyTurn();
                }
            }

            onPlayerTurn() {
                this.aiBusy = false;
                this.selectedUnit = this.currentUnit;
                this.pendingMode = null;
                this.log(`轮到 ${this.currentUnit.name} 行动`);
                this.updateUI();
            }

            onEnemyTurn() {
                if (this.gameOver) return;
                this.aiBusy = true;
                this.selectedUnit = this.currentUnit;
                this.pendingMode = null;
                this.aiStepCount = 0;
                this.log(`敌方 ${this.currentUnit.name} 开始行动`);
                this.updateUI();
                setTimeout(() => this.aiStep(), 400);
            }

            performAttack(target, isAllout) {
                if (!this.selectedUnit || target.dead || this.aiBusy) return;
                if (this.currentUnit?.faction !== 'player') return;
                if (this.selectedUnit !== this.currentUnit) return;

                const atkCells = this.getBaseAttackCells(this.selectedUnit);
                if (!atkCells.some(c => c[0] === target.x && c[1] === target.y)) {
                    this.log('目标不在攻击范围内！');
                    return;
                }

                if (isAllout) {
                    if (this.selectedUnit.hasUsedAlloutAttack || this.selectedUnit.curAp < 5) return;
                } else {
                    if (this.selectedUnit.hasUsedNormalAttack || this.selectedUnit.curAp < 3) return;
                }

                const template = CLASS_TEMPLATES[this.selectedUnit.cls];
                const maxTargets = template.maxTargets || 1;

                let enemyTargets = this.units.filter(u =>
                    u.faction !== this.selectedUnit.faction && !u.dead &&
                    atkCells.some(c => c[0] === u.x && c[1] === u.y)
                );

                if (maxTargets < enemyTargets.length) {
                    enemyTargets.sort((a, b) => (a.y * 100 + a.x) - (b.y * 100 + b.x));
                    enemyTargets = enemyTargets.slice(0, maxTargets);
                }

                for (const enemy of enemyTargets) {
                    const atkPow = this.selectedUnit.attackPower();
                    const tarDef = enemy.defense(this.units);
                    const dmg = Math.max(0, atkPow - tarDef);

                    this.selectedUnit.hasEngaged = true;
                    enemy.hasEngaged = true;
                    enemy.hp -= dmg;
                    if (enemy.hp <= 0) {
                        enemy.hp = 0;
                        enemy.dead = true;
                        enemy.deathTime = Date.now();
                    }

                    this.addDamageText(enemy, dmg);
                    this.addAttackEffect(this.selectedUnit, enemy);
                    enemy.shakeTime = 0.35;

                    if (enemy.dead) this.log(`${enemy.name} 被击败！`, 'system');
                }

                if (isAllout) {
                    this.selectedUnit.curAp = 0;
                    this.selectedUnit.hasUsedAlloutAttack = true;
                    this.log(`${this.selectedUnit.name} 发动再击，攻击${enemyTargets.length}个目标！`, 'damage');
                } else {
                    this.selectedUnit.curAp -= 3;
                    this.selectedUnit.hasUsedNormalAttack = true;
                    this.log(`${this.selectedUnit.name} 普通攻击，攻击${enemyTargets.length}个目标`, 'damage');
                }

                this.pendingMode = null;
                this.checkGameOver();
                this.updateUI();
                this.render();
            }

            performAttackAi(attacker, target, isAllout) {
                if ((attacker.hasUsedAlloutAttack && isAllout) || (attacker.hasUsedNormalAttack && !isAllout)) return;
                const atkCells = this.getBaseAttackCells(attacker);
                if (!atkCells.some(c => c[0] === target.x && c[1] === target.y)) return;
                if (isAllout && attacker.curAp < 5) return;
                if (!isAllout && attacker.curAp < 3) return;

                const template = CLASS_TEMPLATES[attacker.cls];
                const maxTargets = template.maxTargets || 1;

                let enemyTargets = this.units.filter(u =>
                    u.faction !== attacker.faction && !u.dead &&
                    atkCells.some(c => c[0] === u.x && c[1] === u.y)
                );

                if (maxTargets < enemyTargets.length) {
                    enemyTargets.sort((a, b) => (a.y * 100 + a.x) - (b.y * 100 + b.x));
                    enemyTargets = enemyTargets.slice(0, maxTargets);
                }

                for (const enemy of enemyTargets) {
                    const atkPow = attacker.attackPower();
                    const tarDef = enemy.defense(this.units);
                    const dmg = Math.max(0, atkPow - tarDef);

                    enemy.hp -= dmg;
                    if (enemy.hp <= 0) {
                        enemy.hp = 0;
                        enemy.dead = true;
                        enemy.deathTime = Date.now();
                    }
                    attacker.hasEngaged = true;
                    enemy.hasEngaged = true;

                    this.addDamageText(enemy, dmg);
                    this.addAttackEffect(attacker, enemy);
                    enemy.shakeTime = 0.35;
                    if (enemy.dead) this.log(`${enemy.name} 被击败！`, 'system');
                }

                if (isAllout) {
                    attacker.curAp = 0;
                    attacker.hasUsedAlloutAttack = true;
                    this.log(`[敌方] ${attacker.name} 全力攻击${enemyTargets.length}个目标`, 'damage');
                } else {
                    attacker.curAp -= 3;
                    attacker.hasUsedNormalAttack = true;
                    this.log(`[敌方] ${attacker.name} 普通攻击${enemyTargets.length}个目标`, 'damage');
                }
            }

            endUnitTurn(unit = this.selectedUnit) {
                if (!unit) return;
                if (unit.dead) {
                    unit.acted = true;
                    this.selectedUnit = null;
                    this.currentUnit = null;
                    this.pendingMode = null;
                    if (this.checkGameOver()) return;
                    this.advanceTurn();
                    return;
                }

                let enemyCount = 0;
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        if (dx === 0 && dy === 0) continue;
                        const u = getUnitAt(this.units, unit.x + dx, unit.y + dy);
                        if (u && u.faction !== unit.faction && !u.dead) enemyCount++;
                    }
                }

                const heal = unit.curAp - enemyCount;
                const oldHp = unit.hp;
                unit.hp = Math.max(0, Math.min(unit.maxHp, unit.hp + heal));
                const actual = unit.hp - oldHp;

                if (unit.hp <= 0) {
                    unit.hp = 0;
                    unit.dead = true;
                    unit.deathTime = Date.now();
                    this.log(`${unit.name} 因压力过大倒下了！`, 'damage');
                } else if (actual > 0) {
                    this.log(`${unit.name} 回复${actual}点体力`, 'heal');
                } else if (actual < 0) {
                    this.log(`${unit.name} 受到${-actual}点压力伤害！`, 'damage');
                }

                // ★ 河流溺水伤害 ★
                if (!unit.dead) {
                    const inRiver = this.riverCells.has(`${unit.x},${unit.y}`);
                    const onBridge = this.bridgeCells.has(`${unit.x},${unit.y}`);
                    if (inRiver && !onBridge) {
                        unit.hp -= 10;
                        this.log(`${unit.name} 在河中受到10点溺水伤害！`, 'damage');
                        if (unit.hp <= 0) {
                            unit.hp = 0;
                            unit.dead = true;
                            unit.deathTime = Date.now();
                            this.log(`${unit.name} 溺水身亡！`, 'system');
                        }
                    }
                }

                unit.acted = true;
                this.selectedUnit = null;
                this.currentUnit = null;
                this.pendingMode = null;

                if (this.checkGameOver()) return;
                this.advanceTurn();
            }

            checkGameOver() {
                const pAlive = this.units.filter(u => u.faction === 'player' && !u.dead).length;
                const eAlive = this.units.filter(u => u.faction === 'enemy' && !u.dead).length;
                if (pAlive === 0) {
                    this.gameOver = true;
                    this.log('💀 游戏结束：敌方胜利！', 'system');
                    this.updateUI();
                    return true;
                }
                if (eAlive === 0) {
                    this.gameOver = true;
                    this.log('🎉 游戏结束：玩家胜利！', 'system');
                    this.updateUI();
                    return true;
                }
                return false;
            }

            getBaseAttackCells(unit) {
                const base = [
                    [0, 1],
                    [-1, 0],
                    [1, 0]
                ];
                const extra = CLASS_TEMPLATES[unit.cls].extraRange;
                const allRel = [...base, ...extra];
                const cells = [];
                for (const [dx, dy] of allRel) {
                    const [mx, my] = templateToMap(dx, dy, unit.facing);
                    const tx = unit.x + mx,
                        ty = unit.y + my;
                    if (tx >= 0 && tx < BOARD_W && ty >= 0 && ty < BOARD_H) cells.push([tx, ty]);
                }
                return cells;
            }

            getMoveCells(unit) {
                const reachable = {};
                const visited = new Map();
                visited.set(`${unit.x},${unit.y}`, 0);
                const queue = [
                    [unit.x, unit.y, 0]
                ];
                let head = 0;

                while (head < queue.length) {
                    const [x, y, cost] = queue[head++];
                    if (cost > 0) reachable[`${x},${y}`] = cost;
                    if (cost >= unit.curAp) continue;
                    for (const [dx, dy] of [
                            [0, -1],
                            [0, 1],
                            [-1, 0],
                            [1, 0]
                        ]) {
                        const nx = x + dx,
                            ny = y + dy;
                        if (nx < 0 || nx >= BOARD_W || ny < 0 || ny >= BOARD_H) continue;
                        if (this.obstacles.has(`${nx},${ny}`)) continue;
                        if (getUnitAt(this.units, nx, ny)) continue;
                        
                        // ★ 河流消耗5AP，桥梁正常1AP ★
                        const isRiver = this.riverCells.has(`${nx},${ny}`);
                        const isBridge = this.bridgeCells.has(`${nx},${ny}`);
                        let stepCost = 1;
                        if (isRiver && !isBridge) stepCost = 5;
                        
                        const key = `${nx},${ny}`;
                        const newCost = cost + stepCost;
                        if (!visited.has(key) || visited.get(key) > newCost) {
                            visited.set(key, newCost);
                            queue.push([nx, ny, newCost]);
                        }
                    }
                }
                return reachable;
            }

            moveUnitTo(x, y) {
                if (!this.selectedUnit || this.aiBusy) return;
                if (this.currentUnit?.faction !== 'player') return;
                if (this.selectedUnit !== this.currentUnit) return;
                const moves = this.getMoveCells(this.selectedUnit);
                const key = `${x},${y}`;
                if (!(key in moves)) return;

                const cost = moves[key];
                this.selectedUnit.x = x;
                this.selectedUnit.y = y;
                this.selectedUnit.curAp -= cost;
                
                const isRiver = this.riverCells.has(key);
                const isBridge = this.bridgeCells.has(key);
                let terrainMsg = '';
                if (isRiver && !isBridge) terrainMsg = '（渡河）';
                else if (isBridge) terrainMsg = '（过桥）';
                
                this.log(`${this.selectedUnit.name} 移动到 (${x},${y})${terrainMsg}，消耗${cost}AP，剩余AP:${this.selectedUnit.curAp}`);
                this.updateUI();
            }

            // ==================== AI部分 ====================
            aiStep() {
                if (!this.aiBusy || this.gameOver) return;
                
                this.aiStepCount++;
                if (this.aiStepCount > 50) {
                    this.log(`[系统] ${this.currentUnit?.name || '敌方单位'} 行动超时，强制结束回合`, 'system');
                    if (this.currentUnit) {
                        this.currentUnit.acted = true;
                    }
                    this.aiBusy = false;
                    this.selectedUnit = null;
                    this.currentUnit = null;
                    this.pendingMode = null;
                    this.advanceTurn();
                    return;
                }

                const unit = this.currentUnit;
                if (!unit || unit.dead) {
                    this.aiBusy = false;
                    this.advanceTurn();
                    return;
                }
                
                if (unit.acted) {
                    this.aiBusy = false;
                    this.advanceTurn();
                    return;
                }

                const targets = this.units.filter(u => u.faction !== unit.faction && !u.dead);
                if (!targets.length) {
                    this.aiBusy = false;
                    this.advanceTurn();
                    return;
                }

                const target = targets.reduce((best, t) => {
                    const d1 = Math.abs(t.x - unit.x) + Math.abs(t.y - unit.y);
                    const d2 = Math.abs(best.x - unit.x) + Math.abs(best.y - unit.y);
                    return d1 < d2 ? t : best;
                });

                const atkCells = this.getBaseAttackCells(unit);
                
                if (atkCells.some(c => c[0] === target.x && c[1] === target.y)) {
                    if (!unit.hasUsedNormalAttack && unit.curAp >= 3) {
                        this.performAttackAi(unit, target, false);
                        this.render();
                        this.updateUI();
                        setTimeout(() => this.aiStep(), 500);
                        return;
                    }
                    if (!unit.hasUsedAlloutAttack && unit.curAp >= 5) {
                        this.performAttackAi(unit, target, true);
                        this.render();
                        this.updateUI();
                        setTimeout(() => this.aiStep(), 500);
                        return;
                    }
                    this.aiBusy = false;
                    this.endUnitTurn(unit);
                    return;
                }

                if (unit.curAp >= 1) {
                    const originalFacing = unit.facing;
                    
                    for (const tryDir of ['up', 'down', 'left', 'right']) {
                        if (tryDir === originalFacing) continue;
                        unit.facing = tryDir;
                        const newAtk = this.getBaseAttackCells(unit);
                        if (newAtk.some(c => c[0] === target.x && c[1] === target.y)) {
                            unit.curAp -= 1;
                            this.log(`[敌方] ${unit.name} 转向${tryDir}`);
                            
                            if (!unit.hasUsedNormalAttack && unit.curAp >= 3) {
                                this.performAttackAi(unit, target, false);
                                this.render();
                                this.updateUI();
                                setTimeout(() => this.aiStep(), 500);
                                return;
                            } else if (!unit.hasUsedAlloutAttack && unit.curAp >= 5) {
                                this.performAttackAi(unit, target, true);
                                this.render();
                                this.updateUI();
                                setTimeout(() => this.aiStep(), 500);
                                return;
                            } else {
                                this.aiBusy = false;
                                this.endUnitTurn(unit);
                                return;
                            }
                        }
                    }
                    unit.facing = originalFacing;
                }

                if (unit.curAp >= 1) {
                    const moves = this.getMoveCells(unit);
                    let bestPos = null,
                        bestDist = Infinity;
                    
                    for (const [key, cost] of Object.entries(moves)) {
                        const [mx, my] = key.split(',').map(Number);
                        const dist = Math.abs(target.x - mx) + Math.abs(target.y - my);
                        if (dist < bestDist) {
                            bestDist = dist;
                            bestPos = [mx, my, cost];
                        }
                    }

                    if (bestPos) {
                        const [mx, my, cost] = bestPos;
                        const dx = mx - unit.x,
                            dy = my - unit.y;
                        const stepX = dx === 0 ? 0 : (dx > 0 ? 1 : -1);
                        const stepY = dy === 0 ? 0 : (dy > 0 ? 1 : -1);
                        let moved = false;

                        const tryMoves = [
                            [stepX, 0],
                            [0, stepY],
                            [stepX, stepY]
                        ];
                        
                        for (const [sx, sy] of tryMoves) {
                            if (sx === 0 && sy === 0) continue;
                            const nx = unit.x + sx,
                                ny = unit.y + sy;
                            const nKey = `${nx},${ny}`;
                            if (nKey in moves && moves[nKey] <= unit.curAp) {
                                unit.x = nx;
                                unit.y = ny;
                                unit.curAp -= moves[nKey];
                                if (Math.abs(sx) >= Math.abs(sy)) {
                                    unit.facing = sx > 0 ? 'right' : 'left';
                                } else {
                                    unit.facing = sy > 0 ? 'down' : 'up';
                                }
                                moved = true;
                                break;
                            }
                        }

                        if (!moved) {
                            this.aiBusy = false;
                            this.endUnitTurn(unit);
                            return;
                        }
                        
                        this.render();
                        this.updateUI();
                        
                        if (unit.curAp > 0 && !unit.acted) {
                            setTimeout(() => this.aiStep(), 350);
                        } else {
                            this.aiBusy = false;
                            this.endUnitTurn(unit);
                        }
                        return;
                    }
                }
                
                this.aiBusy = false;
                this.endUnitTurn(unit);
            }

            toggleAttackMode() {
                if (!this.selectedUnit || this.aiBusy || this.gameOver) return;
                if (this.currentUnit?.faction !== 'player') return;
                if (this.selectedUnit !== this.currentUnit) return;
                if (this.selectedUnit.hasUsedNormalAttack || this.selectedUnit.curAp < 3) return;
                this.pendingMode = this.pendingMode === 'attack' ? null : 'attack';
                this.updateUI();
                this.render();
            }

            toggleAlloutMode() {
                if (!this.selectedUnit || this.aiBusy || this.gameOver) return;
                if (this.currentUnit?.faction !== 'player') return;
                if (this.selectedUnit !== this.currentUnit) return;
                if (this.selectedUnit.hasUsedAlloutAttack || this.selectedUnit.curAp < 5) return;
                this.pendingMode = this.pendingMode === 'allout' ? null : 'allout';
                this.updateUI();
                this.render();
            }

            changeFacing(direction) {
                if (!this.selectedUnit || this.aiBusy || this.gameOver || this.selectedUnit.curAp < 1) return;
                if (this.currentUnit?.faction !== 'player') return;
                if (this.selectedUnit !== this.currentUnit) return;

                this.selectedUnit.facing = direction;
                this.selectedUnit.curAp -= 1;
                const dirNames = { up: '上', down: '下', left: '左', right: '右' };
                this.log(`${this.selectedUnit.name} 转向${dirNames[direction]}，消耗1AP`);
                this.updateUI();
                this.render();
            }

            handleClick(e) {
                if (this.aiBusy || this.gameOver) return;
                if (this.currentUnit && this.currentUnit.faction !== 'player') return;
                const rect = this.canvas.getBoundingClientRect();
                const mx = e.clientX - rect.left,
                    my = e.clientY - rect.top;
                const gx = Math.floor(mx / CELL_SIZE),
                    gy = Math.floor(my / CELL_SIZE);
                if (gx < 0 || gx >= BOARD_W || gy < 0 || gy >= BOARD_H) return;

                const unit = getUnitAt(this.units, gx, gy);

                if (this.pendingMode && this.selectedUnit && this.selectedUnit === this.currentUnit) {
                    if (unit && unit.faction !== this.selectedUnit.faction && !unit.dead) {
                        this.performAttack(unit, this.pendingMode === 'allout');
                        return;
                    } else {
                        this.pendingMode = null;
                        this.updateUI();
                        this.render();
                        return;
                    }
                }

                if (unit && unit.faction === 'player' && !unit.dead) {
                    if (unit === this.currentUnit) {
                        this.selectedUnit = unit;
                        this.pendingMode = null;
                        this.updateUI();
                        this.render();
                        return;
                    } else {
                        this.log('现在不是该单位的行动轮次');
                        return;
                    }
                }

                if (this.selectedUnit && !unit && this.selectedUnit === this.currentUnit) {
                    this.moveUnitTo(gx, gy);
                    this.render();
                    return;
                }
            }

            updateUI() {
                const turnInfo = document.getElementById('turnInfo');
                if (this.gameOver) {
                    turnInfo.textContent = '游戏结束';
                    turnInfo.className = 'game-over';
                } else if (this.currentUnit && this.currentUnit.faction === 'player') {
                    turnInfo.textContent = `🛡️ 玩家行动 (第${this.turnCount}回合)`;
                    turnInfo.className = 'player-turn';
                } else {
                    turnInfo.textContent = `⚔️ 敌方行动 (第${this.turnCount}回合)`;
                    turnInfo.className = 'enemy-turn';
                }

                const unitInfo = document.getElementById('unitInfo');
                if (this.selectedUnit && !this.selectedUnit.dead && this.selectedUnit.faction === 'player') {
                    const u = this.selectedUnit;
                    unitInfo.innerHTML = `
                        <div class="info-line"><span class="label">位置:</span> (${u.x},${u.y}) 朝向${u.facing}</div>
                        <div class="info-line"><span class="label">体力:</span> ${u.hp}/${u.maxHp}</div>
                        <div class="info-line"><span class="label">行动点:</span> ${u.curAp}/${u.apMax}</div>
                        <div class="info-line"><span class="label">攻击力:</span> ${u.attackPower()}${!u.hasEngaged  ? ' (首次-2)' : ''}</div>
                        <div class="info-line"><span class="label">防御力:</span> ${u.defense(this.units)} (基础${u.defBase}+站位)</div>
                        <div class="info-line"><span class="label">普通攻击:</span> ${u.hasUsedNormalAttack ? '已用' : '可用'}</div>
                        <div class="info-line"><span class="label">奋力再击:</span> ${u.curAp>=5 ? '可用' : '不可用'}</div>
                        <div class="info-line" style="color:#ffd700;margin-top:8px;">${CLASS_TEMPLATES[u.cls].desc}</div>
                    `;
                } else {
                    unitInfo.innerHTML =
                        `<div style="color:#aaa;text-align:center;padding:20px;">${this.aiBusy ? '敌方思考中...' : (this.gameOver ? '战斗结束' : '等待行动')}</div>`;
                }

                const btnAttack = document.getElementById('btnAttack');
                const btnAllout = document.getElementById('btnAllout');
                const btnEnd = document.getElementById('btnEnd');
                const canAct = this.selectedUnit && !this.aiBusy && !this.gameOver && this.selectedUnit === this.currentUnit;

                btnAttack.disabled = !canAct || this.selectedUnit?.hasUsedNormalAttack || this.selectedUnit?.curAp < 3;
                btnAttack.classList.toggle('active', this.pendingMode === 'attack');
                btnAttack.textContent = this.pendingMode === 'attack' ? '【攻击中】' : '普通攻击';

                btnAllout.disabled = !canAct || this.selectedUnit?.hasUsedAlloutAttack || this.selectedUnit?.curAp < 5;
                btnAllout.classList.toggle('active', this.pendingMode === 'allout');
                btnAllout.textContent = this.pendingMode === 'allout' ? '【奋力中】' : '奋力再击';

                btnEnd.disabled = !this.selectedUnit || this.aiBusy;
            }

            // ==================== 绘制山峰 ====================
            drawMountain(ctx, rectX, rectY) {
                const size = CELL_SIZE;
                const cx = rectX + size / 2;
                
                // 山体阴影底
                ctx.fillStyle = '#2d3436';
                ctx.fillRect(rectX, rectY, size, size);
                
                // 主山体（深灰）
                ctx.fillStyle = '#636e72';
                ctx.beginPath();
                ctx.moveTo(cx, rectY + 6);
                ctx.lineTo(rectX + size - 4, rectY + size - 6);
                ctx.lineTo(rectX + 4, rectY + size - 6);
                ctx.closePath();
                ctx.fill();
                
                // 山体高光面（浅灰）
                ctx.fillStyle = '#7f8c8d';
                ctx.beginPath();
                ctx.moveTo(cx, rectY + 6);
                ctx.lineTo(cx + 2, rectY + 6);
                ctx.lineTo(rectX + size - 8, rectY + size - 6);
                ctx.lineTo(rectX + 4, rectY + size - 6);
                ctx.closePath();
                ctx.fill();
                
                // 山顶积雪
                ctx.fillStyle = '#dfe6e9';
                ctx.beginPath();
                ctx.moveTo(cx, rectY + 6);
                ctx.lineTo(cx + 9, rectY + 18);
                ctx.lineTo(cx - 9, rectY + 18);
                ctx.closePath();
                ctx.fill();
                
                // 山脊线
                ctx.strokeStyle = '#2d3436';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(cx, rectY + 6);
                ctx.lineTo(cx, rectY + 18);
                ctx.stroke();
                
                // 边框
                ctx.strokeStyle = '#505050';
                ctx.lineWidth = 1.5;
                ctx.strokeRect(rectX, rectY, size, size);
            }

            render() {
                const ctx = this.ctx;
                ctx.fillStyle = COLORS.BG;
                ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

                ctx.fillStyle = COLORS.BOARD_BG;
                ctx.fillRect(8, 8, this.canvas.width - 16, this.canvas.height - 16);

                ctx.strokeStyle = 'rgba(255,255,255,0.06)';
                ctx.lineWidth = 1;
                for (let i = 1; i < BOARD_H; i++) {
                    ctx.beginPath();
                    ctx.moveTo(10, i * CELL_SIZE + 8);
                    ctx.lineTo(this.canvas.width - 10, i * CELL_SIZE + 8);
                    ctx.stroke();
                }

                let moveCells = {};
                let atkCells = [];
                if (this.selectedUnit && !this.aiBusy && this.selectedUnit.faction === 'player' && !this.pendingMode) {
                    moveCells = this.getMoveCells(this.selectedUnit);
                }
                if (this.selectedUnit && !this.aiBusy) {
                    atkCells = this.getBaseAttackCells(this.selectedUnit);
                }

                for (let y = 0; y < BOARD_H; y++) {
                    for (let x = 0; x < BOARD_W; x++) {

                        const offsetX = 15, offsetY = 15;
                        const rectX = offsetX + x * CELL_SIZE;
                        const rectY = offsetY + y * CELL_SIZE;
                        const key = `${x},${y}`;

                        // ★ 障碍物绘制为山峰 ★
                        if (this.obstacles.has(key)) {
                            this.drawMountain(ctx, rectX, rectY);
                            continue;
                        }

                        // 基础地形色（草地/沙地/河流/桥）
                        let color = this.terrainColors[key] || COLORS.CELL;
                        
                        // 移动范围覆盖
                        if (key in moveCells && !this.pendingMode) color = '#1e5aa8';
                        // 攻击范围覆盖
                        if (atkCells.some(c => c[0] === x && c[1] === y)) color = '#9f2a2a';

                        ctx.fillStyle = color;
                        ctx.fillRect(rectX, rectY, CELL_SIZE, CELL_SIZE);

                        // 河流波纹效果
                        if (this.riverCells.has(key) && !this.bridgeCells.has(key)) {
                            ctx.strokeStyle = 'rgba(100, 180, 255, 0.3)';
                            ctx.lineWidth = 1;
                            const waveY = rectY + CELL_SIZE / 2 + Math.sin(x * 0.8 + y * 0.5) * 3;
                            ctx.beginPath();
                            ctx.moveTo(rectX + 4, waveY);
                            ctx.lineTo(rectX + CELL_SIZE - 4, waveY);
                            ctx.stroke();
                        }

                        // 桥梁纹理
                        if (this.bridgeCells.has(key)) {
                            ctx.strokeStyle = 'rgba(60, 40, 20, 0.4)';
                            ctx.lineWidth = 2;
                            for (let i = 1; i < 4; i++) {
                                ctx.beginPath();
                                ctx.moveTo(rectX + i * 12, rectY + 4);
                                ctx.lineTo(rectX + i * 12, rectY + CELL_SIZE - 4);
                                ctx.stroke();
                            }
                        }

                        if (this.currentUnit && this.currentUnit.x === x && this.currentUnit.y === y) {
                            ctx.strokeStyle = COLORS.CURRENT_TURN;
                            ctx.lineWidth = 4;
                            ctx.strokeRect(rectX + 2, rectY + 2, CELL_SIZE - 4, CELL_SIZE - 4);
                        }

                        if (this.selectedUnit && this.selectedUnit.x === x && this.selectedUnit.y === y) {
                            ctx.strokeStyle = '#ffd700';
                            ctx.lineWidth = 3;
                            ctx.strokeRect(rectX + 3, rectY + 3, CELL_SIZE - 6, CELL_SIZE - 6);
                        }

                        ctx.strokeStyle = COLORS.CELL_BORDER;
                        ctx.lineWidth = 1;
                        ctx.strokeRect(rectX, rectY, CELL_SIZE, CELL_SIZE);

                        // ★ 移动提示显示剩余AP ★
                        if (key in moveCells && key !== `${this.selectedUnit?.x},${this.selectedUnit?.y}`) {
                            const cost = moveCells[key];
                            const remainingAp = this.selectedUnit.curAp - cost;
                            ctx.fillStyle = '#ffee88';
                            ctx.font = 'bold 11px Microsoft YaHei';
                            ctx.textAlign = 'right';
                            ctx.fillText(`${remainingAp}`, rectX + CELL_SIZE - 4, rectY + CELL_SIZE - 4);
                            ctx.textAlign = 'left';
                        }

                        const unit = getUnitAt(this.units, x, y);
                        if (unit) {
                            this.drawUnit(ctx, unit, rectX + CELL_SIZE/2, rectY + CELL_SIZE/2);
                            this.drawUnitStats(ctx, unit, rectX, rectY);
                        }
                    }
                }

                this.drawAnimations();
            }

            drawUnit(ctx, unit, cx, cy) {
                let x = cx;
                let y = cy;
                let alpha = unit.dead ? Math.max(0, 1 - (Date.now() - unit.deathTime) / 900) : 1.0;

                if (alpha <= 0) return;

                if (unit.shakeTime > 0) {
                    const shake = Math.sin(unit.shakeTime * 55) * 4;
                    x += shake;
                    unit.shakeTime -= 0.018;
                }

                ctx.globalAlpha = alpha;

                const radius = 19;
                let color;
                if (unit.dead) {
                    color = unit.faction === 'player' ? '#2a2a3a' : '#3a2a2a';
                } else if (unit.acted) {
                    color = unit.faction === 'player' ? COLORS.PLAYER_ACTED : COLORS.ENEMY_ACTED;
                } else {
                    color = unit.faction === 'player' ? COLORS.PLAYER : COLORS.ENEMY;
                }

                ctx.shadowColor = 'rgba(0,0,0,0.7)';
                ctx.shadowBlur = 10;
                ctx.shadowOffsetX = 3;
                ctx.shadowOffsetY = 6;

                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();

                ctx.shadowBlur = 0;
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 0;

                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2.8;
                ctx.stroke();

                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 15px Microsoft YaHei';
                ctx.textAlign = 'center';
                const arrows = { up: '↑', down: '↓', left: '←', right: '→' };
                ctx.fillText(arrows[unit.facing] || '●', x, y - 7);

                ctx.font = '10px Microsoft YaHei';
                ctx.fillText(unit.name, x, y + 8);
                
                ctx.globalAlpha = 1.0;
                ctx.textAlign = 'left';
            }
            
            drawUnitStats(ctx, unit, rectX, rectY) {
                if (unit.dead) return;
                const atk = unit.attackPower();
                const def = unit.defense(this.units);
                const hp = unit.hp;
                const ap = unit.curAp;

                ctx.font = 'bold 14px Microsoft YaHei';
                ctx.textBaseline = 'middle';

                // ★ 左上角 - AP（蓝色）★
                ctx.fillStyle = '#3388ff';
                ctx.textAlign = 'left';
                ctx.fillText(ap, rectX + 4, rectY + 12);

                // ★ 右上角 - 攻击力（红色）★
                ctx.fillStyle = '#ff3333';
                ctx.textAlign = 'right';
                ctx.fillText(atk, rectX + CELL_SIZE - 4, rectY + 12);

                // 左下角 - HP（绿色）
                ctx.fillStyle = '#00ff66';
                ctx.textAlign = 'left';
                ctx.fillText(hp, rectX + 4, rectY + CELL_SIZE - 6);

                // 右下角 - 防御力（黄色）
                ctx.fillStyle = '#ffdd00';
                ctx.textAlign = 'right';
                ctx.fillText(def, rectX + CELL_SIZE - 4, rectY + CELL_SIZE - 6);
            }

            drawAnimations() {
                const ctx = this.ctx;
                ctx.save();
                ctx.textAlign = 'center';
                ctx.font = 'bold 18px Microsoft YaHei';

                for (const a of this.animations) {
                    const progress = Math.min(1, a.time / a.duration);
                    const alpha = Math.max(0, 1 - progress * 1.3);

                    if (a.type === 'damage') {
                        const yOffset = -progress * 68;
                        ctx.fillStyle = `rgba(255, 80, 80, ${alpha})`;
                        ctx.shadowColor = '#ff2222';
                        ctx.shadowBlur = 15;
                        ctx.fillText(`-${a.value}`, a.screenX, a.screenY + yOffset);
                    } else if (a.type === 'attackEffect') {
                        const size = 12 + progress * 42;
                        ctx.strokeStyle = `rgba(255, 220, 100, ${1 - progress * 1.8})`;
                        ctx.lineWidth = 5 - progress * 4;
                        ctx.beginPath();
                        ctx.arc(a.screenX, a.screenY, size, 0, Math.PI * 2);
                        ctx.stroke();
                    }
                }
                ctx.restore();
            }
        }

        const game = new Game();
    </script>
</body>
</html>'''

with open('/mnt/agents/output/san-guo-zhi-demo-updated.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

print("文件已保存到 /mnt/agents/output/san-guo-zhi-demo-updated.html")
