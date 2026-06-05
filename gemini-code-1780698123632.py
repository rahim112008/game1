import streamlit as st
import pygame
import math
import random
import numpy as np
import time

# --- CONFIGURATION DE LA PAGE STREAMLIT ---
st.set_page_config(
    page_title="L'Odyssée des 7 Mondes",
    page_icon="🐉",
    layout="centered"
)

st.title("🎮 L'Odyssée Thématique des 7 Mondes")
st.caption("Jeu de plateforme 2D rendu en temps réel via Pygame & Streamlit")

# Dimensions de rendu fixes
TARGET_WIDTH = 1000
TARGET_HEIGHT = 500

# INITIALISATION DU MOTEUR GRAPHIQUE ET AUDIO
if 'init' not in st.session_state:
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=1)
    st.session_state.init = True

# --- SYNTHÈSE AUDIO ---
def generate_sound(freq, duration, type='sine'):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    if type == 'sine':
        data = np.sin(2 * np.pi * freq * t)
    elif type == 'square':
        data = np.sign(np.sin(2 * np.pi * freq * t))
    else:
        data = np.random.uniform(-1, 1, n_samples)
    
    fade = int(n_samples * 0.1)
    if fade > 0:
        data[:fade] *= np.linspace(0, 1, fade)
        data[-fade:] *= np.linspace(1, 0, fade)
    return pygame.sndarray.make_sound((data * 32767).astype(np.int16))

SOUNDS = {
    'jump': generate_sound(400, 0.1, 'sine'),
    'shoot': generate_sound(600, 0.08, 'square'),
    'coin': generate_sound(900, 0.15, 'sine'),
    'hit': generate_sound(150, 0.12, 'noise')
}

# --- THÈMES DES 7 NIVEAUX ---
LEVEL_THEMES = {
    1: {"name": "Japon 🇯🇵", "bg": (255, 220, 230), "ground": (220, 160, 180), "char_outfit": (255, 105, 180), "char_hair": (255, 182, 193), "enemy": "Wolf", "shoots": False, "enemy_color": (128, 128, 128), "shape": "heart", "p_color": (255, 50, 50)},
    2: {"name": "Algérie 🇩🇿", "bg": (244, 164, 96), "ground": (210, 105, 30), "char_outfit": (34, 139, 34), "char_hair": (139, 69, 19), "enemy": "Fennec", "shoots": False, "enemy_color": (245, 222, 179), "shape": "fire", "p_color": (255, 69, 0)},
    3: {"name": "Égypte 🇪🇬", "bg": (230, 190, 138), "ground": (180, 140, 90), "char_outfit": (212, 175, 55), "char_hair": (30, 30, 30), "enemy": "Jackal", "shoots": False, "enemy_color": (70, 70, 70), "shape": "crescent", "p_color": (240, 230, 140)},
    4: {"name": "Rome 🇮🇹", "bg": (210, 200, 190), "ground": (140, 130, 120), "char_outfit": (178, 34, 34), "char_hair": (100, 60, 40), "enemy": "Wolf", "shoots": True, "enemy_color": (100, 100, 100), "shape": "spear", "p_color": (192, 192, 192)},
    5: {"name": "Angleterre 🇬🇧", "bg": (112, 128, 144), "ground": (70, 80, 90), "char_outfit": (173, 216, 230), "char_hair": (244, 164, 96), "enemy": "NPC", "shoots": False, "enemy_color": (255, 228, 196), "shape": "umbrella", "p_color": (0, 0, 139)},
    6: {"name": "Monde Glacial ❄️", "bg": (224, 255, 255), "ground": (175, 238, 238), "char_outfit": (255, 255, 255), "char_hair": (200, 230, 255), "enemy": "Bear", "shoots": True, "enemy_color": (240, 248, 255), "shape": "ice", "p_color": (0, 191, 255), "ice": True},
    7: {"name": "Samouraï 🐉", "bg": (245, 235, 215), "ground": (139, 69, 19), "char_outfit": (101, 67, 33), "char_hair": (20, 20, 20), "enemy": "Boss", "shoots": False, "enemy_color": (0,0,0), "shape": "katana", "p_color": (138, 43, 226), "boss": True}
}

