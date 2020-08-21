from time import sleep
import sys
import json

from datetime import datetime  
from datetime import timedelta  
import argparse

from twilio.rest import Client
import cv2
import mysql.connector
from gtts import gTTS
import os
import win32com.client
import random
from gpiozero import Buzzer, LED
from gpiozero.pins.pigpio import PiGPIOFactory

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json

from IOTAssignmentClientdorachua.GrabCarClient import GrabCarClient
from IOTAssignmentUtilitiesdorachua.MySQLManager import MySQLManager
from IOTAssignmentUtilitiesdorachua.MySQLManager import QUERYTYPE_DELETE, QUERYTYPE_INSERT
import dynamodb

def customCallback(client, userdata, message):
    payload = json.loads((message.payload))
    speedkmhour = payload['speedkmhour']
    datetime_value = payload['datetime_value']
    bid = payload['bookingid']
    print("speed is ", speedkmhour)
    if speedkmhour >= 0:
        cam = cv2.VideoCapture("http://27.104.173.113:8081/out.jpg")                          
        ret, frame = cam.read()
        if not ret:
            exit()
        imgpathaddon = datetime_value.replace(":",".") + ".jpg"
        imgname = bid+"_"+imgpathaddon
        success = dynamodb.uploadImageFileToS3(frame,imgname)
        if success:
            print("image of the driver captured")
        cam.release() 

        account_sid = ""
        auth_token = ""

        client = Client(account_sid, auth_token)
        sms = "Dear Driver, at *{}*, It was identified that you drove at a speed of *{}*, which is beyond the maximum speed limit of 90km/hr. Please drive slower so as to provide the passenger a more pleasant ride. \nBy Grab\nBooking ID : *{}*".format(datetime_value,speedkmhour,bid)
        #message = client.messages.create(to=my_hp,from_=twilio_hp,body=sms, mediaUrl=imgname) 
        client.messages.create(body=sms,
            media_url = ['http://27.104.173.113:8081/out.jpg'],
            from_='whatsapp:+14155238886',
            to='whatsapp:+6598421399')
        print("message sent")

        # alert driver with IOT device
        factory = PiGPIOFactory(host='192.168.72.205')
        led= LED(21,pin_factory=factory)
        buzzer = Buzzer(27, pin_factory=factory)
        led.blink()
        buzzer.beep()
        sleep(1) # blink and sound alarm for 3 seconds
        led.off()
        buzzer.off()

def getData(gcc,datetime_start,my_rpi):    
    while True:
        try:
            reading = gcc.get_reading()            

            if reading is not None and len(reading)>0:
                readings = json.loads(reading)
                    
                for str_reading in readings:
                    r = json.loads(str_reading)
                    print(r)
                
                    deviceid = "deviceid_zhiyang"
                    bid = r["bookingid"]                                                
                    seconds = r["seconds"]
                    speed = r["speed"]
                    speedkmhour = r["speedkmhour"]
            
                    datetime_value = datetime_start + timedelta(seconds=seconds)
                    datetime_value = datetime_value.strftime('%Y-%m-%d %H:%M:%S') 
                    datetimestart_value = str(datetime_start)
                    bidwithtime = f"{bid}_{datetimestart_value}"
                    imgpathaddon = datetime_value.replace(":",".") + ".jpg"
                    imgname = bid+"_"+imgpathaddon
                    #print(f"bid,seconds,speed,speedkmhour,datetime_value {bid} {seconds} {speed} {speedkmhour} {datetime_value}")
                    iottabledata = {'device_id':deviceid, 'bookingid': bid , 'bookingidwithtime':bidwithtime,'datetimestart_value':datetimestart_value,'seconds': seconds,'speed': speed,
                    'speedkmhour': speedkmhour, 'datetime_value':datetime_value} 

                    randLat = random.uniform(1.2489458, 1.435562)
                    randLong = random.uniform(103.665025,103.99032758267639)
                    mapdata = {'bookingid':bid, 'datetime_value':datetime_value, 'datetimestart_value':datetimestart_value, 'Latitude':randLat, 'Longitude':randLong}
                    imageData = {'VehicleType':'GrabCar', 'datetime_value':datetime_value, 'bookingid':bid, 'KeyName':imgname, 'speedkmhour':speedkmhour}
                    my_rpi.publish("iotdatabase/image", json.dumps(imageData), 1)
                    print("published to image")
                    my_rpi.publish("iotdatabase/map", json.dumps(mapdata), 1)
                    print("published to map")
                    my_rpi.publish("iotdatabase/modeldata", json.dumps(r),1)
                    print("published to modeldata")
                    my_rpi.publish("iotdatabase/iotapp", json.dumps(iottabledata), 1)
                    print("published to iotapp")    
                    
                    my_rpi.subscribe("iotdatabase/iotapp", 1, customCallback) 
                    print("subscibed to iotapp")            
                    
            yield             

        except GeneratorExit:
            print("Generator Exit error")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return

        except KeyboardInterrupt:
            exit(0)


        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])


if __name__ == "__main__":

    try:                 
        host,port = "127.0.0.1", 8889
        parser = argparse.ArgumentParser()
        parser.add_argument('host')
        parser.add_argument('port',type=int)
        
        args = parser.parse_args()
        if args.host:
            host = args.host
        if args.port:
            port = args.port

        mygcc = GrabCarClient(host,port)

        host = "a3kfg2bxlkhyhy-ats.iot.us-east-1.amazonaws.com"
        rootCAPath = "certs/rootca.pem"
        certificatePath = "certs/certificate.pem.crt"
        privateKeyPath = "certs/private.pem.key"

        my_rpi = AWSIoTMQTTClient("p1828430")
        my_rpi.configureEndpoint(host, 8883)
        my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

        my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
        my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
        my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect and subscribe to AWS IoT
        my_rpi.connect()

        print("Streaming started")        
        datetime_start = datetime.now()
        gen = getData(mygcc,datetime_start,my_rpi)

        while True:
            next(gen)
            sleep(2)
        
    except KeyboardInterrupt:
        print('Interrupted')        
        sys.exit()


    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])       




