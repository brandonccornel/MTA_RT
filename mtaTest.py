from botocore.compat import total_seconds
import requests
import csv
import math
from google.transit import gtfs_realtime_pb2
import datetime
import boto3

from twilio.rest import Client


#=====================================
requestedStop = 'A46'
direction = 'N'
verbalDirection = 'Uptown'
requestedTrains=['A', 'C']
desiredCount = 6
debugging = False
sendSMS = True
#=====================================


url = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace'
headers = {'x-api-key': 'iadrtGahXeam6ohE5ZxpQ498PHErz6x918chAIiT'}

r = requests.get(url, headers=headers)


feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(r.content)

stationsDict = {}

with open('Stations.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
      stationsDict[row[2]] = [row[4], row[5]]

if(debugging == True):
  f = open("gtfsData_A_Line.txt", "w")
  f.flush()
  for entity in feed.entity:
    stop_id = entity.vehicle.stop_id
    f.write(str(entity))
    f.write('\n\n\n\n\n')

  f.close()

if(verbalDirection == 'downtown'):
  direction = 'S'
else:
  direction = 'N'

requestedTrainString = ''

if(len(requestedTrains)>1):
  requestedTrainString = ''
  trainCount = 1
  for train in requestedTrains:
    if(len(requestedTrains) > 2):
      if(len(requestedTrains) - trainCount == 0):
        requestedTrainString += 'and {0} trains'.format(train)
      else:
        requestedTrainString += '{0}, '.format(train)
    elif(len(requestedTrains) <=2):
      if(len(requestedTrains) - trainCount == 0):
        requestedTrainString += 'and {0} trains'.format(train)
      else:
        requestedTrainString += '{0} '.format(train)
    trainCount+=1
else:
  requestedTrainString = '{0} train'.format(requestedTrains[0])

outputString = '\nArrival Times for the {0} going {2} at {1} \n==============================================================================='.format(requestedTrainString, stationsDict[requestedStop][1], verbalDirection)

trainArrivalTimes = {}

for entity in feed.entity:
  if('trip_update' in str(entity) and entity.trip_update.trip.route_id in requestedTrains):
    if(len(entity.trip_update.stop_time_update)>0):
      for stopUpdate in entity.trip_update.stop_time_update:
        if(requestedStop == stopUpdate.stop_id[:3] and direction == stopUpdate.stop_id[3]):
          if(entity.trip_update.trip.route_id in trainArrivalTimes):
            trainArrivalTimes[entity.trip_update.trip.route_id].append(datetime.datetime.fromtimestamp(int(stopUpdate.arrival.time)))
          else:
            trainArrivalTimes[entity.trip_update.trip.route_id] = [datetime.datetime.fromtimestamp(int(stopUpdate.arrival.time))]

now = datetime.datetime.now()

for key in trainArrivalTimes:
  count = 1
  outputString += '\n{0} train\n------------\n'.format(key)
  for value in sorted(trainArrivalTimes[key]):
    if((value-now).total_seconds()/60>=60):
      hour = round(((value-now).total_seconds()/60)/60)
      hourString = '1 hour'
      if(hour>1):
        hourString = '{0} hours'.format(hour)

      minute = round(round((value-now).total_seconds()/60)%60)
      minuteString = '1 minute'

      if(minute>1):
        minuteString = '{0} minutes'. format(minute)
      
      outputString +='{0}: {1} and {2}\n'.format(value.strftime("%I:%M %p"), hourString, minuteString)
    else:
      outputString +='{0}: {1} minutes\n'.format(value.strftime("%I:%M %p"), round((value-now).total_seconds()/60))
    count+=1
    if(count>desiredCount):
      break

print(outputString)


if(sendSMS):
  '''
  client = boto3.client(
      "sns",
      aws_access_key_id="AKIAJY6QK4RMU23U55NQ",
      aws_secret_access_key="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",
      region_name='us-east-2'
  )

  print(client.publish(
      PhoneNumber="+15704195079",
      Message=outputString
  ))
  '''
  account_sid = 'ACf51769da9b2f1c9c04e11451ba6254b5'
  auth_token = '6b4395bc24cb1c8b6a59f330b7eed411'
  client = Client(account_sid, auth_token)
  message = client.messages \
                .create(
                     body=outputString,
                     from_='+12297858046',
                     to='+15704195079'
                 )
  print(message.sid)


