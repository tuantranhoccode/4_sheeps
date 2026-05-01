import pandas as pd
import numpy as np
from lifetimes import BetaGeoFitter, GammaGammaFitter
from lifetimes.utils import summary_data_from_transaction_data
from src.config.settings import SNAPSHOT_DATE, CODE_TO_SEGMENT, EXACT_PROFIT_MARGIN

def quintile_score(series: pd.Series, reverse: bool = False) -> pd.Series:
    """
    Divide series into 5 equal groups using ranking.
    """
    labels = [5, 4, 3, 2, 1] if reverse else [1, 2, 3, 4, 5]
    ranked_series = series.rank(method='first')
    return pd.qcut(ranked_series, q=5, labels=labels).astype(int)

def calculate_rfm_metrics(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate base R, F, M metrics for each customer.
    """
    df_valid = df_orders[~df_orders['is_cancelled']].copy()
    
    rfm_base = df_valid.groupby('customer_id').agg(
        Last_Order  = ('order_date', 'max'),
        First_Order = ('order_date', 'min'),
        Frequency   = ('order_id',   'count'),
        Monetary    = ('nmv',        'sum')
    ).reset_index()

    rfm_base['Recency'] = (SNAPSHOT_DATE - rfm_base['Last_Order']).dt.days
    
    # Filter out customers with zero or negative monetary value
    return rfm_base[rfm_base['Monetary'] > 0].copy()

def assign_segments(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign R, F, M scores and segments.
    """
    rfm_df['R_Score'] = quintile_score(rfm_df['Recency'],  reverse=True)
    rfm_df['F_Score'] = quintile_score(rfm_df['Frequency'], reverse=False)
    rfm_df['M_Score'] = quintile_score(rfm_df['Monetary'],  reverse=False)

    rfm_df['RFM_Code'] = (
        rfm_df['R_Score'].astype(str) +
        rfm_df['F_Score'].astype(str) +
        rfm_df['M_Score'].astype(str)
    )

    rfm_df['Segment'] = rfm_df['RFM_Code'].map(CODE_TO_SEGMENT).fillna('Potential Loyalist')
    
    # Calculate AOV and Tenure
    rfm_df['AOV'] = rfm_df['Monetary'] / rfm_df['Frequency']
    rfm_df['Tenure'] = np.maximum((SNAPSHOT_DATE - rfm_df['First_Order']).dt.days / 365.25, 0.1)
    rfm_df['Annual_Frequency'] = rfm_df['Frequency'] / rfm_df['Tenure']
    
    return rfm_df

def predict_clv_12m(df_orders: pd.DataFrame, rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict future 12-month value using BG/NBD and Gamma-Gamma models.
    """
    df_valid = df_orders[~df_orders['is_cancelled']].copy()
    
    rfm_predictive = summary_data_from_transaction_data(
        df_valid, 
        customer_id_col        = 'customer_id', 
        datetime_col           = 'order_date', 
        monetary_value_col     = 'nmv', 
        observation_period_end = SNAPSHOT_DATE
    )

    # Filter for customers with repeat purchases
    rfm_model = rfm_predictive[(rfm_predictive['frequency'] > 0) & (rfm_predictive['monetary_value'] > 0)].copy()

    if len(rfm_model) < 10:
        rfm_df['CLV'] = 0.0
        rfm_df['exp_purchases_12m'] = 0.0
        return rfm_df

    # Fit BG/NBD
    bgf = BetaGeoFitter(penalizer_coef=0.05)
    bgf.fit(rfm_model['frequency'], rfm_model['recency'], rfm_model['T'])

    # Fit Gamma-Gamma
    ggf = GammaGammaFitter(penalizer_coef=0.01)
    ggf.fit(rfm_model['frequency'], rfm_model['monetary_value'])

    # Predict 12m metrics
    rfm_model['pred_rev_12m'] = ggf.customer_lifetime_value(
        bgf, rfm_model['frequency'], rfm_model['recency'], rfm_model['T'], rfm_model['monetary_value'], 
        time=365, discount_rate=0.01, freq='D'
    )
    rfm_model['exp_purchases_12m'] = bgf.predict(365, rfm_model['frequency'], rfm_model['recency'], rfm_model['T'])
    rfm_model['pred_clv_12m'] = rfm_model['pred_rev_12m'] * EXACT_PROFIT_MARGIN

    # Merge back to main dataframe
    clv_results = rfm_model[['exp_purchases_12m', 'pred_rev_12m', 'pred_clv_12m']].reset_index()
    rfm_df = rfm_df.merge(clv_results, on='customer_id', how='left').fillna(0)
    
    # Rename to standardized names
    rfm_df = rfm_df.rename(columns={'pred_clv_12m': 'CLV', 'pred_rev_12m': 'Expected_Revenue'})
    
    return rfm_df

def add_behavioral_metrics(rfm_df: pd.DataFrame, reviews: pd.DataFrame, returns: pd.DataFrame, df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Integrate sentiment (reviews) and return rates.
    """
    # 1. Sentiment
    sentiment = reviews.groupby('customer_id').agg(Avg_Rating=('rating', 'mean'), Review_Count=('rating', 'count')).reset_index()
    
    # 2. Return Rate
    df_valid = df_orders[~df_orders['is_cancelled']].copy()
    returned_orders = returns[['order_id']].drop_duplicates()
    returned_orders['has_return'] = 1
    
    df_return_calc = df_valid[['order_id','customer_id']].merge(returned_orders, on='order_id', how='left').fillna({'has_return': 0})
    return_rate = df_return_calc.groupby('customer_id').agg(Return_Rate=('has_return', 'mean')).reset_index()
    
    # Merge
    rfm_df = rfm_df.merge(sentiment, on='customer_id', how='left')
    rfm_df = rfm_df.merge(return_rate, on='customer_id', how='left')
    
    # Fill NA (Bổ sung kiểm tra sự tồn tại của cột để tránh KeyError)
    if 'Avg_Rating' in rfm_df.columns:
        rfm_df['Avg_Rating'] = rfm_df['Avg_Rating'].fillna(rfm_df['Avg_Rating'].median() if not rfm_df['Avg_Rating'].isna().all() else 5.0)
    else:
        rfm_df['Avg_Rating'] = 5.0

    if 'Review_Count' in rfm_df.columns:
        rfm_df['Review_Count'] = rfm_df['Review_Count'].fillna(0)
    else:
        rfm_df['Review_Count'] = 0

    if 'Return_Rate' in rfm_df.columns:
        rfm_df['Return_Rate'] = rfm_df['Return_Rate'].fillna(0)
    else:
        rfm_df['Return_Rate'] = 0
    
    return rfm_df

def run_customer_pipeline(df_orders: pd.DataFrame, reviews: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    Full pipeline to generate the customer master table.
    """
    rfm = calculate_rfm_metrics(df_orders)
    rfm = assign_segments(rfm)
    rfm = predict_clv_12m(df_orders, rfm)
    rfm = add_behavioral_metrics(rfm, reviews, returns, df_orders)
    return rfm
