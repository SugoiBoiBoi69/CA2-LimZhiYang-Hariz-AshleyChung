from flask import Flask, render_template, jsonify, request,Response,redirect,url_for

import argparse
import sys

import json
import dynamodb
import jsonconverter as jsonc

import cv2

import pandas as pd
from pandas import DataFrame
import numpy as np
import warnings
warnings.filterwarnings("ignore")
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import botocore
import boto3
from boto3.dynamodb.conditions import Key, Attr

import mysql.connector
from gevent.pywsgi import WSGIServer

from datetime import datetime
from twilio.rest import Client

from IOTAssignmentUtilitiesdorachua.MySQLManager import MySQLManager

from IOTAssignmentUtilitiesdorachua.MySQLManager import QUERYTYPE_DELETE, QUERYTYPE_INSERT

import boto3
from boto3.dynamodb.conditions import Key, Attr
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import pandas as pd


app = Flask(__name__)

@app.route("/api/getdata",methods=['GET', 'POST'])
def apidata_getdata():
    try:
        maxdatetimestart = dynamodb.get_maxdatetimestart_from_dynamodb()
        data_reversed = dynamodb.get_top10data_from_dynamodb(maxdatetimestart)
        datarows = jsonc.data_to_json(data_reversed)
        
        #return data_reversed'''

        return jsonify(json.loads(datarows))
        
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/getDashboardDetails",methods=['GET', 'POST'])
def apidata_getTotalNumOfVehicles():
    try:
        datarows = []
        maxdatetimestart = dynamodb.get_maxdatetimestart_from_dynamodb()     
        datarows.append(dynamodb.get_numofbid_and_maxspeed(maxdatetimestart))
        datarows.append(dynamodb.getDistinctBidandAvgSpeedandCount(maxdatetimestart))

        return jsonify(json.loads(jsonc.data_to_json(datarows)))  

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/getSummaryTable",methods=['GET', 'POST'])
def apidata_getSummaryTable():
    try:
        data = dynamodb.getSummaryTableData()
        return jsonify(json.loads(jsonc.data_to_json(data)))
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])   

@app.route("/api/getIndividualBooking/<string:bid>",methods=['GET', 'POST'])
def getBooking(bid):
    try:
        dataRows = dynamodb.getindividualBookingData(bid)

        return jsonify(json.loads(jsonc.data_to_json(dataRows)))

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])    

@app.route("/individualBooking/<string:bid>",methods=['GET', 'POST'])
def detailedtable(bid):
    try:
        bookingid = bid

        return render_template('detailed-table.html',bookingid=bookingid)  

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])  

