import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from matplotlib.patches import FancyBboxPatch
import pandas as pd
import numpy as np
from src.config.settings import COLOR_MAP, MATRIX_BOUNDS, SEGMENT_ORDER, EXACT_PROFIT_MARGIN, EXACT_CHURN_RATE

# =============================================================================
# 1. RFM MATRIX & DISTRIBUTION GRID
# =============================================================================


def plot_profit_contribution_highfi(rfm_df, df_orders):
    """
    Vẽ biểu đồ thanh ngang đóng góp lợi nhuận (High-Fidelity) với chú thích Top 2.
    """
    profit_by_seg = df_orders.merge(rfm_df[['customer_id', 'Segment']], on='customer_id', how='left')
    profit_dist = profit_by_seg.groupby('Segment')['profit'].sum().reset_index()
    total_profit = profit_dist['profit'].sum()
    profit_dist['Percentage'] = (profit_dist['profit'] / total_profit * 100).round(1)
    profit_dist = profit_dist.sort_values('Percentage', ascending=True)

    fig, ax = plt.subplots(figsize=(12, 10), facecolor='white')
    
    # Bo góc cho hình
    fancy = FancyBboxPatch((0.005, 0.005), 0.99, 0.99, boxstyle="round,pad=0", 
                            linewidth=1.5, edgecolor='#CCCCCC', facecolor='white',
                            transform=fig.transFigure, zorder=0)
    fig.add_artist(fancy)

    colors = [COLOR_MAP.get(s, '#BDC3C7') for s in profit_dist['Segment']]
    bars = ax.barh(profit_dist['Segment'], profit_dist['Percentage'], color=colors, alpha=0.9, height=0.6)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.8, bar.get_y() + bar.get_height()/2., f'{width}%', 
                ha='left', va='center', fontsize=10, fontweight='bold', color='#2C3E50')

    fig.text(0.5, 0.94, 'TỶ TRỌNG ĐÓNG GÓP LỢI NHUẬN (%) THEO PHÂN KHÚC KHÁCH HÀNG',
             ha='center', va='center', fontsize=14, fontweight='bold', color='white',
             bbox=dict(boxstyle='square,pad=0.6', facecolor='#1E3A5F', edgecolor='none'))

    # Annotate Top 2
    top2 = profit_dist.nlargest(2, 'Percentage')
    top2_total = top2['Percentage'].sum().round(1)
    box_x, box_y = 85, 9.5 

    ax.annotate('', xy=(top2.iloc[0]['Percentage'] + 10, 10), xytext=(box_x - 7, box_y + 0.3),
                arrowprops=dict(arrowstyle='->', color='#27AE60', lw=1.2, connectionstyle="arc3,rad=0.2"))
    ax.annotate('', xy=(top2.iloc[1]['Percentage'] + 10, 9), xytext=(box_x - 7, box_y - 0.3),
                arrowprops=dict(arrowstyle='->', color='#27AE60', lw=1.2, connectionstyle="arc3,rad=-0.2"))

    ax.text(box_x, box_y, f"Top 2 phân khúc\n\n\ntổng lợi nhuận", 
            ha='center', va='center', fontsize=10, color='#1E3A5F', fontweight='bold',
            bbox=dict(boxstyle='round,pad=1.0', facecolor='#E8F8F0', edgecolor='#27AE60', linewidth=1.2))
    ax.text(box_x, box_y, f"= {top2_total}%", ha='center', va='center', fontsize=15, color='#27AE60', fontweight='bold')

    sns.despine(ax=ax, left=True, bottom=True)
    ax.set_xlim(0, 105)
    plt.subplots_adjust(left=0.25, right=0.9, top=0.88, bottom=0.1)
    return fig

