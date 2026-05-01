import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
import pandas as pd

def plot_yearly_gmv_analysis(summary_table):
    """
    Vẽ bộ đôi biểu đồ phân tích Gross GMV: Trung bình tháng và Tổng năm.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 14), facecolor='white')
    sns.set_style("white")

    # BIỂU ĐỒ 1: Trung bình doanh thu tháng
    max_avg = summary_table['Avg_Monthly_GMV'].max()
    colors_avg = ['#EA4335' if x == max_avg else '#4285F4' for x in summary_table['Avg_Monthly_GMV']]
    ax1.bar(summary_table['Year'].astype(str), summary_table['Avg_Monthly_GMV'], color=colors_avg, alpha=0.8)
    
    for i, v in enumerate(summary_table['Avg_Monthly_GMV']):
        ax1.text(i, v + (max_avg * 0.02), f'${v*1e-6:,.1f}M', ha='center', fontweight='bold')
    
    ax1.set_title('BIỂU ĐỒ 1: TRUNG BÌNH DOANH THU THÁNG THEO TỪNG NĂM', fontsize=14, fontweight='bold', pad=15)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x*1e-6:,.0f}M'))

    # BIỂU ĐỒ 2: Tổng doanh thu (Gross GMV)
    max_total = summary_table['Total_Yearly_GMV'].max()
    colors_total = ['#34A853' if x == max_total else '#FBBC04' for x in summary_table['Total_Yearly_GMV']]
    ax2.bar(summary_table['Year'].astype(str), summary_table['Total_Yearly_GMV'], color=colors_total, alpha=0.8)
    
    for i, v in enumerate(summary_table['Total_Yearly_GMV']):
        ax2.text(i, v + (max_total * 0.02), f'${v*1e-9:,.2f}B', ha='center', fontweight='bold')
        
    ax2.set_title('BIỂU ĐỒ 2: TỔNG DOANH THU (GROSS GMV) THEO TỪNG NĂM', fontsize=14, fontweight='bold', pad=15)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x*1e-9:,.1f}B'))
    ax2.set_ylabel('Tỷ VNĐ (Billion)')

    sns.despine()
    plt.tight_layout(pad=4.0)
    return fig

def plot_nmv_volatility_analysis(df_nmv_vol):
    """
    Vẽ biểu đồ biến động NMV hàng tháng với highlight các tháng đột biến.
    """
    # Đảm bảo có cột thời gian để vẽ trục X
    x_col = 'ym' if 'ym' in df_nmv_vol.columns else 'month_str'
    
    plt.figure(figsize=(22, 10), facecolor='white')
    sns.set_style("white")
    
    colors = ['#D93025' if high else '#AECBFA' for high in df_nmv_vol['is_high']]
    plt.bar(df_nmv_vol[x_col], df_nmv_vol['nmv'], color=colors, alpha=0.9, edgecolor='white', linewidth=0.3)

    # Cấu hình trục
    plt.xticks(range(0, len(df_nmv_vol), 3), df_nmv_vol[x_col][::3], rotation=45, fontsize=10)
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x*1e-6:,.0f} trđ'))
    
    plt.title('PHÂN TÍCH BIẾN ĐỘNG DOANH THU THỰC TẾ (NMV) HÀNG THÁNG (LỊCH SỬ)', 
              fontsize=22, fontweight='bold', color='#1A73E8', pad=40)
    plt.ylabel('Giá trị NMV (Triệu VNĐ)', fontsize=14)
    plt.xlabel('Tháng/Năm', fontsize=14)

    # Thêm vạch ngăn cách năm
    years = df_nmv_vol['year'].unique()
    for year in years:
        if year == years[0]: continue
        try:
            year_start = df_nmv_vol[df_nmv_vol['year'] == year].index[0]
            plt.axvline(year_start - 0.5, color='gray', linestyle='--', alpha=0.3)
            plt.text(year_start + 5.5, plt.ylim()[1] * 0.95, str(int(year)), 
                     weight='bold', alpha=0.5, ha='center', fontsize=14)
        except: continue

    sns.despine(left=True)
    plt.tight_layout()
    return plt.gcf()

def plot_profit_pressure_heatmap(profit_pivot, text_data):
    """
    Vẽ Heatmap lợi nhuận thuần và áp lực thất thoát theo năm/tháng.
    """
    import plotly.graph_objects as go
    fig = go.Figure(data=go.Heatmap(
        z=profit_pivot.values, 
        x=[f'T{m}' for m in range(1, 13)], 
        y=[str(y) for y in profit_pivot.index],
        text=text_data, texttemplate="%{text}", textfont=dict(size=9),
        colorscale='RdYlGn', zmid=0, xgap=2, ygap=2
    ))

    fig.update_layout(
        title="<b>HEATMAP: LỢI NHUẬN THUẦN & ÁP LỰC THẤT THOÁT (DISCOUNT + CANCEL / PROFIT)</b>",
        xaxis_title="Tháng", yaxis_title="Năm", yaxis=dict(autorange='reversed'),
        template='plotly_white', height=650
    )
    return fig
