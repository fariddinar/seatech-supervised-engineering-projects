import cv2
import numpy as np
import torch
from djitellopy import Tello
import time
import warnings

warnings.simplefilter("ignore", FutureWarning)


screen_width = 1400  # Mets la résolution de ton écran
screen_height = 800

cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Output", screen_width, screen_height)
# Charger le modèle YOLOv5n-Face depuis un repo local
# Charger le modèle YOLOv5n
model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
    

# Initialisation du drone
tello1 = Tello()
tello1.connect()
print('Niveau de batterie:', tello1.get_battery())
tello1.streamon()
time.sleep(2) 
#tello1.takeoff()
time.sleep(3)
start_time = time.time()

w, h = 360, 240
fbRange = [28000, 30000]
pid = [0.4, 0.4, 0]
pError = 0
fly_up = 0

detection_status = "";

# Détection avec YOLOv5

def findFace(img):
    results = model(img)  # Détection YOLO
    detections = results.xyxy[0].numpy()  # Format [x1, y1, x2, y2, conf, cls]

    bestFace = None
    maxArea = 0

    for detection in detections:
        #AJOUTER BLOQUE SI NON DETECTIONS 
        x1, y1, x2, y2, conf, cls = detection
        if conf > 0.5:  # Seulement les détections fiables
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            area = (x2 - x1) * (y2 - y1)

            if area > maxArea:  # Garder seulement le plus grand visage
                maxArea = area
                bestFace = (cx, cy, area, x1, y1, x2, y2)
                #print(cx, cy, area, x1, y1, x2, y2)
    if bestFace:
        cx, cy, area, x1, y1, x2, y2 = bestFace
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), cv2.FILLED)
        detection_status = "Personne detectee"
        return img, [[cx, cy], area,y1],detection_status
    else:
        detection_status = "Aucune personne detectee"
        return img, [[0, 0], 0, 45],detection_status

# Suivi du visage
def trackFace(info, w, pid, pError):
    #print("info",info)
    area = info[1]
    x, y = info[0]
    fb = 0
    error = x - w // 2
    if pError == 0:
        yaw = 0
    else:
        yaw = pid[0] * error + pid[1] * (error - pError)
        yaw = int(np.clip(yaw, -100, 100))

    y_haut = info[-1]
    print("y_haut",y_haut)
    print("pError ",pError)
    print("Error ",error)
    #if x_haut =<
    if fbRange[0] < area < fbRange[1]:
        fb = 0

    if  area == 0 :
        fb = 0
    elif area > fbRange[1]:
       
        fb = -10
    elif area < fbRange[0] :
        fb = 35

    if x == 0:
        speed = 0
        error = 0
        
    if y_haut <= 40 :
        fly_up = 50
        yaw = 0
        fb = 0
    elif y_haut >= 70:
        fly_up = -10
        yaw = 0
        fb = 0
    else :
        fly_up = 0
        
    print("y:", yaw, "F:", fb,"up",fly_up)
    
    tello1.send_rc_control(0, fb, fly_up, yaw)
    
        
    return error

# Capture et traitement vidéo

while True:
    
    img = tello1.get_frame_read().frame
    
     # Vérifier que l'image est valide avant de la traiter
    if img is None:
        print("⚠️ Aucun cadre reçu, tentative de reconnexion...")
        time.sleep(0.1)
        continue
    
    img = cv2.resize(img, (w, h))
    img, info,detection_status = findFace(img)
    #print("NOS INFO",info[1])
    pError = trackFace(info, w, pid, pError)
    # Récupérer le niveau de batterie
    battery_level = tello1.get_battery()
    # Ajouter le texte avec le niveau de batterie à côté de l'icône
    cv2.putText(img, f"{battery_level}%", (5, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (51, 204, 51), 1)
    # Calcul du temps écoulé depuis le décollage
    elapsed_time = int(time.time() - start_time)  # Temps en secondes
    # Affichage du temps de vol en haut à droite
    cv2.putText(img, f"Temps de vol: {elapsed_time}s", (250, 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 0), 1)
    
    color = (0, 255, 0) if detection_status == "Personne detectee" else (0, 0, 255)
    cv2.putText(img, detection_status, (10, h - 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)


    #print("Center:", info[0], "Area:", info[1])
    cv2.imshow("Output", img)
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
tello1.land()
tello1.streamoff()
cv2.destroyAllWindows()
