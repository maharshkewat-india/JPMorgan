import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

# ==========================================
# 1. Generate Synthetic Loan Data 
# (Mirroring the risk manager's dataset)
# ==========================================
np.random.seed(42)
n_samples = 5000

data = pd.DataFrame({
    'income': np.random.normal(65000, 20000, n_samples).clip(20000, 250000),
    'total_loans_outstanding': np.random.normal(30000, 15000, n_samples).clip(0, 150000),
    'credit_history_length_yrs': np.random.uniform(1, 20, n_samples),
    'loan_amount': np.random.normal(15000, 8000, n_samples).clip(1000, 50000)
})

# Engineer the 'default' target variable (introducing non-linear risk)
# Higher loans relative to income + shorter credit history = higher risk
risk_score = (data['total_loans_outstanding'] / data['income']) - (data['credit_history_length_yrs'] * 0.05)
probability = 1 / (1 + np.exp(-risk_score)) # Sigmoid function
data['has_previously_defaulted'] = (np.random.rand(n_samples) < probability).astype(int)

# ==========================================
# 2. Model Training and Comparative Analysis
# ==========================================
# Features and Target
features = ['income', 'total_loans_outstanding', 'credit_history_length_yrs']
X = data[features]
y = data['has_previously_defaulted']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features (Critical for Logistic Regression)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Model A: Logistic Regression (Baseline)
log_reg = LogisticRegression()
log_reg.fit(X_train_scaled, y_train)
log_reg_preds = log_reg.predict_proba(X_test_scaled)[:, 1]

# Model B: Random Forest (Advanced)
rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
rf_model.fit(X_train, y_train) # Tree models don't strictly require scaling
rf_preds = rf_model.predict_proba(X_test)[:, 1]

print("--- Comparative Analysis: Model Performance (ROC-AUC) ---")
print(f"Logistic Regression AUC: {roc_auc_score(y_test, log_reg_preds):.4f}")
print(f"Random Forest AUC:       {roc_auc_score(y_test, rf_preds):.4f}")
print("Note: The Random Forest typically performs better on complex datasets with non-linear feature interactions.\n")

# We will select the Random Forest for the final expected loss function
selected_model = rf_model

# ==========================================
# 3. Expected Loss Inference Function
# ==========================================
def calculate_expected_loss(loan_properties, model, recovery_rate=0.10):
    """
    Calculates the expected loss of a loan given borrower properties.
    
    Parameters:
    - loan_properties (dict): A dictionary containing borrower metrics.
      Example: {'income': 50000, 'total_loans_outstanding': 20000, 
                'credit_history_length_yrs': 5, 'loan_amount': 10000}
    - model: The trained predictive model (must have .predict_proba() method).
    - recovery_rate (float): The expected recovery rate on the loan (default 10%).
    
    Returns:
    - float: The expected loss in dollars.
    """
    # Extract features expected by the model
    # Note: Must be in the exact same order as the training data
    input_data = pd.DataFrame([{
        'income': loan_properties['income'],
        'total_loans_outstanding': loan_properties['total_loans_outstanding'],
        'credit_history_length_yrs': loan_properties['credit_history_length_yrs']
    }])
    
    # 1. Calculate Probability of Default (PD)
    pd_estimate = model.predict_proba(input_data)[0, 1]
    
    # 2. Calculate Loss Given Default (LGD)
    lgd = 1.0 - recovery_rate
    
    # 3. Calculate Expected Loss (EL)
    expected_loss = pd_estimate * lgd * loan_properties['loan_amount']
    
    print(f"--- Loan Assessment ---")
    print(f"Estimated PD:   {pd_estimate * 100:.2f}%")
    print(f"Exposure (EAD): ${loan_properties['loan_amount']:,.2f}")
    print(f"Expected Loss:  ${expected_loss:,.2f}")
    
    return expected_loss

# ==========================================
# 4. Test the Function
# ==========================================
new_loan_application = {
    'income': 45000,
    'total_loans_outstanding': 35000, # High debt relative to income
    'credit_history_length_yrs': 3,   # Short credit history
    'loan_amount': 15000              # New requested loan
}

el_result = calculate_expected_loss(new_loan_application, selected_model)