@app.route("/api/getIndividualSpeedDetails/<string:bid>",methods=['GET', 'POST'])
def getIndividualSpeedDetails(bid):
    try:
        bookingid = bid
        data = dynamodb.getIndivividualDashboard(bookingid)
        
        return jsonify(json.loads(jsonc.data_to_json(data)))    

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/getIndividualMapData/<bid>", methods=['GET', 'POST'])
def getIndividualMapData(bid):
    try:
        bookingid = bid
        mapdata = dynamodb.getIndividualMapData(bookingid)
        
        return jsonify(json.loads(jsonc.data_to_json(mapdata)))

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/captureDriverImage/<bid>",methods=['GET', 'POST'])
def captureDriverImage(bid):
    try:
        bookingid = bid
        cam = cv2.VideoCapture("http://27.104.173.113:8081/out.jpg")                          
        ret, frame = cam.read()
        if not ret:
            exit()
        currentdatetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        imgpathaddon = currentdatetime.replace(":",".") 
        imgpathaddon = imgpathaddon.replace(" ","_")+ ".jpg"
        imgname = bookingid+"_"+imgpathaddon
        success = dynamodb.uploadImageFileToS3(frame,imgname)
        print(success)
        #cv2.imwrite(imgname,frame)
        print(imgname)
        cam.release()

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
        imageData = {'VehicleType':'GrabCar', 'datetime_value':currentdatetime, 'bookingid':bookingid, 'KeyName':imgname}
        my_rpi.publish("iotdatabase/image", json.dumps(imageData), 1)

        return jsonify(json.loads(jsonc.data_to_json(success)))
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/getDriverImage/<bid>",methods=['GET', 'POST'])
def getDriverImage(bid):
    try:
        bookingid = bid
        data = []
        image, facesimilarity, ageDetails = dynamodb.retrieveImageFromS3(bookingid)
        data = [image, facesimilarity, ageDetails]
        return jsonify(json.loads(jsonc.data_to_json(data)))
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/checkCapturedImageIndex/<bid>",methods=['GET', 'POST'])
def checkLatestImage(bid):
    try:
        bookingid = bid
        data = []
        image, facesimilarity, ageDetails = dynamodb.retrieveImageFromS3forIndex(bookingid)
        data = [image, facesimilarity, ageDetails]
        return jsonify(json.loads(jsonc.data_to_json(data)))
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/getDriverSpeedingDetails", methods=['GET', 'POST'])
def getDriverSpeedingDetails():
    try:
        driversImages = dynamodb.getLatest3DriversthatSped()

        return jsonify(json.loads(jsonc.data_to_json(driversImages)))

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/getMapData", methods=['GET', 'POST'])
def getMapData():
    try:
        data = []
        maxdatetimestart = dynamodb.get_maxdatetimestart_from_dynamodb()
        listofBID = dynamodb.getListofBIDforLatestDTS()
        for bid in listofBID:
            data.append(dynamodb.getMapData(bid,maxdatetimestart))

        return jsonify(json.loads(jsonc.data_to_json(data)))

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/sendAlert/<bid>/<speed>",methods=['GET', 'POST'])
def sendAlert(bid = None,speed = None):
    try:
        bookingid = bid
        carspeed = speed

        # INSERT ACCOUNT SID AND AUTH TOKEN HERE AND PHONE NUMBER

        account_sid = ""
        auth_token = ""

        client = Client(account_sid, auth_token)
        sms = "It was identified that you drove at a speed of *{}*, which is beyond the maximum speed limit of 90km/hr. Please drive slower so as to provide the passenger a more pleasant ride. \nBy Grab\nBooking ID : *{}*".format(carspeed,bookingid)
        #message = client.messages.create(to=my_hp,from_=twilio_hp,body=sms, mediaUrl=imgname) 
        client.messages.create(body=sms,
            from_='whatsapp:+14155238886',
            to='whatsapp:+6598421399')

        return("message sent successfully")
    
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/api/predictSafety/<bid>",methods=['GET', 'POST'])
def predictSafety(bid):
    try:
        # Obtain SQL Reading for selected BookingID (SQLQuery)
        # https://www.kite.com/python/answers/how-to-convert-an-sql-query-result-to-a-pandas-dataframe-in-python
        # https://stackoverflow.com/questions/12047193/how-to-convert-sql-query-result-to-pandas-data-structure

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('modedata')
        response = table.query(
            KeyConditionExpression = Key('bookingid').eq(bid)
        )
        datarows = response['Items']

        df = pd.DataFrame(datarows,dtype=float)

        #resoverall is yr sql statement
        # df = DataFrame(resoverall.fetchall())
        # df.columns = resoverall.keys()
        df.drop(['accuracy'], axis=1, inplace=True)

        df['acceleration'] = np.sqrt((df.loc[:, ('acceleration_x', 'acceleration_y', 'acceleration_z')] ** 2).sum(axis=1))
        df.drop(['acceleration_x', 'acceleration_y','acceleration_z','speedkmhour'], axis=1, inplace=True)

        pca_gyro = PCA(n_components=1).fit(df.loc[:, ['gyro_x', 'gyro_y', 'gyro_z']])
        df['gyro'] = pca_gyro.transform(df.loc[:, ('gyro_x', 'gyro_y', 'gyro_z')])
        df.drop(['gyro_x', 'gyro_y','gyro_z'], axis=1, inplace=True)

        data = pd.DataFrame()
        for col in df.columns:
            if col != "bookingid" and col != "label":
                temp = df.groupby("bookingid")[col].agg(["mean", "sum", "max", "min"])
                data[col + "_mean"] = temp["mean"]
                data[col + "_sum"] = temp["sum"]
                data[col + "_max"] = temp["max"]
                data[col + "_min"] = temp["min"]
        #data = data.drop(columns=["bookingid"]).reset_index(drop=True)
        data.drop(columns=["seconds_min"], inplace=True)

        # generate distance, velocity and angle features
        for col in data.columns:
            if col.startswith("seconds"):
                agg_method = col.split("_")[1]
                data["distance_" + agg_method] = data[col] * data["speed_" + agg_method]
                data["velocity_" + agg_method] = data[col] * data["acceleration_" + agg_method]
                data["angle_" + agg_method] = data[col] * data["gyro_" + agg_method]

        data = data.drop(columns=['seconds_sum','seconds_mean']).reset_index(drop=True)

        # Once Obtain model after hyper tuning save weights here and predict

        from joblib import load

        sr = load("GBR.joblib")
        y_pred = sr.predict(data)
        print("regression value: ", y_pred[0])
        return jsonify(json.loads(jsonc.data_to_json(y_pred[0])))

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

@app.route("/summary-table")
def summarytable():
    return render_template('summary-table.html')

@app.route("/map")
def map():
    return render_template('map-google.html')

@app.route("/")
def home():
    return render_template('index.html')

if __name__ == '__main__':
   try:
        host = '0.0.0.0'
        port = 80
        parser = argparse.ArgumentParser()        
        parser.add_argument('port',type=int)
        
        args = parser.parse_args()
        if args.port:
            port = args.port
                
        http_server = WSGIServer((host, port), app)
        app.debug = True
        print('Web server waiting for requests')
        http_server.serve_forever()

       

   except:
        print("Exception while running web server")
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])
