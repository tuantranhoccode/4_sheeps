import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mticker

# =============================================================================
# 1. FINANCIAL WATERFALL CHART
# =============================================================================

def plot_financial_waterfall(df_orders):
    """
    Vẽ biểu đồ Waterfall phân tích dòng tiền từ Gross GMV đến Net Profit.
    """
    gross_gmv = df_orders["gross_gmv"].sum()
    total_discount = df_orders["discount_active"].sum()
    total_cancel = df_orders["cancel_val"].sum()
    total_refund = df_orders["refund_val"].sum()
    total_nmv = df_orders["nmv"].sum()
    total_cogs = df_orders["cogs_clean"].sum()
    total_shipping = df_orders["shipping_clean"].sum()
    total_profit = df_orders["profit"].sum()

    scale = 1e9  # Đơn vị: Tỷ VNĐ
    labels = [
        "<b>Gross GMV</b>", "Giảm giá<br>(Discount)", "Hủy hàng<br>(Cancellations)", "Hoàn tiền<br>(Refunds)", 
        "<b>NMV (Doanh thu thuần)</b>", "Giá vốn (COGS)", "Phí vận chuyển<br>(Shipping)", "<b>Lợi nhuận thuần</b>"
    ]

    v_gmv      = gross_gmv / scale
    v_discount = -total_discount / scale
    v_cancel   = -total_cancel / scale
    v_refund   = -total_refund / scale
    v_nmv      = total_nmv / scale
    v_cogs     = -total_cogs / scale
    v_ship     = -total_shipping / scale
    v_profit   = total_profit / scale

    values = [v_gmv, v_discount, v_cancel, v_refund, 0, v_cogs, v_ship, 0]
    measures = ["absolute", "relative", "relative", "relative", "total", "relative", "relative", "total"]

    bases = []
    bar_x = []
    current_total = 0

    for m, v in zip(measures, values):
        if m == "absolute":
            bases.append(0)
            bar_x.append(v)
            current_total = v
        elif m == "relative":
            bases.append(current_total)
            bar_x.append(v)
            current_total += v
        elif m == "total":
            bases.append(0)
            bar_x.append(current_total)

    bar_x_visual = []
    for v in bar_x:
        if v != 0 and abs(v) < 0.08: 
            bar_x_visual.append(-0.08 if v < 0 else 0.08)
        else:
            bar_x_visual.append(v)

    color_list = ["#1A73E8", "#E74C3C", "#E74C3C", "#E74C3C", "#1A73E8", "#F39C12", "#F39C12", "#1A73E8"]

    def smart_format(val, color):
        abs_val = abs(val)
        if abs_val >= 1e8: 
            txt = f"{val/1e9:.2f} Tỷ"
        else: 
            txt = f"{val/1e6:.2f} Triệu"
        return f"<span style='color:{color}'><b>{txt}</b></span>"

    display_text = [
        smart_format(gross_gmv, color_list[0]),
        smart_format(-total_discount, color_list[1]),
        smart_format(-total_cancel, color_list[2]),
        smart_format(-total_refund, color_list[3]),
        smart_format(total_nmv, color_list[4]),
        smart_format(-total_cogs, color_list[5]),
        smart_format(-total_shipping, color_list[6]),
        smart_format(total_profit, color_list[7])
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bar_x_visual, y=labels, base=bases, orientation='h',
        marker=dict(color=color_list, line=dict(color=color_list, width=2)),
        text=display_text, textposition='outside', cliponaxis=False, showlegend=False
    ))

    connector_x = []
    connector_y = []
    for i in range(len(labels) - 1):
        x_val = bases[i] + bar_x[i]
        connector_x.extend([x_val, x_val, None])
        connector_y.extend([labels[i], labels[i+1], None])

    fig.add_trace(go.Scatter(
        x=connector_x, y=connector_y, mode='lines',
        line=dict(color='#BDC3C7', width=1.5, dash='dot'),
        showlegend=False, hoverinfo='skip'
    ))

    legend_items = [
        ("Tăng giá trị", "#1A73E8"),
        ("Giảm do tổn thất vận hành & khuyến mãi", "#E74C3C"),
        ("Chi phí chính", "#F39C12")
    ]
    for name, color in legend_items:
        fig.add_trace(go.Bar(x=[None], y=[None], name=name, marker_color=color, showlegend=True))

    fig.update_layout(
        title = dict(
            text = "<b>DÒNG TIỀN: TỪ DOANH THU ĐẾN LỢI NHUẬN</b><br><i><span style='font-size:14px; color:#555555'>Chỉ ~12% GMV được giữ lại dưới dạng lợi nhuận do khuyến mãi và tổn thất vận hành làm suy giảm biên lợi nhuận</span></i>",
            x = 0.05, y = 0.95
        ),
        height = 650, width = 1100, template = "plotly_white",
        xaxis = dict(title="Giá trị (Tỷ VNĐ)", side="bottom", tickformat=".1f", gridcolor='whitesmoke', showline=True, linewidth=1, linecolor='black'),
        yaxis = dict(autorange="reversed", tickfont=dict(size=12)),
        legend = dict(orientation="h", x=0.5, xanchor="center", y=-0.15, yanchor="top", font=dict(size=13)),
        margin = dict(b=100, l=150, t=100)
    )
    return fig


