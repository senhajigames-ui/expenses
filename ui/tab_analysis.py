"""
Analysis Tab - Advanced analytics and budget management.

Features:
- Spending patterns and trends
- Category analysis over time
- Budget creation and management
- Merchant rules management
- Comparative analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
from database.budget_operations import get_budgets, save_budget, load_merchant_rules, save_merchant_rule, delete_budget, delete_merchant_rule
from config import EXPENSE_CATEGORIES, CURRENCY_SYMBOL


class SpendingPatterns:
    """Analyze spending patterns and trends."""
    
    @staticmethod
    def analyze_by_day_of_week(transactions: pd.DataFrame) -> go.Figure:
        """Analyze spending by day of week."""
        if transactions.empty:
            return None
        
        # Add day of week
        transactions['date_parsed'] = pd.to_datetime(transactions['date'])
        transactions['day_of_week'] = transactions['date_parsed'].dt.day_name()
        
        # Filter expenses only
        expenses = transactions[transactions['transaction_type'] == 'expense']
        
        # Group by day
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_spending = expenses.groupby('day_of_week')['amount'].sum().reindex(day_order)
        
        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=daily_spending.index,
            y=daily_spending.values,
            marker=dict(color=daily_spending.values, colorscale='Burg'),
            text=[f"${val:,.0f}" for val in daily_spending.values],
            textposition='auto',
            hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>"
        )])
        
        fig.update_layout(
            template="plotly_white",
            title="Spending by Day of Week",
            xaxis_title=None,
            yaxis_title=None,
            height=400,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    
    @staticmethod
    def analyze_category_trends(transactions: pd.DataFrame, top_n: int = 5) -> go.Figure:
        """Show category spending trends over time."""
        if transactions.empty:
            return None
        
        # Filter expenses
        expenses = transactions[transactions['transaction_type'] == 'expense'].copy()
        
        if expenses.empty:
            return None
        
        # Get top categories
        top_categories = expenses.groupby('category')['amount'].sum().nlargest(top_n).index
        
        # Filter to top categories
        filtered = expenses[expenses['category'].isin(top_categories)]
        
        # Group by month and category
        monthly_category = filtered.groupby(['month', 'category'])['amount'].sum().reset_index()
        
        # Create area chart
        fig = px.area(
            monthly_category,
            x='month',
            y='amount',
            color='category',
            title=f"Top {top_n} Categories Over Time",
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        
        fig.update_layout(
            template="plotly_white",
            xaxis_title=None,
            yaxis_title="Amount ($)",
            height=450,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig


class ComparativeAnalysis:
    """Compare spending across time periods."""
    
    @staticmethod
    def month_over_month(transactions: pd.DataFrame) -> pd.DataFrame:
        """Calculate month-over-month changes."""
        if transactions.empty:
            return pd.DataFrame()
        
        # Group by month and type
        monthly = transactions.groupby(['month', 'transaction_type'])['amount'].sum().reset_index()
        
        # Pivot
        monthly_pivot = monthly.pivot(
            index='month',
            columns='transaction_type',
            values='amount'
        ).fillna(0)
        
        # Calculate changes
        for col in monthly_pivot.columns:
            monthly_pivot[f'{col}_change'] = monthly_pivot[col].pct_change() * 100
        
        return monthly_pivot
    
    
    @staticmethod
    def render_comparison(current_month: pd.Series, previous_month: pd.Series):
        """Render month comparison cards."""
        st.subheader("📊 Month-over-Month Comparison")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_expense = current_month.get('expense', 0)
            prev_expense = previous_month.get('expense', 0)
            change = ((current_expense - prev_expense) / prev_expense * 100) if prev_expense > 0 else 0
            
            st.metric(
                "Expenses",
                f"${current_expense:,.2f}",
                delta=f"{change:+.1f}%",
                delta_color="inverse"
            )
        
        with col2:
            current_income = current_month.get('income', 0)
            prev_income = previous_month.get('income', 0)
            change = ((current_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
            
            st.metric(
                "Income",
                f"${current_income:,.2f}",
                delta=f"{change:+.1f}%"
            )
        
        with col3:
            current_net = current_month.get('income', 0) - current_month.get('expense', 0)
            prev_net = previous_month.get('income', 0) - previous_month.get('expense', 0)
            change = ((current_net - prev_net) / abs(prev_net) * 100) if prev_net != 0 else 0
            
            st.metric(
                "Net Balance",
                f"${current_net:,.2f}",
                delta=f"{change:+.1f}%"
            )


class BudgetManager:
    """Budget creation and management."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def render(self):
        """Render budget management UI."""
        st.subheader("💰 Budget Management")
        
        # Show existing budgets
        budgets = get_budgets(self.conn)
        
        if budgets:
            self._render_budget_list(budgets)
        else:
            st.info("No budgets set yet. Create your first budget below!")
        
        st.divider()
        
        # Add new budget
        self._render_budget_form()
    
    def _render_budget_list(self, budgets: List):
        """Display existing budgets."""
        st.markdown("### Current Budgets")
        
        for budget in budgets:
            budget_id, category, amount = budget
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{category}**")
            
            with col2:
                st.text(f"${amount:,.2f}/month")
            
            with col3:
                if st.button("🗑️", key=f"delete_budget_{budget_id}"):
                    self._delete_budget(budget_id)
                    st.rerun()
    
    def _render_budget_form(self):
        """Render form to add new budget."""
        st.markdown("### Add New Budget")
        
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Category",
                options=EXPENSE_CATEGORIES,
                key='new_budget_category'
            )
        
        with col2:
            amount = st.number_input(
                "Monthly Budget ($)",
                min_value=0.0,
                step=50.0,
                key='new_budget_amount'
            )
        
        if st.button("➕ Add Budget", type="primary", width="stretch"):
            if amount > 0:
                if save_budget(self.conn, category, amount):
                    st.success(f"✅ Budget created: {category} - ${amount:,.2f}/month")
                    st.rerun()
                else:
                    st.error("Failed to save budget")
            else:
                st.warning("Budget amount must be greater than 0")
    
    def _delete_budget(self, budget_id: int):
        """Delete a budget using Supabase."""
        if delete_budget(None, budget_id):
            st.success("✅ Budget deleted")
        else:
            st.error("Failed to delete budget")


