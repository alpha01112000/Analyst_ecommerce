import os
import pandas as pd

def agg_data(date:str):

    product_path=os.path.join("data", "clean_data", "products", str(date.year), str(date.month), f"{str(date.day)}.csv")
    order_path=os.path.join("data", "clean_data", "orders", str(date.year), str(date.month), f"{str(date.day)}.csv")
    
    df_product= pd.read_csv(product_path)
    df_order=pd.read_csv(order_path)
    
    commande=df_order.groupby(['product_id'])['quantity'].sum().reset_index()
    stock_initial=df_product['stock']
    stock_journalier = pd.DataFrame({
        "date" : df_order['order_date'],
        "stock_journalier" :stock_initial - commande['quantity'],
        "product_id":commande['product_id']
    })
    
    out_path=os.path.join("data", "enrichi_data", "products", str(date.year), str(date.month), f"{str(date.day)}.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    stock_journalier.to_csv(out_path)

if __name__ == "__main__":
    from datetime import datetime
    # Exemple d'exécution pour la date du 3 juin 2024
    date_to_process = datetime.strptime("2024-05-10", "%Y-%m-%d")

    #clean_clients_data(date_to_process)
    #clean_products_data(date_to_process)
    agg_data(date_to_process)