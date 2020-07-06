## Liste ey valeur des constantes
### Side Keys
LSK1 01 RSK1 11  
LSK2 02 RSK2 12  
LSK3 03 RSK3 13  
LSK4 04 RSK4 14  
LSK5 05 RSK5 15  
LSK6 06 RSK6 16  
LSK7 07 RSK7 17  
LSK8 08 RSK8 18  
### Couleurs
WHITE 99  
YELLOW 98  
GREEN 97  
BLACK 96  
### Boutons tactiles
LSK1 01 RSK1 11  
LSK2 02 RSK2 12  
LSK3 03 RSK3 13  
LSK4 04 RSK3 14  
LSK4 04 RSK4 14  
LSK5 05 RSK5 15  
LSK6 06 RSK6 16  
LSK7 07 RSK7 17  
LSK8 08 RSK8 18  
### Encodeurs
INC1UP 50  
INC1DN 51  
INC2UP 52  
INC2DN 53  
### Boutons mecanbiques
BT1 57  
BT2 58  
BT3 59  

## bridge vers device (mode commande)
### Nouvel ecran
topic: j/[nomDevice]/c/d  
content: N,[titre]  
New Screen, efface l'ecran, supprime les boutons/reactions et ecrit titre en haut en blanc

### Creer un bouton clickable sur l'ecran
topic: j/[nomDevice]/c/d  
content: B,[code Side Key sur 2 car],[intutule bouton]  
cree un Bonton vert LSK1-4, RSK1-4, qui réagit aux appuis et retourn la valeur du bouton presse sur le topic key

### Affichage texte, avec ou sans contour clickable
topic: j/[nomDevice]/c/d  
content: T,XX,CC,B,Z,[chaine formattee]  
affichage du text chaine a l'emplacement Side Key XX de couleur CC  
si B=0, pas de contour, si B=1 contour vert
Z est la taille de la police: 2 ou 3

### afficher un slider
topic: j/[nomDevice]/c/d  
content: S,XX,CC,value in percent
afficher du slider a l'emplacement XX (LSK1-4, RSK1-4) de couleur CC, la valeur est en pourcent

### commander la led pilote automatique
topic: j/[nomDevice]/c/d  
content: L,value (0 or 1)
allume (value=1) ou eteint la led (value=0)

### demande status (facultatif)
topic: j/[nomDevice]/c/reqstatus  
content: 1  
envoie une demande de status

## device vers bridge (mode evennement)
### Touche pressee (clickable, mecanique ou encorder)
topic: j/[device]/e/k  
content: [valeur bouton presse]  
envoie le code de la touche pressee (valeur chaine constante boutons tactiles/mecaniques/encodeurs)

### status
topic: j/[device]/e/s  
content: [code status]  
en reponse au reqstatus, retourne le status actuel  
0 OK
autre ERREUR