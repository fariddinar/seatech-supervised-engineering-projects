import tkinter as tk
from PIL import Image, ImageTk
from tkinter import simpledialog 
import json
import math
import random
import os
print("Répertoire de travail actuel :", os.getcwd())


# Liste des points
points = []
point_visuals = []  # Pour stocker les visuels des points ajoutés (cercle, flèche, texte, drone)
origin = None  # Pour stocker l'origine (premier point)

# Dimensions maximales de la fenêtre et du terrain de jeu (600x600 px = 6x6 m)
MAX_WIDTH = 800
MAX_HEIGHT = 600
PIXEL_TO_METER = 0.01  # 100 pixels = 1 mètre

# Liste des couleurs pour les flèches
arrow_colors = ["blue", "green", "red", "purple", "orange", "brown"]

# Fonction pour sauvegarder les points en JSON
def save_json():
    # Exclure le premier point (point de départ) du JSON
    data = {"points": [{"x": point[0], "y": point[1]} for point in points[1:]]}
    with open("motion_planning\MAP\points.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Points sauvegardés dans points.json")

# Fonction pour calculer la distance entre deux points en mètres
def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    distance_pixels = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    distance_meters = distance_pixels * PIXEL_TO_METER
    return round(distance_meters, 2)

# Fonction pour dessiner une flèche entre deux points avec la distance affichée
def draw_arrow_with_distance(start, end, color):
    x1, y1 = start
    x2, y2 = end
    # Dessiner la ligne avec une flèche
    line = canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill=color, width=2)
    
    # Calculer et afficher la distance en mètres
    distance = calculate_distance(start, end)
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2  # Positionner le texte au milieu de la flèche
    distance_text = canvas.create_text(mid_x, mid_y - 10, text=f"{distance} m", fill=color)
    
    # Retourner la ligne et le texte créés pour pouvoir les supprimer si nécessaire
    return line, distance_text

# Fonction pour ajouter un point visuellement et le lier aux autres points
def add_point(x, y):
    global origin  # Utiliser la variable globale pour l'origine
    if origin is None:  # Si c'est le premier point, le définir comme origine
        origin = (x, y)

    # Ajuster les coordonnées par rapport à l'origine
    adjusted_x = x - origin[0]
    adjusted_y = y - origin[1]
    points.append((adjusted_x, adjusted_y))
    print(f"Point ajouté : ({adjusted_x}, {adjusted_y})")

    # Dessiner un petit cercle pour visualiser le point
    point_visual = canvas.create_oval(x-3, y-3, x+3, y+3, fill='red')
    point_visuals.append(point_visual)

    # Ajouter un texte numéroté au-dessus du point
    point_number = len(points)
    text_visual = canvas.create_text(x, y-10, text=f"Point {point_number}", fill="black")
    point_visuals.append(text_visual)

    # Si c'est le premier point, afficher l'image du drone
    if point_number == 1:
        drone_visual = canvas.create_image(x, y, anchor=tk.CENTER, image=drone_photo)
        point_visuals.append(drone_visual)

    # Dessiner une flèche entre les deux derniers points avec une couleur différente et afficher la distance
    if len(points) > 1:
        color = random.choice(arrow_colors)  # Choisir une couleur aléatoire
        start_point = (origin[0] + points[-2][0], origin[1] + points[-2][1])  # Coordonnées du point précédent
        end_point = (origin[0] + points[-1][0], origin[1] + points[-1][1])  # Coordonnées du point actuel
        arrow_visual, distance_text = draw_arrow_with_distance(start_point, end_point, color)
        point_visuals.append(arrow_visual)  # Ajouter la flèche à la liste des visuels
        point_visuals.append(distance_text)  # Ajouter la distance à la liste des visuels

# Fonction appelée lorsqu'on clique sur l'image
def click_event(event):
    x, y = event.x, event.y
    add_point(x, y)

# Fonction pour supprimer tous les points et visuels du canvas
def clear_points():
    global origin
    points.clear()  # Vider la liste des points
    origin = None  # Réinitialiser l'origine
    for visual in point_visuals:  # Supprimer chaque élément visuel du canvas
        canvas.delete(visual)
    point_visuals.clear()  # Vider la liste des visuels

