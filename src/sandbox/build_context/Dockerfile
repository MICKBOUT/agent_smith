# 1. Utiliser une image Python officielle légère (Alpine ou Slim)
FROM python:3.14-slim

# 2. Définir le répertoire de travail dans le conteneur
WORKDIR /goinfre

# 3. Copier les fichiers du projet dans le conteneur
COPY worker.py .
COPY sandbox_utils.py .

# 4. Commande d'exécution
CMD ["python", "worker.py"]