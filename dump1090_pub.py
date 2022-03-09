#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import logging
from ipfs_pubsub import IPFS_API as IPFS_PUBSUB
import dump1090_async as dump1090
from os import path
from uuid import uuid4
from time import time
from json import dumps, load as loadjson
from configparser import ConfigParser
from collections import OrderedDict


###############################################################################
# LOGGING
###############################################################################
loglevel = 'info'

numeric_level = getattr(logging, loglevel.upper())
fmt = '[%(levelname)s] %(asctime)s - %(message)s'
logging.basicConfig(level=numeric_level, format=fmt)

###############################################################################
# CONFIGURATION
###############################################################################
config_name = 'dump1090_ipfs.conf'
config_file = path.join( path.dirname(__file__), config_name )
config = ConfigParser()
config.read( config_file )


# [ipfs] Set IPFS HTTP API params from config file
pubsub = IPFS_PUBSUB()
pubsub.setHost( config['ipfs']['api_host'] )
pubsub.setPort( int(config['ipfs']['api_port']) )


# [dump1090] Get dump1090 host/port
DUMP1090_HOST = config['dump1090']['host']
DUMP1090_PORT = config['dump1090']['port']


# [receiver] Set receiver params from config file
MY_RX_LOCATION = [ float( config['receiver']['lat'] ), 
                   float( config['receiver']['lon'] ) ]


# [receiver] Set metadata and metadata pub channels from IATA airport codes
METADATA_PUB_CHANNELS = ['ADSB-ALL']

airports = [ config['receiver']['closest_airport'], 
             config['receiver']['closest_major_airport'] ]

for airport in airports:    
    metadata_chan = "ADSB-" + airport
    METADATA_PUB_CHANNELS.append(metadata_chan)


# Get pub channel id if exists, else create it and write to config
PUB_CHANNEL_ID = config['channel']['id']

if PUB_CHANNEL_ID == '':
    PUB_CHANNEL_ID = str(uuid4().hex)
    config.set('channel', 'id', PUB_CHANNEL_ID)

    with open(config_file, 'w') as configfile:
        config.write(configfile)
else: pass

DATA_FORMAT = config['channel']['format']


# Set metadata
metadata = {'id': PUB_CHANNEL_ID,        
            'format': DATA_FORMAT, 
            'location': MY_RX_LOCATION,
            'tracking': 0,        
            'ts': 0 }

metadata_key_order = ['id', 'format', 'location', 'tracking', 'ts']

###############################################################################
# CALLBACKS
###############################################################################

# ADS-B DATA CALLBACK
def onData( data ):
    
    export_key_order = ['icao', 'csg', 'ts', 'alt', 'lat', 'lon', 'spd', 'trk', 'vrt', 'gnf']

    try:
        pubsub.publishNDJSON( PUB_CHANNEL_ID, data)
        #pubsub.publishOrderedNDJSON( PUB_CHANNEL_ID, data, export_key_order )
    except Exception as e:
        logging.error("IPFS Error: %s", e)

# METADATA CALLBACK
def pubMetaData():

    # Check how many aircrafts we are tracking
    with open(dump1090.cacheFile, 'r') as f:
        data = loadjson(f)
        metadata['tracking'] = len(data)

    # Update timestamp
    metadata['ts'] = int( time() )

    # Publish metadata
    for channel in METADATA_PUB_CHANNELS:        
        pubsub.publishOrderedNDJSON( channel, metadata, metadata_key_order )


###############################################################################
# RUN MAIN
###############################################################################
logging.info(">>> DUMP1090 IPFS PUBSUB v0.1 <<<")
logging.info("Using ipfs api url @ %s", pubsub.base_url)
logging.info("Using dump1090 instance @ %s:%s", DUMP1090_HOST, DUMP1090_PORT)
logging.info("Publishing metadata to: %s", METADATA_PUB_CHANNELS)
logging.info("Publishing dump1090 data to: %s", PUB_CHANNEL_ID)

dump1090.run(exportCallback=onData, 
             metadataCallback=pubMetaData,
             dump1090_host=DUMP1090_HOST,
             dump1090_port=DUMP1090_PORT)