#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import logging
from ipfs_pubsub import IPFS_API as IPFS_PUBSUB
import dump1090_async as dump1090
from os import getcwd
from uuid import uuid4
from time import time
from json import load as loadjson
from configparser import ConfigParser


###############################################################################
# CONFIGURATION
###############################################################################
config_path = getcwd() + '/'
config = ConfigParser()
config.read(config_path + 'ipfs_dump1090.conf')


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
    PUB_CHANNEL_ID = str(uuid4())
    config.set('channel', 'id', PUB_CHANNEL_ID)

    with open('ipfs_dump1090.conf', 'w') as configfile:
        config.write(configfile)
else: pass

DATA_FORMAT = config['channel']['format']


# Set metadata
meta = {'id': PUB_CHANNEL_ID,        
        'format': DATA_FORMAT, 
        'location': MY_RX_LOCATION,
        'tracking': 0,        
        'ts': 0 }


###############################################################################
# CALLBACKS
###############################################################################

# ADS-B DATA CALLBACK
def onData( data ):    
    try: pubsub.publishNDJSON( PUB_CHANNEL_ID, data )
    except Exception as e:
        logging.error(f"IPFS Error: {e}")

# METADATA CALLBACK
def pubMetaData():

    # Check how many aircrafts we are tracking
    with open('dump1090.json', 'r') as f:
        data = loadjson(f)
        meta['tracking'] = len(data)

    # Update timestamp
    meta['ts'] = int( time() )

    # Publish metadata
    for channel in METADATA_PUB_CHANNELS:
        pubsub.publishNDJSON( channel, meta )


###############################################################################
# RUN MAIN
###############################################################################
print(f"IPFS-API Url: {pubsub.base_url}")
print(f"Publishing metadata to: {METADATA_PUB_CHANNELS}")
print(f"Publishing data to: {PUB_CHANNEL_ID}")

dump1090.run(exportCallback=onData, 
             metadataCallback=pubMetaData,
             dump1090_host=DUMP1090_HOST,
             dump1090_port=DUMP1090_PORT)