# =============================================================================
# 2. GAUGE CHARTS (NET PROFIT & DISCOUNT RATIO)
# =============================================================================

def calculate_net_margin(total_profit, total_nmv):
    if total_nmv == 0: return 0
    return (total_profit / total_nmv * 100)

def calculate_gauge_needle_coordinates(value, max_range=25):
    angle = 180 - (value / max_range) * 180
    radius, base_width = 0.28, 0.02
    x_tip = 0.5 + radius * math.cos(math.radians(angle))
    y_tip = 0.35 + radius * math.sin(math.radians(angle))
    x_base1 = 0.5 + base_width * math.cos(math.radians(angle + 90))
    y_base1 = 0.35 + base_width * math.sin(math.radians(angle + 90))
    x_base2 = 0.5 + base_width * math.cos(math.radians(angle - 90))
    y_base2 = 0.35 + base_width * math.sin(math.radians(angle - 90))
    return x_tip, y_tip, x_base1, y_base1, x_base2, y_base2

def plot_net_margin_gauge(total_profit, total_nmv):
    """
    Vẽ biểu đồ Gauge hiển thị Net Profit Margin.
    """
    net_margin_pct = calculate_net_margin(total_profit, total_nmv)
    max_range = 25
    
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="gauge", value=0, domain={"x": [0, 1], "y": [0.1, 0.9]},
        gauge={
            "axis": {"range": [0, max_range], "tickvals": [0, 5, 10, 15, 20, 25], "tickfont": {"size": 15}},
            "bar": {"color": "rgba(0,0,0,0)", "thickness": 0},
            "steps": [
                {"range": [0, 10], "color": "#D9534F"},
                {"range": [10, 17], "color": "#FFD700"},
                {"range": [17, 25], "color": "#92D050"}
            ]
        }
    ))
    
    x_tip, y_tip, x_base1, y_base1, x_base2, y_base2 = calculate_gauge_needle_coordinates(net_margin_pct, max_range)
    fig.add_trace(go.Scatter(x=[x_base1, x_tip, x_base2, x_base1], y=[y_base1, y_tip, y_base2, y_base1], 
                             fill="toself", fillcolor="#555", mode="lines", showlegend=False))
    fig.add_trace(go.Scatter(x=[0.5], y=[0.35], marker=dict(color="#555", size=10), mode="markers", showlegend=False))
    
    fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=0.2, line=dict(width=0), fillcolor="#92D050")
    fig.add_annotation(x=0.5, y=0.1, text=f"{net_margin_pct:.1f} %", showarrow=False, 
                       font=dict(size=45, color="white", family="Arial Black"))
    
    fig.update_layout(title={"text": "Net Profit Margin", "x": 0.5, "y": 0.95}, height=500, width=600,
                      xaxis=dict(range=[0, 1], visible=False), yaxis=dict(range=[0, 1], visible=False))
    return fig

# Alias để tương thích ngược với code cũ
def plot_profit_margin_gauge(df_orders):
    return plot_net_margin_gauge(df_orders['profit'].sum(), df_orders['nmv'].sum())

