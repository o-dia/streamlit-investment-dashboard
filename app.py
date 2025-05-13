# Import necessary libraries
import streamlit as st  # Streamlit library for creating web applications
import pandas as pd     # Pandas for data manipulation and analysis
import numpy as np      # NumPy for numerical operations
import time             # Time library for handling time-related tasks
import requests         # Requests library for making HTTP requests to APIs
import os               # OS module for interacting with the operating system
import plotly.express as px          # Plotly Express for simple interactive plots
import plotly.graph_objects as go     # Plotly Graph Objects for more complex plots
from datetime import datetime         # DateTime for handling dates and times
from dotenv import load_dotenv        # dotenv for loading environment variables from .env file

# Load environment variables from .env file
# This function reads the .env file in your project directory
# and makes its contents available through os.getenv()
load_dotenv()

# Set page configuration for the Streamlit app
# This configures the page title and layout
st.set_page_config(page_title="Investment Portfolio Dashboard", layout="wide")

# Set the title and subtitle for your application
# These will appear at the top of your Streamlit app
st.title("Investment Portfolio Dashboard")
st.subheader("Track your investments across Charles Schwab and Interactive Brokers")

#######################################################
# Configuration and API Credentials
#######################################################

# The os.getenv() function retrieves environment variables from your system
# Syntax: os.getenv(variable_name, default_value)
# - variable_name: Name of the environment variable to retrieve
# - default_value: Value to return if the variable doesn't exist

# This gets the SCHWAB_CLIENT_ID from your .env file
# If the variable isn't found, it uses "your_client_id_here" as a fallback
SCHWAB_CLIENT_ID = os.getenv("SCHWAB_CLIENT_ID", "your_client_id_here")

# Similarly, this gets SCHWAB_CLIENT_SECRET with a fallback value
SCHWAB_CLIENT_SECRET = os.getenv("SCHWAB_CLIENT_SECRET", "your_client_secret_here")

# Gets the redirect URI from .env or uses a default
SCHWAB_REDIRECT_URI = os.getenv("SCHWAB_REDIRECT_URI", "https://your-ngrok-url.ngrok-free.app/callback")

# Interactive Brokers configuration with default values
# These will be loaded from .env when implemented
IB_CLIENT_ID = os.getenv("IB_CLIENT_ID", "")  # Empty string default means no value
IB_GATEWAY_PORT = os.getenv("IB_GATEWAY_PORT", "4001")  # Default port is 4001
IB_HOST = os.getenv("IB_HOST", "127.0.0.1")  # Default to localhost

# API endpoints for Schwab services
# These URLs are where our app will send requests to interact with Schwab's API
SCHWAB_AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"  # For user authorization
SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"     # For getting access tokens
SCHWAB_ACCOUNTS_URL = "https://api.schwab.com/v2/accounts"        # For retrieving account data

#######################################################
# Charles Schwab Functions
#######################################################

def get_schwab_access_token(auth_code):
    """
    Exchange an authorization code for an access token with Schwab API
    
    Parameters:
    - auth_code (str): The authorization code received after user authorization
    
    Returns:
    - str or None: The access token if successful, None if it failed
    
    This function:
    1. Prepares the payload for the token request
    2. Sends a POST request to Schwab's token endpoint
    3. Processes the response and stores the token in session state
    4. Returns the access token or None if there's an error
    """
    # Add debugging information to the Streamlit interface
    st.write(f"Attempting to exchange auth code for token...")
    
    # Prepare the request payload according to OAuth standards
    payload = {
        "grant_type": "authorization_code",  # Type of OAuth grant
        "code": auth_code,                   # The code we received
        "redirect_uri": SCHWAB_REDIRECT_URI, # Must match what was registered
        "client_id": SCHWAB_CLIENT_ID,       # Our app's ID
        "client_secret": SCHWAB_CLIENT_SECRET, # Our app's secret
    }
    
    # Show some information (with sensitive parts redacted)
    st.write(f"Using redirect URI: {SCHWAB_REDIRECT_URI}")
    # Only show the first 5 chars of the client ID for security
    st.write(f"Using client ID: {SCHWAB_CLIENT_ID[:5]}... (redacted)")
    
    try:
        # Log the API endpoint we're contacting
        st.write(f"Sending request to: {SCHWAB_TOKEN_URL}")
        
        # Send the POST request to Schwab's token endpoint
        # - requests.post() makes an HTTP POST request
        # - data=payload sends our parameters in the request body
        response = requests.post(SCHWAB_TOKEN_URL, data=payload)
        
        # Log the response status code and body for debugging
        st.write(f"Response status code: {response.status_code}")
        st.write(f"Response body: {response.text}")
        
        # Raise an exception if the response status code is 4XX or 5XX
        # This helps catch HTTP errors like 401 Unauthorized, 404 Not Found, etc.
        response.raise_for_status()
        
        # Parse the JSON response into a Python dictionary
        access_token_info = response.json()
        
        # Store the entire token response in Streamlit's session state
        # This makes it available across different runs of the app
        st.session_state["schwab_token"] = access_token_info
        
        # Return just the access token part
        return access_token_info["access_token"]
    
    # Handle errors from the requests library
    except requests.exceptions.RequestException as e:
        # Display the error in the Streamlit interface
        st.error(f"Error getting access token: {str(e)}")
        
        # If the error has a response, show more details
        if hasattr(e, "response") and e.response is not None:
            st.error(f"Error details: {e.response.text}")
        
        # Return None to indicate failure
        return None
    
    # Catch any other unexpected errors
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        
        # Import traceback to get more detailed error information
        import traceback
        # Display the full stack trace
        st.error(traceback.format_exc())
        
        # Return None to indicate failure
        return None
    
