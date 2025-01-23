import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Read the CSV file
csv_file = 'sizes.csv'
df = pd.read_csv(csv_file)
# Step 2: Extract the median times
# Assuming the CSV has columns: 'Benchmark', 'Implementation', 'MedianTime'

for metric in ("text", "data", "bss", "rss"):
    res = df.pivot(index='Benchmark', columns='Target', values=metric)
    res = res.divide(1000)
    
    
    normalized_res = res.div(res['lf-c'], axis=0)
    res.plot(kind='bar', figsize=(10, 6), logy=True)
    plt.title(f'Segment size: {metric}')
    plt.xlabel('Benchmark')
    plt.xticks(rotation=15)
    plt.ylabel('Size [KB]')
    plt.legend(title='Target')
    plt.tight_layout()
    plt.savefig(f"results/{metric}.png")