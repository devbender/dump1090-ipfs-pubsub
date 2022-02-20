# IPFS pubsub dump1090

Publish your dump1090 data streams to IPFS so we can create a decentralized free to access peer to peer ADS-B traffic network.


## To run

Modify the __ipfs-dump1090.service__ file with your current user and the path to de repo.

Copy the service file to __/etc/systemd/system/__

To start:
`sudo systemctl start ipfs-dump1090.service`

Confirm its running:
`sudo systemctl status ipfs-dump1090.service`

To auto start:
`sudo systemctl enable ipfs-dump1090.service`

## Credits

Copyright (C) 2022 by Juan Benitez   <juan.a.benitez(at)gmail.com>

Distributed under GPLv3
