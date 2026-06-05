# 📊 DevOps Monitoring Dashboard

Système de monitoring temps réel construit entièrement en Python, conteneurisé avec Docker, et déployé sur Azure via un pipeline CI/CD GitHub Actions.

---

## 🏗️ Architecture cible

```
GitHub Repository
       │
       ▼  push to main
GitHub Actions CI/CD
  ├── lint (flake8)
  ├── test (pytest --cov ≥ 75 %)
  ├── build & push → Azure Container Registry (ACR)
  └── deploy → Azure Container Apps
       │
       ▼
Azure Container Apps Environment
  ├── devops-monitor-api  (FastAPI — port 8000)
  │   ├── GET  /health                  ← liveness probe
  │   ├── GET  /metrics                 ← CPU, mémoire, disque (psutil)
  │   ├── WS   /ws/metrics              ← stream JSON toutes les secondes
  │   ├── POST /servers                 ← enregistrer un serveur (API key)
  │   ├── GET  /servers                 ← lister les serveurs + statut
  │   ├── DELETE /servers/{id}          ← supprimer un serveur (API key)
  │   └── POST /servers/{id}/check      ← déclencher un health check manuel
  │
  └── devops-monitor-dashboard  (Streamlit — port 8501)
      ├── Onglet Métriques : KPIs + graphique live (fenêtre 60 s)
      └── Onglet Serveurs : tableau coloré + formulaire d'enregistrement
```

---

## 🛠️ Stack Technique

* **Langage** : Python 3.11
* **Framework API** : FastAPI + Uvicorn (ASGI)
* **Frontend** : Streamlit (Premium Styling, Outfit Font)
* **Client HTTP** : httpx (async)
* **Métriques système** : psutil (non-bloquant)
* **Authentification** : API Key via le header `X-API-Key`
* **Conteneurisation** : Docker, Docker Compose
* **Tests** : pytest, pytest-cov, FastAPI TestClient
* **CI/CD** : GitHub Actions
* **Hébergement cloud** : Azure Container Registry (ACR) + Azure Container Apps (ACA)

---

## 🚀 Lancement Local (Moins de 5 minutes)

### Prérequis
* Python 3.11
* Docker & Docker Compose
* Make (optionnel, mais recommandé)

### Instructions rapides

1. **Cloner le projet et se rendre dans le répertoire** :
   ```bash
   cd mini-projet
   ```

2. **Créer et configurer le fichier d'environnement** :
   ```bash
   cp .env.example .env
   # Remplissez les valeurs (par exemple API_KEY=dev-secret-key)
   ```

