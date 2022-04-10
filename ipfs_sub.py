#!/usr/bin/python3

###############################################################################
# IPFS PUBSUB DUMP1090 v0.1 
# Copyright (C) 2022  Juan Benitez
# Distributed under GPLv3
###############################################################################
from ipfs_pubsub import IPFS_API

#ipfs = IPFS_API(host="localhost", port=5001, proto='http')
ipfs = IPFS_API(host="api.iostream.network", port=8447, proto='https')
ipfs.setHttpAuth("admin", "bdre4s")

TOPIC = 'ADSB-ALL'

def onData( peer, data ):
    print( data, end='' )

ipfs.printPeers( TOPIC )
ipfs.subscribe( TOPIC, onData )