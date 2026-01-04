"""
Overview Tab - Main dashboard with KPIs and visualizations.

Displays:
- Financial summary (income, expenses, balance)
- Category breakdown charts
- Monthly trends
- Budget progress
- Recent transactions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from utils.date_helpers import get_date_range_presets
from database.budget_operations import get_budgets
from config import CURRENCY_SYMBOL
from ui.aggrid_table import render_aggrid_table


class DashboardMetrics:
    """Calculate core dashboard metrics."""
    
    @staticmethod
    def calculate_kpis(transactions: pd.DataFrame, date_range: Tuple[str, str]) -> Dict:
        """Calculate high-level KPIs for the top row."""
        start_date, end_date = date_range
        
        # Filter for selected period
        mask = (transactions['date_obj'] >= start_date) & (transactions['date_obj'] <= end_date)
        period_txns = transactions.loc[mask]
        
        if period_txns.empty:
            return {
                'income': 0, 'expenses': 0, 'balance': 0, 'savings_rate': 0,
                'daily_spend': 0, 'burn_rate_status': 'N/A'
            }
            
        # Basic totals
        income = period_txns[period_txns['transaction_type'] == 'income']['amount'].sum()
        expenses = period_txns[period_txns['transaction_type'] == 'expense']['amount'].sum()
        balance = income - expenses
        
        # Savings Rate
        savings_rate = ((income - expenses) / income * 100) if income > 0 else 0
        
        # Burn Rate (Daily Average)
        # Calculate days passed in this period (up to today if current month)
        today = datetime.now().date()
        effective_end_date = min(end_date, today)
        days_passed = (effective_end_date - start_date).days + 1
        days_passed = max(1, days_passed)
        
        daily_spend = expenses / days_passed
        
        return {
            'income': income,
            'expenses': expenses,
            'balance': balance,
            'savings_rate': savings_rate,
            'daily_spend': daily_spend
        }

    @staticmethod
    def get_spending_trend(transactions: pd.DataFrame, start_date, end_date, exclude_categories: list = None) -> pd.DataFrame:
        """Calculate cumulative spending trend for the period."""
        # Filter expenses
        mask = (transactions['date_obj'] >= start_date) & (transactions['date_obj'] <= end_date) & \
               (transactions['transaction_type'] == 'expense')
        
        if exclude_categories:
            mask = mask & (~transactions['category'].isin(exclude_categories))
            
        expenses = transactions.loc[mask].copy()
        
        if expenses.empty:
            return pd.DataFrame()
            
        # Group by date and sum
        daily = expenses.groupby('date_obj')['amount'].sum().reset_index()
        daily = daily.sort_values('date_obj')
        
        # Calculate cumulative sum
        daily['cumulative'] = daily['amount'].cumsum()
        
        return daily

    @staticmethod
    def get_fixed_expenses(transactions: pd.DataFrame, start_date, end_date, fixed_categories: list) -> pd.DataFrame:
        """Get fixed expenses grouped by category."""
        mask = (transactions['date_obj'] >= start_date) & (transactions['date_obj'] <= end_date) & \
               (transactions['transaction_type'] == 'expense') & \
               (transactions['category'].isin(fixed_categories))
        
        fixed = transactions.loc[mask].copy()
        if fixed.empty:
            return pd.DataFrame()
            
        return fixed.groupby('category')['amount'].sum().reset_index().sort_values('amount', ascending=False)


class DashboardCharts:
    """Create modern Plotly charts for the dashboard."""
    
    @staticmethod
    def create_gauge_chart(value: float, title: str, max_val: float = 100) -> go.Figure:
        """Create a minimalist gauge chart for savings rate."""
        color = "#2ecc71" if value >= 20 else "#f1c40f" if value >= 0 else "#e74c3c"
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title, 'font': {'size': 14, 'color': "gray"}},
            number = {'suffix': "%", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "lightgray"},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "white",
                'steps': [
                    {'range': [0, 20], 'color': '#f9f9f9'},
                    {'range': [20, max_val], 'color': '#f0fdf4'}
                ],
            }
        ))
        
        fig.update_layout(
            height=160, 
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': "Inter, sans-serif"}
        )
        return fig

    @staticmethod
    def create_trend_vs_budget(daily_trend: pd.DataFrame, budget_limit: float = None) -> go.Figure:
        """Create a cumulative spending trend chart."""
        if daily_trend.empty:
            return None
            
        fig = go.Figure()
        
        # Actual Spending Line
        fig.add_trace(go.Scatter(
            x=daily_trend['date_obj'],
            y=daily_trend['cumulative'],
            mode='lines',
            name='Variable Spending',
            line=dict(color='#3b82f6', width=3),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        
        # Budget Line (if provided)
        if budget_limit:
            fig.add_hline(
                y=budget_limit, 
                line_dash="dash", 
                line_color="gray", 
                annotation_text="Budget Limit",
                annotation_position="top right"
            )
            
        fig.update_layout(
            title="📉 Variable Spending Trajectory",
            template="plotly_white",
            hovermode="x unified",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, title=None),
            yaxis=dict(showgrid=True, gridcolor='lightgray', tickprefix="$"),
            showlegend=False
        )
        return fig

    @staticmethod
    def create_fixed_costs_chart(fixed_data: pd.DataFrame) -> go.Figure:
        """Create a bar chart for fixed costs."""
        if fixed_data.empty:
            return None
            
        fig = go.Figure(data=[go.Bar(
            x=fixed_data['category'],
            y=fixed_data['amount'],
            marker=dict(color='#9b59b6'),  # Purple for fixed costs
            text=[f"${x:,.0f}" for x in fixed_data['amount']],
            textposition='auto'
        )])
        
        fig.update_layout(
            title="🔒 Recurring & Fixed Costs",
            template="plotly_white",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, title=None),
            yaxis=dict(showgrid=True, gridcolor='lightgray', tickprefix="$"),
            showlegend=False
        )
        return fig

    @staticmethod
    def create_category_donut(transactions: pd.DataFrame) -> go.Figure:
        """Create a clean donut chart for top categories."""
        expenses = transactions[transactions['transaction_type'] == 'expense']
        if expenses.empty:
            return None
            
        # Top 5 categories + Other
        cat_totals = expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        if len(cat_totals) > 5:
            top_5 = cat_totals.head(5)
            other = pd.Series({'Other': cat_totals.iloc[5:].sum()})
            final_data = pd.concat([top_5, other])
        else:
            final_data = cat_totals
            
        fig = go.Figure(data=[go.Pie(
            labels=final_data.index,
            values=final_data.values,
            hole=0.6,
            textinfo='percent',
            textposition='outside',
            marker=dict(colors=px.colors.qualitative.Set2)
        )])
        
        fig.update_layout(
            title="Top Categories (All)",
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0),
            height=350,
            margin=dict(t=40, b=20, l=20, r=80)
        )
        return fig


def render_overview_tab(conn, all_transactions: pd.DataFrame):
    """
    Main entry point for the redesigned Overview Dashboard.
    """
    if all_transactions.empty:
        st.info("👋 No transactions yet. Import some data to see your dashboard!")
        return

    # --- Header & Controls ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 Financial Cockpit")
    
    with col2:
        # Date Filter
        presets = get_date_range_presets()
        preset_keys = list(presets.keys())
        default_index = preset_keys.index("Last Month") if "Last Month" in preset_keys else 0
        
        selected_preset = st.selectbox(
            "Period", 
            options=preset_keys, 
            index=default_index, 
            label_visibility="collapsed"
        )
        date_range = presets[selected_preset]
        start_date, end_date = date_range

    # Pre-process data
    all_transactions['date_obj'] = pd.to_datetime(all_transactions['date']).dt.date
    
    # Calculate Metrics
    metrics = DashboardMetrics.calculate_kpis(all_transactions, date_range)
    
    # --- ROW 1: The Vitals (KPI Cards) ---
    st.markdown("###") # Spacer
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric(
            "💰 Net Balance", 
            f"${metrics['balance']:,.2f}",
            delta=f"${metrics['income']:,.0f} in / ${metrics['expenses']:,.0f} out",
            delta_color="off"
        )
        
    with kpi_col2:
        # Savings Rate Gauge
        gauge = DashboardCharts.create_gauge_chart(metrics['savings_rate'], "Savings Rate")
        st.plotly_chart(gauge, use_container_width=True, config={'displayModeBar': False})
        
    with kpi_col3:
        st.metric(
            "🔥 Daily Burn", 
            f"${metrics['daily_spend']:,.0f} / day",
            help="Average daily spending in this period"
        )
        
    with kpi_col4:
        # Simple projection or insight
        if metrics['balance'] > 0:
            st.success(f"✅ You're saving\n**${metrics['balance']:,.0f}** this period")
        else:
            st.error(f"⚠️ Overspending by\n**${abs(metrics['balance']):,.0f}**")

    st.divider()

    # --- ROW 2: The Pulse (Main Charts) ---
    
    # Tabs for different views
    tab_dashboard, tab_cashflow = st.tabs(["📈 Trends & Categories", "🌊 Cash Flow"])
    
    with tab_dashboard:
        chart_col1, chart_col2 = st.columns([2, 1])
        
        # Define fixed categories
        from config import FIXED_EXPENSE_CATEGORIES
        
        with chart_col1:
            # Variable Spending Trend Chart (Excluding Fixed)
            daily_trend = DashboardMetrics.get_spending_trend(
                all_transactions, 
                start_date, 
                end_date, 
                exclude_categories=FIXED_EXPENSE_CATEGORIES
            )
            
            if not daily_trend.empty:
                fig_trend = DashboardCharts.create_trend_vs_budget(daily_trend)
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No variable spending data for this period")
                
        with chart_col2:
            # Fixed Costs Bar Chart
            fixed_data = DashboardMetrics.get_fixed_expenses(
                all_transactions, 
                start_date, 
                end_date, 
                fixed_categories=FIXED_EXPENSE_CATEGORIES
            )
            
            if not fixed_data.empty:
                fig_fixed = DashboardCharts.create_fixed_costs_chart(fixed_data)
                st.plotly_chart(fig_fixed, use_container_width=True, config={'displayModeBar': False})
            else:
                # If no fixed costs, show the general donut
                st.info("No fixed costs found (Rent, Utilities, etc.)")
                
                # Fallback to general donut if no fixed costs
                period_txns = all_transactions[
                    (all_transactions['date_obj'] >= start_date) & 
                    (all_transactions['date_obj'] <= end_date)
                ]
                fig_donut = DashboardCharts.create_category_donut(period_txns)
                if fig_donut:
                    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

    with tab_cashflow:
        # Simple Waterfall or Bar chart for Income vs Expense
        st.caption("Cash flow visualization coming soon...")
        
    st.divider()

    # --- ROW 3: The Action (Recent Transactions) ---
    st.subheader("🕒 Recent Activity")
    
    # Filter for recent transactions (global, not just selected period)
    recent_txns = all_transactions.sort_values('date', ascending=False).head(10)
    
    # Prepare for AG Grid
    display_df = recent_txns.copy()
    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
    display_df['Amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
    
    display_df = display_df.rename(columns={
        'id': 'ID', 'date': 'Date', 'description': 'Description',
        'transaction_type': 'Type', 'category': 'Category', 'card': 'Card'
    })
    
    grid_data = display_df[['ID', 'Date', 'Description', 'Amount', 'Type', 'Category', 'Card']]
    render_aggrid_table(grid_data, key="dashboard_recent_grid")
