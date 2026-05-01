import warnings
import pandas as pd
import numpy as np

# =========================================
# SYSTEM CONFIGURATION
# =========================================

# Tắt các cảnh báo không cần thiết
warnings.filterwarnings("ignore")

# Cấu hình hiển thị Pandas
pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

# Các hằng số quan trọng cho dự án
SNAPSHOT_DATE = pd.Timestamp("2022-12-31")
RANDOM_STATE = 42


# =========================================
# RFM SEGMENT CONFIGURATION
# =========================================

SEGMENT_ORDER = [
    "Champions",
    "Loyal Customers",
    "Potential Loyalist",
    "Recent Customers",
    "Promising",
    "Customers Needing Attention",
    "About To Sleep",
    "Can't Lose Them",
    "At Risk",
    "Hibernating",
    "Lost"
]


# =========================================
# RFM SEGMENT MAPPING (125 CODES)
# =========================================

SEGMENT_MAP = {
    'Champions': ['555','554','544','545','454','455','445'],
    'Loyal Customers': ['543','444','435','355','354','345','344','335'],
    'Potential Loyalist': [
        '553','551','552','541','542','533','532','531',
        '452','451','442','441','431','453','433','432',
        '423','353','352','351','342','341','333','323'
    ],
    'Recent Customers': ['512','511','422','421','412','411','311'],
    'Promising': [
        '525','524','523','522','521','515','514','513',
        '425','424','413','414','415','315','314','313'
    ],
    'Customers Needing Attention': ['535','534','443','434','343','334','325','324'],
    'About To Sleep': ['331','321','312','221','213'], 
    "Can't Lose Them": ['155','154','144','214','215','115','114','113'],
    'At Risk': [
        '255','254','245','244','253','252','243','242',
        '235','234','225','224','153','152','145','143',
        '142','135','134','133','125','124'
    ],
    'Hibernating': [
        '332','322','231','241','251','233','232','223','222','132','123','122','212','211'
    ],
    'Lost': ['111','112','121','131','141','151']
}

# Reverse mapping for O(1) lookup
CODE_TO_SEGMENT = {
    code: seg
    for seg, codes in SEGMENT_MAP.items()
    for code in codes
}


# =========================================
# FINANCIAL CONSTANTS FOR CLV
# =========================================

EXACT_PROFIT_MARGIN = 0.119838  # 11.9838% based on Waterfall (13.64B / 113.82B)
EXACT_CHURN_RATE = 0.05    # Estimated churn rate



# =========================================
# SEGMENT COLOR PALETTE
# =========================================

COLOR_MAP = {
    "Champions": "#4FFFB0",
    "Loyal Customers": "#5DB7FF",
    "Potential Loyalist": "#B580FF",
    "Recent Customers": "#33FFFF",
    "Promising": "#88B7AC",
    "Customers Needing Attention": "#FFFF66",
    "About To Sleep": "#A56B32",
    "Can't Lose Them": "#FF8B8B",
    "At Risk": "#FFAD55",
    "Hibernating": "#C0C0C0",
    "Lost": "#E0E0E0"
}


# =========================================
# RFM MATRIX BOUNDARIES
# =========================================

MATRIX_BOUNDS = {
    "Champions": {
        "x0": 4.5,
        "x1": 5.5,
        "y0": 3.5,
        "y1": 5.5
    },
    "Loyal Customers": {
        "x0": 2.5,
        "x1": 4.5,
        "y0": 3.5,
        "y1": 5.5
    },
    "Potential Loyalist": {
        "x0": 3.5,
        "x1": 5.5,
        "y0": 1.5,
        "y1": 3.5
    },
    "Recent Customers": {
        "x0": 4.5,
        "x1": 5.5,
        "y0": 0.5,
        "y1": 1.5
    },
    "Promising": {
        "x0": 3.5,
        "x1": 4.5,
        "y0": 0.5,
        "y1": 1.5
    },
    "Customers Needing Attention": {
        "x0": 2.5,
        "x1": 3.5,
        "y0": 0.5,
        "y1": 2.5
    },
    "About To Sleep": {
        "x0": 2.5,
        "x1": 3.5,
        "y0": 2.5,
        "y1": 3.5
    },
    "Can't Lose Them": {
        "x0": 0.5,
        "x1": 2.5,
        "y0": 4.5,
        "y1": 5.5
    },
    "At Risk": {
        "x0": 0.5,
        "x1": 2.5,
        "y0": 2.5,
        "y1": 4.5
    },
    "Hibernating": {
        "x0": 1.5,
        "x1": 2.5,
        "y0": 0.5,
        "y1": 2.5
    },
    "Lost": {
        "x0": 0.5,
        "x1": 1.5,
        "y0": 0.5,
        "y1": 2.5
    }
}

