import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
import pandas as pd

def plot_stockout_vs_nmv(inventory_df: pd.DataFrame, df_orders: pd.DataFrame):
    """
    Plots the correlation between stock-out days and NMV growth.
    """
    df_stockout_agg = inventory_df.groupby(['year', 'month'])['stockout_days'].sum().reset_index()
    df_stockout_agg['Time'] = df_stockout_agg.apply(lambda x: f"{int(x['year'])}-{int(x['month']):02d}", axis=1)
    
    monthly_nmv = (
        df_orders[~df_orders['is_cancelled']]
        .assign(Time = lambda x: x['order_date'].dt.to_period('M').astype(str))
        .groupby('Time')['nmv'].sum().reset_index()
    )

    df_merged = df_stockout_agg.merge(monthly_nmv, on='Time', how='left').fillna(0)

    fig, ax1 = plt.subplots(figsize=(20, 8))
    sns.set_style("white")
    
    # Stockout bars
    ax1.bar(df_merged['Time'], df_merged['stockout_days'], color='#BDC1C6', alpha=0.4, label='Stockout Days')
    ax1.set_ylabel('Stockout Days (SKU-Days)', fontsize=12, color='#D93025', fontweight='bold')
    
    # NMV line
    ax2 = ax1.twinx()
    ax2.plot(df_merged['Time'], df_merged['nmv'], color='#1A73E8', linewidth=2.5, marker='o', label='NMV')
    ax2.set_ylabel('NMV (VNĐ)', fontsize=12, color='#1A73E8', fontweight='bold')
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x*1e-6:,.0f}M'))

    plt.title('STOCK-OUT IMPACT ON REVENUE GROWTH (NMV)', fontsize=18, fontweight='bold', pad=20)
    ax1.set_xticklabels(df_merged['Time'], rotation=90, fontsize=8)
    plt.tight_layout()
    return fig

def plot_stockout_distribution(inventory_df: pd.DataFrame):
    """
    Plots a simple bar chart of stock-out days by month/year.
    """
    df_stockout_agg = inventory_df.groupby(['year', 'month'])['stockout_days'].sum().reset_index()
    df_stockout_agg['Time'] = df_stockout_agg.apply(lambda x: f"{int(x['year'])}-{int(x['month']):02d}", axis=1)
    
    plt.figure(figsize=(20, 6))
    plt.bar(df_stockout_agg['Time'], df_stockout_agg['stockout_days'], color='#4285F4')
    plt.xticks(rotation=90, fontsize=8)
    plt.title('MONTHLY STOCK-OUT TREND', fontsize=14, fontweight='bold')
    plt.tight_layout()
    return plt.gcf()
