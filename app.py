import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import gspread
from google.oauth2.service_account import Credentials
import warnings
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
</style>
""", unsafe_allow_html=True)

# --- Judul Dashboard ---
st.markdown('<h1 class="main-header">📊 INVENTORY INTELLIGENCE DASHBOARD</h1>', unsafe_allow_html=True)
st.caption(f"🚀 Professional Inventory Control & Demand Planning | Real-time Analytics | Updated: {datetime.now().strftime('%d %B %Y %H:%M')}")

# --- ====================================================== ---
# ---                KONEKSI & LOAD DATA                     ---
# --- ====================================================== ---

@st.cache_resource(show_spinner=False)
def init_gsheet_connection():
    """Inisialisasi koneksi ke Google Sheets"""
    try:
        skey = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(skey, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Koneksi Gagal: {str(e)}")
        return None

def parse_month_label(label):
    """Parse berbagai format bulan ke datetime"""
    try:
        label_str = str(label).strip().upper()
        month_map = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                     'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
        for month_name, month_num in month_map.items():
            if month_name in label_str:
                year_part = label_str.replace(month_name, '').replace('-', '').replace(' ', '').strip()
                if year_part:
                    year = int('20' + year_part) if len(year_part) == 2 else int(year_part)
                else:
                    year = datetime.now().year
                return datetime(year, month_num, 1)
        return datetime.now()
    except:
        return datetime.now()

@st.cache_data(ttl=300, show_spinner=False)
def load_and_process_data(_client):
    """Load dan proses semua data dengan proteksi tipe data"""
    gsheet_url = st.secrets["gsheet_url"]
    data = {}
    try:
        # 1. PRODUCT MASTER
        ws = _client.open_by_url(gsheet_url).worksheet("Product_Master")
        df_product = pd.DataFrame(ws.get_all_records())
        df_product.columns = [col.strip().replace(' ', '_') for col in df_product.columns]
        
        # --- FIX 1: Ensure SKU_ID is String & Trimmed ---
        if 'SKU_ID' in df_product.columns:
            df_product['SKU_ID'] = df_product['SKU_ID'].astype(str).str.strip()
            
        # Ensure Status column
        if 'Status' not in df_product.columns:
            df_product['Status'] = 'Active'
            
        # --- FIX 2: Drop duplicates in Master to prevent merge explosion ---
        df_product = df_product.drop_duplicates(subset=['SKU_ID'])
        
        df_product_active = df_product[df_product['Status'].str.upper() == 'ACTIVE'].copy()
        active_skus = df_product_active['SKU_ID'].tolist()
        
        # Helper to load transaction data
        def load_transaction_sheet(sheet_name, value_name):
            ws_temp = _client.open_by_url(gsheet_url).worksheet(sheet_name)
            df_raw = pd.DataFrame(ws_temp.get_all_records())
            df_raw.columns = [col.strip() for col in df_raw.columns]
            
            # --- FIX 3: Ensure SKU_ID is String ---
            if 'SKU_ID' in df_raw.columns:
                df_raw['SKU_ID'] = df_raw['SKU_ID'].astype(str).str.strip()
                
            month_cols = [col for col in df_raw.columns if any(m in col.upper() for m in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])]
            
            if month_cols and 'SKU_ID' in df_raw.columns:
                # Keep necessary cols to avoid conflicts (SKU_ID Centric)
                cols_to_keep = ['SKU_ID'] + month_cols
                df_long = df_raw[cols_to_keep].melt(
                    id_vars=['SKU_ID'],
                    value_vars=month_cols,
                    var_name='Month_Label',
                    value_name=value_name
                )
                df_long[value_name] = pd.to_numeric(df_long[value_name], errors='coerce').fillna(0)
                df_long['Month'] = df_long['Month_Label'].apply(parse_month_label)
                # --- FIX 4: Force Datetime ---
                df_long['Month'] = pd.to_datetime(df_long['Month'])
                
                return df_long[df_long['SKU_ID'].isin(active_skus)]
            return pd.DataFrame()

        # 2. LOAD TRANSACTIONS
        data['sales'] = load_transaction_sheet("Sales", "Sales_Qty")
        data['forecast'] = load_transaction_sheet("Rofo", "Forecast_Qty")
        data['po'] = load_transaction_sheet("PO", "PO_Qty")
        
        # 5. STOCK DATA
        ws_stock = _client.open_by_url(gsheet_url).worksheet("Stock_Onhand")
        df_stock_raw = pd.DataFrame(ws_stock.get_all_records())
        df_stock_raw.columns = [col.strip().replace(' ', '_') for col in df_stock_raw.columns]
        
        if 'SKU_ID' in df_stock_raw.columns:
            df_stock_raw['SKU_ID'] = df_stock_raw['SKU_ID'].astype(str).str.strip()
        
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
            data['stock'] = df_stock
        else:
            data['stock'] = pd.DataFrame(columns=['SKU_ID', 'Stock_Qty'])
            
        data['product'] = df_product
        data['product_active'] = df_product_active
        
        return data
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return {}

# --- ====================================================== ---
# ---                ANALYTICS FUNCTIONS                     ---
# --- ====================================================== ---

def calculate_monthly_performance(df_forecast, df_po, df_product):
    monthly_performance = {}
    if df_forecast.empty or df_po.empty: return monthly_performance
    
    try:
        # --- FIX 5: Explicit Copy & Datetime Enforcement ---
        df_f = df_forecast.copy()
        df_p = df_po.copy()
        df_f['Month'] = pd.to_datetime(df_f['Month'])
        df_p['Month'] = pd.to_datetime(df_p['Month'])
        
        # Merge
        df_merged = pd.merge(df_f, df_p, on=['SKU_ID', 'Month'], how='inner', suffixes=('_forecast', '_po'))
        
        if not df_merged.empty:
            if not df_product.empty:
                product_info = df_product[['SKU_ID', 'Product_Name', 'SKU_Tier', 'Brand']].drop_duplicates()
                df_merged = pd.merge(df_merged, product_info, on='SKU_ID', how='left')
            
            df_merged['PO_Rofo_Ratio'] = np.where(
                df_merged['Forecast_Qty'] > 0, (df_merged['PO_Qty'] / df_merged['Forecast_Qty']) * 100, 0
            )
            
            conditions = [
                df_merged['PO_Rofo_Ratio'] < 80,
                (df_merged['PO_Rofo_Ratio'] >= 80) & (df_merged['PO_Rofo_Ratio'] <= 120),
                df_merged['PO_Rofo_Ratio'] > 120
            ]
            df_merged['Accuracy_Status'] = np.select(conditions, ['Under', 'Accurate', 'Over'], default='Unknown')
            
            df_merged['Absolute_Percentage_Error'] = abs(df_merged['PO_Rofo_Ratio'] - 100)
            
            for month in sorted(df_merged['Month'].unique()):
                month_data = df_merged[df_merged['Month'] == month].copy()
                mape = month_data['Absolute_Percentage_Error'].mean()
                
                status_counts = month_data['Accuracy_Status'].value_counts().to_dict()
                total_records = len(month_data)
                status_percentages = {k: (v/total_records*100) for k, v in status_counts.items()}
                
                monthly_performance[month] = {
                    'accuracy': 100 - mape,
                    'mape': mape,
                    'status_counts': status_counts,
                    'status_percentages': status_percentages,
                    'total_records': total_records,
                    'data': month_data,
                    'under_skus': month_data[month_data['Accuracy_Status'] == 'Under'].copy(),
                    'over_skus': month_data[month_data['Accuracy_Status'] == 'Over'].copy()
                }
        return monthly_performance
    except Exception as e:
        st.error(f"Monthly perf error: {str(e)}")
        return monthly_performance

def get_last_3_months_performance(monthly_performance):
    if not monthly_performance: return {}
    sorted_months = sorted(monthly_performance.keys())
    last_3_months = sorted_months[-3:] if len(sorted_months) >= 3 else sorted_months
    return {month: monthly_performance[month] for month in last_3_months}

def calculate_inventory_metrics_with_3month_avg(df_stock, df_sales, df_product):
    metrics = {}
    if df_stock.empty: return metrics
    
    try:
        # Calculate Avg Sales 3 Months
        if not df_sales.empty:
            df_s = df_sales.copy()
            df_s['Month'] = pd.to_datetime(df_s['Month'])
            sales_months = sorted(df_s['Month'].unique())
            last_3_sales_months = sales_months[-3:] if len(sales_months) >= 3 else sales_months
            df_sales_last_3 = df_s[df_s['Month'].isin(last_3_sales_months)].copy()
            
            avg_monthly_sales = df_sales_last_3.groupby('SKU_ID')['Sales_Qty'].mean().reset_index()
            avg_monthly_sales.columns = ['SKU_ID', 'Avg_Monthly_Sales_3M']
        else:
            avg_monthly_sales = pd.DataFrame(columns=['SKU_ID', 'Avg_Monthly_Sales_3M'])
        
        df_inventory = pd.merge(df_stock, df_product[['SKU_ID', 'Product_Name', 'SKU_Tier', 'Brand', 'Status']], on='SKU_ID', how='left')
        df_inventory = pd.merge(df_inventory, avg_monthly_sales, on='SKU_ID', how='left')
        df_inventory['Avg_Monthly_Sales_3M'] = df_inventory['Avg_Monthly_Sales_3M'].fillna(0)
        
        df_inventory['Cover_Months'] = np.where(
            df_inventory['Avg_Monthly_Sales_3M'] > 0,
            df_inventory['Stock_Qty'] / df_inventory['Avg_Monthly_Sales_3M'], 999
        )
        
        conditions = [
            df_inventory['Cover_Months'] < 0.8,
            (df_inventory['Cover_Months'] >= 0.8) & (df_inventory['Cover_Months'] <= 1.5),
            df_inventory['Cover_Months'] > 1.5
        ]
        df_inventory['Inventory_Status'] = np.select(conditions, ['Need Replenishment', 'Ideal/Healthy', 'High Stock'], default='Unknown')
        
        high_stock_df = df_inventory[df_inventory['Inventory_Status'] == 'High Stock'].copy()
        
        if 'SKU_Tier' in df_inventory.columns:
            tier_analysis = df_inventory.groupby('SKU_Tier').agg({
                'SKU_ID': 'count', 'Stock_Qty': 'sum', 'Avg_Monthly_Sales_3M': 'sum', 'Cover_Months': 'mean'
            }).reset_index()
            tier_analysis.columns = ['Tier', 'SKU_Count', 'Total_Stock', 'Total_Sales_3M_Avg', 'Avg_Cover_Months']
            metrics['tier_analysis'] = tier_analysis
            
        metrics['inventory_df'] = df_inventory
        metrics['high_stock'] = high_stock_df
        metrics['total_stock'] = df_inventory['Stock_Qty'].sum()
        metrics['total_skus'] = len(df_inventory)
        metrics['avg_cover'] = df_inventory[df_inventory['Cover_Months'] < 999]['Cover_Months'].mean()
        
        return metrics
    except Exception as e:
        st.error(f"Inventory metrics error: {str(e)}")
        return metrics

def calculate_sales_vs_forecast_po(df_sales, df_forecast, df_po, df_product):
    results = {}
    if df_sales.empty or df_forecast.empty: return results
    
    try:
        # --- FIX 6: Force Datetime ---
        df_s = df_sales.copy(); df_s['Month'] = pd.to_datetime(df_s['Month'])
        df_f = df_forecast.copy(); df_f['Month'] = pd.to_datetime(df_f['Month'])
        df_p = df_po.copy(); df_p['Month'] = pd.to_datetime(df_p['Month'])
        
        common_months = sorted(set(df_s['Month']) & set(df_f['Month']) & set(df_p['Month']))
        if not common_months: return results
        
        last_month = common_months[-1]
        
        df_s_m = df_s[df_s['Month'] == last_month]
        df_f_m = df_f[df_f['Month'] == last_month]
        df_p_m = df_p[df_p['Month'] == last_month]
        
        df_merged = pd.merge(df_s_m[['SKU_ID', 'Sales_Qty']], df_f_m[['SKU_ID', 'Forecast_Qty']], on='SKU_ID', how='inner')
        df_merged = pd.merge(df_merged, df_p_m[['SKU_ID', 'PO_Qty']], on='SKU_ID', how='left')
        
        if not df_product.empty:
            prod_info = df_product[['SKU_ID', 'Product_Name', 'SKU_Tier', 'Brand']].drop_duplicates()
            df_merged = pd.merge(df_merged, prod_info, on='SKU_ID', how='left')
            
        df_merged['Sales_vs_Forecast_Ratio'] = np.where(df_merged['Forecast_Qty']>0, (df_merged['Sales_Qty']/df_merged['Forecast_Qty'])*100, 0)
        df_merged['Sales_vs_PO_Ratio'] = np.where(df_merged['PO_Qty']>0, (df_merged['Sales_Qty']/df_merged['PO_Qty'])*100, 0)
        
        df_merged['Forecast_Deviation'] = abs(df_merged['Sales_vs_Forecast_Ratio'] - 100)
        df_merged['PO_Deviation'] = abs(df_merged['Sales_vs_PO_Ratio'] - 100)
        
        high_deviation_skus = df_merged[(df_merged['Forecast_Deviation'] > 30) | (df_merged['PO_Deviation'] > 30)].copy()
        
        results = {
            'last_month': last_month,
            'comparison_data': df_merged,
            'high_deviation_skus': high_deviation_skus,
            'avg_forecast_deviation': df_merged['Forecast_Deviation'].mean(),
            'avg_po_deviation': df_merged['PO_Deviation'].mean(),
            'total_skus_compared': len(df_merged)
        }
        return results
    except Exception as e:
        st.error(f"Sales analysis error: {e}")
        return results

def calculate_brand_performance(df_forecast, df_po, df_product):
    if df_forecast.empty or df_po.empty or df_product.empty: return pd.DataFrame()
    try:
        # --- FIX 7: Force Datetime ---
        df_f = df_forecast.copy(); df_f['Month'] = pd.to_datetime(df_f['Month'])
        df_p = df_po.copy(); df_p['Month'] = pd.to_datetime(df_p['Month'])
        
        common_months = sorted(set(df_f['Month']) & set(df_p['Month']))
        if not common_months: return pd.DataFrame()
        
        last_month = common_months[-1]
        df_f_m = df_f[df_f['Month'] == last_month]
        df_p_m = df_p[df_p['Month'] == last_month]
        
        df_merged = pd.merge(df_f_m, df_p_m, on=['SKU_ID'], how='inner', suffixes=('_forecast', '_po'))
        
        brand_info = df_product[['SKU_ID', 'Brand']].drop_duplicates()
        df_merged = pd.merge(df_merged, brand_info, on='SKU_ID', how='left')
        
        df_merged['PO_Rofo_Ratio'] = np.where(df_merged['Forecast_Qty']>0, (df_merged['PO_Qty']/df_merged['Forecast_Qty'])*100, 0)
        
        conditions = [
            df_merged['PO_Rofo_Ratio'] < 80,
            (df_merged['PO_Rofo_Ratio'] >= 80) & (df_merged['PO_Rofo_Ratio'] <= 120),
            df_merged['PO_Rofo_Ratio'] > 120
        ]
        df_merged['Accuracy_Status'] = np.select(conditions, ['Under', 'Accurate', 'Over'], default='Unknown')
        
        brand_perf = df_merged.groupby('Brand').agg({
            'SKU_ID': 'count',
            'Forecast_Qty': 'sum',
            'PO_Qty': 'sum',
            'PO_Rofo_Ratio': lambda x: 100 - abs(x - 100).mean()
        }).reset_index()
        
        brand_perf.columns = ['Brand', 'SKU_Count', 'Total_Forecast', 'Total_PO', 'Accuracy']
        brand_perf['PO_vs_Forecast_Ratio'] = (brand_perf['Total_PO'] / brand_perf['Total_Forecast'] * 100)
        brand_perf['Qty_Difference'] = brand_perf['Total_PO'] - brand_perf['Total_Forecast']
        
        status_counts = df_merged.groupby(['Brand', 'Accuracy_Status']).size().unstack(fill_value=0).reset_index()
        brand_perf = pd.merge(brand_perf, status_counts, on='Brand', how='left').fillna(0)
        
        return brand_perf
    except Exception as e:
        st.error(f"Brand error: {e}")
        return pd.DataFrame()

# --- ====================================================== ---
# ---                DASHBOARD INITIALIZATION                ---
# --- ====================================================== ---

client = init_gsheet_connection()
if client is None: st.stop()

with st.spinner('🔄 Loading and processing data from Google Sheets...'):
    all_data = load_and_process_data(client)
    df_product = all_data.get('product', pd.DataFrame())
    df_product_active = all_data.get('product_active', pd.DataFrame())
    df_sales = all_data.get('sales', pd.DataFrame())
    df_forecast = all_data.get('forecast', pd.DataFrame())
    df_po = all_data.get('po', pd.DataFrame())
    df_stock = all_data.get('stock', pd.DataFrame())

monthly_performance = calculate_monthly_performance(df_forecast, df_po, df_product)
last_3_months_performance = get_last_3_months_performance(monthly_performance)
inventory_metrics = calculate_inventory_metrics_with_3month_avg(df_stock, df_sales, df_product)
sales_vs_forecast = calculate_sales_vs_forecast_po(df_sales, df_forecast, df_po, df_product)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Dashboard Controls")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    if not df_product_active.empty: st.metric("Active SKUs", len(df_product_active))
    if not df_stock.empty: st.metric("Total Stock", f"{df_stock['Stock_Qty'].sum():,.0f}")
    if monthly_performance:
        last = sorted(monthly_performance.keys())[-1]
        st.metric("Latest Accuracy", f"{monthly_performance[last]['accuracy']:.1f}%")

# --- MAIN DASHBOARD ---

# SECTION 1: LAST 3 MONTHS PERFORMANCE
st.subheader("🎯 Forecast Performance - 3 Bulan Terakhir")

if last_3_months_performance:
    month_cols = st.columns(3)
    for i, (month, data) in enumerate(sorted(last_3_months_performance.items())):
        month_name = month.strftime('%b %Y')
        accuracy = data['accuracy']
        with month_cols[i]:
            uc = data['status_counts'].get('Under', 0)
            ac = data['status_counts'].get('Accurate', 0)
            oc = data['status_counts'].get('Over', 0)
            tr = data['total_records']
            
            st.markdown(f"""
            <div class="monthly-performance-card performance-{('accurate' if accuracy >= 80 else 'under')}">
                <h3 style="margin:0; text-align:center;">{month_name}</h3>
                <div style="text-align:center; font-size:2rem; font-weight:bold; color:#667eea; margin:10px 0;">{accuracy:.1f}%</div>
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-top:10px;">
                    <span style="color:#D32F2F"><b>Und: {uc}</b></span>
                    <span style="color:#2E7D32"><b>Acc: {ac}</b></span>
                    <span style="color:#E65100"><b>Ovr: {oc}</b></span>
                </div>
                <div style="text-align:center; font-size:0.8rem; color:#888; margin-top:5px;">Total: {tr} SKUs</div>
            </div>
            """, unsafe_allow_html=True)
            
    # TOTAL METRICS
    st.divider()
    st.subheader("📊 Total Metrics - Bulan Terakhir")
    last_month = sorted(monthly_performance.keys())[-1]
    last_data = monthly_performance[last_month]['data']
    
    u_c = last_data[last_data['Accuracy_Status']=='Under']['SKU_ID'].nunique()
    a_c = last_data[last_data['Accuracy_Status']=='Accurate']['SKU_ID'].nunique()
    o_c = last_data[last_data['Accuracy_Status']=='Over']['SKU_ID'].nunique()
    tot_c = last_data['SKU_ID'].nunique()
    
    u_q = last_data[last_data['Accuracy_Status']=='Under']['Forecast_Qty'].sum()
    a_q = last_data[last_data['Accuracy_Status']=='Accurate']['Forecast_Qty'].sum()
    o_q = last_data[last_data['Accuracy_Status']=='Over']['Forecast_Qty'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="compact-metric" style="border-left:4px solid #F44336">
        <div style="color:#666; font-size:0.8rem">UNDER FORECAST</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#F44336">{u_c}</div>
        <div style="font-size:0.8rem">Qty: {u_q:,.0f}</div>
        </div>""", unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""<div class="compact-metric" style="border-left:4px solid #4CAF50">
        <div style="color:#666; font-size:0.8rem">ACCURATE</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#4CAF50">{a_c}</div>
        <div style="font-size:0.8rem">Qty: {a_q:,.0f}</div>
        </div>""", unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""<div class="compact-metric" style="border-left:4px solid #FF9800">
        <div style="color:#666; font-size:0.8rem">OVER FORECAST</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#FF9800">{o_c}</div>
        <div style="font-size:0.8rem">Qty: {o_q:,.0f}</div>
        </div>""", unsafe_allow_html=True)
        
    with col4:
         acc = monthly_performance[last_month]['accuracy']
         st.markdown(f"""<div class="compact-metric" style="border-left:4px solid #667eea">
        <div style="color:#666; font-size:0.8rem">OVERALL</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#667eea">{acc:.1f}%</div>
        <div style="font-size:0.8rem">{last_month.strftime('%b %Y')}</div>
        </div>""", unsafe_allow_html=True)

    # ROFO VS PO TOTAL
    st.divider()
    st.subheader("📈 Total Rofo vs PO - Bulan Terakhir")
    t_rofo = last_data['Forecast_Qty'].sum()
    t_po = last_data['PO_Qty'].sum()
    diff = t_po - t_rofo
    
    r1, r2, r3, r4 = st.columns(4)
    with r1: st.metric("Total Rofo Qty", f"{t_rofo:,.0f}")
    with r2: st.metric("Total PO Qty", f"{t_po:,.0f}")
    with r3: st.metric("Selisih Qty", f"{diff:+,.0f}", delta_color="off")
    with r4: st.metric("Accurate SKU %", f"{(a_c/tot_c*100):.1f}%")

