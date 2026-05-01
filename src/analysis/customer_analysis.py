import pandas as pd
from src.config.settings import SEGMENT_ORDER


def get_rfm_summary_table(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bảng tổng hợp RFM chi tiết theo phân khúc, có hàng TỔNG CỘNG.
    """
    # 1. Tính toán bảng tổng hợp
    summary = rfm_df.groupby('Segment').agg({
        'customer_id': 'count',
        'Recency': 'sum',
        'Frequency': 'sum',
        'Monetary': 'sum'
    }).reset_index()

    # 2. Sắp xếp theo thứ tự chiến lược
    summary['_order'] = summary['Segment'].map({s: i for i, s in enumerate(SEGMENT_ORDER)})
    summary = summary.sort_values('_order').drop(columns='_order')

    # 3. Tính hàng TỔNG CỘNG
    grand_total = pd.DataFrame({
        'Segment': ['TỔNG CỘNG'],
        'customer_id': [summary['customer_id'].sum()],
        'Recency': [summary['Recency'].sum()],
        'Frequency': [summary['Frequency'].sum()],
        'Monetary': [summary['Monetary'].sum()]
    })

    # 4. Gộp và đổi tên
    final_table = pd.concat([summary, grand_total], ignore_index=True)
    final_table.columns = [
        'Phân Khúc', 'Số KH',
        'TỔNG RECENCY (Ngày)', 'TỔNG FREQUENCY (Đơn)', 'TỔNG MONETARY (Đồng)'
    ]
    
    return final_table

def get_df_line_detail(df_orders, order_items, products, rfm_df):
    """
    Tạo bảng dữ liệu chi tiết đến từng dòng hàng (line item) kèm thông tin phân khúc.
    """
    df_valid = df_orders[~df_orders['is_cancelled']].copy()
    order_items_rich = order_items.copy()
    order_items_rich['gross_item_val'] = order_items_rich['quantity'] * order_items_rich['unit_price']
    
    df_line_detail = (
        df_valid[['order_id', 'customer_id', 'order_date', 'nmv']]
        .merge(order_items_rich[['order_id', 'product_id', 'quantity', 'unit_price', 'gross_item_val']], on='order_id')
        .merge(products[['product_id', 'category']], on='product_id', how='left')
        .merge(rfm_df[['customer_id', 'Segment']], on='customer_id')
    )
    return df_line_detail

def get_behavioral_summary(df_line_detail, big_order_threshold=50000):
    """
    Tính toán bảng tổng quan hành vi mua sắm (AOV, Items per Order, Big Order %).
    """
    order_metrics = df_line_detail.groupby(['order_id', 'Segment']).agg(
        order_val  = ('nmv',        'first'), 
        item_qty   = ('quantity',   'sum'),
        unique_pds = ('product_id', 'nunique')
    ).reset_index()

    behavior_summary = order_metrics.groupby('Segment').agg(
        Total_Orders    = ('order_id',   'count'),
        Avg_AOV         = ('order_val',  'mean'),  
        Median_AOV      = ('order_val',  'median'), 
        Items_per_Order = ('item_qty',   'mean'),
        Prod_per_Order  = ('unique_pds', 'mean')
    ).reset_index()

    big_orders_count = order_metrics[order_metrics['order_val'] >= big_order_threshold].groupby('Segment').size()
    behavior_summary['Big_Order_%'] = behavior_summary['Segment'].map(big_orders_count).fillna(0)
    behavior_summary['Big_Order_%'] = (behavior_summary['Big_Order_%'] / behavior_summary['Total_Orders'] * 100).round(1)

    # Sort
    behavior_summary['_order'] = behavior_summary['Segment'].map({s: i for i, s in enumerate(SEGMENT_ORDER)})
    behavior_summary = behavior_summary.sort_values('_order').drop(columns='_order')
    
    return behavior_summary, order_metrics

def get_top_categories(df_line_detail, top_n=3):
    """
    Lấy Top N danh mục sản phẩm ưa thích của từng phân khúc.
    """
    cat_revenue = df_line_detail.groupby(['Segment', 'category'])['gross_item_val'].sum().reset_index()
    cat_revenue['Rank'] = cat_revenue.groupby('Segment')['gross_item_val'].rank(ascending=False, method='dense')
    top_cat = cat_revenue[cat_revenue['Rank'] <= top_n].sort_values(['Segment', 'Rank'])
    
    # Pivot for clean display
    pivot_top = top_cat.pivot(index='Segment', columns='Rank', values='category')
    return pivot_top.loc[SEGMENT_ORDER]

def generate_behavioral_insights(behavior_summary):
    """
    Sinh các kết luận chiến lược tự động dựa trên bảng hành vi.
    """
    insights = []
    for seg in ['Champions', 'Loyal Customers', "Can't Lose Them"]:
        if seg not in behavior_summary['Segment'].values: continue
        row = behavior_summary[behavior_summary['Segment'] == seg].iloc[0]
        avg, med, big_pct = row['Avg_AOV'], row['Median_AOV'], row['Big_Order_%']
        
        pattern = "Mua đơn lớn giá trị cao" if big_pct > 25 else "Mua sắm đều đặn mức trung bình"
        if med < avg * 0.5: pattern = "Bị ảnh hưởng bởi một vài đơn hàng cực lớn (Skewed)"
        
        insights.append(f"  - [{seg:20}]: AOV=${avg:,.0f} | %Đơn lớn={big_pct:>4}% -> {pattern}")
    insights.append(f"  - [{seg:20}]: AOV=${avg:,.0f} | %Đơn lớn={big_pct:>4}% -> {pattern}")
    return insights

def get_strategic_dashboard(rfm_df, df_orders):
    """
    Tạo Dashboard chiến lược 11 phân khúc kết hợp RFM, CLV và Sentiment.
    """
    # 1. Tính AOV mức đơn hàng (Order-level)
    df_valid = df_orders[~df_orders['is_cancelled']].copy()
    aov_by_segment = (
        df_valid[['order_id', 'customer_id', 'nmv']]
        .merge(rfm_df[['customer_id', 'Segment']], on='customer_id')
        .groupby('Segment')['nmv']
        .mean()
        .reset_index()
        .rename(columns={'nmv': 'Avg_AOV'})
    )

    # 2. Chuẩn bị bảng RFM phụ để tính tỷ lệ review
    rfm_temp = rfm_df.copy()
    rfm_temp['Has_Review'] = (rfm_temp['Review_Count'] > 0).astype(int)

    # 3. Aggregation chính
    dashboard = rfm_temp.groupby('Segment').agg(
        Customer_Count = ('customer_id',      'count'),
        Avg_Recency    = ('Recency',          'mean'),
        Avg_Frequency  = ('Frequency',        'mean'),
        Avg_Mon        = ('Monetary',         'mean'),   
        Avg_CLV        = ('CLV',              'mean'),   
        Total_CLV      = ('CLV',              'sum'),
        Avg_Rating     = ('Avg_Rating',       'mean'),   
        Review_Rate    = ('Has_Review',       'mean'),
        Avg_ReturnRate = ('Return_Rate',      'mean'),   
    ).reset_index()

    # 4. Merge và tính các chỉ số %
    dashboard = dashboard.merge(aov_by_segment, on='Segment', how='left')
    
    total_customers = dashboard['Customer_Count'].sum()
    total_clv = dashboard['Total_CLV'].sum()
    
    dashboard['Share_%']      = (dashboard['Customer_Count'] / total_customers * 100).round(1)
    dashboard['CLV_Share_%']  = (dashboard['Total_CLV'] / (total_clv if total_clv != 0 else 1) * 100).round(1)
    dashboard['Review_Rate_%']= (dashboard['Review_Rate'] * 100).round(1)

    # 5. Sắp xếp và format cột
    dashboard['_order'] = dashboard['Segment'].map({s: i for i, s in enumerate(SEGMENT_ORDER)})
    dashboard = dashboard.sort_values('_order').drop(columns='_order').reset_index(drop=True)

    dashboard_display = dashboard[[
        'Segment','Customer_Count','Share_%',
        'Avg_Recency','Avg_Frequency','Avg_Mon','Avg_AOV','Avg_CLV',
        'Avg_Rating', 'Review_Rate_%', 'Avg_ReturnRate','CLV_Share_%'
    ]].copy()

    dashboard_display.columns = [
        'Phân Khúc','Số KH','% KH',
        'Recency TB (ngày)','Freq TB','Mon TB','AOV TB','CLV TB',
        'Rating TB', 'Tỷ lệ Review', 'Return Rate','% CLV'
    ]
    
    return dashboard_display

def perform_data_integrity_audit(df_orders, rfm_df):
    """
    Thực hiện kiểm kê tính toàn vẹn của dữ liệu sau khi xử lý RFM.
    """
    # 1. Tính toán NMV
    total_net_nmv = df_orders[~df_orders['is_cancelled']]['nmv'].sum()
    valid_rfm_nmv = rfm_df['Monetary'].sum()
    excluded_nmv  = total_net_nmv - valid_rfm_nmv
    
    # 2. Tính tỷ lệ % thất thoát
    loss_pct = (excluded_nmv / (total_net_nmv if total_net_nmv != 0 else 1) * 100)
    
    # 3. Chuẩn bị kết quả
    audit_results = {
        'Total_Net_NMV': total_net_nmv,
        'RFM_Included_NMV': valid_rfm_nmv,
        'Excluded_NMV': excluded_nmv,
        'Loss_Pct': loss_pct,
        'Status': '✅ PASS' if loss_pct < 0.1 else '⚠️ WARNING'
    }
    
    # In báo cáo nhanh
    print("="*50)
    print(f"AUDIT: TÍNH TOÀN VẸN CỦA DỮ LIỆU RFM")
    print("="*50)
    print(f"Tổng NMV (Đơn không hủy): {total_net_nmv:,.0f} VND")
    print(f"Tổng NMV (Đưa vào RFM)  : {valid_rfm_nmv:,.0f} VND")
    print(f"NMV bị loại (NMV <= 0) : {excluded_nmv:,.0f} VND")
    print(f"Tỷ lệ dữ liệu bị loại  : {loss_pct:.4f}%")
    print(f"Kết luận                : {audit_results['Status']}")
    print("="*50)
    
    return audit_results
