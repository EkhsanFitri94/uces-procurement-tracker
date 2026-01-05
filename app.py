import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="UCES Procurement Analytics",
    page_icon="📊",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stDataFrame { width: 100%; }
    h1 { color: #2E4053; }
    h2 { color: #283747; }
    .metric-label { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: File Upload & SharePoint Setup ---
st.sidebar.title("📂 Data Source")

# OPTION 1: File Upload
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

# OPTION 2: SharePoint URL (For Deployment)
sharepoint_url = st.sidebar.text_input("Or paste SharePoint File URL", placeholder="https://company.sharepoint.com/...")
sharepoint_access = st.sidebar.radio("SharePoint Access", ["None", "Internal Network", "VPN Required"], index=1)

# --- Data Processing Function ---
@st.cache_data # This decorator keeps the file in memory so you don't have to re-upload on refresh
def load_data(uploaded_file):
    try:
        # 1. Read Excel
        df = pd.read_excel(uploaded_file) 
        
        # 2. Clean Column Names (remove spaces)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 3. LOGIC MAP: Map ACTUAL columns to STANDARD internal names
        # We check if column exists FIRST, then rename.
        
        renamed_cols = {}
        
        # -- Amounts --
        if 'App_Amount' in df.columns: pass
        elif 'Total_Paid' in df.columns: renamed_cols['Total_Paid'] = 'App_Amount'
        elif 'Payment Amount' in df.columns: renamed_cols['Payment Amount'] = 'App_Amount'
        elif 'Total Paid' in df.columns: renamed_cols['Total Paid'] = 'App_Amount'
        
        # -- PO Values --
        if 'App_PO_Value' in df.columns: pass
        elif 'Total_PO_Value' in df.columns: renamed_cols['Total_PO_Value'] = 'App_PO_Value'
        elif 'Total PO Value' in df.columns: renamed_cols['Total PO Value'] = 'App_PO_Value'
        elif 'Total PO Value ' in df.columns: renamed_cols['Total PO Value '] = 'App_PO_Value'
        
        # -- Percentages --
        if 'App_Percent' in df.columns: pass
        elif 'Actual_Payment_%' in df.columns: renamed_cols['Actual_Payment_%'] = 'App_Percent'
        elif 'Payment %' in df.columns: renamed_cols['Payment %'] = 'App_Percent'
        elif 'Actual_Payment_% ' in df.columns: renamed_cols['Actual_Payment_% '] = 'App_Percent'
        
        # -- Dates --
        if 'App_Date' in df.columns: pass
        elif 'PO_Date' in df.columns: renamed_cols['PO_Date'] = 'App_Date'
        elif 'PO DATE' in df.columns: renamed_cols['PO DATE'] = 'App_Date'
        elif 'PO_Date ' in df.columns: renamed_cols['PO_Date '] = 'App_Date'
        elif 'Invoice Date' in df.columns: renamed_cols['Invoice Date'] = 'App_Date'
        elif 'Invoice Date ' in df.columns: renamed_cols['Invoice Date '] = 'App_Date'
        elif 'PR DATE' in df.columns: renamed_cols['PR DATE'] = 'App_Date'

        # -- Vendor --
        if 'Vendor_Name' in df.columns: pass
        elif 'Vendor' in df.columns: renamed_cols['Vendor'] = 'Vendor_Name'
        elif 'VENDOR' in df.columns: renamed_cols['VENDOR'] = 'Vendor_Name'
        
        # -- Project Manager --
        if 'Project_Manager' in df.columns: pass
        elif 'Project Manager' in df.columns: renamed_cols['Project Manager'] = 'Project_Manager'
        elif 'Project Manager ' in df.columns: renamed_cols['Project Manager '] = 'Project_Manager'

        # Apply Renaming
        if renamed_cols:
            df = df.rename(columns=renamed_cols)

        # 4. ENSURE CRITICAL COLUMNS EXIST
        if 'App_Amount' not in df.columns:
            st.error("❌ Critical Error: 'App_Amount' column not found after processing.")
            st.write("🔍 Found Columns:", df.columns.tolist())
            return pd.DataFrame()

        # 5. HANDLE DATE COLUMN (Safe conversion)
        if 'App_Date' in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df['App_Date']):
                pass 
            else:
                df['App_Date'] = pd.to_datetime(df['App_Date'], errors='coerce')
        else:
            # Fallback: Create dummy date if missing
            df['App_Date'] = pd.Timestamp.now()

        # 6. HANDLE NUMERIC COLUMNS (Safe conversion)
        numeric_cols = ['App_Amount', 'App_PO_Value', 'App_Percent']
        for col in numeric_cols:
            if col in df.columns:
                def to_float(val):
                    try:
                        return float(str(val).replace(',', '').replace('RM', '').replace('-', '0').strip())
                    except:
                        return 0.0
                df[col] = df[col].apply(to_float).fillna(0)

        return df

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        # For debugging, print the columns we found
        if 'df' in locals():
            st.write("📋 Columns detected in file:", df.columns.tolist())
        return pd.DataFrame()

# --- Main Execution Logic ---
df = None

if uploaded_file:
    df = load_data(uploaded_file)
    if not df.empty:
        st.success(f"✅ Data loaded successfully! {len(df)} rows found.")
        st.info("💡 Tip: Use the 'Download' button below to save this CSV to your SharePoint folder.")
elif sharepoint_url:
    st.info("🌐 SharePoint Mode: URL detected. (Note: Direct SharePoint web access requires specific enterprise libraries not included in this free Streamlit version).")
    st.info("💡 **Recommended Workflow:**")
    st.write("1. Click the 'Download' button on the Dashboard below.")
    st.write("2. Upload the downloaded CSV to your SharePoint Library.")
    st.write("3. Refresh this app and open the CSV from SharePoint.")
else:
    st.info("👈 Please upload a local Excel file to begin.")

# --- Stop if no data ---
if df is None or df.empty:
    st.stop()

# --- TABS SETUP ---
tab1, tab2, tab3 = st.tabs(["📊 Tracker Dashboard", "📈 Advanced Analytics", "📋 Raw Data"])

# ================= TAB 1: TRACKER DASHBOARD =================
with tab1:
    st.title("UCES Sdn Bhd Procurement Tracker 2026")
    
    # --- KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_spend = df['App_Amount'].sum()
    total_po_value = df['App_PO_Value'].sum()
    
    vendor_col = 'Vendor_Name' if 'Vendor_Name' in df.columns else 'Vendor'
    unique_vendors = df[vendor_col].nunique() if vendor_col in df.columns else 0
    pending_pos = len(df[df['App_Percent'] < 99.9])

    col1.metric("Total Payments", f"RM {total_spend:,.2f}")
    col2.metric("Total PO Value", f"RM {total_po_value:,.2f}")
    col3.metric("Unique Vendors", unique_vendors)
    col4.metric("Pending / Partial POs", pending_pos)

    st.markdown("---")

    # --- Filters ---
    with st.sidebar:
        st.header("🔍 Filters")
        
        pm_col = 'Project_Manager' if 'Project_Manager' in df.columns else 'Project Manager'
        if pm_col in df.columns:
            pm_list = ['All'] + sorted(df[pm_col].dropna().unique().tolist())
            selected_pm = st.sidebar.selectbox("Project Manager", pm_list)
        else:
            selected_pm = 'All'

        if vendor_col in df.columns:
            vendor_search = st.sidebar.text_input("Search Vendor Name")
        else:
            vendor_search = ""

        # Apply Filters
        df_view = df.copy()
        
        if selected_pm != 'All' and pm_col in df.columns:
            df_view = df_view[df_view[pm_col] == selected_pm]
        
        if vendor_search and vendor_col in df.columns:
            df_view = df_view[df_view[vendor_col].str.contains(vendor_search, case=False, na=False)]

        status_filter = st.sidebar.radio("Payment Status", ["All", "Fully Paid (100%)", "Partial / Pending"])
        if status_filter == "Fully Paid (100%)":
            df_view = df_view[df_view['App_Percent'] >= 99.9]
        elif status_filter == "Partial / Pending":
            df_view = df_view[df_view['App_Percent'] < 99.9]

    # --- Charts ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Spend by Project Manager")
        if pm_col in df.columns:
            pm_spend = df_view.groupby(pm_col)['App_Amount'].sum().reset_index()
            fig_pm = px.bar(pm_spend, x=pm_col, y='App_Amount', color='App_Amount', template='plotly_white')
            st.plotly_chart(fig_pm, use_container_width=True)
    
    with chart_col2:
        st.subheader("Vendor Concentration (Top 10)")
        if vendor_col in df.columns:
            # FIX: Used .head(10) instead of .hard(10)
            top_vendors = df_view.groupby(vendor_col)['App_Amount'].sum().sort_values(ascending=False).head(10).reset_index()
            if not top_vendors.empty:
                fig_vendor = px.pie(top_vendors, values='App_Amount', names=vendor_col, hole=0.4)
                st.plotly_chart(fig_vendor, use_container_width=True)

    st.markdown("---")

    # --- Data Table ---
    st.subheader("PO Details")
    
    desired_columns = [
        ('PO No', 'PO No'), 
        ('PR_No', 'PR No'), 
        ('Vendor_Name', 'Vendor'), 
        ('Project_Manager', 'Project Manager'), 
        ('App_PO_Value', 'Total PO Value'), 
        ('App_Amount', 'Total Paid'), 
        ('App_Percent', 'Payment %')
    ]
    
    # Dynamically build list of columns to display
    actual_display_cols = []
    for (internal, fallback) in desired_columns:
        if internal in df.columns:
            actual_display_cols.append(internal)
        elif fallback in df.columns:
            actual_display_cols.append(fallback)
            
    # Sort data
    df_view_sorted = df_view.sort_values(by='App_Date', ascending=False)

    st.dataframe(
        df_view_sorted[actual_display_cols], 
        use_container_width=True,
        column_config={
            "App_Amount": st.column_config.NumberColumn("Total Paid (RM)", format="RM %.2f"),
            "App_PO_Value": st.column_config.NumberColumn("PO Value (RM)", format="RM %.2f"),
            "App_Percent": st.column_config.ProgressColumn("Status", format="%.1f%%", min_value=0, max_value=100)
        }
    )


# ================= TAB 2: ADVANCED ANALYTICS =================
with tab2:
    st.header("📈 Advanced Procurement Analytics")
    
    # 1. Financial Health (Cumulative Flow)
    st.subheader("💰 Financial Health (Payment vs. Outstanding)")
    
    daily_flow = df_view.copy()
    daily_flow['YearMonth'] = pd.to_datetime(daily_flow['App_Date']).dt.to_period('M')
    
    monthly_stats = daily_flow.groupby('YearMonth').agg(
        Paid=('App_Amount', 'sum'),
        PO_Value=('App_PO_Value', 'sum')
    ).reset_index()
    
    monthly_stats['Outstanding'] = monthly_stats['PO_Value'] - monthly_stats['Paid']
    
    fig_flow = go.Figure()
    fig_flow.add_trace(go.Bar(x=monthly_stats['YearMonth'].astype(str), y=monthly_stats['Paid'], name='Paid Amount', marker_color='#2ECC71'))
    fig_flow.add_trace(go.Bar(x=monthly_stats['YearMonth'].astype(str), y=monthly_stats['Outstanding'], name='Outstanding Balance', marker_color='#E74C3C'))
    
    fig_flow.update_layout(barmode='stack', xaxis_title="Month", yaxis_title="Amount (RM)", legend_title="Cash Flow")
    st.plotly_chart(fig_flow, use_container_width=True)

    st.markdown("*This chart shows the cumulative value of POs generated vs. how much has been paid. The gap is your current liability.*")

    # 2. Project Budget vs. Actual Spend
    st.subheader("🏗️ Project Budget vs. Actual Spend")
    
    if pm_col in df.columns:
        project_spend = df_view.groupby(pm_col).agg(
            Budget=('App_PO_Value', 'sum'), 
            Actual=('App_Amount', 'sum')
        ).reset_index()
        
        project_spend['Variance'] = project_spend['Budget'] - project_spend['Actual']
        project_spend = project_spend.sort_values(by='Budget', ascending=False)
        
        fig_budget = px.bar(
            project_spend, 
            x=pm_col, 
            y=['Budget', 'Actual'], 
            barmode='group',
            text_auto=True,
            template='plotly_white'
        )
        fig_budget.update_layout(yaxis_title="Amount (RM)", xaxis_title="Project", legend_title="Budget vs Actual")
        st.plotly_chart(fig_budget, use_container_width=True)

    # 3. Payment Terms Analysis (Invoice Aging)
    st.subheader("⏳ Pending Invoice Analysis (Aging)")
    
    pending_df = df_view[df_view['App_Percent'] < 99.9]
    
    if 'App_Date' in pending_df.columns:
        today = pd.Timestamp.now()
        pending_df['Age_Days'] = (today - pending_df['App_Date']).dt.days
    else:
        pending_df['Age_Days'] = 0

    def get_age_bucket(days):
        if days <= 30: return '0-30 Days'
        elif days <= 60: return '31-60 Days'
        elif days <= 90: return '61-90 Days'
        else: return '90+ Days'
    
    pending_df['Age_Bucket'] = pending_df['Age_Days'].apply(get_age_bucket)
    
    # Try to use PO No or first column if available for count
    count_col = 'PO No' if 'PO No' in pending_df.columns else pending_df.columns[0]
    
    aging_data = pending_df.groupby('Age_Bucket').agg(
        Count=(count_col, 'count'),
        Total_Value=('App_PO_Value', 'sum')
    ).reset_index()
    
    fig_aging = px.bar(aging_data, x='Age_Bucket', y='Total_Value', color='Age_Bucket', template='plotly_white', text='Total_Value')
    fig_aging.update_layout(yaxis_title="Outstanding Amount (RM)", xaxis_title="Invoice Age", showlegend=False)
    st.plotly_chart(fig_aging, fig_aging, use_container_width=True) # Displayed both chart and table
    
    with st.expander("View Detailed Aging Data"):
        st.dataframe(pending_df[['PO No', 'App_Date', 'Age_Days', 'App_PO_Value', 'App_Percent']])


# ================= TAB 3: RAW DATA =================
with tab3:
    st.header("📋 Raw Data View")
    
    st.dataframe(
        df.sort_values(by='App_Date', ascending=False),
        use_container_width=True,
        height=400
    )

# --- Download Button (SharePoint Ready) ---
csv = df_view.to_csv(index=False).encode('utf-8')

# Provide clear instructions
st.sidebar.markdown("---")
st.sidebar.header("📥 SharePoint Export")

st.sidebar.write("Step 1: Download the file using button below.")
st.sidebar.write("Step 2: Upload the .csv to your SharePoint Document Library.")

st.download_button(
    label="📥 Download Filtered Data (for SharePoint)",
    data=csv,
    file_name='UCES_Procurement_Export.csv',
    mime='text/csv',
)