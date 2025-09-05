import os
import pandas as pd

def clean_clients_data(date: str):
    """
    Nettoie et transforme les données des clients extraites.
    """
    input_path = os.path.join("data", "raw_data", "clients", str(date.year), str(date.month), f"{str(date.day)}.csv")
    output_path = os.path.join("data", "clean_data", "clients", str(date.year), str(date.month), f"{str(date.day)}.csv")

    if not os.path.exists(input_path):
        print(f"Fichier client non trouvé pour la date {date}")
        return

    df = pd.read_csv(input_path)
    
    #  Supprimer les doublons
    df.drop_duplicates(inplace=True)

    #  Supprimer les lignes avec des valeurs manquantes
    df.dropna(subset=['client_id', 'email_client'], inplace=True)
    
    # Créer les répertoires de sortie s'ils n'existent pas
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Fichier client nettoyé et enregistré dans : {output_path}")

# Vous pouvez créer des fonctions similaires pour les produits et les commandes
def clean_products_data(date: str):
    """
    Nettoie et transforme les données des produits extraites.
    """
    input_path = os.path.join("data", "raw_data", "products", str(date.year), str(date.month), f"{str(date.day)}.csv")
    output_path = os.path.join("data", "clean_data", "products", str(date.year), str(date.month), f"{str(date.day)}.csv")

    if not os.path.exists(input_path):
        print(f"Fichier produit non trouvé pour la date {date}")
        return

    df = pd.read_csv(input_path)

    # Exemple de transformations :
    # Conversion de la colonne 'price' en numérique
    #df['price'] = pd.to_numeric(df['price'])
    
    # Créer les répertoires de sortie s'ils n'existent pas
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Fichier produit nettoyé et enregistré dans : {output_path}")


def clean_orders_data(date: str):
    """
    Nettoie et transforme les données des commandes extraites.
    """
    input_path = os.path.join("data", "raw_data", "orders", str(date.year), str(date.month), f"{str(date.day)}.csv")
    output_path = os.path.join("data", "clean_data", "orders", str(date.year), str(date.month), f"{str(date.day)}.csv")
    if not os.path.exists(input_path):
        print(f"Fichier commandes non trouvé pour la date {date}")
        return

    df = pd.read_csv(input_path)

    # Exemple de transformations :
    # Convertir le type de date et vérifier les valeurs aberrantes, etc.
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Créer les répertoires de sortie s'ils n'existent pas
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Fichier commandes nettoyé et enregistré dans : {output_path}")


if __name__ == "__main__":
    from datetime import datetime
    # Exemple d'exécution pour la date du 3 juin 2024
    date_to_process = datetime.strptime("2024-05-10", "%Y-%m-%d")

    clean_clients_data(date_to_process)
    #clean_products_data(date_to_process)
    #clean_orders_data(date_to_process)