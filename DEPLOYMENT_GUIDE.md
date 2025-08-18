# Guide de déploiement sur Hostinger

## Préparation des fichiers

### 1. Fichiers à télécharger sur Hostinger

Créez ces dossiers et fichiers sur votre hébergement Hostinger :

```
/public_html/
├── app.py                          # Application principale
├── main.py                         # Point d'entrée
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

### 2. Configuration des variables d'environnement

Dans le panneau de contrôle Hostinger, ajoutez ces variables :

```
SESSION_SECRET=votre-clé-secrète-très-longue-et-complexe
```

### 3. Installation des dépendances

Si Hostinger supporte pip, installez les dépendances :

```bash
pip install -r hostinger_requirements.txt
```

## Configuration du serveur web

### Option 1 : Apache + mod_wsgi

Créez un fichier `.htaccess` :

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ app.py/$1 [QSA,L]
```

### Option 2 : Gunicorn (si supporté)

```bash
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
```

### Dépendances système requises

Vérifiez que ces packages sont installés :
- `python3`
- `ffmpeg` (pour la conversion audio)
- `python3-pip`

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