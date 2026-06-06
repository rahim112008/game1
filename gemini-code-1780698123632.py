import streamlit as st

GAME_WITH_POWERUPS = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Racer's Legacy - Turbo Edition</title>
    <style>
        * { user-select: none; touch-action: pan-y pinch-zoom; }
        body {
            background: radial-gradient(ellipse at 30% 40%, #021010, #000000);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: 'Courier New', 'VT323', monospace;
            margin: 0;
            padding: 20px;
        }
        .game-container {
            background: #0f211c;
            border-radius: 36px;
            padding: 15px 20px 20px;
            box-shadow: 0 20px 30px rgba(0,0,0,0.6), inset 0 1px 3px rgba(255,255,200,0.2);
        }
        canvas {
            display: block;
            margin: 0 auto;
            border-radius: 20px;
            box-shadow: 0 0 0 4px #f7d98c, 0 12px 28px black;
            cursor: none;
        }
        .info-panel {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            background: #03100cee;
            backdrop-filter: blur(4px);
            margin: 12px 0 8px;
            padding: 8px 15px;
            border-radius: 60px;
            gap: 10px;
        }
        .info-panel div {
            background: #1e3d33;
            padding: 4px 14px;
            border-radius: 32px;
            font-weight: bold;
            color: #ffe0a3;
        }
        .powerup-status {
            background: #2a2418;
            font-size: 0.8rem;
        }
        button {
            background: #d68b30;
            border: none;
            font-family: monospace;
            font-weight: bold;
            font-size: 1rem;
            padding: 6px 20px;
            border-radius: 60px;
            cursor: pointer;
            color: #1f2f1a;
            transition: 0.05s linear;
            box-shadow: 0 3px 0 #7a3e0e;
        }
        button:active { transform: translateY(2px); box-shadow: 0 1px 0 #7a3e0e; }
        .controls {
            text-align: center;
            margin-top: 12px;
            color: #c0e0c0;
            font-size: 0.75rem;
        }
    </style>
</head>
<body>
<div>
    <div class="game-container">
        <canvas id="gameCanvas" width="550" height="650"></canvas>
        <div class="info-panel">
            <div>🏆 NIV <span id="levelVal">1</span>/10</div>
            <div>🎯 OBJ <span id="objVal">0</span></div>
            <div>🏁 SCORE <span id="scoreVal">0</span></div>
            <div class="powerup-status">⚡ <span id="powerupLabel">Aucun</span></div>
        </div>
        <div style="display: flex; justify-content: center; gap: 20px;">
            <button id="resetStoryBtn">🔄 Reprendre l'histoire</button>
        </div>
        <div class="controls">
            🚗 ← →  ou A/D – Attrape les POWER-UPS (★) pour des bonus !
        </div>
    </div>
</div>

<script>
    (function(){
        // ---------- CONFIGURATION CANVAS ----------
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const LANE_COUNT = 3;
        const LANE_WIDTH = canvas.width / LANE_COUNT;
        const CAR_W = 46, CAR_H = 74;
        const LANE_POS = [LANE_WIDTH/2, LANE_WIDTH + LANE_WIDTH/2, LANE_WIDTH*2 + LANE_WIDTH/2];
        
        // ---------- JOUEUR ----------
        let player = {
            x: LANE_POS[1] - CAR_W/2,
            y: canvas.height - 100,
            w: CAR_W, h: CAR_H,
            lane: 1,
            invincible: false,
            invincibleEnd: 0
        };
        
        // ---------- ENNEMIS ----------
        let enemies = [];
        const ENEMY_W = 48, ENEMY_H = 76;
        
        // ---------- POWER-UPS ----------
        let powerups = [];
        const POWER_SIZE = 28;
        
        // ---------- ÉTAT JEU & HISTOIRE ----------
        let currentLevel = 1;
        let levelObjectives = {1:10,2:18,3:28,4:40,5:55,6:70,7:85,8:100,9:120,10:150};
        let currentScore = 0;
        let gameRunning = true;
        let victory = false;
        
        // Variables power-up actifs (effets)
        let activeBoost = false;
        let boostEnd = 0;
        let activeSlow = false;
        let slowEnd = 0;
        let activeShield = false;
        let shieldEnd = 0;
        
        // Difficulté dynamique
        let baseEnemySpeed = 4.6;
        let spawnDelayFrames = 36;
        let frameCounter = 0;
        
        // Dialogues
        const dialogues = {
            1:"Niveau 1 : Échauffement. 10 dépassements !",
            2:"Niveau 2 : Les rookies débarquent. 18 évitements.",
            3:"Niveau 3 : Trafic dense. 28 dépassements.",
            4:"Niveau 4 : Pluie imminente. 40 voitures à éviter.",
            5:"Niveau 5 : Demi-finale. 55 dépassements !",
            6:"Niveau 6 : Zone dangereuse. 70 adversaires.",
            7:"Niveau 7 : Course nocturne. Objectif 85.",
            8:"Niveau 8 : Poursuite policière. 100 dépassements.",
            9:"Niveau 9 : Avant la finale. 120 adversaires !",
            10:"NIVEAU FINAL : Affronte Victor et ses sbires. 150 dépassements !"
        };
        
        function updateUI() {
            document.getElementById('levelVal').innerText = currentLevel;
            let remaining = levelObjectives[currentLevel] - currentScore;
            if(remaining<0) remaining=0;
            document.getElementById('objVal').innerText = remaining;
            document.getElementById('scoreVal').innerText = currentScore;
            let powerText = "";
            if(activeShield) powerText = "🛡️ BOUCLIER";
            else if(activeBoost) powerText = "⚡ BOOST";
            else if(activeSlow) powerText = "🐢 SLOW";
            else powerText = "—";
            document.getElementById('powerupLabel').innerText = powerText;
            let msgDiv = document.getElementById('storyMsg');
            if(msgDiv) {
                if(victory) msgDiv.innerText = "🏆 VICTOIRE ! Tu as remporté la légende ! 🏆";
                else if(!gameRunning) msgDiv.innerText = "💥 CRASH... Relance l'histoire.";
                else msgDiv.innerText = dialogues[currentLevel] || "Continue !";
            }
        }
        
        // Ajout d'un élément storyMsg (création dynamique)
        let storyDiv = document.createElement('div');
        storyDiv.id = 'storyMsg';
        storyDiv.style.background = '#051f1a';
        storyDiv.style.borderRadius = '24px';
        storyDiv.style.padding = '8px';
        storyDiv.style.marginTop = '10px';
        storyDiv.style.textAlign = 'center';
        storyDiv.style.color = '#ffdfaa';
        storyDiv.style.fontSize = '0.85rem';
        document.querySelector('.game-container').appendChild(storyDiv);
        
        // ---------- CLAVIER ----------
        let keys = {ArrowLeft:false,ArrowRight:false,KeyA:false,KeyD:false};
        window.addEventListener('keydown', (e) => {
            if(keys.hasOwnProperty(e.code)) { keys[e.code]=true; e.preventDefault(); }
        });
        window.addEventListener('keyup', (e) => { if(keys.hasOwnProperty(e.code)) keys[e.code]=false; });
        
        function movePlayer() {
            if(!gameRunning || victory) return;
            let newLane = player.lane;
            if(keys.ArrowLeft || keys.KeyA) newLane--;
            if(keys.ArrowRight || keys.KeyD) newLane++;
            newLane = Math.min(2, Math.max(0, newLane));
            if(newLane !== player.lane) {
                player.lane = newLane;
                player.x = LANE_POS[player.lane] - CAR_W/2;
            }
        }
        
        // ---------- POWER-UPS : spawn ----------
        function trySpawnPowerup() {
            if(Math.random() > 0.012) return; // 1.2% par frame
            let lane = Math.floor(Math.random() * LANE_COUNT);
            let xPos = LANE_POS[lane] - POWER_SIZE/2;
            let types = ['boost', 'slow', 'shield'];
            let randType = types[Math.floor(Math.random()*3)];
            powerups.push({
                x: xPos, y: -POWER_SIZE, w: POWER_SIZE, h: POWER_SIZE,
                type: randType, lane: lane
            });
        }
        
        // Gestion collection power-up
        function applyPowerup(type) {
            let now = Date.now();
            if(type === 'boost') {
                activeBoost = true; boostEnd = now + 3000;
                activeSlow = false; activeShield = false;
            } else if(type === 'slow') {
                activeSlow = true; slowEnd = now + 3500;
                activeBoost = false; activeShield = false;
            } else if(type === 'shield') {
                activeShield = true; shieldEnd = now + 4000;
                activeBoost = false; activeSlow = false;
                player.invincible = true;
                setTimeout(()=> { if(!activeShield) player.invincible = false; }, 4000);
            }
            updateUI();
            setTimeout(() => {
                if(activeBoost && Date.now() >= boostEnd) { activeBoost = false; updateUI(); }
                if(activeSlow && Date.now() >= slowEnd) { activeSlow = false; updateUI(); }
                if(activeShield && Date.now() >= shieldEnd) { activeShield = false; player.invincible = false; updateUI(); }
            }, 4000);
        }
        
        // ---------- SPAWN ENNEMIS ----------
        function spawnEnemy() {
            let lane = Math.floor(Math.random() * LANE_COUNT);
            let isVictor = (currentLevel === 10 && Math.random() < 0.2);
            enemies.push({
                x: LANE_POS[lane] - ENEMY_W/2, y: -ENEMY_H,
                w: ENEMY_W, h: ENEMY_H, lane: lane,
                isVictor: isVictor, counted: false
            });
        }
        
        // ---------- MISE À JOUR LOGIQUE ----------
        function updateGame() {
            if(!gameRunning || victory) return;
            
            // vitesse ennemis
            let speedMulti = (currentLevel-1) * 0.45;
            let enemySpeed = baseEnemySpeed + speedMulti;
            if(activeSlow) enemySpeed *= 0.55;
            
            for(let e of enemies) e.y += enemySpeed;
            enemies = enemies.filter(e => e.y < canvas.height);
            
            // spawn ennemis
            let spawnSpd = Math.max(20, spawnDelayFrames - Math.floor(currentScore/25) - Math.floor(currentLevel/2));
            frameCounter++;
            if(frameCounter >= spawnSpd) {
                frameCounter = 0;
                spawnEnemy();
            }
            
            // spawn power-ups
            trySpawnPowerup();
            for(let p of powerups) p.y += 4.8;
            powerups = powerups.filter(p => p.y < canvas.height);
            
            // COLLECT power-ups
            for(let i=0; i<powerups.length; i++) {
                let p = powerups[i];
                if(player.x < p.x+p.w && player.x+player.w > p.x &&
                   player.y < p.y+p.h && player.y+player.h > p.y) {
                    applyPowerup(p.type);
                    powerups.splice(i,1);
                    break;
                }
            }
            
            // collision avec ennemis (sauf si invincible)
            for(let i=0; i<enemies.length; i++) {
                let e = enemies[i];
                if(player.x < e.x+e.w && player.x+player.w > e.x &&
                   player.y < e.y+e.h && player.y+player.h > e.y) {
                    if(!player.invincible && !activeShield) {
                        gameRunning = false;
                        updateUI();
                        return;
                    } else {
                        // si bouclier actif, détruit l'ennemi touché
                        enemies.splice(i,1);
                        i--;
                    }
                }
            }
            
            // Ajout score pour ennemis sortis
            for(let i=0; i<enemies.length; i++) {
                if(!enemies[i].counted && enemies[i].y + enemies[i].h >= canvas.height) {
                    enemies[i].counted = true;
                    currentScore++;
                    updateUI();
                    // vérifier passage niveau
                    if(currentScore >= levelObjectives[currentLevel] && currentLevel < 10) {
                        currentLevel++;
                        currentScore = 0;
                        enemies = [];
                        powerups = [];
                        frameCounter = 0;
                        gameRunning = true;
                        // bonus: désactive effets spéciaux
                        activeBoost=false; activeSlow=false; activeShield=false; player.invincible=false;
                        updateUI();
                        let msg = dialogues[currentLevel];
                        document.getElementById('storyMsg').innerText = msg;
                        setTimeout(()=>updateUI(),100);
                    } else if(currentLevel === 10 && currentScore >= levelObjectives[10]) {
                        victory = true;
                        gameRunning = false;
                        updateUI();
                    }
                }
            }
            // gestion boost : effet sur vitesse joueur (visuel seulement, mouvement identique)
            if(activeBoost) {
                // on pourrait accélérer les frames de déplacement mais garder réactif
            }
        }
        
        // ---------- DESSIN SPECTACULAIRE (sprites & effets) ----------
        function drawRoad() {
            const grad = ctx.createLinearGradient(0,0,0,canvas.height);
            grad.addColorStop(0,'#1f3a30');
            grad.addColorStop(1,'#0b231d');
            ctx.fillStyle=grad;
            ctx.fillRect(0,0,canvas.width,canvas.height);
            ctx.strokeStyle = '#ffecb3';
            ctx.lineWidth=4;
            ctx.setLineDash([25,40]);
            for(let i=1;i<LANE_COUNT;i++){
                ctx.beginPath();
                ctx.moveTo(i*LANE_WIDTH,0);
                ctx.lineTo(i*LANE_WIDTH,canvas.height);
                ctx.stroke();
            }
            ctx.setLineDash([]);
            ctx.strokeStyle='#ebb45e';
            ctx.lineWidth=5;
            ctx.strokeRect(12,12,canvas.width-24,canvas.height-24);
            // marquage central
            for(let i=0;i<20;i++){
                ctx.fillStyle='#fae472';
                ctx.fillRect(canvas.width/2-6, (i*45 + Date.now()*0.2)%canvas.height, 12, 22);
            }
        }
        
        function drawPlayerCar() {
            // effet boost : lueur orange
            if(activeBoost) ctx.shadowBlur=15, ctx.shadowColor='#ffaa44';
            ctx.fillStyle='#3cc9ff';
            ctx.beginPath();
            ctx.roundRect(player.x, player.y, CAR_W, CAR_H, 12);
            ctx.fill();
            ctx.fillStyle='#162b38';
            ctx.beginPath();
            ctx.roundRect(player.x+7, player.y+14, CAR_W-14, 30, 8);
            ctx.fill();
            ctx.fillStyle='#ffcf7a';
            ctx.fillRect(player.x+5, player.y+66, 10,8);
            ctx.fillRect(player.x+CAR_W-15, player.y+66,10,8);
            ctx.shadowBlur=0;
            if(activeShield){
                ctx.beginPath();
                ctx.arc(player.x+CAR_W/2, player.y+CAR_H/2, CAR_W/1.8, 0, Math.PI*2);
                ctx.strokeStyle='#6ef0ff';
                ctx.lineWidth=3;
                ctx.stroke();
            }
        }
        
        function drawEnemyCar(e){
            if(e.isVictor){
                ctx.fillStyle='#181818';
                ctx.shadowBlur=6;
                ctx.shadowColor='#ff4422';
            } else {
                let grad = ctx.createLinearGradient(e.x, e.y, e.x+10, e.y+ENEMY_H);
                grad.addColorStop(0,'#da4a2e');
                grad.addColorStop(1,'#a1230c');
                ctx.fillStyle=grad;
            }
            ctx.beginPath();
            ctx.roundRect(e.x, e.y, ENEMY_W, ENEMY_H, 10);
            ctx.fill();
            ctx.fillStyle='#3d251c';
            ctx.beginPath();
            ctx.roundRect(e.x+7, e.y+12, ENEMY_W-14, 28, 6);
            ctx.fill();
            if(e.isVictor){
                ctx.fillStyle='#ffaa55';
                ctx.font='bold 18px monospace';
                ctx.fillText("V", e.x+18, e.y+48);
            }
            ctx.shadowBlur=0;
        }
        
        function drawPowerup(p){
            ctx.shadowBlur=8;
            ctx.shadowColor='#ffdd77';
            ctx.fillStyle = p.type==='boost' ? '#7aff87' : (p.type==='slow' ? '#ffd966' : '#6ac8ff');
            ctx.beginPath();
            ctx.arc(p.x+POWER_SIZE/2, p.y+POWER_SIZE/2, POWER_SIZE/2, 0, Math.PI*2);
            ctx.fill();
            ctx.fillStyle='#000000aa';
            ctx.font = 'bold 20px monospace';
            let symbol = p.type==='boost' ? '⚡' : (p.type==='slow' ? '🐢' : '🛡️');
            ctx.fillText(symbol, p.x+6, p.y+22);
            ctx.shadowBlur=0;
        }
        
        function drawGameMessages(){
            if(!gameRunning && !victory){
                ctx.font='bold 34px monospace';
                ctx.fillStyle='#ffbb77';
                ctx.shadowBlur=0;
                ctx.fillText('GAME OVER', canvas.width/2-120, canvas.height/2-50);
            } else if(victory){
                ctx.font='28px monospace';
                ctx.fillStyle='#fde16d';
                ctx.fillText('LÉGENDE DE LA ROUTE', canvas.width/2-150, canvas.height/2-30);
                ctx.font='18px monospace';
                ctx.fillStyle='#c3f0d2';
                ctx.fillText('Garage sauvé - Crédits finaux', canvas.width/2-120, canvas.height/2+40);
            }
        }
        
        function render() {
            drawRoad();
            for(let e of enemies) drawEnemyCar(e);
            for(let p of powerups) drawPowerup(p);
            drawPlayerCar();
            drawGameMessages();
            ctx.font='bold 14px monospace';
            ctx.fillStyle='#ffefb0';
            ctx.fillText('BOOST:'+(activeBoost?'ON':'OFF')+' | SLOW:'+(activeSlow?'ON':'OFF'), 15, 45);
        }
        
        // ---------- RESET COMPLET ----------
        function fullReset() {
            gameRunning = true;
            victory = false;
            currentLevel = 1;
            currentScore = 0;
            enemies = [];
            powerups = [];
            frameCounter = 0;
            activeBoost = false; activeSlow = false; activeShield = false; player.invincible = false;
            player.lane = 1;
            player.x = LANE_POS[1] - CAR_W/2;
            updateUI();
            document.getElementById('storyMsg').innerText = dialogues[1];
        }
        
        // Animation
        function gameLoop() {
            movePlayer();
            updateGame();
            render();
            requestAnimationFrame(gameLoop);
        }
        
        document.getElementById('resetStoryBtn').addEventListener('click', () => fullReset());
        fullReset();
        gameLoop();
    })();
</script>
</body>
</html>
"""

st.set_page_config(page_title="Racer's Legacy Turbo - 10 niveaux & power-ups", page_icon="🏎️💨", layout="centered")
st.markdown("<h1 style='text-align:center; color:#ffbc6e;'>🏁 RACER'S LEGACY – TURBO EDITION 🏁</h1>", unsafe_allow_html=True)
st.components.v1.html(GAME_WITH_POWERUPS, height=820, scrolling=False)
st.markdown("🎮 **Nouveautés :** 10 niveaux, 3 power-ups (⚡Boost, 🐢Slow, 🛡️Bouclier), graphismes améliorés avec effets de lumière. Utilise les flèches ou A/D.")
