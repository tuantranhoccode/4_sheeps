import pandas as pd
import numpy as np

def calculate_acquisition_performance(rfm_df: pd.DataFrame, df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Analyzes acquisition channel performance based on customer CLV.
    """
    customer_first_touch = df_orders.sort_values('order_date').groupby('customer_id').first()['order_source'].reset_index()
    customer_first_touch.columns = ['customer_id', 'Acquisition_Channel']
    
    channel_data = rfm_df.merge(customer_first_touch, on='customer_id', how='left')
    
    channel_summary = channel_data.groupby('Acquisition_Channel').agg({
        'customer_id': 'count',
        'Monetary': 'mean',        
        'CLV': 'mean'     
    }).reset_index()
    
    # Loại bỏ các cột trùng tên nếu có (phòng trường hợp chạy lại nhiều lần)
    channel_summary = channel_summary.loc[:, ~channel_summary.columns.duplicated()]

    # Đổi tên một cách tường minh
    channel_summary.columns = ['Channel', 'Customer_Count', 'Avg_NMV_Historical', 'Avg_CL_12m']
    
    return channel_summary.sort_values('Avg_CL_12m', ascending=False)

def calculate_channel_performance(channel_summary, web_traffic, df_orders):
    """
    Tính toán hiệu suất chi tiết của kênh (Conversion Rate, Total CLV).
    """
    # 1. Traffic Aggregation
    df_traffic_agg = web_traffic.groupby('traffic_source').agg(
        Avg_Bounce_Rate=('bounce_rate', 'mean'),
        Avg_Session_Duration=('avg_session_duration_sec', 'mean')
    ).reset_index()

    # 2. Order Breakdown (Total, Success, Cancelled)
    order_stats = df_orders.groupby('order_source').agg(
        total_orders     = ('order_id', 'nunique'),
        success_orders   = ('is_cancelled', lambda x: (~x).sum()),
        cancelled_orders = ('is_cancelled', 'sum')
    ).reset_index()
    order_stats.columns = ['traffic_source', 'total_orders', 'success_orders', 'cancelled_orders']
    
    # 3. Sessions Breakdown
    channel_sessions = web_traffic.groupby('traffic_source')['sessions'].sum().reset_index()
    total_all_sessions = channel_sessions['sessions'].sum()
    channel_sessions['session_share_pct'] = (channel_sessions['sessions'] / total_all_sessions * 100)

    # 4. Merge và tính các tỷ lệ theo chuẩn của bạn
    df_conv = channel_sessions.merge(order_stats, on='traffic_source', how='left').fillna(0)
    
    # Conversion Rate (Đơn trên 1000 Sessions)
    df_conv['Avg_Conversion_Rate'] = (df_conv['success_orders'] / df_conv['sessions'].replace(0, 1)) * 1000
    
    # Tỷ lệ hủy đơn
    df_conv['cancel_rate_pct'] = (df_conv['cancelled_orders'] / df_conv['total_orders'].replace(0, 1)) * 100
    
    # Tỷ trọng đơn thành công trên tổng đơn thành công toàn sàn
    total_success_all = df_conv['success_orders'].sum()
    df_conv['success_share_pct'] = (df_conv['success_orders'] / (total_success_all if total_success_all != 0 else 1)) * 100

    df_traffic_agg = df_traffic_agg.merge(
        df_conv[['traffic_source', 'sessions', 'session_share_pct', 'total_orders', 'success_orders', 'cancelled_orders', 'Avg_Conversion_Rate', 'cancel_rate_pct', 'success_share_pct']], 
        on='traffic_source', 
        how='left'
    )

    # 5. Gộp với channel_summary
    channel_summary['Total_CLV_Predict'] = channel_summary['Customer_Count'] * channel_summary['Avg_CL_12m']
    
    df_plot = channel_summary.merge(df_traffic_agg, left_on='Channel', right_on='traffic_source', how='inner')
    return df_plot

def get_promotion_roadmap(df_promo):
    """
    Tạo bảng tổng hợp Roadmap các chiến dịch khuyến mãi.
    """
    import pandas as pd
    
    promo = df_promo.copy()
    
    # Đảm bảo cột ngày tháng chuẩn datetime
    promo['start_date'] = pd.to_datetime(promo['start_date'])
    promo['end_date'] = pd.to_datetime(promo['end_date'])
    
    # 1. Định dạng hiển thị Mức Giảm
    promo['Mức Giảm'] = promo.apply(
        lambda x: f"{x['discount_value']}%" if x['promo_type'] == 'percentage' else f"{x['discount_value']:,.0f} VNĐ", 
        axis=1
    )

    # 2. Tính thời lượng (Duration) và Giai đoạn
    promo['Số Ngày Chạy'] = (promo['end_date'] - promo['start_date']).dt.days + 1
    promo['Giai Đoạn'] = (
        promo['start_date'].dt.strftime('%m/%Y') + 
        " -> " + 
        promo['end_date'].dt.strftime('%m/%Y')
    )

    # 3. Sắp xếp và chọn cột
    roadmap = promo.sort_values('start_date', ascending=False)
    roadmap = roadmap[['promo_name', 'Mức Giảm', 'Giai Đoạn', 'Số Ngày Chạy']]
    roadmap.columns = ['Tên Chiến Dịch', 'Ưu Đãi', 'Giai Đoạn', 'Số Ngày Chạy']
    
    return roadmap

def calculate_promotion_calendar(df_promo, start_year=2013, end_year=2022):
    """
    Tạo ma trận lịch khuyến mãi theo Năm và Tháng.
    """
    import pandas as pd
    
    promo = df_promo.copy()
    promo['start_date'] = pd.to_datetime(promo['start_date'])
    promo['end_date'] = pd.to_datetime(promo['end_date'])
    
    years = range(start_year, end_year + 1)
    months = range(1, 13)
    data_list = []

    for y in years:
        row = {'Năm': y}
        for m in months:
            m_start = pd.Timestamp(year=y, month=m, day=1)
            m_end = m_start + pd.offsets.MonthEnd(0)
            
            # Tìm các KM hoạt động trong tháng này
            active = promo[(promo['start_date'] <= m_end) & (promo['end_date'] >= m_start)]
            
            if not active.empty:
                cell_text = ""
                for _, p in active.iterrows():
                    suffix = "%" if p['promo_type'] == 'percentage' else " fixed"
                    cell_text += f"{p['promo_name']}\n({p['discount_value']}{suffix})\n---\n"
                row[f"Tháng {m}"] = cell_text.strip("\n---")
            else:
                row[f"Tháng {m}"] = "-"
        data_list.append(row)

    return pd.DataFrame(data_list)

def calculate_roi_scenarios(rfm_df, budget=30000000):
    """
    Tính toán 3 kịch bản ROI (Bi quan, Cơ sở, Lạc quan) dựa trên 3 nhóm chiến lược.
    """
    # 1. Định nghĩa nhóm chiến lược
    strategy_map = {
        'Champions': 'Champions + Loyal Customers',
        'Loyal Customers': 'Champions + Loyal Customers',
        'Potential Loyalist': 'Potential Loyalist',
        'At Risk': 'At Risk + Customers Needing Attention',
        'Customers Needing Attention': 'At Risk + Customers Needing Attention'
    }
    
    df_strat = rfm_df[rfm_df['Segment'].isin(strategy_map.keys())].copy()
    df_strat['Target_Group'] = df_strat['Segment'].map(strategy_map)
    
    # 2. Tính Baseline
    baseline = df_strat.groupby('Target_Group').agg(
        So_khach=('customer_id', 'count'),
        Tong_CLV=('CLV', 'sum')
    ).reset_index()
    baseline['CLV_binh_quan'] = (baseline['Tong_CLV'] / baseline['So_khach'])

    # 3. Kịch bản
    scenarios = {
        'Bi quan':  {'impact': [0.03, 0.08, 0.12]}, # Thứ tự: Champions, Potential, At Risk
        'Cơ sở':    {'impact': [0.05, 0.15, 0.20]},
        'Lạc quan': {'impact': [0.08, 0.25, 0.30]}
    }
    
    results = []
    # Lưu ý: Cần đảm bảo thứ tự của impact khớp với thứ tự của baseline['Target_Group']
    # Sắp xếp baseline theo đúng thứ tự để nhân vector
    order = ['Champions + Loyal Customers', 'Potential Loyalist', 'At Risk + Customers Needing Attention']
    baseline['sort_order'] = baseline['Target_Group'].apply(lambda x: order.index(x))
    baseline = baseline.sort_values('sort_order').reset_index(drop=True)
    
    for name, cfg in scenarios.items():
        impact_rates = np.array(cfg['impact'])
        khach_ky_vong = (baseline['So_khach'] * impact_rates).sum()
        clv_ky_vong = (baseline['So_khach'] * impact_rates * baseline['CLV_binh_quan']).sum()
        net_benefit = clv_ky_vong - budget
        roi = (net_benefit / budget * 100)
        
        results.append({
            'Kịch bản': name,
            'Khách kỳ vọng tác động': khach_ky_vong,
            'Giá trị CLV kỳ vọng (VNĐ)': clv_ky_vong,
            'Chi phí bỏ ra (VNĐ)': budget,
            'Lợi ích ròng (VNĐ)': net_benefit,
            'ROI (%)': roi
        })
        
    return pd.DataFrame(results), baseline
