# pip install openpyxl plotly dash dash-bootstrap-components 
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import html, dcc, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import sys

# --- Định nghĩa các hằng số cho giao diện ---
PLOTLY_TEMPLATE = 'plotly_white'
BLUE_COLORS_DISCRETE = px.colors.qualitative.Pastel

# --- 1. Data Loading and Preprocessing ---
print("Loading data...")
file_path = r"D:\Study\3. CODE\1. Python_code_file\Big_Data\group_assignment\Cleaned_Insurance_Claims_Data.xlsx" # Sửa lại đường dẫn nếu cần
try:
    excel_file = pd.ExcelFile(file_path)
    sheets_needed = ["Participants", "Regions", "Claims Announcements", "Products", "Brokers", "Policies"]
    all_dfs = {}
    for sheet in sheets_needed:
        if sheet in excel_file.sheet_names:
            all_dfs[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
            print(f"Loaded sheet: {sheet}")
        else:
            print(f"Warning: Sheet '{sheet}' not found.")
            all_dfs[sheet] = pd.DataFrame()
except FileNotFoundError:
    print(f"Error: Data file not found at {file_path}")
    sys.exit(f"Exiting: Data file not found.")
except Exception as e:
     print(f"Error loading data: {e}")
     sys.exit("Exiting due to error loading data.")

# === Customer Analysis Data Processing ===
print("Processing Customer data...")
# ... (Giữ nguyên code xử lý Regions, merge Participants và Regions, tính Age -> tạo participants_merged_age_valid) ...
# <<< BẮT ĐẦU CODE XỬ LÝ CUSTOMER >>>
if 'Regions' in all_dfs and not all_dfs['Regions'].empty:
    if 'id' in all_dfs['Regions'].columns:
        all_dfs["Regions"].drop(columns=['water_area', 'type', 'time_zone', 'name', 'county', 'area_code'], inplace=True, errors='ignore')
        all_dfs['Regions'].rename(columns={'id': 'RegionID_Map'}, inplace=True)
    else:
        all_dfs['Regions']['RegionID_Map'] = None

    if 'median_income' in all_dfs["Regions"].columns and 'population' in all_dfs["Regions"].columns and 'state' in all_dfs['Regions'].columns:
        all_dfs["Regions"]['population'] = pd.to_numeric(all_dfs["Regions"]['population'], errors='coerce').fillna(0)
        all_dfs["Regions"]['median_income'] = pd.to_numeric(all_dfs["Regions"]['median_income'], errors='coerce').fillna(0)
        all_dfs["Regions"]["weighted_income"] = all_dfs["Regions"]["median_income"] * all_dfs["Regions"]["population"]
        state_weighted_data = all_dfs["Regions"].groupby("state").agg(
             weighted_income_sum=("weighted_income", "sum"), population_sum=("population", "sum")
        ).reset_index()
        state_weighted_data["weighted_median_income"] = state_weighted_data.apply(
             lambda row: row["weighted_income_sum"] / row["population_sum"] if row["population_sum"] > 0 else 0, axis=1
        )
        weighted_income_dict = dict(zip(state_weighted_data["state"], state_weighted_data["weighted_median_income"]))
        all_dfs["Regions"]["median_income"] = all_dfs["Regions"]["state"].map(weighted_income_dict).fillna(0)
        if "weighted_income" in all_dfs["Regions"].columns:
             all_dfs["Regions"] = all_dfs["Regions"].drop(columns=["weighted_income"])

    agg_cols = ['population', 'land_area', 'households']
    existing_agg_cols = {col: 'sum' for col in agg_cols if col in all_dfs["Regions"].columns}
    if existing_agg_cols and 'state' in all_dfs['Regions'].columns:
        state_totals = all_dfs["Regions"].groupby("state").agg(existing_agg_cols).reset_index()
        for col in existing_agg_cols:
            col_dict = dict(zip(state_totals["state"], state_totals[col]))
            all_dfs["Regions"][col] = all_dfs["Regions"]["state"].map(col_dict).fillna(0)

if 'Participants' in all_dfs and 'Regions' in all_dfs and not all_dfs['Participants'].empty and not all_dfs['Regions'].empty :
    if 'RegionID' in all_dfs['Participants'].columns and 'RegionID_Map' in all_dfs['Regions'].columns:
        regions_renamed = all_dfs["Regions"].add_suffix('_region')
        participants_merged = pd.merge(
            all_dfs["Participants"], regions_renamed.rename(columns={'RegionID_Map_region': 'RegionID'}),
            on="RegionID", how="left"
        )
        cols_from_region = [col for col in participants_merged.columns if col.endswith('_region')]
        participants_merged['state_region'] = participants_merged['state_region'].astype(str).fillna('Unknown')
        for col in ['median_income_region', 'population_region', 'land_area_region', 'households_region']:
            if col in participants_merged.columns: participants_merged[col] = pd.to_numeric(participants_merged[col], errors='coerce').fillna(0)
        for col in ['latitude_region', 'longitude_region']:
            if col in participants_merged.columns: participants_merged[col] = pd.to_numeric(participants_merged[col], errors='coerce')
    else:
        participants_merged = pd.DataFrame(columns=['ParticipantID', 'Gender', 'MaritalStatus', 'BirthDate', 'RegionID', 'state_region'])
else:
    participants_merged = pd.DataFrame(columns=['ParticipantID', 'Gender', 'MaritalStatus', 'BirthDate', 'RegionID', 'state_region'])

if 'BirthDate' in participants_merged.columns:
    participants_merged['BirthDate'] = pd.to_datetime(participants_merged['BirthDate'], errors='coerce')
    current_date = pd.Timestamp('2021-01-01')
    participants_merged['Age'] = participants_merged['BirthDate'].apply(lambda x: (current_date - x).days / 365.25 if pd.notna(x) else np.nan)
    participants_merged_age_valid = participants_merged.dropna(subset=['Age']).copy()
    if not participants_merged_age_valid.empty:
        participants_merged_age_valid['Age'] = participants_merged_age_valid['Age'].astype(int)
        participants_merged_age_valid = participants_merged_age_valid[(participants_merged_age_valid['Age'] >= 0) & (participants_merged_age_valid['Age'] <= 100)]
    else: participants_merged_age_valid = pd.DataFrame(columns=participants_merged.columns.tolist() + ['Age'])
else:
    participants_merged['Age'] = np.nan
    participants_merged_age_valid = participants_merged.copy()

# <<< KẾT THÚC CODE XỬ LÝ CUSTOMER >>>
unique_states = sorted(participants_merged['state_region'].astype(str).unique()) if 'state_region' in participants_merged else []
unique_genders = sorted(participants_merged['Gender'].astype(str).unique()) if 'Gender' in participants_merged else []
AGE_GROUPS_DEF = [(0, 18, 'Under 18'), (18, 30, '18-30'), (30, 45, '30-45'), (45, 60, '45-60'), (60, 101, '60+')]
print("Customer data processed.")


# === Product Analysis Data Processing ===
print("Processing Product data...")
df_claims = all_dfs.get("Claims Announcements", pd.DataFrame())
df_products = all_dfs.get("Products", pd.DataFrame())

if not df_claims.empty and not df_products.empty:
    # ... (Giữ nguyên code xử lý Product -> tạo df_prod) ...
    df_claims['ClosingDate'] = pd.to_datetime(df_claims['ClosingDate'], errors='coerce')
    df_claims['AnnouncementDate'] = pd.to_datetime(df_claims['AnnouncementDate'], errors='coerce')
    df_claims['processTime'] = (df_claims['ClosingDate'] - df_claims['AnnouncementDate']).dt.days
    df_claims = df_claims.dropna(subset=['ClosingDate', 'AnnouncementDate', 'processTime'])
    df_claims = df_claims[df_claims["ClosingDate"].dt.year < 2099]
    df_claims = df_claims[df_claims['processTime'] >= 0]
    required_prod_cols = ['ProductID', 'ProductSubCategory']
    if all(col in df_products.columns for col in required_prod_cols):
         df_products_to_merge = df_products[required_prod_cols].drop_duplicates()
         df_prod = pd.merge(df_claims, df_products_to_merge, how='left', on="ProductID")
         df_prod['ProductSubCategory'] = df_prod['ProductSubCategory'].astype(str).fillna('Unknown')
    else:
         df_prod = df_claims.copy()
         df_prod['ProductSubCategory'] = 'Unknown'
else:
    df_prod = pd.DataFrame(columns=['processTime', 'ProductSubCategory', 'LastForecastAmount', 'ProductID', 'ClaimID'])

unique_subcategories = sorted(df_prod['ProductSubCategory'].unique()) if 'ProductSubCategory' in df_prod else []
print("Product data processed.")


# === Broker Analysis Data Processing ===
print("Processing Broker data...")
df_brokers = all_dfs.get("Brokers", pd.DataFrame())
df_policies = all_dfs.get("Policies", pd.DataFrame())

if not df_claims.empty and not df_brokers.empty:
    # ... (Giữ nguyên code xử lý Broker -> tạo df_broker, policy_with_network) ...
    if 'BrokerID' not in df_claims.columns or 'BrokerID' not in df_brokers.columns:
        print("Warning: BrokerID missing in Claims or Brokers sheet. Broker analysis may be incomplete.")
        df_broker = df_claims.copy(); df_broker['DistributionNetwork'] = 'Unknown'; df_broker['DistributionChannel'] = 'Unknown'; df_broker['CommissionScheme'] = 'Unknown'; df_broker['BrokerFullName'] = 'Unknown'
    else:
        df_broker = pd.merge(df_claims, df_brokers, on="BrokerID", how="left")
        df_broker['ClosingDate'] = pd.to_datetime(df_broker['ClosingDate'], errors='coerce')
        df_broker['AnnouncementDate'] = pd.to_datetime(df_broker['AnnouncementDate'], errors='coerce')
        df_broker['ClaimDuration'] = (df_broker['ClosingDate'] - df_broker['AnnouncementDate']).dt.days
        df_broker = df_broker.dropna(subset=['ClaimDuration'])
        df_broker = df_broker[df_broker['ClaimDuration'] >= 0]
        for col in ['DistributionNetwork', 'DistributionChannel', 'CommissionScheme', 'BrokerFullName']:
             if col in df_broker.columns: df_broker[col] = df_broker[col].astype(str).fillna('Unknown')
             else: df_broker[col] = 'Unknown'
else:
    df_broker = pd.DataFrame(columns=['ClaimID', 'BrokerID', 'LastForecastAmount', 'ClaimDuration', 'DistributionNetwork', 'DistributionChannel', 'CommissionScheme', 'BrokerFullName'])

if not df_policies.empty and not df_brokers.empty and 'BrokerID' in df_policies.columns and 'BrokerID' in df_brokers.columns:
    policy_with_network = pd.merge(
        df_policies, df_brokers[['BrokerID', 'DistributionNetwork', 'DistributionChannel', 'CommissionScheme']].drop_duplicates(),
        on='BrokerID', how='left'
    )
    for col in ['DistributionNetwork', 'DistributionChannel', 'CommissionScheme']:
        if col in policy_with_network.columns: policy_with_network[col] = policy_with_network[col].astype(str).fillna('Unknown')
        else: policy_with_network[col] = 'Unknown'
    if 'AnnualizedPolicyPremium' in policy_with_network.columns: policy_with_network['AnnualizedPolicyPremium'] = pd.to_numeric(policy_with_network['AnnualizedPolicyPremium'], errors='coerce').fillna(0)
    else: policy_with_network['AnnualizedPolicyPremium'] = 0
else:
     policy_with_network = pd.DataFrame(columns=['PolicyID', 'BrokerID', 'AnnualizedPolicyPremium', 'DistributionNetwork', 'DistributionChannel', 'CommissionScheme'])

unique_networks = sorted(df_broker['DistributionNetwork'].unique()) if 'DistributionNetwork' in df_broker else []
unique_schemes = sorted(df_broker['CommissionScheme'].unique()) if 'CommissionScheme' in df_broker else []
print("Broker data processed.")


# --- 2. Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# --- 3. Define Dashboard Layout with Tabs ---
app.layout = dbc.Container([
    dbc.Row([dbc.Col(dbc.Alert(
                # ĐỔI TIÊU ĐỀ Ở ĐÂY
                html.H1("INSURANCE CLAIMS DATA ANALYSIS", className='text-center mb-0 fw-bold'),
                color="primary", className="my-4 shadow"))
            ]),

    dbc.Row([
        dbc.Col(
            dcc.Tabs(id='main-tabs', value='tab-customer', children=[

                # === Tab 1: Customer Relationship Analysis ===
                dcc.Tab(label='Customer Relationship Analysis', value='tab-customer', children=[
                    dbc.Container([
                        dbc.Row([dbc.Col(dbc.Card(dbc.CardBody([dbc.Row([
                                        dbc.Col([html.Label("Select Gender:", className="fw-bold"), dcc.Dropdown(id='gender-dropdown', multi=False, value='All', options=[{'label': 'All Genders', 'value': 'All'}] + [{'label': g, 'value': g} for g in unique_genders], clearable=False)], width=6),
                                        dbc.Col([html.Label("Select State:", className="fw-bold"), dcc.Dropdown(id='state-dropdown', multi=False, value='All', options=[{'label': 'All States', 'value': 'All'}] + [{'label': s, 'value': s} for s in unique_states], clearable=False)], width=6),
                                    ])]), className="mt-4 mb-4 shadow-sm"))
                        ]),
                        dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='age-histogram')])]), width=7, className="mb-4"),
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='age-group-pie')])]), width=5, className="mb-4"),
                        ]),
                        dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='gender-pie')])]), width=5, className="mb-4"),
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='marital-bar')])]), width=7, className="mb-4"),
                        ]),
                    ], fluid=True, className="pt-4")
                ]), # End Tab 1

                # === Tab 2: Products Analysis ===
                dcc.Tab(label='Products Analysis', value='tab-product', children=[
                     dbc.Container([
                        dbc.Row([dbc.Col(dbc.Card(dbc.CardBody([dbc.Row([
                                        dbc.Col([html.Label("Select Product SubCategory:", className="fw-bold"), dcc.Dropdown(id='product-subcategory-dropdown', multi=False, value='All', options=[{'label': 'All SubCategories', 'value': 'All'}] + [{'label': sub, 'value': sub} for sub in unique_subcategories], clearable=False)], width=12),
                                    ])]), className="mt-4 mb-4 shadow-sm"))
                        ]),
                        dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='prod-dist-chart')])]), width=6, className="mb-4"),
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='prod-time-hist')])]), width=6, className="mb-4"),
                        ]),
                         dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='prod-time-cat-chart')])]), width=6, className="mb-4"),
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='prod-forecast-hist')])]), width=6, className="mb-4"),
                        ]),
                     ], fluid=True, className="pt-4")
                ]), # End Tab 2

                # === Tab 3: Broker Analysis ===
                dcc.Tab(label='Broker Analysis', value='tab-broker', children=[
                    dbc.Container([
                        dbc.Row([dbc.Col(dbc.Card(dbc.CardBody([dbc.Row([
                                        dbc.Col([html.Label("Select Distribution Network:", className="fw-bold"), dcc.Dropdown(id='dist-network-dropdown', multi=False, value='All', options=[{'label': 'All Networks', 'value': 'All'}] + [{'label': n, 'value': n} for n in unique_networks], clearable=False)], width=6),
                                        dbc.Col([html.Label("Select Commission Scheme:", className="fw-bold"), dcc.Dropdown(id='comm-scheme-dropdown', multi=False, value='All', options=[{'label': 'All Schemes', 'value': 'All'}] + [{'label': s, 'value': s} for s in unique_schemes], clearable=False)], width=6),
                                    ])]), className="mt-4 mb-4 shadow-sm"))
                        ]),
                        dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='broker-net-premium-chart')])]), width=6, className="mb-4"),
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='broker-net-policy-pie')])]), width=6, className="mb-4"),
                        ]),
                        dbc.Row([dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='broker-channel-chart')])]), width=12, className="mb-4")]),
                        dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='broker-scheme-premium-claim-chart')])]), width=7, className="mb-4"),
                            dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(id='broker-scheme-duration-chart')])]), width=5, className="mb-4"),
                        ]),
                        dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardHeader("Top 10 Brokers Analysis"), dbc.CardBody([
                                dbc.Row([ # Hàng 1 Top 10
                                    dbc.Col(dcc.Graph(id='broker-top10-policy-chart'), width=6),
                                    dbc.Col(dcc.Graph(id='broker-top10-claimfreq-chart'), width=6),
                                ]),
                                dbc.Row([ # Hàng 2 Top 10
                                    dbc.Col(dcc.Graph(id='broker-top10-claimcost-high-chart'), width=6),
                                    dbc.Col(dcc.Graph(id='broker-top10-claimcost-low-chart'), width=6),
                                ]),
                                dbc.Row([ # Hàng 3 Top 10
                                    dbc.Col(dcc.Graph(id='broker-top10-costpolicy-chart'), width=6),
                                    dbc.Col(dcc.Graph(id='broker-top10-lossratio-chart'), width=6),
                                ]),
                                dbc.Row([ # Hàng 4 Top 10 - THÊM BIỂU ĐỒ MỚI VÀO ĐÂY
                                    dbc.Col(dcc.Graph(id='broker-top10-profitratio-chart'), width=6),
                                    dbc.Col(dcc.Graph(id='broker-top10-profitratio-low-chart'), width=6), # Biểu đồ Lowest Profit Ratio
                                ]),
                            ])]), width=12, className="mb-4")
                        ]),
                    ], fluid=True, className="pt-4")
                ]), # End Tab 3

            ]) # End Tabs
        ) # End Col
    ]) # End Row Tabs

], fluid=True)


