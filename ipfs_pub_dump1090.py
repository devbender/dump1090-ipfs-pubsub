#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import ipfs_pubsub as ipfs
import ipfs_dump1090_async as dump1090
from uuid import uuid4
from json import dump, load as loadjson

data = 'ADSB'
airports = ['SDQ', 'JQB']

MY_RX_LOCATION = [18.465, -69.942]
DATA_FORMAT = 'ndjson'

PEER_PUBSUB_CHANNEL = uuid4().hex
METADATA_PUBSUB_CHANNELS = []

for airport in airports:
    refPoint = data + '-' + airport
    METADATA_PUBSUB_CHANNELS.append( refPoint )

meta = {'id': PEER_PUBSUB_CHANNEL,        
        'format': DATA_FORMAT, 
        'location': MY_RX_LOCATION,
        'tracking': 0 }

# PUBLISH ADS-B DATA
def onData( data ):    
    ipfs.publish( PEER_PUBSUB_CHANNEL, data )

# PUBLISH METADATA
def metaData():

    # Check how many aircrafts we are tracking
    with open('dump1090.json', 'r') as f:
        data = loadjson(f)
        meta['tracking'] = len(data)

    # Publish metadata
    for channel in METADATA_PUBSUB_CHANNELS:
        ipfs.publish( channel, meta )

###############################################################################
# RUN MAIN
###############################################################################
dump1090.run(onData, metaData)