# import the necessary packages
from picamera2 import Picamera2
import RPi.GPIO as GPIO
import time
import cv2
import numpy as np

#hardware work
GPIO.setmode(GPIO.BOARD)

GPIO_TRIGGER1 = 29      #Right ultrasonic sensor
GPIO_ECHO1 = 31

GPIO_TRIGGER3 = 33      #Left ultrasonic sensor
GPIO_ECHO3 = 35

GPIO_TRIGGER5 = 13      #Back ultrasonic sensor
GPIO_ECHO5 = 15


MOTOR1B=21  #Left Motor
MOTOR1E=19

MOTOR2B=22  #Right Motor
MOTOR2E=18


# Set pins as output and input
GPIO.setup(GPIO_TRIGGER1,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO1,GPIO.IN)      # Echo
GPIO.setup(GPIO_TRIGGER3,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO3,GPIO.IN)      # Echo
GPIO.setup(GPIO_TRIGGER5,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO5,GPIO.IN)      # Echo


# Set trigger to False (Low)
GPIO.output(GPIO_TRIGGER1, False)
GPIO.output(GPIO_TRIGGER3, False)
GPIO.output(GPIO_TRIGGER5, False)

def sonar(GPIO_TRIGGER,GPIO_ECHO):
      start=0
      stop=0
      GPIO.setup(GPIO_TRIGGER,GPIO.OUT)
      GPIO.setup(GPIO_ECHO,GPIO.IN)
      GPIO.output(GPIO_TRIGGER, False)
      time.sleep(0.01)
      GPIO.output(GPIO_TRIGGER, True)
      time.sleep(0.00001)
      GPIO.output(GPIO_TRIGGER, False)
      begin = time.time()
      while GPIO.input(GPIO_ECHO)==0 and time.time()<begin+0.05:
            start = time.time()
      while GPIO.input(GPIO_ECHO)==1 and time.time()<begin+0.1:
            stop = time.time()
      elapsed = stop-start
      distance = elapsed * 34000
      distance = distance / 2
      print("Distance : %.1f" % distance)
      return distance

GPIO.setup(MOTOR1B, GPIO.OUT)
GPIO.setup(MOTOR1E, GPIO.OUT)
GPIO.setup(MOTOR2B, GPIO.OUT)
GPIO.setup(MOTOR2E, GPIO.OUT)

def reverse():
      GPIO.output(MOTOR1B, GPIO.HIGH)
      GPIO.output(MOTOR1E, GPIO.LOW)
      GPIO.output(MOTOR2B, GPIO.HIGH)
      GPIO.output(MOTOR2E, GPIO.LOW)

def forward():
      GPIO.output(MOTOR1B, GPIO.LOW)
      GPIO.output(MOTOR1E, GPIO.HIGH)
      GPIO.output(MOTOR2B, GPIO.LOW)
      GPIO.output(MOTOR2E, GPIO.HIGH)

def rightturn():
      GPIO.output(MOTOR1B, GPIO.LOW)
      GPIO.output(MOTOR1E, GPIO.HIGH)
      GPIO.output(MOTOR2B, GPIO.HIGH)
      GPIO.output(MOTOR2E, GPIO.LOW)

def leftturn():
      GPIO.output(MOTOR1B, GPIO.HIGH)
      GPIO.output(MOTOR1E, GPIO.LOW)
      GPIO.output(MOTOR2B, GPIO.LOW)
      GPIO.output(MOTOR2E, GPIO.HIGH)

def stop():
      GPIO.output(MOTOR1E, GPIO.LOW)
      GPIO.output(MOTOR1B, GPIO.LOW)
      GPIO.output(MOTOR2E, GPIO.LOW)
      GPIO.output(MOTOR2B, GPIO.LOW)

#Image analysis work
def segment_colour(frame):    #returns only the red colors in the frame
    hsv_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_1 = cv2.inRange(hsv_roi, np.array([160, 160, 10]), np.array([180, 255, 255]))
    ycr_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    mask_2 = cv2.inRange(ycr_roi, np.array((0., 165., 0.)), np.array((255., 255., 255.)))
    mask = mask_1 | mask_2
    kern_dilate = np.ones((8,8),np.uint8)
    kern_erode  = np.ones((3,3),np.uint8)
    mask= cv2.erode(mask,kern_erode)
    mask=cv2.dilate(mask,kern_dilate)
    return mask