# --- 4. Define Callbacks ---

# === Callback for Customer Analysis Tab ===
@callback(
    Output('age-histogram', 'figure'),
    Output('age-group-pie', 'figure'),
    Output('gender-pie', 'figure'),
    Output('marital-bar', 'figure'),
    Input('gender-dropdown', 'value'),
    Input('state-dropdown', 'value')
)
def update_customer_charts(selected_gender, selected_state):
    # (Giữ nguyên logic của callback này)
    # ...
    filtered_df = participants_merged_age_valid.copy()
    if selected_gender != 'All':
        if 'Gender' in filtered_df.columns: filtered_df = filtered_df[filtered_df['Gender'] == selected_gender]
    if selected_state != 'All':
        if 'state_region' in filtered_df.columns: filtered_df = filtered_df[filtered_df['state_region'] == selected_state]

    empty_figure = go.Figure().update_layout(template=PLOTLY_TEMPLATE, annotations=[dict(text="No data available for selected filters", xref="paper", yref="paper", showarrow=False, font=dict(size=16))])
    chart_title_suffix = f'({selected_gender}, {selected_state})'

    # Age Histogram
    if not filtered_df.empty and 'Age' in filtered_df.columns and not filtered_df['Age'].isnull().all():
        mean_age_filtered = filtered_df['Age'].mean(); median_age_filtered = filtered_df['Age'].median()
        fig_age = px.histogram(filtered_df, x='Age', nbins=20, title=f'Age Distribution {chart_title_suffix}', labels={'Age': 'Age (years)', 'count': 'Participants'}, template=PLOTLY_TEMPLATE, opacity=0.8)
        fig_age.update_layout(title_font_size=18, bargap=0.1).update_traces(marker_color='#0d6efd')
        if pd.notna(mean_age_filtered): fig_age.add_vline(x=mean_age_filtered, line_dash="dash", line_color="red", annotation_text=f"Mean: {mean_age_filtered:.1f}", annotation_position="top left")
        if pd.notna(median_age_filtered): fig_age.add_vline(x=median_age_filtered, line_dash="dash", line_color="green", annotation_text=f"Median: {median_age_filtered:.1f}", annotation_position="bottom left")
    else: fig_age = go.Figure(empty_figure).update_layout(title=f'No Age Data {chart_title_suffix}')

    # Age Group Pie
    if not filtered_df.empty and 'Age' in filtered_df.columns and not filtered_df['Age'].isnull().all():
        age_group_counts, age_group_labels = [], []
        for min_age, max_age, label in AGE_GROUPS_DEF:
            count = filtered_df[(filtered_df['Age'] >= min_age) & (filtered_df['Age'] < max_age)].shape[0]
            if count > 0: age_group_counts.append(count); age_group_labels.append(label)
        if age_group_counts:
             fig_age_group_pie = px.pie(names=age_group_labels, values=age_group_counts, title=f'Age Group Distribution {chart_title_suffix}', hole=0.4, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE)
             fig_age_group_pie.update_traces(textposition='outside', textinfo='percent+label').update_layout(title_font_size=18, showlegend=False)
        else: fig_age_group_pie = go.Figure(empty_figure).update_layout(title=f'No Age Group Data {chart_title_suffix}')
    else: fig_age_group_pie = go.Figure(empty_figure).update_layout(title=f'No Age Group Data {chart_title_suffix}')

    # Gender Pie
    if not filtered_df.empty and 'Gender' in filtered_df.columns and filtered_df['Gender'].nunique() > 0:
        gender_counts_filtered = filtered_df['Gender'].value_counts()
        fig_gender = px.pie(gender_counts_filtered, values=gender_counts_filtered.values, names=gender_counts_filtered.index, title=f'Gender Distribution ({selected_state})', hole=0.4, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE)
        fig_gender.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='radial').update_layout(title_font_size=18, showlegend=True, legend_title_text='Gender')
    else: fig_gender = go.Figure(empty_figure).update_layout(title=f'No Gender Data {chart_title_suffix}')

    # Marital Status Bar
    if not filtered_df.empty and 'MaritalStatus' in filtered_df.columns and filtered_df['MaritalStatus'].nunique() > 0:
        marital_counts_filtered = filtered_df['MaritalStatus'].value_counts()
        fig_marital = px.bar(marital_counts_filtered, x=marital_counts_filtered.index, y=marital_counts_filtered.values, title=f'Marital Status {chart_title_suffix}', labels={'index': 'Marital Status', 'y': 'Participants'}, text=marital_counts_filtered.values, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE)
        fig_marital.update_traces(texttemplate='%{text:,}', textposition='outside').update_layout(title_font_size=18, xaxis_tickangle=-30)
    else: fig_marital = go.Figure(empty_figure).update_layout(title=f'No Marital Status Data {chart_title_suffix}')

    return fig_age, fig_age_group_pie, fig_gender, fig_marital

