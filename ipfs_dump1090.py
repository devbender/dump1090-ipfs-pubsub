#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import socket, json, logging, argparse, threading
from requests import get as getJSON
from time import sleep, time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable

###############################################################################
# SBS1 MSG FIELDS
###############################################################################
msgtype_field = 1
icao_field = 4
date_field = 6
time_field = 7

callsign_field = 10

alt_field = 11
lat_field = 14
lon_field = 15

gspd_field = 12
trk_field = 13
vrt_field = 16

gndf = 21

localCache = {}

###############################################################################
# Process SBS1 line
###############################################################################
def SBS1toDict( line ):
   SBS1 = line.split(",")
   msgtype = SBS1[msgtype_field]
   icao = SBS1[icao_field]
     
   if msgtype == '1':
      return { 'id': int(msgtype), 
               'icao': icao, 
               'cs': SBS1[callsign_field].rstrip(), 
               'ts': int(time()) }
      
   elif msgtype == '2': 
      return { 'id': int(msgtype), 
               'icao': icao,  
               'alt': SBS1[alt_field],
               'lat': SBS1[lat_field], 
               'lon': SBS1[lon_field],
               'spd': SBS1[gspd_field],
               'trk': SBS1[trk_field],
               'gf':  SBS1[gndf],
               'ts': int( time() )
               }
   
   elif msgtype == '3':
      if SBS1[lat_field] != '' and SBS1[lon_field] != '':
         return { 'id': int(msgtype), 
                  'icao': icao, 
                  'alt': int(SBS1[alt_field]),
                  'lat': float(SBS1[lat_field]), 
                  'lon': float(SBS1[lon_field]), 
                  'gf': SBS1[gndf],
                  'ts': int( time() )
                  }

   elif msgtype == '4':
      return { 'id': int(msgtype), 
               'icao': icao, 
               'spd': int(SBS1[gspd_field]),
               'trk': int(SBS1[trk_field]),
               'vrt': int(SBS1[vrt_field]), 
               'ts': int( time() )
               }
   

###############################################################################
# UPDATE LOCAL CACHE
###############################################################################
def updateLocalCache( data ):

   icao = data['icao']
   msgid = data['id']
   
   if icao in localCache:

      # If in local cache update data
      if msgid == 1:
         logging.debug(f"[UPDATED][CALLSIGN] {icao}")
         localCache[icao]['cs'] = data['cs']

      elif msgid == 2:
         logging.debug(f"[UPDATED][G-LOCATION] {icao}")
         localCache[icao]['alt'] = 0
         localCache[icao]['lat'] = data['lat']
         localCache[icao]['lon'] = data['lon']
         localCache[icao]['gf'] = data['gf']
               
      elif msgid == 3:
         logging.debug(f"[UPDATED][LOCATION] {icao}")
         localCache[icao]['alt'] = data['alt']
         localCache[icao]['lat'] = data['lat']
         localCache[icao]['lon'] = data['lon']
         localCache[icao]['gf'] = data['gf']

      elif msgid == 4:
         logging.debug(f"[UPDATED][VECTOR] {icao}")
         localCache[icao]['spd'] = data['spd']
         localCache[icao]['trk'] = data['trk']
         localCache[icao]['vrt'] = data['vrt']
      
      else: pass

      localCache[icao]['stl'] = 0
      localCache[icao]['ts'] = data['ts']

   # New aircraft
   else:
      localCache[icao] = {}
      #logging.info(f"[NEW] {icao}")
     
      if msgid == 1:
         logging.debug(f"[NEW][CALLSIGN] {icao}")
         localCache[icao] = { 'cs': data['cs'] }

      if msgid == 3:
         logging.debug(f"[NEW][LOCATION] {icao}")
         localCache[icao] = { 'alt': data['alt'], 
                              'lat': data['lat'], 
                              'lon': data['lon'] }
      if msgid == 4:
         logging.debug(f"[NEW][VECTOR] {icao}")
         localCache[icao] = { 'spd': data['spd'], 
                              'trk': data['trk'], 
                              'vrt': data['vrt'] }

      localCache[icao]['stl'] = 0
      localCache[icao]['icao'] = str(data['icao'])
      localCache[icao]['ts'] = data['ts']      

###############################################################################
# Get dump1090 json data
###############################################################################
def getJsonData():
   url = 'http://localhost:8080/data/aircraft.json'
   response = getJSON(url)
   data = json.loads(response.text)['aircraft']

   return data


