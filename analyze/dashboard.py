import pandas as pd
import glob
import os

def get_latest_report():
    """Find the latest report file in the REPORTS directory."""
    files = glob.glob('REPORTS/report-*.xlsx')
    if not files:
        return None
    # Sort files by name to get the latest based on the date in the filename
    files.sort(reverse=True)
    return files[0]

def import_trends():
    """Import the table in Trends sheet from the latest report."""
    latest_file = get_latest_report()
    if not latest_file:
        print("No report files found in REPORTS directory.")
        return None
    
    print(f"Loading latest report: {latest_file}")
    
    try:
        # Read the 'Trends' sheet
        # The Trends sheet usually has the main table starting at row 28 (skip 27)
        # We only need the first 8 columns
        df = pd.read_excel(latest_file, sheet_name='Trends', skiprows=27, usecols="A:H")
        
        # Stop at the first empty row (to only get the first table)
        # We find the first row that is all NaN
        empty_row_idx = df.isnull().all(axis=1).idxmax() if df.isnull().all(axis=1).any() else len(df)
        df = df.iloc[:empty_row_idx]
        
        # Clean up: Remove completely empty columns and rows
        df = df.dropna(axis=1, how='all')
        df = df.dropna(axis=0, how='all')
        
        # Ensure the 'Date' column is in datetime format if it exists
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            # Drop rows where Date could not be parsed
            df = df.dropna(subset=['Date'])
            
        return df
    except Exception as e:
        print(f"Error reading Trends sheet: {e}")
        return None

def calculate_performance(df):
    """Calculate absolute and percentage increase for the last 7 columns over multiple periods."""
    if df is None or df.empty:
        return None
    
    # Sort by date ascending to make calculations easier
    df = df.sort_values('Date').reset_index(drop=True)
    latest_date = df['Date'].max()
    latest_values = df.iloc[-1]
    
    # Columns to calculate for (last 7 columns, excluding Date)
    cols = [c for c in df.columns if c != 'Date']
    
    periods = {
        '1 Month': latest_date - pd.DateOffset(months=1),
        '3 Months': latest_date - pd.DateOffset(months=3),
        '6 Months': latest_date - pd.DateOffset(months=6),
        '1 Year': latest_date - pd.DateOffset(years=1),
        '2 Years': latest_date - pd.DateOffset(years=2),
        '3 Years': latest_date - pd.DateOffset(years=3)
    }
    
    performance_results = []
    
    for period_name, target_date in periods.items():
        # Find the row with the date closest to target_date (not after)
        past_data = df[df['Date'] <= target_date]
        if past_data.empty:
            continue
            
        past_row = past_data.iloc[-1]
        past_date_actual = past_row['Date']
        
        for col in cols:
            current_val = latest_values[col]
            past_val = past_row[col]
            
            abs_change = current_val - past_val
            pct_change = (abs_change / past_val * 100) if past_val != 0 else 0
            
            performance_results.append({
                'Period': period_name,
                'Category': col,
                'Current Value': current_val,
                'Past Value': past_val,
                'Abs Change': abs_change,
                'Pct Change': pct_change,
                'As Of': past_date_actual.strftime('%Y-%m-%d')
            })
            
    return pd.DataFrame(performance_results)

if __name__ == "__main__":
    df_trends = import_trends()
    if df_trends is not None:
        print("\nTrends Table imported successfully.")
        
        perf_df = calculate_performance(df_trends)
        if perf_df is not None:
            # Pivot the data to show Absolute Change
            print("\n" + "="*80)
            print("ABSOLUTE INCREASE (in Lacs)")
            print("="*80)
            abs_pivot = perf_df.pivot(index='Period', columns='Category', values='Abs Change')
            # Reorder rows to maintain logical sequence
            period_order = ['1 Month', '3 Months', '6 Months', '1 Year', '2 Years', '3 Years']
            abs_pivot = abs_pivot.reindex(period_order).dropna(how='all')
            # Reorder columns to match original (Total first usually)
            cols_order = [c for c in df_trends.columns if c != 'Date']
            abs_pivot = abs_pivot[cols_order]
            print(abs_pivot.to_string(float_format=lambda x: "{:,.2f}".format(x)))
            
            print("\n" + "="*80)
            print("PERCENTAGE INCREASE (%)")
            print("="*80)
            pct_pivot = perf_df.pivot(index='Period', columns='Category', values='Pct Change')
            pct_pivot = pct_pivot.reindex(period_order).dropna(how='all')
            pct_pivot = pct_pivot[cols_order]
            print(pct_pivot.to_string(float_format=lambda x: "{:,.1f}%".format(x)))
            print("="*80)
        else:
            print("Could not calculate performance metrics.")
    else:
        print("Failed to import Trends table.")
