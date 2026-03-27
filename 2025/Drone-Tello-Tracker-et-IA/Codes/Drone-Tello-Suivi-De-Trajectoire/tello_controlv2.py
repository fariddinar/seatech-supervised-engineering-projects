import math
import time
from djitellopy import Tello
import json
import keyboard

# Charger les points depuis le fichier JSON
with open('./Motion_planning/MAP/points.json', 'r') as f:
    data = json.load(f)
points = data["points"]

# Initialiser le drone
tello = Tello()
tello.connect()

# Vérifier la connexion
print(f"Battery level: {tello.get_battery()}%")

# Faire décoller le drone
tello.takeoff()
time.sleep(0.5)

# Fonction pour calculer l'angle vers le point cible
def calculate_angle_to_target(current_x, current_y, target_x, target_y):
    dx = target_x - current_x
    dy = target_y - current_y

    angle = math.degrees(math.atan2(dy, dx))
    return angle

# Fonction pour orienter le drone vers un angle donné
def orient_drone(tello, angle):
    if angle > 0:
        tello.rotate_clockwise(int(angle))
    else:
        tello.rotate_counter_clockwise(int(abs(angle)))

# Fonction pour normaliser un angle entre -180 et 180 degrés
def normalize_angle(angle):
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle

# Fonction pour déplacer le drone vers un point avec angle minimal
def move_to_point(tello, current_x, current_y, target_x, target_y, pre_angle):
    print("Current position:", current_x, current_y)
    print("Target position:", target_x, target_y)

    # Calculer l'angle vers le point cible
    target_angle = calculate_angle_to_target(current_x, current_y, target_x, target_y)

    # Calculer l'angle de rotation relatif par rapport à l'orientation précédente
    rotation_angle = target_angle - pre_angle

    # Normaliser l'angle de rotation pour qu'il soit toujours entre -180 et 180 degrés
    rotation_angle = normalize_angle(rotation_angle)

    print(f"Rotating by {rotation_angle} degrees to face target point.")
    orient_drone(tello, rotation_angle)

    # Mettre à jour l'angle précédent
    pre_angle = target_angle

    # Calculer la distance à parcourir (en cm)
    distance = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
    print(f"Moving forward by {distance} cm.")
    tello.move_forward(int(distance))
    time.sleep(0.5)

    return target_x, target_y, pre_angle


# Boucle principale pour déplacer le drone
try:
    prev_x, prev_y = 0, 0
    pre_angle = 0

    for i in range(len(points)):
        # Coordonnées du point cible
        target_x, target_y = points[i]["x"], points[i]["y"]

        # Déplacer le drone vers le point cible
        prev_x, prev_y, pre_angle = move_to_point(tello, prev_x, prev_y, target_x, target_y, pre_angle)

        # Vérifier si la touche "L" est appuyée pour atterrir immédiatement
        if keyboard.is_pressed('l'):
            print("Landing command received.")
            if tello.is_flying:
                tello.land()
            print("Drone has landed.")
            break

    # Si la boucle se termine normalement, revenir au point de départ
    if not keyboard.is_pressed('l'):
        prev_x, prev_y, pre_angle = move_to_point(tello, prev_x, prev_y, 0, 0, pre_angle)

except KeyboardInterrupt:
    print("Landing due to KeyboardInterrupt.")
    if tello.is_flying:
        tello.land()
    print("Drone has landed.")

# Atterrir si non encore atterri
if tello.is_flying:
    tello.land()
print("Drone has landed.")