def find_blob(blob):
    largest_contour=0
    cont_index=0
    contours, hierarchy = cv2.findContours(blob, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for idx, contour in enumerate(contours):
        area=cv2.contourArea(contour)
        if (area > largest_contour):
            largest_contour=area
            cont_index=idx
    r=(0,0,2,2)
    if len(contours) > 0:
        r = cv2.boundingRect(contours[cont_index])
    return r, largest_contour

#CAMERA CAPTURE
camera = Picamera2()
config = camera.create_preview_configuration(main={"size": (160, 120), "format": "RGB888"})
camera.configure(config)
camera.start()

time.sleep(0.1)

flag=0

while True:

      # Setting up Camera
      frame = camera.capture_array()
      frame = cv2.flip(frame, -1)
      centre_x=0.
      centre_y=0.
      mask_red=segment_colour(frame)
      loct,area=find_blob(mask_red)
      x,y,w,h=loct

      # Sensors
      distanceR = sonar(GPIO_TRIGGER1,GPIO_ECHO1)
      distanceL = sonar(GPIO_TRIGGER3,GPIO_ECHO3)
      distanceB = sonar(GPIO_TRIGGER5,GPIO_ECHO5)

      if (w*h) < 10:
            found=0
      else:
            found=1
            simg2 = cv2.rectangle(frame, (x,y), (x+w,y+h), 255,2)
            centre_x=x+((w)/2)
            centre_y=y+((h)/2)
            cv2.circle(frame,(int(centre_x),int(centre_y)),3,(0,110,255),-1)
            centre_x-=80
            centre_y=60-centre_y
            print(centre_x, centre_y)
     
      initial=750
      initial2=2000

      if (distanceL<5 or distanceR<5):
            if distanceB<15:                    # Back Sensor
                  stop()
                  time.sleep(0.0125)
            else:
                  forward()
                  time.sleep(0.00625)

      elif(found==0):
            if flag==0:
                  rightturn()
                  time.sleep(0.075)
            else:
                  leftturn()
                  time.sleep(0.075)
            stop()
            time.sleep(0.0125)

      elif(found==1):
            if(area>initial2):                  # Ball is too Close
                  if(centre_x<=-25 or centre_x>=25):
                              if(centre_x<0):
                                    flag=1
                                    leftturn()
                                    time.sleep(0.05)
                                    stop()
                                    time.sleep(0.0125)
                              elif(centre_x>0):
                                    flag=0
                                    rightturn()
                                    time.sleep(0.05)
                                    stop()
                                    time.sleep(0.0125)
                  else:      
                        if distanceB<15:
                              stop()
                              time.sleep(0.0125)
                        else:
                              forward()
                              time.sleep(0.25)
                              stop()
                              time.sleep(0.0125)
      
            elif(area<initial):                 # Ball is too Far
                  if centre_x > 25:
                        rightturn()
                        time.sleep(0.05)
                        stop()
                        time.sleep(0.0125)
                  elif centre_x < -25:
                        leftturn()
                        time.sleep(0.05)
                        stop()
                        time.sleep(0.0125)
                  elif (centre_y<-45 or centre_y>30):
                        stop()
                        time.sleep(0.0125)
                  else:
                        reverse()
                        time.sleep(0.125)
                        stop()
                        time.sleep(0.0125)
            else:                               # Ball is at a Good Distance
                  if(centre_x<-15):
                        flag=1
                        leftturn()
                        time.sleep(0.05)
                        stop()
                        time.sleep(0.00625)
                  elif(centre_x>15):
                        flag=0
                        rightturn()
                        time.sleep(0.05)
                        stop()
                        time.sleep(0.00625)                  

      #Debugging Purposes, making sure the ball is seen
      cv2.imshow("Camera feed", frame)
      cv2.imshow("Red mask", mask_red)

      if(cv2.waitKey(1) & 0xff == ord('q')):
            break

stop()
camera.stop()
cv2.destroyAllWindows()
GPIO.cleanup()