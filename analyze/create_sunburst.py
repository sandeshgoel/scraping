import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import sys
import os

def get_text_points(center, radius, angle):
    """Calculate the position for text labels"""
    rad = np.radians(angle)
    x = center[0] + radius * np.cos(rad)
    y = center[1] + radius * np.sin(rad)
    return x, y

def create_sunburst(data, title='', filename='', show=False):
    """
    Create a sunburst chart with Col3 as outer ring and Col1 as inner ring
    """
    #print(data)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data, columns=['Col1', 'Col2', 'Col3', 'Percent'])
    
    if 'Percent' not in data.columns:
        if 'Value' not in data.columns:
            print('Value column not found!!')
            sys.exit(1)
        else:
            total = data['Value'].sum()
            data['Percent'] = data['Value'] * 100/total
        
    fig, ax = plt.subplots(figsize=(15, 15))
    ax.set_title(title, pad=20, fontdict={'fontsize': 20, 'weight': 'bold'})
    
    total = data['Percent'].sum()
    if total != 100:
        print(f'WARNING: Total {total} does not equal 100!!')
        
    colors_inner = plt.cm.Pastel2(np.linspace(0, 1, len(data['Col1'].unique())+1))
    # colors_middle = plt.cm.Set2(np.linspace(0, 1, len(data['Col2'].unique())))
    # colors_outer = plt.cm.Set1(np.linspace(0, 1, len(data['Col3'].unique())))
    
    # Start with Col1s (inner ring)
    Col1_groups = data.groupby('Col1')['Percent'].sum().sort_values(ascending=False)
    start_angle = 90
    
    fontdict = {'fontsize': 12, 'weight': 'bold' }
    
    for i, (Col1, sales) in enumerate(Col1_groups.items()):
        angle = (sales / total) * 360
        end_angle = start_angle - angle
        mid_angle = (start_angle + end_angle) / 2
        
        color = colors_inner[i]
        # Create Col1 wedge (inner)
        wedge = plt.matplotlib.patches.Wedge(
            center=(0, 0),
            r=1.0,
            theta1=end_angle,
            theta2=start_angle,
            width=0.8,
            color=color,
            ec='white', lw=3
        )
        ax.add_patch(wedge)
        
        # Add Col1 label
        x, y = get_text_points((0, 0), 0.6, mid_angle)
        plt.text(x, y, f"{Col1} {sales:,.0f}", 
                ha='center', va='center', fontdict=fontdict,
                rotation=mid_angle)# - 90 if mid_angle > 90 and mid_angle < 270 else mid_angle + 90)
        
        # Plot categories (middle ring)
        Col1_data = data[data['Col1'] == Col1]
        Col2_groups = Col1_data.groupby('Col2')['Percent'].sum()
        cat_start = start_angle
        
        for j, (Col2, cat_sales) in enumerate(Col2_groups.items()):
            cat_angle = (cat_sales / total) * 360
            cat_end = cat_start - cat_angle
            cat_mid = (cat_start + cat_end) / 2
            
            wedge = plt.matplotlib.patches.Wedge(
                center=(0, 0),
                r=2.0,
                theta1=cat_end,
                theta2=cat_start,
                width=0.95,
                color=color,#colors_middle[j],
                ec='white', lw=3
            )
            ax.add_patch(wedge)
            
            # Add Col2 label
            x, y = get_text_points((0, 0), 1.6, cat_mid)
            plt.text(x, y, f"{Col2} {cat_sales:,.0f}", 
                    ha='center', va='center', fontdict=fontdict,
                    rotation=cat_mid)# - 90 if cat_mid > 90 and cat_mid < 270 else cat_mid + 90)
            
            # Plot Col3s (outer ring)
            Col3_data = Col1_data[Col1_data['Col2'] == Col2]
            prod_start = cat_start
            
            for k, row in Col3_data.iterrows():
                prod_angle = (row['Percent'] / total) * 360
                prod_end = prod_start - prod_angle
                prod_mid = (prod_start + prod_end) / 2
                
                wedge = plt.matplotlib.patches.Wedge(
                    center=(0, 0),
                    r=3.0,
                    theta1=prod_end,
                    theta2=prod_start,
                    width=0.95,
                    color=color,#colors_outer[k % len(colors_outer)],
                    ec='white', lw=3
                )
                ax.add_patch(wedge)
                
                if row['Percent'] >= 0.6:
                    # Add Col3 label
                    x, y = get_text_points((0, 0), 2.6, prod_mid)
                    plt.text(x, y, f"{row['Col3']} {row['Percent']:,.0f}", 
                            ha='center', va='center', fontdict=fontdict,
                            rotation=prod_mid)# - 90 if prod_mid > 90 and prod_mid < 270 else prod_mid + 90)
                
                prod_start = prod_end
            
            cat_start = cat_end
        start_angle = end_angle
    
    # Configure plot
    ax.set_aspect('equal')
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_axis_off()
    
    # Save plot
    if filename != '':
        plt.savefig(filename, bbox_inches='tight', dpi=300, pad_inches=0.1)
        print(f"Sunburst chart has been saved as {filename}")

    # Save the figure to a bytes buffer
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png')

    if show: plt.show()
    plt.close() 

    return img_buffer

def is_excel_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ['.xls', '.xlsx', '.xlsm', '.xlsb']

# Example usage
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if not is_excel_file(sys.argv[1]):
            print("Usage: python create_sunburst.py <excel_file>")
            sys.exit(1)
            
        data = pd.read_excel(sys.argv[1])
        data = data.dropna(how='all')
        data.rename(columns={'Type': 'Col1', 'Subtype': 'Col2', 'Category': 'Col3'}, inplace=True)   
    else:
        data = [
            ['Debt', 'A', 'G', 10],
            ['Debt', 'B', 'H', 10],
            ['Equity', 'E', 'I', 10],
            ['Equity', 'F', 'J', 10],
            ['Gold', 'C', 'K', 10],
            ['Global', 'D', 'L', 50],
        ]
    
    create_sunburst(data, title='Asset Allocation', show=True)
