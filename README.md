# SelfHydro

This is an automated hydroponic system. 

It currently consists of an automated watering system, air pump, grow LEDs and temp. sensors.

It all runs on a Raspberry Pi.

### Wifi-Connect
Install using: 
``` 
bash <(curl -L https://github.com/resin-io/resin-wifi-connect/raw/master/scripts/raspbian-install.sh)
```

[]


### Setting Selfhydro up as a service

1. ``cp selfhydro.serivce /etc/systemd/system/selfhydro.service``
2. ``sudo systemctl enable selfhydro.service``