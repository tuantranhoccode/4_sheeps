import pandas as pd
from pathlib import Path
from src.config.paths import RAW_DATA_DIR

def load_data(data_dir: Path = RAW_DATA_DIR):
    """
    Tải toàn bộ dữ liệu từ thư mục raw.
    data_dir: Path object trỏ đến thư mục chứa các file .csv (mặc định lấy từ config).
    """
    
    datasets = {
        "orders": pd.read_csv(
            data_dir / "orders.csv",
            parse_dates=["order_date"]
        ),

        "order_items": pd.read_csv(
            data_dir / "order_items.csv",
            low_memory=False
        ),

        "payments": pd.read_csv(
            data_dir / "payments.csv"
        ),

        "returns": pd.read_csv(
            data_dir / "returns.csv",
            parse_dates=["return_date"]
        ),

        "sales": pd.read_csv(
            data_dir / "sales.csv",
            parse_dates=["Date"]
        ),

        "shipments": pd.read_csv(
            data_dir / "shipments.csv"
        ),

        "products": pd.read_csv(
            data_dir / "products.csv"
        ),

        "reviews": pd.read_csv(
            data_dir / "reviews.csv"
        ),

        "customers": pd.read_csv(
            data_dir / "customers.csv"
        ),

        "geography": pd.read_csv(
            data_dir / "geography.csv"
        ),

        "inventory": pd.read_csv(
            data_dir / "inventory.csv"
        ),

        "promotions": pd.read_csv(
            data_dir / "promotions.csv"
        ),

        "web_traffic": pd.read_csv(
            data_dir / "web_traffic.csv"
        )
    }

    return datasets