WEAPON_SHOP = {
    "Base": {"power": 1, "cost": 0, "color": (200, 200, 200)},
    "Feu": {"power": 2, "cost": 50, "color": (255, 69, 0)},
    "Glace": {"power": 3, "cost": 100, "color": (0, 191, 255)},
    "Foudre": {"power": 4, "cost": 200, "color": (255, 255, 0)},
    "Légendaire": {"power": 8, "cost": 500, "color": (255, 215, 0)}
}

# --- ÉTATS PERSISTANTS DANS STREAMLIT ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        "level": 1, "score": 0, "coins": 10, "lives": 3, "combo": 1.0,
        "px": 100, "py": 300, "pvx": 0, "pvy": 0, "grounded": False, "double_jump": True,
        "weapon": "Base", "unlocked": ["Base"], "enemies": [], "boss_hp": 8, "boss_y": 200, "boss_dir": 1
    }

gs = st.session_state.game_state

# --- INTERFACE DE CONTRÔLE DANS STREAMLIT ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("⬅️ Gauche"):
        gs["pvx"] = -8; gs["px"] = max(0, gs["px"] - 15)
with col2:
    if st.button("🚀 Sauter"):
        if gs["grounded"]:
            gs["pvy"] = -12; gs["grounded"] = False; SOUNDS['jump'].play()
        elif gs["double_jump"]:
            gs["pvy"] = -10; gs["double_jump"] = False; SOUNDS['jump'].play()
with col3:
    if st.button("➡️ Droite"):
        gs["pvx"] = 8; gs["px"] = min(3900, gs["px"] + 15)
with col4:
    if st.button("🔥 Tirer (J)"):
        SOUNDS['shoot'].play()
        # Logique de tir simplifiée : élimine l'ennemi le plus proche devant
        config = LEVEL_THEMES[gs["level"]]
        power = WEAPON_SHOP[gs["weapon"]]["power"]
        if config.get("boss"):
            gs["boss_hp"] -= power
            if gs["boss_hp"] <= 0: st.balloons()
        elif gs["enemies"]:
            gs["enemies"].pop(0)
            gs["score"] += int(100 * gs["combo"])
            gs["combo"] = min(2.0, gs["combo"] + 0.2)

# --- BOUTIQUE INTEGRÉE STREAMLIT ---
st.sidebar.header("🛒 Magasin d'Armes")
for name, data in WEAPON_SHOP.items():
    if name in gs["unlocked"]:
        if st.sidebar.button(f"Équiper {name} (Puissance {data['power']}) [Possédé]", key=name):
            gs["weapon"] = name
    else:
        if st.sidebar.button(f"Acheter {name} - {data['cost']} pièces", key=name):
            if gs["coins"] >= data["cost"]:
                gs["coins"] -= data["cost"]
                gs["unlocked"].append(name)
                gs["weapon"] = name

if st.sidebar.button("🔄 Réinitialiser le Jeu"):
    st.session_state.game_state = {
        "level": 1, "score": 0, "coins": 0, "lives": 3, "combo": 1.0,
        "px": 100, "py": 300, "pvx": 0, "pvy": 0, "grounded": False, "double_jump": True,
        "weapon": "Base", "unlocked": ["Base"], "enemies": [], "boss_hp": 8, "boss_y": 200, "boss_dir": 1
    }
    st.rerun()

# --- BOUCLE ET PHYSIQUE DU JEU ---
config = LEVEL_THEMES[gs["level"]]

# Initialisation des ennemis du niveau si la liste est vide
if not gs["enemies"] and not config.get("boss"):
    gs["enemies"] = [{"x": 600 * i, "y": 410, "dir": -1} for i in range(1, 5)]

