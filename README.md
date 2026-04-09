# Projet 10: Évaluez les performances d'un LLM

> Ce projet implémente un assistant virtuel basé sur le modèle Mistral, utilisant la technique de **Retrieval-Augmented Generation** (RAG) pour fournir des réponses précises et contextuelles à partir d'une base de connaissances personnalisée.
> Des discussions Reddit et excels concernant la NBA constitueront cette base.

<!-- Balise d'en-tête -->
<a id="readme-top"></a>

<!-- PROJET -->
<br />
<div align="center">
  <a href="https://github.com/S-S-Zheng/Openclassrooms_P10.git">
    <!-- <img src="images/logo.png" alt="Logo" width="80" height="80"> -->
  </a>

<h3 align="center">Projet 10: Évaluez les performances d'un LLM</h3>

  <p align="center">
    Projet 10 de la formation d'OpenClassrooms: Data scientist Machine Learning (projet débuté le 26/03/2026)
    <br />
    <a href="https://github.com/S-S-Zheng/Openclassrooms_P10.git"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/S-S-Zheng/Openclassrooms_P10.git">View Demo</a>
    &middot;
    <a href="https://github.com/S-S-Zheng/Openclassrooms_P10.git/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/S-S-Zheng/Openclassrooms_P10.git/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Sommaire</summary>
  <ol>
    <li><a href="#Fonctionnalités">Fonctionnalités</a></li>
    <li><a href="#Prérequis">Prérequis</a></li>
    <li><a href="#Installation">Installation</a></li>
    <li><a href="#Structure-du-projet">Structure du projet</a></li>
    <li><a href="#Utilisation">Utilisation</a></li>
      <ul>
        <li><a href="#Ajouter-des-documents">Ajouter des documents</a></li>
        <li><a href="#Indexer-les-documents">Indexer les documents</a></li>
        <li><a href="#Remplir-la-base-de données">Remplir la base de données</a></li>
        <li><a href="#Lancer-lapplication">Lancer l'application</a></li>
      </ul>
    <li><a href="#Modules-principaux">Modules principaux</a></li>
      <ul>
        <li><a href="#Orchestration">Orchestration store`</a></li>
        <li><a href="#Outil-SQL">Outil SQL</a></li>
        <li><a href="#Outil-sémantique">Outil sémantique</a></li>
      </ul>
    <li><a href="#Personnalisation">Personnalisation</a></li>
    <li><a href="#License">License</a></li>
  </ol>
</details>

## Fonctionnalités

- **Recherche sémantique** avec FAISS pour trouver les documents pertinents
- **Recherche tabulaire** avec une requête SQL pour trouver des données numériques
- **Génération de réponses** avec le modèle Mistral (Small-latest)
- **Paramètres personnalisables** modèle, hyperparamètres

## Prérequis

- Python 3.12+
- Clef API Mistral (obtenue sur [console.mistral.ai](https://console.mistral.ai/))
- Créer un compte logfire (eventuellement clef API) : [logfire](https://logfire-eu.pydantic.dev/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Installation

1. **Cloner le dépôt**

    ```bash
    git clone https://github.com/S-S-Zheng/Openclassrooms_P10.git
    cd Openclassrooms_P10.git
    ```

2. **Créer un environnement virtuel**

    ```bash
    # Création de l'environnement virtuel
    python -m venv venv

    # Activation de l'environnement virtuel
    # Sur Windows
    venv\Scripts\activate
    # Sur macOS/Linux
    source venv/bin/activate
    ```

3. **Installer les dépendances (Poetry)**

    ```bash
    poetry init
    poetry install
    poetry shell

    # Configurer les variables d'environnement
    cp .env.example .env
    # Éditer .env
    # Variables (filtres...) ET MISTRAL_API_KEY
    ```

4. **Configurer la clé API**

    Toujours dans le `.env`:

    ```bash
    MISTRAL_API_KEY=votre_clé_api_mistral
    ```

5. **Logfire quickstart**

    ```bash
    # Install SDK
    poetry add logfire

    # En environnement de dev:
    # Authentification de l'environnement local
    poetry run logfire auth
    # Set up du dossier logfire
    poetry run logfire projects use nom-dossier-logfire

    # En environnement de prod:
    export LOGFIRE_TOKEN='__YOUR_LOGFIRE_WRITE_TOKEN__'
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Structure du projet

