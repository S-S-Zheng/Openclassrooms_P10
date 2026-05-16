#!/bin/bash

# Configuration Git
git config --global user.email "actions@github.com"
git config --global user.name "Github Actions"

# 1. Ajout du remote avec token
git remote add hf https://x-access-token:$HF_TOKEN@huggingface.co/spaces/$HF_REPO

# 2. STRATÉGIE ORPHAN : On crée une branche vide de tout historique
git checkout --orphan temp-main

# 3. Nettoyage de l'index pour repartir de zéro
git rm -rf --cached .

# 4. Création d'un .gitattributes propre pour ton modèle ONNX
cat << EOF > .gitattributes
*.onnx filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.json filter=lfs diff=lfs merge=lfs -text
EOF

# 5. Ajout sélectif des fichiers (on suit ta structure Dockerfile)
git add .gitattributes
git add README.md
git add Dockerfile
git add pyproject.toml poetry.lock
git add src/
git add configs/
# On ajoute spécifiquement tes dossiers de données
git add datas/NBA_database/interactions.db
git add datas/vector_db/document_chunks.pkl
git add datas/vector_db/faiss_index.idx

# 6. Commit et Push forcé
git commit -m "Deploy clean state to HF"
git push hf temp-main:main --force