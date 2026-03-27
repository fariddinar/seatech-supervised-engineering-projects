import cv2
import numpy as np
import torch
from djitellopy import Tello
import time
import warnings
import math
warnings.simplefilter("ignore", FutureWarning)
start_time = time.time()

screen_width = int(1920/4)  # Mets la résolution de ton écran
screen_height = int(1080/4)
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
tello1.takeoff()
time.sleep(3) 

w, h = 360, 240
fbRange = [50, 100]
pid = [0.4, 0.4, 0]
pError = 0
fly_up = 0

# Détection avec YOLOv5

def findFace(img,target):
    
    results = model(img)  # Détection YOLO
    detections = results.xyxy[0].numpy()  # Format [x1, y1, x2, y2, conf, cls]
    clear_detections = []


    clear_detections   = detections[detections[:, 5] == 0]
    bestFace = None
    maxArea = 0
    best_conf = 0
    

    if target == False :
        #print("first init target")
        #print("clear_detections ",clear_detections)
        
        for clear_detection in clear_detections:
            x1, y1, x2, y2, conf, cls = clear_detection
            if conf > 0.5 and cls ==0 :
                if best_conf< conf : 
                    ##print("target found")
                    best_conf = conf
                    target = [x1, y1, x2, y2, conf, cls]
                    #print("best_conf ",best_conf)
                    #print("target ,", target)
        
    
    if target != False : 
        dist_min = np.inf   
        new_target= target 
        #print("all detection,",clear_detections)       
        for i in range(len(clear_detections)) :
            
            if clear_detections[i][4]>0.4 and clear_detections[i][5]==0:
                #print("i, ",i)
                #print("clear_detections i,",clear_detections[i])
                x1, y1, x2, y2, conf, cls = clear_detections[i]
                distance = math.dist((target[0], target[1]), (x1, y1)) +math.dist((target[2], target[3]), (x2, y2)) 

                #print(distance)
                if dist_min > distance :
                    dist_min = distance
                    #print(dist_min)
                    new_target = [x1, y1, x2, y2, conf, cls]
        target = new_target 
        #print("-------------------------------------------------")
        #print(target)
        #print("-------------------------------------")  
        
        x1, y1, x2, y2, conf, cls = target
        if conf > 0.5 and cls ==0 :  # Seulement les détections fiables
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            area = (x2 - x1) * (y2 - y1)
        
            bestFace = (cx, cy, area, x1, y1, x2, y2)
            ##print(cx, cy, area, x1, y1, x2, y2)

        if bestFace:
            cx, cy, area, x1, y1, x2, y2 = bestFace
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(img, (cx, cy), 5, (0, 0, 255), cv2.FILLED)
            detection_status = "Personne detectee"
            return img, [[cx, cy], x2-x1,y1],target,detection_status
        else:
            detection_status = "Aucune Personne detectee"
            return img, [[0, 0], 0, 45],target,detection_status
    else : 
        detection_status = "Aucune Personne detectee"
        return img, [[0, 0], 0, 45],target,detection_status
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
    print("area",area)

    if fbRange[0] < area < fbRange[1]:
        fb = 0

    elif  area == 0 :
        fb = 0
    elif area > fbRange[1]:
        fb = -20
    elif area < fbRange[0] :
        fb = 35

    if x == 0:
        speed = 0
        error = 0
        
    if y_haut <= 40 :
        fly_up = 50
        fb = 0
        yaw=0
    elif y_haut >= 100:
        fly_up = -50 
        fb = 0
        yaw=0
    else :
        fly_up = 0

        
    print("y:", yaw, "F:", fb,"up",fly_up)
    
    tello1.send_rc_control(0, fb, fly_up, yaw)
    
        
    return error

# Capture et traitement vidéo
target = False 
def hud(img,detection_status):
    battery_level = tello1.get_battery()
    elapsed_time = int(time.time() - start_time)  # Temps en secondes
    cv2.putText(img, f"Temps de vol: {elapsed_time}s", (250, 10), 
    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 0), 1)
    
    # Ajouter le texte avec le niveau de batterie à côté de l'icône
    cv2.putText(img, f"{battery_level}%", (5, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (51, 204, 51), 1)
    color = (0, 255, 0) if detection_status == "Personne detectee" else (0, 0, 255)
    cv2.putText(img, detection_status, (10, h - 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

    
    return img
while True:
    
    img = tello1.get_frame_read().frame
    
     # Vérifier que l'image est valide avant de la traiter
    if img is None:
        print("⚠️ Aucun cadre reçu, tentative de reconnexion...")
        time.sleep(0.1)
        continue

    
    img = cv2.resize(img, (w, h))


    img, info,target,detection_status = findFace(img,target)
    img = hud(img,detection_status)
    init = False
    #print("NOS INFO",info[1])
    pError = trackFace(info, w, pid, pError)
    cv2.imshow("Output", img)
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
tello1.land()
tello1.streamoff()
cv2.destroyAllWindows()
