def calculate_monthly_kpis(df_orders):
    """
    Tổng hợp dữ liệu theo tháng để tính toán các chỉ số KPI chính (NMV, Profit).
    """
    monthly_df = df_orders.copy()

    # Tạo cột tháng dạng chuỗi (YYYY-MM) để group
    monthly_df["month_str"] = (
        monthly_df["order_date"]
        .dt.to_period("M")
        .astype(str)
    )

    # Aggregation
    monthly_kpis = (
        monthly_df
        .groupby("month_str")
        .agg({
            "nmv": "sum",
            "profit": "sum"
        })
        .reset_index()
    )

    return monthly_kpis



def calculate_yearly_financial_metrics(df_orders):
    """
    Tổng hợp dữ liệu theo năm để tính toán các chỉ số tài chính (Historical Trends).
    """
    yearly_metrics = (
        df_orders
        .groupby("year")
        .agg({
            "gross_gmv": "sum",
            "discount_active": "sum",
            "cancel_val": "sum",
            "refund_val": "sum",
            "nmv": "sum",
            "cogs_clean": "sum",
            "shipping_clean": "sum",
            "profit": "sum"
        })
        .reset_index()
    )

    return yearly_metrics
