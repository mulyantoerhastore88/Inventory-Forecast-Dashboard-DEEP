import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from dateutil.relativedelta import relativedelta
import warnings
from tenacity import retry, stop_after_attempt, wait_exponential
import math
warnings.filterwarnings('ignore')

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Inventory Intelligence Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS Premium ---
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        text-align: center;
        padding: 1rem;
        border-bottom: 3px solid linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .status-indicator {
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .status-indicator:hover {
        transform: translateY(-5px);
    }
    .status-under { 
        background: linear-gradient(135deg, #FF5252 0%, #FF1744 100%);
        color: white;
        border-left: 5px solid #D32F2F;
    }
    .status-accurate { 
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        border-left: 5px solid #1B5E20;
    }
    .status-over { 
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        border-left: 5px solid #E65100;
    }
    
    .inventory-card {
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .inventory-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    .card-replenish { 
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        color: #EF6C00;
        border: 2px solid #FF9800;
    }
    .card-ideal { 
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        color: #2E7D32;
        border: 2px solid #4CAF50;
    }
    .card-high { 
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        color: #C62828;
        border: 2px solid #F44336;
    }
    
    .metric-highlight {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
        border-top: 5px solid #667eea;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 10px 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 1rem;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: 2px solid #5a67d8 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .sankey-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* New CSS */
    .monthly-performance-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid;
    }
    
    .performance-under { border-left-color: #F44336; }
    .performance-accurate { border-left-color: #4CAF50; }
    .performance-over { border-left-color: #FF9800; }
    
    .highlight-row {
        background-color: #FFF9C4 !important;
        font-weight: bold !important;
    }
    
    .warning-badge {
        background: #FF5252;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .success-badge {
        background: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Compact metrics */
    .compact-metric {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
    }
    
    /* Brand performance */
    .brand-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-top: 4px solid #667eea;
    }
    
    /* Financial cards */
    .financial-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 4px solid;
        transition: all 0.3s ease;
    }
    .financial-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .card-revenue { border-top-color: #667eea; }
    .card-margin { border-top-color: #4CAF50; }
    .card-cost { border-top-color: #FF9800; }
    .card-inventory { border-top-color: #9C27B0; }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #0E1117;
            color: #FFFFFF;
        }
        .financial-card, .brand-card, .compact-metric {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
    }
    
    /* Progress bar animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# --- Judul Dashboard ---
st.markdown('<h1 class="main-header">💰 INVENTORY INTELLIGENCE PRO DASHBOARD</h1>', unsafe_allow_html=True)
st.caption(f"🚀 Professional Inventory Control & Financial Analytics | Real-time Insights | Updated: {datetime.now().strftime('%d %B %Y %H:%M')}")

# --- ====================================================== ---
# ---                KONEKSI & LOAD DATA                    ---
# --- ====================================================== ---

@st.cache_resource(show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def init_gsheet_connection():
    """Inisialisasi koneksi ke Google Sheets dengan retry mechanism"""
    try:
        skey = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(skey, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Koneksi Gagal: {str(e)}")
        return None

def validate_month_format(month_str):
    """Validate and standardize month formats"""
    if pd.isna(month_str):
        return datetime.now()
    
    month_str = str(month_str).strip().upper()
    
    # Mapping bulan
    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    formats_to_try = ['%b-%Y', '%b-%y', '%B %Y', '%m/%Y', '%Y-%m']
    
    for fmt in formats_to_try:
        try:
            return datetime.strptime(month_str, fmt)
        except:
            continue
    
    # Fallback: cari bulan dalam string
    for month_name, month_num in month_map.items():
        if month_name in month_str:
            # Cari tahun
            year_part = month_str.replace(month_name, '').replace('-', '').replace(' ', '').strip()
            if year_part and year_part.isdigit():
                year = int('20' + year_part) if len(year_part) == 2 else int(year_part)
            else:
                year = datetime.now().year
            
            return datetime(year, month_num, 1)
    
    return datetime.now()

def add_product_info_to_data(df, df_product):
    """Add Product_Name, Brand, SKU_Tier, Prices from Product_Master to any dataframe"""
    if df.empty or df_product.empty or 'SKU_ID' not in df.columns:
        return df
    
    # Get product info from Product_Master (including prices)
    price_cols = ['Floor_Price', 'Net_Order_Price'] if 'Floor_Price' in df_product.columns and 'Net_Order_Price' in df_product.columns else []
    
    product_info_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 'Status'] + price_cols
    product_info_cols = [col for col in product_info_cols if col in df_product.columns]
    
    product_info = df_product[product_info_cols].copy()
    product_info = product_info.drop_duplicates(subset=['SKU_ID'])
    
    # Remove existing columns if they exist (except SKU_ID)
    cols_to_remove = []
    for col in ['Product_Name', 'Brand', 'SKU_Tier', 'Status', 'Floor_Price', 'Net_Order_Price']:
        if col in df.columns and col != 'SKU_ID':
            cols_to_remove.append(col)
    
    if cols_to_remove:
        df_temp = df.drop(columns=cols_to_remove)
    else:
        df_temp = df.copy()
    
    # Merge with product info
    df_result = pd.merge(df_temp, product_info, on='SKU_ID', how='left')
    return df_result

@st.cache_data(ttl=300, max_entries=3, show_spinner=False)
def load_and_process_data(_client):
    """Load dan proses semua data sekaligus dengan chunk processing"""
    
    gsheet_url = st.secrets["gsheet_url"]
    data = {}
    
    try:
        # 1. PRODUCT MASTER (SUMBER UTAMA PRODUCT_INFO)
        ws = _client.open_by_url(gsheet_url).worksheet("Product_Master")
        df_product = pd.DataFrame(ws.get_all_records())
        df_product.columns = [col.strip().replace(' ', '_') for col in df_product.columns]
        
        # Validate price columns
        if 'Floor_Price' in df_product.columns:
            df_product['Floor_Price'] = pd.to_numeric(df_product['Floor_Price'], errors='coerce').fillna(0)
        if 'Net_Order_Price' in df_product.columns:
            df_product['Net_Order_Price'] = pd.to_numeric(df_product['Net_Order_Price'], errors='coerce').fillna(0)
        
        # Ensure Status column
        if 'Status' not in df_product.columns:
            df_product['Status'] = 'Active'
        
        df_product_active = df_product[df_product['Status'].str.upper() == 'ACTIVE'].copy()
        active_skus = df_product_active['SKU_ID'].tolist()
        
        # 2. SALES DATA (Data lengkap sejak Jan 2024)
        ws_sales = _client.open_by_url(gsheet_url).worksheet("Sales")
        df_sales_raw = pd.DataFrame(ws_sales.get_all_records())
        df_sales_raw.columns = [col.strip() for col in df_sales_raw.columns]
        
        # Process Sales data
        month_cols = [col for col in df_sales_raw.columns if any(m in col.upper() for m in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])]
        
        if month_cols and 'SKU_ID' in df_sales_raw.columns:
            # Get ID columns
            id_cols = ['SKU_ID']
            for col in ['SKU_Name', 'Product_Name', 'Brand', 'SKU_Tier']:
                if col in df_sales_raw.columns:
                    id_cols.append(col)
            
            # Melt to long format
            df_sales_long = df_sales_raw.melt(
                id_vars=id_cols,
                value_vars=month_cols,
                var_name='Month_Label',
                value_name='Sales_Qty'
            )
            
            df_sales_long['Sales_Qty'] = pd.to_numeric(df_sales_long['Sales_Qty'], errors='coerce').fillna(0)
            df_sales_long['Month'] = df_sales_long['Month_Label'].apply(validate_month_format)
            
            # Filter active SKUs
            df_sales_long = df_sales_long[df_sales_long['SKU_ID'].isin(active_skus)]
            
            # ADD PRODUCT INFO LOOKUP (with prices)
            df_sales_long = add_product_info_to_data(df_sales_long, df_product)
            
            # Sort by Month
            df_sales_long = df_sales_long.sort_values('Month')
            
            data['sales'] = df_sales_long
        
        # 3. ROFO DATA
        ws_rofo = _client.open_by_url(gsheet_url).worksheet("Rofo")
        df_rofo_raw = pd.DataFrame(ws_rofo.get_all_records())
        df_rofo_raw.columns = [col.strip() for col in df_rofo_raw.columns]
        
        month_cols_rofo = [col for col in df_rofo_raw.columns if any(m in col.upper() for m in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])]
        
        if month_cols_rofo:
            id_cols_rofo = ['SKU_ID']
            for col in ['Product_Name', 'Brand']:
                if col in df_rofo_raw.columns:
                    id_cols_rofo.append(col)
            
            df_rofo_long = df_rofo_raw.melt(
                id_vars=id_cols_rofo,
                value_vars=month_cols_rofo,
                var_name='Month_Label',
                value_name='Forecast_Qty'
            )
            
            df_rofo_long['Forecast_Qty'] = pd.to_numeric(df_rofo_long['Forecast_Qty'], errors='coerce').fillna(0)
            df_rofo_long['Month'] = df_rofo_long['Month_Label'].apply(validate_month_format)
            df_rofo_long = df_rofo_long[df_rofo_long['SKU_ID'].isin(active_skus)]
            
            # ADD PRODUCT INFO LOOKUP
            df_rofo_long = add_product_info_to_data(df_rofo_long, df_product)
            
            data['forecast'] = df_rofo_long
        
        # 4. PO DATA
        ws_po = _client.open_by_url(gsheet_url).worksheet("PO")
        df_po_raw = pd.DataFrame(ws_po.get_all_records())
        df_po_raw.columns = [col.strip() for col in df_po_raw.columns]
        
        month_cols_po = [col for col in df_po_raw.columns if any(m in col.upper() for m in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])]
        
        if month_cols_po and 'SKU_ID' in df_po_raw.columns:
            df_po_long = df_po_raw.melt(
                id_vars=['SKU_ID'],
                value_vars=month_cols_po,
                var_name='Month_Label',
                value_name='PO_Qty'
            )
            
            df_po_long['PO_Qty'] = pd.to_numeric(df_po_long['PO_Qty'], errors='coerce').fillna(0)
            df_po_long['Month'] = df_po_long['Month_Label'].apply(validate_month_format)
            df_po_long = df_po_long[df_po_long['SKU_ID'].isin(active_skus)]
            
            # ADD PRODUCT INFO LOOKUP
            df_po_long = add_product_info_to_data(df_po_long, df_product)
            
            data['po'] = df_po_long
        
        # 5. STOCK DATA
        ws_stock = _client.open_by_url(gsheet_url).worksheet("Stock_Onhand")
        df_stock_raw = pd.DataFrame(ws_stock.get_all_records())
        df_stock_raw.columns = [col.strip().replace(' ', '_') for col in df_stock_raw.columns]
        
        stock_col = None
        for col in ['Quantity_Available', 'Stock_Qty', 'STOCK_SAP']:
            if col in df_stock_raw.columns:
                stock_col = col
                break
        
        if stock_col and 'SKU_ID' in df_stock_raw.columns:
            df_stock = pd.DataFrame({
                'SKU_ID': df_stock_raw['SKU_ID'],
                'Stock_Qty': pd.to_numeric(df_stock_raw[stock_col], errors='coerce').fillna(0)
            })
            
            df_stock = df_stock.groupby('SKU_ID')['Stock_Qty'].max().reset_index()
            df_stock = df_stock[df_stock['SKU_ID'].isin(active_skus)]
            
            # ADD PRODUCT INFO LOOKUP (with prices)
            df_stock = add_product_info_to_data(df_stock, df_product)
            
            data['stock'] = df_stock
        
        # 6. FORECAST 2026 ECOMM (sebelumnya Rofo_onwards)
        try:
            ws_ecomm_forecast = _client.open_by_url(gsheet_url).worksheet("Forecast_2026_Ecomm")
            df_ecomm_forecast_raw = pd.DataFrame(ws_ecomm_forecast.get_all_records())
            df_ecomm_forecast_raw.columns = [col.strip().replace(' ', '_') for col in df_ecomm_forecast_raw.columns]
            
            # Identify month columns
            month_cols_ecomm = []
            for col in df_ecomm_forecast_raw.columns:
                if any(m in col.upper() for m in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']):
                    month_cols_ecomm.append(col)
            
            # Convert month columns to numeric
            for col in month_cols_ecomm:
                df_ecomm_forecast_raw[col] = pd.to_numeric(df_ecomm_forecast_raw[col], errors='coerce').fillna(0)
            
            data['ecomm_forecast'] = df_ecomm_forecast_raw
            data['ecomm_forecast_month_cols'] = month_cols_ecomm
            
        except Exception as e:
            st.warning(f"Forecast_2026_Ecomm data not available: {str(e)}")
            data['ecomm_forecast'] = pd.DataFrame()
            data['ecomm_forecast_month_cols'] = []
        
        # 7. FORECAST 2026 RESELLER (data baru)
        try:
            ws_reseller_forecast = _client.open_by_url(gsheet_url).worksheet("Forecast_2026_Reseller")
            df_reseller_forecast_raw = pd.DataFrame(ws_reseller_forecast.get_all_records())
            df_reseller_forecast_raw.columns = [col.strip().replace(' ', '_') for col in df_reseller_forecast_raw.columns]
            
            # Identify ALL month columns (Jan-24 sampai Dec-26)
            all_month_cols_reseller = []
            for col in df_reseller_forecast_raw.columns:
                if any(m in col.upper() for m in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']):
                    all_month_cols_reseller.append(col)
            
            # Convert month columns to numeric
            for col in all_month_cols_reseller:
                df_reseller_forecast_raw[col] = pd.to_numeric(df_reseller_forecast_raw[col], errors='coerce').fillna(0)
            
            # Split into historical (up to Dec-25) and forecast (Jan-26 onward)
            forecast_start_date = datetime(2026, 1, 1)
            
            def is_forecast_month(month_str):
                """Check if month is Jan-2026 or later"""
                try:
                    month_str = str(month_str).upper()
                    if '-' in month_str:
                        month_part, year_part = month_str.split('-')
                        month_num = datetime.strptime(month_part[:3], '%b').month
                        year = 2000 + int(year_part) if len(year_part) == 2 else int(year_part)
                        month_date = datetime(year, month_num, 1)
                        return month_date >= forecast_start_date
                except:
                    return False
                return False
            
            historical_cols = []
            forecast_cols = []
            for col in all_month_cols_reseller:
                if is_forecast_month(col):
                    forecast_cols.append(col)
                else:
                    historical_cols.append(col)
            
            data['reseller_forecast'] = df_reseller_forecast_raw
            data['reseller_all_month_cols'] = all_month_cols_reseller
            data['reseller_historical_cols'] = historical_cols  # Sales data
            data['reseller_forecast_cols'] = forecast_cols     # Forecast data
            
        except Exception as e:
            st.warning(f"Forecast_2026_Reseller data not available: {str(e)}")
            data['reseller_forecast'] = pd.DataFrame()
            data['reseller_all_month_cols'] = []
            data['reseller_historical_cols'] = []
            data['reseller_forecast_cols'] = []
        
        data['product'] = df_product
        data['product_active'] = df_product_active
        
        return data
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return {}

# --- ====================================================== ---
# ---                FINANCIAL FUNCTIONS                    ---
# --- ====================================================== ---

@st.cache_data(ttl=300)
def calculate_financial_metrics_all(df_sales, df_product):
    """Calculate all financial metrics from sales data"""
    
    if df_sales.empty or df_product.empty:
        return pd.DataFrame()
    
    try:
        # Check if price columns exist
        required_price_cols = ['Floor_Price', 'Net_Order_Price']
        price_cols_exist = all(col in df_product.columns for col in required_price_cols)
        
        if not price_cols_exist:
            st.warning("⚠️ Price columns missing in Product Master")
            return pd.DataFrame()
        
        # Ensure sales data has product info with prices
        if 'Floor_Price' not in df_sales.columns or 'Net_Order_Price' not in df_sales.columns:
            df_sales = add_product_info_to_data(df_sales, df_product)
        
        # Fill missing prices
        df_sales['Floor_Price'] = df_sales['Floor_Price'].fillna(0)
        df_sales['Net_Order_Price'] = df_sales['Net_Order_Price'].fillna(0)
        
        # Calculate financial metrics
        df_sales['Revenue'] = df_sales['Sales_Qty'] * df_sales['Floor_Price']
        df_sales['Cost'] = df_sales['Sales_Qty'] * df_sales['Net_Order_Price']
        df_sales['Gross_Margin'] = df_sales['Revenue'] - df_sales['Cost']
        df_sales['Margin_Percentage'] = np.where(
            df_sales['Revenue'] > 0,
            (df_sales['Gross_Margin'] / df_sales['Revenue'] * 100),
            0
        )
        
        # Add additional metrics
        df_sales['Avg_Selling_Price'] = np.where(
            df_sales['Sales_Qty'] > 0,
            df_sales['Revenue'] / df_sales['Sales_Qty'],
            0
        )
        
        return df_sales
        
    except Exception as e:
        st.error(f"Financial metrics calculation error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def calculate_inventory_financial(df_stock, df_product):
    """Calculate inventory financial value"""
    
    if df_stock.empty or df_product.empty:
        return pd.DataFrame()
    
    try:
        # Check price columns
        if 'Floor_Price' not in df_product.columns or 'Net_Order_Price' not in df_product.columns:
            return pd.DataFrame()
        
        # Ensure stock data has prices
        if 'Floor_Price' not in df_stock.columns or 'Net_Order_Price' not in df_stock.columns:
            df_stock = add_product_info_to_data(df_stock, df_product)
        
        # Fill missing prices
        df_stock['Floor_Price'] = df_stock['Floor_Price'].fillna(0)
        df_stock['Net_Order_Price'] = df_stock['Net_Order_Price'].fillna(0)
        
        # Calculate inventory values
        df_stock['Value_at_Cost'] = df_stock['Stock_Qty'] * df_stock['Net_Order_Price']
        df_stock['Value_at_Retail'] = df_stock['Stock_Qty'] * df_stock['Floor_Price']
        df_stock['Potential_Margin'] = df_stock['Value_at_Retail'] - df_stock['Value_at_Cost']
        df_stock['Margin_Percentage'] = np.where(
            df_stock['Value_at_Retail'] > 0,
            (df_stock['Potential_Margin'] / df_stock['Value_at_Retail'] * 100),
            0
        )
        
        return df_stock
        
    except Exception as e:
        st.error(f"Inventory financial calculation error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def calculate_seasonality(df_financial):
    """Calculate seasonal patterns from financial data"""
    
    if df_financial.empty:
        return pd.DataFrame()
    
    try:
        # Add month and year columns
        df_financial['Year'] = df_financial['Month'].dt.year
        df_financial['Month_Num'] = df_financial['Month'].dt.month
        df_financial['Month_Name'] = df_financial['Month'].dt.strftime('%b')
        
        # Group by month across years
        seasonal_pattern = df_financial.groupby(['Month_Num', 'Month_Name']).agg({
            'Revenue': 'mean',
            'Gross_Margin': 'mean',
            'Sales_Qty': 'mean'
        }).reset_index()
        
        # Calculate seasonal indices
        overall_avg_revenue = seasonal_pattern['Revenue'].mean()
        seasonal_pattern['Seasonal_Index_Revenue'] = seasonal_pattern['Revenue'] / overall_avg_revenue
        
        overall_avg_margin = seasonal_pattern['Gross_Margin'].mean()
        seasonal_pattern['Seasonal_Index_Margin'] = seasonal_pattern['Gross_Margin'] / overall_avg_margin
        
        # Classify seasons
        conditions = [
            seasonal_pattern['Seasonal_Index_Revenue'] >= 1.2,
            (seasonal_pattern['Seasonal_Index_Revenue'] >= 0.9) & (seasonal_pattern['Seasonal_Index_Revenue'] < 1.2),
            seasonal_pattern['Seasonal_Index_Revenue'] < 0.9
        ]
        choices = ['Peak Season', 'Normal Season', 'Low Season']
        
        seasonal_pattern['Season_Type'] = np.select(conditions, choices, default='Normal Season')
        
        return seasonal_pattern.sort_values('Month_Num')
        
    except Exception as e:
        st.error(f"Seasonality calculation error: {str(e)}")
        return pd.DataFrame()

def calculate_eoq(demand, order_cost, holding_cost_per_unit):
    """Calculate Economic Order Quantity"""
    if demand <= 0 or order_cost <= 0 or holding_cost_per_unit <= 0:
        return 0
    
    eoq = math.sqrt((2 * demand * order_cost) / holding_cost_per_unit)
    return round(eoq)

def calculate_forecast_bias(df_forecast, df_po):
    """Calculate forecast bias (systematic over/under forecasting)"""
    
    if df_forecast.empty or df_po.empty:
        return {}
    
    try:
        # Get common months
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        common_months = sorted(set(forecast_months) & set(po_months))
        
        if not common_months:
            return {}
        
        bias_results = []
        
        for month in common_months:
            df_f_month = df_forecast[df_forecast['Month'] == month]
            df_p_month = df_po[df_po['Month'] == month]
            
            # Merge forecast and PO
            df_merged = pd.merge(
                df_f_month[['SKU_ID', 'Forecast_Qty']],
                df_p_month[['SKU_ID', 'PO_Qty']],
                on='SKU_ID',
                how='inner'
            )
            
            # Calculate bias
            df_merged['Bias'] = df_merged['PO_Qty'] - df_merged['Forecast_Qty']
            df_merged['Bias_Percentage'] = np.where(
                df_merged['Forecast_Qty'] > 0,
                (df_merged['Bias'] / df_merged['Forecast_Qty'] * 100),
                0
            )
            
            avg_bias = df_merged['Bias'].mean()
            avg_bias_pct = df_merged['Bias_Percentage'].mean()
            
            bias_results.append({
                'Month': month,
                'Avg_Bias': avg_bias,
                'Avg_Bias_Percentage': avg_bias_pct,
                'Over_Forecast_SKUs': len(df_merged[df_merged['Bias'] > 0]),
                'Under_Forecast_SKUs': len(df_merged[df_merged['Bias'] < 0])
            })
        
        return pd.DataFrame(bias_results)
        
    except Exception as e:
        st.error(f"Forecast bias calculation error: {str(e)}")
        return pd.DataFrame()

# --- ====================================================== ---
# ---                ANALYTICS FUNCTIONS                    ---
# --- ====================================================== ---

def calculate_monthly_performance(df_forecast, df_po, df_product):
    """Calculate performance for each month separately - HANYA SKU dengan Forecast_Qty > 0"""
    
    monthly_performance = {}
    
    if df_forecast.empty or df_po.empty:
        return monthly_performance
    
    try:
        # ADD PRODUCT INFO jika belum ada
        df_forecast = add_product_info_to_data(df_forecast, df_product)
        df_po = add_product_info_to_data(df_po, df_product)
        
        # Get unique months from both datasets
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        all_months = sorted(set(list(forecast_months) + list(po_months)))
        
        for month in all_months:
            # Get data for this month - FILTER HANYA Forecast_Qty > 0
            df_forecast_month = df_forecast[
                (df_forecast['Month'] == month) & 
                (df_forecast['Forecast_Qty'] > 0)
            ].copy()
            
            df_po_month = df_po[df_po['Month'] == month].copy()
            
            if df_forecast_month.empty or df_po_month.empty:
                continue
            
            # Merge forecast and PO for this month
            df_merged = pd.merge(
                df_forecast_month,
                df_po_month,
                on=['SKU_ID'],
                how='inner',
                suffixes=('_forecast', '_po')
            )
            
            if not df_merged.empty:
                # Add product info (jika belum ada dari merge)
                if 'Product_Name' not in df_merged.columns or 'Brand' not in df_merged.columns:
                    df_merged = add_product_info_to_data(df_merged, df_product)
                
                # Calculate ratio - Pastikan Forecast_Qty > 0
                df_merged['PO_Rofo_Ratio'] = np.where(
                    df_merged['Forecast_Qty'] > 0,
                    (df_merged['PO_Qty'] / df_merged['Forecast_Qty']) * 100,
                    0
                )
                
                # Categorize
                conditions = [
                    df_merged['PO_Rofo_Ratio'] < 80,
                    (df_merged['PO_Rofo_Ratio'] >= 80) & (df_merged['PO_Rofo_Ratio'] <= 120),
                    df_merged['PO_Rofo_Ratio'] > 120
                ]
                choices = ['Under', 'Accurate', 'Over']
                df_merged['Accuracy_Status'] = np.select(conditions, choices, default='Unknown')
                
                # Calculate metrics
                df_merged['Absolute_Percentage_Error'] = abs(df_merged['PO_Rofo_Ratio'] - 100)
                
                # Hanya hitung MAPE untuk SKU dengan Forecast_Qty > 0
                valid_skus = df_merged[df_merged['Forecast_Qty'] > 0]
                if not valid_skus.empty:
                    mape = valid_skus['Absolute_Percentage_Error'].mean()
                else:
                    mape = 0
                    
                monthly_accuracy = 100 - mape
                
                # Status counts
                status_counts = df_merged['Accuracy_Status'].value_counts().to_dict()
                total_records = len(df_merged)
                status_percentages = {k: (v/total_records*100) for k, v in status_counts.items()}
                
                # Store results
                monthly_performance[month] = {
                    'accuracy': monthly_accuracy,
                    'mape': mape,
                    'status_counts': status_counts,
                    'status_percentages': status_percentages,
                    'total_records': total_records,
                    'data': df_merged,
                    'under_skus': df_merged[df_merged['Accuracy_Status'] == 'Under'].copy(),
                    'over_skus': df_merged[df_merged['Accuracy_Status'] == 'Over'].copy(),
                    'accurate_skus': df_merged[df_merged['Accuracy_Status'] == 'Accurate'].copy()
                }
        
        return monthly_performance
        
    except Exception as e:
        st.error(f"Monthly performance calculation error: {str(e)}")
        return monthly_performance

def get_last_3_months_performance(monthly_performance):
    """Get performance for last 3 months"""
    
    if not monthly_performance:
        return {}
    
    # Get last 3 months
    sorted_months = sorted(monthly_performance.keys())
    if len(sorted_months) >= 3:
        last_3_months = sorted_months[-3:]
    else:
        last_3_months = sorted_months
    
    last_3_data = {}
    for month in last_3_months:
        last_3_data[month] = monthly_performance[month]
    
    return last_3_data

def calculate_inventory_metrics_with_3month_avg(df_stock, df_sales, df_product):
    """Calculate inventory metrics using 3-month average sales"""
    
    metrics = {}
    
    if df_stock.empty or df_sales.empty:
        return metrics
    
    try:
        # ADD PRODUCT INFO jika belum ada
        df_stock = add_product_info_to_data(df_stock, df_product)
        df_sales = add_product_info_to_data(df_sales, df_product)
        
        # Get last 3 months sales data
        if not df_sales.empty:
            sales_months = sorted(df_sales['Month'].unique())
            if len(sales_months) >= 3:
                last_3_sales_months = sales_months[-3:]
                df_sales_last_3 = df_sales[df_sales['Month'].isin(last_3_sales_months)].copy()
            else:
                df_sales_last_3 = df_sales.copy()
        
        # Calculate average monthly sales per SKU for last 3 months
        if not df_sales_last_3.empty:
            avg_monthly_sales = df_sales_last_3.groupby('SKU_ID')['Sales_Qty'].mean().reset_index()
            avg_monthly_sales.columns = ['SKU_ID', 'Avg_Monthly_Sales_3M']
        else:
            avg_monthly_sales = pd.DataFrame(columns=['SKU_ID', 'Avg_Monthly_Sales_3M'])
        
        # Merge with product info
        df_inventory = pd.merge(
            df_stock,
            df_product[['SKU_ID', 'Product_Name', 'SKU_Tier', 'Brand', 'Status']],
            on='SKU_ID',
            how='left'
        )
        
        # Merge with average sales
        df_inventory = pd.merge(df_inventory, avg_monthly_sales, on='SKU_ID', how='left')
        df_inventory['Avg_Monthly_Sales_3M'] = df_inventory['Avg_Monthly_Sales_3M'].fillna(0)
        
        # Calculate cover months using 3-month average
        df_inventory['Cover_Months'] = np.where(
            df_inventory['Avg_Monthly_Sales_3M'] > 0,
            df_inventory['Stock_Qty'] / df_inventory['Avg_Monthly_Sales_3M'],
            999  # For SKUs with no sales in last 3 months
        )
        
        # Categorize inventory status
        conditions = [
            df_inventory['Cover_Months'] < 0.8,
            (df_inventory['Cover_Months'] >= 0.8) & (df_inventory['Cover_Months'] <= 1.5),
            df_inventory['Cover_Months'] > 1.5
        ]
        choices = ['Need Replenishment', 'Ideal/Healthy', 'High Stock']
        df_inventory['Inventory_Status'] = np.select(conditions, choices, default='Unknown')
        
        # Get high stock items for reduction
        high_stock_df = df_inventory[df_inventory['Inventory_Status'] == 'High Stock'].copy()
        high_stock_df = high_stock_df.sort_values('Cover_Months', ascending=False)
        
        # Get low stock items
        low_stock_df = df_inventory[df_inventory['Inventory_Status'] == 'Need Replenishment'].copy()
        low_stock_df = low_stock_df.sort_values('Cover_Months', ascending=True)
        
        # Tier analysis
        if 'SKU_Tier' in df_inventory.columns:
            tier_analysis = df_inventory.groupby('SKU_Tier').agg({
                'SKU_ID': 'count',
                'Stock_Qty': 'sum',
                'Avg_Monthly_Sales_3M': 'sum',
                'Cover_Months': 'mean'
            }).reset_index()
            tier_analysis.columns = ['Tier', 'SKU_Count', 'Total_Stock', 'Total_Sales_3M_Avg', 'Avg_Cover_Months']
            tier_analysis['Turnover'] = tier_analysis['Total_Sales_3M_Avg'] / tier_analysis['Total_Stock']
            metrics['tier_analysis'] = tier_analysis
        
        metrics['inventory_df'] = df_inventory
        metrics['high_stock'] = high_stock_df
        metrics['low_stock'] = low_stock_df
        metrics['total_stock'] = df_inventory['Stock_Qty'].sum()
        metrics['total_skus'] = len(df_inventory)
        metrics['avg_cover'] = df_inventory[df_inventory['Cover_Months'] < 999]['Cover_Months'].mean()
        
        # Calculate inventory value metrics
        metrics['inventory_value_score'] = (len(df_inventory[df_inventory['Inventory_Status'] == 'Ideal/Healthy']) / 
                                         len(df_inventory) * 100) if len(df_inventory) > 0 else 0
        
        return metrics
        
    except Exception as e:
        st.error(f"Inventory metrics error: {str(e)}")
        return metrics

def calculate_sales_vs_forecast_po(df_sales, df_forecast, df_po, df_product):
    """Calculate sales vs forecast and PO comparison - HANYA ACTIVE SKUS"""
    
    results = {}
    
    if df_sales.empty or df_forecast.empty:
        return results
    
    try:
        # ADD PRODUCT INFO jika belum ada
        df_sales = add_product_info_to_data(df_sales, df_product)
        df_forecast = add_product_info_to_data(df_forecast, df_product)
        df_po = add_product_info_to_data(df_po, df_product)
        
        # FILTER HANYA ACTIVE SKUS
        if 'Status' in df_product.columns:
            active_skus = df_product[df_product['Status'].str.upper() == 'ACTIVE']['SKU_ID'].tolist()
            
            # Filter semua dataset untuk hanya active SKUs
            df_sales = df_sales[df_sales['SKU_ID'].isin(active_skus)]
            df_forecast = df_forecast[df_forecast['SKU_ID'].isin(active_skus)]
            if not df_po.empty:
                df_po = df_po[df_po['SKU_ID'].isin(active_skus)]
        
        # Get last 3 months for comparison
        sales_months = sorted(df_sales['Month'].unique())
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        
        # Find common months
        common_months = sorted(set(sales_months) & set(forecast_months) & set(po_months))
        
        if not common_months:
            return results
        
        # Use last common month
        last_month = common_months[-1]
        
        # Get data for last month
        df_sales_month = df_sales[df_sales['Month'] == last_month].copy()
        df_forecast_month = df_forecast[df_forecast['Month'] == last_month].copy()
        df_po_month = df_po[df_po['Month'] == last_month].copy()
        
        # Filter hanya SKU dengan Forecast_Qty > 0
        df_forecast_month = df_forecast_month[df_forecast_month['Forecast_Qty'] > 0]
        
        # Merge all data
        df_merged = pd.merge(
            df_sales_month[['SKU_ID', 'Sales_Qty']],
            df_forecast_month[['SKU_ID', 'Forecast_Qty']],
            on='SKU_ID',
            how='inner'
        )
        
        df_merged = pd.merge(
            df_merged,
            df_po_month[['SKU_ID', 'PO_Qty']],
            on='SKU_ID',
            how='left'
        )
        
        # Add product info
        df_merged = add_product_info_to_data(df_merged, df_product)
        
        # Filter out SKU dengan PO_Qty = 0 (tidak ada PO) jika mau
        # df_merged = df_merged[df_merged['PO_Qty'] > 0]
        
        # Calculate ratios
        df_merged['Sales_vs_Forecast_Ratio'] = np.where(
            df_merged['Forecast_Qty'] > 0,
            (df_merged['Sales_Qty'] / df_merged['Forecast_Qty']) * 100,
            0
        )
        
        df_merged['Sales_vs_PO_Ratio'] = np.where(
            df_merged['PO_Qty'] > 0,
            (df_merged['Sales_Qty'] / df_merged['PO_Qty']) * 100,
            0
        )
        
        # Calculate deviations
        df_merged['Forecast_Deviation'] = abs(df_merged['Sales_vs_Forecast_Ratio'] - 100)
        df_merged['PO_Deviation'] = abs(df_merged['Sales_vs_PO_Ratio'] - 100)
        
        # Identify SKUs with high deviation (> 30%) - HANYA ACTIVE SKUS
        high_deviation_skus = df_merged[
            (df_merged['Forecast_Deviation'] > 30) | 
            (df_merged['PO_Deviation'] > 30)
        ].copy()
        
        high_deviation_skus = high_deviation_skus.sort_values('Forecast_Deviation', ascending=False)
        
        # Calculate overall metrics
        avg_forecast_deviation = df_merged['Forecast_Deviation'].mean()
        avg_po_deviation = df_merged['PO_Deviation'].mean()
        
        results = {
            'last_month': last_month,
            'comparison_data': df_merged,
            'high_deviation_skus': high_deviation_skus,
            'avg_forecast_deviation': avg_forecast_deviation,
            'avg_po_deviation': avg_po_deviation,
            'total_skus_compared': len(df_merged),
            'active_skus_only': True
        }
        
        return results
        
    except Exception as e:
        st.error(f"Sales vs forecast calculation error: {str(e)}")
        return results

def calculate_brand_performance(df_forecast, df_po, df_product):
    """Calculate forecast accuracy performance by brand"""
    
    if df_forecast.empty or df_po.empty or df_product.empty:
        return pd.DataFrame()
    
    try:
        # ADD PRODUCT INFO jika belum ada
        df_forecast = add_product_info_to_data(df_forecast, df_product)
        df_po = add_product_info_to_data(df_po, df_product)
        
        # Get last month data
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        common_months = sorted(set(forecast_months) & set(po_months))
        
        if not common_months:
            return pd.DataFrame()
        
        last_month = common_months[-1]
        
        # Get data for last month
        df_forecast_month = df_forecast[df_forecast['Month'] == last_month].copy()
        df_po_month = df_po[df_po['Month'] == last_month].copy()
        
        # Merge forecast and PO
        df_merged = pd.merge(
            df_forecast_month,
            df_po_month,
            on=['SKU_ID'],
            how='inner'
        )
        
        # Add brand info jika belum ada
        if 'Brand' not in df_merged.columns:
            df_merged = add_product_info_to_data(df_merged, df_product)
        
        if 'Brand' not in df_merged.columns:
            return pd.DataFrame()
        
        # Calculate ratio and accuracy
        df_merged['PO_Rofo_Ratio'] = np.where(
            df_merged['Forecast_Qty'] > 0,
            (df_merged['PO_Qty'] / df_merged['Forecast_Qty']) * 100,
            0
        )
        
        # Categorize
        conditions = [
            df_merged['PO_Rofo_Ratio'] < 80,
            (df_merged['PO_Rofo_Ratio'] >= 80) & (df_merged['PO_Rofo_Ratio'] <= 120),
            df_merged['PO_Rofo_Ratio'] > 120
        ]
        choices = ['Under', 'Accurate', 'Over']
        df_merged['Accuracy_Status'] = np.select(conditions, choices, default='Unknown')
        
        # Calculate brand performance
        brand_performance = df_merged.groupby('Brand').agg({
            'SKU_ID': 'count',
            'Forecast_Qty': 'sum',
            'PO_Qty': 'sum',
            'PO_Rofo_Ratio': lambda x: 100 - abs(x - 100).mean()  # Accuracy
        }).reset_index()
        
        brand_performance.columns = ['Brand', 'SKU_Count', 'Total_Forecast', 'Total_PO', 'Accuracy']
        
        # Calculate additional metrics
        brand_performance['PO_vs_Forecast_Ratio'] = (brand_performance['Total_PO'] / brand_performance['Total_Forecast'] * 100)
        brand_performance['Qty_Difference'] = brand_performance['Total_PO'] - brand_performance['Total_Forecast']
        
        # Get status counts
        status_counts = df_merged.groupby(['Brand', 'Accuracy_Status']).size().unstack(fill_value=0).reset_index()
        
        # Merge with performance data
        brand_performance = pd.merge(brand_performance, status_counts, on='Brand', how='left')
        
        # Fill NaN with 0 for status columns
        for status in ['Under', 'Accurate', 'Over']:
            if status not in brand_performance.columns:
                brand_performance[status] = 0
        
        # Sort by accuracy
        brand_performance = brand_performance.sort_values('Accuracy', ascending=False)
        
        return brand_performance
        
    except Exception as e:
        st.error(f"Brand performance calculation error: {str(e)}")
        return pd.DataFrame()

def identify_profitability_segments(df_financial):
    """Segment SKUs by profitability"""
    
    if df_financial.empty:
        return pd.DataFrame()
    
    try:
        sku_profitability = df_financial.groupby(['SKU_ID', 'Product_Name', 'Brand']).agg({
            'Revenue': 'sum',
            'Gross_Margin': 'sum',
            'Sales_Qty': 'sum'
        }).reset_index()
        
        # Calculate metrics
        sku_profitability['Avg_Margin_Per_SKU'] = sku_profitability['Gross_Margin'] / sku_profitability['Sales_Qty']
        sku_profitability['Margin_Percentage'] = np.where(
            sku_profitability['Revenue'] > 0,
            (sku_profitability['Gross_Margin'] / sku_profitability['Revenue'] * 100),
            0
        )
        
        # Segment by margin percentage
        conditions = [
            (sku_profitability['Margin_Percentage'] >= 40),
            (sku_profitability['Margin_Percentage'] >= 20) & (sku_profitability['Margin_Percentage'] < 40),
            (sku_profitability['Margin_Percentage'] < 20) & (sku_profitability['Margin_Percentage'] > 0),
            (sku_profitability['Margin_Percentage'] <= 0)
        ]
        choices = ['High Margin (>40%)', 'Medium Margin (20-40%)', 'Low Margin (<20%)', 'Negative Margin']
        
        sku_profitability['Margin_Segment'] = np.select(conditions, choices, default='Unknown')
        
        return sku_profitability.sort_values('Gross_Margin', ascending=False)
        
    except Exception as e:
        st.error(f"Profitability segmentation error: {str(e)}")
        return pd.DataFrame()

def validate_data_quality(df, df_name):
    """Comprehensive data quality validation"""
    
    checks = {}
    
    if df.empty:
        checks['Empty Dataset'] = '❌ Dataset kosong'
        return checks
    
    # Basic checks
    checks['Total Rows'] = f"📊 {len(df):,} rows"
    checks['Total Columns'] = f"📋 {len(df.columns)} columns"
    
    # Missing values
    missing_values = df.isnull().sum().sum()
    missing_pct = (missing_values / (len(df) * len(df.columns)) * 100)
    checks['Missing Values'] = f"⚠️ {missing_values:,} ({missing_pct:.1f}%)" if missing_values > 0 else f"✅ {missing_values:,}"
    
    # Duplicates
    duplicates = df.duplicated().sum()
    checks['Duplicate Rows'] = f"⚠️ {duplicates:,}" if duplicates > 0 else f"✅ {duplicates:,}"
    
    # Zero values (for numeric columns)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        zero_values = (df[numeric_cols] == 0).sum().sum()
        zero_pct = (zero_values / (len(df) * len(numeric_cols)) * 100)
        checks['Zero Values'] = f"📉 {zero_values:,} ({zero_pct:.1f}%)"
    
    # Negative values
    if len(numeric_cols) > 0:
        negative_values = (df[numeric_cols] < 0).sum().sum()
        if negative_values > 0:
            checks['Negative Values'] = f"❌ {negative_values:,}"
    
    # Date range (if Month column exists)
    if 'Month' in df.columns:
        try:
            min_date = df['Month'].min()
            max_date = df['Month'].max()
            checks['Date Range'] = f"📅 {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
        except:
            pass
    
    return checks

# --- ====================================================== ---
# ---                DASHBOARD INITIALIZATION               ---
# --- ====================================================== ---

# Initialize connection
client = init_gsheet_connection()

if client is None:
    st.error("❌ Tidak dapat terhubung ke Google Sheets")
    st.stop()

# Load and process data
with st.spinner('🔄 Loading and processing data from Google Sheets...'):
    all_data = load_and_process_data(client)
    
    df_product = all_data.get('product', pd.DataFrame())
    df_product_active = all_data.get('product_active', pd.DataFrame())
    df_sales = all_data.get('sales', pd.DataFrame())
    df_forecast = all_data.get('forecast', pd.DataFrame())
    df_po = all_data.get('po', pd.DataFrame())
    df_stock = all_data.get('stock', pd.DataFrame())
    
    # Ganti rofo_onwards dengan ecomm_forecast (untuk Tab 7)
    df_ecomm_forecast = all_data.get('ecomm_forecast', pd.DataFrame())
    ecomm_forecast_month_cols = all_data.get('ecomm_forecast_month_cols', [])
    
    # Tambah data reseller (untuk Tab 9)
    df_reseller_forecast = all_data.get('reseller_forecast', pd.DataFrame())
    reseller_all_month_cols = all_data.get('reseller_all_month_cols', [])
    reseller_historical_cols = all_data.get('reseller_historical_cols', [])
    reseller_forecast_cols = all_data.get('reseller_forecast_cols', [])
    
    # Untuk backward compatibility (jika ada script yang masih pakai nama lama)
    df_rofo_onwards = df_ecomm_forecast  # Alias untuk Tab 7
    rofo_onwards_month_cols = ecomm_forecast_month_cols  # Alias untuk Tab 7

# Calculate metrics
monthly_performance = calculate_monthly_performance(df_forecast, df_po, df_product)
last_3_months_performance = get_last_3_months_performance(monthly_performance)
inventory_metrics = calculate_inventory_metrics_with_3month_avg(df_stock, df_sales, df_product)
sales_vs_forecast = calculate_sales_vs_forecast_po(df_sales, df_forecast, df_po, df_product)

# Calculate financial metrics
df_financial = calculate_financial_metrics_all(df_sales, df_product)
df_inventory_financial = calculate_inventory_financial(df_stock, df_product)
seasonal_pattern = calculate_seasonality(df_financial) if not df_financial.empty else pd.DataFrame()
forecast_bias = calculate_forecast_bias(df_forecast, df_po)
profitability_segments = identify_profitability_segments(df_financial) if not df_financial.empty else pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Dashboard Controls")
    
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    with col_sb2:
        if st.button("📊 Show Data Stats", use_container_width=True):
            st.session_state.show_stats = True
    
    st.markdown("---")
    st.markdown("### 📈 Data Overview")
    
    if not df_product_active.empty:
        st.metric("Active SKUs", len(df_product_active))
    
    if not df_stock.empty:
        total_stock = df_stock['Stock_Qty'].sum()
        st.metric("Total Stock", f"{total_stock:,.0f}")
    
    if monthly_performance:
        last_month = sorted(monthly_performance.keys())[-1]
        accuracy = monthly_performance[last_month]['accuracy']
        st.metric("Latest Accuracy", f"{accuracy:.1f}%")
    
    # Financial metrics in sidebar
    if not df_financial.empty:
        st.markdown("---")
        st.markdown("### 💰 Financial Overview")
        
        total_revenue = df_financial['Revenue'].sum()
        total_margin = df_financial['Gross_Margin'].sum()
        avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
        
        st.metric("Total Revenue", f"Rp {total_revenue:,.0f}")
        st.metric("Total Margin", f"Rp {total_margin:,.0f}")
        st.metric("Avg Margin %", f"{avg_margin_pct:.1f}%")
    
    st.markdown("---")
    
    # Threshold Settings
    st.markdown("### ⚙️ Threshold Settings")
    under_threshold = st.slider("Under Forecast Threshold (%)", 0, 100, 80)
    over_threshold = st.slider("Over Forecast Threshold (%)", 100, 200, 120)
    
    st.markdown("---")
    
    # Inventory Thresholds
    st.markdown("### 📦 Inventory Thresholds")
    low_stock_threshold = st.slider("Low Stock (months)", 0.0, 2.0, 0.8, 0.1)
    high_stock_threshold = st.slider("High Stock (months)", 1.0, 6.0, 1.5, 0.1)
    
    # Financial Thresholds
    st.markdown("---")
    st.markdown("### 💰 Financial Thresholds")
    high_margin_threshold = st.slider("High Margin Threshold (%)", 0, 100, 40)
    low_margin_threshold = st.slider("Low Margin Threshold (%)", 0, 100, 20)
    
    # Dark mode toggle
    st.markdown("---")
    dark_mode = st.checkbox("🌙 Dark Mode", value=False)
    if dark_mode:
        st.markdown("""
        <style>
            .stApp { background-color: #0E1117; color: white; }
            .stDataFrame { background-color: #1E1E1E; }
        </style>
        """, unsafe_allow_html=True)

# Data quality check
if 'show_stats' in st.session_state and st.session_state.show_stats:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Data Quality Check")
    
    for df_name, df in [("Product", df_product), ("Sales", df_sales), 
                       ("Forecast", df_forecast), ("PO", df_po), 
                       ("Stock", df_stock), ("Financial", df_financial)]:
        if not df.empty:
            checks = validate_data_quality(df, df_name)
            with st.sidebar.expander(f"{df_name} Data"):
                for check_name, check_result in checks.items():
                    st.write(f"{check_name}: {check_result}")

# --- MAIN DASHBOARD ---

# PERUBAHAN 1: Chart Accuracy Trend di Paling Atas
st.subheader("📈 Accuracy Trend Over Time")

if monthly_performance:
    # Create monthly performance summary table
    summary_data = []
    for month, data in sorted(monthly_performance.items()):
        summary_data.append({
            'Month': month,
            'Month_Display': month.strftime('%b-%Y'),
            'Accuracy (%)': data['accuracy'],
            'Under': data['status_counts'].get('Under', 0),
            'Accurate': data['status_counts'].get('Accurate', 0),
            'Over': data['status_counts'].get('Over', 0),
            'Total SKUs': data['total_records'],
            'MAPE': data['mape']
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Display chart with enhanced styling
    if not summary_df.empty:
        # Sort by month
        summary_df = summary_df.sort_values('Month')
        
        # Create enhanced chart dengan styling yang aman
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=summary_df['Month_Display'],
            y=summary_df['Accuracy (%)'],
            mode='lines+markers+text',
            line=dict(color='#667eea', width=4),
            marker=dict(size=12, color='#764ba2'),
            text=summary_df['Accuracy (%)'].apply(lambda x: f"{x:.1f}%"),
            textposition="top center"
        ))
        
        fig.update_layout(
            height=500,
            title_text='<b>Forecast Accuracy Trend Over Time</b>',
            title_x=0.5,
            xaxis_title='<b>Month-Year</b>',
            yaxis_title='<b>Accuracy (%)</b>',
            yaxis_ticksuffix="%",
            plot_bgcolor='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# SECTION 1: LAST 3 MONTHS PERFORMANCE (DIPERBESAR)
st.subheader("🎯 Forecast Performance - 3 Bulan Terakhir")

if last_3_months_performance:
    # Display last 3 months performance
    months_display = []
    
    # Create container untuk 3 bulan
    month_cols = st.columns(3)
    
    for i, (month, data) in enumerate(sorted(last_3_months_performance.items())):
        month_name = month.strftime('%b %Y')
        accuracy = data['accuracy']
        
        with month_cols[i]:
            under_count = data['status_counts'].get('Under', 0)
            accurate_count = data['status_counts'].get('Accurate', 0)
            over_count = data['status_counts'].get('Over', 0)
            total_records = data['total_records']
            
            # Create HTML dengan single line f-string
            html_content = (
                f'<div style="background: white; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(0,0,0,0.1); border-top: 5px solid #667eea;">'
                f'<div style="text-align: center; margin-bottom: 1rem;">'
                f'<h3 style="margin: 0; color: #333;">{month_name}</h3>'
                f'<div style="font-size: 2rem; font-weight: 900; color: #667eea;">{accuracy:.1f}%</div>'
                f'<div style="font-size: 0.9rem; color: #666;">Overall Accuracy</div>'
                f'</div>'
                f'<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 1rem;">'
                f'<div style="text-align: center; padding: 0.5rem; background: #FFEBEE; border-radius: 8px;">'
                f'<div style="font-size: 1.5rem; font-weight: 900; color: #F44336;">{under_count}</div>'
                f'<div style="font-size: 0.8rem; color: #F44336;">Under</div>'
                f'</div>'
                f'<div style="text-align: center; padding: 0.5rem; background: #E8F5E9; border-radius: 8px;">'
                f'<div style="font-size: 1.5rem; font-weight: 900; color: #4CAF50;">{accurate_count}</div>'
                f'<div style="font-size: 0.8rem; color: #4CAF50;">Accurate</div>'
                f'</div>'
                f'<div style="text-align: center; padding: 0.5rem; background: #FFF3E0; border-radius: 8px;">'
                f'<div style="font-size: 1.5rem; font-weight: 900; color: #FF9800;">{over_count}</div>'
                f'<div style="font-size: 0.8rem; color: #FF9800;">Over</div>'
                f'</div>'
                f'</div>'
                f'<div style="text-align: center; font-size: 0.9rem; color: #666;">Total SKUs: {total_records}</div>'
                f'</div>'
            )
            
            st.markdown(html_content, unsafe_allow_html=True)
        
        months_display.append(month_name)
        
    # TOTAL METRICS - BULAN TERAKHIR (dengan Qty dan persentase)
    st.divider()
    st.subheader("📊 Total Metrics - Bulan Terakhir")
    
    # Calculate metrics for LAST MONTH ONLY
    if monthly_performance:
        last_month = sorted(monthly_performance.keys())[-1]
        last_month_data = monthly_performance[last_month]['data']
        
        # Count SKUs by status for last month
        under_count = last_month_data[last_month_data['Accuracy_Status'] == 'Under']['SKU_ID'].nunique()
        accurate_count = last_month_data[last_month_data['Accuracy_Status'] == 'Accurate']['SKU_ID'].nunique()
        over_count = last_month_data[last_month_data['Accuracy_Status'] == 'Over']['SKU_ID'].nunique()
        total_count_last_month = last_month_data['SKU_ID'].nunique()
        
        # Sum of forecast quantity by status for last month
        under_forecast_qty = last_month_data[last_month_data['Accuracy_Status'] == 'Under']['Forecast_Qty'].sum()
        accurate_forecast_qty = last_month_data[last_month_data['Accuracy_Status'] == 'Accurate']['Forecast_Qty'].sum()
        over_forecast_qty = last_month_data[last_month_data['Accuracy_Status'] == 'Over']['Forecast_Qty'].sum()
        total_forecast_qty = last_month_data['Forecast_Qty'].sum()
        
        # Calculate percentages
        under_pct = (under_count / total_count_last_month * 100) if total_count_last_month > 0 else 0
        accurate_pct = (accurate_count / total_count_last_month * 100) if total_count_last_month > 0 else 0
        over_pct = (over_count / total_count_last_month * 100) if total_count_last_month > 0 else 0
        
        under_forecast_pct = (under_forecast_qty / total_forecast_qty * 100) if total_forecast_qty > 0 else 0
        accurate_forecast_pct = (accurate_forecast_qty / total_forecast_qty * 100) if total_forecast_qty > 0 else 0
        over_forecast_pct = (over_forecast_qty / total_forecast_qty * 100) if total_forecast_qty > 0 else 0
    
        # Layout untuk Total Metrics bulan terakhir
    col_total1, col_total2, col_total3, col_total4 = st.columns(4)
    
    with col_total1:
        html_under = (
            f'<div style="background: white; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #F44336;">'
            f'<div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">UNDER FORECAST</div>'
            f'<div style="font-size: 1.5rem; font-weight: 800; color: #F44336;">{under_count} SKUs</div>'
            f'<div style="font-size: 0.9rem; color: #888;">Qty: {under_forecast_qty:,.0f}</div>'
            f'<div style="font-size: 0.8rem; color: #999;">SKU: {under_pct:.1f}% | Qty: {under_forecast_pct:.1f}%</div>'
            f'</div>'
        )
        st.markdown(html_under, unsafe_allow_html=True)
    
    with col_total2:
        html_accurate = (
            f'<div style="background: white; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #4CAF50;">'
            f'<div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">ACCURATE FORECAST</div>'
            f'<div style="font-size: 1.5rem; font-weight: 800; color: #4CAF50;">{accurate_count} SKUs</div>'
            f'<div style="font-size: 0.9rem; color: #888;">Qty: {accurate_forecast_qty:,.0f}</div>'
            f'<div style="font-size: 0.8rem; color: #999;">SKU: {accurate_pct:.1f}% | Qty: {accurate_forecast_pct:.1f}%</div>'
            f'</div>'
        )
        st.markdown(html_accurate, unsafe_allow_html=True)
    
    with col_total3:
        html_over = (
            f'<div style="background: white; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #FF9800;">'
            f'<div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">OVER FORECAST</div>'
            f'<div style="font-size: 1.5rem; font-weight: 800; color: #FF9800;">{over_count} SKUs</div>'
            f'<div style="font-size: 0.9rem; color: #888;">Qty: {over_forecast_qty:,.0f}</div>'
            f'<div style="font-size: 0.8rem; color: #999;">SKU: {over_pct:.1f}% | Qty: {over_forecast_pct:.1f}%</div>'
            f'</div>'
        )
        st.markdown(html_over, unsafe_allow_html=True)
    
    with col_total4:
        # Calculate overall accuracy for last month
        last_month_accuracy = monthly_performance[last_month]['accuracy']
        html_overall = (
            f'<div style="background: white; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #667eea;">'
            f'<div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">OVERALL</div>'
            f'<div style="font-size: 1.8rem; font-weight: 800; color: #667eea;">{last_month_accuracy:.1f}%</div>'
            f'<div style="font-size: 0.9rem; color: #888;">{last_month.strftime("%b %Y")}</div>'
            f'<div style="font-size: 0.8rem; color: #999;">Total SKUs: {total_count_last_month}</div>'
            f'</div>'
        )
        st.markdown(html_overall, unsafe_allow_html=True)
    
    # Summary stats for last month
    st.caption(f"""
    **Bulan {last_month.strftime('%b %Y')}:** Total Forecast: {total_forecast_qty:,.0f} | Total SKUs: {total_count_last_month} | Overall Accuracy: {last_month_accuracy:.1f}%
    """)
    
    # TOTAL ROFO DAN PO BULAN TERAKHIR
    if monthly_performance:
        last_month = sorted(monthly_performance.keys())[-1]
        last_month_data = monthly_performance[last_month]['data']
        
        total_rofo_last_month = last_month_data['Forecast_Qty'].sum()
        total_po_last_month = last_month_data['PO_Qty'].sum()
        selisih_qty = total_po_last_month - total_rofo_last_month
        selisih_persen = (selisih_qty / total_rofo_last_month * 100) if total_rofo_last_month > 0 else 0
    
        # ROW UNTUK TOTAL ROFO, PO, SALES - BULAN TERAKHIR
    st.divider()
    st.subheader("📈 Total Rofo vs PO vs Sales - Bulan Terakhir")
    
    # Hitung total sales untuk bulan terakhir
    total_sales_last_month = 0
    sales_vs_rofo_pct = 0
    sales_vs_po_pct = 0
    
    if not df_sales.empty and monthly_performance:
        last_month = sorted(monthly_performance.keys())[-1]
        df_sales_last_month = df_sales[df_sales['Month'] == last_month].copy()
        total_sales_last_month = df_sales_last_month['Sales_Qty'].sum()
        
        # Hitung persentase sales vs rofo
        if total_rofo_last_month > 0:
            sales_vs_rofo_pct = (total_sales_last_month / total_rofo_last_month * 100)
        
        # Hitung persentase sales vs po
        if total_po_last_month > 0:
            sales_vs_po_pct = (total_sales_last_month / total_po_last_month * 100)
    
    # Buat 6 columns untuk Rofo, PO, Sales dan persentasenya
    rofo_col1, rofo_col2, rofo_col3, rofo_col4, rofo_col5, rofo_col6 = st.columns(6)
    
    with rofo_col1:
        st.metric(
            "Total Rofo Qty",
            f"{total_rofo_last_month:,.0f}",
            help="Total quantity dari forecast/Rofo bulan terakhir"
        )
    
    with rofo_col2:
        st.metric(
            "Total PO Qty", 
            f"{total_po_last_month:,.0f}",
            help="Total quantity dari Purchase Order bulan terakhir"
        )
    
    with rofo_col3:
        st.metric(
            "Total Sales Qty",
            f"{total_sales_last_month:,.0f}",
            help="Total quantity dari Sales bulan terakhir"
        )
    
    with rofo_col4:
        # Sales vs Rofo %
        delta_sales_rofo = f"{sales_vs_rofo_pct-100:+.1f}%" if sales_vs_rofo_pct > 0 else "0%"
        st.metric(
            "Sales/Rofo %",
            f"{sales_vs_rofo_pct:.1f}%",
            delta=delta_sales_rofo,
            delta_color="normal" if 80 <= sales_vs_rofo_pct <= 120 else "off",
            help="Persentase Sales vs Rofo (100% = Sales = Rofo)"
        )
    
    with rofo_col5:
        # Sales vs PO %
        delta_sales_po = f"{sales_vs_po_pct-100:+.1f}%" if sales_vs_po_pct > 0 else "0%"
        st.metric(
            "Sales/PO %",
            f"{sales_vs_po_pct:.1f}%",
            delta=delta_sales_po,
            delta_color="normal" if 80 <= sales_vs_po_pct <= 120 else "off",
            help="Persentase Sales vs PO (100% = Sales = PO)"
        )
    
    with rofo_col6:
        # PO vs Rofo % (selisih PO-Rofo yang sudah ada)
        delta_po_rofo = f"{selisih_persen:+.1f}%"
        st.metric(
            "PO/Rofo %",
            f"{(total_po_last_month/total_rofo_last_month*100 if total_rofo_last_month > 0 else 0):.1f}%",
            delta=delta_po_rofo,
            delta_color="normal" if abs(selisih_persen) < 20 else "off",
            help="Persentase PO vs Rofo (100% = PO = Rofo)"
        )
    
    # Summary bar di bawah
    st.caption(f"""
    **Bulan {last_month.strftime('%b %Y')}:** 
    • **Rofo:** {total_rofo_last_month:,.0f} | 
    • **PO:** {total_po_last_month:,.0f} | 
    • **Sales:** {total_sales_last_month:,.0f} | 
    • **Sales/Rofo:** {sales_vs_rofo_pct:.1f}% | 
    • **Sales/PO:** {sales_vs_po_pct:.1f}% | 
    • **PO/Rofo:** {(total_po_last_month/total_rofo_last_month*100 if total_rofo_last_month > 0 else 0):.1f}%
    """)
else:
    st.warning("⚠️ Insufficient data for monthly performance analysis")

st.divider()
# SECTION 2: LAST MONTH EVALUATION (UNDER & OVER ONLY)
st.subheader("📋 Evaluasi Rofo - Bulan Terakhir (Under & Over Forecast)")

if monthly_performance:
    # Get last month data
    sorted_months = sorted(monthly_performance.keys())
    if sorted_months:
        last_month = sorted_months[-1]
        last_month_data = monthly_performance[last_month]
        last_month_name = last_month.strftime('%b %Y')
        
        # Create tabs for Under and Over SKUs
        eval_tab1, eval_tab2 = st.tabs([f"📉 UNDER Forecast ({last_month_name})", f"📈 OVER Forecast ({last_month_name})"])
        
        with eval_tab1:
            under_skus_df = last_month_data['under_skus']
            if not under_skus_df.empty:
                # Add inventory data
                if 'inventory_df' in inventory_metrics:
                    inventory_data = inventory_metrics['inventory_df'][['SKU_ID', 'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']]
                    under_skus_df = pd.merge(under_skus_df, inventory_data, on='SKU_ID', how='left')
                
                # TAMBAH: Get last 3 months sales data
                sales_cols_last_3 = []
                if not df_sales.empty:
                    # Get last 3 months from sales data
                    sales_months = sorted(df_sales['Month'].unique())
                    if len(sales_months) >= 3:
                        last_3_sales_months = sales_months[-3:]
                        
                        # Create pivot for last 3 months sales
                        try:
                            sales_pivot = df_sales[df_sales['Month'].isin(last_3_sales_months)].pivot_table(
                                index='SKU_ID',
                                columns='Month',
                                values='Sales_Qty',
                                aggfunc='sum',
                                fill_value=0
                            ).reset_index()
                            
                            # Rename columns to month names
                            month_rename = {}
                            for col in sales_pivot.columns:
                                if isinstance(col, datetime):
                                    month_rename[col] = col.strftime('%b-%Y')
                            sales_pivot = sales_pivot.rename(columns=month_rename)
                            
                            # Merge with under_skus_df
                            under_skus_df = pd.merge(
                                under_skus_df,
                                sales_pivot,
                                on='SKU_ID',
                                how='left'
                            )
                            
                            # Get the sales column names
                            sales_cols_last_3 = [col for col in sales_pivot.columns if isinstance(col, str) and '-' in col]
                            sales_cols_last_3 = sorted(sales_cols_last_3[-3:])  # Get last 3 months
                            
                        except Exception as e:
                            st.warning(f"Tidak bisa menambahkan data sales 3 bulan terakhir: {str(e)}")
                
                # Prepare display columns - TAMBAH sales columns
                display_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 'Accuracy_Status',
                              'Forecast_Qty', 'PO_Qty', 'PO_Rofo_Ratio', 
                              'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']
                
                # Tambah sales columns jika ada
                display_cols.extend(sales_cols_last_3)
                
                # Filter available columns
                available_cols = [col for col in display_cols if col in under_skus_df.columns]
                
                # Pastikan Product_Name selalu ada
                if 'Product_Name' not in available_cols and 'Product_Name' in under_skus_df.columns:
                    available_cols.insert(1, 'Product_Name')
                
                # Format the dataframe
                display_df = under_skus_df[available_cols].copy()
                
                # Add formatted columns
                if 'PO_Rofo_Ratio' in display_df.columns:
                    display_df['PO_Rofo_Ratio'] = display_df['PO_Rofo_Ratio'].apply(lambda x: f"{x:.1f}%")
                
                if 'Cover_Months' in display_df.columns:
                    display_df['Cover_Months'] = display_df['Cover_Months'].apply(lambda x: f"{x:.1f}" if x < 999 else "N/A")
                
                if 'Avg_Monthly_Sales_3M' in display_df.columns:
                    display_df['Avg_Monthly_Sales_3M'] = display_df['Avg_Monthly_Sales_3M'].apply(lambda x: f"{x:.0f}")
                
                # Format sales columns
                for col in sales_cols_last_3:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "0")
                
                # Rename columns for display
                column_names = {
                    'SKU_ID': 'SKU ID',
                    'Product_Name': 'Product Name',
                    'Brand': 'Brand',
                    'SKU_Tier': 'Tier',
                    'Accuracy_Status': 'Status',
                    'Forecast_Qty': 'Forecast Qty',
                    'PO_Qty': 'PO Qty',
                    'PO_Rofo_Ratio': 'PO/Rofo %',
                    'Stock_Qty': 'Stock Available',
                    'Avg_Monthly_Sales_3M': 'Avg Sales (3M)',
                    'Cover_Months': 'Cover (Months)'
                }
                
                # Add sales columns to rename dict
                for col in sales_cols_last_3:
                    column_names[col] = col
                
                display_df = display_df.rename(columns=column_names)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=500
                )
                
                # Summary dengan HIGHLIGHT
                total_forecast = under_skus_df['Forecast_Qty'].sum()
                total_po = under_skus_df['PO_Qty'].sum()
                avg_ratio = under_skus_df['PO_Rofo_Ratio'].mean()
                selisih_qty = total_po - total_forecast
                selisih_persen = (selisih_qty / total_forecast * 100) if total_forecast > 0 else 0
                po_rofo_pct = (total_po / total_forecast * 100) if total_forecast > 0 else 0
                
                # Buat HTML content
                html_content = f"""
                <div style="background: #FFEBEE; border-left: 5px solid #F44336; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h4 style="color: #C62828; margin-top: 0;">📉 UNDER FORECAST SUMMARY - {last_month_name}</h4>
                    
                    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 24px; color: #F44336; font-weight: bold; margin-bottom: 5px;">{avg_ratio:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">Avg PO/Rofo</div>
                            <div style="font-size: 10px; color: #999;">Target: 80-120%</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 22px; color: #2E7D32; font-weight: bold; margin-bottom: 5px;">{total_forecast:,.0f}</div>
                            <div style="font-size: 12px; color: #666;">Total Rofo</div>
                            <div style="font-size: 10px; color: #999;">Forecast Qty</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 22px; color: #1565C0; font-weight: bold; margin-bottom: 5px;">{total_po:,.0f}</div>
                            <div style="font-size: 12px; color: #666;">Total PO</div>
                            <div style="font-size: 10px; color: #999;">Purchase Order</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 24px; color: {'#F44336' if selisih_qty < 0 else '#2E7D32'}; font-weight: bold; margin-bottom: 5px;">{selisih_qty:+,.0f}</div>
                            <div style="font-size: 12px; color: #666;">Selisih Qty</div>
                            <div style="font-size: 11px; color: {'#F44336' if selisih_qty < 0 else '#2E7D32'}; font-weight: 600;">({selisih_persen:+.1f}%)</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 22px; color: #FF9800; font-weight: bold; margin-bottom: 5px;">{po_rofo_pct:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">PO/Rofo %</div>
                            <div style="font-size: 10px; color: #999;">Overall Ratio</div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(244, 67, 54, 0.3); font-size: 14px; color: #666;">
                        <strong>Total UNDER Forecast SKUs: {len(under_skus_df)}</strong> | 
                        <span style="color: #F44336;">Avg PO/Rofo: {avg_ratio:.1f}%</span> | 
                        <span style="color: #2E7D32;">Rofo: {total_forecast:,.0f}</span> | 
                        <span style="color: #1565C0;">PO: {total_po:,.0f}</span> | 
                        <span style="color: {'#F44336' if selisih_qty < 0 else '#2E7D32'}; font-weight: bold;">Selisih: {selisih_qty:+,.0f} ({selisih_persen:+.1f}%)</span>
                    </div>
                </div>
                """
                
                # Tampilkan dengan st.html()
                st.html(html_content)
            else:
                st.success(f"✅ No SKUs with UNDER forecast in {last_month_name}")
        
        with eval_tab2:
            over_skus_df = last_month_data['over_skus']
            if not over_skus_df.empty:
                # Add inventory data
                if 'inventory_df' in inventory_metrics:
                    inventory_data = inventory_metrics['inventory_df'][['SKU_ID', 'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']]
                    over_skus_df = pd.merge(over_skus_df, inventory_data, on='SKU_ID', how='left')
                
                # TAMBAH: Get last 3 months sales data
                sales_cols_last_3 = []
                if not df_sales.empty:
                    # Get last 3 months from sales data
                    sales_months = sorted(df_sales['Month'].unique())
                    if len(sales_months) >= 3:
                        last_3_sales_months = sales_months[-3:]
                        
                        # Create pivot for last 3 months sales
                        try:
                            sales_pivot = df_sales[df_sales['Month'].isin(last_3_sales_months)].pivot_table(
                                index='SKU_ID',
                                columns='Month',
                                values='Sales_Qty',
                                aggfunc='sum',
                                fill_value=0
                            ).reset_index()
                            
                            # Rename columns to month names
                            month_rename = {}
                            for col in sales_pivot.columns:
                                if isinstance(col, datetime):
                                    month_rename[col] = col.strftime('%b-%Y')
                            sales_pivot = sales_pivot.rename(columns=month_rename)
                            
                            # Merge with over_skus_df
                            over_skus_df = pd.merge(
                                over_skus_df,
                                sales_pivot,
                                on='SKU_ID',
                                how='left'
                            )
                            
                            # Get the sales column names
                            sales_cols_last_3 = [col for col in sales_pivot.columns if isinstance(col, str) and '-' in col]
                            sales_cols_last_3 = sorted(sales_cols_last_3[-3:])  # Get last 3 months
                            
                        except Exception as e:
                            st.warning(f"Tidak bisa menambahkan data sales 3 bulan terakhir: {str(e)}")
                
                # Prepare display columns - TAMBAH sales columns
                display_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 'Accuracy_Status',
                              'Forecast_Qty', 'PO_Qty', 'PO_Rofo_Ratio', 
                              'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']
                
                # Tambah sales columns jika ada
                display_cols.extend(sales_cols_last_3)
                
                # Filter available columns
                available_cols = [col for col in display_cols if col in over_skus_df.columns]
                
                # Pastikan Product_Name selalu ada
                if 'Product_Name' not in available_cols and 'Product_Name' in over_skus_df.columns:
                    available_cols.insert(1, 'Product_Name')
                
                # Format the dataframe
                display_df = over_skus_df[available_cols].copy()
                
                # Add formatted columns
                if 'PO_Rofo_Ratio' in display_df.columns:
                    display_df['PO_Rofo_Ratio'] = display_df['PO_Rofo_Ratio'].apply(lambda x: f"{x:.1f}%")
                
                if 'Cover_Months' in display_df.columns:
                    display_df['Cover_Months'] = display_df['Cover_Months'].apply(lambda x: f"{x:.1f}" if x < 999 else "N/A")
                
                if 'Avg_Monthly_Sales_3M' in display_df.columns:
                    display_df['Avg_Monthly_Sales_3M'] = display_df['Avg_Monthly_Sales_3M'].apply(lambda x: f"{x:.0f}")
                
                # Format sales columns
                for col in sales_cols_last_3:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "0")
                
                # Rename columns for display
                column_names = {
                    'SKU_ID': 'SKU ID',
                    'Product_Name': 'Product Name',
                    'Brand': 'Brand',
                    'SKU_Tier': 'Tier',
                    'Accuracy_Status': 'Status',
                    'Forecast_Qty': 'Forecast Qty',
                    'PO_Qty': 'PO Qty',
                    'PO_Rofo_Ratio': 'PO/Rofo %',
                    'Stock_Qty': 'Stock Available',
                    'Avg_Monthly_Sales_3M': 'Avg Sales (3M)',
                    'Cover_Months': 'Cover (Months)'
                }
                
                # Add sales columns to rename dict
                for col in sales_cols_last_3:
                    column_names[col] = col
                
                display_df = display_df.rename(columns=column_names)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=500
                )
                
                # Summary dengan HIGHLIGHT
                total_forecast = over_skus_df['Forecast_Qty'].sum()
                total_po = over_skus_df['PO_Qty'].sum()
                avg_ratio = over_skus_df['PO_Rofo_Ratio'].mean()
                selisih_qty = total_po - total_forecast
                selisih_persen = (selisih_qty / total_forecast * 100) if total_forecast > 0 else 0
                po_rofo_pct = (total_po / total_forecast * 100) if total_forecast > 0 else 0
                
                # Buat HTML content untuk OVER
                html_content_over = f"""
                <div style="background: #FFF3E0; border-left: 5px solid #FF9800; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h4 style="color: #EF6C00; margin-top: 0;">📈 OVER FORECAST SUMMARY - {last_month_name}</h4>
                    
                    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 24px; color: #FF9800; font-weight: bold; margin-bottom: 5px;">{avg_ratio:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">Avg PO/Rofo</div>
                            <div style="font-size: 10px; color: #999;">Target: 80-120%</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 22px; color: #2E7D32; font-weight: bold; margin-bottom: 5px;">{total_forecast:,.0f}</div>
                            <div style="font-size: 12px; color: #666;">Total Rofo</div>
                            <div style="font-size: 10px; color: #999;">Forecast Qty</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 22px; color: #1565C0; font-weight: bold; margin-bottom: 5px;">{total_po:,.0f}</div>
                            <div style="font-size: 12px; color: #666;">Total PO</div>
                            <div style="font-size: 10px; color: #999;">Purchase Order</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 24px; color: {'#F44336' if selisih_qty < 0 else '#2E7D32'}; font-weight: bold; margin-bottom: 5px;">{selisih_qty:+,.0f}</div>
                            <div style="font-size: 12px; color: #666;">Selisih Qty</div>
                            <div style="font-size: 11px; color: {'#F44336' if selisih_qty < 0 else '#2E7D32'}; font-weight: 600;">({selisih_persen:+.1f}%)</div>
                        </div>
                        
                        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="font-size: 22px; color: #FF9800; font-weight: bold; margin-bottom: 5px;">{po_rofo_pct:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">PO/Rofo %</div>
                            <div style="font-size: 10px; color: #999;">Overall Ratio</div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 152, 0, 0.3); font-size: 14px; color: #666;">
                        <strong>Total OVER Forecast SKUs: {len(over_skus_df)}</strong> | 
                        <span style="color: #FF9800;">Avg PO/Rofo: {avg_ratio:.1f}%</span> | 
                        <span style="color: #2E7D32;">Rofo: {total_forecast:,.0f}</span> | 
                        <span style="color: #1565C0;">PO: {total_po:,.0f}</span> | 
                        <span style="color: {'#F44336' if selisih_qty < 0 else '#2E7D32'}; font-weight: bold;">Selisih: {selisih_qty:+,.0f} ({selisih_persen:+.1f}%)</span>
                    </div>
                </div>
                """
                
                # Tampilkan dengan st.html()
                st.html(html_content_over)
            else:
                st.success(f"✅ No SKUs with OVER forecast in {last_month_name}")

st.divider()

# --- MAIN TABS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📈 Monthly Performance Details",
    "🏷️ Forecast Performance by Brand & Tier Analysis",
    "📦 Inventory Analysis",
    "🔍 SKU Evaluation",
    "📈 Sales & Forecast Analysis",
    "📋 Data Explorer",
    "🛒 Ecommerce Forecast",  # Diubah dari "🔮 Forecast Generator"
    "💰 Profitability Analysis",
    "🤝 Reseller Forecast"  # <-- TAB BARU
])

# --- TAB 1: MONTHLY PERFORMANCE DETAILS ---
with tab1:
    st.subheader("📅 Monthly Performance Details")
    
    if monthly_performance:
        # Create monthly performance summary table
        summary_data = []
        for month, data in sorted(monthly_performance.items()):
            summary_data.append({
                'Month': month.strftime('%b %Y'),
                'Accuracy (%)': data['accuracy'],
                'Under': data['status_counts'].get('Under', 0),
                'Accurate': data['status_counts'].get('Accurate', 0),
                'Over': data['status_counts'].get('Over', 0),
                'Total SKUs': data['total_records'],
                'MAPE': data['mape']
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Display summary table
        st.dataframe(
            summary_df,
            column_config={
                "Accuracy (%)": st.column_config.ProgressColumn(
                    "Accuracy %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                ),
                "MAPE": st.column_config.NumberColumn("MAPE %", format="%.1f%%")
            },
            use_container_width=True,
            height=400
        )
        
        # Add forecast bias analysis if available
        if not forecast_bias.empty:
            st.divider()
            st.subheader("📉 Forecast Bias Analysis")
            
            fig_bias = go.Figure()
            fig_bias.add_trace(go.Bar(
                x=forecast_bias['Month'].dt.strftime('%b-%Y'),
                y=forecast_bias['Avg_Bias_Percentage'],
                name='Forecast Bias %',
                marker_color=forecast_bias['Avg_Bias_Percentage'].apply(
                    lambda x: '#4CAF50' if x >= -10 and x <= 10 else '#FF9800' if x >= -20 and x <= 20 else '#F44336'
                )
            ))
            
            fig_bias.update_layout(
                height=300,
                title='Monthly Forecast Bias (Positive = Over-forecast, Negative = Under-forecast)',
                xaxis_title='Month',
                yaxis_title='Bias %'
            )
            
            st.plotly_chart(fig_bias, use_container_width=True)

# --- TAB 2: FORECAST PERFORMANCE BY BRAND & TIER ANALYSIS ---
with tab2:
    # Brand Performance Analysis
    st.subheader("🏷️ Forecast Performance by Brand")
    
    brand_performance = calculate_brand_performance(df_forecast, df_po, df_product)
    
    if not brand_performance.empty:
        # ================ KPI CARDS SECTION ================
        st.subheader("📊 Brand Performance KPIs")
        
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        with col_kpi1:
            # Best accuracy brand
            best_acc = brand_performance.loc[brand_performance['Accuracy'].idxmax()]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); 
                        border-radius: 10px; padding: 1rem; margin: 0.5rem 0; 
                        border-left: 5px solid #4CAF50;">
                <div style="font-size: 0.9rem; color: #2E7D32; font-weight: 600;">🎯 Best Accuracy</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #1B5E20;">{best_acc['Brand']}</div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                    <span style="font-size: 0.8rem; color: #666;">Accuracy:</span>
                    <span style="font-size: 1rem; font-weight: 700; color: #1B5E20;">{best_acc['Accuracy']:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_kpi2:
            # Most SKUs brand
            most_skus = brand_performance.loc[brand_performance['SKU_Count'].idxmax()]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                        border-radius: 10px; padding: 1rem; margin: 0.5rem 0; 
                        border-left: 5px solid #2196F3;">
                <div style="font-size: 0.9rem; color: #1565C0; font-weight: 600;">📦 Most SKUs</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #0D47A1;">{most_skus['Brand']}</div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                    <span style="font-size: 0.8rem; color: #666;">SKUs:</span>
                    <span style="font-size: 1rem; font-weight: 700; color: #0D47A1;">{most_skus['SKU_Count']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_kpi3:
            # Highest volume brand
            highest_rofo = brand_performance.loc[brand_performance['Total_Forecast'].idxmax()]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%); 
                        border-radius: 10px; padding: 1rem; margin: 0.5rem 0; 
                        border-left: 5px solid #9C27B0;">
                <div style="font-size: 0.9rem; color: #7B1FA2; font-weight: 600;">📈 Highest Volume</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #4A148C;">{highest_rofo['Brand']}</div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                    <span style="font-size: 0.8rem; color: #666;">Rofo Qty:</span>
                    <span style="font-size: 1rem; font-weight: 700; color: #4A148C;">{highest_rofo['Total_Forecast']:,.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ================ FINANCIAL ANALYSIS PER BRAND ================
        st.divider()
        st.subheader("💰 Brand Financial Performance")
        
        if not df_financial.empty:
            brand_financial = df_financial.groupby('Brand').agg({
                'Revenue': 'sum',
                'Gross_Margin': 'sum',
                'Sales_Qty': 'sum'
            }).reset_index()
            
            brand_financial['Margin_Percentage'] = np.where(
                brand_financial['Revenue'] > 0,
                (brand_financial['Gross_Margin'] / brand_financial['Revenue'] * 100),
                0
            )
            
            brand_financial = brand_financial.sort_values('Gross_Margin', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    brand_financial.head(10),
                    column_config={
                        "Revenue": st.column_config.NumberColumn("Revenue", format="Rp  %.0f"),
                        "Gross_Margin": st.column_config.NumberColumn("Gross Margin", format="Rp  %.0f"),
                        "Margin_Percentage": st.column_config.ProgressColumn("Margin %", format="%.1f%%", min_value=0, max_value=100)
                    },
                    use_container_width=True
                )
            
            with col2:
                # Chart brand profitability
                fig = px.bar(brand_financial.head(10), x='Brand', y='Margin_Percentage',
                            title='Top 10 Brands by Margin %',
                            color='Margin_Percentage',
                            color_continuous_scale='RdYlGn')
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # ================ DATA TABLE SECTION ================
        st.divider()
        st.subheader("📋 Brand Performance Data")
        
        # Format the display
        display_brand_df = brand_performance.copy()
        
        # Format columns
        display_brand_df['Accuracy'] = display_brand_df['Accuracy'].apply(lambda x: f"{x:.1f}%")
        display_brand_df['PO_vs_Forecast_Ratio'] = display_brand_df['PO_vs_Forecast_Ratio'].apply(lambda x: f"{x:.1f}%")
        display_brand_df['Total_Forecast'] = display_brand_df['Total_Forecast'].apply(lambda x: f"{x:,.0f}")
        display_brand_df['Total_PO'] = display_brand_df['Total_PO'].apply(lambda x: f"{x:,.0f}")
        display_brand_df['Qty_Difference'] = display_brand_df['Qty_Difference'].apply(lambda x: f"{x:+,.0f}")
        
        # Rename columns
        column_names = {
            'Brand': 'Brand',
            'SKU_Count': 'SKU Count',
            'Total_Forecast': 'Total Rofo',
            'Total_PO': 'Total PO',
            'Accuracy': 'Accuracy %',
            'PO_vs_Forecast_Ratio': 'PO/Rofo %',
            'Qty_Difference': 'Qty Diff',
            'Under': 'Under',
            'Accurate': 'Accurate',
            'Over': 'Over'
        }
        
        display_brand_df = display_brand_df.rename(columns=column_names)
        
        # Display table
        st.dataframe(
            display_brand_df,
            use_container_width=True,
            height=400
        )
        
        # ================ GROUPED BAR CHART SECTION ================
        st.divider()
        st.subheader("📊 Brand Performance Comparison")
        
        # PENTING: Cari bulan terakhir yang ADA DATA SALES-nya
        sales_months = sorted(df_sales['Month'].unique()) if not df_sales.empty else []
        forecast_months = sorted(df_forecast['Month'].unique()) if not df_forecast.empty else []
        po_months = sorted(df_po['Month'].unique()) if not df_po.empty else []
        
        # Cari bulan terakhir yang ADA di ketiga dataset
        common_months = sorted(set(sales_months) & set(forecast_months) & set(po_months))
        if common_months:
            last_month = common_months[-1]
        else:
            # Kalau ngga ada bulan yang sama, ambil bulan terakhir dari forecast saja
            last_month = forecast_months[-1] if forecast_months else None
        
        if last_month:
            st.caption(f"📅 Data untuk bulan: {last_month.strftime('%b %Y')}")
            
            # Get data untuk bulan terakhir
            df_forecast_last = df_forecast[df_forecast['Month'] == last_month]
            df_po_last = df_po[df_po['Month'] == last_month]
            df_sales_last = df_sales[df_sales['Month'] == last_month]
            
            # Debug info
            st.caption(f"Forecast SKUs: {len(df_forecast_last)} | PO SKUs: {len(df_po_last)} | Sales SKUs: {len(df_sales_last)}")
            
            # Add product info
            df_forecast_last = add_product_info_to_data(df_forecast_last, df_product)
            df_po_last = add_product_info_to_data(df_po_last, df_product)
            df_sales_last = add_product_info_to_data(df_sales_last, df_product)
            
            if 'Brand' in df_forecast_last.columns:
                # Get UNIQUE BRANDS dari semua dataset
                forecast_brands = set(df_forecast_last['Brand'].dropna().unique())
                po_brands = set(df_po_last['Brand'].dropna().unique()) if 'Brand' in df_po_last.columns else set()
                sales_brands = set(df_sales_last['Brand'].dropna().unique()) if 'Brand' in df_sales_last.columns else set()
                
                # Gabungkan semua brand
                all_brands = forecast_brands.union(po_brands).union(sales_brands)
                
                brand_comparison = []
                
                for brand in sorted(all_brands):
                    # Forecast
                    rofo_qty = df_forecast_last[df_forecast_last['Brand'] == brand]['Forecast_Qty'].sum()
                    
                    # PO
                    po_qty = df_po_last[df_po_last['Brand'] == brand]['PO_Qty'].sum() if 'Brand' in df_po_last.columns else 0
                    
                    # Sales
                    sales_qty = 0
                    if not df_sales_last.empty and 'Brand' in df_sales_last.columns:
                        sales_qty = df_sales_last[df_sales_last['Brand'] == brand]['Sales_Qty'].sum()
                    
                    brand_comparison.append({
                        'Brand': brand,
                        'Rofo': rofo_qty,
                        'PO': po_qty,
                        'Sales': sales_qty,
                        'PO_Rofo_Ratio': (po_qty / rofo_qty * 100) if rofo_qty > 0 else 0
                    })
                
                comparison_df = pd.DataFrame(brand_comparison)
                
                # TAMPILKAN SEMUA BRAND (tanpa .head())
                comparison_df = comparison_df.sort_values('Rofo', ascending=False)
                
                # Tampilkan jumlah brand
                st.caption(f"📊 Menampilkan {len(comparison_df)} brand")
                
                # Cek apakah ada data Sales
                total_sales = comparison_df['Sales'].sum()
                
                if total_sales > 0:
                    # Buat chart dengan 3 bar (Rofo, PO, Sales)
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=comparison_df['Brand'],
                        y=comparison_df['Rofo'],
                        name='Rofo',
                        marker_color='#667eea',
                        hovertemplate='<b>%{x}</b><br>Rofo: %{y:,.0f}<extra></extra>'
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=comparison_df['Brand'],
                        y=comparison_df['PO'],
                        name='PO',
                        marker_color='#FF9800',
                        hovertemplate='<b>%{x}</b><br>PO: %{y:,.0f}<extra></extra>'
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=comparison_df['Brand'],
                        y=comparison_df['Sales'],
                        name='Sales',
                        marker_color='#4CAF50',
                        hovertemplate='<b>%{x}</b><br>Sales: %{y:,.0f}<extra></extra>'
                    ))
                    
                    chart_title = f'Brand Performance - {last_month.strftime("%b %Y")} (Rofo vs PO vs Sales)'
                else:
                    # Kalau ngga ada Sales, tampilkan cuma Rofo vs PO
                    st.info("ℹ️ Data Sales tidak tersedia untuk bulan ini, menampilkan Rofo vs PO saja")
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=comparison_df['Brand'],
                        y=comparison_df['Rofo'],
                        name='Rofo',
                        marker_color='#667eea',
                        hovertemplate='<b>%{x}</b><br>Rofo: %{y:,.0f}<extra></extra>'
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=comparison_df['Brand'],
                        y=comparison_df['PO'],
                        name='PO',
                        marker_color='#FF9800',
                        hovertemplate='<b>%{x}</b><br>PO: %{y:,.0f}<extra></extra>'
                    ))
                    
                    chart_title = f'Brand Performance - {last_month.strftime("%b %Y")} (Rofo vs PO)'
                
                fig.update_layout(
                    height=500,
                    title=chart_title,
                    xaxis_title='Brand',
                    yaxis_title='Quantity',
                    barmode='group',
                    hovermode='x unified',
                    plot_bgcolor='white',
                    xaxis={'categoryorder': 'total descending'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # ================ ACCURACY VISUALIZATION SECTION ================
        st.divider()
        st.subheader("🎯 Brand Accuracy Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gauge chart for top brand accuracy
            if 'comparison_df' in locals() and not comparison_df.empty:
                top_brand = comparison_df.iloc[0]
                
                # Hitung accuracy untuk top brand
                top_accuracy = 0
                if top_brand['Rofo'] > 0:
                    top_accuracy = 100 - abs(top_brand['PO_Rofo_Ratio'] - 100)
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=top_accuracy,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': f"Top Brand: {top_brand['Brand']}"},
                    delta={'reference': 80, 'increasing': {'color': "green"}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1},
                        'bar': {'color': "#667eea"},
                        'steps': [
                            {'range': [0, 70], 'color': "#FF5252"},
                            {'range': [70, 85], 'color': "#FF9800"},
                            {'range': [85, 100], 'color': "#4CAF50"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 80
                        }
                    }
                ))
                
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            # Horizontal bar chart for accuracy ranking
            if 'comparison_df' in locals() and not comparison_df.empty:
                # Hitung accuracy untuk semua brand
                comparison_df['Accuracy'] = comparison_df.apply(
                    lambda row: 100 - abs(row['PO_Rofo_Ratio'] - 100) if row['Rofo'] > 0 else 0,
                    axis=1
                )
                
                accuracy_sorted = comparison_df.sort_values('Accuracy', ascending=True)
                
                fig_accuracy = go.Figure()
                
                fig_accuracy.add_trace(go.Bar(
                    y=accuracy_sorted['Brand'],
                    x=accuracy_sorted['Accuracy'],
                    orientation='h',
                    marker_color=accuracy_sorted['Accuracy'].apply(
                        lambda x: '#4CAF50' if x >= 80 else '#FF9800' if x >= 70 else '#FF5252'
                    ),
                    text=accuracy_sorted['Accuracy'].apply(lambda x: f"{x:.1f}%"),
                    textposition='outside'
                ))
                
                fig_accuracy.update_layout(
                    height=300,
                    title='Brand Accuracy Ranking',
                    xaxis_title='Accuracy (%)',
                    yaxis_title='Brand',
                    xaxis_range=[0, 100]
                )
                
                st.plotly_chart(fig_accuracy, use_container_width=True)
        
        # ================ HEATMAP SECTION ================
        st.divider()
        st.subheader("📊 Brand Performance Status Heatmap")
        
        # Prepare data for heatmap
        status_data = []
        for _, row in display_brand_df.iterrows():
            brand = row['Brand']
            total_skus = int(str(row['SKU Count']).replace(',', ''))
            under = int(row['Under']) if pd.notnull(row['Under']) else 0
            accurate = int(row['Accurate']) if pd.notnull(row['Accurate']) else 0
            over = int(row['Over']) if pd.notnull(row['Over']) else 0
            
            status_data.append({
                'Brand': brand,
                'Under': (under/total_skus*100) if total_skus > 0 else 0,
                'Accurate': (accurate/total_skus*100) if total_skus > 0 else 0,
                'Over': (over/total_skus*100) if total_skus > 0 else 0
            })
        
        status_df = pd.DataFrame(status_data)
        status_df = status_df.sort_values('Accurate', ascending=False)
        
        fig_heatmap = go.Figure()
        
        fig_heatmap.add_trace(go.Heatmap(
            z=[status_df['Under'], status_df['Accurate'], status_df['Over']],
            x=status_df['Brand'].tolist(),
            y=['Under %', 'Accurate %', 'Over %'],
            colorscale=[[0, '#FF5252'], [0.5, '#FF9800'], [1, '#4CAF50']],
            text=np.round([status_df['Under'], status_df['Accurate'], status_df['Over']], 1),
            texttemplate='%{text:.1f}%',
            hovertemplate='<b>%{y}</b><br>Brand: %{x}<br>Percentage: %{text:.1f}%<extra></extra>'
        ))
        
        fig_heatmap.update_layout(
            height=400,
            title='Brand Performance Distribution',
            xaxis_title='Brand',
            yaxis_title='Performance Status'
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # ================ SCATTER PLOT SECTION ================
        st.divider()
        st.subheader("🔍 Brand Performance Scatter Analysis")
        
        # Prepare data for scatter plot
        scatter_data = brand_performance.copy()
        
        # Create scatter plot
        fig_scatter = px.scatter(
            scatter_data,
            x='Total_Forecast',
            y='Accuracy',
            size='SKU_Count',
            color='PO_vs_Forecast_Ratio',
            hover_name='Brand',
            hover_data=['SKU_Count', 'Total_PO', 'Under', 'Accurate', 'Over'],
            title='Brand Performance: Accuracy vs Forecast Volume',
            labels={
                'Total_Forecast': 'Total Forecast Volume',
                'Accuracy': 'Forecast Accuracy (%)',
                'SKU_Count': 'Number of SKUs',
                'PO_vs_Forecast_Ratio': 'PO/Rofo Ratio (%)'
            },
            color_continuous_scale='RdYlGn',
            size_max=50
        )
        
        # Add quadrant lines
        fig_scatter.add_hline(y=80, line_dash="dash", line_color="gray", 
                             annotation_text="Accuracy Target (80%)")
        fig_scatter.add_vline(x=scatter_data['Total_Forecast'].median(), 
                             line_dash="dash", line_color="gray",
                             annotation_text="Median Volume")
        
        fig_scatter.update_layout(
            height=500,
            xaxis_title='Total Forecast Volume (log scale)',
            xaxis_type='log',
            plot_bgcolor='white'
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Quadrant analysis
        st.subheader("📊 Brand Performance Quadrants")
        
        # Calculate quadrant metrics
        median_volume = scatter_data['Total_Forecast'].median()
        
        quadrants = {
            'High Accuracy, High Volume': scatter_data[
                (scatter_data['Accuracy'] >= 80) & 
                (scatter_data['Total_Forecast'] >= median_volume)
            ],
            'High Accuracy, Low Volume': scatter_data[
                (scatter_data['Accuracy'] >= 80) & 
                (scatter_data['Total_Forecast'] < median_volume)
            ],
            'Low Accuracy, High Volume': scatter_data[
                (scatter_data['Accuracy'] < 80) & 
                (scatter_data['Total_Forecast'] >= median_volume)
            ],
            'Low Accuracy, Low Volume': scatter_data[
                (scatter_data['Accuracy'] < 80) & 
                (scatter_data['Total_Forecast'] < median_volume)
            ]
        }
        
        # Display quadrant summary
        quad_cols = st.columns(4)
        quad_colors = ['#4CAF50', '#8BC34A', '#FF9800', '#F44336']
        
        for idx, (quadrant_name, quadrant_data) in enumerate(quadrants.items()):
            with quad_cols[idx]:
                count = len(quadrant_data)
                percent = (count / len(scatter_data) * 100) if len(scatter_data) > 0 else 0
                
                # Get top brand in quadrant
                top_brand = quadrant_data.iloc[0]['Brand'] if not quadrant_data.empty else "N/A"
                
                st.markdown(f"""
                <div style="background: white; border-radius: 10px; padding: 1rem; 
                            margin: 0.5rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                            border-left: 5px solid {quad_colors[idx]};">
                    <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.5rem;">
                        {quadrant_name}
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #333;">
                        {count}
                    </div>
                    <div style="font-size: 0.8rem; color: #888; margin-top: 0.3rem;">
                        {percent:.1f}% of brands
                    </div>
                    <div style="font-size: 0.7rem; color: #999; margin-top: 0.5rem; border-top: 1px solid #eee; padding-top: 0.3rem;">
                        Top: {top_brand}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
    else:
        st.info("📊 No brand performance data available")
    
    st.divider()
    
    # ================ TIER ANALYSIS SECTION ================
    st.subheader("🏷️ SKU Tier Analysis")
    
    if monthly_performance and not df_product.empty:
        # Get last month data for tier analysis
        last_month = sorted(monthly_performance.keys())[-1]
        last_month_data = monthly_performance[last_month]['data']
        
        # Tier analysis
        if 'SKU_Tier' in last_month_data.columns:
            tier_summary = last_month_data.groupby('SKU_Tier').agg({
                'SKU_ID': 'count',
                'PO_Rofo_Ratio': 'mean',
                'Forecast_Qty': 'sum',
                'PO_Qty': 'sum'
            }).reset_index()
            
            tier_summary.columns = ['Tier', 'SKU Count', 'Avg PO/Rofo %', 'Total Forecast', 'Total PO']
            tier_summary['Avg PO/Rofo %'] = tier_summary['Avg PO/Rofo %'].apply(lambda x: f"{x:.1f}%")
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.dataframe(
                    tier_summary,
                    use_container_width=True,
                    height=300
                )
            
            with col_t2:
                # Pie chart for tier distribution
                fig_pie = go.Figure(data=[go.Pie(
                    labels=tier_summary['Tier'],
                    values=tier_summary['SKU Count'],
                    hole=0.3,
                    marker_colors=['#667eea', '#FF9800', '#4CAF50', '#FF5252', '#9C27B0'],
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>SKUs: %{value}<br>%{percent}<extra></extra>'
                )])
                
                fig_pie.update_layout(
                    height=300,
                    title='SKU Distribution by Tier',
                    showlegend=False
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Tier Performance Comparison
            st.subheader("📈 Tier Performance Comparison")
            
            # Prepare data for radar chart
            tiers = tier_summary['Tier'].tolist()
            accuracy_values = []
            po_rofo_values = []
            
            for tier in tiers:
                tier_data = last_month_data[last_month_data['SKU_Tier'] == tier]
                if not tier_data.empty:
                    # Calculate accuracy
                    accuracy = 100 - abs(tier_data['PO_Rofo_Ratio'] - 100).mean()
                    accuracy_values.append(accuracy)
                    
                    # Calculate PO/Rofo ratio
                    po_rofo = (tier_data['PO_Qty'].sum() / tier_data['Forecast_Qty'].sum() * 100) if tier_data['Forecast_Qty'].sum() > 0 else 0
                    po_rofo_values.append(po_rofo)
            
            # Radar chart
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=accuracy_values,
                theta=tiers,
                fill='toself',
                name='Accuracy %',
                line_color='#667eea',
                fillcolor='rgba(102, 126, 234, 0.3)'
            ))
            
            fig_radar.add_trace(go.Scatterpolar(
                r=po_rofo_values,
                theta=tiers,
                fill='toself',
                name='PO/Rofo %',
                line_color='#FF9800',
                fillcolor='rgba(255, 152, 0, 0.3)'
            ))
            
            fig_radar.update_layout(
                height=400,
                title='Tier Performance Radar Chart',
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(max(accuracy_values), max(po_rofo_values)) * 1.1]
                    )
                ),
                showlegend=True
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
        
        # Inventory tier analysis
        if 'tier_analysis' in inventory_metrics:
            st.divider()
            st.subheader("📦 Inventory by Tier")
            
            tier_inv = inventory_metrics['tier_analysis']
            
            # Treemap for inventory distribution
            fig_treemap = px.treemap(
                tier_inv,
                path=['Tier'],
                values='Total_Stock',
                color='Avg_Cover_Months',
                color_continuous_scale='RdYlGn',
                title='Inventory Distribution by Tier (Size = Total Stock, Color = Cover Months)',
                hover_data=['SKU_Count', 'Total_Sales_3M_Avg', 'Turnover']
            )
            
            fig_treemap.update_layout(height=400)
            st.plotly_chart(fig_treemap, use_container_width=True)
            
            # Additional metrics
            col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
            
            with col_metrics1:
                if not tier_inv.empty:
                    best_tier = tier_inv.loc[tier_inv['Turnover'].idxmax()]
                    st.metric(
                        "Highest Turnover Tier",
                        best_tier['Tier'],
                        delta=f"{best_tier['Turnover']:.2f} Turnover"
                    )
            
            with col_metrics2:
                if not tier_inv.empty:
                    best_cover = tier_inv.loc[tier_inv['Avg_Cover_Months'].idxmax()]
                    st.metric(
                        "Highest Cover Tier",
                        best_cover['Tier'],
                        delta=f"{best_cover['Avg_Cover_Months']:.1f} months"
                    )
            
            with col_metrics3:
                if not tier_inv.empty:
                    total_stock = tier_inv['Total_Stock'].sum()
                    st.metric("Total Stock All Tiers", f"{total_stock:,.0f}")
            
            with col_metrics4:
                if not tier_inv.empty:
                    avg_cover = tier_inv['Avg_Cover_Months'].mean()
                    st.metric("Average Cover All Tiers", f"{avg_cover:.1f} months")

# --- TAB 3: INVENTORY ANALYSIS ---
with tab3:
    st.subheader("📦 Inventory Analysis dengan 3-Month Average Sales")
    
    if inventory_metrics:
        # Inventory status cards
        inv_df = inventory_metrics['inventory_df']
        
        if 'Inventory_Status' in inv_df.columns:
            status_counts = inv_df['Inventory_Status'].value_counts().to_dict()
            total_skus = len(inv_df)
            
            col_i1, col_i2, col_i3 = st.columns(3)
            
            with col_i1:
                need_count = status_counts.get('Need Replenishment', 0)
                need_pct = (need_count / total_skus * 100) if total_skus > 0 else 0
                st.markdown(f"""
                <div class="inventory-card card-replenish">
                    <div style="font-size: 1rem; font-weight: 800;">NEED REPLENISHMENT</div>
                    <div style="font-size: 1.8rem; font-weight: 900;">{need_pct:.1f}%</div>
                    <div style="font-size: 0.9rem;">{need_count} SKUs (Cover < 0.8 months)</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_i2:
                ideal_count = status_counts.get('Ideal/Healthy', 0)
                ideal_pct = (ideal_count / total_skus * 100) if total_skus > 0 else 0
                st.markdown(f"""
                <div class="inventory-card card-ideal">
                    <div style="font-size: 1rem; font-weight: 800;">IDEAL/HEALTHY</div>
                    <div style="font-size: 1.8rem; font-weight: 900;">{ideal_pct:.1f}%</div>
                    <div style="font-size: 0.9rem;">{ideal_count} SKUs (0.8-1.5 months)</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_i3:
                high_count = status_counts.get('High Stock', 0)
                high_pct = (high_count / total_skus * 100) if total_skus > 0 else 0
                st.markdown(f"""
                <div class="inventory-card card-high">
                    <div style="font-size: 1rem; font-weight: 800;">HIGH STOCK</div>
                    <div style="font-size: 1.8rem; font-weight: 900;">{high_pct:.1f}%</div>
                    <div style="font-size: 0.9rem;">{high_count} SKUs (Cover > 1.5 months)</div>
                </div>
                """, unsafe_allow_html=True)
        
        # ================ INVENTORY FINANCIAL VALUE ================
        st.divider()
        st.subheader("💵 Inventory Financial Value")
        
        if not df_inventory_financial.empty:
            total_cost_value = df_inventory_financial['Value_at_Cost'].sum()
            total_retail_value = df_inventory_financial['Value_at_Retail'].sum()
            total_potential_margin = df_inventory_financial['Potential_Margin'].sum()
            avg_margin_pct = (total_potential_margin / total_retail_value * 100) if total_retail_value > 0 else 0
            
            col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
            
            with col_fin1:
                st.metric("Inventory @ Cost", f"Rp {total_cost_value:,.0f}")
            
            with col_fin2:
                st.metric("Inventory @ Retail", f"Rp {total_retail_value:,.0f}")
            
            with col_fin3:
                st.metric("Potential Margin", f"Rp {total_potential_margin:,.0f}")
            
            with col_fin4:
                st.metric("Avg Margin %", f"{avg_margin_pct:.1f}%")
            
            # High value inventory items
            high_value_items = df_inventory_financial.sort_values('Value_at_Cost', ascending=False).head(10)
            
            st.markdown("#### 📊 Top 10 Highest Value Inventory Items")
            
            # Tampilkan kolom yang tersedia
            display_cols_high_value = []
            for col in ['SKU_ID', 'Product_Name', 'Brand', 'Stock_Qty', 
                       'Value_at_Cost', 'Value_at_Retail', 'Potential_Margin']:
                if col in high_value_items.columns:
                    display_cols_high_value.append(col)
            
            if display_cols_high_value:
                st.dataframe(
                    high_value_items[display_cols_high_value],
                    column_config={
                        "Value_at_Cost": st.column_config.NumberColumn("Value @ Cost", format="Rp  %.0f"),
                        "Value_at_Retail": st.column_config.NumberColumn("Value @ Retail", format="Rp  %.0f"),
                        "Potential_Margin": st.column_config.NumberColumn("Potential Margin", format="Rp  %.0f")
                    } if 'Value_at_Cost' in display_cols_high_value else {},
                    use_container_width=True
                )
            else:
                st.warning("No financial data available for display")
            
            # ================ INVENTORY RISK ANALYSIS ================
            st.divider()
            st.subheader("⚠️ Inventory Risk Analysis")
            
            # Identify high-risk items (high value + slow moving)
            if 'inventory_df' in inventory_metrics:
                # Gabungkan inventory metrics dengan financial data
                df_inv_risk = pd.merge(
                    inventory_metrics['inventory_df'][['SKU_ID', 'Cover_Months', 'Avg_Monthly_Sales_3M', 'Inventory_Status']],
                    df_inventory_financial[['SKU_ID', 'Value_at_Cost', 'Value_at_Retail', 'Potential_Margin']],
                    on='SKU_ID',
                    how='left'
                )
                
                # Pastikan Product_Name ada
                if 'Product_Name' not in df_inv_risk.columns:
                    df_inv_risk = add_product_info_to_data(df_inv_risk, df_product)
                
                # Flag high risk items
                high_risk_condition = (
                    (df_inv_risk['Cover_Months'] > 3) &  # Slow moving (>3 months cover)
                    (df_inv_risk['Value_at_Cost'] > 1000)  # High value (>Rp 1000)
                )
                
                # Filter hanya jika kolomnya ada
                if 'Cover_Months' in df_inv_risk.columns and 'Value_at_Cost' in df_inv_risk.columns:
                    high_risk = df_inv_risk[high_risk_condition].sort_values('Value_at_Cost', ascending=False)
                else:
                    high_risk = pd.DataFrame()  # Empty dataframe jika kolom tidak ada
                
                if not high_risk.empty:
                    st.warning(f"⚠️ **{len(high_risk)} high-value slow-moving items detected**")
                    
                    # Pilih kolom yang tersedia untuk ditampilkan
                    display_cols_risk = []
                    for col in ['SKU_ID', 'Product_Name', 'Cover_Months', 'Value_at_Cost', 'Inventory_Status']:
                        if col in high_risk.columns:
                            display_cols_risk.append(col)
                    
                    if display_cols_risk:
                        st.dataframe(
                            high_risk[display_cols_risk],
                            use_container_width=True
                        )
                    else:
                        st.warning("No display columns available for risk items")
                else:
                    st.success("✅ No high-risk inventory items detected")
        
        st.divider()
        
        # ================ DETAILED INVENTORY TABLE ================
        st.subheader("📋 Detailed Inventory Status")
        
        # Filter options
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=['Need Replenishment', 'Ideal/Healthy', 'High Stock'],
                default=['Need Replenishment', 'High Stock'],
                key="inv_status_filter"
            )
        
        with col_f2:
            tier_options = inv_df['SKU_Tier'].unique().tolist() if 'SKU_Tier' in inv_df.columns else []
            tier_filter = st.multiselect(
                "Filter by Tier",
                options=tier_options,
                default=tier_options,
                key="inv_tier_filter"
            )
        
        with col_f3:
            brand_options = inv_df['Brand'].unique().tolist() if 'Brand' in inv_df.columns else []
            brand_filter = st.multiselect(
                "Filter by Brand",
                options=brand_options,
                default=brand_options,
                key="inv_brand_filter"
            )
        
        # Apply filters
        filtered_df = inv_df.copy()
        
        if status_filter:
            filtered_df = filtered_df[filtered_df['Inventory_Status'].isin(status_filter)]
        
        if tier_filter and 'SKU_Tier' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['SKU_Tier'].isin(tier_filter)]
        
        if brand_filter and 'Brand' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Brand'].isin(brand_filter)]
        
        # Pastikan Product_Name selalu ada
        if 'Product_Name' not in filtered_df.columns:
            filtered_df = add_product_info_to_data(filtered_df, df_product)
        
        # Reapply filters setelah merge (jika diperlukan)
        if status_filter:
            filtered_df = filtered_df[filtered_df['Inventory_Status'].isin(status_filter)]
        
        if tier_filter and 'SKU_Tier' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['SKU_Tier'].isin(tier_filter)]
        
        if brand_filter and 'Brand' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Brand'].isin(brand_filter)]
        
        # Prepare display columns
        base_display_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 'Inventory_Status', 
                           'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']
        
        # Tambahkan financial columns jika ada
        financial_cols = []
        if not df_inventory_financial.empty:
            # Merge dengan financial data
            filtered_df = pd.merge(
                filtered_df,
                df_inventory_financial[['SKU_ID', 'Value_at_Cost', 'Value_at_Retail', 'Potential_Margin']],
                on='SKU_ID',
                how='left'
            )
            financial_cols = ['Value_at_Cost', 'Value_at_Retail', 'Potential_Margin']
        
        display_cols = base_display_cols + financial_cols
        
        # Filter hanya kolom yang ada
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        
        # Pastikan Product_Name selalu ada
        if 'Product_Name' not in available_cols:
            # Coba cari kolom serupa
            product_name_cols = [col for col in filtered_df.columns if 'product' in col.lower() or 'name' in col.lower()]
            if product_name_cols:
                available_cols.insert(1, product_name_cols[0])
            else:
                # Tambahkan Product_Name meskipun tidak ada di dataframe
                available_cols.insert(1, 'Product_Name')
                # Add dummy column
                filtered_df['Product_Name'] = 'N/A'
        
        # Format the dataframe
        display_df = filtered_df[available_cols].copy()
        
        # Format columns
        if 'Cover_Months' in display_df.columns:
            display_df['Cover_Months'] = display_df['Cover_Months'].apply(
                lambda x: f"{x:.1f}" if pd.notnull(x) and x < 999 else "N/A"
            )
        
        if 'Avg_Monthly_Sales_3M' in display_df.columns:
            display_df['Avg_Monthly_Sales_3M'] = display_df['Avg_Monthly_Sales_3M'].apply(
                lambda x: f"{x:.0f}" if pd.notnull(x) else "0"
            )
        
        if 'Stock_Qty' in display_df.columns:
            display_df['Stock_Qty'] = display_df['Stock_Qty'].apply(
                lambda x: f"{x:,.0f}" if pd.notnull(x) else "0"
            )
        
        # Format financial columns
        if 'Value_at_Cost' in display_df.columns:
            display_df['Value_at_Cost'] = display_df['Value_at_Cost'].apply(
                lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "Rp 0"
            )
        
        if 'Value_at_Retail' in display_df.columns:
            display_df['Value_at_Retail'] = display_df['Value_at_Retail'].apply(
                lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "Rp 0"
            )
        
        if 'Potential_Margin' in display_df.columns:
            display_df['Potential_Margin'] = display_df['Potential_Margin'].apply(
                lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "Rp 0"
            )
        
        # Rename columns for display
        column_names = {
            'SKU_ID': 'SKU ID',
            'Product_Name': 'Product Name',
            'Brand': 'Brand',
            'SKU_Tier': 'Tier',
            'Inventory_Status': 'Status',
            'Stock_Qty': 'Stock Available',
            'Avg_Monthly_Sales_3M': 'Avg Sales (3M)',
            'Cover_Months': 'Cover (Months)',
            'Value_at_Cost': 'Value @ Cost',
            'Value_at_Retail': 'Value @ Retail',
            'Potential_Margin': 'Potential Margin'
        }
        
        # Filter hanya kolom yang ada
        column_names = {k: v for k, v in column_names.items() if k in display_df.columns}
        
        display_df = display_df.rename(columns=column_names)
        
        # Sort by status and cover months
        if 'Cover (Months)' in display_df.columns and 'Status' in display_df.columns:
            # Convert back to numeric for sorting
            try:
                display_df['Cover_Numeric'] = pd.to_numeric(
                    display_df['Cover (Months)'].replace('N/A', np.nan), 
                    errors='coerce'
                )
                
                # Determine sort order based on status filter
                if 'High Stock' in status_filter:
                    cover_sort_ascending = False  # High stock first
                elif 'Need Replenishment' in status_filter:
                    cover_sort_ascending = True  # Low stock first
                else:
                    cover_sort_ascending = True
                
                display_df = display_df.sort_values(
                    ['Status', 'Cover_Numeric'], 
                    ascending=[True, cover_sort_ascending]
                )
                display_df = display_df.drop('Cover_Numeric', axis=1)
            except:
                # If sorting fails, just sort by Status
                display_df = display_df.sort_values('Status')
        
        # Display dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500
        )
        
        # Summary statistics
        st.caption(f"""
        **Showing {len(filtered_df)} of {len(inv_df)} SKUs** | 
        **Average Cover:** {inv_df[inv_df['Cover_Months'] < 999]['Cover_Months'].mean():.1f} months | 
        **Total Stock Value:** Rp {total_cost_value:,.0f} (@Cost)
        """)
        
        # Download button untuk filtered data
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Inventory Data",
                data=csv,
                file_name=f"inventory_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # ================ INVENTORY HEALTH CHART ================
        st.divider()
        st.subheader("📊 Inventory Health Overview")
        
        if 'Inventory_Status' in inv_df.columns:
            # Pie chart for inventory status
            status_summary = inv_df['Inventory_Status'].value_counts().reset_index()
            status_summary.columns = ['Status', 'Count']
            
            fig_pie = px.pie(
                status_summary, 
                values='Count', 
                names='Status',
                title='Inventory Status Distribution',
                color='Status',
                color_discrete_map={
                    'Need Replenishment': '#FF5252',
                    'Ideal/Healthy': '#4CAF50',
                    'High Stock': '#FF9800'
                }
            )
            
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Bar chart for cover months by tier
            if 'SKU_Tier' in inv_df.columns:
                tier_cover = inv_df.groupby('SKU_Tier')['Cover_Months'].mean().reset_index()
                tier_cover = tier_cover[tier_cover['Cover_Months'] < 999]  # Exclude infinite values
                
                fig_bar = px.bar(
                    tier_cover,
                    x='SKU_Tier',
                    y='Cover_Months',
                    title='Average Cover Months by Tier',
                    color='Cover_Months',
                    color_continuous_scale='RdYlGn_r',  # Red for high, Green for low
                    text_auto='.1f'
                )
                
                fig_bar.update_layout(height=300)
                st.plotly_chart(fig_bar, use_container_width=True)
    
    else:
        st.warning("No inventory metrics available. Please check your data.")

# --- TAB 4: SKU EVALUATION ---
with tab4:
    st.subheader("🔍 SKU Performance Evaluation")
    
    if monthly_performance and not df_sales.empty:
        # Get last month for evaluation
        last_month = sorted(monthly_performance.keys())[-1]
        last_month_data = monthly_performance[last_month]['data'].copy()
        
        # Get last 3 months sales data for each SKU
        if not df_sales.empty:
            sales_months = sorted(df_sales['Month'].unique())
            if len(sales_months) >= 3:
                last_3_sales_months = sales_months[-3:]
                df_sales_last_3 = df_sales[df_sales['Month'].isin(last_3_sales_months)].copy()
                
                # Pivot sales data to get last 3 months sales per SKU
                try:
                    sales_pivot = df_sales_last_3.pivot_table(
                        index='SKU_ID',
                        columns='Month',
                        values='Sales_Qty',
                        aggfunc='sum',
                        fill_value=0
                    ).reset_index()
                    
                    # Rename columns to month names
                    month_rename = {}
                    for col in sales_pivot.columns:
                        if isinstance(col, datetime):
                            month_rename[col] = col.strftime('%b-%Y')
                    sales_pivot = sales_pivot.rename(columns=month_rename)
                    
                    # Merge with last month data
                    last_month_data = pd.merge(
                        last_month_data,
                        sales_pivot,
                        on='SKU_ID',
                        how='left'
                    )
                except Exception as e:
                    st.warning(f"Tidak bisa memproses data sales 3 bulan terakhir: {str(e)}")
        
        # Add inventory data
        if 'inventory_df' in inventory_metrics:
            inventory_data = inventory_metrics['inventory_df'][['SKU_ID', 'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']]
            last_month_data = pd.merge(last_month_data, inventory_data, on='SKU_ID', how='left')
        
        # Add financial data if available
        if not df_financial.empty:
            # Get financial metrics for last month
            financial_last_month = df_financial[df_financial['Month'] == last_month]
            if not financial_last_month.empty:
                financial_metrics = financial_last_month[['SKU_ID', 'Revenue', 'Gross_Margin', 'Margin_Percentage']]
                last_month_data = pd.merge(last_month_data, financial_metrics, on='SKU_ID', how='left')
        
        # Create comprehensive evaluation table
        # Filter by SKU
        sku_filter = st.text_input("🔍 Filter by SKU ID or Product Name", "")
        
        # Apply filter
        if sku_filter:
            filtered_eval_df = last_month_data[
                last_month_data['SKU_ID'].astype(str).str.contains(sku_filter, case=False, na=False) |
                (last_month_data['Product_Name'].astype(str).str.contains(sku_filter, case=False, na=False) if 'Product_Name' in last_month_data.columns else False)
            ].copy()
        else:
            filtered_eval_df = last_month_data.copy()
        
        # Determine which sales columns to show
        sales_cols = []
        for col in filtered_eval_df.columns:
            if isinstance(col, str) and '-' in col and len(col) in [7, 8]:  # Format like 'Sep-2024' or 'Mar-2025'
                try:
                    # Validate it's a proper month-year format
                    datetime.strptime(col, '%b-%Y')
                    sales_cols.append(col)
                except:
                    pass
        
        # Sort sales columns chronologically
        if sales_cols:
            sales_cols_sorted = sorted(sales_cols, key=lambda x: datetime.strptime(x, '%b-%Y'))
            # Get last 3 months only
            sales_cols_sorted = sales_cols_sorted[-3:] if len(sales_cols_sorted) >= 3 else sales_cols_sorted
        else:
            sales_cols_sorted = []
        
        # Define columns to display - WAJIB dengan Product_Name
        eval_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 
                    'Forecast_Qty', 'PO_Qty', 'PO_Rofo_Ratio',
                    'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']
        
        # Add financial columns if available
        if 'Revenue' in filtered_eval_df.columns:
            eval_cols.extend(['Revenue', 'Gross_Margin', 'Margin_Percentage'])
        
        # Add sales columns
        eval_cols.extend(sales_cols_sorted)
        
        # Filter hanya kolom yang ada
        available_cols = [col for col in eval_cols if col in filtered_eval_df.columns]
        
        # Pastikan Product_Name selalu ada
        if 'Product_Name' not in available_cols and 'Product_Name' in filtered_eval_df.columns:
            available_cols.insert(1, 'Product_Name')
        
        eval_df = filtered_eval_df[available_cols].copy()
        
        # Format columns
        if 'PO_Rofo_Ratio' in eval_df.columns:
            eval_df['PO_Rofo_Ratio'] = eval_df['PO_Rofo_Ratio'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "0%")
        
        if 'Cover_Months' in eval_df.columns:
            eval_df['Cover_Months'] = eval_df['Cover_Months'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) and x < 999 else "N/A")
        
        if 'Avg_Monthly_Sales_3M' in eval_df.columns:
            eval_df['Avg_Monthly_Sales_3M'] = eval_df['Avg_Monthly_Sales_3M'].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "0")
        
        # Format financial columns
        if 'Revenue' in eval_df.columns:
            eval_df['Revenue'] = eval_df['Revenue'].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "Rp 0")
        
        if 'Gross_Margin' in eval_df.columns:
            eval_df['Gross_Margin'] = eval_df['Gross_Margin'].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "Rp 0")
        
        if 'Margin_Percentage' in eval_df.columns:
            eval_df['Margin_Percentage'] = eval_df['Margin_Percentage'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "0%")
        
        # Format sales columns
        for col in sales_cols_sorted:
            if col in eval_df.columns:
                eval_df[col] = eval_df[col].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "0")
        
        # Rename columns - WAJIB dengan Product Name
        column_names = {
            'SKU_ID': 'SKU ID',
            'Product_Name': 'Product Name',
            'Brand': 'Brand',
            'SKU_Tier': 'Tier',
            'Forecast_Qty': 'Forecast',
            'PO_Qty': 'PO',
            'PO_Rofo_Ratio': 'PO/Rofo %',
            'Stock_Qty': 'Stock',
            'Avg_Monthly_Sales_3M': 'Avg Sales (L3M)',
            'Cover_Months': 'Cover (Months)',
            'Revenue': 'Revenue',
            'Gross_Margin': 'Gross Margin',
            'Margin_Percentage': 'Margin %'
        }
        
        # Add sales columns to rename dict
        for col in sales_cols_sorted:
            column_names[col] = col
        
        eval_df = eval_df.rename(columns=column_names)
        
        # Reorder columns
        column_order = ['SKU ID', 'Product Name', 'Brand', 'Tier', 'Forecast', 'PO', 
                       'PO/Rofo %', 'Stock', 'Avg Sales (L3M)', 'Cover (Months)']
        
        # Tambahkan financial columns
        if 'Revenue' in eval_df.columns:
            column_order.extend(['Revenue', 'Gross Margin', 'Margin %'])
        
        # Tambahkan sales columns ke urutan
        for col in sales_cols_sorted:
            if col in eval_df.columns:
                column_order.append(col)
        
        # Ensure all columns exist before reordering
        existing_columns = [col for col in column_order if col in eval_df.columns]
        eval_df = eval_df[existing_columns]
        
        st.dataframe(
            eval_df,
            use_container_width=True,
            height=400
        )
        
        # ================ NEW: SKU DEEP DIVE ANALYSIS ================
        st.divider()
        st.subheader("🔬 SKU Deep Dive Analysis")
        
        # Pilih SKU untuk deep dive
        if not last_month_data.empty:
            # Get unique SKUs for selection
            available_skus = last_month_data['SKU_ID'].unique().tolist()
            
            # Jika ada filter SKU, otomatis select yang difilter
            selected_sku = None
            if sku_filter and len(filtered_eval_df) == 1:
                selected_sku = filtered_eval_df.iloc[0]['SKU_ID']
            else:
                # Dropdown untuk pilih SKU
                sku_options = []
                for sku in available_skus[:50]:  # Limit to first 50 for performance
                    product_name = last_month_data[last_month_data['SKU_ID'] == sku]['Product_Name'].iloc[0] if 'Product_Name' in last_month_data.columns else sku
                    sku_options.append(f"{sku} - {product_name}")
                
                if sku_options:
                    selected_sku_display = st.selectbox(
                        "📋 Select SKU for Deep Dive Analysis",
                        options=sku_options,
                        index=0
                    )
                    if selected_sku_display:
                        selected_sku = selected_sku_display.split(" - ")[0]
            
            if selected_sku:
                st.markdown(f"### 📊 Analysis for SKU: **{selected_sku}**")
                
                # Get SKU details
                sku_details = last_month_data[last_month_data['SKU_ID'] == selected_sku].iloc[0].to_dict() if not last_month_data.empty else {}
                product_name = sku_details.get('Product_Name', 'N/A')
                brand = sku_details.get('Brand', 'N/A')
                tier = sku_details.get('SKU_Tier', 'N/A')
                
                # Display SKU info
                col_info1, col_info2, col_info3, col_info4 = st.columns(4)
                with col_info1:
                    st.metric("Product", product_name)
                with col_info2:
                    st.metric("Brand", brand)
                with col_info3:
                    st.metric("Tier", tier)
                with col_info4:
                    stock_qty = sku_details.get('Stock_Qty', 0)
                    st.metric("Current Stock", f"{stock_qty:,.0f}")
                
                # SECTION 1: 12-MONTH PERFORMANCE TIMELINE - SIMPLE VERSION
                st.markdown("#### 📈 12-Month Performance Timeline")
                
                # Prepare historical data for this SKU
                historical_data = []
                
                # Get last 12 months data
                if not df_sales.empty:
                    sales_months = sorted(df_sales['Month'].unique())
                    last_12_months = sales_months[-12:] if len(sales_months) >= 12 else sales_months
                    
                    for month in last_12_months:
                        month_name = month.strftime('%b-%Y')
                        
                        # Get data for this SKU in this month
                        sales_qty = df_sales[(df_sales['Month'] == month) & 
                                           (df_sales['SKU_ID'] == selected_sku)]['Sales_Qty'].sum()
                        
                        forecast_qty = df_forecast[(df_forecast['Month'] == month) & 
                                                 (df_forecast['SKU_ID'] == selected_sku)]['Forecast_Qty'].sum() if not df_forecast.empty else 0
                        
                        po_qty = df_po[(df_po['Month'] == month) & 
                                     (df_po['SKU_ID'] == selected_sku)]['PO_Qty'].sum() if not df_po.empty else 0
                        
                        historical_data.append({
                            'Month': month,
                            'Month_Display': month_name,
                            'Sales': sales_qty,
                            'Rofo': forecast_qty,
                            'PO': po_qty
                        })
                
                if historical_data:
                    hist_df = pd.DataFrame(historical_data)
                    hist_df = hist_df.sort_values('Month')
                    
                    # SIMPLE CHART - tanpa dual-axis dulu
                    fig_timeline = go.Figure()
                    
                    # Quantity lines
                    fig_timeline.add_trace(go.Scatter(
                        x=hist_df['Month_Display'],
                        y=hist_df['Rofo'],
                        name='Rofo',
                        mode='lines+markers',
                        line=dict(color='#667eea', width=3),
                        marker=dict(size=8, color='#667eea')
                    ))
                    
                    fig_timeline.add_trace(go.Scatter(
                        x=hist_df['Month_Display'],
                        y=hist_df['PO'],
                        name='PO',
                        mode='lines+markers',
                        line=dict(color='#FF9800', width=3),
                        marker=dict(size=8, color='#FF9800')
                    ))
                    
                    fig_timeline.add_trace(go.Scatter(
                        x=hist_df['Month_Display'],
                        y=hist_df['Sales'],
                        name='Sales',
                        mode='lines+markers',
                        line=dict(color='#4CAF50', width=3),
                        marker=dict(size=8, color='#4CAF50')
                    ))
                    
                    # SIMPLE LAYOUT
                    fig_timeline.update_layout(
                        height=400,
                        title=f'SKU Performance: {selected_sku}',
                        xaxis_title='Month',
                        yaxis_title='Quantity',
                        plot_bgcolor='white'
                    )
                    
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    # Tambahkan accuracy chart terpisah
                    if not df_forecast.empty and not df_po.empty:
                        # Calculate accuracy per month
                        accuracy_data = []
                        for month in last_12_months:
                            month_name = month.strftime('%b-%Y')
                            forecast_qty = df_forecast[(df_forecast['Month'] == month) & 
                                                     (df_forecast['SKU_ID'] == selected_sku)]['Forecast_Qty'].sum()
                            po_qty = df_po[(df_po['Month'] == month) & 
                                         (df_po['SKU_ID'] == selected_sku)]['PO_Qty'].sum()
                            
                            if forecast_qty > 0 and po_qty > 0:
                                accuracy = 100 - abs((po_qty / forecast_qty * 100) - 100)
                                accuracy_data.append({
                                    'Month': month_name,
                                    'Accuracy': accuracy
                                })
                        
                        if accuracy_data:
                            acc_df = pd.DataFrame(accuracy_data)
                            
                            fig_acc = go.Figure()
                            fig_acc.add_trace(go.Scatter(
                                x=acc_df['Month'],
                                y=acc_df['Accuracy'],
                                mode='lines+markers',
                                name='Accuracy %',
                                line=dict(color='#FF5252', width=3),
                                marker=dict(size=8, color='#FF5252')
                            ))
                            
                            fig_acc.update_layout(
                                height=300,
                                title='Forecast Accuracy Trend',
                                xaxis_title='Month',
                                yaxis_title='Accuracy %',
                                yaxis_range=[0, 110]
                            )
                            
                            st.plotly_chart(fig_acc, use_container_width=True)
                    
                    # SECTION 2: INVENTORY HEALTH
                    st.markdown("#### 📦 Inventory Health Analysis")
                    
                    col_inv1, col_inv2, col_inv3, col_inv4 = st.columns(4)
                    
                    with col_inv1:
                        # Current stock
                        current_stock = sku_details.get('Stock_Qty', 0)
                        st.metric("Current Stock", f"{current_stock:,.0f}")
                    
                    with col_inv2:
                        # Avg monthly sales (3-month average)
                        avg_sales_3m = sku_details.get('Avg_Monthly_Sales_3M', 0)
                        st.metric("Avg Monthly Sales (3M)", f"{avg_sales_3m:,.0f}")
                    
                    with col_inv3:
                        # Cover months
                        cover_months = sku_details.get('Cover_Months', 0)
                        cover_status = "High Stock" if cover_months > 1.5 else "Ideal" if cover_months >= 0.8 else "Low Stock"
                        st.metric("Cover (Months)", f"{cover_months:.1f}", delta=cover_status)
                    
                    with col_inv4:
                        # Sales trend (last 3 months vs previous 3 months)
                        if len(hist_df) >= 6:
                            recent_sales = hist_df.tail(3)['Sales'].sum()
                            previous_sales = hist_df.head(3)['Sales'].sum() if len(hist_df) >= 6 else recent_sales
                            sales_growth = ((recent_sales - previous_sales) / previous_sales * 100) if previous_sales > 0 else 0
                            st.metric("Sales Growth (3M)", f"{sales_growth:+.1f}%")
                    
                    # SECTION 3: FORECAST PERFORMANCE METRICS
                    st.markdown("#### 🎯 Forecast Performance Metrics")
                    
                    # Calculate forecast accuracy metrics
                    if not df_forecast.empty and not df_po.empty:
                        # Get accuracy data separately
                        accuracy_data = []
                        for month in last_12_months:
                            forecast_qty = df_forecast[(df_forecast['Month'] == month) & 
                                                     (df_forecast['SKU_ID'] == selected_sku)]['Forecast_Qty'].sum()
                            po_qty = df_po[(df_po['Month'] == month) & 
                                         (df_po['SKU_ID'] == selected_sku)]['PO_Qty'].sum()
                            
                            if forecast_qty > 0 and po_qty > 0:
                                accuracy = 100 - abs((po_qty / forecast_qty * 100) - 100)
                                accuracy_data.append({
                                    'Month': month,
                                    'Forecast_Qty': forecast_qty,
                                    'PO_Qty': po_qty,
                                    'Accuracy': accuracy
                                })
                        
                        if accuracy_data:
                            acc_df = pd.DataFrame(accuracy_data)
                            
                            col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                            
                            with col_met1:
                                # Average accuracy
                                avg_accuracy = acc_df['Accuracy'].mean()
                                accuracy_status = "Good" if avg_accuracy >= 80 else "Needs Improvement"
                                st.metric("Avg Forecast Accuracy", f"{avg_accuracy:.1f}%", delta=accuracy_status)
                            
                            with col_met2:
                                # Forecast vs Sales ratio
                                total_forecast = acc_df['Forecast_Qty'].sum()
                                # Get total sales for same months
                                total_sales = 0
                                for month in acc_df['Month']:
                                    sales_qty = df_sales[(df_sales['Month'] == month) & 
                                                       (df_sales['SKU_ID'] == selected_sku)]['Sales_Qty'].sum()
                                    total_sales += sales_qty
                                
                                forecast_vs_sales = (total_forecast / total_sales * 100) if total_sales > 0 else 0
                                st.metric("Forecast/Sales %", f"{forecast_vs_sales:.1f}%")
                            
                            with col_met3:
                                # PO vs Forecast ratio
                                total_po = acc_df['PO_Qty'].sum()
                                po_vs_forecast = (total_po / total_forecast * 100) if total_forecast > 0 else 0
                                st.metric("PO/Forecast %", f"{po_vs_forecast:.1f}%")
                            
                            with col_met4:
                                # Consistency score (std dev of accuracy)
                                accuracy_std = acc_df['Accuracy'].std()
                                consistency_score = max(0, 100 - accuracy_std)
                                st.metric("Consistency Score", f"{consistency_score:.1f}")
                            
                            # SECTION 4: RECOMMENDATIONS
                            st.markdown("#### 💡 Recommendations")
                            
                            recommendations = []
                            
                            # Stock recommendations
                            cover_months = sku_details.get('Cover_Months', 0)
                            if cover_months < 0.8:
                                recommendations.append("🔄 **Need Replenishment**: Stock cover is below 0.8 months")
                            elif cover_months > 1.5:
                                recommendations.append("📉 **Reduce Stock**: High stock coverage (>1.5 months)")
                            
                            # Forecast accuracy recommendations
                            if avg_accuracy < 80:
                                recommendations.append("🎯 **Improve Forecasting**: Accuracy below 80% target")
                            
                            # Sales trend recommendations
                            sales_growth = 0  # Calculate sales growth
                            if len(hist_df) >= 6:
                                recent_sales = hist_df.tail(3)['Sales'].sum()
                                previous_sales = hist_df.head(3)['Sales'].sum()
                                sales_growth = ((recent_sales - previous_sales) / previous_sales * 100) if previous_sales > 0 else 0
                            
                            if sales_growth < -10:
                                recommendations.append("📊 **Review Demand**: Sales declining significantly")
                            elif sales_growth > 50:
                                recommendations.append("🚀 **Opportunity**: Strong sales growth detected")
                            
                            # PO compliance recommendations
                            if po_vs_forecast < 80:
                                recommendations.append("📝 **Increase PO Compliance**: PO significantly below forecast")
                            elif po_vs_forecast > 120:
                                recommendations.append("⚠️ **Reduce Over-PO**: PO significantly above forecast")
                            
                            # Financial recommendations (if financial data available)
                            if 'Margin_Percentage' in sku_details:
                                margin = sku_details.get('Margin_Percentage', 0)
                                if margin < 20:
                                    recommendations.append("💰 **Low Margin Alert**: Margin below 20%")
                                elif margin > 40:
                                    recommendations.append("💰 **High Margin Opportunity**: Excellent margin performance")
                            
                            if recommendations:
                                for rec in recommendations:
                                    st.write(f"- {rec}")
                            else:
                                st.success("✅ **Excellent**: This SKU is performing well across all metrics!")
                        else:
                            st.info("No forecast accuracy data available for this SKU")
    else:
        st.info("📊 Insufficient data for SKU evaluation")

# --- TAB 5: SALES & FORECAST ANALYSIS ---
with tab5:
    st.subheader("📈 Sales & Forecast Analysis")
    
    if sales_vs_forecast:
        last_month = sales_vs_forecast['last_month']
        last_month_name = last_month.strftime('%b %Y')
        
                # SECTION 1: SIMPLE MONTHLY TREND
        st.markdown("### 📊 Monthly Trend")
        
        # Get ALL available months, not just last 6
        monthly_trend = []
        
        # Get unique months from ALL datasets
        all_months = set()
        if not df_sales.empty:
            all_months.update(df_sales['Month'].unique())
        if not df_forecast.empty:
            all_months.update(df_forecast['Month'].unique())
        if not df_po.empty:
            all_months.update(df_po['Month'].unique())
        
        if all_months:
            sorted_months = sorted(all_months)
            
            for month in sorted_months:  # PAKAI SEMUA BULAN, bukan cuma 6 terakhir
                month_name = month.strftime('%b-%Y')
                sales_qty = df_sales[df_sales['Month'] == month]['Sales_Qty'].sum() if not df_sales.empty else 0
                forecast_qty = df_forecast[df_forecast['Month'] == month]['Forecast_Qty'].sum() if not df_forecast.empty else 0
                po_qty = df_po[df_po['Month'] == month]['PO_Qty'].sum() if not df_po.empty else 0
                
                monthly_trend.append({
                    'Month': month_name,
                    'Rofo': forecast_qty,
                    'PO': po_qty,
                    'Sales': sales_qty
                })
        
        if monthly_trend:
            trend_df = pd.DataFrame(monthly_trend)
            
            # Tampilkan info bulan yang tersedia
            st.caption(f"📅 Showing data for {len(trend_df)} months")
            
            # CHART 1: Quantity Trend
            fig1 = go.Figure()
            
            fig1.add_trace(go.Bar(
                x=trend_df['Month'],
                y=trend_df['Rofo'],
                name='Rofo',
                marker_color='#667eea'
            ))
            
            fig1.add_trace(go.Bar(
                x=trend_df['Month'],
                y=trend_df['PO'],
                name='PO',
                marker_color='#FF9800'
            ))
            
            fig1.add_trace(go.Bar(
                x=trend_df['Month'],
                y=trend_df['Sales'],
                name='Sales',
                marker_color='#4CAF50'
            ))
            
            fig1.update_layout(
                height=400,
                title='Monthly Trend: Rofo vs PO vs Sales (All Available Months)',
                xaxis_title='Month',
                yaxis_title='Quantity',
                barmode='group'
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            # CHART 2: Accuracy Trend
            if not df_forecast.empty and not df_po.empty:
                accuracy_trend = []
                
                for month in sorted_months:  # PAKAI SEMUA BULAN
                    month_name = month.strftime('%b-%Y')
                    forecast_qty = df_forecast[df_forecast['Month'] == month]['Forecast_Qty'].sum()
                    po_qty = df_po[df_po['Month'] == month]['PO_Qty'].sum()
                    
                    if forecast_qty > 0:
                        accuracy = 100 - abs((po_qty / forecast_qty * 100) - 100)
                        accuracy_trend.append({
                            'Month': month_name,
                            'Accuracy': accuracy
                        })
                
                if accuracy_trend:
                    acc_df = pd.DataFrame(accuracy_trend)
                    
                    fig2 = go.Figure()
                    
                    fig2.add_trace(go.Scatter(
                        x=acc_df['Month'],
                        y=acc_df['Accuracy'],
                        mode='lines+markers',
                        name='Accuracy %',
                        line=dict(color='#FF5252', width=3),
                        marker=dict(size=8, color='#FF5252')
                    ))
                    
                    fig2.update_layout(
                        height=300,
                        title='Forecast Accuracy Trend (All Available Months)',
                        xaxis_title='Month',
                        yaxis_title='Accuracy %',
                        yaxis_range=[0, 110]
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
        
        # SECTION 2: BRAND PERFORMANCE
        st.divider()
        st.markdown("### 🏷️ Brand Performance")
        
        if not df_forecast.empty and not df_po.empty and not df_sales.empty:
            # Get last month brand data
            forecast_last = df_forecast[df_forecast['Month'] == last_month].copy()
            po_last = df_po[df_po['Month'] == last_month].copy()
            sales_last = df_sales[df_sales['Month'] == last_month].copy()
            
            # Add product info
            forecast_last = add_product_info_to_data(forecast_last, df_product)
            po_last = add_product_info_to_data(po_last, df_product)
            sales_last = add_product_info_to_data(sales_last, df_product)
            
            if 'Brand' in forecast_last.columns:
                # Aggregate by brand
                brand_data = []
                brands = forecast_last['Brand'].unique()
                
                for brand in brands:
                    rofo = forecast_last[forecast_last['Brand'] == brand]['Forecast_Qty'].sum()
                    po = po_last[po_last['Brand'] == brand]['PO_Qty'].sum()
                    sales = sales_last[sales_last['Brand'] == brand]['Sales_Qty'].sum()
                    
                    brand_data.append({
                        'Brand': brand,
                        'Rofo': rofo,
                        'PO': po,
                        'Sales': sales
                    })
                
                if brand_data:
                    brand_df = pd.DataFrame(brand_data)
                    brand_df = brand_df.sort_values('Rofo', ascending=False).head(10)
                    
                    # Brand chart
                    fig3 = go.Figure()
                    
                    fig3.add_trace(go.Bar(
                        x=brand_df['Brand'],
                        y=brand_df['Rofo'],
                        name='Rofo',
                        marker_color='#667eea'
                    ))
                    
                    fig3.add_trace(go.Bar(
                        x=brand_df['Brand'],
                        y=brand_df['PO'],
                        name='PO',
                        marker_color='#FF9800'
                    ))
                    
                    fig3.add_trace(go.Bar(
                        x=brand_df['Brand'],
                        y=brand_df['Sales'],
                        name='Sales',
                        marker_color='#4CAF50'
                    ))
                    
                    fig3.update_layout(
                        height=400,
                        title=f'Top 10 Brands - {last_month_name}',
                        xaxis_title='Brand',
                        yaxis_title='Quantity',
                        barmode='group'
                    )
                    
                    st.plotly_chart(fig3, use_container_width=True)
        
        # SECTION 3: HIGH DEVIATION ANALYSIS
        st.divider()
        st.subheader("⚠️ High Deviation Analysis")
        
        # TAMBAH NOTE INI
        st.info("""
        **📌 Note:** Analysis ini hanya mencakup **ACTIVE SKUs** dengan **Forecast > 0**. 
        SKU Inactive/Discontinued tidak dihitung karena tidak ada forecast requirement.
        """)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Forecast Deviation",
                f"{sales_vs_forecast['avg_forecast_deviation']:.1f}%",
                delta="Target: < 20%"
            )
        with col2:
            st.metric(
                "PO Deviation", 
                f"{sales_vs_forecast['avg_po_deviation']:.1f}%",
                delta="Target: < 20%"
            )
        with col3:
            st.metric(
                "High Deviation SKUs",
                len(sales_vs_forecast['high_deviation_skus']),
                delta=f"Active SKUs: {sales_vs_forecast['total_skus_compared']}"
            )
        
        high_dev_df = sales_vs_forecast['high_deviation_skus']
        
        if not high_dev_df.empty:
            # Display table
            display_df = high_dev_df.copy()
            
            # Select columns
            cols_to_show = ['SKU_ID', 'Product_Name', 'Brand', 
                          'Sales_Qty', 'Forecast_Qty', 'PO_Qty',
                          'Sales_vs_Forecast_Ratio', 'Sales_vs_PO_Ratio']
            
            available_cols = [col for col in cols_to_show if col in display_df.columns]
            
            # Ensure Product_Name
            if 'Product_Name' not in available_cols and 'Product_Name' in display_df.columns:
                available_cols.insert(1, 'Product_Name')
            
            display_df = display_df[available_cols].head(20)
            
            # Format
            if 'Sales_vs_Forecast_Ratio' in display_df.columns:
                display_df['Sales_vs_Forecast_Ratio'] = display_df['Sales_vs_Forecast_Ratio'].apply(lambda x: f"{x:.1f}%")
            
            if 'Sales_vs_PO_Ratio' in display_df.columns:
                display_df['Sales_vs_PO_Ratio'] = display_df['Sales_vs_PO_Ratio'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.success(f"✅ No high deviation SKUs in {last_month_name}")
    
    else:
        st.info("📊 Need sales, forecast, and PO data for analysis")

# --- TAB 6: DATA EXPLORER ---
with tab6:
    st.subheader("📋 Raw Data Explorer")
    
    dataset_options = {
        "Product Master": df_product,
        "Active Products": df_product_active,
        "Sales Data": df_sales,
        "Forecast Data": df_forecast,
        "PO Data": df_po,
        "Stock Data": df_stock,
        "Financial Data": df_financial,
        "Inventory Financial": df_inventory_financial
    }
    
    selected_dataset = st.selectbox("Select Dataset", list(dataset_options.keys()))
    df_selected = dataset_options[selected_dataset]
    
    if not df_selected.empty:
        # Ensure Product_Name is shown alongside SKU_ID if available
        if 'SKU_ID' in df_selected.columns and 'Product_Name' in df_selected.columns:
            # Reorder columns to show SKU_ID and Product_Name first
            cols = list(df_selected.columns)
            if 'Product_Name' in cols:
                cols.remove('Product_Name')
                cols.insert(1, 'Product_Name')
            df_selected = df_selected[cols]
        
        # Data info
        st.write(f"**Rows:** {df_selected.shape[0]:,} | **Columns:** {df_selected.shape[1]}")
        
        # Column selector
        if st.checkbox("Select Columns", False):
            all_columns = df_selected.columns.tolist()
            selected_columns = st.multiselect("Choose columns:", all_columns, default=all_columns[:10])
            df_display = df_selected[selected_columns]
        else:
            df_display = df_selected
        
        # Data preview
        st.dataframe(
            df_display,
            use_container_width=True,
            height=500
        )
        
        # Download option
        csv = df_selected.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{selected_dataset.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("No data available for selected dataset")

# --- TAB 7: FORECAST ECOMMERCE ANALYSIS ---
with tab7:
    st.subheader("🛒 Ecommerce Forecast Analysis 2026")
    st.markdown("**Analyze Ecommerce forecast data from Forecast_2026_Ecomm sheet**")
    
    # ================ INISIALISASI DATA ================
    use_fallback_data = False
    
    # Jika ecomm forecast kosong, coba fallback
    if df_ecomm_forecast.empty:
        st.warning("⚠️ **Forecast_2026_Ecomm sheet not found** - Trying fallback options")
        
        # Coba cari di forecast data biasa
        if not df_forecast.empty:
            try:
                # Transform forecast data to ecomm format
                forecast_pivot = df_forecast.pivot_table(
                    index=['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier'],
                    columns='Month',
                    values='Forecast_Qty',
                    aggfunc='sum',
                    fill_value=0
                ).reset_index()
                
                # Rename columns to month format
                forecast_pivot.columns.name = None
                for col in forecast_pivot.columns:
                    if isinstance(col, datetime):
                        new_name = col.strftime('%b-%y')
                        forecast_pivot = forecast_pivot.rename(columns={col: new_name})
                
                # Get month columns
                ecomm_forecast_month_cols = [col for col in forecast_pivot.columns 
                                            if any(m in col.lower() for m in 
                                                ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])]
                
                if ecomm_forecast_month_cols:
                    df_ecomm_forecast = forecast_pivot
                    use_fallback_data = True
                    st.success(f"✅ Created fallback data: {len(df_ecomm_forecast)} SKUs, {len(ecomm_forecast_month_cols)} months")
            except Exception as e:
                st.error(f"❌ Error creating fallback data: {str(e)}")
        else:
            st.error("❌ No forecast data available!")
            st.stop()
    else:
        st.success(f"✅ Ecommerce forecast loaded: {len(df_ecomm_forecast)} SKUs, {len(ecomm_forecast_month_cols)} months")
    
    # ================ FUNGSI BANTU LOKAL ================
    def format_number(value):
        """Format angka dengan koma, tanpa desimal"""
        try:
            if pd.isna(value): return "0"
            value = float(value)
            if value == 0: return "0"
            elif abs(value) >= 1000: return f"{value:,.0f}"
            else: return f"{value:.0f}"
        except: return str(value)
    
    def parse_month_str(month_str):
        """Parse bulan dari string format"""
        try:
            month_str = str(month_str).upper()
            if '-' in month_str:
                month_part, year_part = month_str.split('-')
                month_num = datetime.strptime(month_part[:3], '%b').month
                year = 2000 + int(year_part) if len(year_part) == 2 else int(year_part)
                return datetime(year, month_num, 1)
            return datetime.now()
        except:
            return datetime.now()

    def calculate_monthly_value(df_forecast, month_cols, df_product):
        """Hitung value (revenue projection) untuk setiap bulan"""
        if df_forecast.empty or not month_cols:
            return pd.DataFrame()
        
        # Gabungkan dengan harga
        df_with_price = add_product_info_to_data(df_forecast, df_product)
        
        # Hitung value untuk setiap bulan
        monthly_values = []
        for month in month_cols:
            if 'Floor_Price' in df_with_price.columns:
                # Hitung value = qty × floor price
                month_value = (df_with_price[month] * df_with_price['Floor_Price'].fillna(0)).sum()
            else:
                month_value = 0
            
            monthly_values.append({
                'Month': month,
                'Qty': df_with_price[month].sum(),
                'Value': month_value
            })
        
        return pd.DataFrame(monthly_values)
    
    # ================ DASHBOARD CONTENT ================
    if ecomm_forecast_month_cols:
        
        # --- SECTION 1: KPI OVERVIEW ---
        st.divider()
        st.subheader("📈 Ecommerce Forecast Overview")
        
        # Hitung totals
        total_qty = df_ecomm_forecast[ecomm_forecast_month_cols].sum().sum()
        
        # Hitung value jika ada harga
        total_value = 0
        df_with_price = add_product_info_to_data(df_ecomm_forecast, df_product)
        if 'Floor_Price' in df_with_price.columns:
            for month in ecomm_forecast_month_cols:
                total_value += (df_with_price[month] * df_with_price['Floor_Price'].fillna(0)).sum()
        
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1: st.metric("Total SKUs", f"{len(df_ecomm_forecast):,}")
        with col_kpi2: st.metric("Total Forecast Qty", f"{format_number(total_qty)}")
        with col_kpi3: st.metric("Total Forecast Value", f"Rp {format_number(total_value)}")
        with col_kpi4: 
            avg_monthly = total_qty / len(ecomm_forecast_month_cols) if ecomm_forecast_month_cols else 0
            st.metric("Avg Monthly Qty", f"{format_number(avg_monthly)}")
        
        # --- SECTION 2: MONTHLY TREND (LINE CHART) ---
        st.divider()
        st.subheader("📊 Monthly Forecast Trend by Brand (Line Chart)")
        
        # Filter controls
        trend_col1, trend_col2, trend_col3 = st.columns(3)
        
        with trend_col1:
            all_brands = df_ecomm_forecast['Brand'].unique().tolist() if 'Brand' in df_ecomm_forecast.columns else []
            # Default select top 5
            default_brands = []
            if all_brands:
                default_brands = df_ecomm_forecast.groupby('Brand')[ecomm_forecast_month_cols].sum().sum(axis=1).nlargest(5).index.tolist()

            selected_brands = st.multiselect("Filter by Brand", options=all_brands, default=default_brands, key="ecomm_brand_filter")
        
        with trend_col2:
            display_months = st.slider("Months to Display", 6, len(ecomm_forecast_month_cols), min(12, len(ecomm_forecast_month_cols)), key="ecomm_month_slider")
        
        with trend_col3:
            show_value = st.checkbox("Show Total Value (Secondary Axis)", value=True)
        
        # Filter logic
        filtered_ecomm = df_ecomm_forecast.copy()
        if selected_brands and 'Brand' in filtered_ecomm.columns:
            filtered_ecomm = filtered_ecomm[filtered_ecomm['Brand'].isin(selected_brands)]
        
        # Sort months
        display_month_cols = ecomm_forecast_month_cols[-display_months:] if display_months < len(ecomm_forecast_month_cols) else ecomm_forecast_month_cols
        sorted_month_cols = sorted(display_month_cols, key=parse_month_str)

        # Generate Line Chart
        fig = go.Figure()

        # Add Lines for Brands
        if 'Brand' in filtered_ecomm.columns and not filtered_ecomm.empty:
            brand_volumes = filtered_ecomm.groupby('Brand')[sorted_month_cols].sum().sum(axis=1).sort_values(ascending=False)
            for brand in brand_volumes.index:
                brand_monthly_qty = filtered_ecomm[filtered_ecomm['Brand'] == brand][sorted_month_cols].sum()
                fig.add_trace(go.Scatter(
                    x=brand_monthly_qty.index, y=brand_monthly_qty.values, name=brand,
                    mode='lines+markers', line=dict(width=3), marker=dict(size=7),
                    hovertemplate=f'<b>%{{x}}</b><br>{brand}: %{{y:,.0f}} units<extra></extra>'
                ))
        else:
            total_qty_series = filtered_ecomm[sorted_month_cols].sum()
            fig.add_trace(go.Scatter(
                x=total_qty_series.index, y=total_qty_series.values, name='Total Qty',
                mode='lines+markers', line=dict(color='#667eea', width=4),
                hovertemplate='<b>%{x}</b><br>Total: %{y:,.0f} units<extra></extra>'
            ))
        
        # Add Total Value Line
        if show_value:
            monthly_value_df = calculate_monthly_value(filtered_ecomm, sorted_month_cols, df_product)
            if not monthly_value_df.empty:
                monthly_value_df['Month_Date'] = monthly_value_df['Month'].apply(parse_month_str)
                monthly_value_df = monthly_value_df.set_index('Month').reindex(sorted_month_cols).reset_index()
                fig.add_trace(go.Scatter(
                    x=monthly_value_df['Month'], y=monthly_value_df['Value'], name='Total Value (Rp)',
                    mode='lines+markers', line=dict(color='#333333', width=2, dash='dot'), 
                    marker=dict(size=5, color='#333333', symbol='x'), yaxis='y2', opacity=0.6,
                    hovertemplate='<b>%{x}</b><br>Total Value: Rp %{y:,.0f}<extra></extra>'
                ))
        
        # Re-calc monthly_df for Insights Section
        monthly_totals = filtered_ecomm[sorted_month_cols].sum()
        monthly_df = pd.DataFrame({'Month': monthly_totals.index, 'Quantity': monthly_totals.values})
        monthly_df['Month_Display'] = monthly_df['Month'] 

        # Chart Layout
        layout_config = {
            'height': 500, 'title': 'Monthly Forecast Trend (Line Chart)',
            'xaxis_title': 'Month', 'yaxis_title': 'Quantity (units)',
            'hovermode': 'x unified', 'plot_bgcolor': 'white', 'showlegend': True,
            'legend': dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        }
        if show_value:
            layout_config['yaxis2'] = {'title': 'Total Value (Rp)', 'overlaying': 'y', 'side': 'right', 'showgrid': False}
        
        fig.update_layout(**layout_config)
        st.plotly_chart(fig, use_container_width=True)

# --- SECTION 3: NEW QUARTERLY ANALYSIS (FULL NUMBER FORMAT) ---
        st.divider()
        st.subheader("📅 Quarterly Brand Analysis (Qty & Value)")
        
        # 1. Prepare Quarter Logic
        q_map = {'Q1': ['jan', 'feb', 'mar'], 'Q2': ['apr', 'may', 'jun'], 
                 'Q3': ['jul', 'aug', 'sep'], 'Q4': ['oct', 'nov', 'dec']}
        
        quarter_cols_map = {'Q1': [], 'Q2': [], 'Q3': [], 'Q4': []}
        
        # Sort cols first
        all_cols_sorted = sorted(ecomm_forecast_month_cols, key=parse_month_str)
        
        for col in all_cols_sorted:
            m_str = col.split('-')[0].lower()[:3]
            for q, months in q_map.items():
                if m_str in months:
                    quarter_cols_map[q].append(col)
        
        # Identify available quarters (those that have data)
        active_quarters = [q for q, cols in quarter_cols_map.items() if len(cols) > 0]
        
        if 'Brand' in df_ecomm_forecast.columns and active_quarters:
            # Prepare Tabs for Qty vs Value
            q_tab1, q_tab2 = st.tabs(["📦 By Quantity", "💰 By Value (Rp)"])
            
            # --- Tab Qty ---
            with q_tab1:
                # Group by Brand
                q_brand_qty = []
                for brand in df_ecomm_forecast['Brand'].unique():
                    row = {'Brand': brand}
                    total_row = 0
                    brand_data = df_ecomm_forecast[df_ecomm_forecast['Brand'] == brand]
                    
                    for q in active_quarters:
                        cols = quarter_cols_map[q]
                        q_val = brand_data[cols].sum().sum()
                        row[q] = q_val
                        total_row += q_val
                    
                    row['Total'] = total_row
                    q_brand_qty.append(row)
                
                df_q_qty = pd.DataFrame(q_brand_qty).sort_values('Total', ascending=False)
                
                # Format for display
                df_q_qty_disp = df_q_qty.copy()
                for col in df_q_qty_disp.columns:
                    if col != 'Brand':
                        df_q_qty_disp[col] = df_q_qty_disp[col].apply(format_number)
                
                # Visual Heatmap
                fig_heat_qty = go.Figure(data=go.Heatmap(
                    z=df_q_qty[active_quarters].head(10).values,
                    x=active_quarters,
                    y=df_q_qty['Brand'].head(10),
                    colorscale='Blues',
                    text=df_q_qty[active_quarters].head(10).values,
                    texttemplate="%{text:,.0f}"
                ))
                fig_heat_qty.update_layout(height=400, title="Top 10 Brands - Quarterly Quantity Heatmap")
                st.plotly_chart(fig_heat_qty, use_container_width=True)
                
                st.markdown("#### 📋 Quarterly Quantity Table")
                st.dataframe(df_q_qty_disp, use_container_width=True)

            # --- Tab Value ---
            with q_tab2:
                # Check price
                df_for_val = add_product_info_to_data(df_ecomm_forecast, df_product)
                if 'Floor_Price' in df_for_val.columns:
                    # Pre-calculate totals per row to optimize
                    df_for_val['Temp_Price'] = df_for_val['Floor_Price'].fillna(0)
                    
                    q_brand_val = []
                    for brand in df_for_val['Brand'].unique():
                        row = {'Brand': brand}
                        total_row = 0
                        brand_data = df_for_val[df_for_val['Brand'] == brand]
                        
                        for q in active_quarters:
                            cols = quarter_cols_map[q]
                            # Vectorized calc: Sum(Qty * Price) for specific columns
                            q_val = 0
                            for c in cols:
                                q_val += (brand_data[c] * brand_data['Temp_Price']).sum()
                            
                            row[q] = q_val
                            total_row += q_val
                        
                        row['Total'] = total_row
                        q_brand_val.append(row)
                    
                    df_q_val = pd.DataFrame(q_brand_val).sort_values('Total', ascending=False)
                    
                    # Format
                    df_q_val_disp = df_q_val.copy()
                    for col in df_q_val_disp.columns:
                        if col != 'Brand':
                            df_q_val_disp[col] = df_q_val_disp[col].apply(lambda x: f"Rp {format_number(x)}")
                    
                    # Visual Heatmap (FULL NUMBER FORMAT)
                    fig_heat_val = go.Figure(data=go.Heatmap(
                        z=df_q_val[active_quarters].head(10).values,
                        x=active_quarters,
                        y=df_q_val['Brand'].head(10),
                        colorscale='Greens',
                        text=df_q_val[active_quarters].head(10).values,
                        # UBAH DISINI: Pakai format full comma (Rp 15,000,000)
                        texttemplate="Rp %{text:,.0f}" 
                    ))
                    fig_heat_val.update_layout(height=400, title="Top 10 Brands - Quarterly Value Heatmap")
                    st.plotly_chart(fig_heat_val, use_container_width=True)
                    
                    st.markdown("#### 📋 Quarterly Value Table")
                    st.dataframe(df_q_val_disp, use_container_width=True)
                else:
                    st.warning("⚠️ Cannot calculate value: 'Floor_Price' missing in Product Master")

        # --- SECTION 4: DATA EXPLORER ---
        st.divider()
        st.subheader("📋 Data Explorer")
        
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            explorer_brands = st.multiselect("Filter Brands for Table", options=all_brands, default=[], key="explorer_brand_filter")
        with exp_col2:
            table_months = st.slider("Months to Show in Table", 3, len(ecomm_forecast_month_cols), 6, key="table_month_slider")
        
        table_data = df_ecomm_forecast.copy()
        if explorer_brands and 'Brand' in table_data.columns:
            table_data = table_data[table_data['Brand'].isin(explorer_brands)]
        
        table_month_cols = sorted_month_cols[-table_months:]
        display_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier'] + table_month_cols
        available_cols = [col for col in display_cols if col in table_data.columns]
        
        table_disp = table_data[available_cols].head(50).copy()
        for col in table_month_cols:
            if col in table_disp.columns: table_disp[col] = table_disp[col].apply(format_number)
            
        st.dataframe(table_disp, use_container_width=True, height=400)
        
        csv = table_data.to_csv(index=False)
        st.download_button("📥 Download Forecast CSV", data=csv, file_name=f"ecomm_forecast_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

        # --- SECTION 5: INSIGHTS ---
        st.divider()
        st.subheader("💡 Key Insights")
        
        insights = []
        insights.append(f"**📊 Total Forecast:** {format_number(total_qty)} units (Rp {format_number(total_value)})")
        if not monthly_df.empty:
            peak_month = monthly_df.loc[monthly_df['Quantity'].idxmax()]
            insights.append(f"**🎯 Peak Month:** {peak_month['Month_Display']} ({format_number(peak_month['Quantity'])} units)")
        
        # Calculate Brand Share based on Qty
        if 'Brand' in df_ecomm_forecast.columns:
             # Gunakan total volume dari loop brand section sebelumnya
             if total_qty > 0:
                 top_brand_name = df_ecomm_forecast.groupby('Brand')[ecomm_forecast_month_cols].sum().sum(axis=1).idxmax()
                 top_brand_qty = df_ecomm_forecast.groupby('Brand')[ecomm_forecast_month_cols].sum().sum(axis=1).max()
                 share = (top_brand_qty/total_qty*100)
                 insights.append(f"**🏆 Top Brand:** {top_brand_name} ({format_number(top_brand_qty)} units, {share:.1f}%)")

        for insight in insights: st.info(insight)
    
    else:
        st.error("❌ No Ecommerce forecast data available")

# --- TAB 8: PROFITABILITY ANALYSIS ---
with tab8:
    st.subheader("💰 Profitability & Financial Analysis")
    
    if not df_financial.empty:
        # 1. QUICK METRICS
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_revenue = df_financial['Revenue'].sum()
            st.metric("Total Revenue", f"Rp {total_revenue:,.0f}")
        
        with col2:
            total_margin = df_financial['Gross_Margin'].sum()
            st.metric("Total Gross Margin", f"Rp {total_margin:,.0f}")
        
        with col3:
            avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            st.metric("Avg Margin %", f"{avg_margin_pct:.1f}%")
        
        with col4:
            total_units = df_financial['Sales_Qty'].sum()
            avg_price = total_revenue / total_units if total_units > 0 else 0
            st.metric("Avg Selling Price", f"Rp {avg_price:.2f}")
        
        # 2. INVENTORY VALUE (Real Impact!)
        st.divider()
        st.subheader("📦 Inventory Financial Value")
        
        if not df_inventory_financial.empty:
            total_cost_value = df_inventory_financial['Value_at_Cost'].sum()
            total_retail_value = df_inventory_financial['Value_at_Retail'].sum()
            total_potential_margin = df_inventory_financial['Potential_Margin'].sum()
            inventory_margin_pct = (total_potential_margin / total_retail_value * 100) if total_retail_value > 0 else 0
            
            col_inv1, col_inv2, col_inv3, col_inv4 = st.columns(4)
            
            with col_inv1:
                st.metric("Inventory @ Cost", f"Rp {total_cost_value:,.0f}")
            
            with col_inv2:
                st.metric("Inventory @ Retail", f"Rp {total_retail_value:,.0f}")
            
            with col_inv3:
                st.metric("Potential Margin", f"Rp {total_potential_margin:,.0f}")
            
            with col_inv4:
                st.metric("Inventory Margin %", f"{inventory_margin_pct:.1f}%")
            
            # Show high value inventory
            high_value_skus = df_inventory_financial.sort_values('Value_at_Cost', ascending=False).head(10)
            
            st.markdown("#### 📊 Top 10 Highest Value Inventory Items")
            st.dataframe(
                high_value_skus[['SKU_ID', 'Product_Name', 'Brand', 'Stock_Qty', 
                               'Value_at_Cost', 'Value_at_Retail', 'Potential_Margin', 'Margin_Percentage']],
                column_config={
                    "Value_at_Cost": st.column_config.NumberColumn("Value @ Cost", format="Rp  %.0f"),
                    "Value_at_Retail": st.column_config.NumberColumn("Value @ Retail", format="Rp  %.0f"),
                    "Potential_Margin": st.column_config.NumberColumn("Potential Margin", format="Rp  %.0f"),
                    "Margin_Percentage": st.column_config.ProgressColumn("Margin %", format="%.1f%%", min_value=0, max_value=100)
                },
                use_container_width=True
            )
        
        # 3. PROFITABILITY TREND
        st.divider()
        st.subheader("📈 Monthly Profitability Trend")
        
        monthly_profit = df_financial.groupby('Month').agg({
            'Revenue': 'sum',
            'Gross_Margin': 'sum',
            'Sales_Qty': 'sum'
        }).reset_index()
        
        monthly_profit['Margin_Percentage'] = np.where(
            monthly_profit['Revenue'] > 0,
            (monthly_profit['Gross_Margin'] / monthly_profit['Revenue'] * 100),
            0
        )
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_profit['Month'].dt.strftime('%b-%Y'),
            y=monthly_profit['Revenue'],
            name='Revenue',
            marker_color='#667eea'
        ))
        fig.add_trace(go.Scatter(
            x=monthly_profit['Month'].dt.strftime('%b-%Y'),
            y=monthly_profit['Margin_Percentage'],
            name='Margin %',
            yaxis='y2',
            line=dict(color='#4CAF50', width=3)
        ))
        
        fig.update_layout(
            title='Monthly Revenue vs Margin %',
            yaxis=dict(title='Revenue (Rp )'),
            yaxis2=dict(title='Margin %', overlaying='y', side='right'),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 4. TOP PERFORMING SKUs BY MARGIN
        st.divider()
        st.subheader("🏆 Top Performing SKUs by Gross Margin")
        
        if not profitability_segments.empty:
            # Top 10 by absolute margin
            st.dataframe(
                profitability_segments.head(10)[['SKU_ID', 'Product_Name', 'Brand', 
                                               'Sales_Qty', 'Revenue', 'Gross_Margin', 'Margin_Percentage', 'Margin_Segment']],
                column_config={
                    "Revenue": st.column_config.NumberColumn("Revenue", format="Rp  %.0f"),
                    "Gross_Margin": st.column_config.NumberColumn("Gross Margin", format="Rp  %.0f"),
                    "Margin_Percentage": st.column_config.ProgressColumn("Margin %", format="%.1f%%", min_value=0, max_value=100)
                },
                use_container_width=True
            )
            
            # Margin segmentation analysis
            st.divider()
            st.subheader("📊 Margin Segmentation Analysis")
            
            segment_summary = profitability_segments.groupby('Margin_Segment').agg({
                'SKU_ID': 'count',
                'Revenue': 'sum',
                'Gross_Margin': 'sum',
                'Sales_Qty': 'sum'
            }).reset_index()
            
            segment_summary['Avg_Margin_Percentage'] = (segment_summary['Gross_Margin'] / segment_summary['Revenue'] * 100)
            segment_summary = segment_summary.sort_values('Revenue', ascending=False)
            
            col_seg1, col_seg2 = st.columns(2)
            
            with col_seg1:
                # Pie chart
                fig_pie = px.pie(segment_summary, values='Revenue', names='Margin_Segment',
                                title='Revenue Distribution by Margin Segment',
                                color='Margin_Segment',
                                color_discrete_map={
                                    'High Margin (>40%)': '#4CAF50',
                                    'Medium Margin (20-40%)': '#FF9800',
                                    'Low Margin (<20%)': '#F44336',
                                    'Negative Margin': '#9E9E9E'
                                })
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_seg2:
                # Bar chart
                fig_bar = px.bar(segment_summary, x='Margin_Segment', y='Avg_Margin_Percentage',
                                title='Average Margin % by Segment',
                                color='Margin_Segment',
                                color_discrete_map={
                                    'High Margin (>40%)': '#4CAF50',
                                    'Medium Margin (20-40%)': '#FF9800',
                                    'Low Margin (<20%)': '#F44336',
                                    'Negative Margin': '#9E9E9E'
                                })
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # 5. SEASONALITY ANALYSIS
        st.divider()
        st.subheader("🌊 Seasonality Analysis")
        
        if not seasonal_pattern.empty:
            fig_seasonal = go.Figure()
            
            fig_seasonal.add_trace(go.Scatter(
                x=seasonal_pattern['Month_Name'],
                y=seasonal_pattern['Seasonal_Index_Revenue'],
                name='Revenue Index',
                mode='lines+markers',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#667eea')
            ))
            
            fig_seasonal.add_trace(go.Scatter(
                x=seasonal_pattern['Month_Name'],
                y=seasonal_pattern['Seasonal_Index_Margin'],
                name='Margin Index',
                mode='lines+markers',
                line=dict(color='#4CAF50', width=3),
                marker=dict(size=8, color='#4CAF50')
            ))
            
            fig_seasonal.add_hline(y=1, line_dash="dash", line_color="gray",
                                 annotation_text="Average = 1.0")
            
            fig_seasonal.update_layout(
                height=400,
                title='Seasonal Indices (Monthly Average = 1.0)',
                xaxis_title='Month',
                yaxis_title='Seasonal Index',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_seasonal, use_container_width=True)
            
            # Season recommendations
            peak_months = seasonal_pattern[seasonal_pattern['Seasonal_Index_Revenue'] >= 1.2]
            low_months = seasonal_pattern[seasonal_pattern['Seasonal_Index_Revenue'] < 0.9]
            
            if not peak_months.empty:
                st.info(f"**📈 Peak Season:** {', '.join(peak_months['Month_Name'].tolist())}")
            
            if not low_months.empty:
                st.warning(f"**📉 Low Season:** {', '.join(low_months['Month_Name'].tolist())}")
        
        # 6. FINANCIAL RECOMMENDATIONS
        st.divider()
        st.subheader("💡 Financial Recommendations")
        
        recommendations = []
        
        # High margin SKU analysis
        if not profitability_segments.empty:
            high_margin_skus = profitability_segments[profitability_segments['Margin_Segment'] == 'High Margin (>40%)']
            low_margin_skus = profitability_segments[profitability_segments['Margin_Segment'] == 'Low Margin (<20%)']
            negative_margin_skus = profitability_segments[profitability_segments['Margin_Segment'] == 'Negative Margin']
            
            if not high_margin_skus.empty:
                recommendations.append(f"✅ **Focus on High Margin SKUs:** {len(high_margin_skus)} SKUs with >40% margin contribute Rp {high_margin_skus['Gross_Margin'].sum():,.0f} margin")
            
            if not low_margin_skus.empty:
                recommendations.append(f"⚠️ **Review Low Margin SKUs:** {len(low_margin_skus)} SKUs with <20% margin")
            
            if not negative_margin_skus.empty:
                recommendations.append(f"❌ **Urgent Action Needed:** {len(negative_margin_skus)} SKUs with negative margin")
        
        # Inventory financial risk
        if not df_inventory_financial.empty:
            slow_moving_high_value = df_inventory_financial[
                (df_inventory_financial['Value_at_Cost'] > 1000) & 
                (df_inventory_financial['Stock_Qty'] > 100)
            ]
            
            if not slow_moving_high_value.empty:
                recommendations.append(f"📉 **Inventory Risk:** {len(slow_moving_high_value)} high-value items (>Rp 1000) with high stock levels")
        
        # Display recommendations
        if recommendations:
            st.markdown("#### 🚀 Action Items:")
            for rec in recommendations:
                st.write(f"- {rec}")
        else:
            st.success("✅ **Excellent financial performance!** No major issues detected.")
            
    else:
        st.warning("Financial data not available. Check price columns in Product Master.")


# --- TAB 9: RESELLER FORECAST ANALYSIS ---
with tab9:
    st.subheader("🤝 Reseller Channel Analysis")
    st.markdown("**Sales History & Forecast Analysis for Reseller Channel**")
    
    if not df_reseller_forecast.empty:
        # ================ SECTION 1: OVERVIEW ================
        st.divider()
        st.subheader("📊 Reseller Channel Overview")
        
        # Calculate totals
        total_historical_qty = df_reseller_forecast[reseller_historical_cols].sum().sum() if reseller_historical_cols else 0
        total_forecast_qty = df_reseller_forecast[reseller_forecast_cols].sum().sum() if reseller_forecast_cols else 0
        
        # Calculate value if price available
        total_historical_value = 0
        total_forecast_value = 0
        
        df_with_price = add_product_info_to_data(df_reseller_forecast, df_product)
        if 'Floor_Price' in df_with_price.columns:
            # Historical value
            for month in reseller_historical_cols:
                total_historical_value += (df_with_price[month] * df_with_price['Floor_Price'].fillna(0)).sum()
            
            # Forecast value
            for month in reseller_forecast_cols:
                total_forecast_value += (df_with_price[month] * df_with_price['Floor_Price'].fillna(0)).sum()
        
        # Display KPIs
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        
        with col_kpi1:
            st.metric("Total SKUs", f"{len(df_reseller_forecast):,}")
        
        with col_kpi2:
            st.metric("Historical Sales Qty", f"{total_historical_qty:,.0f}")
        
        with col_kpi3:
            st.metric("2026 Forecast Qty", f"{total_forecast_qty:,.0f}")
        
        with col_kpi4:
            growth_pct = ((total_forecast_qty - total_historical_qty) / total_historical_qty * 100) if total_historical_qty > 0 else 0
            st.metric("Forecast Growth", f"{growth_pct:+.1f}%")
        
        # ================ SECTION 2: CONNECTED TREND ================
        st.divider()
        st.subheader("📈 Historical Sales vs 2026 Forecast")
        
        # Prepare data for chart
        monthly_data = []
        
        # Add historical data
        if reseller_historical_cols:
            for month in reseller_historical_cols:
                month_qty = df_reseller_forecast[month].sum()
                monthly_data.append({
                    'Period': 'Historical',
                    'Month': month,
                    'Quantity': month_qty,
                    'Month_Date': parse_month_str(month)
                })
        
        # Add forecast data
        if reseller_forecast_cols:
            for month in reseller_forecast_cols:
                month_qty = df_reseller_forecast[month].sum()
                monthly_data.append({
                    'Period': 'Forecast',
                    'Month': month,
                    'Quantity': month_qty,
                    'Month_Date': parse_month_str(month)
                })
        
        if monthly_data:
            trend_df = pd.DataFrame(monthly_data)
            trend_df = trend_df.sort_values('Month_Date')
            trend_df['Month_Display'] = trend_df['Month']
            
            # Create connected chart
            fig = go.Figure()
            
            # Historical line
            hist_df = trend_df[trend_df['Period'] == 'Historical']
            if not hist_df.empty:
                fig.add_trace(go.Scatter(
                    x=hist_df['Month_Display'],
                    y=hist_df['Quantity'],
                    name='Historical Sales',
                    mode='lines+markers',
                    line=dict(color='#4CAF50', width=3),
                    marker=dict(size=6, color='#4CAF50'),
                    hovertemplate='<b>%{x}</b><br>Sales: %{y:,.0f} units<extra></extra>'
                ))
            
            # Forecast line
            forecast_df = trend_df[trend_df['Period'] == 'Forecast']
            if not forecast_df.empty:
                fig.add_trace(go.Scatter(
                    x=forecast_df['Month_Display'],
                    y=forecast_df['Quantity'],
                    name='2026 Forecast',
                    mode='lines+markers',
                    line=dict(color='#667eea', width=3, dash='dash'),
                    marker=dict(size=8, color='#667eea'),
                    hovertemplate='<b>%{x}</b><br>Forecast: %{y:,.0f} units<extra></extra>'
                ))
            
            # Add separator line between historical and forecast
            if not hist_df.empty and not forecast_df.empty:
                last_hist_month = hist_df['Month_Display'].iloc[-1]
                first_forecast_month = forecast_df['Month_Display'].iloc[0]
                
                # Find the gap between historical and forecast
                fig.add_vline(
                    x=(len(hist_df) - 0.5),
                    line_dash="dot",
                    line_color="gray",
                    annotation_text="2026 Forecast Start",
                    annotation_position="top"
                )
            
            fig.update_layout(
                height=500,
                title='Reseller Channel: Historical Sales vs 2026 Forecast',
                xaxis_title='Month',
                yaxis_title='Quantity (units)',
                hovermode='x unified',
                plot_bgcolor='white',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # ================ SECTION 3: BRAND ANALYSIS ================
        st.divider()
        st.subheader("🏷️ Brand Performance - Reseller Channel")
        
        if 'Brand' in df_reseller_forecast.columns:
            # Calculate brand performance
            brand_performance = []
            
            for brand in df_reseller_forecast['Brand'].unique():
                brand_data = df_reseller_forecast[df_reseller_forecast['Brand'] == brand]
                
                # Historical sales
                hist_sales = brand_data[reseller_historical_cols].sum().sum() if reseller_historical_cols else 0
                
                # Forecast
                forecast_qty = brand_data[reseller_forecast_cols].sum().sum() if reseller_forecast_cols else 0
                
                # Growth
                if hist_sales > 0:
                    growth = ((forecast_qty - hist_sales) / hist_sales * 100)
                else:
                    growth = 0
                
                brand_performance.append({
                    'Brand': brand,
                    'Historical_Sales': hist_sales,
                    '2026_Forecast': forecast_qty,
                    'Growth_%': growth,
                    'SKU_Count': len(brand_data)
                })
            
            brand_df = pd.DataFrame(brand_performance)
            brand_df = brand_df.sort_values('2026_Forecast', ascending=False)
            
            # Display charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Historical vs Forecast comparison
                top_brands = brand_df.head(10)
                
                fig_comparison = go.Figure()
                
                fig_comparison.add_trace(go.Bar(
                    x=top_brands['Brand'],
                    y=top_brands['Historical_Sales'],
                    name='Historical Sales',
                    marker_color='#4CAF50'
                ))
                
                fig_comparison.add_trace(go.Bar(
                    x=top_brands['Brand'],
                    y=top_brands['2026_Forecast'],
                    name='2026 Forecast',
                    marker_color='#667eea'
                ))
                
                fig_comparison.update_layout(
                    height=400,
                    title='Top 10 Brands: Historical vs Forecast',
                    xaxis_title='Brand',
                    yaxis_title='Quantity',
                    barmode='group',
                    plot_bgcolor='white'
                )
                
                st.plotly_chart(fig_comparison, use_container_width=True)
            
            with chart_col2:
                # Growth chart
                growth_df = brand_df[brand_df['Historical_Sales'] > 0].copy()
                if not growth_df.empty:
                    growth_df = growth_df.sort_values('Growth_%', ascending=False)
                    
                    fig_growth = go.Figure()
                    
                    # Color based on growth
                    colors = ['#4CAF50' if x >= 0 else '#F44336' for x in growth_df['Growth_%'].head(10)]
                    
                    fig_growth.add_trace(go.Bar(
                        x=growth_df['Brand'].head(10),
                        y=growth_df['Growth_%'].head(10),
                        name='Growth %',
                        marker_color=colors,
                        text=growth_df['Growth_%'].head(10).apply(lambda x: f"{x:+.0f}%"),
                        textposition='auto'
                    ))
                    
                    fig_growth.update_layout(
                        height=400,
                        title='Brand Growth Rate (Historical → 2026)',
                        xaxis_title='Brand',
                        yaxis_title='Growth %',
                        plot_bgcolor='white'
                    )
                    
                    st.plotly_chart(fig_growth, use_container_width=True)
                else:
                    st.info("No historical sales data available for growth calculation")
            
            # Brand summary table
            st.markdown("#### 📋 Brand Performance Summary")
            
            display_brand_df = brand_df.copy()
            display_brand_df['Historical_Sales'] = display_brand_df['Historical_Sales'].apply(lambda x: f"{x:,.0f}")
            display_brand_df['2026_Forecast'] = display_brand_df['2026_Forecast'].apply(lambda x: f"{x:,.0f}")
            display_brand_df['Growth_%'] = display_brand_df['Growth_%'].apply(lambda x: f"{x:+.1f}%")
            
            st.dataframe(
                display_brand_df[['Brand', 'SKU_Count', 'Historical_Sales', '2026_Forecast', 'Growth_%']],
                use_container_width=True,
                height=300
            )
        
        # ================ SECTION 4: QUARTERLY ANALYSIS ================
        st.divider()
        st.subheader("📅 Quarterly Analysis")
        
        # Group by quarter
        def get_quarter_from_month(month_str):
            """Get quarter from month string"""
            try:
                month_date = parse_month_str(month_str)
                quarter = (month_date.month - 1) // 3 + 1
                year = month_date.year
                return f"Q{quarter} {year}"
            except:
                return "Unknown"
        
        # Historical quarterly
        hist_quarterly = {}
        if reseller_historical_cols:
            for month in reseller_historical_cols:
                quarter = get_quarter_from_month(month)
                qty = df_reseller_forecast[month].sum()
                hist_quarterly[quarter] = hist_quarterly.get(quarter, 0) + qty
        
        # Forecast quarterly
        forecast_quarterly = {}
        if reseller_forecast_cols:
            for month in reseller_forecast_cols:
                quarter = get_quarter_from_month(month)
                qty = df_reseller_forecast[month].sum()
                forecast_quarterly[quarter] = forecast_quarterly.get(quarter, 0) + qty
        
        # Combine data
        quarter_data = []
        all_quarters = sorted(set(list(hist_quarterly.keys()) + list(forecast_quarterly.keys())))
        
        for quarter in all_quarters:
            quarter_data.append({
                'Quarter': quarter,
                'Historical': hist_quarterly.get(quarter, 0),
                'Forecast': forecast_quarterly.get(quarter, 0)
            })
        
        if quarter_data:
            quarter_df = pd.DataFrame(quarter_data)
            
            # Quarterly chart
            fig_quarter = go.Figure()
            
            fig_quarter.add_trace(go.Bar(
                x=quarter_df['Quarter'],
                y=quarter_df['Historical'],
                name='Historical Sales',
                marker_color='#4CAF50'
            ))
            
            fig_quarter.add_trace(go.Bar(
                x=quarter_df['Quarter'],
                y=quarter_df['Forecast'],
                name='2026 Forecast',
                marker_color='#667eea'
            ))
            
            fig_quarter.update_layout(
                height=400,
                title='Quarterly Performance: Historical vs Forecast',
                xaxis_title='Quarter',
                yaxis_title='Quantity',
                barmode='group',
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig_quarter, use_container_width=True)
            
            # Quarterly table
            st.markdown("#### 📋 Quarterly Summary")
            
            display_quarter_df = quarter_df.copy()
            display_quarter_df['Historical'] = display_quarter_df['Historical'].apply(lambda x: f"{x:,.0f}")
            display_quarter_df['Forecast'] = display_quarter_df['Forecast'].apply(lambda x: f"{x:,.0f}")
            display_quarter_df['Growth'] = ((display_quarter_df['Forecast'].str.replace(',', '').astype(float) - 
                                          display_quarter_df['Historical'].str.replace(',', '').astype(float)) / 
                                         display_quarter_df['Historical'].str.replace(',', '').astype(float) * 100).apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "N/A")
            
            st.dataframe(
                display_quarter_df,
                use_container_width=True,
                height=200
            )
        
        # ================ SECTION 5: DATA EXPLORER ================
        st.divider()
        st.subheader("📋 Reseller Data Explorer")
        
        # Explorer controls
        exp_col1, exp_col2 = st.columns(2)
        
        with exp_col1:
            reseller_brands = df_reseller_forecast['Brand'].unique().tolist() if 'Brand' in df_reseller_forecast.columns else []
            selected_reseller_brands = st.multiselect(
                "Filter Brands",
                options=reseller_brands,
                default=[],
                key="reseller_brand_filter"
            )
        
        with exp_col2:
            show_data_type = st.selectbox(
                "Show Data",
                options=["Historical Sales", "2026 Forecast", "Both"],
                index=2
            )
        
        # Filter data
        explorer_data = df_reseller_forecast.copy()
        
        if selected_reseller_brands and 'Brand' in explorer_data.columns:
            explorer_data = explorer_data[explorer_data['Brand'].isin(selected_reseller_brands)]
        
        # Select columns based on data type
        if show_data_type == "Historical Sales":
            month_cols = reseller_historical_cols
        elif show_data_type == "2026 Forecast":
            month_cols = reseller_forecast_cols
        else:  # Both
            month_cols = reseller_historical_cols + reseller_forecast_cols
        
        # Select display columns
        base_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 'SKU_Fokus_Notes'] if 'SKU_Fokus_Notes' in explorer_data.columns else ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier']
        display_cols = base_cols + month_cols[:6]  # Show first 6 months
        
        # Filter available columns
        available_cols = [col for col in display_cols if col in explorer_data.columns]
        display_df = explorer_data[available_cols].head(20)
        
        # Format numbers
        for col in month_cols[:6]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "0")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
        
        # Download button
        csv = explorer_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Reseller Data",
            data=csv,
            file_name=f"reseller_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # ================ SECTION 6: INSIGHTS ================
        st.divider()
        st.subheader("💡 Channel Insights")
        
        insights = []
        
        # Insight 1: Total comparison
        insights.append(f"**📊 Total Volume:** Historical Sales (2024-2025): {total_historical_qty:,.0f} units → 2026 Forecast: {total_forecast_qty:,.0f} units")
        
        # Insight 2: Growth rate
        if total_historical_qty > 0:
            overall_growth = ((total_forecast_qty - total_historical_qty) / total_historical_qty * 100)
            growth_color = "📈" if overall_growth > 0 else "📉"
            insights.append(f"**{growth_color} Overall Growth:** {overall_growth:+.1f}% from historical to 2026 forecast")
        else:
            insights.append("**📊 Historical Data:** No historical sales data available for comparison")
        
        # Insight 3: Top brand
        if 'brand_df' in locals() and not brand_df.empty and 'Brand' in brand_df.columns:
            top_brand = brand_df.iloc[0]
            brand_name = top_brand['Brand']
            forecast_qty = top_brand['2026_Forecast']
            
            # Calculate brand share
            if total_forecast_qty > 0:
                brand_share = (forecast_qty / total_forecast_qty * 100)
                insights.append(f"**🏆 Top Brand:** {brand_name} forecasts {forecast_qty:,.0f} units ({brand_share:.1f}% of total forecast)")
            else:
                insights.append(f"**🏆 Top Brand:** {brand_name} forecasts {forecast_qty:,.0f} units")
        
        # Insight 4: Forecast coverage
        if reseller_forecast_cols:
            forecast_months = len(reseller_forecast_cols)
            insights.append(f"**📅 Forecast Period:** {forecast_months} months (Jan-Dec 2026)")
        
        # Insight 5: Historical period
        if reseller_historical_cols:
            historical_months = len(reseller_historical_cols)
            insights.append(f"**📊 Historical Period:** {historical_months} months (Jan 2024 - Dec 2025)")
        
        # Display insights
        for insight in insights:
            st.info(insight)
        
        # Recommendations
        st.markdown("#### 🚀 Channel Strategy Recommendations")
        
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.markdown("""
            **📈 Growth Opportunities:**
            1. **Focus on high-growth brands** identified in analysis
            2. **Develop promotional calendar** for peak forecast months
            3. **Build inventory buffers** for forecasted demand spikes
            4. **Strengthen partnerships** with top-performing resellers
            """)
        
        with rec_col2:
            st.markdown("""
            **🤝 Relationship Management:**
            1. **Share forecast insights** with key reseller partners
            2. **Align production planning** with reseller demand patterns
            3. **Create incentive programs** for forecast accuracy
            4. **Regular performance reviews** with reseller accounts
            """)
    
    else:
        st.warning("⚠️ No Reseller forecast data available. Please check if 'Forecast_2026_Reseller' sheet exists.")

# --- FOOTER ---
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;">
    <p>🚀 <strong>Inventory Intelligence Dashboard v6.0</strong> | Professional Inventory Control & Financial Analytics</p>
    <p>✅ Product Name Auto-Lookup | ✅ Financial Analysis with Price Data | ✅ Inventory Value Analysis</p>
    <p>💰 Profitability Dashboard | 📊 Seasonality Analysis | 🎯 Margin Segmentation</p>
    <p>📈 Data since January 2024 | 🔄 Real-time Google Sheets Integration</p>
</div>
""", unsafe_allow_html=True)
