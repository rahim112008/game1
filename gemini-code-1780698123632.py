<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Neon Racer - Jeu de course arcade</title>
    <style>
        body {
            margin: 0;
            min-height: 100vh;
            background: radial-gradient(circle at center, #0a0f1e, #03060c);
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Courier New', monospace;
        }
        .game-container {
            border-radius: 24px;
            box-shadow: 0 0 0 4px #ffc966, 0 20px 30px rgba(0,0,0,0.5);
            overflow: hidden;
        }
        canvas {
            display: block;
            margin: 0 auto;
        }
        .info {
            text-align: center;
            margin-top: 16px;
            color: #ffd966;
            font-weight: bold;
            letter-spacing: 2px;
        }
        .controls {
            font-size: 14px;
            color: #8aac9b;
        }
        @media (max-width: 600px) {
            .game-container { transform: scale(0.95); }
        }
    </style>
</head>
<body>
<div>
    <div class="game-container">
        <div id="gameCanvas"></div>
    </div>
    <div class="info">
        🏁 NEON RACER 🏁<br>
        <span class="controls">← →  ou  A/D  –  Évite les rouges, collecte les boosts (⚡) et shields (🛡️)</span>
    </div>
</div>

<!-- Phaser 3 CDN -->
<script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js"></script>

<script>
    // Configuration du jeu
    const config = {
        type: Phaser.AUTO,
        parent: 'gameCanvas',
        width: 800,
        height: 600,
        backgroundColor: '#0b1f1a',
        physics: {
            default: 'arcade',
            arcade: {
                debug: false,
                gravity: { y: 0 }
            }
        },
        scene: {
            preload: preload,
            create: create,
            update: update
        },
        pixelArt: false,
        scale: {
            mode: Phaser.Scale.FIT,
            autoCenter: Phaser.Scale.CENTER_BOTH
        }
    };

    let game = new Phaser.Game(config);

    // Variables globales
    let player;
    let cursors;
    let enemies;
    let powerups;
    let score = 0;
    let scoreText;
    let bestScore = 0;
    let bestText;
    let gameOver = false;
    let gameOverText;
    let restartKey;
    let lanePositions = [200, 400, 600]; // 3 voies fixes
    let playerLane = 1; // 0,1,2
    let enemySpawnTimer;
    let powerupSpawnTimer;
    let speed = 5;
    let baseSpeed = 5;
    let laneWidth = 200;
    
    // Effets visuels
    let roadLines;
    let lineOffset = 0;
    let exhaustEmitter;

    function preload() {
        // Création de graphismes procéduraux (pas d'images externes)
        this.add.graphics();
        
        // On crée des textures canvas pour voitures et power-ups
        createCarTexture(this, 'playerCar', 0x3cc9ff, 0x1a5276);
        createCarTexture(this, 'enemyCar', 0xe34c26, 0x8b2c12);
        createPowerupTexture(this, 'boostPower', 0xf7d44a, '⚡');
        createPowerupTexture(this, 'shieldPower', 0x4ac7f7, '🛡️');
    }

    // Fonction pour dessiner une voiture sur une texture canvas
    function createCarTexture(scene, key, mainColor, windowColor) {
        const graphics = scene.make.graphics({ x: 0, y: 0, add: false });
        graphics.fillStyle(mainColor, 1);
        graphics.fillRoundedRect(0, 0, 48, 80, 12);
        graphics.fillStyle(windowColor, 1);
        graphics.fillRoundedRect(6, 15, 36, 35, 8);
        graphics.fillStyle(0xffdd99, 1);
        graphics.fillRect(8, 68, 10, 8);
        graphics.fillRect(30, 68, 10, 8);
        graphics.generateTexture(key, 48, 80);
        graphics.destroy();
    }

    function createPowerupTexture(scene, key, color, symbol) {
        const graphics = scene.make.graphics({ x: 0, y: 0, add: false });
        graphics.fillStyle(color, 1);
        graphics.fillCircle(24, 24, 24);
        graphics.generateTexture(key, 48, 48);
        graphics.destroy();
        // Ajout du texte sur la texture
        const textTexture = scene.add.text(0, 0, symbol, { font: '32px monospace', color: '#000' });
        scene.textures.addImage(key + 'Sym', textTexture);
    }

    function create() {
        // Ajout de la route décorative (lignes)
        roadLines = this.add.group();
        for (let i = 0; i < 20; i++) {
            let line = this.add.rectangle(400, i * 40, 8, 20, 0xffd966);
            roadLines.add(line);
        }
        
        // Création du joueur
        player = this.physics.add.sprite(lanePositions[1], 520, 'playerCar');
        player.setCollideWorldBounds(true);
        player.body.setSize(40, 70);
        player.body.immovable = true;
        
        // Groupe des ennemis et power-ups
        enemies = this.physics.add.group();
        powerups = this.physics.add.group();
        
        // Collisions
        this.physics.add.overlap(player, enemies, hitEnemy, null, this);
        this.physics.add.overlap(player, powerups, collectPowerup, null, this);
        
        // Score text
        scoreText = this.add.text(20, 20, 'SCORE: 0', { fontSize: '28px', fontFamily: 'Courier New', color: '#ffdb7e', stroke: '#000', strokeThickness: 3 });
        bestScore = localStorage.getItem('neonBest') ? parseInt(localStorage.getItem('neonBest')) : 0;
        bestText = this.add.text(20, 60, 'BEST: ' + bestScore, { fontSize: '22px', fontFamily: 'Courier New', color: '#ffb347', stroke: '#000', strokeThickness: 2 });
        
        // Contrôles clavier
        cursors = this.input.keyboard.createCursorKeys();
        this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A);
        this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D);
        
        // Timer spawn ennemis (toutes les 1.2 secondes)
        enemySpawnTimer = this.time.addEvent({
            delay: 1100,
            callback: spawnEnemy,
            callbackScope: this,
            loop: true
        });
        
        // Timer spawn power-ups (toutes les 5 secondes)
        powerupSpawnTimer = this.time.addEvent({
            delay: 5000,
            callback: spawnPowerup,
            callbackScope: this,
            loop: true
        });
        
        // Effet de particules sur l'échappement
        exhaustEmitter = this.add.particles(0, 0, 'playerCar', {
            x: { min: -15, max: 15 },
            y: 35,
            speedY: { min: 80, max: 150 },
            angle: { min: 80, max: 100 },
            scale: { start: 0.4, end: 0 },
            lifespan: 400,
            frequency: 60,
            tint: 0xffaa44
        });
        exhaustEmitter.startFollow(player);
        
        // Gestion de redémarrage (touche R)
        restartKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.R);
        
        // Animation de survie
        this.cameras.main.setBackgroundColor('#0b1a14');
    }
    
    function spawnEnemy() {
        if (gameOver) return;
        let lane = Phaser.Math.Between(0, 2);
        let enemy = enemies.create(lanePositions[lane], -40, 'enemyCar');
        enemy.setVelocityY(speed * 60);
        enemy.body.setSize(42, 72);
        enemy.setData('lane', lane);
    }
    
    function spawnPowerup() {
        if (gameOver) return;
        let lane = Phaser.Math.Between(0, 2);
        let type = Phaser.Math.Between(0, 1) === 0 ? 'boost' : 'shield';
        let power = powerups.create(lanePositions[lane], -40, type === 'boost' ? 'boostPower' : 'shieldPower');
        power.setVelocityY(speed * 55);
        power.setData('type', type);
        power.body.setCircle(20);
    }
    
    function hitEnemy(player, enemy) {
        if (!gameOver) {
            gameOver = true;
            enemySpawnTimer.remove();
            powerupSpawnTimer.remove();
            this.physics.pause();
            player.setTint(0xff0000);
            gameOverText = this.add.text(400, 300, 'GAME OVER\nAppuie sur R', { fontSize: '42px', fontFamily: 'Courier New', color: '#ff8866', align: 'center', stroke: '#000', strokeThickness: 4 }).setOrigin(0.5);
            // Sauvegarde du meilleur score
            if (score > bestScore) {
                bestScore = score;
                localStorage.setItem('neonBest', bestScore);
                bestText.setText('BEST: ' + bestScore);
            }
        }
    }
    
    function collectPowerup(player, power) {
        let type = power.getData('type');
        power.destroy();
        if (type === 'boost') {
            // Boost de vitesse temporaire
            speed = 9;
            this.time.delayedCall(3000, () => { if (!gameOver) speed = baseSpeed; });
            score += 30;
            updateScoreUI();
            // Effet visuel
            player.setTint(0xffcc88);
            this.time.delayedCall(300, () => player.clearTint());
        } else if (type === 'shield') {
            // Invincibilité temporaire (avec flash)
            player.setTint(0x88ccff);
            this.physics.world.overlap(false);
            this.time.delayedCall(4000, () => {
                if (!gameOver) {
                    player.clearTint();
                    this.physics.world.overlap(true);
                }
            });
            score += 20;
            updateScoreUI();
        }
    }
    
    function updateScoreUI() {
        scoreText.setText('SCORE: ' + Math.floor(score));
        if (score > bestScore) {
            bestText.setText('BEST: ' + Math.floor(score));
        }
    }
    
    function update() {
        if (gameOver) {
            if (restartKey.isDown) {
                location.reload(); // simple redémarrage
            }
            return;
        }
        
        // Mouvement du joueur (gauche/droite)
        let newLane = playerLane;
        if (cursors.left.isDown || this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A).isDown) {
            newLane--;
        } else if (cursors.right.isDown || this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D).isDown) {
            newLane++;
        }
        newLane = Phaser.Math.Clamp(newLane, 0, 2);
        if (newLane !== playerLane) {
            playerLane = newLane;
            this.tweens.add({
                targets: player,
                x: lanePositions[playerLane],
                duration: 120,
                ease: 'Power2'
            });
        }
        
        // Incrémentation progressive du score (survie)
        score += 0.2;
        updateScoreUI();
        
        // Difficulté progressive (vitesse max 12)
        if (speed < 12) {
            speed = baseSpeed + Math.floor(score / 800);
        }
        
        // Ajuster vélocité des ennemis et power-ups déjà présents
        enemies.getChildren().forEach(enemy => {
            enemy.setVelocityY(speed * 60);
        });
        powerups.getChildren().forEach(p => {
            p.setVelocityY(speed * 55);
        });
        
        // Animation des lignes de route
        lineOffset = (lineOffset + speed * 2) % 40;
        let index = 0;
        roadLines.getChildren().forEach(line => {
            line.y = (index * 40 + lineOffset) % 600;
            if (line.y < 0) line.y += 600;
            index++;
        });
        
        // Supprimer les ennemis/power-ups sortis
        enemies.getChildren().forEach(enemy => {
            if (enemy.y > 650) enemy.destroy();
        });
        powerups.getChildren().forEach(p => {
            if (p.y > 650) p.destroy();
        });
    }
</script>
</body>
</html>
