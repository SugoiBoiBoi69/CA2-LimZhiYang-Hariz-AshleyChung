import boto3
from boto3.dynamodb.conditions import Key, Attr
import botocore
import jsonconverter as jsonc
import json
from flask import jsonify
import sys
import cv2
import base64 
import io
from io import BytesIO
from PIL import Image, ImageDraw, ExifTags, ImageColor

def getListofBIDforLatestDTS():
    try:
        bidList = []
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        maxdatetimestart = get_maxdatetimestart_from_dynamodb()
        response = table.query(
            KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
            FilterExpression = Key('datetimestart_value').eq(maxdatetimestart),
            ProjectionExpression = 'bookingid'
        )
        item = response['Items']
        for i in item:
            currentbid = i.get('bookingid')
            if currentbid not in bidList:
                bidList.append(currentbid)

        return bidList

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def getListofAllBID():
    try:
        bidList = []
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        response = table.query(
            KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
            ProjectionExpression = 'bookingid'
        )
        item = response['Items']
        for i in item:
            currentbid = i.get('bookingid')
            if currentbid not in bidList:
                bidList.append(currentbid)

        return bidList

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def get_maxdatetimestart_from_dynamodb():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')

        response = table.query(
            KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
            ProjectionExpression = 'datetimestart_value',
            ScanIndexForward = False,
            Limit = 1
        )        
        datetime_start = response['Items']
        #datetime_start = items[-1]['datetimestart_value']
        return datetime_start[0].get('datetimestart_value')

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def get_maxdatetimestart_forbookingid(bookingid):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        response = table.query(
            KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
            ProjectionExpression = 'datetimestart_value',
            FilterExpression = Key('bookingid').eq(bookingid),
            ScanIndexForward = False
        )

        datetimestartvalue = response['Items']

        return datetimestartvalue[0].get('datetimestart_value')

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def get_top10data_from_dynamodb(datetimestart_value):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        response = table.scan(
            FilterExpression = Key('datetimestart_value').eq(datetimestart_value)
        )
        rows = response['Items']
        n=10 # limit to last 10 items
        extractedrows = rows[:n]

        return extractedrows

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def get_numofbid_and_maxspeed(datetimestart_value):
    try:
        data = []
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        numofbid = len(getListofBIDforLatestDTS())
        data.append(numofbid)

        response = table.query(
            KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
            ProjectionExpression = 'speedkmhour, bookingid',
            FilterExpression = Key('datetimestart_value').eq(datetimestart_value)
        )
        maxspeedlist = response['Items']
        maxspeedlist = jsonc.data_to_json(maxspeedlist)
        maxspeed = 0.0
        bidWithMaxSpeed = ''
        for i in json.loads(maxspeedlist):
            currentspeed = i.get('speedkmhour')
            if currentspeed > maxspeed:
                maxspeed = currentspeed
                bidWithMaxSpeed = i.get('bookingid')
        data.append(round(maxspeed,2))
        data.append(bidWithMaxSpeed)

        return data

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def getDistinctBidandAvgSpeedandCount(datetimestart_value):
    try:
        data = []
        bidData = []

        bidList = []
        bidCounter = []
        bidTotalSpeed = []
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        response = table.query(
            KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
            FilterExpression = Key('datetimestart_value').eq(datetimestart_value),
            ProjectionExpression = 'bookingid, speedkmhour'
        )
        items = response['Items']
        items = jsonc.data_to_json(items)
        for i in json.loads(items):
            currentbid = i.get('bookingid')
            currentbidspeed = i.get('speedkmhour')
            if currentbid not in bidList:
                bidList.append(currentbid)
                bidCounter.append(1)
                bidTotalSpeed.append(currentbidspeed)
            else:
                index = bidList.index(currentbid)
                totalspeed = bidTotalSpeed[index]
                bidTotalSpeed[index] = totalspeed + currentbidspeed
                totalcount  = bidCounter[index]
                bidCounter[index] = totalcount+1  

        for i in range(len(bidList)):
            bidData = []
            bidData.append(bidList[i])
            totalspeed = bidTotalSpeed[i]
            avgspeed = totalspeed / bidCounter[i]
            bidData.append(round(avgspeed,2))
            bidData.append(bidCounter[i])
            data.append(bidData)
        
        return data
        
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def getSummaryTableData():
    try:
        data = []
        datetimestartList = []

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        listofbid = getListofAllBID()

        for bid in listofbid:
            bidData = [bid]
            response = table.query(
                KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
                ProjectionExpression = 'seconds, speedkmhour, datetime_value , datetimestart_value',
                FilterExpression = Key('bookingid').eq(bid)
            )
            items = response['Items']
            items = jsonc.data_to_json(items)
            numofreadings = response['Count']

            counter = 0
            prevSpeed = 0.0
            latestSpeed = 0.0
            totalspeed = 0.0
            totalduration = 0
            latestdatetime = ''
            speedingCounter = 0
            datetimestartList = []
            
            for i in json.loads(items):
                counter +=1
                totalduration += i.get('seconds')
                speed = i.get('speedkmhour')
                datetimestartvalue = i.get('datetimestart_value')
                if datetimestartvalue not in datetimestartList:
                    datetimestartList.append(datetimestartvalue)
                if speed > 90: 
                    speedingCounter += 1
                if counter == 1:
                    latestSpeed = speed
                    latestdatetime = i.get('datetime_value')
                if counter == 2:
                    prevSpeed = speed
                totalspeed += speed   

            avgspeed = totalspeed / numofreadings
            bidData.append(totalduration)
            bidData.append(len(datetimestartList))
            bidData.append(avgspeed)
            bidData.append(prevSpeed)
            bidData.append(latestSpeed)
            bidData.append(latestdatetime)
            bidData.append(numofreadings)
            bidData.append(speedingCounter)

            data.append(bidData)

        return data

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])        

