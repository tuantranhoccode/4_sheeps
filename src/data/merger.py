import pandas as pd

def build_order_master(
    orders,
    order_items,
    products,
    returns,
    shipments
):
    """
    Hợp nhất các bảng dữ liệu thô để tạo bảng Order Master.
    """

    # =========================================
    # MERGE PRODUCT COST
    # =========================================
    oi = order_items.merge(
        products[["product_id", "cogs"]],
        on="product_id",
        how="left"
    )

    # =========================================
    # ITEM-LEVEL METRICS
    # =========================================
    oi["gross_item_val"] = oi["quantity"] * oi["unit_price"]
    oi["total_item_cogs"] = oi["quantity"] * oi["cogs"]

    # =========================================
    # ORDER-LEVEL AGGREGATION
    # =========================================
    order_agg = (
        oi.groupby("order_id")
        .agg(
            gross_gmv=("gross_item_val", "sum"),
            discount=("discount_amount", "sum"),
            total_cogs=("total_item_cogs", "sum")
        )
        .reset_index()
    )

    # =========================================
    # REFUND AGGREGATION
    # =========================================
    refund_agg = (
        returns.groupby("order_id")["refund_amount"]
        .sum()
        .reset_index()
    )

    # =========================================
    # SHIPPING AGGREGATION
    # =========================================
    shipping_agg = (
        shipments.groupby("order_id")["shipping_fee"]
        .sum()
        .reset_index()
    )

    # =========================================
    # BUILD ORDER MASTER
    # =========================================
    df_orders = (
        orders
        .merge(order_agg, on="order_id", how="left")
        .merge(refund_agg, on="order_id", how="left")
        .merge(shipping_agg, on="order_id", how="left")
    )

    # =========================================
    # HANDLE MISSING VALUES
    # =========================================
    df_orders = df_orders.fillna({
        "gross_gmv": 0,
        "discount": 0,
        "total_cogs": 0,
        "refund_amount": 0,
        "shipping_fee": 0
    })

    return df_orders
