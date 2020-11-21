## Liste des valeurs des constantes
### Disposition ecran
L'ecran est divise en 4 colonnes et 8 lignes. Le code position sur 2 chiffres donne la colonne (a partir de 0) et la ligne (a partir de 1) depuis le coin superieur gauche
01 11 21 31  
02 12 22 32   
03 13 23 33  
04 14 24 34  
05 15 25 35  
06 16 26 36  
07 17 27 37  
08 18 28 38  

### Encodeurs
INC1UP 50  
INC1DN 51  
INC2UP 52  
INC2DN 53  

### Boutons mecaniques
BT1 57  
BT2 58  
BT3 59  

### Couleurs
WHITE 99  
YELLOW 98  
GREEN 97  
BLACK 96  

## bridge vers device (mode commande)
### Nouvel ecran
topic: j/[nomDevice]/c/d  
content: N,[titre]  
New Screen, efface l'ecran, supprime les boutons/reactions et ecrit titre en haut en blanc

### Creer un bouton clickable sur l'ecran
topic: j/[nomDevice]/c/d  
content: B,[code Side Key sur 2 car],[intutule bouton]  
cree un Bonton encadre en vert LSK1-4, RSK1-4, qui réagit aux appuis et retourne la position du bouton presse sur le topic key

### Affichage texte, avec ou sans contour clickable
topic: j/[nomDevice]/c/d  
content: T,XX,CC,B,Z,[chaine formattee]  
affichage du text chaine a l'emplacement Side Key XX de couleur CC  
si B=0, pas de contour, si B=1 contour vert (le bouton reagit au click et retourne la position sur le topic key)
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
envoie le code de position de la touche pressee (valeur chaine constante boutons tactiles/mecaniques/encodeurs)

### status
topic: j/[device]/e/s  
content: [code status]  
en reponse au reqstatus, retourne le status actuel  
0 OK
autre ERREUR