def plot_clv_bubble_chart(rfm_df, df_orders):
    """
    Vẽ biểu đồ bong bóng CLV tương quan giữa Tần suất (X) và AOV (Y).
    """
    # 1. Tính toán dữ liệu mức đơn hàng
    df_valid = df_orders[~df_orders['is_cancelled']].copy()
    aov_by_segment = (
        df_valid[['order_id', 'customer_id', 'nmv']]
        .merge(rfm_df[['customer_id', 'Segment']], on='customer_id')
        .groupby('Segment')['nmv']
        .mean()
        .reset_index()
        .rename(columns={'nmv': 'Avg_AOV'})
    )

    agg_data = rfm_df.groupby('Segment').agg(
        Customer_Count  = ('customer_id',      'count'),
        Avg_Frequency   = ('Annual_Frequency', 'mean'),
        Avg_CLV         = ('CLV',              'mean')
    ).reset_index()
    
    agg_data = agg_data.merge(aov_by_segment, on='Segment', how='left')
    agg_data['Percentage'] = (agg_data['Customer_Count'] / agg_data['Customer_Count'].sum() * 100).round(1)

    # 2. Vẽ biểu đồ
    fig = px.scatter(
        agg_data, x='Avg_Frequency', y='Avg_AOV', size='Avg_CLV', color='Segment',
        color_discrete_map=COLOR_MAP,
        custom_data=['Customer_Count', 'Percentage', 'Segment'],
        title=(
            '<b>CUSTOMER LIFETIME VALUE (CLV) BY SEGMENT</b><br>'
            '<i><span style="font-size:12px;color:gray">'
            'Kích thước bong bóng = CLV dự kiến | '
            f'Profit Margin = {EXACT_PROFIT_MARGIN*100:.2f}% | '
            f'Churn Rate = {EXACT_CHURN_RATE*100:.2f}%'
            '</span></i>'
        ),
        labels={'Avg_Frequency': 'Tần suất mua hàng TB (đơn/năm)', 'Avg_AOV': 'AOV ($)', 'Segment': 'Phân khúc'},
        size_max=70
    )

    fig.update_traces(
        hovertemplate=(
            '<b>Phân khúc: %{customdata[2]}</b><br>'
            'Annual Freq TB: %{x:.1f} đơn/năm<br>'
            'AOV TB: $%{y:,.0f}<br>'
            '<b>CLV dự kiến: $%{marker.size:,.0f}</b><br>'
            'Số KH: %{customdata[0]:,} (%{customdata[1]:.1f}%)<extra></extra>'
        ),
        marker=dict(line=dict(width=1.5, color='white'), opacity=0.85)
    )

    fig.update_layout(
        width=1100, height=660, plot_bgcolor='white', paper_bgcolor='white',
        showlegend=True,
        legend=dict(title="Phân khúc khách hàng", yanchor="top", y=0.99, xanchor="left", x=1.02, bgcolor="rgba(255,255,255,0.5)"),
        margin=dict(t=110, l=80, r=150, b=80), font=dict(family='Arial', size=13)
    )

    fig.update_xaxes(showgrid=True, gridcolor='#F0F0F0', zeroline=True, zerolinecolor='#D0D0D0')
    fig.update_yaxes(showgrid=True, gridcolor='#F0F0F0', zeroline=True, zerolinecolor='#D0D0D0', tickformat='$,.0f')
    
    return fig

def plot_clv_donut(rfm_df: pd.DataFrame):
    """
    Plots a donut chart of CLV distribution.
    """
    share = rfm_df.groupby('Segment')['CLV'].sum().reset_index()
    total = share['CLV'].sum()
    
    fig = go.Figure(data=[go.Pie(
        labels=share['Segment'], values=share['CLV'], hole=0.6,
        marker=dict(colors=[COLOR_MAP.get(s,'#AAA') for s in share['Segment']], line=dict(color='white', width=2))
    )])
    
    fig.update_layout(
        title='<b>TỶ TRỌNG ĐÓNG GÓP CLV THEO PHÂN KHÚC</b>',
        annotations=[dict(text=f'<b>TOTAL CLV</b><br>${total/1e9:.2f}B', showarrow=False, font_size=16)],
        showlegend=True, height=600, width=900
    )
    return fig

def plot_order_value_distribution(order_metrics):
    """
    Vẽ biểu đồ Box Plot phân phối giá trị đơn hàng theo phân khúc.
    """
    fig = px.box(
        order_metrics, 
        x='Segment', y='order_val', color='Segment',
        color_discrete_map=COLOR_MAP,
        title='<b>PHÂN PHỐI GIÁ TRỊ ĐƠN HÀNG (BOX PLOT)</b><br><span style="font-size:12px;color:gray">Dùng để nhận diện các đơn hàng "khủng" (outliers) trong từng nhóm</span>',
        category_orders={'Segment': SEGMENT_ORDER}
    )

    fig.update_layout(
        showlegend=False, plot_bgcolor='white', height=550, width=1050,
        yaxis=dict(title='Giá trị đơn hàng ($)', range=[0, order_metrics['order_val'].quantile(0.98)], gridcolor='#F0F0F0')
    )
    return fig

