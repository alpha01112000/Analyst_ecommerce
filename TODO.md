# TODO: Corriger les bugs dans src/dags/common/extract.py

- [x] Ajouter l'import manquant pour `io`
- [x] Corriger SERVICE_ACCOUNT_FILE vers "service_account.json"
- [x] Dans extract_clients: Obtenir l'ID du dossier et l'ajouter à la requête de recherche de fichiers
- [x] Dans extract_clients: Ajouter vérification si daily_clients_files est vide avant d'accéder à [0]
- [x] Dans extract_products: Ajouter vérification de dossier et obtenir ID
- [x] Dans extract_products: Ajouter vérification si products_files est vide
- [x] Dans extract_orders: Utiliser une requête SQL paramétrée
- [x] Ajouter try-except autour des appels API Google Drive
- [x] Tester les modifications
