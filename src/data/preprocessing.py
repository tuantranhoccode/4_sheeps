def build_legacy_order_view(df_orders):
    """
    Tạo một bản sao của df_orders với các tên cột cũ để đảm bảo 
    tính tương thích với các logic phân tích cũ (Backward Compatibility).
    """
    order_full = df_orders.copy()

    # =========================================
    # LEGACY COLUMN MAPPING
    # =========================================
    # Map gross_gmv sang revenue_item cho các cell cũ
    order_full["revenue_item"] = order_full["gross_gmv"]

    # =========================================
    # DATE FEATURES
    # =========================================
    order_full["year"] = order_full["order_date"].dt.year
    order_full["month_num"] = order_full["order_date"].dt.month
    order_full["month_period"] = order_full["order_date"].dt.to_period("M")

    return order_full

def enrich_orders_financials(df_orders, df_items, df_returns):
    """
    Làm giàu bảng orders bằng cách tính toán Profit, Discount và Cancel Value từ các bảng liên quan.
    """
    import pandas as pd
    from src.config.settings import EXACT_PROFIT_MARGIN

    # 1. Tính toán từ Order Items
    items_tmp = df_items.copy()
    items_tmp['item_gross'] = items_tmp['quantity'] * items_tmp['unit_price']
    
    order_metrics = items_tmp.groupby('order_id').agg(
        gross_gmv       = ('item_gross', 'sum'),
        discount_active = ('discount_amount', 'sum')
    ).reset_index()

    # 2. Merge vào Orders
    enriched = df_orders.merge(order_metrics, on='order_id', how='left').fillna(0)
    
    # 3. Tính NMV nếu chưa có
    if 'nmv' not in enriched.columns:
        # Giả sử bảng orders có sẵn các thành phần khác, nếu không ta tính từ Gross và Discount vừa merge
        enriched['nmv'] = enriched['gross_gmv'] - enriched['discount_active']

    # 4. Xử lý Trả hàng/Hủy hàng (Cancel Value)
    # Đảm bảo có cột is_cancelled
    if 'is_cancelled' not in enriched.columns:
        if 'order_status' in enriched.columns:
            enriched['is_cancelled'] = enriched['order_status'].isin(['cancelled', 'Cancelled', 'Hủy', 'Refused'])
        else:
            enriched['is_cancelled'] = False

    returns_tmp = df_returns[['order_id']].drop_duplicates()
    returns_tmp['is_returned'] = True
    enriched = enriched.merge(returns_tmp, on='order_id', how='left').fillna({'is_returned': False})
    
    # cancel_val = nmv nếu đơn bị hủy hoặc trả
    enriched['cancel_val'] = enriched.apply(lambda x: x['nmv'] if (x['is_cancelled'] or x['is_returned']) else 0, axis=1)
    
    # 5. Tính Profit (CHỈ TÍNH CHO ĐƠN THÀNH CÔNG)
    from src.config.settings import EXACT_PROFIT_MARGIN
    enriched['profit'] = enriched.apply(
        lambda x: x['nmv'] * EXACT_PROFIT_MARGIN if (not x['is_cancelled'] and not x['is_returned']) else 0, 
        axis=1
    )
        
    return enriched
        
    return enriched
