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


while True:
    fly_up = 50
    tello1.send_rc_control(0, 0, fly_up, 0)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
tello1.land()
tello1.streamoff()
cv2.destroyAllWindows()