def plot_discount_profit_gauge(total_discount, total_profit):
    """
    Vẽ biểu đồ Gauge hiển thị tỉ lệ Discount trên Net Profit.
    """
    discount_profit_pct = (total_discount / total_profit * 100) if total_profit != 0 else 0
    max_range = 60

    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="gauge", value=0, domain={'x': [0, 1], 'y': [0.1, 0.9]}, 
        gauge={
            'axis': {'range': [0, max_range], 'tickvals': [0, 20, 40, 60], 'tickfont': {'size': 15}},
            'bar': {'color': "rgba(0,0,0,0)", 'thickness': 0}, 
            'steps': [
                {'range': [0, 20], 'color': '#92D050'},
                {'range': [20, 40], 'color': '#FFD700'},
                {'range': [40, 60], 'color': '#D9534F'}
            ]
        }
    ))

    clamped_val = min(discount_profit_pct, max_range)
    x_tip, y_tip, x_base1, y_base1, x_base2, y_base2 = calculate_gauge_needle_coordinates(clamped_val, max_range)
    fig.add_trace(go.Scatter(x=[x_base1, x_tip, x_base2, x_base1], y=[y_base1, y_tip, y_base2, y_base1], 
                             fill="toself", fillcolor='#555', mode='lines', showlegend=False))
    fig.add_trace(go.Scatter(x=[0.5], y=[0.35], marker=dict(color='#555', size=10), mode='markers', showlegend=False))

    banner_color = '#92D050' if discount_profit_pct <= 20 else ('#FFD700' if discount_profit_pct <= 40 else '#D9534F')
    fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=0.2, line=dict(width=0), fillcolor=banner_color)
    fig.add_annotation(x=0.5, y=0.1, text=f"{discount_profit_pct:.1f} %", showarrow=False, 
                       font=dict(size=45, color="white", family="Arial Black"))

    fig.update_layout(title={'text': "Discount / Net Profit Ratio", 'x': 0.5, 'y': 0.95}, height=500, width=600,
                      xaxis=dict(range=[0, 1], visible=False), yaxis=dict(range=[0, 1], visible=False))
    return fig


# =============================================================================
# 3. TREND & SPARKLINE CHARTS
# =============================================================================

def plot_monthly_trend(monthly_data):
    """
    Vẽ biểu đồ xu hướng biến động NMV và Net Profit hàng tháng (Plotly High-Fidelity).
    """
    fig = go.Figure()

    # 1. NMV Line
    fig.add_trace(go.Scatter(
        x=monthly_data['month_str'], 
        y=monthly_data['nmv'],
        name='Doanh thu thuần (NMV)', 
        line=dict(color='#1A73E8', width=2.5),
        hovertemplate='NMV: %{y:,.0f} VNĐ'
    ))

    # 2. Profit Line
    fig.add_trace(go.Scatter(
        x=monthly_data['month_str'], 
        y=monthly_data['profit'],
        name='Lợi nhuận thuần (Net Profit)', 
        line=dict(color='#34A853', width=2.5),
        hovertemplate='Net Profit: %{y:,.0f} VNĐ'
    ))

    # 3. Baseline 0
    fig.add_hline(y=0, line_dash="dash", line_color="#FF4B4B", line_width=1.5)

    # 4. Professional Layout
    fig.update_layout(
        title={
            'text': "<b>XU HƯỚNG BIẾN ĐỘNG DOANH THU (NMV) & LỢI NHUẬN THUẦN HÀNG THÁNG</b><br><span style='font-size:13px; color:gray'>Dữ liệu từ 2012 - 2022 | Phân tích tương quan tăng trưởng và hiệu quả kinh doanh</span>",
            'x': 0.5, 'xanchor': 'center'
        },
        height=600, width=1600, template='plotly_white',
        hovermode='x unified',
        xaxis=dict(title="Giai đoạn (Tháng)", tickangle=45, nticks=60, gridcolor='whitesmoke'),
        yaxis=dict(title="Giá trị (VNĐ)", tickformat='s', gridcolor='whitesmoke'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=120)
    )
    return fig

