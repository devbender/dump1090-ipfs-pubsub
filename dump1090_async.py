#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import asyncio, logging,json
from time import time
from collections import OrderedDict
from os import path

tasks = []
localCache = {}

cacheFileName = 'localCache.json'
cacheFile = path.join( path.dirname(__file__), cacheFileName )

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

###############################################################################
# Process SBS1 line
###############################################################################
def SBS1toDict( line ):
   SBS1 = line.split(",")
   msgtype = SBS1[msgtype_field]
   icao = SBS1[icao_field]
   
   if( SBS1[gndf] == "" ):    ongnd = 0
   elif (SBS1[gndf] == "-1"): ongnd = 1
   else: ongnd = 0
     
   if msgtype == '1':
      return { 'id': int(msgtype), 
               'icao': icao, 
               'csg': SBS1[callsign_field].rstrip(), 
               'ts': int(time()) }
      
   elif msgtype == '2': 
      return { 'id': int(msgtype), 
               'icao': icao,  
               'alt': SBS1[alt_field],
               'lat': SBS1[lat_field], 
               'lon': SBS1[lon_field],
               'spd': SBS1[gspd_field],
               'trk': SBS1[trk_field],
               'gnf': ongnd,
               'ts': int( time() )
               }
   
   elif msgtype == '3':
      if SBS1[lat_field] != '' and SBS1[lon_field] != '':
         return { 'id': int(msgtype), 
                  'icao': icao, 
                  'alt': int(SBS1[alt_field]),
                  'lat': float(SBS1[lat_field]), 
                  'lon': float(SBS1[lon_field]), 
                  'gnf': ongnd,
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

   msgid = data['id']
   icao = data['icao']

   # AIRCRAFT in CACHE =============================================
   if icao in localCache:

      # If in local cache update data
      if msgid == 1:
         logging.debug("[UPDATED][CALLSIGN] %s", icao)
         localCache[icao]['csg'] = data['csg']

         # call sign msg does not trigger an update

      elif msgid == 2:
         logging.debug("[UPDATED][G-LOCATION] %s", icao)
         localCache[icao]['alt'] = 0
         localCache[icao]['lat'] = data['lat']
         localCache[icao]['lon'] = data['lon']
         localCache[icao]['gnf'] = data['gnf']

         localCache[icao]['new'] = 1
               
      elif msgid == 3:
         logging.debug("[UPDATED][LOCATION] %s", icao)
         localCache[icao]['alt'] = data['alt']
         localCache[icao]['lat'] = data['lat']
         localCache[icao]['lon'] = data['lon']
         localCache[icao]['gnf'] = data['gnf']

         localCache[icao]['new'] = 1

      elif msgid == 4:
         logging.debug("[UPDATED][VECTOR] %s", icao)
         localCache[icao]['spd'] = data['spd']
         localCache[icao]['trk'] = data['trk']
         localCache[icao]['vrt'] = data['vrt']

         localCache[icao]['new'] = 1
      
      else: pass

      # Common fields
      localCache[icao]['ts'] = data['ts']
      

   # NEW AIRCRAFT ================================================
   else:
      localCache[icao] = {'csg': '', 
                          'alt': '', 
                          'lat': '', 
                          'lon': '', 
                          'gnf': '', 
                          'spd': '', 
                          'trk': '', 
                          'vrt': '' }
     
      if msgid == 1:
         logging.debug("[NEW][CALLSIGN] %s", icao)
         localCache[icao] = { 'csg': data['csg'] }

      if msgid == 3:
         logging.debug("[NEW][LOCATION] %s", icao)
         localCache[icao] = { 'alt': data['alt'], 
                              'lat': data['lat'], 
                              'lon': data['lon'] }
      if msgid == 4:
         logging.debug("[NEW][VECTOR] %s", icao)
         localCache[icao] = { 'spd': data['spd'], 
                              'trk': data['trk'], 
                              'vrt': data['vrt'] }

      # Common fields      
      localCache[icao]['new'] = 1
      localCache[icao]['icao'] = str(data['icao'])
      localCache[icao]['ts'] = data['ts']


###############################################################################
# Get dump1090 SBS1 data
###############################################################################
async def getSBS1DataTask( dump1090Host='localhost', dump1090Port=30003, frameSizeKb=64 ):
   logging.info("TASK: [getSBS1DataTask] Started")
    
   try: reader, writer = await asyncio.open_connection( dump1090Host, dump1090Port)
   except Exception as e:
      logging.error("Unable to connect to dump1090: %s", e)

   while True:
      data = await reader.read( frameSizeKb*1024 )
      data = data.decode('utf-8').splitlines()        
        
      for line in data:
         if line != '':
            try: val = SBS1toDict(line)
            except: pass
            if val != None:                   
               updateLocalCache(val)


###############################################################################
# DATA EXPORT
###############################################################################
async def exportDataTask( callback=None):
   logging.info("TASK: [exportDataTask] Started")

   export_key_order = ['icao', 'csg', 'ts', 'alt', 'lat', 'lon', 'spd', 'trk', 'vrt', 'gnf']

   while True:
      await asyncio.sleep(1)
        
      for icao in list(localCache):
         if ('lat' in localCache[icao]) and \
            ('lon' in localCache[icao]) and \
            ( localCache[icao]['new'] ):
                  
            dataOUT = dict( OrderedDict((k, localCache[icao].get(k)) for k in export_key_order) )            
            if callback is not None: 
               callback( dataOUT )

            localCache[icao]['new'] = 0

      with open(cacheFile, 'w') as outfile:
         json.dump(localCache, outfile, indent=4)


###############################################################################
# DATA CLEANUP
###############################################################################
async def localCleanupTask(exportMetadata, cleanEveryXsecs=10, expireEveryYsecs=60):

   logging.info("TASK: [localCleanupTask] Started")
   
   while True:      
   
      for icao in list(localCache):

         # Remove aircraft from local cache if no new data in last X seconds
         if (time() - localCache[icao]['ts'] ) > expireEveryYsecs:
            localCache.pop(icao, None)
            logging.debug("[REMOVED] %s", icao)
      
         else: pass

      # Export metadata to callback
      exportMetadata()

      await asyncio.sleep(cleanEveryXsecs)

###############################################################################
# ASYNC MAIN
###############################################################################
async def main( loop, exportCallback, metadataCallback, dump1090_host, dump1090_port, loglevel ):
   
   # Setup logging
   numeric_level = getattr(logging, loglevel.upper())
   fmt = '[%(levelname)s] %(asctime)s - %(message)s'
   logging.basicConfig(level=numeric_level, format=fmt)

   logging.info("Starting dump1090 tasks...")
   
   t1 = loop.create_task( getSBS1DataTask(dump1090_host, dump1090_port) )
   t2 = loop.create_task( exportDataTask(exportCallback) )
   t3 = loop.create_task( localCleanupTask(metadataCallback) )

   tasks.extend([t1,t2,t3])
   
   await asyncio.sleep(1)
   logging.info("*** RUNNING ***")
    
   while True: await asyncio.sleep(1)

###############################################################################
# RUN
###############################################################################
def run( exportCallback=None, 
         metadataCallback=None, 
         dump1090_host='localhost',
         dump1090_port=30003,
         loglevel='INFO' ):
   
   try:       
      loop = asyncio.get_event_loop()
      loop.run_until_complete( main(loop, exportCallback, metadataCallback, dump1090_host, dump1090_port, loglevel) )

   except KeyboardInterrupt:

      logging.info("KeyboardInterrupt")
      logging.info("Stopping dump1090 tasks...")

      for task in tasks: #asyncio.Task.all_tasks(loop):         
         try: task.cancel()
         except asyncio.CancelledError:
            pass

      loop.stop()

      # Clear JSON file
      with open(cacheFile, 'w') as outfile:
         json.dump({}, outfile, indent=4)

      logging.info("*** TERMINATED ***")

   except Exception as e:
      logging.error(e)

###############################################################################
# MAIN
###############################################################################
if __name__ == "__main__":
   run( lambda x: print(x), 'INFO' )