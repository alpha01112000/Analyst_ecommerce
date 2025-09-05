import os
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

def enrich_data(date):
    product_path = os.path.join("data", "clean_data", "products", str(date.year), str(date.month), f"{str(date.day)}.csv")
    order_path = os.path.join("data", "clean_data", "orders", str(date.year), str(date.month), f"{str(date.day)}.csv")
    
    df_product = pd.read_csv(product_path)
    df_order = pd.read_csv(order_path)
    
    # Calculer la quantité commandée par produit
    order_qty = df_order.groupby(['product_id', 'order_date'])['quantity'].sum().reset_index()
    
    # Calculer le chiffre d'affaires par produit
    revenue = df_order.groupby(['product_id', 'order_date']).apply(
        lambda x: (x['quantity'] * x['price']).sum()
    ).reset_index(name='daily_revenue')
    
    # Calculer le nombre total de commandes par produit
    total_orders = df_order.groupby(['product_id', 'order_date'])['order_id'].nunique().reset_index(name='total_orders')
    
    # Fusionner avec le stock initial
    daily_stock = pd.merge(df_product, order_qty, how='left', on='product_id')
    daily_stock = pd.merge(daily_stock, revenue, how='left', on=['product_id', 'order_date'])
    daily_stock = pd.merge(daily_stock, total_orders, how='left', on=['product_id', 'order_date'])
    
    # Remplir les valeurs manquantes
    daily_stock['quantity'] = daily_stock['quantity'].fillna(0)
    daily_stock['daily_revenue'] = daily_stock['daily_revenue'].fillna(0)
    daily_stock['total_orders'] = daily_stock['total_orders'].fillna(0)
    
    # Calculer les métriques additionnelles
    daily_stock['remaining_stock'] = daily_stock['stock'] - daily_stock['quantity']
    daily_stock['stock_ratio'] = (daily_stock['remaining_stock'] / daily_stock['stock'] * 100).round(2)
    daily_stock['avg_price_per_unit'] = (daily_stock['daily_revenue'] / daily_stock['quantity']).replace([float("inf"), float("nan")], 0).round(2)
    daily_stock['date'] = date.strftime("%Y-%m-%d")
    
    # Contribution au chiffre d’affaires total
    total_revenue_day = daily_stock['daily_revenue'].sum()
    daily_stock['revenue_contribution'] = ((daily_stock['daily_revenue'] / total_revenue_day) * 100).round(2) if total_revenue_day > 0 else 0
    
    # Revenu cumulé par produit (jusqu’à la date)
    cumulative_revenue = df_order.groupby('product_id').apply(
        lambda x: (x['quantity'] * x['price']).sum()
    ).reset_index(name='cumulative_revenue')
    daily_stock = pd.merge(daily_stock, cumulative_revenue, how='left', on='product_id')
    
    # Stock turnover ratio (ventes / stock)
    daily_stock['stock_turnover_ratio'] = (daily_stock['quantity'] / daily_stock['stock']).replace([float("inf"), float("nan")], 0).round(2)
    
    # Ajouter des indicateurs d'alerte
    daily_stock['low_stock_alert'] = daily_stock['stock_ratio'] < 20
    daily_stock['out_of_stock_risk'] = daily_stock['remaining_stock'] <= 0
    daily_stock['high_demand_alert'] = daily_stock['revenue_contribution'] > 10  # produit majeur dans les ventes
    
    # Sélectionner les colonnes à exporter
    out = daily_stock[[
        'product_id', 'product_name', 'stock', 'quantity', 'remaining_stock',
        'stock_ratio', 'daily_revenue', 'avg_price_per_unit', 'total_orders',
        'revenue_contribution', 'cumulative_revenue', 'stock_turnover_ratio',
        'low_stock_alert', 'out_of_stock_risk', 'high_demand_alert', 'date'
    ]]
    
    out_path = os.path.join("data", "enrichi_data", "products", str(date.year), str(date.month), f"{str(date.day)}.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"Enriched daily stock saved to: {out_path}")

if __name__ == "__main__":
    from datetime import datetime
    date_to_process = datetime.strptime("2024-05-10", "%Y-%m-%d")
    enrich_data(date_to_process)