def plot_monthly_losses(monthly_data):
    """
    Vẽ biểu đồ cột phân tích chi tiết các tháng có lợi nhuận thuần âm (Loss).
    """
    loss_only = monthly_data[monthly_data['profit'] < 0].copy()
    if loss_only.empty:
        print("📊 Không có tháng nào bị lỗ thuần.")
        return None
        
    min_loss = loss_only['profit'].min()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=loss_only['month_str'], 
        y=loss_only['profit'],
        marker_color='#D17A86',
        text=loss_only['profit'].apply(lambda x: f"{x/1e6:.1f}M" if abs(x)<1e9 else f"{x/1e9:.1f}B"),
        textposition="outside", textangle=-90, cliponaxis=False,
        textfont=dict(color='red', size=12, family="Arial Black"),
        name='Net Profit (Loss)',
        hovertemplate='Tháng: %{x}<br>Lỗ thuần: %{y:,.0f} VNĐ<extra></extra>'
    ))

    fig.update_layout(
        title="<b>DANH SÁCH CÁC THÁNG CÓ LỢI NHUẬN THUẦN (NET PROFIT) ÂM</b>",
        height=600, width=1600, template='plotly_white',
        xaxis=dict(title="Giai đoạn (Tháng)", type='category', tickangle=45),
        yaxis=dict(title="Net Profit (VNĐ)", tickformat='s', range=[min_loss * 1.4, 0]),
        margin=dict(t=100, b=180)
    )
    fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.3)
    
    return fig


def build_financial_metric_config(gross_gmv, total_discount, total_cancel, total_refund, total_nmv, total_cogs, total_shipping, total_profit):
    return [
        ("Gross GMV", "gross_gmv", "#17A2B8", gross_gmv),
        ("Giảm giá", "discount_active", "#FF6D01", total_discount),
        ("Hủy hàng", "cancel_val", "#FF6D01", total_cancel),
        ("Hoàn tiền", "refund_val", "#FF6D01", total_refund),
        ("NMV", "nmv", "#17A2B8", total_nmv),
        ("Giá vốn", "cogs_clean", "#FF6D01", total_cogs),
        ("Phí vận chuyển", "shipping_clean", "#FF6D01", total_shipping),
        ("Lợi nhuận thuần", "profit", "#17A2B8", total_profit)
    ]

def format_metric_total(value):
    if abs(value) >= 1e8: return f"{value/1e9:.2f}B"
    return f"{value/1e6:.1f}M"

def calculate_growth(curr, prev):
    return ((curr - prev) / prev * 100) if prev != 0 else 0

def plot_financial_sparklines(df_trend, gross_gmv, total_discount, total_cancel, total_refund, total_nmv, total_cogs, total_shipping, total_profit):
    metrics = build_financial_metric_config(gross_gmv, total_discount, total_cancel, total_refund, total_nmv, total_cogs, total_shipping, total_profit)
    fig = make_subplots(rows=2, cols=4, horizontal_spacing=0.08, vertical_spacing=0.4,
                        subplot_titles=[(f"<b>{m[0]}</b><br>{format_metric_total(m[3])}") for m in metrics])

    for i, (label, metric_col, highlight_color, total) in enumerate(metrics):
        row, col = (i // 4) + 1, (i % 4) + 1
        curr, prev = df_trend[metric_col].iloc[-1], df_trend[metric_col].iloc[-2]
        pct = calculate_growth(curr, prev)
        colors = (["#DCDCDC"] * (len(df_trend) - 1) + [highlight_color])
        
        fig.add_trace(go.Bar(x=df_trend["year"], y=df_trend[metric_col], marker_color=colors, showlegend=False), row=row, col=col)
        fig.add_annotation(text=f"<span style='color:{highlight_color if pct>=0 else '#EA4335'}; font-weight:bold'>{pct:+.1f}%</span>",
                           x=0.5, y=-0.5, xref="x domain", yref="y domain", showarrow=False, row=row, col=col)
        fig.update_xaxes(visible=False, row=row, col=col)
        fig.update_yaxes(visible=False, row=row, col=col)

    fig.update_layout(title="Historical Financial KPIs (2012-2022)", height=650, width=1150, template="plotly_white")
    return fig


# =============================================================================
# 4. EXECUTIVE MATPLOTLIB CHARTS (PRINT-READY)
# =============================================================================

def _format_y_axis(x, p):
    if abs(x) >= 1e9: return f'{x/1e9:,.2f}B'
    elif abs(x) >= 1e6: return f'{x/1e6:,.0f}M'
    elif x == 0: return '0'
    return f'{x:,.0f}'

def plot_yearly_financial_scale(yearly_df):
    """
    Biểu đồ quy mô các thành phần tài chính theo năm (Stacked Bar).
    """
    years = yearly_df['year'].astype(str)
    components = ['cogs_clean', 'shipping_clean', 'refund_val', 'cancel_val', 'discount_active', 'profit']
    labels = ['Giá vốn', 'Phí Ship', 'Hoàn tiền', 'Hủy hàng', 'Giảm giá', 'Lợi nhuận']
    colors = ['#23395B', '#406E8E', '#D1495B', '#8D99AE', '#EDAE49', '#30634D']

    plt.figure(figsize=(14, 7), facecolor='white', dpi=300)
    bottom = np.zeros(len(years))
    for i, col in enumerate(components):
        plt.bar(years, yearly_df[col], bottom=bottom, label=labels[i], color=colors[i], width=0.6, edgecolor='white', linewidth=0.5)
        bottom += yearly_df[col]

    plt.title('PHÂN TÍCH QUY MÔ CẤU TRÚC TÀI CHÍNH (VND)', fontsize=16, fontweight='bold', pad=25, color='#23395B')
    plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(_format_y_axis))
    plt.ylabel('Giá trị', fontsize=12, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False)
    sns.despine(left=True)
    plt.tight_layout()
    return plt.gcf()