def getindividualBookingData(bookingid):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        response = table.query(
            KeyConditionExpression = Key('device_id').eq('deviceid_zhiyang'),
            ProjectionExpression = 'bookingid,seconds,speed,speedkmhour,datetime_value',
            FilterExpression = Key('bookingid').eq(bookingid),
            ScanIndexForward = True
        )
        items = response['Items']

        return items

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])      

def getIndivividualDashboard(bookingid):
    try:
        data = []
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('GrabDataTable')
        response = table.query(
            KeyConditionExpression = Key('device_id').eq("deviceid_zhiyang"),
            ProjectionExpression = 'speedkmhour',
            FilterExpression = Key('bookingid').eq(bookingid)
        )
        items = jsonc.data_to_json(response['Items'])
        numofrows= response['Count']
        totalSpeed = 0.0
        highestSpeed = 0.0
        for i in json.loads(items):
            speed = i.get('speedkmhour')
            if speed > highestSpeed:
                highestSpeed = speed
            totalSpeed += speed
        avgspeed = totalSpeed / numofrows
        data.append(avgspeed)
        data.append(highestSpeed)
        data.append(numofrows)

        return data

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])  

def getIndividualMapData(bookingid):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('map')
        maxdatetimestart = get_maxdatetimestart_forbookingid(bookingid)
        print(maxdatetimestart)
        table = dynamodb.Table('map')
        response = table.query(
            KeyConditionExpression = Key('bookingid').eq(bookingid),
            ProjectionExpression = 'Latitude, Longitude, datetime_value',
            FilterExpression = Key('datetimestart_value').eq(maxdatetimestart),
            Limit = 50
        )
        mapdata = response['Items']
        return mapdata

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1]) 