def plot_rfm_m_distribution_grid(rfm_df):
    """
    Vẽ lưới 5x5 hiển thị phân bổ điểm M cho mỗi cặp R và F.
    """
    fig, axes = plt.subplots(nrows=5, ncols=5, sharex=False, sharey=True, figsize=(14, 14))

    for r in range(1, 6):
        for f in range(1, 6):
            # Lọc dữ liệu cho ô (r, f)
            subset = rfm_df[(rfm_df['R_Score'] == r) & (rfm_df['F_Score'] == f)]
            y = subset['M_Score'].value_counts().sort_index()
            x = y.index
            
            ax = axes[r - 1, f - 1]
            bars = ax.bar(x, y, color='silver')
            
            # Highlight cột cao nhất
            if not y.empty:
                max_val = y.max()
                for bar in bars:
                    if bar.get_height() == max_val:
                        bar.set_color('firebrick')
                    
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height(),
                            int(bar.get_height()),
                            ha='center', va='bottom', color='k', fontsize=8)

            # Nhãn R và F
            if r == 5:
                if f == 3: ax.set_xlabel('{}\nF'.format(f), va='top', fontsize=12, fontweight='bold')
                else: ax.set_xlabel('{}\n'.format(f), va='top')
            if f == 1:
                if r == 3: ax.set_ylabel('R\n{}'.format(r), fontsize=12, fontweight='bold')
                else: ax.set_ylabel(r)
                
            ax.set_frame_on(False)
            ax.tick_params(left=False, labelleft=False, bottom=False)
            ax.set_xticks(x)
            ax.set_xticklabels(x, fontsize=8)

    fig.suptitle('Distribution of Monetary Score for each Frequency and Recency', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig

def plot_rfm_segment_matrix(rfm_df):
    """
    Vẽ ma trận phân bổ phân khúc RFM (Plotly) với khung tiêu đề và chú giải chuyên nghiệp.
    """
    total_customers = len(rfm_df)
    agg_data = rfm_df.groupby('Segment').agg(count=('customer_id', 'count')).reset_index()
    agg_data['pct'] = (agg_data['count'] / total_customers * 100).round(1)

    fig = go.Figure()

    # 1. Vẽ các ô vuông ma trận
    for seg, b in MATRIX_BOUNDS.items():
        color = COLOR_MAP.get(seg, '#AAAAAA')
        fig.add_shape(
            type='rect', x0=b['x0'], x1=b['x1'], y0=b['y0'], y1=b['y1'],
            fillcolor=color, line=dict(color='white', width=2), layer='below'
        )
        
        row = agg_data[agg_data['Segment'] == seg]
        if not row.empty:
            fig.add_annotation(
                x=(b['x0']+b['x1'])/2, y=(b['y0']+b['y1'])/2,
                text=f"<b>{row.pct.values[0]}%</b><br><span style='font-size:11px; color:rgba(0,0,0,0.7)'>{row['count'].values[0]:,} KH</span>",
                font=dict(size=20, color='black'), showarrow=False
            )

    # 2. Chú giải (Legend)
    for seg in SEGMENT_ORDER:
        if seg in COLOR_MAP:
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers',
                marker=dict(size=12, color=COLOR_MAP[seg], symbol='square'), name=seg
            ))

    # 3. Khung và Tiêu đề
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
        x0=-0.16, x1=1.42, y0=-0.18, y1=1.22,
        line=dict(color="#CCCCCC", width=1.5), fillcolor="white", layer="below"
    )

    fig.add_annotation(
        xref='paper', yref='paper', x=0.0, y=1.08, 
        xanchor='left', yanchor='bottom', showarrow=False,
        text="&nbsp;<b>2. MA TRẬN PHÂN BỔ PHÂN KHÚC RFM</b>&nbsp;",
        font=dict(color='white', size=14),
        bgcolor='#1E3A5F', bordercolor='#1E3A5F', borderwidth=2, borderpad=8
    )

    fig.add_annotation(
        xref='paper', yref='paper', x=1.0, y=1.08, 
        xanchor='right', yanchor='bottom', showarrow=False, align='right',
        text=(f"<b style='font-size:28px; color:#1E293B'>{total_customers:,}</b><br>"
              f"<span style='font-size:10px; color:#64748b; letter-spacing: 1px;'>TỔNG KHÁCH HÀNG</span>")
    )

    # 4. Cấu hình trục
    axis_cfg = dict(
        tickvals=[1,2,3,4,5], range=[0.5, 5.5], 
        showgrid=False, mirror=True, linecolor='#CCCCCC', 
        tickfont=dict(size=13), zeroline=False
    )
    fig.update_xaxes(title='<b>Recency Score →</b>', **axis_cfg)
    fig.update_yaxes(title='<b>← Frequency + Monetary Score</b>', **axis_cfg)

    fig.update_layout(
        width=1000, height=750, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=120, l=100, r=280, b=100), 
        legend=dict(y=0.5, x=1.02, borderwidth=1, bordercolor="#CCCCCC", font=dict(size=10), bgcolor='white')
    )
    
    return fig

