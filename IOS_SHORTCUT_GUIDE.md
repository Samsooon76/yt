# Guide pour créer un raccourci iOS pour YouTube to MP3

## Configuration du raccourci iOS

### Étape 1 : Créer un nouveau raccourci
1. Ouvrez l'app **Raccourcis** sur votre iPhone
2. Appuyez sur **+** pour créer un nouveau raccourci
3. Nommez votre raccourci "YouTube to MP3"

### Étape 2 : Ajouter les actions

#### Action 1 : Obtenir l'URL du presse-papiers
- Recherchez et ajoutez l'action **"Obtenir le presse-papiers"**
- Cela récupère automatiquement l'URL YouTube copiée

#### Action 2 : Faire une requête web
- Ajoutez l'action **"Obtenir le contenu des URL"**
- Configurez comme suit :
  - **URL** : `https://votre-domaine.com/api/convert`
  - **Méthode** : POST
  - **En-têtes** : 
    - `Content-Type` : `application/json`
  - **Corps de la requête** : 
    ```json
    {
      "url": "[Sortie du presse-papiers]"
    }
    ```

#### Action 3 : Analyser la réponse JSON
- Ajoutez l'action **"Obtenir la valeur du dictionnaire"**
- Configurez pour obtenir la clé `download_url`

#### Action 4 : Télécharger le fichier MP3
- Ajoutez l'action **"Télécharger l'URL"**
- Utilisez l'URL de téléchargement de l'étape précédente

#### Action 5 : Sauvegarder dans Photos/Fichiers
- Ajoutez l'action **"Enregistrer dans l'album photo"** ou **"Enregistrer dans Fichiers"**
- Choisissez le dossier de destination

### Étape 3 : Configuration avancée

#### Partage depuis YouTube
1. Dans les réglages du raccourci, activez **"Utiliser avec le partage"**
2. Configurez les types acceptés : **URLs**
3. Le raccourci apparaîtra maintenant dans le menu partage de YouTube

#### Notification de fin
Ajoutez une action **"Afficher une notification"** à la fin pour confirmer le téléchargement.

## Utilisation

1. **Méthode 1 - Presse-papiers** :
   - Copiez une URL YouTube
   - Lancez le raccourci depuis l'app Raccourcis

2. **Méthode 2 - Partage direct** :
   - Sur YouTube, appuyez sur Partager
   - Sélectionnez "YouTube to MP3"
   - Le téléchargement se lance automatiquement

## API Endpoints disponibles

### Conversion complète
```
POST /api/convert
Body: {"url": "https://youtube.com/watch?v=..."}
Response: {
  "success": true,
  "title": "Titre de la vidéo",
  "download_url": "https://votre-app.com/download/id"
}
```

### Informations seulement
```
POST /api/info
Body: {"url": "https://youtube.com/watch?v=..."}
Response: {
  "success": true,
  "info": {
    "title": "Titre",
    "duration": 180,
    "uploader": "Chaîne"
  }
}
```

## Hébergement sur Hostinger

### Préparation pour le déploiement
1. **Fichier requirements.txt** (déjà créé)
2. **Configuration de l'environnement** :
   - Définir `SESSION_SECRET` dans les variables d'environnement
3. **Permissions d'écriture** pour le dossier downloads

### Variables d'environnement requises
```
SESSION_SECRET=votre-clé-secrète-unique
```

### Structure des fichiers pour l'upload
```
/
├── app.py
├── main.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── downloads/
    └── .gitkeep
```

## Conseils d'utilisation

- **Qualité audio** : L'app télécharge en MP3 192kbps par défaut
- **Limitations** : Certaines vidéos protégées peuvent ne pas fonctionner
- **Performance** : Les vidéos longues prennent plus de temps à convertir
- **Stockage** : Les fichiers sont automatiquement nettoyés après téléchargement

## Dépannage

### Problèmes courants
1. **"URL invalide"** : Vérifiez que l'URL est bien une URL YouTube
2. **"Could not extract video information"** : Restrictions YouTube sur serveurs cloud Replit
   - Essayez avec une vidéo plus récente ou populaire
   - Certaines vidéos passent mieux que d'autres
   - Considérez un hébergement VPS pour plus de fiabilité
3. **"Conversion échouée"** : La vidéo peut être protégée ou indisponible
4. **"Fichier non trouvé"** : Réessayez la conversion, le fichier a peut-être expiré

### Limitations connues des serveurs cloud
- **YouTube restreint l'accès** depuis les serveurs cloud comme Replit
- **Taux de succès variable** selon le type de vidéo
- **Alternative recommandée** : VPS personnel ou hébergement dédié

### Support
Pour tout problème, vérifiez d'abord que :
- L'URL YouTube est valide et accessible
- Votre connexion internet est stable
- L'app est bien hébergée et accessible