def plot_yearly_financial_percentage(yearly_df):
    """
    Biểu đồ tỷ trọng % các thành phần trong Gross GMV.
    """
    years = yearly_df['year'].astype(str)
    components = ['cogs_clean', 'shipping_clean', 'refund_val', 'cancel_val', 'discount_active', 'profit']
    labels = ['Giá vốn', 'Phí Ship', 'Hoàn tiền', 'Hủy hàng', 'Giảm giá', 'Lợi nhuận']
    colors = ['#23395B', '#406E8E', '#D1495B', '#8D99AE', '#EDAE49', '#30634D']

    plt.figure(figsize=(14, 7), facecolor='white', dpi=300)
    bottom = np.zeros(len(years))
    for i, col in enumerate(components):
        pct = (yearly_df[col] / yearly_df['gross_gmv']) * 100
        plt.bar(years, pct, bottom=bottom, label=labels[i], color=colors[i], width=0.6, edgecolor='white', linewidth=0.5)
        for j, val in enumerate(pct):
            if val > 3: 
                plt.text(j, bottom[j] + val/2, f"{val:.1f}%", ha='center', va='center', 
                         color='white' if i in [0, 5] else '#2C3E50', fontsize=10, fontweight='bold')
        bottom += pct

    plt.title('TỶ TRỌNG % CÁC YẾU TỐ TRONG GIÁ NIÊM YẾT (GROSS GMV)', fontsize=16, fontweight='bold', pad=25, color='#23395B')
    plt.ylabel('Tỷ trọng (%)', fontsize=12, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False)
    plt.ylim(0, 105) 
    sns.despine(left=True)
    plt.tight_layout()
    return plt.gcf()

def plot_monthly_profit_volatility(df_orders):
    """
    Biểu đồ biến động lợi nhuận ròng hàng tháng (Xanh/Đỏ).
    """
    df_temp = df_orders.copy()
    df_temp['month_str'] = df_temp['order_date'].dt.strftime('%Y-%m')
    monthly_df = df_temp.groupby('month_str').agg({'profit': 'sum'}).reset_index().sort_values('month_str')
    
    temp_dates = pd.to_datetime(monthly_df['month_str'])
    monthly_df['date_label'] = temp_dates.dt.strftime('%b %Y')

    plt.figure(figsize=(24, 8), facecolor='white', dpi=300)
    colors_profit = np.where(monthly_df['profit'] >= 0, '#2E7D32', '#D32F2F')

    plt.bar(monthly_df['month_str'], monthly_df['profit'], color=colors_profit, alpha=1.0, width=0.7)
    plt.axhline(0, color='#333333', linewidth=1.5)
    
    xticks = np.arange(0, len(monthly_df), 3)
    plt.xticks(xticks, monthly_df['date_label'].iloc[xticks], rotation=45, ha='right', fontsize=14, fontweight='bold')
    plt.yticks(fontsize=16, fontweight='bold')
    plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(_format_y_axis))
    
    plt.title('PHÂN TÍCH BIẾN ĐỘNG LỢI NHUẬN THUẦN HÀNG THÁNG', fontsize=24, fontweight='bold', pad=45, color='#1A252F')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    sns.despine(left=True)
    plt.tight_layout()
    return plt.gcf()
