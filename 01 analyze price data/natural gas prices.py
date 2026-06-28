from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

try:
    from sklearn.linear_model import LinearRegression
except ImportError:
    class LinearRegression:
        def __init__(self):
            self.coef_ = None
            self.intercept_ = None

        def fit(self, X, y):
            X_mat = np.asarray(X)
            y_vec = np.asarray(y)
            if X_mat.ndim == 1:
                X_mat = X_mat.reshape(-1, 1)
            ones = np.ones((X_mat.shape[0], 1))
            X_design = np.hstack([ones, X_mat])
            coef, *_ = np.linalg.lstsq(X_design, y_vec, rcond=None)
            self.intercept_ = coef[0]
            self.coef_ = coef[1:]
            return self

        def predict(self, X):
            X_mat = np.asarray(X)
            if X_mat.ndim == 1:
                X_mat = X_mat.reshape(-1, 1)
            return self.intercept_ + X_mat.dot(self.coef_)

# 1. Load the data
# Resolve the CSV path relative to this script so it works from any current working directory.
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / 'Nat_Gas.csv'

df = pd.read_csv(CSV_PATH)
df['Dates'] = pd.to_datetime(df['Dates'])
df = df.sort_values('Dates')

# 2. Prepare features for the model
# We use the number of days since the earliest date as the time variable
start_date = df['Dates'].min()
df['Days'] = (df['Dates'] - start_date).dt.days

# To capture the seasonal pattern, we use sine and cosine transformations.
# Dividing by 365.25 captures the annual cyclical nature of the prices perfectly.
df['Sin'] = np.sin(2 * np.pi * df['Days'] / 365.25)
df['Cos'] = np.cos(2 * np.pi * df['Days'] / 365.25)

X = df[['Days', 'Sin', 'Cos']]
y = df['Prices']

# 3. Fit a Linear Regression model
model = LinearRegression()
model.fit(X, y)

# 4. Define the estimation function
def estimate_price(date_input):
    """
    Estimates the natural gas price for a given date in the past or future.
    date_input: str or datetime object (e.g., '2023-05-15')
    """
    if isinstance(date_input, str):
        target_date = pd.to_datetime(date_input)
    else:
        target_date = date_input

    days_since_start = (target_date - start_date).days

    # Calculate seasonal features for the target date
    sin_val = np.sin(2 * np.pi * days_since_start / 365.25)
    cos_val = np.cos(2 * np.pi * days_since_start / 365.25)

    # Structure features for the model
    features = pd.DataFrame({
        'Days': [days_since_start],
        'Sin': [sin_val],
        'Cos': [cos_val]
    })

    # Return the predicted price
    price_estimate = model.predict(features)[0]
    return price_estimate


if __name__ == '__main__':
    # --- Testing the Function ---
    print(f"Estimated price on mid-month past date (2022-01-15): {estimate_price('2022-01-15'):.2f}")
    print(f"Estimated price one year into the future (2025-01-15): {estimate_price('2025-01-15'):.2f}")

    # 5. Visualization for finding patterns
    # Extrapolate for one year beyond the maximum historical date
    future_dates = pd.date_range(
        start=df['Dates'].max(),
        end=df['Dates'].max() + pd.DateOffset(years=1),
        freq='ME'  # Month End frequency
    )

    # Create a sequence of continuous dates for a smooth curve
    smooth_dates = pd.date_range(start=start_date, end=future_dates.max(), freq='D')
    smooth_prices = [estimate_price(d) for d in smooth_dates]

    plt.figure(figsize=(12, 6))
    plt.plot(df['Dates'], df['Prices'], marker='o', label='Historical Monthly Data', color='blue')
    plt.plot(smooth_dates, smooth_prices, label='Modeled Price Curve', linestyle='--', color='orange')

    # Mark where historical data ends and extrapolation begins
    plt.axvline(x=df['Dates'].max(), color='red', linestyle=':', label='End of Historical Data')

    plt.title('Natural Gas Prices: Historical Data and 1-Year Forecast')
    plt.xlabel('Date')
    plt.ylabel('Price in USD')
    plt.legend()
    plt.grid(True, alpha=0.5)
    plt.tight_layout()
    plt.show()