# === Callback for Product Analysis Tab ===
@callback(
    Output('prod-dist-chart', 'figure'),
    Output('prod-time-hist', 'figure'),
    Output('prod-time-cat-chart', 'figure'),
    Output('prod-forecast-hist', 'figure'),
    Input('product-subcategory-dropdown', 'value')
)
def update_product_charts(selected_subcategory):
    # (Giữ nguyên logic của callback này)
    # ...
    df_prod_filtered = df_prod.copy()
    if selected_subcategory != 'All':
        if 'ProductSubCategory' in df_prod_filtered.columns: df_prod_filtered = df_prod_filtered[df_prod_filtered['ProductSubCategory'] == selected_subcategory]

    empty_figure = go.Figure().update_layout(template=PLOTLY_TEMPLATE, annotations=[dict(text="No data available for selected filters", xref="paper", yref="paper", showarrow=False, font=dict(size=16))])
    prod_chart_title_suffix = f'({selected_subcategory})'

    # Chart 1: Claim Count by SubCategory
    if not df_prod_filtered.empty and 'ProductSubCategory' in df_prod_filtered.columns:
         prod_counts = df_prod_filtered['ProductSubCategory'].value_counts().reset_index(); prod_counts.columns = ['ProductSubCategory', 'claim_count']
         prod_counts = prod_counts.sort_values('claim_count', ascending=False)
         if not prod_counts.empty:
              fig_prod_dist = px.bar(prod_counts, x='ProductSubCategory', y='claim_count', title=f'Claim Count by SubCategory {prod_chart_title_suffix}', labels={'ProductSubCategory': 'Sub Category', 'claim_count': 'Number of Claims'}, text='claim_count', template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE)
              fig_prod_dist.update_traces(texttemplate='%{text:,}', textposition='outside').update_layout(title_font_size=18, xaxis_tickangle=-45)
         else: fig_prod_dist = go.Figure(empty_figure).update_layout(title=f'No Claim Count Data {prod_chart_title_suffix}')
    else: fig_prod_dist = go.Figure(empty_figure).update_layout(title=f'No Claim Count Data {prod_chart_title_suffix}')

    # Chart 2: Process time histogram
    if not df_prod_filtered.empty and 'processTime' in df_prod_filtered.columns and not df_prod_filtered['processTime'].isnull().all():
        fig_prod_time_hist = px.histogram(df_prod_filtered, x='processTime', nbins=30, title=f'Process Time Distribution {prod_chart_title_suffix}', labels={'processTime': 'Days', 'count': 'Number of Claims'}, template=PLOTLY_TEMPLATE)
        fig_prod_time_hist.update_layout(title_font_size=18, bargap=0.1).update_traces(marker_color='#5bc0de')
    else: fig_prod_time_hist = go.Figure(empty_figure).update_layout(title=f'No Process Time Data {prod_chart_title_suffix}')

    # Chart 3: Average Process time by category (Bar Chart)
    if not df_prod_filtered.empty and 'processTime' in df_prod_filtered.columns and 'ProductSubCategory' in df_prod_filtered.columns and not df_prod_filtered['processTime'].isnull().all():
        if selected_subcategory == 'All' or df_prod_filtered['ProductSubCategory'].nunique() > 1 : avg_process_time = df_prod_filtered.groupby('ProductSubCategory')['processTime'].mean().reset_index()
        else: avg_process_time = df_prod_filtered[['ProductSubCategory', 'processTime']].drop_duplicates(); avg_process_time['processTime'] = avg_process_time['processTime'].mean()
        avg_process_time = avg_process_time.sort_values('processTime', ascending=False)
        if not avg_process_time.empty:
            fig_prod_time_cat = px.bar(avg_process_time, y='ProductSubCategory', x='processTime', orientation='h', title=f'Average Process Time by SubCategory {prod_chart_title_suffix}', labels={'processTime': 'Average Days', 'ProductSubCategory': 'Sub Category'}, text='processTime', template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE)
            fig_prod_time_cat.update_traces(texttemplate='%{text:.0f} days', textposition='outside').update_layout(title_font_size=18, yaxis={'categoryorder':'total ascending'})
        else: fig_prod_time_cat = go.Figure(empty_figure).update_layout(title=f'No Avg Process Time Data {prod_chart_title_suffix}')
    else: fig_prod_time_cat = go.Figure(empty_figure).update_layout(title=f'No Avg Process Time Data {prod_chart_title_suffix}')

    # Chart 4: Frequency distribution of last forecast amount
    if not df_prod_filtered.empty and 'LastForecastAmount' in df_prod_filtered.columns and not df_prod_filtered['LastForecastAmount'].isnull().all():
         df_forecast_valid = df_prod_filtered[df_prod_filtered['LastForecastAmount'] >= 0]
         if not df_forecast_valid.empty:
             fig_prod_forecast_hist = px.histogram(df_forecast_valid, x='LastForecastAmount', nbins=30, title=f'Last Forecast Amount Distribution {prod_chart_title_suffix}', labels={'LastForecastAmount': 'Amount ($)', 'count': 'Frequency'}, template=PLOTLY_TEMPLATE)
             fig_prod_forecast_hist.update_layout(title_font_size=18, bargap=0.1).update_traces(marker_color='#337ab7')
         else: fig_prod_forecast_hist = go.Figure(empty_figure).update_layout(title=f'No Valid Forecast Data {prod_chart_title_suffix}')
    else: fig_prod_forecast_hist = go.Figure(empty_figure).update_layout(title=f'No Forecast Data {prod_chart_title_suffix}')

    return fig_prod_dist, fig_prod_time_hist, fig_prod_time_cat, fig_prod_forecast_hist

