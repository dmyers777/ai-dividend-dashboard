
import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.express as px
from google import genai
from dotenv import load_dotenv

# 1. SETUP & KEYS
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)
CURRENT_MODEL = "gemini-3-flash-preview"
SAVE_FILE = "my_portfolio.csv"

# 2. PAGE SETTINGS
st.set_page_config(page_title="Dividend Income Tracker", layout="wide")

# --- PROFESSIONAL DISCLOSURE ---
st.caption("⚠️ **IMPORTANT DISCLOSURE:** This platform is an AI-driven educational tool. It does not provide financial advice. All calculations are estimates. Use of this tool constitutes acceptance that the creator is not liable for investment losses.")

st.title("💰 Dividend Income Tracker and AI Insights")
st.markdown("---")

# 3. SIDEBAR: CUSTOM BILL GOALS & SAVE/LOAD
with st.sidebar:
    st.header("⚙️ Your Monthly Bill Goals")
    u_cost = st.number_input("Level 1: Utilities", value=150)
    g_cost = st.number_input("Level 2: Groceries", value=600)
    v_cost = st.number_input("Level 3: Vehicle", value=1200)
    h_cost = st.number_input("Level 4: Housing", value=3500)
    f_cost = st.number_input("Level 5: Financial Freedom", value=6000)

    USER_MILESTONES = {
        "Utilities": u_cost,
        "Groceries": g_cost,
        "Vehicle": v_cost,
        "Housing": h_cost,
        "Financial Freedom": f_cost
    }

    st.markdown("---")
    st.header("💾 Portfolio Storage")
    
    col_s1, col_s2 = st.columns(2)
    
    # Save Button
    if col_s1.button("💾 Save"):
        if 'portfolio_df' in st.session_state:
            st.session_state.portfolio_df.to_csv(SAVE_FILE, index=False)
            st.success("Saved!")

    # Load Button
    if col_s2.button("📂 Load"):
        if os.path.exists(SAVE_FILE):
            st.session_state.portfolio_df = pd.read_csv(SAVE_FILE)
            st.rerun()
        else:
            st.error("No file found.")

# 4. MAIN PORTFOLIO INPUT
st.header("📋 Your Portfolio Holdings")
st.write("Add your tickers and share counts. Click the '+' below the table to add rows.")

# Initialize the table in session state if it doesn't exist
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = pd.DataFrame([{"Ticker": "", "Shares": 0.0}])

# The data editor updates the session state directly
edited_df = st.data_editor(st.session_state.portfolio_df, num_rows="dynamic", use_container_width=True, key="portfolio_editor")

# Update the stored dataframe whenever the editor changes
st.session_state.portfolio_df = edited_df

analyze_btn = st.button("🚀 Analyze Entire Portfolio", type="primary")

# 5. CORE LOGIC
if analyze_btn:
    portfolio_results = []
    total_monthly_income = 0
    sector_data = {} 
    
    try:
        with st.spinner("Fetching data and calculating portfolio totals..."):
            for index, row in edited_df.iterrows():
                ticker_sym = str(row["Ticker"]).strip().upper()
                num_shares = row["Shares"]
                
                if ticker_sym and ticker_sym != "" and num_shares > 0:
                    stock = yf.Ticker(ticker_sym)
                    info = stock.info
                    
                    price = info.get('currentPrice', info.get('previousClose', 1))
                    sector = info.get('sector', 'Other/ETF')
                    
                    # --- REINFORCED MATH PATCH ---
                    raw_yield = info.get('dividendYield', 0)
                    if raw_yield is None: raw_yield = 0
                    
                    if raw_yield > 0.2: 
                        refined_yield = raw_yield / 100
                    else:
                        refined_yield = raw_yield
                    
                    annual_div_total = refined_yield * price * num_shares
                    monthly_div = annual_div_total / 12
                    
                    portfolio_results.append({
                        "Ticker": ticker_sym,
                        "Sector": sector,
                        "Price": f"${price:.2f}",
                        "Yield": f"{refined_yield * 100:.2f}%",
                        "Monthly Income": monthly_div
                    })
                    
                    total_monthly_income += monthly_div
                    sector_data[sector] = sector_data.get(sector, 0) + monthly_div

        if not portfolio_results:
            st.warning("Please enter at least one valid ticker and share amount.")
        else:
            # C. DISPLAY TOTALS
            st.markdown("---")
            st.metric("Total Combined Monthly Income", f"${total_monthly_income:.2f}")

            # D. DISPLAY PORTFOLIO SUMMARY & CHART
            sum_col1, sum_col2 = st.columns([1.5, 1.2]) 
            
            with sum_col1:
                st.subheader("📊 Portfolio Table")
                display_df = pd.DataFrame(portfolio_results)
                display_df["Monthly Income"] = display_df["Monthly Income"].map("${:,.2f}".format)
                st.dataframe(display_df, use_container_width=True, hide_index=True)

            with sum_col2:
                if sector_data:
                    fig = px.pie(
                        values=list(sector_data.values()), 
                        names=list(sector_data.keys()), 
                        title="Income Contribution by Sector",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig.update_traces(textposition='outside', textinfo='percent+label')
                    fig.update_layout(
                        showlegend=False, 
                        margin=dict(t=50, b=50, l=10, r=10),
                        height=450 
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # E. MILESTONE PROGRESS
            st.markdown("---")
            st.subheader("🏁 Financial Milestone Progress")
            cols = st.columns(len(USER_MILESTONES))
            
            for i, (level, cost) in enumerate(USER_MILESTONES.items()):
                progress = min(total_monthly_income / cost, 1.0) if cost > 0 else 1.0
                with cols[i]:
                    st.write(f"**{level}**")
                    st.write(f"${cost}/mo")
                    st.progress(progress)
                    if progress >= 1.0:
                        st.success("PAID OFF")
                    else:
                        st.write(f"{progress*100:.1f}% Covered")

            # F. AI INSIGHTS
            st.markdown("---")
            st.subheader("🤖 AI Portfolio Insights")
            
            next_goal = "Financial Freedom"
            next_val = f_cost
            for level, cost in USER_MILESTONES.items():
                if total_monthly_income < cost:
                    next_goal = level
                    next_val = cost
                    break

            tickers_str = ", ".join([r['Ticker'] for r in portfolio_results])
            prompt = f"""
            You are a Dividend Portfolio Strategist.
            Portfolio: {tickers_str}
            Total Monthly Income: ${total_monthly_income:.2f}
            Sector Mix: {list(sector_data.keys())}
            Next Milestone: {next_goal} (${next_val}/mo)

            TASK:
            1. Summarize the overall health of this portfolio.
            2. Based on the Sector Mix, which area is the portfolio most reliant on?
            3. Suggest a path to reach the '${next_val}' milestone faster.
            
            End with: 'This analysis is for educational purposes only.'
            """

            try:
                ai_response = client.models.generate_content(model=CURRENT_MODEL, contents=prompt)
                st.info(ai_response.text)
            except Exception as ai_err:
                st.error(f"AI Error: {ai_err}")

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("👈 Enter your holdings or click 'Load' in the sidebar to begin.")
    
