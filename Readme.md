# Introduction fsbridge
Pont FSUIPC/MQTT en python 2.7 pour tourner sur la machine winXP.

esp8266_fsx sert d'afficheur distant

# Installation
## Installation des prerequis (win XP)
### Python
Installer python 2.7
Executer l'installer FSUIPCSK pour python 2.7 (a partir de FSUIPC SDK v4)
pip install paho-mqtt
pip install configparser

### Mosquitto
Installer mosquitto 1.4.9 et les librairies complémentaires

### Tortoise GIT 
Installer TortoiseGit 1.7.2.0

## Installation fsbridge
Faire un clone git du depot fsbridge

# Execution
Lancer Flight Simulator (FSX ou FS9)
Lancer mosquitto
Aller dans le répertoire fsbridge
Lancer fsbridge
`python fsbridge.py`
Brancher le device esp8266_fsx

# Configuration
fsbridge.ini
