#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import requests, json, sys, socket
from requests.api import get
from requests.models import iter_slices
from base64 import b64decode, b64encode
from time import sleep, time

###############################################################################
# IPFS HTTP API Calls
###############################################################################
def ipfs_b64decode( data ):
   d = str(data[1:]) + '===' 
   return b64decode(d).decode('utf-8')

def ipfs_b64encode( data ):
   return 'u' + b64encode( bytes(data.encode('utf-8')) ).decode('utf-8').replace('=', '')

def getPeers( topic ):
   urlPeers = "http://127.0.0.1:5001/api/v0/pubsub/peers?arg="
   peers = requests.post( urlPeers + ipfs_b64encode(topic) )

   return json.loads( peers.text )['Strings']

def printPeers( topic ):
   urlPeers = "http://127.0.0.1:5001/api/v0/pubsub/peers?arg="
   peers = requests.post( urlPeers + ipfs_b64encode(topic) )

   print( json.loads( peers.text )['Strings'] )

def publish( topic, dataIN, delimiter='\n' ):
   urlPub = "http://127.0.0.1:5001/api/v0/pubsub/pub?arg="   
   data = { 'file': ( json.dumps(dataIN) + delimiter ) }
   pub = requests.post( urlPub + ipfs_b64encode(topic), files=data )
   
   return pub

def subscribe( topic, callback ):
   urlSub = "http://127.0.0.1:5001/api/v0/pubsub/sub?arg="
   req = requests.post( urlSub + ipfs_b64encode(topic), stream=True )
   
   for line in req.iter_lines():      
      json_data = json.loads( line.decode('utf-8') )
      callback( json_data['from'], ipfs_b64decode( json_data['data'] ) )

def testPublish(TOPIC):
   i=0
   try:
      while True:
         publish(TOPIC, str({'test': [1+i,2+i,3+i]})  )
         i+=1
         sleep(1)
   except KeyboardInterrupt:
      print('\nExiting...')

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':   

   CMD = str(sys.argv[1]) 
   TOPIC = str(sys.argv[2])
   
   def onMsg( peer, data): 
      print( peer, data)

   if CMD == "peers": printPeers(TOPIC)
   elif CMD == "pub": 
      DATA = str(sys.argv[3])
      publish(TOPIC, DATA)
   elif CMD == "sub": 
      subscribe(TOPIC, onMsg)
   elif CMD == "encode":
      print(ipfs_b64encode(TOPIC))
   elif CMD == "decode":
      print(ipfs_b64decode(TOPIC))
   else:
      print("Error: Invalid command")