def uploadImageFileToS3(frame,imagename):
    try:
        s3 = boto3.resource('s3')
        location = {'LocationConstraint': 'us-east-1'}
        try:
            bucket = 'sp-1828430-s3-bucket' # replace with your own unique bucket name
            exists = True
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                exists = False

        if exists == False:
            s3.create_bucket(Bucket=bucket,CreateBucketConfiguration=location)
        frame = cv2.imencode('.jpg', frame)[1].tostring()
        s3.Object(bucket, imagename).put(Body=bytes(frame))
        facesimilarity, ageDetails, newimage = retrieveDriverFaceDetails(imagename,frame)
        '''if facesimilarity is None:
            return ("face is not indexed")
        else:
            client=boto3.client('rekognition',region_name='us-east-1')
            response=client.index_faces(CollectionId='DriverFaceCollection',
                                    Image={'S3Object':{'Bucket':bucket,'Name':imagename}},
                                    ExternalImageId=imagename,
                                    MaxFaces=1,
                                    QualityFilter="AUTO",
                                    DetectionAttributes=['ALL'])
            print('Faces indexed:')						
            for faceRecord in response['FaceRecords']:
                print('  Face ID: ' + faceRecord['Face']['FaceId'])
                print('  Location: {}'.format(faceRecord['Face']['BoundingBox']))
            for unindexedFace in response['UnindexedFaces']:
                print(' Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
                print(' Reasons:')
                for reason in unindexedFace['Reasons']:
                    print('   ' + reason)            
            return ("Face indexed")'''
        return facesimilarity
        
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])
         
def retrieveImageFromS3(bookingid):     
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('image')
        response = table.query(
            KeyConditionExpression = Key('VehicleType').eq('GrabCar'),
            FilterExpression = Key('bookingid').eq(bookingid),
            ProjectionExpression = 'datetime_value',
            ScanIndexForward = False,
            Limit = 3
        )
        item = response['Items']  
        print(item)
        for num in range(len(item)):  
            latestDateTime = item[num].get('datetime_value')
            imgpathaddon = latestDateTime.replace(":",".")
            imgpathaddon = imgpathaddon.replace(" ","_")+ ".jpg"
            keyname = bookingid+"_"+imgpathaddon
            s3 = boto3.resource('s3')
            bucket = 'sp-1828430-s3-bucket' # replace with your own unique bucket name
            obj = s3.Object(bucket,keyname)
            image = obj.get()['Body'].read()
            stream = io.BytesIO(image)
            imagedata = Image.open(stream)
            facesimilarity, ageDetails, newimage = retrieveDriverFaceDetails(keyname,imagedata)
            if facesimilarity == 1:
                print("No Details for ", num, "st image")
            else:
                buffered = BytesIO()
                newimage.save(buffered, format="JPEG")
                newimage.close()
                image = base64.b64encode(buffered.getvalue())
                image = image.decode('utf-8')
                return image, facesimilarity, ageDetails
        print("looped thru everyything, returning all none")
        return None, 1, None

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def retrieveImageFromS3forIndex(bookingid):     
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('image')
        response = table.query(
            KeyConditionExpression = Key('VehicleType').eq('GrabCar'),
            FilterExpression = Key('bookingid').eq(bookingid),
            ProjectionExpression = 'datetime_value',
            ScanIndexForward = False,
            Limit = 1
        )
        item = response['Items']
        facesimilarity, ageDetails, newimage = "","",""
        for num in range(len(item)):  
            latestDateTime = item[num].get('datetime_value')
            imgpathaddon = latestDateTime.replace(":",".")
            imgpathaddon = imgpathaddon.replace(" ","_")+ ".jpg"
            keyname = bookingid+"_"+imgpathaddon
            s3 = boto3.resource('s3')
            bucket = 'sp-1828430-s3-bucket' # replace with your own unique bucket name
            obj = s3.Object(bucket,keyname)
            image = obj.get()['Body'].read()
            stream = io.BytesIO(image)
            imagedata = Image.open(stream)
            facesimilarity, ageDetails, newimage = retrieveDriverFaceDetails(keyname,imagedata)

        return facesimilarity, ageDetails, newimage

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def retrieveDriverFaceDetails(keyname,imagedata):
    try:
        bucket = 'sp-1828430-s3-bucket'
        client=boto3.client('rekognition',region_name='us-east-1')
        ageDetails = ""
        try:
            response = client.detect_faces(
                Image={
                    "S3Object": {
                        "Bucket": bucket,
                        "Name": keyname,
                    }
                },
                Attributes=['ALL']
            )
            if not isinstance(imagedata,bytes):
                imgWidth, imgHeight = imagedata.size  
                draw = ImageDraw.Draw(imagedata) 
                for faceDetail in response['FaceDetails']:
                    ageLow = faceDetail['AgeRange']['Low']
                    ageHigh = faceDetail['AgeRange']['High']
                    ageDetails = 'Age is between {} and {} years old'.format(ageLow,ageHigh)
                    box = faceDetail['BoundingBox']
                    left = imgWidth * box['Left']
                    top = imgHeight * box['Top']
                    width = imgWidth * box['Width']
                    height = imgHeight * box['Height']               
                    points = (
                                (left,top),
                                (left + width, top),
                                (left + width, top + height),
                                (left , top + height),
                                (left, top)
                    )
                    draw.line(points, fill='#00d400', width=2)
            
            response = client.search_faces_by_image(CollectionId='DriverFaceCollection',
                                        Image={'S3Object':{'Bucket':bucket,'Name':keyname}},
                                        FaceMatchThreshold=80,
                                        MaxFaces=1)
            facematch = response['FaceMatches']
            print("facematches ", facematch)
            if facematch:
                for match in facematch:
                    if match is not None:
                        facesimilarity = "{:.2f}".format(match['Similarity'])
                        print("face matched")
                        #facesimilarity = f"Driver's face detected, with {similarity} similarity match"
            else:
                #facesimilarity = "Driver's face does not match the expected face in the database"
                facesimilarity = 0
                print("face not matched")
            
            return facesimilarity, ageDetails, imagedata

        except:
            print("no face is detected gonna reutnr 1 for sim")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return 1,None,None

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1]) 