# Gravité et mouvements basiques
gs["pvy"] += 0.8
gs["py"] += gs["pvy"]
gs["pvx"] *= 0.8

# Collision Sol fixe
if gs["py"] >= 402:
    gs["py"] = 402
    gs["pvy"] = 0
    gs["grounded"] = True
    gs["double_jump"] = True

# Gestion du Boss volant
if config.get("boss"):
    gs["boss_y"] += 3 * gs["boss_dir"]
    if gs["boss_y"] <= 100 or gs["boss_y"] >= 300:
        gs["boss_dir"] *= -1

# Avancement au niveau suivant si le joueur atteint le bout de la carte (x > 1500 pour simplifier sur Streamlit)
if gs["px"] >= 1500 and not config.get("boss"):
    if gs["level"] < 7:
        gs["level"] += 1
        gs["px"] = 100
        gs["enemies"] = []
        gs["lives"] += 1
        st.toast(f"Bienvenue au Niveau {gs['level']} !", icon="🌟")
    else:
        if gs["boss_hp"] <= 0:
            st.success("Félicitations ! Vous avez terrassé le Dragon !")

# --- DESSIN DU JEU VIA SURFACE PYGAME ---
surface = pygame.Surface((TARGET_WIDTH, TARGET_HEIGHT))
surface.fill(config["bg"])

# Dessin du Sol
pygame.draw.rect(surface, config["ground"], (0, 450, TARGET_WIDTH, 50))

# Dessin des Ennemis classiques
for e in gs["enemies"]:
    pygame.draw.rect(surface, config["enemy_color"], (e["x"] - gs["px"] + 200, e["y"], 40, 40))
    pygame.draw.rect(surface, (0, 0, 0), (e["x"] - gs["px"] + 210, e["y"] + 10, 6, 6))

# Dessin du Boss Dragon
if config.get("boss") and gs["boss_hp"] > 0:
    pygame.draw.rect(surface, (200, 0, 0), (600, gs["boss_y"], 120, 120))
    pygame.draw.rect(surface, (255, 255, 0), (620, gs["boss_y"] + 20, 20, 20))
    # Barre de vie du boss
    pygame.draw.rect(surface, (0, 0, 0), (600, gs["boss_y"] - 20, 120, 10))
    pygame.draw.rect(surface, (0, 255, 0), (600, gs["boss_y"] - 20, int(120 * (gs["boss_hp"] / 8)), 10))

# Dessin de l'Héroïne (Pixel art en formes colorées selon le niveau)
px_screen = 200  # Position visuelle fixe (Défilement de caméra simulé)
pygame.draw.rect(surface, config["char_hair"], (px_screen - 2, gs["py"] - 4, 24, 20)) # Cheveux
pygame.draw.rect(surface, config["char_outfit"], (px_screen, gs["py"] + 14, 32, 34)) # Tenue/Robe
pygame.draw.rect(surface, (255, 218, 185), (px_screen + 4, gs["py"], 24, 16))        # Visage
pygame.draw.rect(surface, (0, 0, 0), (px_screen + 16, gs["py"] + 4, 4, 4))           # Yeux

# --- CONVERSION ET AFFICHAGE DANS STREAMLIT ---
img_array = pygame.surfarray.array3d(surface)
img_array = np.transpose(img_array, (1, 0, 2)) # Ajustement des axes pour l'affichage image

st.image(img_array, use_column_width=True)

# Affichage des Statistiques sous le canvas
st.write(f"**Monde actuel :** {config['name']} | **Score :** {gs['score']} | **Pièces :** {gs['coins']} | **Vies :** {gs['lives']} | **Combo :** x{gs['combo']:.1f}")
st.write(f"**Arme équipée :** {gs['weapon']} (Puissance {WEAPON_SHOP[gs['weapon']]['power']})")