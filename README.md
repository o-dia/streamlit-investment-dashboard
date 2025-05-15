# Investment Portfolio Dashboard

A Streamlit-based dashboard that provides a holistic view of investments. 
I created this because I have to check my different investment accounts separately, on my phone, 
but I increasingly want to load ONE app where I view everything together and I can understand and track
how my investments are doing. I have integrated with Charles Schwab and Interactive Brokers, but you can use 
this framework to add more portfolios and it should work all the same - you just need to authenticate with
the relevant brokerage and make sure their APIs support what you need.

## Features

- **Portfolio Overview**: View total portfolio value and performance across all accounts
- **Multi-Broker Support**: Integrate with both Charles Schwab and Interactive Brokers
- **Flexible Views**: Filter by broker or account type
- **Asset Allocation**: Visualize portfolio allocation by security
- **Performance Metrics**: Track unrealized P/L, returns, and more

## Screenshots

[Coming soon]

## Requirements

- Python 3.8+
- Streamlit
- ngrok (for OAuth authentication)
- API credentials for Charles Schwab and/or Interactive Brokers

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/o-dia/streamlit-investment-dashboard.git
   cd streamlit-investment-dashboard
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your credentials:
   ```
   SCHWAB_CLIENT_ID=your_client_id_here
   SCHWAB_CLIENT_SECRET=your_client_secret_here
   SCHWAB_REDIRECT_URI=your_ngrok_url_here/callback
   
   # For Interactive Brokers (optional)
   IB_CLIENT_ID=your_ib_client_id
   IB_GATEWAY_PORT=4001
   IB_HOST=127.0.0.1
   ```

## Usage

1. Start ngrok to create a tunnel for OAuth:
   ```
   ngrok http 8501
   ```

2. Update your `.env` file with the ngrok URL

3. Run the app:
   ```
   streamlit run app.py
   ```

4. Open your browser to http://localhost:8501

5. Navigate to the Authentication tab to connect your brokerage accounts

## Development Status

This project is currently in development. Authentication with Charles Schwab API is pending resolution.

## Technologies Used

- Python
- Streamlit
- Plotly
- Pandas
- OAuth for API authentication