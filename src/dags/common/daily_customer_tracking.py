import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configuration du logging
logger = logging.getLogger('daily_customer_tracking')

def daily_customer_activity(df: pd.DataFrame, date_column: str = 'order_date', 
                           customer_column: str = 'customer_id') -> pd.DataFrame:
    """
    Analyse l'activité quotidienne des clients - Adaptée pour les données e-commerce
    
    Args:
        df (DataFrame): DataFrame contenant les données de commandes
        date_column (str): Nom de la colonne des dates
        customer_column (str): Nom de la colonne des identifiants clients
        
    Returns:
        DataFrame: Activité quotidienne des clients
    """
    try:
        # S'assurer que la colonne de date est au format datetime
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Extraire la date (sans l'heure)
        df['date'] = df[date_column].dt.date
        
        # Agrégation par date et client
        daily_activity = df.groupby(['date', customer_column]).agg({
            'order_id': 'nunique',    # Nombre de commandes
            'quantity': 'sum',        # Quantité totale achetée
            'total_amount': 'sum'     # Chiffre d'affaires généré
        }).reset_index()
        
        daily_activity.columns = ['date', 'customer_id', 'nb_commandes', 'quantite_totale', 'ca_total']
        
        logger.info(f"Activité quotidienne calculée pour {len(daily_activity)} enregistrements")
        return daily_activity
        
    except Exception as e:
        logger.error(f"Erreur dans daily_customer_activity: {str(e)}")
        raise

def new_customers_daily(df: pd.DataFrame, date_column: str = 'order_date', 
                       customer_column: str = 'customer_id') -> pd.DataFrame:
    """
    Identifie les nouveaux clients par jour (première commande)
    
    Args:
        df (DataFrame): DataFrame contenant les données de commandes
        date_column (str): Nom de la colonne des dates
        customer_column (str): Nom de la colonne des identifiants clients
        
    Returns:
        DataFrame: Nouveaux clients par jour
    """
    try:
        # Trouver la première commande de chaque client
        first_orders = df.groupby(customer_column)[date_column].min().reset_index()
        first_orders.columns = [customer_column, 'first_order_date']
        
        # Extraire la date seulement
        first_orders['date'] = pd.to_datetime(first_orders['first_order_date']).dt.date
        
        # Compter les nouveaux clients par jour
        new_customers = first_orders.groupby('date').size().reset_index()
        new_customers.columns = ['date', 'nouveaux_clients']
        
        logger.info(f"Nouveaux clients identifiés pour {len(new_customers)} jours")
        return new_customers
        
    except Exception as e:
        logger.error(f"Erreur dans new_customers_daily: {str(e)}")
        raise

def process_daily_customer_metrics(execution_date: datetime, db_path: str = "ecommerce_orders_may2024.db", 
                                  table_name: str = "ecommerce_orders") -> Dict[str, Any]:
    """
    Traite les métriques quotidiennes des clients et les sauvegarde
    
    Args:
        execution_date (datetime): Date d'exécution du DAG
        db_path (str): Chemin vers la base de données SQLite
        table_name (str): Nom de la table des commandes
        
    Returns:
        dict: Métriques quotidiennes des clients
    """
    try:
        # Charger les données du jour
        date_str = execution_date.strftime("%Y-%m-%d")
        logger.info(f"Traitement des métriques clients pour la date: {date_str}")
        
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f'SELECT * FROM {table_name} WHERE order_date = "{date_str}"', conn)
        conn.close()
        
        if df.empty:
            logger.warning(f"Aucune donnée trouvée pour la date {date_str}")
            return {"date": date_str, "error": "Aucune donnée disponible"}
        
        # Calcul des métriques
        metrics = {
            'date': date_str,
            'clients_uniques': df['customer_id'].nunique(),
            'total_commandes': df['order_id'].nunique(),
            'quantite_totale': df['quantity'].sum(),
            'chiffre_affaires': df['total_amount'].sum(),
            'panier_moyen': df['total_amount'].sum() / df['order_id'].nunique() if df['order_id'].nunique() > 0 else 0
        }
        
        # Identifier les nouveaux clients
        conn = sqlite3.connect(db_path)
        first_orders_query = f"""
        SELECT customer_id, MIN(order_date) as first_order_date 
        FROM {table_name} 
        GROUP BY customer_id
        """
        first_orders = pd.read_sql_query(first_orders_query, conn)
        conn.close()
        
        new_customers = first_orders[first_orders['first_order_date'] == date_str]
        metrics['nouveaux_clients'] = len(new_customers)
        
        # Clients de retour
        returning_customers = df[~df['customer_id'].isin(new_customers['customer_id'])]
        metrics['clients_fideles'] = returning_customers['customer_id'].nunique()
        
        # Taux de rétention (comparaison avec la veille)
        previous_day = (execution_date - timedelta(days=1)).strftime("%Y-%m-%d")
        conn = sqlite3.connect(db_path)
        previous_day_query = f'SELECT DISTINCT customer_id FROM {table_name} WHERE order_date = "{previous_day}"'
        previous_customers = pd.read_sql_query(previous_day_query, conn)
        conn.close()
        
        if not previous_customers.empty:
            returning_from_previous = df[df['customer_id'].isin(previous_customers['customer_id'])]
            metrics['taux_retention_jour'] = (returning_from_previous['customer_id'].nunique() / 
                                            previous_customers['customer_id'].nunique())
        else:
            metrics['taux_retention_jour'] = 0
        
        # Sauvegarder les résultats
        save_daily_metrics(metrics, execution_date)
        
        logger.info(f"Métriques calculées pour {date_str}: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"Erreur dans process_daily_customer_metrics: {str(e)}")
        raise

def save_daily_metrics(metrics: Dict[str, Any], execution_date: datetime) -> None:
    """
    Sauvegarde les métriques quotidiennes dans un fichier CSV
    
    Args:
        metrics (dict): Métriques à sauvegarder
        execution_date (datetime): Date d'exécution
    """
    try:
        # Créer le dossier de destination
        output_dir = "data/processed/customer_metrics"
        os.makedirs(output_dir, exist_ok=True)
        
        # Chemin du fichier
        year = execution_date.year
        month = execution_date.month
        file_path = os.path.join(output_dir, f"customer_metrics_{year}_{month:02d}.csv")
        
        # Convertir en DataFrame
        metrics_df = pd.DataFrame([metrics])
        
        # Sauvegarder (ajouter au fichier existant ou créer un nouveau)
        if os.path.exists(file_path):
            existing_df = pd.read_csv(file_path)
            updated_df = pd.concat([existing_df, metrics_df], ignore_index=True)
            updated_df.to_csv(file_path, index=False)
        else:
            metrics_df.to_csv(file_path, index=False)
        
        logger.info(f"Métriques sauvegardées dans {file_path}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des métriques: {str(e)}")
        raise

def generate_daily_customer_report(execution_date: datetime) -> str:
    """
    Génère un rapport quotidien des clients au format HTML
    
    Args:
        execution_date (datetime): Date du rapport
        
    Returns:
        str: Chemin vers le fichier de rapport généré
    """
    try:
        # Charger les métriques du jour
        date_str = execution_date.strftime("%Y-%m-%d")
        metrics = process_daily_customer_metrics(execution_date)
        
        # Générer le rapport HTML
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport Clients - {date_str}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .metrics {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .metric-item {{ margin: 10px 0; }}
                .value {{ font-weight: bold; color: #0066cc; }}
            </style>
        </head>
        <body>
            <h1>Rapport Quotidien des Clients</h1>
            <p>Date: {date_str}</p>
            
            <div class="metrics">
                <div class="metric-item">Clients uniques: <span class="value">{metrics.get('clients_uniques', 0)}</span></div>
                <div class="metric-item">Total commandes: <span class="value">{metrics.get('total_commandes', 0)}</span></div>
                <div class="metric-item">Quantité totale: <span class="value">{metrics.get('quantite_totale', 0)}</span></div>
                <div class="metric-item">Chiffre d'affaires: <span class="value">{metrics.get('chiffre_affaires', 0):.2f} €</span></div>
                <div class="metric-item">Panier moyen: <span class="value">{metrics.get('panier_moyen', 0):.2f} €</span></div>
                <div class="metric-item">Nouveaux clients: <span class="value">{metrics.get('nouveaux_clients', 0)}</span></div>
                <div class="metric-item">Clients fidèles: <span class="value">{metrics.get('clients_fideles', 0)}</span></div>
                <div class="metric-item">Taux de rétention: <span class="value">{metrics.get('taux_retention_jour', 0) * 100:.2f}%</span></div>
            </div>
        </body>
        </html>
        """
        
        # Sauvegarder le rapport
        reports_dir = "reports/customer_daily"
        os.makedirs(reports_dir, exist_ok=True)
        
        report_path = os.path.join(reports_dir, f"customer_report_{date_str}.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        logger.info(f"Rapport généré: {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Erreur dans generate_daily_customer_report: {str(e)}")
        raise

# Fonction principale pour le DAG
def execute_daily_customer_tracking(**kwargs) -> Dict[str, Any]:
    """
    Fonction principale pour l'exécution du suivi quotidien des clients
    
    Args:
        **kwargs: Context Airflow
        
    Returns:
        dict: Résultats du traitement
    """
    try:
        execution_date = kwargs['execution_date']
        logger.info(f"Début du suivi quotidien des clients pour {execution_date}")
        
        # Traitement des métriques
        metrics = process_daily_customer_metrics(execution_date)
        
        # Génération du rapport
        report_path = generate_daily_customer_report(execution_date)
        
        result = {
            "status": "success",
            "execution_date": execution_date.strftime("%Y-%m-%d"),
            "metrics": metrics,
            "report_path": report_path
        }
        
        logger.info(f"Suivi quotidien terminé avec succès: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Erreur lors du suivi quotidien: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "execution_date": kwargs['execution_date'].strftime("%Y-%m-%d"),
            "error": error_msg
        }