###############################################################################
# Get dump1090 SBS1 data
###############################################################################
def getSBS1data(host, SBS1_port, callback=None):
   logging.info("[getSBS1data] Started")

   dump1090 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   dump1090.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   dump1090.connect( (host, SBS1_port) )

   frame = 1024 * 64

   while threading.currentThread().do_run:    
      try: payload = dump1090.recv( frame ).decode('utf-8').splitlines()
      
      except socket.error as e:
         logging.error(f"EXCEPTION [getSBS1data] Socket error: {e}")
         time.sleep(5)
         dump1090.connect( (host, SBS1_port) )


      if payload != ['']: 
         for line in payload:
               if line != '':
                  try: 
                     out = SBS1toDict(line)
                  except Exception as e:
                     logging.warning(f"EXCEPTION (SBS1toDict): {e}")
                     logging.warning(f"EXCEPTION LINE: {line}")
                  
                  if out != None: 
                     try: 
                        updateLocalCache( out )
                        if callback != None: callback( out )
                     except Exception as e:
                        logging.warning(f"EXCEPTION (updateLocalCache): {e}")

   dump1090.close()
   logging.info("[getSBS1data] Stopped")   

###############################################################################
# EXPORT LOCAL CACHE TO CALLBACK
###############################################################################
def exportLocalCache(callback, data_delay):
   logging.info("[exportLocalCache] Started")
   logging.info(f"[exportLocalCache] Callback: {callback}")
   
   while threading.currentThread().do_run:
      
      try: 
         # Export to callback aircrafts that have location and have been recenlty updated (not stale)
         for icao in list(localCache):
            if callback != None:
               if ('lat' in localCache[icao]) and ('lon' in localCache[icao]) and (not localCache[icao]['stl']):
                  callback( localCache[icao] )                  
            else: pass         
         
         # write local cache to file
         #with open('localCache.json', 'w') as f: 
         #   json.dump(localCache, f, indent=4)
      
      except KeyError as e:
         logging.warning(f"EXCEPTION (exportLocalCache) [KeyError]: {e}")

      except Exception as e:
         logging.warning(f"EXCEPTION (exportLocalCache): {e}")

      sleep( data_delay )
   
   logging.info("[exportLocalCache] Stopped")

###############################################################################
# CLEANUP LOCAL CACHE
###############################################################################
def localCacheCleanup(stale=5, timeout=30):
   logging.info("[cleanLocalCache] Started")
   
   while threading.currentThread().do_run:
   
      for icao in list(localCache):
         
         # Mark aircraft as stale if no data in defined time and not already marked as stale
         if (time() - localCache[icao]['ts'] ) > stale and not localCache[icao]['stl']:
            localCache[icao]['stl'] = 1
            logging.debug(f"[STALE] {icao}")

         # Remove aircraft from local cache if no data in defined time
         elif (time() - localCache[icao]['ts'] ) > (timeout):
            localCache.pop(icao, None)
            logging.debug(f"[REMOVED] {icao}")

         else: pass
      sleep(5)
   
   logging.info("[cleanLocalCache] Stopped")

###############################################################################
# RUN
##############################################################################
def run( host: Optional[str] = 'localhost', 
         port: Optional[int] = 30003,
         callback: Optional[Callable] = None,
         data_out_secs: Optional[int] = 1, 
         aircraft_stale: Optional[int] = 5,
         aircraft_timeout: Optional[int] = 30,
         loglevel = 'INFO'):

   # Setup logging
   numeric_level = getattr(logging, loglevel.upper())
   fmt = '[%(levelname)s] %(asctime)s - %(message)s'
   logging.basicConfig(level=numeric_level, format=fmt)

   logging.info("Starting threads...")

   # Setup threads
   t1 = threading.Thread(target=getSBS1data, args=(host, port) )
   t1.setDaemon(True)
   setattr(t1, 'do_run', True)
   t1.start()

   t2 = threading.Thread(target=localCacheCleanup, args=(aircraft_stale, aircraft_timeout) )   
   t2.setDaemon(True)
   setattr(t2, 'do_run', True)
   t2.start()

   t3 = threading.Thread(target=exportLocalCache, args=(callback, data_out_secs) )
   t3.setDaemon(True)
   setattr(t3, 'do_run', True)
   t3.start()

   sleep(1)
   logging.info("*** RUNNING ***")

   try: 
      while True: 
         aircraft_count = len(localCache)
         logging.info("Tracking: %s aircraft(s)" % aircraft_count)
         sleep(10)
   except KeyboardInterrupt:
      logging.info("Stopping threads...")
      
      setattr(t1, 'do_run', False)
      setattr(t2, 'do_run', False)
      setattr(t3, 'do_run', False)
      
      t1.join()
      t2.join()
      t3.join()
      
      logging.info("*** TERMINATED ***")

###############################################################################
# MAIN
###############################################################################
if __name__ == '__main__':

   # Set up arguments
   parser = argparse.ArgumentParser(description='*** IPFS DUMP1090 PUBSUB ***')
   parser.add_argument('--host', type=str, default='localhost', help='Hostname or IP address of dump1090 instance')
   parser.add_argument('--port', type=int, default=30003, help='Port serving dump1090 SBS1 data')
   parser.add_argument('--log', type=str, default='INFO', help='Log level')
   args = parser.parse_args() 

   run( host = args.host,
        port = args.port,
        callback = lambda x: print( x ), 
        data_out_secs = 1,
        aircraft_stale = 5,
        aircraft_timeout = 30,
        loglevel = args.log )