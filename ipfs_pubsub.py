#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
from collections import OrderedDict
import requests, json, logging
from base64 import b64decode, b64encode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

###############################################################################
# LOGGING
###############################################################################
loglevel = 'info'

numeric_level = getattr(logging, loglevel.upper())
fmt = '[%(levelname)s] %(message)s'
logging.basicConfig(level=numeric_level, format=fmt)

###############################################################################
# API CLASS
###############################################################################
class IPFS_API:

   def __init__(self, host="localhost", port=5001, proto='http'):
      self.host = host      
      self.port = port
      self.proto = proto
      self.auth = False

      if host != 'localhost':
         logging.warning("Using an IPFS remote API server is not recommended.")

      self.session = requests.Session()
      retry = Retry(connect=10, backoff_factor=2)
      adapter = HTTPAdapter(max_retries=retry)

      if(proto == 'http'): 
         self.session.mount('http://', adapter)
      else:
         self.session.mount('https://', adapter)

      self.base_url = self.proto + "://" + self.host + ":" + str(self.port)

   def setHttpAuth(self, user, passwd):
      self.user = user
      self.passwd = passwd
      self.auth = True

   def setHost(self, newHost):
      self.host = newHost
      self.base_url = self.proto + "://" + self.host + ":" + str(self.port)

      if newHost != 'localhost':
         logging.warning("Using an IPFS remote API server is not recommended.")

   def setPort(self, newPort):
      self.port = newPort
      self.base_url = self.proto + "://" + self.host + ":" + str(self.port)

   @staticmethod
   def ipfsb64decode( data ):
      d = str(data[1:]) + '===' 
      return b64decode(d).decode('utf-8')

   @staticmethod
   def ipfsb64encode( data ):
      return 'u' + b64encode( bytes(data.encode('utf-8')) ).decode('utf-8').replace('=', '')

   
   def getPeers( self, topic ):   
      endpoint = self.base_url + "/api/v0/pubsub/peers?arg="
      
      if(not self.auth): 
         peers = self.session.post( endpoint + self.ipfsb64encode(topic) )
      else:         
         peers = self.session.post( endpoint + self.ipfsb64encode(topic), auth=(self.user, self.passwd) )
      
      return json.loads( peers.text )['Strings']

   
   def printPeers( self, topic ):   
      endpoint = self.base_url + "/api/v0/pubsub/peers?arg="
      
      if(not self.auth): 
         peers = self.session.post( endpoint + self.ipfsb64encode(topic) )         
      else:
         peers = self.session.post( endpoint + self.ipfsb64encode(topic), auth=(self.user, self.passwd) )
      
      print( json.loads( peers.text )['Strings'] )


   def publishNDJSON( self, topic, dataIN, delimiter='\n' ):
      endpoint = self.base_url + "/api/v0/pubsub/pub?arg="

      data = { 'file': ( json.dumps(dataIN) + delimiter ) }
      req = self.session.post( endpoint + self.ipfsb64encode(topic), files=data )
      
      return req.status_code


   def publishOrderedNDJSON( self, topic, data, keyOrder, delimiter='\n' ):   
      endpoint = self.base_url + "/api/v0/pubsub/pub?arg="
      
      jsonOrderedData = OrderedDict(  (k, data[k]) for k in keyOrder  )
      data = { 'file': ( json.dumps(jsonOrderedData) + delimiter ) }
      req = self.session.post( endpoint + self.ipfsb64encode(topic), files=data )
      
      return req.status_code
   

   def subscribe( self, topic, callback ):
      endpoint = self.base_url + "/api/v0/pubsub/sub?arg="

      # Send request w/wo auth headers
      if(not self.auth): 
         req = self.session.post( endpoint + self.ipfsb64encode(topic), stream=True )
      else:
         req = self.session.post( endpoint + self.ipfsb64encode(topic), auth=(self.user, self.passwd), stream=True )
                
      # Check response status codes
      if req.status_code != 200: 
         logging.error("HTTP Request Error Code: %s", req.status_code)
      
      # Get data and send to callback
      for line in req.iter_lines():
         json_data = json.loads( line.decode('utf-8') )
         callback( json_data['from'], self.ipfsb64decode( json_data['data'] ) )
         

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':
   pass