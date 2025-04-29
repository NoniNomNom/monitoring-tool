# Installation

## Pour debugging et modification du code :
- Suivre ces instructions pour la création d'un environnement virtuel (.venv) sur Visual Studio Code : https://code.visualstudio.com/docs/python/environments<br>
- Pour l'utilisation de Shiny dans VS Code : https://shiny.posit.co/py/docs/install.html <br>
- Installer les packages indiqués dans le fichier requirements.txt (étape possible lors de la création du .venv)<br>

## Installation chez soi : 
- Suivre ces instructions pour l'installation d'un serveur Shiny :<br>
https://posit.co/download/shiny-server/ (téléchargement et installation) <br>
https://docs.posit.co/shiny-server/ (documentation) <br>

## Stockage des données :
- Actuellement, les données (articles récoltés, articles sauvegardés, liste des mots clés, liste des flux RSS, liste des mots clés sélectionnés, liste des flux RSS sélectionnés) sont stockées au format ".json" dans un Google Drive.
- Pour faire le lien entre l'application et le Google Drive de votre choix, suivre ces instructions : https://docs.iterative.ai/PyDrive2/quickstart/#authentication 

## Webscraping :
- Le webscraping fait l'objet d'un traitement à part en ce qui concerne la récolte des données : à compléter. 
- Le résultat final est stocké avec les articles obtenus via flux RSS. 

## Pistes d'améliorations :
- Webscraping pour les sites sans flux RSS
- Annotation du code