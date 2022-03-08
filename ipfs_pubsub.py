#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import requests, json
from base64 import b64decode, b64encode


class IPFS_API:

   def __init__(self, host="127.0.0.1", port=5001):
      self.host = host
      self.port = port
      self.base_url = "http://" + self.host + ":" + str(self.port)

   def setHost(self, newHost):
      self.host = newHost
      self.base_url = "http://" + self.host + ":" + str(self.port)

   def setPort(self, newPort):
      self.port = newPort
      self.base_url = "http://" + self.host + ":" + str(self.port)

   @staticmethod
   def ipfsb64decode( data ):
      d = str(data[1:]) + '===' 
      return b64decode(d).decode('utf-8')

   @staticmethod
   def ipfsb64encode( data ):
      return 'u' + b64encode( bytes(data.encode('utf-8')) ).decode('utf-8').replace('=', '')

   def getPeers( self, topic ):   
      urlPeers = self.base_url + "/api/v0/pubsub/peers?arg="
      peers = requests.post( urlPeers + self.ipfsb64encode(topic) )
      return json.loads( peers.text )['Strings']

   def printPeers( self, topic ):   
      urlPeers = self.base_url + "/api/v0/pubsub/peers?arg="
      peers = requests.post( urlPeers + self.ipfsb64encode(topic) )
      print( json.loads( peers.text )['Strings'] )

   def publishNDJSON( self, topic:str, dataIN:dict, delimiter='\n' ):   
      urlPub = self.base_url + "/api/v0/pubsub/pub?arg="   
      data = { 'file': ( json.dumps(dataIN) + delimiter ) }
      pub = requests.post( urlPub + self.ipfsb64encode(topic), files=data )      
      return pub

   def subscribe( self, topic, callback ):
      urlSub = self.base_url + "/api/v0/pubsub/sub?arg="
      req = requests.post( urlSub + self.ipfsb64encode(topic), stream=True )
      
      for line in req.iter_lines():      
         json_data = json.loads( line.decode('utf-8') )
         callback( json_data['from'], self.ipfsb64encode( json_data['data'] ) )

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':
   pass