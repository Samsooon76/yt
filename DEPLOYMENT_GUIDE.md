# Guide de déploiement sur Hostinger

## Préparation des fichiers

### 1. Fichiers à télécharger sur Hostinger

Créez ces dossiers et fichiers sur votre hébergement Hostinger :

```
/public_html/
├── app.py                          # Application principale
├── main.py                         # Point d'entrée
├── passenger_wsgi.py               # Entrée WSGI (Passenger)
├── hostinger_requirements.txt      # Dépendances Python
├── templates/
│   └── index.html                 # Interface web
├── static/
│   ├── css/
│   │   └── style.css              # Styles CSS
│   └── js/
│       └── app.js                 # JavaScript frontend
└── downloads/                     # Dossier pour fichiers temporaires
    └── .gitkeep
```

Optionnel (si vous n'avez pas ffmpeg côté serveur):

```
/public_html/
└── bin/
    └── ffmpeg                     # Binaire ffmpeg téléversé par vos soins
```

### 2. Configuration des variables d'environnement

Dans le panneau de contrôle Hostinger, ajoutez ces variables :

```
SESSION_SECRET=votre-clé-secrète-très-longue-et-complexe
FFMPEG_PATH=/home/USER/domains/votre-domaine.com/public_html/bin/ffmpeg
```

### 3. Installation des dépendances

Si Hostinger supporte pip, installez les dépendances :

```bash
pip install -r hostinger_requirements.txt
```

## Configuration du serveur web

### Option recommandée : hPanel > Applications Python (Passenger)

1) Dans hPanel > Avancé > Applications Python, créez une application:
- Version Python: choisissez celle supportée (ex: 3.10+)
- Dossier de l'application: `public_html`
- Fichier de démarrage: `passenger_wsgi.py`
- Point d'entrée WSGI: `application`

2) Cliquez sur « Installer les dépendances » et indiquez:
```
hostinger_requirements.txt
```

3) Ajoutez les variables d'environnement (SESSION_SECRET, FFMPEG_PATH si nécessaire).

4) Redémarrez l'application.

Vos assets `static/` et `templates/` sont servis par Flask. Pas besoin de configuration .htaccess spécifique dans ce mode.

### Option alternative : Gunicorn (VPS ou accès SSH avancé)

```
gunicorn --bind 0.0.0.0:8000 main:app
```

## Configuration spécifique Hostinger

### Permissions des dossiers
```bash
chmod 755 downloads/
chmod 644 *.py
chmod 644 templates/*.html
chmod 644 static/css/*.css
chmod 644 static/js/*.js
chmod 755 bin/ffmpeg   # si vous avez téléversé un binaire ffmpeg
```

### Dépendances système requises

Idéalement disponibles côté serveur :
- `python3`
- `ffmpeg` (pour la conversion audio)
- `python3-pip`

Si `ffmpeg` n'est pas installé côté serveur, téléversez un binaire statique dans `public_html/bin/ffmpeg` et définissez `FFMPEG_PATH`.

## Structure finale de l'URL

Votre application sera accessible à :
```
https://votre-domaine.com/
```

Les API endpoints seront :
```
https://votre-domaine.com/api/convert
https://votre-domaine.com/api/info
```

## Tests après déploiement

### 1. Test de l'interface web
- Visitez `https://votre-domaine.com/`
- Testez avec une URL YouTube
- Vérifiez le téléchargement du MP3

### 2. Test de l'API pour iOS Shortcuts
```bash
curl -X POST https://votre-domaine.com/api/convert \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=EXAMPLE"}'
```

Si l'API renvoie une erreur liée à ffmpeg, vérifiez `FFMPEG_PATH` ou la présence de ffmpeg côté serveur.

### 3. Vérification des logs
Consultez les logs d'erreur pour diagnostiquer les problèmes.

## Optimisations pour la production

### Sécurité
- Limitez les requêtes par IP
- Ajoutez HTTPS obligatoire
- Configurez CORS si nécessaire

### Performance
- Ajoutez un système de cache
- Limitez la taille des fichiers téléchargés
- Configurez un nettoyage automatique des fichiers temporaires

### Monitoring
- Surveillez l'espace disque
- Monitorer les erreurs de conversion
- Suivre l'utilisation des ressources

## Dépannage courant

### Erreur "Module not found"
- Vérifiez que toutes les dépendances sont installées
- Utilisez `pip list` pour voir les packages installés

### Erreur "Permission denied"
- Vérifiez les permissions des dossiers
- Assurez-vous que le dossier `downloads/` est accessible en écriture

### Erreur "ffmpeg not found"
- Installez ffmpeg sur le serveur
- Ou contactez Hostinger pour l'installation

### Problèmes de conversion
- Vérifiez les logs d'erreur
- Testez avec différentes URLs YouTube
- Vérifiez la connectivité internet du serveur

## Support technique

Si vous rencontrez des problèmes :
1. Vérifiez les logs d'erreur Python
2. Testez les URLs en local d'abord
3. Contactez le support Hostinger pour les problèmes serveur
4. Vérifiez que tous les fichiers ont été téléchargés correctement