3. **Démarrer la stack locale (Docker Compose)** :
   ```bash
   make up
   ```
   * *L'API sera disponible sur :* [http://localhost:8000/docs](http://localhost:8000/docs)
   * *Le Dashboard sera disponible sur :* [http://localhost:8501](http://localhost:8501)

4. **Consulter les logs** :
   ```bash
   make logs
   ```

5. **Arrêter la stack** :
   ```bash
   make down
   ```

### Commandes alternatives (Lancement hors Docker pour Dev Local)
Pour exécuter les services séparément sans Docker :
```bash
# Lancement des tests avec couverture
make test

# Lancement du linter
make lint

# Lancement combiné des services locaux en tâche de fond
make dev
```

---

## ⚙️ Variables d'environnement

Le projet utilise les variables d'environnement suivantes à renseigner dans le fichier `.env` :

* `API_KEY` : Clé d'API partagée permettant de sécuriser les endpoints d'écriture/suppression de l'API. (Défaut : `dev-secret-key`).
* `API_BASE_URL` : URL de l'API cible que le Dashboard Streamlit va interroger.
  * En local hors Docker : `http://localhost:8000`
  * En local sous Docker Compose : `http://api:8000`
  * En production sur Azure : `https://<nom-api>.<region>.azurecontainerapps.io`

---

## ☁️ Déploiement Azure (Guide Pas-à-Pas)

Pour déployer cette application sur Azure, suivez les étapes manuelles ci-dessous depuis votre terminal équipé d'**Azure CLI** (`az`).

### 1. Provisionner l'Infrastructure Azure

Connectez-vous à Azure et configurez votre abonnement :
```bash
az login
```

Définissez le groupe de ressources et l'emplacement :
```bash
# Créer le groupe de ressources
az group create --name devops-monitor-rg --location westeurope

# Créer l'Azure Container Registry (ACR) (le nom doit être unique au monde)
az acr create --name <votre-acr-unique> --resource-group devops-monitor-rg --sku Basic --admin-enabled true

# Créer l'environnement Azure Container Apps
az containerapp env create \
  --name devops-monitor-env \
  --resource-group devops-monitor-rg \
  --location westeurope
```

### 2. Pousser les premières images Docker sur l'ACR (Optionnel / Initial)

Pour le déploiement initial des applications Container Apps, il est plus simple de pousser d'abord une image de démarrage sur votre ACR :
```bash
# Connexion locale à l'ACR
az acr login --name <votre-acr-unique>

# Builder et pousser l'API
docker build -t <votre-acr-unique>.azurecr.io/devops-monitor-api:latest -f api/Dockerfile .
docker push <votre-acr-unique>.azurecr.io/devops-monitor-api:latest

# Builder et pousser le Dashboard
docker build -t <votre-acr-unique>.azurecr.io/devops-monitor-dashboard:latest -f dashboard/Dockerfile .
docker push <votre-acr-unique>.azurecr.io/devops-monitor-dashboard:latest
```

### 3. Créer les applications Container Apps sur Azure

```bash
# Déployer l'API Container App
az containerapp create \
  --name devops-monitor-api \
  --resource-group devops-monitor-rg \
  --environment devops-monitor-env \
  --image <votre-acr-unique>.azurecr.io/devops-monitor-api:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server <votre-acr-unique>.azurecr.io \
  --env-vars API_KEY=dev-secret-key

# Récupérez l'URL (FQDN) de l'API générée par Azure (ex: https://devops-monitor-api.westeurope.azurecontainerapps.io)
# Déployer le Dashboard Container App (remplacez <URL_API_PROD> par l'URL FQDN obtenue)
az containerapp create \
  --name devops-monitor-dashboard \
  --resource-group devops-monitor-rg \
  --environment devops-monitor-env \
  --image <votre-acr-unique>.azurecr.io/devops-monitor-dashboard:latest \
  --target-port 8501 \
  --ingress external \
  --registry-server <votre-acr-unique>.azurecr.io \
  --env-vars API_BASE_URL=<URL_API_PROD> API_KEY=dev-secret-key
```

### 4. Configurer les Secrets GitHub pour le pipeline CI/CD

Pour automatiser le déploiement sur chaque `push` sur la branche `main`, générez un **Service Principal** Azure pour GitHub Actions :
```bash
az ad sp create-for-rbac --name "github-actions-devops-monitor" --role contributor \
  --scopes /subscriptions/<votre-subscription-id>/resourceGroups/devops-monitor-rg \
  --sdk-auth
```

Ajoutez les secrets suivants dans les paramètres de votre dépôt GitHub (`Settings > Secrets and variables > Actions`) :

| Secret GitHub | Valeur attendue |
| --- | --- |
| `AZURE_CLIENT_ID` | La valeur de `clientId` issue du JSON retourné ci-dessus |
| `AZURE_CLIENT_SECRET` | La valeur de `clientSecret` issue du JSON retourné ci-dessus |
| `AZURE_TENANT_ID` | La valeur de `tenantId` issue du JSON retourné ci-dessus |
| `AZURE_SUBSCRIPTION_ID`| La valeur de `subscriptionId` issue du JSON |
| `ACR_NAME` | Le nom de votre registre ACR (ex : `<votre-acr-unique>`) |
| `API_KEY` | La clé secrète d'API de production |

Désormais, tout push sur `main` exécutera automatiquement le pipeline CI/CD pour tester la qualité du code et mettre en ligne la dernière version.

---

## 📈 Liens de Production (Une fois déployé)

* **Documentation API (Swagger) :** `https://devops-monitor-api.<votre-env-id>.<region>.azurecontainerapps.io/docs`
* **Frontend Dashboard Streamlit :** `https://devops-monitor-dashboard.<votre-env-id>.<region>.azurecontainerapps.io`
