import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION DE LA PAGE CLOUD ---
st.set_page_config(
    page_title="L'Odyssée des 7 Mondes",
    page_icon="🐉",
    layout="wide"
)

st.markdown("""
    <style>
    .main-title { text-align: center; color: #FF4B4B; font-family: 'Helvetica Neue', sans-serif; font-weight: bold; }
    .subtitle { text-align: center; color: #666; margin-bottom: 20px; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🎮 L'Odyssée Thématique des 7 Mondes</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Édition Web Haute Performance (60 FPS)</p>", unsafe_allow_html=True)

# --- PANNEAU DE CONTRÔLES (SIDEBAR) ---
with st.sidebar:
    st.header("🕹️ Commandes du Joueur")
    st.markdown("""
    * **Flèches GAUCHE / DROITE** : Se déplacer
    * **Flèche HAUT / ESPACE** : Sauter & Double Saut
    * **Touche J** : Tirer avec l'arme active
    * **Touche B** : Ouvrir / Fermer le Magasin d'armes
    * **Touche R** : Réinitialiser la partie
    * **Touche P** : Mettre en pause
    """)
    st.write("---")
    st.header("🛒 Raccourcis Magasin")
    st.markdown("Une fois le magasin ouvert (**B**), utilisez les touches **1 à 5** de votre clavier pour équiper ou acheter une arme !")

# --- MOTEUR DE JEU COMPATIBLE CLOUD (HTML5/CANVAS) ---
game_html_code = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; padding: 0; background-color: #0f0f14; overflow: hidden; font-family: 'Courier New', monospace; }
        canvas { display: block; margin: 10px auto; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border-radius: 4px; }
    </style>
</head>
<body>

<canvas id="gameCanvas" width="1000" height="500"></canvas>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// --- SYNTHÉTISEUR AUDIO WEB ---
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSound(type) {
    if(!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);
    
    if (type === 'jump') {
        osc.frequency.setValueAtTime(350, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(700, audioCtx.currentTime + 0.12);
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        osc.start(); osc.stop(audioCtx.currentTime + 0.12);
    } else if (type === 'shoot') {
        osc.type = 'square'; osc.frequency.setValueAtTime(550, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        osc.start(); osc.stop(audioCtx.currentTime + 0.07);
    } else if (type === 'coin') {
        osc.frequency.setValueAtTime(950, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        osc.start(); osc.stop(audioCtx.currentTime + 0.15);
    } else if (type === 'hit') {
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(140, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
        osc.start(); osc.stop(audioCtx.currentTime + 0.1);
    }
}

// --- CONFIGURATION CONFIGURATION DES 7 NIVEAUX ---
const LEVEL_THEMES = {
    1: { name: "Japon 🇯🇵", bg: "#FFE6EE", ground: "#DC143C", outfit: "#FF69B4", hair: "#FFB6C1", enemyType: "Wolf", shoots: false, enemyColor: "#808080", shape: "heart", pColor: "#FF3232" },
    2: { name: "Algérie 🇩🇿", bg: "#F4A460", ground: "#D2691E", outfit: "#228B22", hair: "#8B4513", enemyType: "Fennec", shoots: false, enemyColor: "#F5DEB3", shape: "fire", pColor: "#FF4500" },
    3: { name: "Égypte 🇪🇬", bg: "#E6BE8A", ground: "#B48C5A", outfit: "#D4AF37", hair: "#1E1E1E", enemyType: "Jackal", shoots: false, enemyColor: "#464646", shape: "crescent", pColor: "#F0E68C" },
    4: { name: "Rome 🇮🇹", bg: "#D2C8BE", ground: "#8C8278", outfit: "#B22222", hair: "#643C28", enemyType: "Wolf", shoots: true, enemyColor: "#646464", shape: "spear", pColor: "#C0C0C0" },
    5: { name: "Angleterre 🇬🇧", bg: "#708090", ground: "#46505A", outfit: "#ADD8E6", hair: "#F4A460", enemyType: "NPC", shoots: false, enemyColor: "#FFE4C4", shape: "umbrella", pColor: "#00008B" },
    6: { name: "Monde Glacial ❄️", bg: "#E0FFFF", ground: "#AFEEEE", outfit: "#FFFFFF", hair: "#C8E6FF", enemyType: "Bear", shoots: true, enemyColor: "#F0F8FF", shape: "ice", pColor: "#00BFFF", ice: true },
    7: { name: "Samouraï 🐉", bg: "#F5EBD7", ground: "#8B4513", outfit: "#654321", hair: "#141414", enemyType: "None", shoots: false, enemyColor: "#000", shape: "katana", pColor: "#8A43E2", hasBoss: true }
};

const WEAPON_SHOP = {
    "Base": { power: 1, cost: 0, color: "#C8C8C8" },
    "Feu": { power: 2, cost: 50, color: "#FF4500" },
    "Glace": { power: 3, cost: 100, color: "#00BFFF" },
    "Foudre": { power: 4, cost: 200, color: "#FFFF00" },
    "Légendaire": { power: 8, cost: 500, color: "#FFD700" }
};

// Variables d'état
let currentLevel = 1, score = 0, coins = 10, lives = 3, comboMultiplier = 1.0, comboTimer = 0;
let currentWeapon = "Base", unlockedWeapons = ["Base"];
let shopOpen = false, gamePaused = false, gameOver = false, victory = false;

let player = { x: 100, y: 300, vx: 0, vy: 0, width: 32, height: 48, grounded: false, doubleJumpAvailable: true, invincibleTimer: 0, speedTimer: 0, shieldTimer: 0, facingRight: true };
let platforms = [], enemies = [], coinsList = [], powerups = [], projectiles = [], boss = null, keys = {};

function setupLevel(lvl) {
    let config = LEVEL_THEMES[lvl];
    player.x = 100; player.y = 300; player.vx = 0; player.vy = 0;
    projectiles = [];
    
    platforms = [
        {x: 0, y: 450, w: 4000, h: 50}, {x: 400, y: 330, w: 150, h: 20}, {x: 700, y: 250, w: 200, h: 20},
        {x: 1100, y: 340, w: 150, h: 20}, {x: 1500, y: 230, w: 250, h: 20}, {x: 1900, y: 310, w: 180, h: 20}
    ];
    
    coinsList = [];
    for(let i=12; i<350; i+=30) { coinsList.push({x: i*10, y: 410, w: 16, h: 16}); }
    
    enemies = []; boss = null;
    if(!config.hasBoss) {
        if(config.enemyType !== "None") {
            for(let i=1; i<=4; i++) { 
                enemies.push({x: 700*i, y: 410, w: 40, h: 40, vx: -1.8, type: config.enemyType, shoots: config.shoots, color: config.enemyColor, cooldown: Math.random()*80 + 40}); 
            }
        }
    } else { boss = { x: 3500, y: 200, w: 120, h: 120, hp: 8, cooldown: 0, pulse: 0 }; }

    powerups = [
        {x: 800, y: 210, w: 20, h: 20, type: "invincibility", collected: false},
        {x: 1600, y: 190, w: 20, h: 20, type: "shield", collected: false}
    ];
}

window.addEventListener('keydown', e => {
    keys[e.code] = true;
    if(e.code === 'KeyR') { currentLevel = 1; score = 0; coins = 10; lives = 3; currentWeapon = "Base"; unlockedWeapons = ["Base"]; gameOver = false; victory = false; setupLevel(currentLevel); }
    if(e.code === 'KeyP') gamePaused = !gamePaused;
    if(e.code === 'KeyB' && !gameOver && !victory) shopOpen = !shopOpen;
    if((e.code === 'Space' || e.code === 'ArrowUp') && !gamePaused && !shopOpen && !gameOver) {
        if(player.grounded) { player.vy = -11.5; player.grounded = false; playSound('jump'); }
        else if(player.doubleJumpAvailable) { player.vy = -10; player.doubleJumpAvailable = false; playSound('jump'); }
    }
    if(e.code === 'KeyJ' && !gamePaused && !shopOpen && !gameOver) {
        let p_vx = player.facingRight ? 8 : -8;
        let p_pow = WEAPON_SHOP[currentWeapon].power;
        let p_color = WEAPON_SHOP[currentWeapon].color;
        projectiles.push({x: player.x + (player.facingRight?24:-4), y: player.y + 16, w: 12, h: 12, vx: p_vx, color: p_color, power: p_pow, side: "player"});
        playSound('shoot');
    }
    if(shopOpen) {
        let sel = {"Digit1":"Base","Digit2":"Feu","Digit3":"Glace","Digit4":"Foudre","Digit5":"Légendaire"}[e.code];
        if(sel) {
            let info = WEAPON_SHOP[sel];
            if(unlockedWeapons.includes(sel)) { currentWeapon = sel; }
            else if(coins >= info.cost) { coins -= info.cost; unlockedWeapons.push(sel); currentWeapon = sel; }
        }
    }
});
window.addEventListener('keyup', e => { keys[e.code] = false; });

function update() {
    if(gamePaused || shopOpen || gameOver || victory) return;
    let config = LEVEL_THEMES[currentLevel];
    let friction = config.ice ? 0.96 : 0.82;
    let accel = config.ice ? 0.35 : 0.75;

    if(keys['ArrowLeft']) { player.vx -= accel; player.facingRight = false; }
    else if(keys['ArrowRight']) { player.vx += accel; player.facingRight = true; }
    else { player.vx *= friction; }

    let maxSpeed = 5.5;
    if(player.vx > maxSpeed) player.vx = maxSpeed;
    if(player.vx < -maxSpeed) player.vx = -maxSpeed;

    player.vy += 0.52; 
    player.x += player.vx; if(player.x < 0) player.x = 0;
    player.y += player.vy; player.grounded = false;

    platforms.forEach(p => {
        if(player.x < p.x + p.w && player.x + player.width > p.x && player.y < p.y + p.h && player.y + player.height > p.y) {
            if(player.vy > 0 && player.y + player.height - player.vy <= p.y) { player.y = p.y - player.height; player.vy = 0; player.grounded = true; player.doubleJumpAvailable = true; }
        }
    });

    if(player.y > 520) { player.x = 100; player.y = 300; lives--; playSound('hit'); if(lives<=0) gameOver=true; }
    if(player.invincibleTimer > 0) player.invincibleTimer--;
    if(player.shieldTimer > 0) player.shieldTimer--;
    if(comboTimer > 0) { comboTimer--; if(comboTimer<=0) comboMultiplier = 1.0; }

    if(boss) {
        boss.pulse += 0.04; boss.y = 160 + Math.sin(boss.pulse) * 70; boss.cooldown--;
        if(boss.cooldown <= 0) { boss.cooldown = 90; projectiles.push({x: boss.x, y: boss.y + 40, w: 12, h: 12, vx: -5.5, color: "#FF3200", side: "hostile"}); }
        if(player.x < boss.x + boss.w && player.x + player.width > boss.x && player.y < boss.y + boss.h && player.y + player.height > boss.y) {
            if(player.invincibleTimer === 0) { lives--; player.invincibleTimer = 60; player.x = 100; if(lives<=0) gameOver=true; }
        }
    }

    enemies.forEach((e, idx) => {
        e.x += e.vx; if(e.x < 0 || e.x > 3900) e.vx *= -1;
        if(e.shoots) { e.cooldown--; if(e.cooldown <= 0) { e.cooldown = 130; projectiles.push({x: e.x, y: e.y+10, w: 12, h: 12, vx: -4.5, color: "#FF0000", side: "hostile"}); } }
        if(player.x < e.x + e.w && player.x + player.width > e.x && player.y < e.y + e.h && player.y + player.height > e.y) {
            if(config.enemyType === "NPC") { enemies.splice(idx, 1); score += 50 * comboMultiplier; playSound('coin'); }
            else if(player.invincibleTimer === 0) {
                if(player.shieldTimer > 0) { player.shieldTimer = 0; player.invincibleTimer = 30; enemies.splice(idx, 1); }
                else { lives--; player.invincibleTimer = 60; player.x = 100; if(lives<=0) gameOver=true; }
            }
        }
    });

    projectiles.forEach((p, pIdx) => {
        p.x += p.vx; if(p.x < 0 || p.x > 4000) { projectiles.splice(pIdx,1); return; }
        if(p.side === "player") {
            enemies.forEach((e, eIdx) => {
                if(p.x < e.x + e.w && p.x + p.w > e.x && p.y < e.y + e.h && p.y + p.h > e.y && config.enemyType !== "NPC") {
                    enemies.splice(eIdx, 1); projectiles.splice(pIdx, 1);
                    comboMultiplier = Math.min(2.0, comboMultiplier + 0.2); comboTimer = 120; score += 100 * comboMultiplier; playSound('hit');
                }
            });
            if(boss && p.x < boss.x + boss.w && p.x + p.w > boss.x && p.y < boss.y + boss.h && p.y + p.h > boss.y) {
                boss.hp -= p.power; projectiles.splice(pIdx, 1); playSound('hit'); if(boss.hp <= 0) victory = true;
            }
        } else {
            if(p.x < player.x + player.width && p.x + p.w > player.x && p.y < player.y + player.height && p.y + p.h > player.y) {
                projectiles.splice(pIdx, 1);
                if(player.invincibleTimer === 0) { if(player.shieldTimer > 0) { player.shieldTimer = 0; player.invincibleTimer = 30; } else { lives--; player.invincibleTimer = 60; player.x = 100; if(lives<=0) gameOver=true; } }
            }
        }
    });

    coinsList.forEach((c, idx) => {
        if(player.x < c.x + c.w && player.x + player.width > c.x && player.y < c.y + c.h && player.y + player.height > c.y) { coinsList.splice(idx, 1); coins++; score += 100 * comboMultiplier; playSound('coin'); }
    });

    powerups.forEach(pu => {
        if(!pu.collected && player.x < pu.x + pu.w && player.x + player.width > pu.x && player.y < pu.y + pu.h && player.y + player.height > pu.y) {
            pu.collected = true;
            if(pu.type === "invincibility") player.invincibleTimer = 300;
            if(pu.type === "shield") player.shieldTimer = 400;
        }
    });

    if(!config.hasBoss && player.x > 3850) { if(currentLevel < 7) { currentLevel++; lives++; setupLevel(currentLevel); } else { victory = true; } }
}

function draw() {
    let config = LEVEL_THEMES[currentLevel];
    ctx.fillStyle = config.bg; ctx.fillRect(0, 0, canvas.width, canvas.height);
    let offsetX = Math.min(Math.max(player.x - 250, 0), 3000);

    ctx.fillStyle = config.ground; platforms.forEach(p => { ctx.fillRect(p.x - offsetX, p.y, p.w, p.h); });
    ctx.fillStyle = "#FFD700"; coinsList.forEach(c => { ctx.beginPath(); ctx.arc(c.x - offsetX + 8, c.y + 8, 8, 0, Math.PI*2); ctx.fill(); });
    powerups.forEach(pu => { if(!pu.collected) { ctx.fillStyle = pu.type === "invincibility" ? "#FF0000" : "#0000FF"; ctx.fillRect(pu.x - offsetX, pu.y, pu.w, pu.h); } });
    enemies.forEach(e => { ctx.fillStyle = e.color; ctx.fillRect(e.x - offsetX, e.y, e.w, e.h); });
    if(boss) { ctx.fillStyle = "#C80000"; ctx.fillRect(boss.x - offsetX, boss.y, boss.w, boss.h); ctx.fillStyle = "#FFFF00"; ctx.fillRect(boss.x - offsetX + 20, boss.y + 20, 20, 20); }
    projectiles.forEach(p => { ctx.fillStyle = p.color; ctx.fillRect(p.x - offsetX, p.y, p.w, p.h); });

    if(!config.hasBoss) { ctx.strokeStyle = "#9400D3"; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(3850 - offsetX + 20, 400, 20, 50, 0, 0, Math.PI*2); ctx.stroke(); }

    if(!(player.invincibleTimer > 0 && Math.floor(player.invincibleTimer/4)%2===0)) {
        ctx.fillStyle = config.hair; ctx.fillRect(player.x - offsetX + (player.facingRight?-2:10), player.y - 4, 24, 20);
        ctx.fillStyle = config.outfit; ctx.fillRect(player.x - offsetX, player.y + 14, player.width, 34);
        ctx.fillStyle = "#FFDAB9"; ctx.fillRect(player.x - offsetX + 4, player.y, 24, 16);
        ctx.fillStyle = "#000000"; ctx.fillRect(player.x - offsetX + (player.facingRight?18:8), player.y + 4, 4, 4);
    }
    if(player.shieldTimer > 0) { ctx.strokeStyle = "#00BFFF"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(player.x - offsetX + 16, player.y + 24, 30, 0, Math.PI*2); ctx.stroke(); }

    ctx.fillStyle = "#000000"; ctx.font = "bold 15px monospace";
    ctx.fillText(`SCORE: ${score} | VIES: ${lives} | PIÈCES: ${coins} | COMBO: x${comboMultiplier.toFixed(1)} | MONDE: ${config.name}`, 15, 25);

    if(shopOpen) {
        ctx.fillStyle = "rgba(40,40,45,0.92)"; ctx.fillRect(200, 80, 600, 340); ctx.fillStyle = "#FFFFFF"; ctx.font = "bold 18px monospace"; ctx.fillText("--- BOUTIQUE D'ARMES (Touches 1 à 5) ---", 240, 120);
        let y = 175; Object.keys(WEAPON_SHOP).forEach((name, i) => {
            let data = WEAPON_SHOP[name]; let status = currentWeapon === name ? "[ÉQUIPÉE]" : (unlockedWeapons.includes(name) ? "[POSSÉDÉE]" : `Coût: ${data.cost} pièces`);
            ctx.fillStyle = currentWeapon === name ? "#00FF00" : "#FFFFFF"; ctx.fillText(`${i+1}. Arme ${name} (Piss. ${data.power}) - ${status}`, 250, y); y += 35;
        });
    }
    if(gameOver) { ctx.fillStyle = "rgba(0,0,0,0.85)"; ctx.fillRect(250, 180, 500, 140); ctx.fillStyle = "#FF0000"; ctx.font = "bold 32px monospace"; ctx.fillText("GAME OVER", 415, 235); ctx.fillStyle = "#FFFFFF"; ctx.font = "16px monospace"; ctx.fillText("Appuyez sur 'R' pour recommencer", 345, 280); }
    if(victory) { ctx.fillStyle = "rgba(205,133,63,0.95)"; ctx.fillRect(250, 150, 500, 180); ctx.fillStyle = "#FFD700"; ctx.font = "bold 26px monospace"; ctx.fillText("VICTOIRE LÉGENDAIRE !", 335, 195); ctx.fillStyle = "#FFFFFF"; ctx.font = "18px monospace"; ctx.fillText(`Score Final: ${score}`, 420, 235); ctx.fillText("Appuyez sur 'R' pour rejouer", 360, 285); }
}

setupLevel(currentLevel);
function loop() { update(); draw(); requestAnimationFrame(loop); }
loop();
</script>
</body>
</html>
"""

components.html(game_html_code, height=530, scrolling=False)