# Fonction pour générer un chemin aléatoire
def create_random_path():
    clear_points()  # Supprimer les points et visuels existants avant d'ajouter de nouveaux points
    num_points = simpledialog.askinteger("Chemin aléatoire", "Nombre de points à générer :")
    if num_points is not None:
        for _ in range(num_points):
            x = random.randint(0, canvas.winfo_width())
            y = random.randint(0, canvas.winfo_height())
            add_point(x, y)

# Fonction pour supprimer le dernier point ajouté et ses visuels (flèche, cercle, texte)
def remove_last_point():
    if points:
        points.pop()  # Supprimer le dernier point de la liste
        # Supprimer les derniers visuels (cercle, texte et flèche)
        last_visual = point_visuals.pop()  # Supprimer le texte
        canvas.delete(last_visual)
        last_visual = point_visuals.pop()  # Supprimer le cercle
        canvas.delete(last_visual)

        # Supprimer la dernière flèche et la distance si elle existe (après le 2e point)
        if len(points) > 1:
            last_distance_text = point_visuals.pop()
            canvas.delete(last_distance_text)
            last_arrow = point_visuals.pop()
            canvas.delete(last_arrow)
        
        # Si le dernier point supprimé était le premier, supprimer l'image du drone
        if len(points) == 0 or len(points) == 0:  # Pas de points restants ou premier point supprimé
            last_drone_visual = point_visuals.pop() if point_visuals else None
            if last_drone_visual:
                canvas.delete(last_drone_visual)

        print("Dernier point et ses visuels supprimés.")

# Redimensionner l'image tout en maintenant les proportions
def resize_image(image, max_width, max_height):
    ratio = min(max_width/image.width, max_height/image.height)
    new_width = int(image.width * ratio)
    new_height = int(image.height * ratio)
    return image.resize((new_width, new_height), Image.LANCZOS)

# Fenêtre Tkinter
root = tk.Tk()
root.title("Sélectionnez les points sur la carte")

# Charger l'image de la carte directement
try:
    image = Image.open("motion_planning\MAP\map.png")  # Chargement de l'image map.png
except FileNotFoundError:
    print("Erreur : le fichier 'map.png' est introuvable.")
    root.destroy()  # Fermer la fenêtre si le fichier n'existe pas
    raise

# Redimensionner l'image si elle dépasse la taille maximale
image = resize_image(image, MAX_WIDTH, MAX_HEIGHT)
photo = ImageTk.PhotoImage(image)

# Canvas pour afficher l'image
canvas = tk.Canvas(root, width=image.width, height=image.height)
canvas.pack()
canvas.create_image(0, 0, anchor=tk.NW, image=photo)

# Lier le clic de la souris à l'événement de capture des points
canvas.bind("<Button-1>", click_event)

# Ajouter une légende pour indiquer les dimensions du terrain de jeu
legend_label = tk.Label(root, text="Dimensions du terrain : 600x600 px (6x6 m)", font=("Arial", 12))
legend_label.pack()

# Charger l'image du drone après la création de la fenêtre
drone_image = Image.open("motion_planning\MAP\drone.png")  # Assure-toi d'avoir une image de drone au format PNG ou JPG
drone_image = drone_image.resize((70, 60), Image.LANCZOS)  # Ajuster la taille à 50x50 pixels
drone_photo = ImageTk.PhotoImage(drone_image)

# Bouton pour sauvegarder les points en JSON
save_button = tk.Button(root, text="Sauvegarder en JSON", command=save_json)
save_button.pack()

# Bouton pour supprimer le dernier point
remove_button = tk.Button(root, text="Supprimer le dernier point", command=remove_last_point)
remove_button.pack()

# Bouton pour créer un chemin aléatoire
random_path_button = tk.Button(root, text="Chemin aléatoire", command=create_random_path)
random_path_button.pack()

# Lancer la fenêtre
root.mainloop()