def getLatest3DriversthatSped():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('image')
        response = table.query(
            KeyConditionExpression = Key('VehicleType').eq('GrabCar'),
            FilterExpression = Key('speedkmhour').gte(90),
            ProjectionExpression = 'bookingid, KeyName, datetime_value, speedkmhour',
            ScanIndexForward = False,
            Limit = 200
        )

        items = response['Items']
        uniqueBidcounter = 0
        data = []
        bidList = []
        bidData = []

        for i in items: 
            bookingid = i.get('bookingid')
            if bookingid not in bidList:
                speedValue = i.get('speedkmhour')
                imageName = i.get('KeyName')
                datetime = i.get('datetime_value')
                bidList.append(bookingid)
                bidData.append(bookingid)
                imageData = retrieveImageforDriversthatSped(imageName)
                bidData.append(imageData)
                bidData.append(datetime)
                bidData.append(speedValue)
                data.append(bidData)
                uniqueBidcounter += 1
                bidData = []
                if uniqueBidcounter == 3:
                    break  
                else:
                    continue

        return data

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])            

def retrieveImageforDriversthatSped(keyname):
    try:
        s3 = boto3.resource('s3')
        bucket = 'sp-1828430-s3-bucket' # replace with your own unique bucket name
        obj = s3.Object(bucket,keyname)
        image = base64.b64encode(obj.get()['Body'].read())
        image = image.decode('utf-8')

        return image

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

def getMapData(bookingid, maxdatetimestart):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('map')
        response = table.query(
            KeyConditionExpression = Key('bookingid').eq(bookingid),
            ProjectionExpression = 'Latitude, Longitude, bookingid',
            FilterExpression = Key('datetimestart_value').eq(maxdatetimestart),
            ScanIndexForward = False,
            Limit = 1
        )
        item = response['Items']
        print(item)
        return item

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])        