def get_schwab_account_info(access_token):
    """
    Fetch account information from the Schwab API
    
    Parameters:
    - access_token (str): OAuth access token to authenticate the request
    
    Returns:
    - dict or None: JSON response with account information or None if it failed
    
    This function makes an authenticated request to Schwab's accounts endpoint
    to retrieve information about the user's accounts and positions.
    """
    # Prepare the request headers
    # The Authorization header uses the Bearer token format for OAuth
    headers = {
        "Authorization": f"Bearer {access_token}",  # Include access token
        "Content-Type": "application/json"          # Specify JSON format
    }
    
    try:
        # Send a GET request to the accounts endpoint
        # - requests.get() makes an HTTP GET request
        # - headers=headers includes our authentication in the request
        response = requests.get(SCHWAB_ACCOUNTS_URL, headers=headers)
        
        # Raise an exception for 4XX/5XX status codes
        response.raise_for_status()
        
        # Parse and return the JSON response
        return response.json()
    
    # Handle any request-related errors
    except requests.exceptions.RequestException as e:
        st.error(f"Error retrieving account information: {str(e)}")
        
        # Show more details if available
        if hasattr(e, "response") and e.response is not None:
            st.error(f"Error details: {e.response.text}")
            
        # Return None to indicate failure
        return None

def parse_schwab_data(raw_data):
    """
    Parse the raw Schwab API response into a structured format
    
    Parameters:
    - raw_data (dict): The JSON response from Schwab's API
    
    Returns:
    - dict or None: Structured portfolio data or None if parsing failed
    
    Note: This function is a placeholder that needs to be adapted
    based on the actual structure of Schwab's API response.
    """
    try:
        # Get the accounts array from the response, or empty list if not found
        # The .get() method on dictionaries returns a default value if the key doesn't exist
        accounts = raw_data.get("accounts", [])
        
        # Initialize the structured data with empty values
        parsed_data = {
            "total_value": 0,           # Will hold the sum of all account values
            "accounts": [],             # Will hold account details
            "positions": []             # Will hold position details
        }
        
        # Process each account in the accounts array
        for account in accounts:
            # Extract the account value, defaulting to 0 if not found
            # The nested .get() calls handle the case where "balances" doesn't exist
            account_value = float(account.get("balances", {}).get("totalAccountValue", 0))
            
            # Add this account's value to the total
            parsed_data["total_value"] += account_value
            
            # Add account details to the accounts array
            parsed_data["accounts"].append({
                "account_id": account.get("accountId", "Unknown"),     # Account identifier
                "account_name": account.get("accountName", "Unknown"), # Account name
                "account_type": account.get("accountType", "Unknown"), # Account type
                "value": account_value                                # Account value
            })
            
            # Get positions for this account, defaulting to empty list if not found
            positions = account.get("positions", [])
            
            # Process each position in this account
            for position in positions:
                # Get security details, defaulting to empty dict if not found
                security = position.get("security", {})
                
                # Add position details to the positions array
                parsed_data["positions"].append({
                    "account_id": account.get("accountId", "Unknown"),      # Link to account
                    "symbol": security.get("symbol", "Unknown"),           # Stock symbol
                    "description": security.get("description", "Unknown"),  # Security name
                    "quantity": float(position.get("quantity", 0)),         # Shares owned
                    "market_value": float(position.get("marketValue", 0)),  # Current value
                    "cost_basis": float(position.get("costBasis", 0)),      # Purchase cost
                    "unrealized_pl": float(position.get("unrealizedPL", 0)), # Profit/loss
                    "unrealized_pl_percent": float(position.get("unrealizedPLPercent", 0)) # P/L %
                })
        
        # Return the fully structured data
        return parsed_data
        
    # Handle any errors during parsing
    except Exception as e:
        st.error(f"Error parsing Schwab data: {str(e)}")
        return None

