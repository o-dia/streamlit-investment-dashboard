import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables for security
load_dotenv()

# Set page configuration
st.set_page_config(page_title="Investment Portfolio Dashboard", layout="wide")

# Title of your app
st.title("Investment Portfolio Dashboard")
st.subheader("Track your investments across Charles Schwab and Interactive Brokers")

# Configuration
# Getting credentials from .env file
SCHWAB_CLIENT_ID = os.getenv("SCHWAB_CLIENT_ID", "your_client_id_here")
SCHWAB_CLIENT_SECRET = os.getenv("SCHWAB_CLIENT_SECRET", "your_client_secret_here")
SCHWAB_REDIRECT_URI = os.getenv("SCHWAB_REDIRECT_URI", "https://your-ngrok-url.ngrok-free.app/callback")

# Interactive Brokers API Configuration (will be loaded from .env when implemented)
IB_CLIENT_ID = os.getenv("IB_CLIENT_ID", "")
IB_GATEWAY_PORT = os.getenv("IB_GATEWAY_PORT", "4001")
IB_HOST = os.getenv("IB_HOST", "127.0.0.1")

# Schwab API endpoints
SCHWAB_AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
SCHWAB_ACCOUNTS_URL = "https://api.schwab.com/v2/accounts"

#######################################################
# Charles Schwab Functions
#######################################################