# === Callback for Broker Analysis Tab ===
@callback(
    Output('broker-net-premium-chart', 'figure'),
    Output('broker-net-policy-pie', 'figure'),
    Output('broker-channel-chart', 'figure'),
    Output('broker-scheme-premium-claim-chart', 'figure'),
    Output('broker-scheme-duration-chart', 'figure'),
    Output('broker-top10-policy-chart', 'figure'),
    Output('broker-top10-claimcost-high-chart', 'figure'),
    Output('broker-top10-claimcost-low-chart', 'figure'),
    Output('broker-top10-claimfreq-chart', 'figure'),
    Output('broker-top10-costpolicy-chart', 'figure'),
    Output('broker-top10-lossratio-chart', 'figure'),
    Output('broker-top10-profitratio-chart', 'figure'),
    # THÊM OUTPUT MỚI
    Output('broker-top10-profitratio-low-chart', 'figure'),
    Input('dist-network-dropdown', 'value'),
    Input('comm-scheme-dropdown', 'value')
)
def update_broker_charts(selected_network, selected_scheme):
    # (Giữ nguyên phần lọc dữ liệu từ code trước)
    df_broker_filtered = df_broker.copy()
    policy_with_network_filtered = policy_with_network.copy()
    if selected_network != 'All':
        if 'DistributionNetwork' in df_broker_filtered.columns: df_broker_filtered = df_broker_filtered[df_broker_filtered['DistributionNetwork'] == selected_network]
        if 'DistributionNetwork' in policy_with_network_filtered.columns: policy_with_network_filtered = policy_with_network_filtered[policy_with_network_filtered['DistributionNetwork'] == selected_network]
    if selected_scheme != 'All':
        if 'CommissionScheme' in df_broker_filtered.columns: df_broker_filtered = df_broker_filtered[df_broker_filtered['CommissionScheme'] == selected_scheme]
        if 'CommissionScheme' in policy_with_network_filtered.columns: policy_with_network_filtered = policy_with_network_filtered[policy_with_network_filtered['CommissionScheme'] == selected_scheme]

    # Figure trống
    empty_figure = go.Figure().update_layout(template=PLOTLY_TEMPLATE, annotations=[dict(text="No data for filter", xref="paper", yref="paper", showarrow=False, font=dict(size=16))])
    broker_chart_title_suffix = f'({selected_network}, {selected_scheme})'
    title_size = 16

    # --- Tính toán lại các bảng summary ---
    # Network Summary
    network_summary_filtered = policy_with_network_filtered.groupby('DistributionNetwork').agg(PolicyCount=('PolicyID', 'count'),TotalPolicyPremium=('AnnualizedPolicyPremium', 'sum')).reset_index()
    if not network_summary_filtered.empty and 'PolicyCount' in network_summary_filtered.columns and network_summary_filtered['PolicyCount'].sum() > 0 : network_summary_filtered['AvgPremium'] = network_summary_filtered['TotalPolicyPremium'] / network_summary_filtered['PolicyCount']
    else: network_summary_filtered['AvgPremium'] = 0

    # Channel Summary
    policy_channel_summary = policy_with_network_filtered.groupby('DistributionChannel').agg(PolicyCount=('PolicyID', 'count'), TotalPolicyPremium=('AnnualizedPolicyPremium', 'sum')).reset_index()
    claims_channel_summary = df_broker_filtered.groupby('DistributionChannel').agg(ClaimCount=('ClaimID', 'count'), TotalForecastAmount=('LastForecastAmount', 'sum')).reset_index()
    channel_summary_filtered = pd.merge(policy_channel_summary, claims_channel_summary, on='DistributionChannel', how='outer').fillna(0)
    if not channel_summary_filtered.empty and 'PolicyCount' in channel_summary_filtered.columns and channel_summary_filtered['PolicyCount'].sum() > 0 :
        channel_summary_filtered['ClaimPerPolicy'] = channel_summary_filtered['ClaimCount'] / channel_summary_filtered['PolicyCount']
        channel_summary_filtered['PremiumPerPolicy'] = channel_summary_filtered['TotalPolicyPremium'] / channel_summary_filtered['PolicyCount']
        channel_summary_filtered['ForecastPerPolicy'] = channel_summary_filtered['TotalForecastAmount'] / channel_summary_filtered['PolicyCount']
    else:
        channel_summary_filtered['ClaimPerPolicy'] = 0; channel_summary_filtered['PremiumPerPolicy'] = 0; channel_summary_filtered['ForecastPerPolicy'] = 0
    channel_long_filtered = channel_summary_filtered.melt(id_vars='DistributionChannel', value_vars=['PremiumPerPolicy', 'ClaimPerPolicy', 'ForecastPerPolicy'], var_name='Metric', value_name='Value')

    # Commission Scheme Summary
    policy_cs_summary = policy_with_network_filtered.groupby('CommissionScheme').agg(PolicyCount=('PolicyID', 'count'), TotalPolicyPremium=('AnnualizedPolicyPremium', 'sum')).reset_index()
    claims_cs_summary = df_broker_filtered.groupby('CommissionScheme').agg(ClaimCount=('ClaimID', 'count'), TotalForecastAmount=('LastForecastAmount', 'sum')).reset_index()
    cs_forecast_filtered = pd.merge(policy_cs_summary, claims_cs_summary, on='CommissionScheme', how='outer').fillna(0)
    if not cs_forecast_filtered.empty and 'PolicyCount' in cs_forecast_filtered.columns and cs_forecast_filtered['PolicyCount'].sum() > 0:
        cs_forecast_filtered['AvgTotalPremiumPerPolicy'] = cs_forecast_filtered['TotalPolicyPremium'] / cs_forecast_filtered['PolicyCount']
        cs_forecast_filtered['AvgForecastClaimPerPolicy'] = cs_forecast_filtered['TotalForecastAmount'] / cs_forecast_filtered['PolicyCount']
    else: cs_forecast_filtered['AvgTotalPremiumPerPolicy'] = 0; cs_forecast_filtered['AvgForecastClaimPerPolicy'] = 0
    cs_long_filtered = cs_forecast_filtered.melt(id_vars='CommissionScheme', value_vars=['AvgTotalPremiumPerPolicy', 'AvgForecastClaimPerPolicy'], var_name='Metric', value_name='Value')

    # Top 10 Broker Calculations
    policy_counts_broker = policy_with_network_filtered.groupby('BrokerID').size().reset_index(name='PolicyCount')
    policy_counts_broker = pd.merge(policy_counts_broker, df_brokers[['BrokerID','BrokerFullName']], on='BrokerID', how='left')
    top10_policies_filt = policy_counts_broker.sort_values("PolicyCount", ascending=False).head(10)

    avg_claim_cost_broker = df_broker_filtered.groupby('BrokerID')['LastForecastAmount'].mean().reset_index(name='AvgClaimCost')
    avg_claim_cost_broker = pd.merge(avg_claim_cost_broker, df_brokers[['BrokerID','BrokerFullName']], on='BrokerID', how='left')
    top10_high_cost_filt = avg_claim_cost_broker.sort_values("AvgClaimCost", ascending=False).head(10)
    top10_low_cost_filt = avg_claim_cost_broker.sort_values("AvgClaimCost", ascending=True).head(10)

    claims_per_broker_filt = df_broker_filtered.groupby('BrokerID').size().reset_index(name='ClaimCount')
    policy_counts_filt = policy_with_network_filtered.groupby('BrokerID').size().reset_index(name='PolicyCount')
    freq_df_filt = pd.merge(claims_per_broker_filt, policy_counts_filt, on='BrokerID', how='inner')
    if not freq_df_filt.empty and freq_df_filt['PolicyCount'].sum() > 0: freq_df_filt['ClaimFrequency'] = freq_df_filt['ClaimCount'] / freq_df_filt['PolicyCount']
    else: freq_df_filt['ClaimFrequency'] = 0
    freq_df_filt = pd.merge(freq_df_filt, df_brokers[['BrokerID','BrokerFullName']], on='BrokerID', how='left')
    top10_freq_filt = freq_df_filt.sort_values("ClaimFrequency", ascending=False).head(10)

    total_cost_by_broker_filt = df_broker_filtered.groupby('BrokerID')['LastForecastAmount'].sum().reset_index(name='TotalClaimCost')
    cost_policy_df_filt = pd.merge(total_cost_by_broker_filt, policy_counts_filt, on='BrokerID', how='inner')
    if not cost_policy_df_filt.empty and cost_policy_df_filt['PolicyCount'].sum() > 0: cost_policy_df_filt['CostPerPolicy'] = cost_policy_df_filt['TotalClaimCost'] / cost_policy_df_filt['PolicyCount']
    else: cost_policy_df_filt['CostPerPolicy'] = 0
    cost_policy_df_filt = pd.merge(cost_policy_df_filt, df_brokers[['BrokerID','BrokerFullName']], on='BrokerID', how='left')
    top10_cost_policy_filt = cost_policy_df_filt.sort_values("CostPerPolicy", ascending=False).head(10)

    claims_cost_filt = df_broker_filtered.groupby('BrokerID')['LastForecastAmount'].sum().reset_index(name='TotalClaimCost')
    premiums_filt = policy_with_network_filtered.groupby('BrokerID')['AnnualizedPolicyPremium'].sum().reset_index(name='TotalPremium')
    loss_df_filt = pd.merge(claims_cost_filt, premiums_filt, on='BrokerID', how='inner')
    if not loss_df_filt.empty:
        loss_df_filt['LossRatio'] = loss_df_filt.apply(lambda row: row['TotalClaimCost'] / row['TotalPremium'] if row['TotalPremium'] > 0 else 0, axis=1)
        loss_df_filt['ProfitRatio'] = loss_df_filt.apply(lambda row: row['TotalPremium'] / row['TotalClaimCost'] if row['TotalClaimCost'] > 0 else np.inf, axis=1)
    else: loss_df_filt['LossRatio'] = 0; loss_df_filt['ProfitRatio'] = 0
    loss_df_filt = pd.merge(loss_df_filt, df_brokers[['BrokerID','BrokerFullName']], on='BrokerID', how='left')
    top10_loss_filt = loss_df_filt.sort_values("LossRatio", ascending=False).head(10)
    # Lấy top 10 Profit cao nhất (bỏ inf)
    top10_profit_filt = loss_df_filt.replace([np.inf, -np.inf], np.nan).dropna(subset=['ProfitRatio']).sort_values("ProfitRatio", ascending=False).head(10)
    # Lấy top 10 Profit thấp nhất (bỏ inf, sắp xếp tăng dần)
    top10_profit_low_filt = loss_df_filt.replace([np.inf, -np.inf], np.nan).dropna(subset=['ProfitRatio']).sort_values("ProfitRatio", ascending=True).head(10)

    # --- Tạo Figures ---
    # (Giữ nguyên code tạo các figure khác từ code trước)
    # ... fig_net_premium, fig_net_policy_pie, fig_channel, fig_scheme_prem_claim, fig_scheme_duration ...
    # Network Premium Bar
    if not network_summary_filtered.empty: fig_net_premium = px.bar(network_summary_filtered, x='DistributionNetwork', y='AvgPremium', title=f'Avg Premium by Network {broker_chart_title_suffix}', labels={'AvgPremium': 'Avg Annualized Premium'}, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE).update_layout(title_font_size=title_size, xaxis_tickangle=-30)
    else: fig_net_premium = go.Figure(empty_figure).update_layout(title='No Network Premium Data')
    # Network Policy Pie
    if not network_summary_filtered.empty and network_summary_filtered['PolicyCount'].sum() > 0: fig_net_policy_pie = px.pie(network_summary_filtered, names='DistributionNetwork', values='PolicyCount', title=f'Policy Distribution by Network {broker_chart_title_suffix}', hole=0.4, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE).update_traces(textposition='inside', textinfo='percent+label').update_layout(title_font_size=title_size, showlegend=False)
    else: fig_net_policy_pie = go.Figure(empty_figure).update_layout(title='No Network Policy Data')
    # Channel Grouped Bar
    if not channel_long_filtered.empty: fig_channel = px.bar(channel_long_filtered, x='DistributionChannel', y='Value', color='Metric', barmode='group', title=f'Channel Metrics {broker_chart_title_suffix}', labels={'Value': 'Average Value per Policy'}, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE).update_layout(title_font_size=title_size, xaxis_tickangle=-45)
    else: fig_channel = go.Figure(empty_figure).update_layout(title='No Channel Data')
    # Scheme Grouped Bar (Premium vs Claim)
    if not cs_long_filtered.empty: fig_scheme_prem_claim = px.bar(cs_long_filtered, x='CommissionScheme', y='Value', color='Metric', barmode='group', title=f'Avg Premium vs Forecast Claim by Scheme {broker_chart_title_suffix}', labels={'Value': 'Average Value per Policy'}, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE).update_layout(title_font_size=title_size, xaxis_tickangle=-45)
    else: fig_scheme_prem_claim = go.Figure(empty_figure).update_layout(title='No Scheme Premium/Claim Data')
    # Scheme Duration Violin
    if not df_broker_filtered.empty and 'ClaimDuration' in df_broker_filtered.columns and not df_broker_filtered['ClaimDuration'].isnull().all():
         lower_bound_v = df_broker_filtered['ClaimDuration'].quantile(0.02); upper_bound_v = df_broker_filtered['ClaimDuration'].quantile(0.98)
         df_broker_violin = df_broker_filtered[(df_broker_filtered['ClaimDuration'] >= lower_bound_v) & (df_broker_filtered['ClaimDuration'] <= upper_bound_v)]
         if not df_broker_violin.empty:
              fig_scheme_duration = px.violin(df_broker_violin, x='CommissionScheme', y='ClaimDuration', title=f'Claim Duration Distribution by Scheme {broker_chart_title_suffix}', labels={'ClaimDuration': 'Claim Duration (days)'}, template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE).update_layout(title_font_size=title_size, xaxis_tickangle=-45)
         else: fig_scheme_duration = go.Figure(empty_figure).update_layout(title=f'No Scheme Duration Data (after trim)')
    else: fig_scheme_duration = go.Figure(empty_figure).update_layout(title=f'No Scheme Duration Data')

    # Top 10 Charts
    fig_top10_policy = px.bar(top10_policies_filt, y='BrokerFullName', x='PolicyCount', orientation='h', title=f'Top 10 Policy Count {broker_chart_title_suffix}', labels={'PolicyCount': 'Policy Count'}, text='PolicyCount', template=PLOTLY_TEMPLATE, color_discrete_sequence=BLUE_COLORS_DISCRETE).update_layout(yaxis={'categoryorder':'total ascending'}, title_font_size=title_size) if not top10_policies_filt.empty else go.Figure(empty_figure).update_layout(title='No Top Policy Data')
    fig_top10_cost_h = px.bar(top10_high_cost_filt, y='BrokerFullName', x='AvgClaimCost', orientation='h', title=f'Top 10 Highest Avg Claim Cost {broker_chart_title_suffix}', labels={'AvgClaimCost': 'Avg Claim Cost ($)'}, text='AvgClaimCost', template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Pastel1).update_layout(yaxis={'categoryorder':'total ascending'}, title_font_size=title_size) if not top10_high_cost_filt.empty else go.Figure(empty_figure).update_layout(title='No Top High Cost Data')
    fig_top10_cost_l = px.bar(top10_low_cost_filt, y='BrokerFullName', x='AvgClaimCost', orientation='h', title=f'Top 10 Lowest Avg Claim Cost {broker_chart_title_suffix}', labels={'AvgClaimCost': 'Avg Claim Cost ($)'}, text='AvgClaimCost', template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Pastel2).update_layout(yaxis={'categoryorder':'total descending'}, title_font_size=title_size) if not top10_low_cost_filt.empty else go.Figure(empty_figure).update_layout(title='No Top Low Cost Data')
    fig_top10_freq = px.bar(top10_freq_filt, y='BrokerFullName', x='ClaimFrequency', orientation='h', title=f'Top 10 Highest Claim Freq {broker_chart_title_suffix}', labels={'ClaimFrequency': 'Avg Claims per Policy'}, text='ClaimFrequency', template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Set1).update_layout(yaxis={'categoryorder':'total ascending'}, title_font_size=title_size) if not top10_freq_filt.empty else go.Figure(empty_figure).update_layout(title='No Top Freq Data')
    fig_top10_costpol = px.bar(top10_cost_policy_filt, y='BrokerFullName', x='CostPerPolicy', orientation='h', title=f'Top 10 Highest Claim Cost/Policy {broker_chart_title_suffix}', labels={'CostPerPolicy': 'Cost per Policy ($)'}, text='CostPerPolicy', template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Set2).update_layout(yaxis={'categoryorder':'total ascending'}, title_font_size=title_size) if not top10_cost_policy_filt.empty else go.Figure(empty_figure).update_layout(title='No Top Cost/Policy Data')
    fig_top10_loss = px.bar(top10_loss_filt, y='BrokerFullName', x='LossRatio', orientation='h', title=f'Top 10 Highest Loss Ratio {broker_chart_title_suffix}', labels={'LossRatio': 'Loss Ratio'}, text='LossRatio', template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Set3).update_layout(yaxis={'categoryorder':'total ascending'}, title_font_size=title_size) if not top10_loss_filt.empty else go.Figure(empty_figure).update_layout(title='No Top Loss Ratio Data')
    fig_top10_profit = px.bar(top10_profit_filt, y='BrokerFullName', x='ProfitRatio', orientation='h', title=f'Top 10 Highest Profit Ratio {broker_chart_title_suffix}', labels={'ProfitRatio': 'Profit Ratio'}, text='ProfitRatio', template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Safe).update_layout(yaxis={'categoryorder':'total ascending'}, title_font_size=title_size) if not top10_profit_filt.empty else go.Figure(empty_figure).update_layout(title='No Top Profit Ratio Data')

    # TẠO FIGURE MỚI CHO LOWEST PROFIT RATIO
    fig_top10_profit_low = px.bar(top10_profit_low_filt, y='BrokerFullName', x='ProfitRatio', orientation='h', title=f'Top 10 Lowest Profit Ratio {broker_chart_title_suffix}', labels={'ProfitRatio': 'Profit Ratio'}, text='ProfitRatio', template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Pastel1).update_layout(yaxis={'categoryorder':'total descending'}, title_font_size=title_size) if not top10_profit_low_filt.empty else go.Figure(empty_figure).update_layout(title='No Top Low Profit Ratio Data')


    # Cập nhật định dạng text cho các bar chart top 10
    for fig in [fig_top10_policy, fig_top10_cost_h, fig_top10_cost_l, fig_top10_costpol, fig_top10_loss, fig_top10_profit, fig_top10_profit_low]: # Thêm fig mới
        if fig.data: fig.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
    if fig_top10_freq.data: fig_top10_freq.update_traces(texttemplate='%{text:.2f}', textposition='outside')


    # TRẢ VỀ FIGURE MỚI Ở CUỐI
    return (fig_net_premium, fig_net_policy_pie, fig_channel, fig_scheme_prem_claim,
            fig_scheme_duration, fig_top10_policy, fig_top10_cost_h, fig_top10_cost_l,
            fig_top10_freq, fig_top10_costpol, fig_top10_loss, fig_top10_profit, fig_top10_profit_low)


# --- 5. Run the App ---
if __name__ == '__main__':
    print("Starting Dash server...")
    app.run(debug=True, port=8050)
    