#######################################################
# Interactive Brokers Functions
#######################################################

def connect_to_ib():
    """
    Connect to the Interactive Brokers API
    
    Returns:
    - dict or None: Connection information or None if connection failed
    
    Note: This is a placeholder function. In a real implementation,
    you would import and use the IB API client.
    """
    # Check if IB credentials are configured
    if not IB_CLIENT_ID:
        st.warning("Interactive Brokers credentials not configured in .env file")
        return None
    
    try:
        # Simulate a successful connection for demonstration purposes
        # In a real implementation, this would connect to the IB API Gateway
        
        # Store connection status in session state
        st.session_state["ib_connected"] = True
        
        # Return a mock connection object
        return {"connected": True, "client_id": IB_CLIENT_ID}
    
    # Handle any errors during connection
    except Exception as e:
        st.error(f"Error connecting to Interactive Brokers: {str(e)}")
        return None

def get_ib_account_data():
    """
    Fetch account data from Interactive Brokers
    
    Returns:
    - dict: Sample account data for demonstration
    
    Note: This is a placeholder function that returns sample data.
    In a real implementation, you would use the IB API to fetch actual data.
    """
    # This is sample data to demonstrate the UI functionality
    # In a real app, this would be replaced with actual API calls
    sample_data = {
        # Account summary information
        "account_summary": {
            "U1234567": {  # Account ID
                "NetLiquidation": {"value": "105432.78", "currency": "USD"},  # Total value
                "TotalCashValue": {"value": "25876.45", "currency": "USD"},   # Cash balance
                "AvailableFunds": {"value": "25876.45", "currency": "USD"}    # Available funds
            }
        },
        # Position information
        "positions": [
            {
                "account": "U1234567",   # Account ID
                "symbol": "AAPL",        # Stock symbol
                "secType": "STK",        # Security type (stock)
                "exchange": "NASDAQ",    # Exchange
                "position": 50,          # Number of shares
                "avgCost": 182.45        # Average cost per share
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
                "secType": "ETF",         # Security type (ETF)
                "exchange": "NYSE",
                "position": 100,
                "avgCost": 217.89
            }
        ]
    }
    
    # Return the sample data
    return sample_data

def parse_ib_data(ib_data):
    """
    Parse Interactive Brokers data into a structured format
    
    Parameters:
    - ib_data (dict): The raw data from Interactive Brokers
    
    Returns:
    - dict or None: Structured portfolio data or None if parsing failed
    """
    # Check if data is None
    if ib_data is None:
        return None
        
    try:
        # Initialize the structured data with empty values
        parsed_data = {
            "total_value": 0,           # Will hold the sum of all account values
            "accounts": [],             # Will hold account details
            "positions": []             # Will hold position details
        }
        
        # Process account summary information
        # Iterate through each account in the account_summary dictionary
        for account_id, summary in ib_data["account_summary"].items():
            # Extract net liquidation value (total account value)
            # Using nested .get() calls with default values in case keys don't exist
            account_value = float(summary.get("NetLiquidation", {}).get("value", 0))
            
            # Add this account's value to the total
            parsed_data["total_value"] += account_value
            
            # Add account details to the accounts array
            parsed_data["accounts"].append({
                "account_id": account_id,               # Account identifier
                "account_name": f"IB {account_id}",     # Create a display name
                "account_type": "Investment",           # Default account type
                "value": account_value                  # Account value
            })
        
        # Process position information
        # Iterate through each position in the positions array
        for position in ib_data["positions"]:
            # Calculate market value (position size * average cost)
            # In a real app, you'd use current price data for accuracy
            market_value = position["position"] * position["avgCost"]
            
            # Calculate cost basis (position size * average cost)
            cost_basis = position["position"] * position["avgCost"]
            
            # Add position details to the positions array
            parsed_data["positions"].append({
                "account_id": position["account"],                     # Link to account
                "symbol": position["symbol"],                          # Stock symbol
                "description": f"{position['symbol']} ({position['secType']})", # Description
                "quantity": position["position"],                       # Number of shares
                "market_value": market_value,                          # Current value
                "cost_basis": cost_basis,                              # Purchase cost
                "unrealized_pl": 0,  # Would need current price data for accurate value
                "unrealized_pl_percent": 0  # Would need current price data for accurate value
            })
            
        # Return the fully structured data
        return parsed_data
        
    # Handle any errors during parsing
    except Exception as e:
        st.error(f"Error parsing IB data: {str(e)}")
        return None

