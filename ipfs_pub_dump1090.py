#!/usr/bin/python

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import json
import ipfs_pubsub as ipfs
import ipfs_dump1090 as dump1090
from collections import OrderedDict

TOPICS = ['ADSB-SDQ', 'ADSB-JBQ']

key_order = ['icao', 'cs', 'ts', 'alt', 'lat', 'lon', 'spd', 'trk', 'vrt', 'gf']

def onData( data ):
    new_data = dict( OrderedDict((k, data.get(k)) for k in key_order) )
    
    for topic in TOPICS:        
        ipfs.publish( topic, json.dumps(new_data) ) 

dump1090.run( host = 'localhost',
              port = 30003,
              callback = onData, 
              data_out_secs = 1,
              aircraft_stale = 5,
              aircraft_timeout = 30,
              loglevel = 'INFO' )