def plot_clv_contribution_highfi(rfm_df):
    """
    Vẽ biểu đồ thanh ngang đóng góp CLV dự kiến (High-Fidelity) với chú thích Top 2.
    """
    clv_dist = rfm_df.groupby('Segment').agg(
        So_KH=('customer_id', 'count'),
        CLV_TB=('CLV', 'mean') 
    ).reset_index()

    clv_dist['CLV_du_kien'] = clv_dist['So_KH'] * clv_dist['CLV_TB']
    total_clv = clv_dist['CLV_du_kien'].sum()
    clv_dist['Percentage'] = (clv_dist['CLV_du_kien'] / total_clv * 100).round(1)
    clv_dist = clv_dist.sort_values('Percentage', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')
    
    # Bo góc cho hình
    fancy = FancyBboxPatch((0.005, 0.005), 0.99, 0.99, boxstyle="round,pad=0", 
                            linewidth=1.5, edgecolor='#CCCCCC', facecolor='white',
                            transform=fig.transFigure, zorder=0)
    fig.add_artist(fancy)

    colors = [COLOR_MAP.get(s, '#BDC3C7') for s in clv_dist['Segment']]
    bars = ax.barh(clv_dist['Segment'], clv_dist['Percentage'], color=colors, alpha=0.9, height=0.6)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.8, bar.get_y() + bar.get_height()/2., f'{width}%', 
                ha='left', va='center', fontsize=10, fontweight='bold', color='#2C3E50')

    fig.text(0.5, 0.92, '    1. TỶ TRỌNG ĐÓNG GÓP CLV DỰ KIẾN (%) THEO PHÂN KHÚC KHÁCH HÀNG    ',
             ha='center', va='center', fontsize=13, fontweight='bold', color='white',
             bbox=dict(boxstyle='square,pad=0.6', facecolor='#1E3A5F', edgecolor='none'))

    ax.set_xlabel('Tỷ trọng CLV dự kiến (%)', fontsize=11)
    ax.set_xlim(0, 125) 

    # Annotate Top 2
    top2 = clv_dist.nlargest(2, 'Percentage')
    top2_total = top2['Percentage'].sum().round(1)
    box_x, box_y = 105, 9.5 

    ax.annotate('', xy=(top2.iloc[0]['Percentage'] + 12, 10), xytext=(box_x - 7, box_y + 0.3),
                arrowprops=dict(arrowstyle='->', color='#27AE60', lw=1.2, connectionstyle="arc3,rad=0.2"))
    ax.annotate('', xy=(top2.iloc[1]['Percentage'] + 12, 9), xytext=(box_x - 7, box_y - 0.3),
                arrowprops=dict(arrowstyle='->', color='#27AE60', lw=1.2, connectionstyle="arc3,rad=-0.2"))

    ax.text(box_x, box_y, f"Top 2 phân khúc\n\n\ntổng CLV dự kiến", 
            ha='center', va='center', fontsize=10, color='#1E3A5F', fontweight='bold',
            bbox=dict(boxstyle='round,pad=1.0', facecolor='#E8F8F0', edgecolor='#27AE60', linewidth=1.2))
    ax.text(box_x, box_y, f"= {top2_total}%", ha='center', va='center', fontsize=15, color='#27AE60', fontweight='bold')

    sns.despine(ax=ax, left=True, bottom=True)
    ax.grid(axis='x', linestyle='--', alpha=0.2)
    plt.subplots_adjust(left=0.3, right=0.9, top=0.8, bottom=0.1)
    return fig