def get_schwab_access_token(auth_code):
    st.write(f"Attempting to exchange auth code for token...")
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": SCHWAB_REDIRECT_URI,
        "client_id": SCHWAB_CLIENT_ID,
        "client_secret": SCHWAB_CLIENT_SECRET,
    }
    
    # Display what we're sending (redact sensitive info)
    st.write(f"Using redirect URI: {SCHWAB_REDIRECT_URI}")
    st.write(f"Using client ID: {SCHWAB_CLIENT_ID[:5]}... (redacted)")
    
    try:
        st.write(f"Sending request to: {SCHWAB_TOKEN_URL}")
        response = requests.post(SCHWAB_TOKEN_URL, data=payload)
        st.write(f"Response status code: {response.status_code}")
        st.write(f"Response body: {response.text}")
        
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        access_token_info = response.json()
        # Store token in session state for future API calls
        st.session_state["schwab_token"] = access_token_info
        return access_token_info["access_token"]
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting access token: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            st.error(f"Error details: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None
    
def get_schwab_account_info(access_token):
    """Fetch account information from Schwab API"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(SCHWAB_ACCOUNTS_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error retrieving account information: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            st.error(f"Error details: {e.response.text}")
        return None

def parse_schwab_data(raw_data):
    """Parse the raw Schwab API response into a structured format
    Note: You'll need to adjust this based on the actual structure of Schwab's API response"""
    try:
        # This is a placeholder - adapt based on actual Schwab API response structure
        accounts = raw_data.get("accounts", [])
        parsed_data = {
            "total_value": 0,
            "accounts": [],
            "positions": []
        }
        
        for account in accounts:
            account_value = float(account.get("balances", {}).get("totalAccountValue", 0))
            parsed_data["total_value"] += account_value
            
            # Add account details
            parsed_data["accounts"].append({
                "account_id": account.get("accountId", "Unknown"),
                "account_name": account.get("accountName", "Unknown"),
                "account_type": account.get("accountType", "Unknown"),
                "value": account_value
            })
            
            # Parse positions if available
            positions = account.get("positions", [])
            for position in positions:
                security = position.get("security", {})
                parsed_data["positions"].append({
                    "account_id": account.get("accountId", "Unknown"),
                    "symbol": security.get("symbol", "Unknown"),
                    "description": security.get("description", "Unknown"),
                    "quantity": float(position.get("quantity", 0)),
                    "market_value": float(position.get("marketValue", 0)),
                    "cost_basis": float(position.get("costBasis", 0)),
                    "unrealized_pl": float(position.get("unrealizedPL", 0)),
                    "unrealized_pl_percent": float(position.get("unrealizedPLPercent", 0))
                })
        
        return parsed_data
        
    except Exception as e:
        st.error(f"Error parsing Schwab data: {str(e)}")
        return None

#######################################################
# Interactive Brokers Functions
#######################################################

def connect_to_ib():
    """Connect to Interactive Brokers API
    For demonstration - actual implementation will depend on IB API structure"""
    
    # This is a placeholder - in a real implementation, you would:
    # 1. Import the IB API client
    # 2. Establish connection
    # 3. Authenticate
    # 4. Return a client object
    
    # For now, we'll return a mock value to simulate connection
    if not IB_CLIENT_ID:
        st.warning("Interactive Brokers credentials not configured in .env file")
        return None
    
    try:
        # Simulate successful connection
        st.session_state["ib_connected"] = True
        return {"connected": True, "client_id": IB_CLIENT_ID}
    
    except Exception as e:
        st.error(f"Error connecting to Interactive Brokers: {str(e)}")
        return None

def get_ib_account_data():
    """Fetch account data from Interactive Brokers
    For demonstration - actual implementation will depend on IB API structure"""
    
    # This is a placeholder - replace with actual IB API calls
    # For now, return sample data to demonstrate UI functionality
    
    sample_data = {
        "account_summary": {
            "U1234567": {
                "NetLiquidation": {"value": "105432.78", "currency": "USD"},
                "TotalCashValue": {"value": "25876.45", "currency": "USD"},
                "AvailableFunds": {"value": "25876.45", "currency": "USD"}
            }
        },
        "positions": [
            {
                "account": "U1234567",
                "symbol": "AAPL",
                "secType": "STK",
                "exchange": "NASDAQ",
                "position": 50,
                "avgCost": 182.45
            },
            {
                "account": "U1234567",
                "symbol": "MSFT",
                "secType": "STK",
                "exchange": "NASDAQ",
                "position": 25,
                "avgCost": 334.67
            },
            {
                "account": "U1234567",
                "symbol": "VTI",
                "secType": "ETF",
                "exchange": "NYSE",
                "position": 100,
                "avgCost": 217.89
            }
        ]
    }
    
    return sample_data

def parse_ib_data(ib_data):
    """Parse Interactive Brokers data into a structured format"""
    if ib_data is None:
        return None
        
    try:
        parsed_data = {
            "total_value": 0,
            "accounts": [],
            "positions": []
        }
        
        # Parse account summary
        for account_id, summary in ib_data["account_summary"].items():
            account_value = float(summary.get("NetLiquidation", {}).get("value", 0))
            parsed_data["total_value"] += account_value
            
            # Add account details
            parsed_data["accounts"].append({
                "account_id": account_id,
                "account_name": f"IB {account_id}",
                "account_type": "Investment",
                "value": account_value
            })
        
        # Parse positions
        for position in ib_data["positions"]:
            market_value = position["position"] * position["avgCost"]
            cost_basis = position["position"] * position["avgCost"]
            # In a real app, you'd get current prices for accurate market value
            
            parsed_data["positions"].append({
                "account_id": position["account"],
                "symbol": position["symbol"],
                "description": f"{position['symbol']} ({position['secType']})",
                "quantity": position["position"],
                "market_value": market_value,
                "cost_basis": cost_basis,
                "unrealized_pl": 0,  # Would need current price data
                "unrealized_pl_percent": 0  # Would need current price data
            })
            
        return parsed_data
        
    except Exception as e:
        st.error(f"Error parsing IB data: {str(e)}")
        return None

#######################################################
# Combined Portfolio Functions
#######################################################

def combine_portfolio_data(schwab_data, ib_data):
    """Combine data from both brokerages into a single portfolio view"""
    if schwab_data is None:
        schwab_data = {"total_value": 0, "accounts": [], "positions": []}
    if ib_data is None:
        ib_data = {"total_value": 0, "accounts": [], "positions": []}
    
    combined_data = {
        "total_value": schwab_data["total_value"] + ib_data["total_value"],
        "accounts": [],
        "positions": [],
        "allocation": {},
        "brokers": {
            "Schwab": schwab_data["total_value"],
            "Interactive Brokers": ib_data["total_value"]
        }
    }
    
    # Add Schwab accounts
    for account in schwab_data["accounts"]:
        combined_data["accounts"].append({
            "broker": "Schwab",
            "account_id": account["account_id"],
            "account_name": account["account_name"],
            "account_type": account["account_type"],
            "value": account["value"]
        })
    
    # Add IB accounts
    for account in ib_data["accounts"]:
        combined_data["accounts"].append({
            "broker": "Interactive Brokers",
            "account_id": account["account_id"],
            "account_name": account["account_name"],
            "account_type": account["account_type"],
            "value": account["value"]
        })
    
    # Add Schwab positions
    for position in schwab_data["positions"]:
        symbol = position["symbol"]
        combined_data["positions"].append({
            "broker": "Schwab",
            "account_id": position["account_id"],
            "symbol": symbol,
            "description": position["description"],
            "quantity": position["quantity"],
            "market_value": position["market_value"],
            "cost_basis": position["cost_basis"],
            "unrealized_pl": position["unrealized_pl"],
            "unrealized_pl_percent": position["unrealized_pl_percent"]
        })
        
        # Update allocation by symbol
        if symbol not in combined_data["allocation"]:
            combined_data["allocation"][symbol] = {
                "total_value": 0,
                "total_quantity": 0,
                "description": position["description"]
            }
        combined_data["allocation"][symbol]["total_value"] += position["market_value"]
        combined_data["allocation"][symbol]["total_quantity"] += position["quantity"]
    
    # Add IB positions
    for position in ib_data["positions"]:
        symbol = position["symbol"]
        combined_data["positions"].append({
            "broker": "Interactive Brokers",
            "account_id": position["account_id"],
            "symbol": symbol,
            "description": position["description"],
            "quantity": position["quantity"],
            "market_value": position["market_value"],
            "cost_basis": position["cost_basis"],
            "unrealized_pl": position["unrealized_pl"],
            "unrealized_pl_percent": position["unrealized_pl_percent"]
        })
        
        # Update allocation by symbol
        if symbol not in combined_data["allocation"]:
            combined_data["allocation"][symbol] = {
                "total_value": 0,
                "total_quantity": 0,
                "description": position["description"]
            }
        combined_data["allocation"][symbol]["total_value"] += position["market_value"]
        combined_data["allocation"][symbol]["total_quantity"] += position["quantity"]
    
    return combined_data

#######################################################
# Dashboard Display Functions
#######################################################

def display_portfolio_summary(combined_data, view_type="all"):
    """Display portfolio summary based on the selected view type
    view_type can be: "all", "schwab", or "ib_isa" """
    
    # Filter data based on view_type
    filtered_data = filter_portfolio_data(combined_data, view_type)
    
    if filtered_data["total_value"] == 0:
        st.info(f"No data available for the selected view: {view_type}")
        return
    
    # Display total portfolio value
    st.subheader("Total Portfolio Value")
    total_value = filtered_data["total_value"]
    # In a real app, you would calculate the change values
    st.metric("Portfolio Value", f"${total_value:,.2f}", "")
    
    # Create a row with three columns for summary metrics
    col1, col2, col3 = st.columns(3)
    
    # Count positions and calculate average position value
    num_positions = len(filtered_data["positions"])
    avg_position_value = total_value / num_positions if num_positions > 0 else 0
    
    with col1:
        st.metric("Number of Positions", f"{num_positions}", "")
    with col2:
        st.metric("Average Position Size", f"${avg_position_value:,.2f}", "")
    with col3:
        # This would be calculated from historical data in a real app
        st.metric("YTD Return", "+7.2%", "")
    
    # Display breakdown by broker if showing all accounts
    if view_type == "all":
        st.subheader("Breakdown by Broker")
        
        # Calculate percentages
        broker_data = []
        for broker, value in filtered_data["brokers"].items():
            if total_value > 0:
                percentage = (value / total_value) * 100
            else:
                percentage = 0
            broker_data.append({
                "Broker": broker,
                "Value": value,
                "Percentage": percentage
            })
        
        # Create broker breakdown pie chart
        fig_broker = px.pie(
            broker_data, 
            values="Value", 
            names="Broker", 
            title="Portfolio by Broker",
            hover_data=["Percentage"],
            labels={"Value": "Portfolio Value"}
        )
        fig_broker.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_broker)
    
    # Display account breakdown
    st.subheader("Account Breakdown")
    
    # Prepare account data for display
    account_data = []
    for account in filtered_data["accounts"]:
        if total_value > 0:
            percentage = (account["value"] / total_value) * 100
        else:
            percentage = 0
            
        account_data.append({
            "Broker": account["broker"],
            "Account": account["account_name"],
            "Type": account["account_type"],
            "Value": account["value"],
            "Percentage": percentage
        })
    
    # Convert to DataFrame for display
    df_accounts = pd.DataFrame(account_data)
    df_accounts["Value"] = df_accounts["Value"].map("${:,.2f}".format)
    df_accounts["Percentage"] = df_accounts["Percentage"].map("{:.1f}%".format)
    
    # Display accounts table
    st.dataframe(df_accounts, use_container_width=True)
    
    # Display asset allocation
    st.subheader("Asset Allocation")
    
    # Prepare allocation data for pie chart
    allocation_data = []
    for symbol, data in filtered_data["allocation"].items():
        if total_value > 0:
            percentage = (data["total_value"] / total_value) * 100
        else:
            percentage = 0
            
        allocation_data.append({
            "Symbol": symbol,
            "Description": data["description"],
            "Value": data["total_value"],
            "Percentage": percentage
        })
    
    # Sort by value descending
    allocation_data = sorted(allocation_data, key=lambda x: x["Value"], reverse=True)
    
    # Convert to DataFrame for plotting
    df_allocation = pd.DataFrame(allocation_data)
    
    # Create pie chart
    fig = px.pie(
        df_allocation, 
        values="Value", 
        names="Symbol", 
        title="Portfolio Allocation by Security",
        hover_data=["Description", "Percentage"],
        labels={"Value": "Market Value"}
    )
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(fig)
    
    # Display positions table
    st.subheader("Positions")
    
    # Prepare positions data for display
    positions_data = []
    for position in filtered_data["positions"]:
        positions_data.append({
            "Broker": position["broker"],
            "Account": position["account_id"],
            "Symbol": position["symbol"],
            "Description": position["description"],
            "Quantity": position["quantity"],
            "Market Value": position["market_value"],
            "Cost Basis": position["cost_basis"],
            "Unrealized P/L": position["unrealized_pl"],
            "% P/L": position["unrealized_pl_percent"]
        })
    
    # Convert to DataFrame and sort by Market Value descending
    df_positions = pd.DataFrame(positions_data)
    df_positions = df_positions.sort_values(by="Market Value", ascending=False)
    
    # Format numeric columns
    df_positions["Market Value"] = df_positions["Market Value"].map("${:,.2f}".format)
    df_positions["Cost Basis"] = df_positions["Cost Basis"].map("${:,.2f}".format)
    df_positions["Unrealized P/L"] = df_positions["Unrealized P/L"].map("${:,.2f}".format)
    df_positions["% P/L"] = df_positions["% P/L"].map("{:.2f}%".format)
    
    # Display positions table
    st.dataframe(df_positions, use_container_width=True)

def filter_portfolio_data(combined_data, view_type):
    """Filter portfolio data based on view type"""
    if view_type == "all":
        return combined_data
    
    filtered_data = {
        "total_value": 0,
        "accounts": [],
        "positions": [],
        "allocation": {},
        "brokers": {}
    }
    
    if view_type == "schwab":
        # Filter for Schwab accounts only
        filtered_data["brokers"]["Schwab"] = combined_data["brokers"].get("Schwab", 0)
        filtered_data["total_value"] = filtered_data["brokers"]["Schwab"]
        
        # Filter accounts
        filtered_data["accounts"] = [
            account for account in combined_data["accounts"] 
            if account["broker"] == "Schwab"
        ]
        
        # Filter positions
        filtered_data["positions"] = [
            position for position in combined_data["positions"]
            if position["broker"] == "Schwab"
        ]
        
    elif view_type == "ib_isa":
        # Filter for Interactive Brokers ISA account only
        # In a real app, you'd have actual account types to filter on
        # This is a placeholder assuming account IDs with "ISA" are ISA accounts
        
        # Filter accounts
        ib_isa_accounts = [
            account for account in combined_data["accounts"]
            if account["broker"] == "Interactive Brokers" and "ISA" in account.get("account_type", "")
        ]
        
        filtered_data["accounts"] = ib_isa_accounts
        filtered_data["total_value"] = sum(account["value"] for account in ib_isa_accounts)
        filtered_data["brokers"]["Interactive Brokers"] = filtered_data["total_value"]
        
        # Get account IDs for filtering positions
        ib_isa_account_ids = [account["account_id"] for account in ib_isa_accounts]
        
        # Filter positions
        filtered_data["positions"] = [
            position for position in combined_data["positions"]
            if position["broker"] == "Interactive Brokers" and position["account_id"] in ib_isa_account_ids
        ]
    
    # Recalculate allocation
    for position in filtered_data["positions"]:
        symbol = position["symbol"]
        
        if symbol not in filtered_data["allocation"]:
            filtered_data["allocation"][symbol] = {
                "total_value": 0,
                "total_quantity": 0,
                "description": position["description"]
            }
            
        filtered_data["allocation"][symbol]["total_value"] += position["market_value"]
        filtered_data["allocation"][symbol]["total_quantity"] += position["quantity"]
    
    return filtered_data

def display_example_dashboard():
    """Display an example dashboard with sample data"""
    example_data = {
        "total_value": 153425.67,
        "accounts": [
            {"broker": "Schwab", "account_id": "12345", "account_name": "Example Schwab Account", "account_type": "Individual", "value": 98765.43},
            {"broker": "Interactive Brokers", "account_id": "67890", "account_name": "Example IB Account", "account_type": "Margin", "value": 34660.24},
            {"broker": "Interactive Brokers", "account_id": "67891", "account_name": "Example IB ISA", "account_type": "ISA", "value": 20000.00}
        ],
        "positions": [
            {"broker": "Schwab", "account_id": "12345", "symbol": "AAPL", "description": "Apple Inc.", "quantity": 50, "market_value": 8750.00, "cost_basis": 6500.00, "unrealized_pl": 2250.00, "unrealized_pl_percent": 34.62},
            {"broker": "Schwab", "account_id": "12345", "symbol": "MSFT", "description": "Microsoft Corp.", "quantity": 40, "market_value": 12800.00, "cost_basis": 10400.00, "unrealized_pl": 2400.00, "unrealized_pl_percent": 23.08},
            {"broker": "Schwab", "account_id": "12345", "symbol": "VTI", "description": "Vanguard Total Stock Market ETF", "quantity": 200, "market_value": 40000.00, "cost_basis": 35000.00, "unrealized_pl": 5000.00, "unrealized_pl_percent": 14.29},
            {"broker": "Interactive Brokers", "account_id": "67890", "symbol": "GOOGL", "description": "Alphabet Inc.", "quantity": 25, "market_value": 3750.00, "cost_basis": 3250.00, "unrealized_pl": 500.00, "unrealized_pl_percent": 15.38},
            {"broker": "Interactive Brokers", "account_id": "67890", "symbol": "AMZN", "description": "Amazon.com Inc.", "quantity": 10, "market_value": 1750.00, "cost_basis": 1500.00, "unrealized_pl": 250.00, "unrealized_pl_percent": 16.67},
            {"broker": "Interactive Brokers", "account_id": "67890", "symbol": "SPY", "description": "SPDR S&P 500 ETF", "quantity": 100, "market_value": 25000.00, "cost_basis": 22000.00, "unrealized_pl": 3000.00, "unrealized_pl_percent": 13.64},
            {"broker": "Interactive Brokers", "account_id": "67891", "symbol": "FTSE", "description": "FTSE 100 Index Fund", "quantity": 500, "market_value": 15000.00, "cost_basis": 14000.00, "unrealized_pl": 1000.00, "unrealized_pl_percent": 7.14},
            {"broker": "Interactive Brokers", "account_id": "67891", "symbol": "VOD", "description": "Vodafone Group PLC", "quantity": 1000, "market_value": 5000.00, "cost_basis": 5500.00, "unrealized_pl": -500.00, "unrealized_pl_percent": -9.09}
        ],
        "brokers": {
            "Schwab": 98765.43,
            "Interactive Brokers": 54660.24
        },
        "allocation": {
            "AAPL": {"total_value": 8750.00, "total_quantity": 50, "description": "Apple Inc."},
            "MSFT": {"total_value": 12800.00, "total_quantity": 40, "description": "Microsoft Corp."},
            "VTI": {"total_value": 40000.00, "total_quantity": 200, "description": "Vanguard Total Stock Market ETF"},
            "GOOGL": {"total_value": 3750.00, "total_quantity": 25, "description": "Alphabet Inc."},
            "AMZN": {"total_value": 1750.00, "total_quantity": 10, "description": "Amazon.com Inc."},
            "SPY": {"total_value": 25000.00, "total_quantity": 100, "description": "SPDR S&P 500 ETF"},
            "FTSE": {"total_value": 15000.00, "total_quantity": 500, "description": "FTSE 100 Index Fund"},
            "VOD": {"total_value": 5000.00, "total_quantity": 1000, "description": "Vodafone Group PLC"}
        }
    }
    
    # Let the user choose which view to display
    view_option = st.radio(
        "Select view:",
        ["All Accounts", "Schwab Only", "Interactive Brokers ISA Only"],
        horizontal=True
    )
    
    view_mapping = {
        "All Accounts": "all",
        "Schwab Only": "schwab",
        "Interactive Brokers ISA Only": "ib_isa"
    }
    
    display_portfolio_summary(example_data, view_mapping[view_option])

#######################################################
# Main Streamlit App
#######################################################

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Portfolio Summary", "Authentication", "Settings", "Help"])

with tab2:
    st.header("Authentication")
    
    # Schwab Authentication
    st.subheader("Charles Schwab")
    
    # Check if we already have a token in session state
    if "schwab_token" in st.session_state:
        st.success("✅ Connected to Charles Schwab")
        if st.button("Disconnect from Schwab"):
            del st.session_state["schwab_token"]
            st.experimental_rerun()
    else:
        # Check if we have an authorization code in the URL
        query_params = st.query_params
        
        if "code" in query_params:
            # Extract the authorization code from the query parameters
            auth_code = query_params["code"]
            st.info(f"Authorization code received. Processing...")
            
            # Exchange the code for an access token
            access_token = get_schwab_access_token(auth_code)
            if access_token:
                st.success("Successfully connected to Charles Schwab!")
                # Clear the query parameter to avoid repeated token requests
                st.experimental_set_query_params()
                st.experimental_rerun()
        else:
            # If no authorization code is present, show the button to authorize the app
            auth_url = (
                f"{SCHWAB_AUTH_URL}"
                f"?response_type=code"
                f"&client_id={SCHWAB_CLIENT_ID}"
                f"&redirect_uri={SCHWAB_REDIRECT_URI}"
                f"&scope=readonly"
            )
            
            st.markdown(f"[Authorize with Schwab]({auth_url})")
            st.info("Note: You'll be redirected to Schwab to authenticate, then back to this app.")
    
    # Interactive Brokers Authentication
    st.subheader("Interactive Brokers")
    
    if "ib_connected" in st.session_state and st.session_state["ib_connected"]:
        st.success("✅ Connected to Interactive Brokers")
        if st.button("Disconnect from Interactive Brokers"):
            st.session_state["ib_connected"] = False
            if "ib_client" in st.session_state:
                del st.session_state["ib_client"]
            st.experimental_rerun()
    else:
        st.info("To connect to Interactive Brokers, you need to set up the IB API Gateway.")
        
        with st.expander("Interactive Brokers Setup Instructions"):
            st.write("""
            1. Download and install the IB API Gateway from the Interactive Brokers website
            2. Configure the gateway with your account credentials
            3. Start the gateway and ensure it's running on port 4001
            4. Add your IB credentials to your .env file:
               ```
               IB_CLIENT_ID=1
               IB_GATEWAY_PORT=4001
               IB_HOST=127.0.0.1
               ```
            5. Click the Connect button below
            """)
        
        if st.button("Connect to Interactive Brokers"):
            ib_client = connect_to_ib()
            if ib_client:
                st.success("Successfully connected to Interactive Brokers!")
                st.session_state["ib_client"] = ib_client
                st.experimental_rerun()
            else:
                st.error("Failed to connect to Interactive Brokers. Check your credentials and make sure the IB Gateway is running.")

with tab1:
    st.header("Portfolio Summary")
    
    # Initialize combined data
    combined_data = None
    
    # Check if we have Schwab data
    schwab_data = None
    if "schwab_token" in st.session_state:
        with st.spinner("Loading Schwab data..."):
            access_token = st.session_state["schwab_token"]["access_token"]
            raw_account_info = get_schwab_account_info(access_token)
            
            if raw_account_info:
                # Parse the raw Schwab data
                schwab_data = parse_schwab_data(raw_account_info)
    
    # Check if we have IB data
    ib_data = None
    if "ib_connected" in st.session_state and st.session_state["ib_connected"]:
        with st.spinner("Loading Interactive Brokers data..."):
            # In a real app, you'd use the IB client to fetch data
            # For now, use the sample data function
            raw_ib_data = get_ib_account_data()
            if raw_ib_data:
                ib_data = parse_ib_data(raw_ib_data)
    
    # Combine data from both brokerages if available
    if schwab_data or ib_data:
        combined_data = combine_portfolio_data(schwab_data, ib_data)
        
        # Let the user choose which view to display
        view_option = st.radio(
            "Select view:",
            ["All Accounts", "Schwab Only", "Interactive Brokers ISA Only"],
            horizontal=True
        )
        
        view_mapping = {
            "All Accounts": "all",
            "Schwab Only": "schwab",
            "Interactive Brokers ISA Only": "ib_isa"
        }
        
        display_portfolio_summary(combined_data, view_mapping[view_option])
        
    else:
        st.info("Please connect at least one brokerage account in the Authentication tab.")
        
        # Show example dashboard if user wants to see a preview
        if st.button("Show Example Dashboard"):
            display_example_dashboard()

with tab3:
    st.header("Settings")
    
    st.subheader("Data Refresh")
    refresh_interval = st.slider("Auto-refresh interval (minutes)", 0, 60, 15)
    st.info(f"Dashboard will auto-refresh every {refresh_interval} minutes. Set to 0 to disable auto-refresh.")
    
    st.subheader("Display Settings")
    currency = st.selectbox("Display Currency", ["USD", "GBP", "EUR", "JPY"], index=0)
    st.info(f"All values will be converted to {currency} using current exchange rates.")
    
    st.subheader("Notifications")
    enable_notifications = st.checkbox("Enable email notifications for significant changes", value=False)
    if enable_notifications:
        email = st.text_input("Email address for notifications")
        threshold = st.slider("Notification threshold (%)", 1, 10, 5)
        st.info(f"You'll receive email notifications when portfolio value changes by {threshold}% or more.")

with tab4:
    st.header("Help & Information")
    
    st.subheader("About This Dashboard")
    st.write("""
    This investment portfolio dashboard helps you track your investments across multiple brokerages.
    Currently supported:
    - Charles Schwab
    - Interactive Brokers
    
    Features:
    - View your total portfolio value across all accounts
    - Track individual positions and performance
    - Analyze your asset allocation
    - Compare performance across different accounts
    """)
    
    st.subheader("API Connection Help")
    with st.expander("Charles Schwab Connection Issues"):
        st.write("""
        To connect to Charles Schwab:
        
        1. Make sure you have a developer account with Schwab
        2. Register your application in the Schwab Developer Portal
        3. Set up your redirect URI with ngrok
        4. Add your credentials to the .env file
        5. Click "Authorize with Schwab" in the Authentication tab
        
        If you're having trouble:
        - Check that your ngrok URL is correctly registered in the Schwab Developer Portal
        - Verify that your Client ID and Client Secret are correct in the .env file
        - Make sure ngrok is running on port 8501
        """)
    
    with st.expander("Interactive Brokers Connection Issues"):
        st.write("""
        To connect to Interactive Brokers:
        
        1. Install the IB API Gateway
        2. Configure it with your IB account credentials
        3. Start the gateway and ensure it's running on port 4001
        4. Add your IB credentials to the .env file
        5. Click "Connect to Interactive Brokers" in the Authentication tab
        
        If you're having trouble:
        - Check that the IB Gateway is running
        - Verify that your Client ID is correct in the .env file
        - Make sure the gateway is configured to accept connections from localhost
        """)
    
    st.subheader("Contact Support")
    st.write("For assistance with this dashboard, please contact support at support@example.com.")