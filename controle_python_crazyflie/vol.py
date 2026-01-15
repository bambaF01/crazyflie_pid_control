# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2017 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
This script shows the basic use of the MotionCommander class.

Simple example that connects to the crazyflie at `URI` and runs a
sequence. This script requires some kind of location system, it has been
tested with (and designed for) the flow deck.

The MotionCommander uses velocity setpoints.

Change the URI variable to your Crazyflie configuration.
"""
import logging
import time
import sys
import threading

import pygame

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

motion_commander = None
sequence_thread = None
sequence_running = False
stop_requested = False
running = True
sync_cf = None
armed = False
joystick_control = False
current_velocity_x = 0.0
current_velocity_y = 0.0
current_velocity_yaw = 0.0

# Variables pour contrôler le PID de position verticale
pid_position_kp = 5.0  # Valeur par défaut du gain proportionnel position verticale
pid_position_step = 0.5  # Pas d'ajustement pour la position

# --------- Fonctions pour chaque bouton de la manette ---------


def on_cross(pressed: bool) -> None:
    print(f"[PS4] Croix (X) {'PRESSEE' if pressed else 'RELACHEE'}")
    global motion_commander, sync_cf, sequence_running, armed, joystick_control
    global current_velocity_x, current_velocity_y, current_velocity_yaw
    if pressed:
        if sequence_running:
            print("[SEQ] Sequence deja en cours")
            return
        if sync_cf is None:
            print("[SEQ] SyncCrazyflie non initialise")
            return
        if not armed:
            print("[PS4] Drone non arme (R1 pour armer)")
            return
        if motion_commander is None:
            motion_commander = MotionCommander(sync_cf)
        try:
            motion_commander.take_off(height=0.3)
            motion_commander.stop()
            joystick_control = True
            current_velocity_x = 0.0
            current_velocity_y = 0.0
            current_velocity_yaw = 0.0
            print("[HOVER] Stationnaire a 0.3 m")
        except Exception as e:
            print(f"[PS4] Action impossible: {e}")


def on_circle(pressed: bool) -> None:
    print(f"[PS4] Cercle (O) {'PRESSE' if pressed else 'RELACHE'}")
    global stop_requested, motion_commander, joystick_control
    if pressed:
        stop_requested = True
        joystick_control = False
        if motion_commander is not None:
            try:
                # Descente progressive et douce avant atterrissage
                print("[LAND] Descente progressive...")
                motion_commander.down(0.3, velocity=0.2)  # Descente lente de 30cm
                time.sleep(0.5)  # Petite pause pour stabilisation
                motion_commander.land(velocity=0.2)  # Atterrissage final en douceur
            except Exception as e:
                print(f"[LAND] Erreur atterrissage: {e}")
        print("[JS] Controle joystick desactive")


def on_square(pressed: bool) -> None:
    print(f"[PS4] Carre [] {'PRESSE' if pressed else 'RELACHE'}")
    global running, stop_requested, motion_commander
    if pressed:
        stop_requested = True
        if motion_commander is not None:
            try:
                # Descente progressive et douce avant atterrissage
                print("[LAND] Descente progressive...")
                motion_commander.down(0.3, velocity=0.2)  # Descente lente de 30cm
                time.sleep(0.5)  # Petite pause pour stabilisation
                motion_commander.land(velocity=0.2)  # Atterrissage final en douceur
            except Exception as e:
                print(f"[LAND] Erreur atterrissage: {e}")
        running = False


def on_triangle(pressed: bool) -> None:
    print(f"[PS4] Triangle /\ {'PRESSE' if pressed else 'RELACHE'}")
    global sequence_thread, sequence_running, motion_commander, stop_requested, armed, sync_cf
    if pressed:
        if sequence_running:
            stop_requested = True
            return
        if not armed:
            print("[PS4] Drone non arme (R1 pour armer)")
            return
        if sync_cf is None:
            print("[SEQ] SyncCrazyflie non initialise")
            return

        if motion_commander is None:
            motion_commander = MotionCommander(sync_cf)
            try:
                print("[SEQ] Decollage a 0.3 m avant la sequence...")
                motion_commander.take_off(height=0.3)
                motion_commander.stop()
            except Exception as e:
                print(f"[SEQ] Echec decollage avant sequence: {e}")
                return

        print("[SEQ] Lancement de la sequence depuis le stationnaire...")
        sequence_thread = threading.Thread(target=run_flight_sequence, daemon=True)
        sequence_thread.start()

def on_l1(pressed: bool) -> None:
    print(f"[PS4] L1 {'PRESSE' if pressed else 'RELACHE'}")


def on_r1(pressed: bool) -> None:
    print(f"[PS4] R1 {'PRESSE' if pressed else 'RELACHE'}")
    global armed, sync_cf
    if pressed:
        if sync_cf is None:
            print("[ARM] SyncCrazyflie non initialise")
            return
        try:
            if not armed:
                sync_cf.cf.platform.send_arming_request(True)
                armed = True
                print("[ARM] Drone arme")
            else:
                sync_cf.cf.platform.send_arming_request(False)
                armed = False
                print("[ARM] Drone desarme")
        except Exception as e:
            print(f"[ARM] Erreur armement/desarmement: {e}")


def on_l2_click(pressed: bool) -> None:
    print(f"[PS4] L2 (clic) {'PRESSE' if pressed else 'RELACHE'}")


def on_r2_click(pressed: bool) -> None:
    print(f"[PS4] R2 (clic) {'PRESSE' if pressed else 'RELACHE'}")


def on_share(pressed: bool) -> None:
    print(f"[PS4] Share {'PRESSE' if pressed else 'RELACHE'}")


def on_options(pressed: bool) -> None:
    print(f"[PS4] Options {'PRESSE' if pressed else 'RELACHE'}")


def on_ps(pressed: bool) -> None:
    print(f"[PS4] PS {'PRESSE' if pressed else 'RELACHE'}")


def on_touchpad(pressed: bool) -> None:
    print(f"[PS4] Touchpad {'PRESSE' if pressed else 'RELACHE'}")


def on_left_stick_click(pressed: bool) -> None:
    print(f"[PS4] Clic stick gauche {'PRESSE' if pressed else 'RELACHE'}")


def on_right_stick_click(pressed: bool) -> None:
    print(f"[PS4] Clic stick droit {'PRESSE' if pressed else 'RELACHE'}")


def on_dpad_up(pressed: bool) -> None:
    print(f"[PS4] D-Pad Haut {'PRESSE' if pressed else 'RELACHE'}")
    if pressed:
        increase_position_gain()


def on_dpad_down(pressed: bool) -> None:
    print(f"[PS4] D-Pad Bas {'PRESSE' if pressed else 'RELACHE'}")
    if pressed:
        decrease_position_gain()


def on_dpad_left(pressed: bool) -> None:
    print(f"[PS4] D-Pad Gauche {'PRESSE' if pressed else 'RELACHE'}")


def on_dpad_right(pressed: bool) -> None:
    print(f"[PS4] D-Pad Droite {'PRESSE' if pressed else 'RELACHE'}")


def set_position_gain() -> None:
    """Configure le gain PID de position verticale du drone"""
    global sync_cf, pid_position_kp
    
    if sync_cf is None:
        print("[PID] SyncCrazyflie non initialise")
        return
    
    try:
        # Paramètre PID pour la position verticale seulement
        sync_cf.cf.param.set_value('posCtlPid.zKp', pid_position_kp)
        
        print(f"[PID] Gain position applique: {pid_position_kp:.1f}")
        
    except Exception as e:
        print(f"[PID] Erreur lors de la configuration du gain: {e}")


def increase_position_gain() -> None:
    """Augmente le gain proportionnel de position verticale"""
    global pid_position_kp, pid_position_step
    pid_position_kp += pid_position_step
    if pid_position_kp > 10.0:  # Limite maximale pour position
        pid_position_kp = 10.0
    print(f"[PID] Gain position augmente: {pid_position_kp:.1f}")
    set_position_gain()


def decrease_position_gain() -> None:
    """Diminue le gain proportionnel de position verticale"""
    global pid_position_kp, pid_position_step
    pid_position_kp -= pid_position_step
    if pid_position_kp < 0.5:  # Limite minimale pour position
        pid_position_kp = 0.5
    print(f"[PID] Gain position diminue: {pid_position_kp:.1f}")
    set_position_gain()


def process_joystick_movement(js) -> None:
    """Traite les mouvements des sticks analogiques et contrôle le drone"""
    global motion_commander, joystick_control, current_velocity_x, current_velocity_y, current_velocity_yaw
    
    if not joystick_control or motion_commander is None:
        return
    
    # Lecture des axes des sticks (ajuster selon la manette)
    # Stick gauche: axe 0 (X) et axe 1 (Y) pour déplacement horizontal
    # Stick droit: axe 2 (X) pour rotation (yaw)
    
    # Stick gauche - déplacement horizontal
    stick_left_x = js.get_axis(0) if js.get_numaxes() > 0 else 0.0
    stick_left_y = js.get_axis(1) if js.get_numaxes() > 1 else 0.0
    
    # Stick droit - rotation (yaw) desactivee
    
    # Zone morte pour éviter les micro-mouvements
    dead_zone = 0.1
    max_velocity = 1.5  # Vitesse maximale en m/s
    max_yaw_rate = 45   # Vitesse de rotation maximale en degrés/s
    
    # Application de la zone morte
    if abs(stick_left_x) < dead_zone:
        stick_left_x = 0.0
    if abs(stick_left_y) < dead_zone:
        stick_left_y = 0.0
    
    # Calcul des vitesses
    velocity_x = stick_left_x * max_velocity  # Droite/Gauche
    velocity_y = -stick_left_y * max_velocity  # Avant/Arrière (inverser Y)
    velocity_yaw = 0.0  # Rotation desactivee
    
    # Envoi des commandes de vitesse seulement si elles ont changé
    if (abs(velocity_x - current_velocity_x) > 0.05 or 
        abs(velocity_y - current_velocity_y) > 0.05):
        
        try:
            motion_commander.start_linear_motion(velocity_x, velocity_y, 0.0)
            
            current_velocity_x = velocity_x
            current_velocity_y = velocity_y
            current_velocity_yaw = velocity_yaw
            
        except Exception as e:
            print(f"[JS] Erreur mouvement: {e}")


# --------- Mapping indices -> handlers (PS4 sous pygame) ---------
# ATTENTION : les index peuvent varier suivant macOS / drivers.
# On démarre avec ce mapping et on ajuste si besoin.

BUTTON_HANDLERS = {}


def setup_default_mapping_ps4(js) -> None:
    name = js.get_name()

    if "Logitech Gamepad F710" in name:
        print(
            "[JS] Mapping Logitech F710 actif : "
            "0=Bas, 1=Droite, 2=Gauche, 3=Haut"
        )
        BUTTON_HANDLERS[0] = on_cross
        BUTTON_HANDLERS[1] = on_circle
        BUTTON_HANDLERS[2] = on_square
        BUTTON_HANDLERS[3] = on_triangle
        BUTTON_HANDLERS[4] = on_l1
        BUTTON_HANDLERS[5] = on_r1
        BUTTON_HANDLERS[6] = on_l2_click
        BUTTON_HANDLERS[7] = on_r2_click
        BUTTON_HANDLERS[8] = on_share
        BUTTON_HANDLERS[9] = on_options
        BUTTON_HANDLERS[10] = on_ps
        BUTTON_HANDLERS[11] = on_touchpad
        BUTTON_HANDLERS[12] = on_left_stick_click
        BUTTON_HANDLERS[13] = on_right_stick_click
    else:
        # Indices typiques sur PS4 (a ajuster apres test)
        # Tu pourras imprimer tous les boutons pour verifier.
        # Sur ta manette, Carre et Cercle semblent inverses, on adapte donc :
        BUTTON_HANDLERS[0] = on_circle      # bouton index 0 -> Cercle
        BUTTON_HANDLERS[1] = on_cross       # bouton index 1 -> Croix
        BUTTON_HANDLERS[2] = on_square      # bouton index 2 -> Carre
        BUTTON_HANDLERS[3] = on_triangle    # souvent Triangle
        BUTTON_HANDLERS[4] = on_l1
        BUTTON_HANDLERS[5] = on_r1
        BUTTON_HANDLERS[6] = on_l2_click
        BUTTON_HANDLERS[7] = on_r2_click
        BUTTON_HANDLERS[8] = on_share
        BUTTON_HANDLERS[9] = on_options
        BUTTON_HANDLERS[10] = on_ps
        BUTTON_HANDLERS[11] = on_touchpad
        BUTTON_HANDLERS[12] = on_left_stick_click
        BUTTON_HANDLERS[13] = on_right_stick_click
        # D-Pad est souvent gere comme un HAT, pas comme des boutons

        if sys.platform.startswith("linux"):
            print(
                "[PS4] Mapping Linux actif : "
                "0=Carre, 1=Croix, 2=Cercle, 3=Triangle"
            )
            BUTTON_HANDLERS[0] = on_square
            BUTTON_HANDLERS[2] = on_circle


def run_flight_sequence() -> None:
    """Sequence: monte puis redescend."""
    global sequence_running, stop_requested, motion_commander, joystick_control, current_velocity_x, current_velocity_y, current_velocity_yaw

    if motion_commander is None:
        print("[SEQ] Aucun motion_commander actif")
        return

    sequence_running = True
    stop_requested = False

    # Arret des mouvements du joystick et stabilisation du drone
    print("[SEQ] Arret des mouvements et stabilisation...")
    try:
        motion_commander.stop()
        current_velocity_x = 0.0
        current_velocity_y = 0.0
        current_velocity_yaw = 0.0
    except Exception as e:
        print(f"[SEQ] Erreur lors de l'arret: {e}")

    print("[SEQ] Debut de la sequence de vol...")
    joystick_control = True

    try:
        time.sleep(1.0)

        print("[SEQ] Montee vers 0.7 m...")
        motion_commander.up(0.4)
        if stop_requested:
            motion_commander.stop()
            sequence_running = False
            return

        time.sleep(1)

        print("[SEQ] Retour position stationnaire a 0.3 m...")
        motion_commander.down(0.4)
        if stop_requested:
            motion_commander.stop()
            sequence_running = False
            return

        # Stoppe toute vitesse residuelle pour stabiliser
        motion_commander.stop()
        time.sleep(0.5)

        print("[SEQ] Sequence de vol terminee - position stationnaire a 0.3 m")

    except Exception as e:
        print(f"[SEQ] Erreur pendant la sequence: {e}")
    finally:
        sequence_running = False


def run_auto_sequence() -> None:
    global sequence_running, stop_requested, motion_commander, sync_cf

    if sync_cf is None:
        print("[SEQ] SyncCrazyflie non initialise")
        return

    sequence_running = True
    stop_requested = False

    # La creation du MotionCommander ne declenche pas de vol, on gere le decollage
    with MotionCommander(sync_cf) as mc:
        motion_commander = mc

        time.sleep(1)

        print("[SEQ] Debut de la sequence auto...")

        mc.take_off(height=0.3)
        mc.stop()
        time.sleep(0.5)

        mc.up(0.4)
        if stop_requested:
            mc.stop()
            sequence_running = False
            return
        mc.down(0.4)
        if stop_requested:
            mc.stop()
            sequence_running = False
            return

        # Stoppe toute vitesse residuelle pour stabiliser
        mc.stop()
        time.sleep(0.5)

    sequence_running = False



if __name__ == '__main__':
    cflib.crtp.init_drivers()

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("Aucune manette detectee.")
        sys.exit(1)

    js = pygame.joystick.Joystick(0)
    js.init()
    print("Manette detectee :", js.get_name())
    print(
        "Boutons :",
        js.get_numbuttons(),
        " Axes :",
        js.get_numaxes(),
        " Hats :",
        js.get_numhats(),
    )

    setup_default_mapping_ps4(js)

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        sync_cf = scf

        print("[ARM] Utilise R1 pour armer / desarmer le drone")
        print("[PID] D-Pad: Haut = Position Kp+, Bas = Position Kp- (controle de position)")
        
        # Initialiser le gain PID de position
        time.sleep(1)  # Attendre que la connexion soit stable
        set_position_gain()

        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                    btn_index = event.button
                    pressed = event.type == pygame.JOYBUTTONDOWN

                    handler = BUTTON_HANDLERS.get(btn_index)
                    if handler is not None:
                        handler(pressed)

                # Gestion du D-Pad (HAT) - Contrôle vitesse verticale
                if event.type == pygame.JOYHATMOTION:
                    hat_x, hat_y = event.value
                    # D-Pad Haut = Augmenter vitesse de correction
                    if hat_y == 1:
                        on_dpad_up(True)
                    # D-Pad Bas = Diminuer vitesse de correction
                    elif hat_y == -1:
                        on_dpad_down(True)

            # Traiter les mouvements du joystick
            process_joystick_movement(js)

            if not running:
                break

            clock.tick(60)

        if sequence_thread is not None and sequence_thread.is_alive():
            sequence_thread.join()

    pygame.quit()
