#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
from posixpath import split
from ipfs_pubsub import IPFS_API as IPFS_PUBSUB
import ipfs_dump1090_async as dump1090
from uuid import uuid4
from time import time
from json import load as loadjson, loads
from configparser import ConfigParser


###############################################################################
# CONFIGURATION
###############################################################################
config = ConfigParser()
config.read('ipfs_dump1090.conf')


# Set IPFS HTTP API params from config file
pubsub = IPFS_PUBSUB()
pubsub.setHost( config['ipfs']['api_host'] )
pubsub.setPort( int(config['ipfs']['api_port']) )


# Set receiver params from config file
DATA_FORMAT = config['channel']['format']
MY_RX_LOCATION = [ float( config['receiver']['lat'] ), 
                   float( config['receiver']['lon'] ) ]


# Get pub channel id if exists, else create it and write to config
PUB_CHANNEL_ID = config['channel']['id']

if PUB_CHANNEL_ID == '':
    PUB_CHANNEL_ID = uuid4().hex
    config.set('channel', 'id', PUB_CHANNEL_ID)

    with open('ipfs_dump1090.conf', 'w') as configfile:
        config.write(configfile)
else: pass

    
# Set metadata and metadata pub channels
METADATA_PUB_CHANNELS = ['ADSB-ALL']

airports = [ config['receiver']['closest_airport'], 
             config['receiver']['closest_major_airport'] ]

for airport in airports:    
    metadata_chan = "ADSB-" + airport
    METADATA_PUB_CHANNELS.append(metadata_chan)

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
    pubsub.publishNDJSON( PUB_CHANNEL_ID, data )

# METADATA CALLBACK
def metaData():

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

dump1090.run(onData, metaData)