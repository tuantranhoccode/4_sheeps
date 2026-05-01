import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def plot_acquisition_efficiency(df_plot):
    """
    Vẽ biểu đồ phân tích hiệu quả thu hút khách hàng (Acquisition Efficiency).
    """
    import plotly.express as px
    
    fig = px.scatter(
        df_plot,
        x='sessions',
        y='Avg_Conversion_Rate',
        size='Total_CLV_Predict',
        color='Channel',
        hover_name='Channel',
        text='Channel',
        size_max=60,
        title='<b>MARKETING ACQUISITION EFFICIENCY: SESSIONS vs. CONVERSION RATE vs. CLV</b>',
        labels={
            'sessions': 'Tổng Sessions (Lưu lượng)',
            'Avg_Conversion_Rate': 'Tỷ lệ chuyển đổi (Đơn/1000 Sessions)',
            'Total_CLV_Predict': 'Tổng CLV Dự báo (12 Tháng)'
        }
    )
    
    fig.update_traces(textposition='top center')
    fig.update_layout(template='plotly_white', height=700)
    return fig

def plot_promotion_calendar(df_calendar):
    """
    Vẽ bảng tra cứu chiến dịch khuyến mãi chuyên nghiệp dưới dạng hình ảnh.
    """
    fig, ax = plt.subplots(figsize=(24, 12), facecolor='white') 
    ax.axis('off')

    # Ép bảng căng tràn khung hình
    table = ax.table(cellText=df_calendar.values, colLabels=df_calendar.columns, 
                     loc='center', cellLoc='center', bbox=[0, 0, 1, 1])

    table.auto_set_font_size(False)
    table.set_fontsize(8.5) 

    # Tô màu cho các ô
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#D5D8DC') 
        
        if row == 0: # Header
            cell.set_facecolor('#4285F4')
            cell.set_text_props(color='white', fontweight='bold', fontsize=10)
        elif col == 0: # Cột Năm
            cell.set_facecolor('#f1f3f4')
            cell.set_text_props(color='#333333', fontweight='bold', fontsize=9)
        else:
            if cell.get_text().get_text() != "-":
                cell.set_facecolor('#e8f0fe') 
                cell.set_text_props(color='#1967d2', fontweight='bold')
            else:
                cell.set_text_props(color='#BDC3C7')

    plt.title('BẢNG TRA CỨU CHI TIẾT CHIẾN DỊCH KHUYẾN MÃI (2013-2022)', 
              fontsize=22, fontweight='bold', color='#333333', pad=15)

    return fig


def plot_roi_scenarios(df_roi_summary):
    """
    Vẽ biểu đồ Bar chuyên nghiệp cho kịch bản ROI (Phiên bản in ấn).
    """
    import plotly.graph_objects as go
    fig = go.Figure()

    # Nhãn hiển thị kết hợp Lợi ích ròng + ROI %
    display_text = [
        f"<b>{row['Lợi ích ròng (VNĐ)']:,.0f} đ</b><br>ROI: {row['ROI (%)']:.2f}%" 
        for _, row in df_roi_summary.iterrows()
    ]

    # Bar cho Lợi ích ròng
    fig.add_trace(go.Bar(
        x=df_roi_summary['Kịch bản'],
        y=df_roi_summary['Lợi ích ròng (VNĐ)'],
        name='Lợi ích ròng (VND)',
        marker_color=['#E74C3C', '#F1C40F', '#2ECC71'],
        text=display_text,
        textposition='outside', # Đưa nhãn ra ngoài cột để dễ đọc
        cliponaxis=False
    ))

    fig.update_layout(
        title='<b>DỰ PHÓNG HIỆU QUẢ TÀI CHÍNH CHIẾN DỊCH (ROI)</b>',
        xaxis_title="Kịch bản",
        yaxis_title="Lợi ích ròng (VNĐ)",
        template='plotly_white', 
        height=600,
        showlegend=False,
        yaxis=dict(
            showgrid=True, 
            gridcolor='#EEEEEE',
            tickformat=',.0f'
        ),
        margin=dict(t=80, b=50, l=80, r=50) # Tăng lề để không bị mất chữ
    )
    
    return fig
