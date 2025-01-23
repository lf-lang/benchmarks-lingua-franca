import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Read the CSV file
csv_file = 'res1.csv'
df = pd.read_csv(csv_file)
df = df[df['target'] != 'lf-ts']
# Step 2: Extract the median times
# Assuming the CSV has columns: 'Benchmark', 'Implementation', 'MedianTime'
median_times = df.pivot(index='benchmark', columns='target', values='median_time_ms')

median_times.divide
print(median_times)
print(median_times['lf-c'])
# Step 3: Normalize the results
# Normalize to the first benchmark (you can change this to any benchmark you want)
normalized_times = median_times.div(median_times['lf-c'], axis=0)

print(normalized_times)

# Step 4: Plot the bar chart
normalized_times.plot(kind='bar', figsize=(10, 6))
plt.title('Normalized Benchmark Results')
plt.xlabel('Benchmark')
plt.xticks(rotation=15)
plt.ylabel('Normalized Median Time')
plt.legend(title='Target')
plt.tight_layout()
plt.savefig('results/performance.png')