else:
    st.warning("⚠️ Insufficient data.")

st.divider()

# --- TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Monthly Details", "🏷️ Brand & Tier", "📦 Inventory", "🔍 SKU Eval", "📈 Sales", "📋 Explorer"
])

# TAB 1: MONTHLY DETAILS
with tab1:
    if monthly_performance:
        sum_data = []
        for m, d in sorted(monthly_performance.items()):
            sum_data.append({
                'Month': m.strftime('%b %Y'),
                'Accuracy': d['accuracy'],
                'Under': d['status_counts'].get('Under',0),
                'Accurate': d['status_counts'].get('Accurate',0),
                'Over': d['status_counts'].get('Over',0),
                'Total': d['total_records']
            })
        st.dataframe(pd.DataFrame(sum_data), use_container_width=True)
        
        # Chart
        trend_df = pd.DataFrame(sum_data)
        chart = alt.Chart(trend_df).mark_line(point=True).encode(
            x='Month', y='Accuracy', tooltip=['Month', 'Accuracy']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

# TAB 2: BRAND & TIER
with tab2:
    st.subheader("🏷️ Brand Performance")
    brand_df = calculate_brand_performance(df_forecast, df_po, df_product)
    if not brand_df.empty:
        st.dataframe(brand_df.style.format({'Accuracy': "{:.1f}%"}), use_container_width=True)
        
        chart = alt.Chart(brand_df).mark_bar().encode(
            x=alt.X('Brand', sort='-y'), y='Accuracy', color='Brand'
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    
    st.divider()
    st.subheader("🏷️ Tier Analysis")
    if monthly_performance:
        last_m = sorted(monthly_performance.keys())[-1]
        tier_data = monthly_performance[last_m]['data']
        if 'SKU_Tier' in tier_data.columns:
            tier_summ = tier_data.groupby('SKU_Tier').agg({
                'SKU_ID':'count', 'PO_Rofo_Ratio': lambda x: 100 - abs(x-100).mean()
            }).reset_index()
            tier_summ.columns = ['Tier', 'Count', 'Accuracy']
            st.dataframe(tier_summ.style.format({'Accuracy': "{:.1f}%"}), use_container_width=True)

# TAB 3: INVENTORY
with tab3:
    st.subheader("📦 Inventory Health")
    if inventory_metrics:
        inv = inventory_metrics['inventory_df']
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Replenish", len(inv[inv['Inventory_Status']=='Need Replenishment']))
        with c2: st.metric("Ideal", len(inv[inv['Inventory_Status']=='Ideal/Healthy']))
        with c3: st.metric("High", len(inv[inv['Inventory_Status']=='High Stock']))
        
        st.dataframe(inv[['SKU_ID', 'Product_Name', 'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months', 'Inventory_Status']], use_container_width=True)

# TAB 4: SKU EVALUATION
with tab4:
    st.subheader("🔍 SKU Performance")
    if monthly_performance:
        last_m = sorted(monthly_performance.keys())[-1]
        data = monthly_performance[last_m]['data']
        
        if 'inventory_df' in inventory_metrics:
            inv_info = inventory_metrics['inventory_df'][['SKU_ID', 'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']]
            data = pd.merge(data, inv_info, on='SKU_ID', how='left')
        
        cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 'Accuracy_Status', 'Forecast_Qty', 'PO_Qty', 'PO_Rofo_Ratio', 'Stock_Qty', 'Avg_Monthly_Sales_3M', 'Cover_Months']
        avail_cols = [c for c in cols if c in data.columns]
        
        st.dataframe(data[avail_cols], use_container_width=True)

# TAB 5: SALES
with tab5:
    st.subheader("📈 Sales Analysis")
    if sales_vs_forecast:
        res = sales_vs_forecast
        st.metric("Avg Forecast Deviation", f"{res['avg_forecast_deviation']:.1f}%")
        st.dataframe(res['high_deviation_skus'][['SKU_ID', 'Product_Name', 'Sales_Qty', 'Forecast_Qty', 'Forecast_Deviation']], use_container_width=True)

# TAB 6: DATA
with tab6:
    opt = st.selectbox("Dataset", ["Sales", "Forecast", "PO", "Stock"])
    d_map = {"Sales": all_data['sales'], "Forecast": all_data['forecast'], "PO": all_data['po'], "Stock": all_data['stock']}
    st.dataframe(d_map[opt], use_container_width=True)
