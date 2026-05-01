import numpy as np

def add_financial_features(df_orders):
    """
    Tính toán các chỉ số tài chính (NMV, Profit, etc.) cho bảng Order Master.
    """

    # =========================================
    # DATE FEATURES
    # =========================================
    df_orders["year"] = df_orders["order_date"].dt.year
    df_orders["month_num"] = df_orders["order_date"].dt.month

    # =========================================
    # ORDER STATUS FLAGS
    # =========================================
    df_orders["is_cancelled"] = df_orders["order_status"] == "cancelled"

    # =========================================
    # ACTIVE DISCOUNT
    # =========================================
    df_orders["discount_active"] = np.where(
        df_orders["is_cancelled"],
        0,
        df_orders["discount"]
    )

    # =========================================
    # CANCELLATION VALUE
    # =========================================
    df_orders["cancel_val"] = np.where(
        df_orders["is_cancelled"],
        df_orders["gross_gmv"],
        0
    )

    # =========================================
    # REFUND VALUE
    # =========================================
    df_orders["refund_val"] = np.where(
        df_orders["is_cancelled"],
        0,
        df_orders["refund_amount"]
    )

    # =========================================
    # NET MERCHANDISE VALUE
    # =========================================
    df_orders["nmv"] = (
        df_orders["gross_gmv"]
        - df_orders["discount_active"]
        - df_orders["cancel_val"]
        - df_orders["refund_val"]
    )

    # =========================================
    # CLEAN COGS
    # =========================================
    df_orders["cogs_clean"] = np.where(
        (df_orders["is_cancelled"]) | (df_orders["refund_val"] > 0),
        0,
        df_orders["total_cogs"]
    )

    # =========================================
    # CLEAN SHIPPING
    # =========================================
    df_orders["shipping_clean"] = np.where(
        df_orders["is_cancelled"],
        0,
        df_orders["shipping_fee"]
    )

    # =========================================
    # NET PROFIT
    # =========================================
    df_orders["profit"] = (
        df_orders["nmv"]
        - df_orders["cogs_clean"]
        - df_orders["shipping_clean"]
    )

    return df_orders
