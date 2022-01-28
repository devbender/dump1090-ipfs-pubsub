#!/usr/bin/python

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
import json
import ipfs_pubsub as ipfs

TOPIC = 'ADSB-SDQ'

def onData( peer, data ):
    print( peer, json.loads( data ) )

ipfs.printPeers( TOPIC )

try: ipfs.subscribe( TOPIC, onData )
except KeyboardInterrupt: print("*** TERMINATED ***")