```text
.
├── CLI                                     # Scripts d'exécution en ligne de commande
│   ├── evaluate_ragas.py                   # Évaluation de la qualité RAG (Fidélité, Pertinence)
│   ├── indexer.py                          # Pipeline d'ingestion sémantique (PDF -> Vector DB)
│   └── load_excel_to_db.py                 # Pipeline d'ingestion tabulaire (Excel -> SQLite)
├── datas                                   # Stockage des données du projet
│   ├── inputs                              # Sources brutes (Documents PDF et Statistiques Excel)
│   ├── NBA_database                        # Persistance des données structurées
│   ├── qa_pairs                            # Jeux de données de test (Questions/Réponses)
│   └── vector_db                           # Index sémantique pour la recherche vectorielle
├── notebooks                               # Travaux d'exploration et brouillons
│   └── rapport.ipynb                       # Rapport de mise en place et d’évaluation du système
├── poetry.lock                             # Verrouillage des versions des dépendances
├── pyproject.toml                          # Configuration du projet et des dépendances Poetry
├── src                                     # Code source de l'application
│   └── livrable_p10                        # Package principal
│       └── app
│           ├── agents                      # Cerveau de l'application
│           │   └── nba_agent.py            # Agent Pydantic AI (Orchestration ReAct & Tool calling)
│           ├── db                          # Couche d'accès aux données (ORM)
│           │   ├── base.py                 # Configuration SQLAlchemy (Declarative Base)
│           │   ├── create_db.py            # Logique d'initialisation des tables
│           │   ├── database.py             # Gestion des sessions et de la connexion
│           │   └── models_db.py            # Définition des schémas SQL (Player, Stat, Team, Report)
│           ├── main.py                     # Interface utilisateur Streamlit (Point d'entrée)
│           ├── tools                       # Outils pour l'agent
│           │   ├── semantic                # Recherche contextuelle (RAG)
│           │   │   └── vector_store.py     # Moteur de recherche FAISS & Embedding local
│           │   └── sql                     # Analyse de données structurées
│           │       ├── sql_pipeline.py     # Pipeline de requête pour NLP -> SQL
│           │       └── sql_tool.py         # Moteur de génération et exécution SQL sécurisée
│           └── utils                       # Modules utilitaires transverses
│               ├── blacklist.txt           # Mots-clés interdits (Sécurité SQL)
│               ├── config.py               # Gestion des variables d'environnement et constantes
│               ├── data_loader.py          # Utilitaires de lecture de fichiers
│               ├── document_reshape.py     # Logique de nettoyage et de structuration des PDF
│               ├── prompts.py              # Centralisation des prompts System et Few-shot
│               └── schemas.py              # Schémas de validation Pydantic (Input/Output)
└── README.md                               # Documentation principale du projet
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Utilisation

### Ajouter des documents

Placez vos documents dans le dossier `inputs/`. Les formats supportés sont :

- PDF
- TXT
- DOCX
- EXCEL
- JSON

### Indexer les documents

Exécutez le script ``ìndexer.py`` pour traiter les documents et créer l'index FAISS :

```bash
# En vous plaçant à la racine du projet
python CLI/indexer.py
```

Le workflow du script est le suivant :

1. *Initialisation et Récupération des Arguments*
    Le script démarre en récupérant les paramètres d'entrée via argparse :
    - Le répertoire source des documents (--input-dir).
    - Une éventuelle URL de téléchargement (--data-url).
    - Configuration du logging pour suivre l'avancement en temps réel.

2. *Extraction de la Donnée (Extraction)*
    Le script gère l'arrivée des fichiers :
    - Si une URL est fournie, le fichier est téléchargé, dézippé et stocké dans le répertoire d'entrée.
    - Si aucune URL n'est fournie : Le script bascule sur l'utilisation des fichiers locaux déjà présents dans le dossier.

3. *Parsing et Gestion du Cache (Transformation)*
    Vérification du cache (évite de refaire l'OCR). Si le cache est vide, lit et parse les données non-structurées, les transforme en "documents" bruts et une copie est sauvegardée au cas où.

4. *Nettoyage Sémantique (Processing)*
    Une fois le texte extrait, il est nettoyé pour améliorer la qualité différents patterns détéctés et ``blacklist.txt`` pour supprimer le bruit (mentions inutiles, headers répétitifs, mots spécifiques). Les documents sont "titrés" ou restructurés pour que l'index contienne une donnée sémantiquement riche.

5. *Construction de l'Index Vectoriel (Loading)*
    Le script appel ensuite ``VectorStoreManager``, pour vectoriser, créer l'index et persister sur le disque.

### Remplir la base de données

Exécutez le script ``load_excel_to_db.py`` pour remplir la base de données.

```bash
# En vous plaçant à la racine du projet
python CLI/load_excel_to_db.py
```

Workflow du script :

1. *Initialisation et Reset de la Base*
    Le script appelle ``init_db(reset_tables=True)`` pour supprimer les anciennes tables et recréer un schéma SQL vierge, garantissant l'idempotence du processus.

2. *Extraction et Nettoyage (Pandas)*
    Lecture des feuilles Excel. Le script nettoie les en-têtes, supprime les colonnes "fantômes" (Unnamed) et applique un strip() sur les données textuelles.

3. *Validation et Normalisation (Pydantic)*
    Chaque ligne est validée par NBAInputSchema ou TeamInputSchema. Cette étape assure l'intégrité des types et gère la conversion des valeurs (ex: NaN vers None).

4. *Ingestion et agregation des tables*
    Remplis les tables ``Player``, ``Stat``, ``Team`` et réalise certaine agrégation.

5. *Validation de la Transaction*
    Le script effectue un ``commit()`` final pour persister les données. En cas d'erreur, un ``rollback()`` est déclenché pour prévenir toute corruption de la base.

### Lancer l'évaluation RAGAS

Exécutez le script ``evaluate_ragas.py`` pour lancer une évaluation RAGAS du RAG.

```bash
# En vous plaçant à la racine du projet
python CLI/evaluate_ragas.py
```

L'évaluateur va regarder les métriques suivantes:

- *Faithfulness (Fidélité)*
    Mesure si la réponse de l'IA est factuellement soutenue par les documents extraits (détection d'hallucinations).

- *Answer Relevancy (Pertinence)*
    Évalue si la réponse reste pertinente par rapport à la question posée.

- *Context Recall (Rappel du Contexte)*
    Vérifie si toutes les informations nécessaires pour répondre (définies dans la "Ground Truth") sont bien présentes dans les documents extraits de la base vectorielle.

Workflow du script :

1. *Initialisation de l'Agent*
    Le script encapsule l'Agent NBA dans un ``RAGPrototypeWrapper`` pour isoler les composants de recherche (contexte) et de génération (réponse).

2. *Inférence sur Dataset de Test*
    Charge un fichier JSON de Q\&A ``qa_pairs.json``. L'agent traite chaque question pour générer une réponse réelle et extraire les contextes associés.

3. *Configuration du Juge LLM*
    Utilisation de Mistral-Small comme "Juge" pour attribuer des scores.

4. *Calcul des Scores*
    Le script itère sur le dataset, calcule les métriques et gère les pauses (async sleep) pour respecter les limites de l'API (Rate Limiting).

5. *Rapport et Sauvegarde*
    Génère un scoring en std et une sauvegarde des résultats dans ``ragas.json`` pour analyse ultérieure.

### Lancer l'application

```bash
# A la racine du projet
streamlit run src/livrable_p10/app/main.py
```

L'application sera accessible à l'adresse <http://localhost:8501> dans votre navigateur.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Modules principaux

### Orchestration

``src/livrable_p10/app/agents/nba_agent.py``

Cerveau de l'application basé sur Pydantic AI :

1. *Aiguillage des outils*
    Détermine s'il doit utiliser l'outil SQL ``ask_database`` ou l'outil Sémantique ``ask_index``

2. *Mémoire court terme*
    Gère l'historique de la conversation pour le contexte.

### Outil SQL

``src/livrable_p10/app/tools/sql/sql_tool.py & sql_pipeline.py``

Transforme le langage naturel en requêtes complexes :

1. *NLP --> SQL*
    Traduit les questions en requêtes SQLite via Mistral.

2. *Sécurité \& Nettoyage*
    Mode de lecture seule, validation pydantic, limite les instructions.

3. *Monitoring*
    Remplit la table ``Report`` pour suivre les requêtes.

4. *Exécution*
    Récupère les statistiques brutes (points, rebonds, victoires) en base.

### Outil sémantique

``src/livrable_p10/app/tools/semantic/vector_store.py``

Gère toutes les fonctionnalités liées à l'index :

1. *Charge et chunk*
    A l'instanciation de ``VectoreStoreManager``, va tenter de charger et chunker les documents brutes.

2. *Embedding et persistence*
    Utilise un modèle HuggingFace local pour transformer le texte en vecteurs. ``build_index()`` va transformer en objet document puis splitter, emmbeder, et sauvegarder les vecteurs générés par les documents.

3. *Recherche*
    Effectue une recherche de similarité pour extraire les passages les plus pertinents via sa méthode ``search()``.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Personnalisation

Vous pouvez personnaliser l'application en modifiant les paramètres dans `config.py` :

- Modèles Mistral utilisés
- Des hyperparamètres de FAISS et du LLM comme la température, le chunking, le nombre de contexte à fournir au LLM
- Les chemins de lecture et de persistence

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