#######################################################
# Combined Portfolio Functions
#######################################################

def combine_portfolio_data(schwab_data, ib_data):
    """
    Combine data from both brokerages into a single portfolio view
    
    Parameters:
    - schwab_data (dict): Structured data from Schwab
    - ib_data (dict): Structured data from Interactive Brokers
    
    Returns:
    - dict: Combined portfolio data from both brokerages
    """
    # Use empty data structures if either input is None
    # This allows the function to work even if only one brokerage is connected
    if schwab_data is None:
        schwab_data = {"total_value": 0, "accounts": [], "positions": []}
    if ib_data is None:
        ib_data = {"total_value": 0, "accounts": [], "positions": []}
    
    # Initialize the combined data structure
    combined_data = {
        "total_value": schwab_data["total_value"] + ib_data["total_value"], # Sum of both
        "accounts": [],              # Will hold all accounts
        "positions": [],             # Will hold all positions
        "allocation": {},            # Will hold asset allocation by symbol
        "brokers": {                 # Breakdown by broker
            "Schwab": schwab_data["total_value"],
            "Interactive Brokers": ib_data["total_value"]
        }
    }
    
    # Add Schwab accounts to the combined accounts list
    # For each account in the Schwab data, add it to the combined data
    for account in schwab_data["accounts"]:
        combined_data["accounts"].append({
            "broker": "Schwab",                  # Add broker name
            "account_id": account["account_id"],
            "account_name": account["account_name"],
            "account_type": account["account_type"],
            "value": account["value"]
        })
    
    # Add Interactive Brokers accounts to the combined accounts list
    # For each account in the IB data, add it to the combined data
    for account in ib_data["accounts"]:
        combined_data["accounts"].append({
            "broker": "Interactive Brokers",     # Add broker name
            "account_id": account["account_id"],
            "account_name": account["account_name"],
            "account_type": account["account_type"],
            "value": account["value"]
        })
    
    # Add Schwab positions to the combined positions list
    # For each position in the Schwab data, add it to the combined data
    for position in schwab_data["positions"]:
        symbol = position["symbol"]
        
        # Add position to the combined positions list
        combined_data["positions"].append({
            "broker": "Schwab",                  # Add broker name
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
        # If this symbol isn't in the allocation dict yet, add it
        if symbol not in combined_data["allocation"]:
            combined_data["allocation"][symbol] = {
                "total_value": 0,
                "total_quantity": 0,
                "description": position["description"]
            }
        
        # Add this position's value and quantity to the symbol's allocation
        combined_data["allocation"][symbol]["total_value"] += position["market_value"]
        combined_data["allocation"][symbol]["total_quantity"] += position["quantity"]
    
    # Add Interactive Brokers positions to the combined positions list
    # For each position in the IB data, add it to the combined data
    for position in ib_data["positions"]:
        symbol = position["symbol"]
        
        # Add position to the combined positions list
        combined_data["positions"].append({
            "broker": "Interactive Brokers",     # Add broker name
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
        # If this symbol isn't in the allocation dict yet, add it
        if symbol not in combined_data["allocation"]:
            combined_data["allocation"][symbol] = {
                "total_value": 0,
                "total_quantity": 0,
                "description": position["description"]
            }
        
        # Add this position's value and quantity to the symbol's allocation
        combined_data["allocation"][symbol]["total_value"] += position["market_value"]
        combined_data["allocation"][symbol]["total_quantity"] += position["quantity"]
    
    # Return the combined portfolio data
    return combined_data

#######################################################
# Dashboard Display Functions
#######################################################

def display_portfolio_summary(combined_data, view_type="all"):
    """
    Display portfolio summary based on the selected view type
    
    Parameters:
    - combined_data (dict): Combined portfolio data
    - view_type (str): Type of view to display ("all", "schwab", or "ib_isa")
    
    This function creates the dashboard visualizations and tables
    based on the filtered portfolio data.
    """
    # Filter data based on view_type
    # This uses the filter_portfolio_data function to get just the data we want to show
    filtered_data = filter_portfolio_data(combined_data, view_type)
    
    # Check if there's data to display
    if filtered_data["total_value"] == 0:
        st.info(f"No data available for the selected view: {view_type}")
        return
    
    # Display total portfolio value
    st.subheader("Total Portfolio Value")
    total_value = filtered_data["total_value"]
    
    # Use st.metric to display the value
    # In a real app, you would calculate the change values for the third parameter
    st.metric("Portfolio Value", f"${total_value:,.2f}", "")
    
    # Create a row with three columns for summary metrics
    # st.columns creates a layout with the specified number of equal-width columns
    col1, col2, col3 = st.columns(3)
    
    # Count positions and calculate average position value
    num_positions = len(filtered_data["positions"])
    # Avoid division by zero by checking if num_positions is zero
    avg_position_value = total_value / num_positions if num_positions > 0 else 0
    
    # Display metrics in the columns
    # The with statement places content in the specified column
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
        
        # Calculate percentages for each broker
        broker_data = []
        for broker, value in filtered_data["brokers"].items():
            # Calculate percentage of total, avoiding division by zero
            if total_value > 0:
                percentage = (value / total_value) * 100
            else:
                percentage = 0
                
            # Add broker data to list for plotting
            broker_data.append({
                "Broker": broker,
                "Value": value,
                "Percentage": percentage
            })
        
        # Create broker breakdown pie chart using Plotly Express
        # px.pie creates a pie chart visualization
        # Parameters:
        # - data: The data to visualize
        # - values: Which field contains the numerical values
        # - names: Which field contains the category names
        # - title: Chart title
        # - hover_data: Additional fields to show on hover
        # - labels: Custom labels for the data fields
        fig_broker = px.pie(
            broker_data, 
            values="Value", 
            names="Broker", 
            title="Portfolio by Broker",
            hover_data=["Percentage"],
            labels={"Value": "Portfolio Value"}
        )
        
        # Configure the pie chart to show percentages and labels
        fig_broker.update_traces(textinfo="percent+label")
        
        # Display the chart in the Streamlit app
        st.plotly_chart(fig_broker)
    
    # Display account breakdown
    st.subheader("Account Breakdown")
    
    # Prepare account data for display
    account_data = []
    for account in filtered_data["accounts"]:
        # Calculate percentage of total, avoiding division by zero
        if total_value > 0:
            percentage = (account["value"] / total_value) * 100
        else:
            percentage = 0
            
        # Add account data to list for display
        account_data.append({
            "Broker": account["broker"],
            "Account": account["account_name"],
            "Type": account["account_type"],
            "Value": account["value"],
            "Percentage": percentage
        })
    
    # Convert to DataFrame for display
    # pd.DataFrame converts a list of dictionaries to a DataFrame
    df_accounts = pd.DataFrame(account_data)
    
    # Format the Value column as currency
    # The map function applies a format to each value in the column
    df_accounts["Value"] = df_accounts["Value"].map("${:,.2f}".format)
    
    # Format the Percentage column with one decimal place
    df_accounts["Percentage"] = df_accounts["Percentage"].map("{:.1f}%".format)
    
    # Display accounts table
    # st.dataframe displays a DataFrame as an interactive table
    # use_container_width=True makes the table fill the available width
    st.dataframe(df_accounts, use_container_width=True)
    
    # Display asset allocation
    st.subheader("Asset Allocation")
    
    # Prepare allocation data for pie chart
    allocation_data = []
    for symbol, data in filtered_data["allocation"].items():
        # Calculate percentage of total, avoiding division by zero
        if total_value > 0:
            percentage = (data["total_value"] / total_value) * 100
        else:
            percentage = 0
            
        # Add allocation data to list for plotting
        allocation_data.append({
            "Symbol": symbol,
            "Description": data["description"],
            "Value": data["total_value"],
            "Percentage": percentage
        })
    
    # Sort by value descending
    # The sorted function returns a new sorted list
    # key=lambda x: x["Value"] means sort by the "Value" field
    # reverse=True means sort in descending order
    allocation_data = sorted(allocation_data, key=lambda x: x["Value"], reverse=True)
    
    # Convert to DataFrame for plotting
    df_allocation = pd.DataFrame(allocation_data)
    
    # Create pie chart using Plotly Express
    fig = px.pie(
        df_allocation, 
        values="Value", 
        names="Symbol", 
        title="Portfolio Allocation by Security",
        hover_data=["Description", "Percentage"],
        labels={"Value": "Market Value"}
    )
    
    # Configure the pie chart to show percentages and labels
    fig.update_traces(textinfo="percent+label")
    
    # Display the chart in the Streamlit app
    st.plotly_chart(fig)
    
    # Display positions table
    st.subheader("Positions")
    
    # Prepare positions data for display
    positions_data = []
    for position in filtered_data["positions"]:
        # Add position data to list for display
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
    # The sort_values method sorts a DataFrame in place
    # by="Market Value" means sort by the "Market Value" column
    # ascending=False means sort in descending order
    df_positions = df_positions.sort_values(by="Market Value", ascending=False)
    
    # Format numeric columns
    # Format Market Value as currency
    df_positions["Market Value"] = df_positions["Market Value"].map("${:,.2f}".format)
    # Format Cost Basis as currency
    df_positions["Cost Basis"] = df_positions["Cost Basis"].map("${:,.2f}".format)
    # Format Unrealized P/L as currency
    df_positions["Unrealized P/L"] = df_positions["Unrealized P/L"].map("${:,.2f}".format)
    # Format % P/L with two decimal places
    df_positions["% P/L"] = df_positions["% P/L"].map("{:.2f}%".format)
    
    # Display positions table
    st.dataframe(df_positions, use_container_width=True)

def filter_portfolio_data(combined_data, view_type):
    """
    Filter portfolio data based on view type
    
    Parameters:
    - combined_data (dict): Combined portfolio data
    - view_type (str): Type of view to filter for ("all", "schwab", or "ib_isa")
    
    Returns:
    - dict: Filtered portfolio data
    """
    # If view_type is "all", return the combined data without filtering
    if view_type == "all":
        return combined_data
    
    # Initialize filtered data structure
    filtered_data = {
        "total_value": 0,
        "accounts": [],
        "positions": [],
        "allocation": {},
        "brokers": {}
    }
    
    # Filter for Schwab accounts only
    if view_type == "schwab":
        # Get Schwab's total value from the combined data
        filtered_data["brokers"]["Schwab"] = combined_data["brokers"].get("Schwab", 0)
        filtered_data["total_value"] = filtered_data["brokers"]["Schwab"]
        
        # Filter accounts to include only Schwab accounts
        # List comprehension creates a new list by filtering the original list
        # "account for account in ..." means "for each account in the original list"
        # "if account["broker"] == "Schwab" means "only include if broker is Schwab"
        filtered_data["accounts"] = [
            account for account in combined_data["accounts"] 
            if account["broker"] == "Schwab"
        ]
        
        # Filter positions to include only Schwab positions
        filtered_data["positions"] = [
            position for position in combined_data["positions"]
            if position["broker"] == "Schwab"
        ]
        
    # Filter for Interactive Brokers ISA accounts only
    elif view_type == "ib_isa":
        # Filter accounts to include only IB accounts with "ISA" in the account type
        # In a real app, you'd have a more precise way to identify ISA accounts
        ib_isa_accounts = [
            account for account in combined_data["accounts"]
            if account["broker"] == "Interactive Brokers" and "ISA" in account.get("account_type", "")
        ]
        
        # Store the filtered accounts
        filtered_data["accounts"] = ib_isa_accounts
        
        # Calculate total value of the filtered accounts
        # sum() adds up all values returned by the generator expression
        # "account["value"] for account in ..." creates a value for each account
        filtered_data["total_value"] = sum(account["value"] for account in ib_isa_accounts)
        
        # Store the broker breakdown
        filtered_data["brokers"]["Interactive Brokers"] = filtered_data["total_value"]
        
        # Get account IDs for filtering positions
        # List comprehension creates a list of account IDs from the filtered accounts
        ib_isa_account_ids = [account["account_id"] for account in ib_isa_accounts]
        
        # Filter positions to include only those from the filtered accounts
        filtered_data["positions"] = [
            position for position in combined_data["positions"]
            if position["broker"] == "Interactive Brokers" and position["account_id"] in ib_isa_account_ids
        ]
    
    # Recalculate allocation based on filtered positions
    for position in filtered_data["positions"]:
        symbol = position["symbol"]
        
        # If this symbol isn't in the allocation dict yet, add it
        if symbol not in filtered_data["allocation"]:
            filtered_data["allocation"][symbol] = {
                "total_value": 0,
                "total_quantity": 0,
                "description": position["description"]
            }
            
        # Add this position's value and quantity to the symbol's allocation
        filtered_data["allocation"][symbol]["total_value"] += position["market_value"]
        filtered_data["allocation"][symbol]["total_quantity"] += position["quantity"]
    
    # Return the filtered data
    return filtered_data

def display_example_dashboard():
    """
    Display an example dashboard with sample data
    
    This function creates a demonstration dashboard with fake data
    to show how the real dashboard will look once connected.
    """
    # Sample data for demonstration
    example_data = {
        # Total portfolio value
        "total_value": 153425.67,
        
        # Account details
        "accounts": [
            {"broker": "Schwab", "account_id": "12345", "account_name": "Example Schwab Account", "account_type": "Individual", "value": 98765.43},
            {"broker": "Interactive Brokers", "account_id": "67890", "account_name": "Example IB Account", "account_type": "Margin", "value": 34660.24},
            {"broker": "Interactive Brokers", "account_id": "67891", "account_name": "Example IB ISA", "account_type": "ISA", "value": 20000.00}
        ],
        
        # Position details
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
        
        # Broker breakdown
        "brokers": {
            "Schwab": 98765.43,
            "Interactive Brokers": 54660.24
        },
        
        # Asset allocation
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
    # st.radio creates a radio button group
    # Parameters:
    # - Label for the radio button group
    # - List of options
    # - horizontal=True displays options horizontally instead of vertically
    view_option = st.radio(
        "Select view:",
        ["All Accounts", "Schwab Only", "Interactive Brokers ISA Only"],
        horizontal=True
    )
    
    # Map the selected option to the view_type parameter
    view_mapping = {
        "All Accounts": "all",
        "Schwab Only": "schwab",
        "Interactive Brokers ISA Only": "ib_isa"
    }
    
    # Display the portfolio summary with the selected view type
    display_portfolio_summary(example_data, view_mapping[view_option])

#######################################################
# Main Streamlit App
#######################################################

# Create tabs for different sections of the app
# st.tabs creates a tabbed interface
# Parameters:
# - List of tab names
# It returns a list of tab objects that can be used with "with" statements
tab1, tab2, tab3, tab4 = st.tabs(["Portfolio Summary", "Authentication", "Settings", "Help"])

# Authentication tab
# The "with" statement focuses the following code on a specific tab
with tab2:
    st.header("Authentication")
    
    # Schwab Authentication section
    st.subheader("Charles Schwab")
    
    # Check if we already have a token in session state
    # st.session_state is a dictionary-like object that persists between reruns
    if "schwab_token" in st.session_state:
        # If we have a token, show connected status
        st.success("✅ Connected to Charles Schwab")
        
        # Add a button to disconnect
        # st.button creates a button that returns True when clicked
        if st.button("Disconnect from Schwab"):
            # Delete the token from session state
            del st.session_state["schwab_token"]
            
            # Rerun the app to update the UI
            # This restarts the script from the beginning
            st.experimental_rerun()
    else:
        # If we don't have a token, check for an authorization code
        # st.query_params contains URL query parameters
        query_params = st.query_params
        
        # Check if "code" is in the query parameters
        if "code" in query_params:
            # Extract the authorization code
            auth_code = query_params["code"]
            st.info(f"Authorization code received. Processing...")
            
            # Exchange the code for an access token
            access_token = get_schwab_access_token(auth_code)
            
            # If we got a token successfully
            if access_token:
                st.success("Successfully connected to Charles Schwab!")
                
                # Clear the query parameter to avoid repeated token requests
                # This removes the code from the URL
                st.experimental_set_query_params()
                
                # Rerun the app to update the UI
                st.experimental_rerun()
        else:
            # If no authorization code is present, show the button to authorize
            
            # Construct the authorization URL
            # This is the URL the user will be redirected to for authorization
            auth_url = (
                f"{SCHWAB_AUTH_URL}"
                f"?response_type=code"
                f"&client_id={SCHWAB_CLIENT_ID}"
                f"&redirect_uri={SCHWAB_REDIRECT_URI}"
                f"&scope=readonly"
            )
            
            # Display a button that links to the authorization URL
            # st.markdown creates formatted text or links
            st.markdown(f"[Authorize with Schwab]({auth_url})")
            
            # Display information about the process
            st.info("Note: You'll be redirected to Schwab to authenticate, then back to this app.")
    
    # Interactive Brokers Authentication section
    st.subheader("Interactive Brokers")
    
    # Check if we're already connected to Interactive Brokers
    if "ib_connected" in st.session_state and st.session_state["ib_connected"]:
        # If connected, show status
        st.success("✅ Connected to Interactive Brokers")
        
        # Add a button to disconnect
        if st.button("Disconnect from Interactive Brokers"):
            # Set connected status to False
            st.session_state["ib_connected"] = False
            
            # Remove the client object if it exists
            if "ib_client" in st.session_state:
                del st.session_state["ib_client"]
                
            # Rerun the app to update the UI
            st.experimental_rerun()
    else:
        # If not connected, show instructions
        st.info("To connect to Interactive Brokers, you need to set up the IB API Gateway.")
        
        # Create an expandable section with more details
        # st.expander creates a section that can be expanded/collapsed
        with st.expander("Interactive Brokers Setup Instructions"):
            # Display instructions for setting up IB connection
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
        
        # Add a button to connect
        if st.button("Connect to Interactive Brokers"):
            # Try to connect
            ib_client = connect_to_ib()
            
            # If connection was successful
            if ib_client:
                st.success("Successfully connected to Interactive Brokers!")
                
                # Store the client object in session state
                st.session_state["ib_client"] = ib_client
                
                # Rerun the app to update the UI
                st.experimental_rerun()
            else:
                # If connection failed, show error
                st.error("Failed to connect to Interactive Brokers. Check your credentials and make sure the IB Gateway is running.")

# Portfolio Summary tab
with tab1:
    st.header("Portfolio Summary")
    
    # Initialize combined data as None
    combined_data = None
    
    # Check if we have Schwab data
    schwab_data = None
    if "schwab_token" in st.session_state:
        # Display a spinner while loading
        # st.spinner shows a loading spinner during the contained operations
        with st.spinner("Loading Schwab data..."):
            # Get the access token from session state
            access_token = st.session_state["schwab_token"]["access_token"]
            
            # Fetch account information from Schwab
            raw_account_info = get_schwab_account_info(access_token)
            
            # If we got data successfully
            if raw_account_info:
                # Parse the raw data into a structured format
                schwab_data = parse_schwab_data(raw_account_info)
    
    # Check if we have IB data
    ib_data = None
    if "ib_connected" in st.session_state and st.session_state["ib_connected"]:
        # Display a spinner while loading
        with st.spinner("Loading Interactive Brokers data..."):
            # In a real app, you'd use the IB client to fetch data
            # For now, use the sample data function
            raw_ib_data = get_ib_account_data()
            
            # If we got data successfully
            if raw_ib_data:
                # Parse the raw data into a structured format
                ib_data = parse_ib_data(raw_ib_data)
    
    # Combine data from both brokerages if available
    if schwab_data or ib_data:
        # Combine the data into a single portfolio view
        combined_data = combine_portfolio_data(schwab_data, ib_data)
        
        # Let the user choose which view to display
        view_option = st.radio(
            "Select view:",
            ["All Accounts", "Schwab Only", "Interactive Brokers ISA Only"],
            horizontal=True
        )
        
        # Map the selected option to the view_type parameter
        view_mapping = {
            "All Accounts": "all",
            "Schwab Only": "schwab",
            "Interactive Brokers ISA Only": "ib_isa"
        }
        
        # Display the portfolio summary with the selected view type
        display_portfolio_summary(combined_data, view_mapping[view_option])
        
    else:
        # If no data is available, show instructions
        st.info("Please connect at least one brokerage account in the Authentication tab.")
        
        # Show example dashboard if user wants to see a preview
        if st.button("Show Example Dashboard"):
            display_example_dashboard()

# Settings tab
with tab3:
    st.header("Settings")
    
    # Data Refresh settings
    st.subheader("Data Refresh")
    
    # Add a slider for refresh interval
    # st.slider creates a slider control
    # Parameters:
    # - Label for the slider
    # - Minimum value
    # - Maximum value
    # - Default value
    refresh_interval = st.slider("Auto-refresh interval (minutes)", 0, 60, 15)
    
    # Display the selected setting
    st.info(f"Dashboard will auto-refresh every {refresh_interval} minutes. Set to 0 to disable auto-refresh.")
    
    # Display Settings
    st.subheader("Display Settings")
    
    # Add a dropdown for currency selection
    # st.selectbox creates a dropdown selector
    # Parameters:
    # - Label for the selector
    # - List of options
    # - index=0 sets the first option as the default
    currency = st.selectbox("Display Currency", ["USD", "GBP", "EUR", "JPY"], index=0)
    
    # Display the selected setting
    st.info(f"All values will be converted to {currency} using current exchange rates.")
    
    # Notifications settings
    st.subheader("Notifications")
    
    # Add a checkbox for enabling notifications
    # st.checkbox creates a checkbox control
    # Parameters:
    # - Label for the checkbox
    # - value=False sets the default state to unchecked
    enable_notifications = st.checkbox("Enable email notifications for significant changes", value=False)
    
    # If notifications are enabled, show additional options
    if enable_notifications:
        # Add a text input for email
        # st.text_input creates a text entry field
        email = st.text_input("Email address for notifications")
        
        # Add a slider for notification threshold
        threshold = st.slider("Notification threshold (%)", 1, 10, 5)
        
        # Display the selected setting
        st.info(f"You'll receive email notifications when portfolio value changes by {threshold}% or more.")

# Help tab
with tab4:
    st.header("Help & Information")
    
    # About section
    st.subheader("About This Dashboard")
    
    # Display information about the dashboard
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
    
    # API Connection Help section
    st.subheader("API Connection Help")
    
    # Create an expandable section for Schwab connection issues
    with st.expander("Charles Schwab Connection Issues"):
        # Display help information for Schwab connection
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
    
    # Create an expandable section for IB connection issues
    with st.expander("Interactive Brokers Connection Issues"):
        # Display help information for IB connection
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
    
    # Contact Support section
    st.subheader("Contact Support")
    
    # Display support contact information
    st.write("For assistance with this dashboard, please contact support at support@example.com.")