class MerchantRulesManager:
    """Manage merchant categorization rules."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def render(self):
        """Render merchant rules management UI."""
        st.subheader("🏪 Merchant Rules")
        
        # Load rules
        rules = load_merchant_rules(self.conn)
        
        if rules:
            self._render_rules_table(rules)
        else:
            st.info("No custom rules yet. Rules are auto-created when you edit transactions!")
        
        st.divider()
        
        # Add manual rule
        self._render_add_rule_form()
    
    def _render_rules_table(self, rules: Dict[str, str]):
        """Display rules in a table."""
        st.markdown(f"### Active Rules ({len(rules)})")
        
        # Convert to DataFrame for display
        rules_df = pd.DataFrame([
            {'Merchant': merchant, 'Category': category}
            for merchant, category in rules.items()
        ])
        
        # Search filter
        search = st.text_input("🔍 Search rules", key='search_rules')
        
        if search:
            rules_df = rules_df[
                rules_df['Merchant'].str.contains(search, case=False) |
                rules_df['Category'].str.contains(search, case=False)
            ]
        
        # Display
        for idx, row in rules_df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.text(row['Merchant'])
            
            with col2:
                st.text(f"→ {row['Category']}")
            
            with col3:
                if st.button("🗑️", key=f"delete_rule_{idx}"):
                    self._delete_rule(row['Merchant'])
                    st.rerun()
    
    def _render_add_rule_form(self):
        """Form to manually add a rule."""
        st.markdown("### Add Manual Rule")
        
        col1, col2 = st.columns(2)
        
        with col1:
            merchant = st.text_input("Merchant Name", key='new_rule_merchant')
        
        with col2:
            category = st.selectbox(
                "Category",
                options=EXPENSE_CATEGORIES,
                key='new_rule_category'
            )
        
        if st.button("➕ Add Rule", type="primary", width="stretch"):
            if merchant:
                if save_merchant_rule(self.conn, merchant, category):
                    st.success(f"✅ Rule created: {merchant} → {category}")
                    st.rerun()
                else:
                    st.error("Failed to save rule")
            else:
                st.warning("Merchant name is required")
    
    def _delete_rule(self, merchant: str):
        """Delete a merchant rule using Supabase."""
        if delete_merchant_rule(None, merchant):
            st.success("✅ Rule deleted")
        else:
            st.error("Failed to delete rule")


class TopSpenders:
    """Identify top spending merchants and categories."""
    
    @staticmethod
    def render(transactions: pd.DataFrame):
        """Render top spenders analysis."""
        if transactions.empty:
            return
        
        st.subheader("🔝 Top Spenders")
        
        # Filter expenses
        expenses = transactions[transactions['transaction_type'] == 'expense']
        
        if expenses.empty:
            st.info("No expense data available")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top Merchants")
            # Group by description (merchant)
            top_merchants = expenses.groupby('description')['amount'].sum().nlargest(10).reset_index()
            top_merchants = top_merchants.sort_values('amount', ascending=True)  # Sort for bar chart
            
            # Create horizontal bar chart
            fig_merch = go.Figure(data=[go.Bar(
                x=top_merchants['amount'],
                y=top_merchants['description'].str.slice(0, 30),  # Truncate long names
                orientation='h',
                marker=dict(color='#3498db'),
                text=[f"${x:,.0f}" for x in top_merchants['amount']],
                textposition='auto'
            )])
            
            fig_merch.update_layout(
                template="plotly_white",
                height=400,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor='lightgray'),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_merch, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            st.markdown("#### Top Categories")
            top_categories = expenses.groupby('category')['amount'].sum().nlargest(10).reset_index()
            top_categories = top_categories.sort_values('amount', ascending=True)
            
            # Create horizontal bar chart
            fig_cat = go.Figure(data=[go.Bar(
                x=top_categories['amount'],
                y=top_categories['category'],
                orientation='h',
                marker=dict(color='#e74c3c'),
                text=[f"${x:,.0f}" for x in top_categories['amount']],
                textposition='auto'
            )])
            
            fig_cat.update_layout(
                template="plotly_white",
                height=400,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor='lightgray'),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_cat, use_container_width=True, config={'displayModeBar': False})


def render_analysis_tab(conn, all_transactions: pd.DataFrame):
    """
    Main entry point for Analysis tab.
    
    Args:
        conn: Database connection
        all_transactions: All transactions DataFrame
    """
    st.subheader("📈 Financial Analysis")
    
    if all_transactions.empty:
        st.info("👋 No data to analyze. Import transactions first!")
        return
    
    # Simplified layout - no sub-tabs, just sections
    
    # Section 1: Key Insights
    st.markdown("### 💡 Key Insights")
    monthly_data = ComparativeAnalysis.month_over_month(all_transactions)
    if not monthly_data.empty and len(monthly_data) >= 2:
        current_month = monthly_data.iloc[-1]
        previous_month = monthly_data.iloc[-2]
        ComparativeAnalysis.render_comparison(current_month, previous_month)
    
    st.divider()
    
    # Section 2: Spending Patterns
    st.markdown("### 📊 Spending Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Day of week analysis
        dow_chart = SpendingPatterns.analyze_by_day_of_week(all_transactions)
        if dow_chart:
            st.plotly_chart(dow_chart, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # Top spenders
        TopSpenders.render(all_transactions)
    
    st.divider()
    
    # Section 3: Category Trends
    st.markdown("### 📈 Category Trends Over Time")
    trend_chart = SpendingPatterns.analyze_category_trends(all_transactions)
    if trend_chart:
        st.plotly_chart(trend_chart, use_container_width=True, config={'displayModeBar': False})
    
    st.divider()
    
    # Section 4: Management Tools (Collapsible)
    with st.expander("💰 Budget Management", expanded=False):
        budget_manager = BudgetManager(conn)
        budget_manager.render()
    
    with st.expander("🏪 Merchant Rules", expanded=False):
        rules_manager = MerchantRulesManager(conn)
        rules_manager.render()
