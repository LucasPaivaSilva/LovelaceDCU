import pandas as pd

# Load your CSV
df = pd.read_csv("acceleration_26_06/lovelace2-2606_part_15.csv")

# Normalize timestamps to start at 0
start_time = df['tempoDoSistema'].min()
df['tempoDoSistema'] = df['tempoDoSistema'] - start_time

# Convert to GVRET CSV log DataFrame
out_df = pd.DataFrame({
    'Type': 1,
    'ID': df['msgId'].apply(lambda x: f"0x{x.lstrip('0') or '0'}"),
    'TimeStamp': (df['tempoDoSistema'] / 1000.0).astype(float),  # convert to seconds
    'Bus': 0,
    'Len': df['DLC']
})

# Add data columns
for i in range(8):
    out_df[f'Data{i}'] = df[f'data{i}']

# Save as GVRET CSV log
out_df.to_csv("lovelace2-2606_part_15_GVRET.csv", index=False)

print("GVRET CSV log generated successfully.")