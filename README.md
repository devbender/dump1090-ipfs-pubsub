# IPFS pubsub dump1090

Publish your dump1090 data streams to IPFS so we can create a decentralized, free to access peer to peer ADS-B traffic network.

This python script (package soon) grabs the SBS-1 TCP output of any dump1090 (usually on port 30003) and aggregates these messages:

* __MSG:1__ ES Callsign
* __MSG:2__ ES Surface Position
* __MSG:3__ ES Airborne Position
* __MSG:4__ ES Airborne Velocity

The agregated data is published via Pubsub to IPFS to the specified topics in the file __ipfs_pub_dump1090.py__ in a newline-delimited JSON (NDJSON) format.

__NOTE: At the moment only ADS-B SBS-1 data is supported, more coming soon!__


## Requirements

* An up and running dump1090 instance
* A local IPFS node with pubsub enabled (--enable-pubsub-experiment flag)


## Defining a location-based topic nomenclature

The idea of this project is that you can subscribe to specific topics depending on your location so you can get the aggregated output off all nearby receivers. To achieve this I defined a preliminary topic nomenclature (until a better idea arises).

The prefix defines the type of data: "ADSB", "UAT", "MLAT", or "FLARM" followed by a dash then the IATA airport code of the nearest largest airport.

Example topic names:

* __ADSB-MIA:__ ADS-B data near Miami Airport
* __UAT-HOU:__  UAT data near William P. Hobby
* __MLAT-FLL:__  MLAT data near Ft. Lauderdale Airport
* __FLARM-JFK:__ FLARM data near JFK Airport


## To run

Clone the repo preferably to your home directory.
```
git clone https://github.com/devbender/ipfs_pubsusb_dump1090
```

Then cd into the repo directory and modify the __ipfs_pub_dump1090.py__ and add the topic names to where your data will be published according to the specified nomenclature (see examples above), more than one can be specified if you wish to publish to more than one IATA code at the time for airports that are relatively close, for example MIA an FLL that are 20 miles apart.
```
TOPICS = []
```
Example: 
```
TOPICS = ['ADSB-MIA', 'ADSB-FLL']
```

Modify the __ipfs-dump1090.service__ unit file with your current user and the path to de repo. You can skip if you are running via raspberry pi default user pi and cloned to the home directory.
```
[Service]
User=pi
ExecStart=/usr/bin/python3 /home/pi/ipfs_pubsusb_dump1090/ipfs_pub_dump1090.py
```

Copy the unit file to __/etc/systemd/system/__: 
```
sudo cp ipfs-dump1090.service /etc/systemd/system/
```

To start:
```
sudo systemctl start ipfs-dump1090.service
```

Confirm its running:
```
sudo systemctl status ipfs-dump1090.service
```

To enable auto start:
```
sudo systemctl enable ipfs-dump1090.service
```

Test the output:
```
ipfs pubsub sub <topic>
```


## Credits

Copyright (C) 2022 by Juan Benitez   <juan.a.benitez(at)gmail.com>

Distributed under GPLv3
