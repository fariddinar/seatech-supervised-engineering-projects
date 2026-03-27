import cv2
import numpy as np
import torch
from djitellopy import Tello
import time

# Charger le modèle YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.classes = [0]  # Classe 0 correspond aux "personnes" dans le modèle COCO

# Initialisation du drone
tello1 = Tello()
tello1.connect()
print('Niveau de batterie:', tello1.get_battery())
tello1.streamon()
tello1.takeoff()
w, h = 360, 240
fbRange = [6200, 6800]
pid = [0.4, 0.4, 0]
pError = 0

# Détection avec YOLOv5
def findFace(img):
    results = model(img)  # Détection YOLO
    detections = results.xyxy[0].numpy()  # Format [x1, y1, x2, y2, conf, cls]

    bestFace = None
    maxArea = 0

    for detection in detections:
        x1, y1, x2, y2, conf, cls = detection
        if conf > 0.5:  # Seulement les détections fiables
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            area = (x2 - x1) * (y2 - y1)

            if area > maxArea:  # Garder seulement le plus grand visage
                maxArea = area
                bestFace = (cx, cy, area, x1, y1, x2, y2)

    if bestFace:
        cx, cy, area, x1, y1, x2, y2 = bestFace
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), cv2.FILLED)
        return img, [[cx, cy], area]
    else:
        return img, [[0, 0], 0]

# Suivi du visage
def trackFace(info, w, pid, pError):
    area = info[1]
    x, y = info[0]
    fb = 0
    error = x - w // 2
    speed = pid[0] * error + pid[1] * (error - pError)
    speed = int(np.clip(speed, -100, 100))

    if fbRange[0] < area < fbRange[1]:
        fb = 0
    elif area > fbRange[1]:
        fb = -20
    elif area < fbRange[0] and area != 0:
        fb = 20

    if x == 0:
        speed = 0
        error = 0

    print("Speed:", speed, "Forward/Backward:", fb)
    tello1.send_rc_control(0, fb, 0, speed)

    return error

# Capture et traitement vidéo
while True:
    img = tello1.get_frame_read().frame
    img = cv2.resize(img, (w, h))
    img, info = findFace(img)
    pError = trackFace(info, w, pid, pError)

    print("Center:", info[0], "Area:", info[1])
    cv2.imshow("Output", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
