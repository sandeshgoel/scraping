import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calculate_income_tax(income, previous_tax=0, previous_income=0):
    """Calculate the total income tax for a given salary in India as per the updated tax regime, including marginal tax relief."""
    tax = 0
    if income <= 400000:
        tax = 0
    elif income <= 800000:
        tax = (income - 400000) * 0.05
    elif income <= 1200000:
        tax = (400000 * 0.05) + (income - 800000) * 0.1
    elif income <= 1600000:
        tax = (400000 * 0.05) + (400000 * 0.1) + (income - 1200000) * 0.15
    elif income <= 2000000:
        tax = (400000 * 0.05) + (400000 * 0.1) + (400000 * 0.15) + (income - 1600000) * 0.2
    elif income <= 2400000:
        tax = (400000 * 0.05) + (400000 * 0.1) + (400000 * 0.15) + (400000 * 0.2) + (income - 2000000) * 0.25
    else:
        tax = (400000 * 0.05) + (400000 * 0.1) + (400000 * 0.15) + (400000 * 0.2) + (400000 * 0.25) + (income - 2400000) * 0.3
    
    # Full waiver of tax due on income up to 12 lacs
    if income <= 1200000:
        tax = 0
    
    # Surcharge application
    if income > 10000000:
        tax *= 1.15  # 15% surcharge for income > 1 crore
    elif income > 5000000:
        tax *= 1.10  # 10% surcharge for income > 50 lacs
    
    cess = tax * 0.04  # 4% Health and Education Cess
  
    final_tax = tax + cess
    # Ensure marginal tax relief so that after-tax income never decreases
    if income > 0 and income - final_tax < previous_income - previous_tax:
        final_tax = previous_tax + (income - previous_income)
    
    #if tax==previous_tax+1000: print(income)
    return final_tax, tax, cess

step = 1000
# Generate income and tax data up to 1.1 crore
income_values = np.arange(0, 55_00_001, step)
income_tax_values = []
tax_values = []
tax_relief_values = []
cess_values = []
previous_tax = 0
previous_income = 0
for income in income_values:
    final_tax, tax, cess = calculate_income_tax(income, previous_tax, previous_income)
    income_tax_values.append(final_tax)
    tax_values.append(tax)
    tax_relief_values.append(tax + cess - final_tax)
    cess_values.append(cess)
    previous_tax = final_tax
    previous_income = income

df = pd.DataFrame({'Income': income_values, 'Tax': tax_values, 'Cess': cess_values, 'Relief': tax_relief_values, 'Income Tax': income_tax_values})
df['Additional Tax'] = df['Income Tax'].diff()
df.to_excel('income_tax.xlsx', index=False)

# Plot income vs income tax
plt.figure(figsize=(10, 5))
plt.plot(df['Income'] / 1_00_000, df['Income Tax'] / 1_00_000, label='Income Tax', color='blue')
plt.xlabel('Income (INR in Lacs)')
plt.ylabel('Income Tax (INR in Lacs)')
plt.title('Income vs Income Tax')
plt.legend()
plt.grid()
plt.show()

# Calculate additional tax as a percentage for each additional 1000 INR of income
additional_income = df['Income'][1:]
additional_tax = df['Income Tax'].diff().dropna()
additional_tax_percentage = (additional_tax / step) * 100  # Convert to percentage

# Plot additional income vs additional tax percentage
plt.figure(figsize=(10, 5))
plt.plot(additional_income / 1_00_000, additional_tax_percentage, label=f'Additional Tax (%) per {step} INR', color='red')
plt.xlabel('Income (INR in Lacs)')
plt.ylabel('Tax Rate on Incremental Income (%)')
plt.title(f'Tax Percentage for Each Additional {step} INR of Income')
plt.legend()
plt.grid()
plt.show()
