import streamlit as st

ARCADE_RACER_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>ARCADE RACER - Highway Strike</title>
    <style>
        body {
            background: #010608;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            font-family: 'Courier New', 'VT323', monospace;
        }
        .arcade-machine {
            background: #1b1e23;
            border-radius: 40px 40px 20px 20px;
            padding: 20px 30px 25px;
            box-shadow: 0 20px 30px rgba(0,0,0,0.7), inset 0 1px 4px rgba(255,255,200,0.2);
            border-bottom: 8px solid #ffb347;
        }
        canvas {
            display: block;
            margin: 0 auto;
            border-radius: 16px;
            box-shadow: 0 0 0 3px #f2d648, 0 10px 20px black;
            cursor: none;
        }
        .dashboard {
            display: flex;
            justify-content: space-between;
            background: #0e0f17cc;
            backdrop-filter: blur(5px);
            margin-top: 15px;
            padding: 8px 25px;
            border-radius: 60px;
            color: #feda7a;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .button-panel {
            display: flex;
            justify-content: center;
            gap: 25px;
            margin: 15px 0 5px;
        }
        button {
            background: #3a2819;
            border: none;
            font-family: monospace;
            font-weight: bold;
            font-size: 1rem;
            padding: 6px 24px;
            border-radius: 40px;
            color: #ffcd94;
            cursor: pointer;
            transition: 0.05s linear;
            box-shadow: 0 4px 0 #1e150c;
        }
        button:active {
            transform: translateY(2px);
            box-shadow: 0 1px 0 #1e150c;
        }
        .controls {
            text-align: center;
            font-size: 0.7rem;
            color: #7c9e8a;
            margin-top: 10px;
        }
        @keyframes neon {
            0% { text-shadow: 0 0 2px #ffb347; }
            100% { text-shadow: 0 0 8px #ff7733; }
        }
        .arcade-title {
            text-align: center;
            font-size: 1.8rem;
            letter-spacing: 4px;
            margin-bottom: 8px;
            color: #ffc857;
            animation: neon 1s infinite alternate;
        }
    </style>
</head>
<body>
<div>
    <div class="arcade-machine">
        <div class="arcade-title">HIGHWAY STRIKE</div>
        <canvas id="gameCanvas" width="500" height="650"></canvas>
        <div class="dashboard">
            <span>🏁 SCORE: <span id="scoreArcade">0</span></span>
            <span>⚡ SPEED: <span id="speedArcade">180</span> km/h</span>
            <span>🏆 BEST: <span id="bestArcade">0</span></span>
        </div>
        <div class="button-panel">
            <button id="resetArcadeBtn">🔄 NEW GAME</button>
        </div>
        <div class="controls">
            🎮 ← →  ou  A/D  –  Évite les voitures, attrape les étoiles (⭐) pour du turbo !
        </div>
    </div>
</div>

<script>
    (function(){
        // ---------- CANVAS ----------
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        
        // ---------- DIMENSIONS JEU (voie virtuelle) ----------
        const LANE_COUNT = 3;
        const LANE_WIDTH = canvas.width / LANE_COUNT;  // ~166.66
        // Positions X des 3 voies (centrées)
        const LANE_POS = [
            LANE_WIDTH/2 - 20,
            LANE_WIDTH + LANE_WIDTH/2 - 20,
            LANE_WIDTH*2 + LANE_WIDTH/2 - 20
        ];
        
        // TAILLE JOUEUR & ENNEMIS
        const CAR_W = 44;
        const CAR_H = 70;
        
        // JOUEUR
        let player = {
            x: LANE_POS[1],
            y: canvas.height - 90,
            w: CAR_W,
            h: CAR_H,
            lane: 1
        };
        
        // ENNEMIS (voitures ennemies)
        let enemies = [];
        const ENEMY_W = 46;
        const ENEMY_H = 72;
        
        // POWER-UPS (étoiles)
        let stars = [];
        const STAR_SIZE = 24;
        
        // ÉTAT JEU
        let gameRunning = true;
        let score = 0;
        let bestScore = localStorage.getItem('arcadeBest') ? parseInt(localStorage.getItem('arcadeBest')) : 0;
        document.getElementById('bestArcade').innerText = bestScore;
        let speed = 180;
        let baseSpeed = 180;
        
        // Gestion des frames / spawn
        let frameCounter = 0;
        let enemySpawnDelay = 45;
        let starSpawnDelay = 70;
        
        // Effet de vitesse / particules (simulé)
        let roadOffset = 0;
        
        // ---------- CLAVIER ----------
        let keys = { ArrowLeft: false, ArrowRight: false, KeyA: false, KeyD: false };
        window.addEventListener('keydown', (e) => {
            if(keys.hasOwnProperty(e.code)) {
                keys[e.code] = true;
                e.preventDefault();
            }
        });
        window.addEventListener('keyup', (e) => {
            if(keys.hasOwnProperty(e.code)) keys[e.code] = false;
        });
        
        function movePlayer() {
            if (!gameRunning) return;
            let newLane = player.lane;
            if (keys.ArrowLeft || keys.KeyA) newLane--;
            if (keys.ArrowRight || keys.KeyD) newLane++;
            newLane = Math.min(2, Math.max(0, newLane));
            if (newLane !== player.lane) {
                player.lane = newLane;
                player.x = LANE_POS[player.lane];
            }
        }
        
        // ---------- SPAWN ----------
        function spawnEnemy() {
            let lane = Math.floor(Math.random() * LANE_COUNT);
            enemies.push({
                x: LANE_POS[lane],
                y: -ENEMY_H,
                w: ENEMY_W,
                h: ENEMY_H,
                lane: lane,
                counted: false
            });
        }
        
        function spawnStar() {
            let lane = Math.floor(Math.random() * LANE_COUNT);
            stars.push({
                x: LANE_POS[lane] + (CAR_W/2 - STAR_SIZE/2),
                y: -STAR_SIZE,
                w: STAR_SIZE,
                h: STAR_SIZE,
                lane: lane
            });
        }
        
        // ---------- MISE À JOUR ----------
        function updateGame() {
            if (!gameRunning) return;
            
            // Augmentation progressive de la vitesse en fonction du score
            let currentSpeed = baseSpeed + Math.floor(score / 400);
            if (currentSpeed > 320) currentSpeed = 320;
            document.getElementById('speedArcade').innerText = currentSpeed;
            let enemySpeed = (currentSpeed / 60) * 2.2;  // ~ 6 à 12 pixels/frame
            
            // Déplacement ennemis
            for (let e of enemies) e.y += enemySpeed;
            enemies = enemies.filter(e => e.y < canvas.height);
            
            // Déplacement étoiles
            for (let s of stars) s.y += enemySpeed * 0.9;
            stars = stars.filter(s => s.y < canvas.height);
            
            // Spawn ennemis (fréquence augmente avec vitesse)
            let spawnRate = Math.max(18, enemySpawnDelay - Math.floor(currentSpeed / 35));
            frameCounter++;
            if (frameCounter >= spawnRate) {
                frameCounter = 0;
                spawnEnemy();
            }
            
            // Spawn étoiles (power-up)
            if (Math.random() < 0.008 && stars.length < 3) {
                spawnStar();
            }
            
            // COLLISION avec ennemis
            for (let i=0; i<enemies.length; i++) {
                let e = enemies[i];
                if (player.x < e.x+e.w && player.x+player.w > e.x &&
                    player.y < e.y+e.h && player.y+player.h > e.y) {
                    gameRunning = false;
                    if (score > bestScore) {
                        bestScore = score;
                        localStorage.setItem('arcadeBest', bestScore);
                        document.getElementById('bestArcade').innerText = bestScore;
                    }
                    return;
                }
            }
            
            // COLLECTION étoiles (power-up : +50 points et boost temporaire de score)
            for (let i=0; i<stars.length; i++) {
                let s = stars[i];
                if (player.x < s.x+s.w && player.x+player.w > s.x &&
                    player.y < s.y+s.h && player.y+player.h > s.y) {
                    stars.splice(i,1);
                    score += 50;
                    document.getElementById('scoreArcade').innerText = Math.floor(score);
                    // effet visuel de boost (on augmente le score plus vite pendant 1 sec, mais simplifié)
                    if (score > bestScore) {
                        bestScore = score;
                        localStorage.setItem('arcadeBest', bestScore);
                        document.getElementById('bestArcade').innerText = bestScore;
                    }
                    break;
                }
            }
            
            // Incrémenter le score au fil du temps (survie)
            score += 0.35;
            document.getElementById('scoreArcade').innerText = Math.floor(score);
            // Mise à jour best en cours de route
            if (Math.floor(score) > bestScore) {
                bestScore = Math.floor(score);
                localStorage.setItem('arcadeBest', bestScore);
                document.getElementById('bestArcade').innerText = bestScore;
            }
        }
        
        // ---------- DESSIN ROUTE ARCADE (vue de dessus style 3D simplifié) ----------
        function drawRoad() {
            // Asphalte
            ctx.fillStyle = '#141e1a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Lignes de voie animées (défilement)
            let step = 45;
            roadOffset = (roadOffset + 5) % step;
            ctx.setLineDash([20, 25]);
            ctx.lineWidth = 4;
            for (let i = 1; i < LANE_COUNT; i++) {
                ctx.beginPath();
                ctx.moveTo(i * LANE_WIDTH, 0);
                ctx.lineTo(i * LANE_WIDTH, canvas.height);
                ctx.strokeStyle = '#ffefb0';
                ctx.stroke();
            }
            ctx.setLineDash([]);
            
            // Bandes latérales réfléchissantes
            ctx.strokeStyle = '#fcb43a';
            ctx.lineWidth = 4;
            ctx.strokeRect(5, 5, canvas.width-10, canvas.height-10);
            
            // Marqueurs centraux (effet de vitesse)
            for (let y = roadOffset - step; y < canvas.height + step; y += step) {
                ctx.fillStyle = '#ffc285';
                ctx.fillRect(canvas.width/2 - 8, y, 16, 20);
            }
            
            // Petites particules de vitesse (lignes blanches horizontales)
            for (let i = 0; i < 12; i++) {
                let randY = (Date.now() * 0.01 + i * 37) % canvas.height;
                ctx.fillStyle = '#eef5ff';
                ctx.fillRect(canvas.width/2 - 40 + Math.sin(i)*10, randY, 6, 2);
                ctx.fillRect(canvas.width/2 + 30 + Math.cos(i)*8, randY, 6, 2);
            }
        }
        
        // dessin voiture joueur (style rétro)
        function drawPlayer() {
            // carrosserie
            ctx.fillStyle = '#3ed6ff';
            ctx.shadowBlur = 0;
            ctx.beginPath();
            ctx.roundRect(player.x, player.y, CAR_W, CAR_H, 12);
            ctx.fill();
            ctx.fillStyle = '#142b33';
            ctx.beginPath();
            ctx.roundRect(player.x+8, player.y+12, CAR_W-16, 30, 8);
            ctx.fill();
            // phares
            ctx.fillStyle = '#fff0a0';
            ctx.fillRect(player.x+5, player.y+CAR_H-14, 8, 8);
            ctx.fillRect(player.x+CAR_W-13, player.y+CAR_H-14, 8, 8);
            // néon
            ctx.fillStyle = '#ff8744';
            ctx.fillRect(player.x+2, player.y+CAR_H-6, CAR_W-4, 4);
        }
        
        function drawEnemy(e) {
            let grad = ctx.createLinearGradient(e.x, e.y, e.x+10, e.y+ENEMY_H);
            grad.addColorStop(0, '#c0442a');
            grad.addColorStop(1, '#8f2a14');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.roundRect(e.x, e.y, ENEMY_W, ENEMY_H, 10);
            ctx.fill();
            ctx.fillStyle = '#382016';
            ctx.beginPath();
            ctx.roundRect(e.x+7, e.y+12, ENEMY_W-14, 28, 6);
            ctx.fill();
            // calandre
            ctx.fillStyle = '#a0a0a0';
            ctx.fillRect(e.x+12, e.y+ENEMY_H-18, 22, 8);
        }
        
        function drawStar(s) {
            ctx.shadowBlur = 10;
            ctx.shadowColor = '#f7d44a';
            ctx.fillStyle = '#ffdf70';
            ctx.beginPath();
            ctx.arc(s.x + STAR_SIZE/2, s.y + STAR_SIZE/2, STAR_SIZE/2, 0, Math.PI*2);
            ctx.fill();
            ctx.fillStyle = '#000000';
            ctx.font = 'bold 18px monospace';
            ctx.fillText('⭐', s.x+4, s.y+18);
            ctx.shadowBlur = 0;
        }
        
        function drawGameOverlay() {
            if (!gameRunning) {
                ctx.font = 'bold 32px monospace';
                ctx.fillStyle = '#ffae70';
                ctx.shadowBlur = 0;
                ctx.fillText('GAME OVER', canvas.width/2-110, canvas.height/2-40);
                ctx.font = '18px monospace';
                ctx.fillStyle = '#ccccaa';
                ctx.fillText('Appuie sur NEW GAME', canvas.width/2-100, canvas.height/2+30);
            }
        }
        
        // Helper arrondi
        if (!CanvasRenderingContext2D.prototype.roundRect) {
            CanvasRenderingContext2D.prototype.roundRect = function(x,y,w,h,r) {
                if (w < 2*r) r = w/2;
                if (h < 2*r) r = h/2;
                this.moveTo(x+r,y);
                this.lineTo(x+w-r,y);
                this.quadraticCurveTo(x+w,y,x+w,y+r);
                this.lineTo(x+w,y+h-r);
                this.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
                this.lineTo(x+r,y+h);
                this.quadraticCurveTo(x,y+h,x,y+h-r);
                this.lineTo(x,y+r);
                this.quadraticCurveTo(x,y,x+r,y);
                return this;
            };
        }
        
        function render() {
            drawRoad();
            for(let e of enemies) drawEnemy(e);
            for(let s of stars) drawStar(s);
            drawPlayer();
            drawGameOverlay();
            // affiche petite jauge de vitesse (arcade)
            let speedPercent = Math.min(1, (parseInt(document.getElementById('speedArcade').innerText) / 300));
            ctx.fillStyle = '#ffa047';
            ctx.fillRect(15, 25, 120 * speedPercent, 12);
            ctx.strokeStyle = '#ffde9e';
            ctx.strokeRect(15, 25, 120, 12);
        }
        
        // ---------- RESET ----------
        function resetGame() {
            gameRunning = true;
            score = 0;
            document.getElementById('scoreArcade').innerText = "0";
            enemies = [];
            stars = [];
            frameCounter = 0;
            player.lane = 1;
            player.x = LANE_POS[1];
            baseSpeed = 180;
            document.getElementById('speedArcade').innerText = "180";
        }
        
        // ---------- BOUCLE PRINCIPALE ----------
        function gameLoop() {
            movePlayer();
            updateGame();
            render();
            requestAnimationFrame(gameLoop);
        }
        
        document.getElementById('resetArcadeBtn').addEventListener('click', () => resetGame());
        resetGame();
        gameLoop();
    })();
</script>
</body>
</html>
"""

st.set_page_config(page_title="ARCADE RACER - Highway Strike", layout="centered", page_icon="🏎️")
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(145deg, #021010, #000000);
        }
        .inline-title {
            text-align: center;
            font-family: 'Courier New', monospace;
            font-size: 2.5rem;
            color: #ffbc6a;
            margin-top: -30px;
        }
    </style>
    <div class="inline-title">🕹️ ARCADE RACER 🕹️</div>
""", unsafe_allow_html=True)

st.components.v1.html(ARCADE_RACER_HTML, height=800, scrolling=False)
st.caption("🎯 Évite les voitures rouges, collecte les ⭐ pour +50 points. La vitesse augmente avec le score. Ambiance salle de jeux !")
