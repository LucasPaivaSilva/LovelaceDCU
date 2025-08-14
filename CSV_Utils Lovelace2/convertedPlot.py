import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# Load the decoded CSV log
df = pd.read_csv("acceleration_26_06.csv")

# As per user feedback, swap the data for the power columns as they might be inverted at the source.
if 'Motor_Output_Power' in df.columns and 'Inverter_Output_Power' in df.columns:
    df['Motor_Output_Power'], df['Inverter_Output_Power'] = (
        df['Inverter_Output_Power'].copy(), df['Motor_Output_Power'].copy()
    )

# Convert 'Time' to seconds if needed (if it's already in seconds like 0.100552, no need)
df['Time'] = df['Time'] * 1000

# Define plot time range (in milliseconds)
use_time_limits = False  # set to False to disable time range limit
time_start = 146   # adjust as needed
time_end = 156  # adjust as needed

# Plot grid layout: 3 columns x 2 rows
fig, axs = plt.subplots(2, 3, figsize=(16, 10))
axs = axs.flatten()
time_mask = (df['Time'] >= time_start) & (df['Time'] <= time_end)

# --- Define pretty labels for signals ---
signal_labels = {
    'Motor_Output_Power': 'Motor Output Power (W)',
    'Inverter_Output_Power': 'Inverter Output Power (W)'
}

# Plot 1: Powers
ax = axs[0]
for signal in ['Motor_Output_Power', 'Inverter_Output_Power']:
    if signal in df.columns:
        mask = df[signal].notna()
        if use_time_limits:
            mask &= time_mask
        if mask.any():
            ax.plot(df['Time'][mask], df[signal][mask], label=signal_labels.get(signal, signal))
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.set_title("Power Signals")
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Power (W)")
ax.legend()
ax.grid(True)

# Plot 2: Temperatures
ax = axs[1]
for signal in ['Motor_Temp', 'Inverter_Temp']:
    if signal in df.columns:
        mask = df[signal].notna()
        if use_time_limits:
            mask &= time_mask
        if mask.any():
            ax.plot(df['Time'][mask], df[signal][mask], label=signal)
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.set_title("Temperatures")
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Temperature (°C)")
ax.legend()
ax.grid(True)

# Plot 3: HV and BMS Current
ax = axs[2]
if 'HV_Current' in df.columns:
    mask_current = df['HV_Current'].notna()
    if use_time_limits:
        mask_current &= time_mask
    if mask_current.any():
        ax.plot(df['Time'][mask_current], df['HV_Current'][mask_current], 'b-', label='HV_Current')
if 'BMS_Current' in df.columns:
    mask_bms_current = df['BMS_Current'].notna()
    if use_time_limits:
        mask_bms_current &= time_mask
    if mask_bms_current.any():
        ax.plot(df['Time'][mask_bms_current], df['BMS_Current'][mask_bms_current], 'g-', label='BMS_Current')
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.set_title("HV and BMS Current")
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Current")
ax.legend()
ax.grid(True)

# Plot 4: HV and BMS Voltage
ax = axs[3]
if 'HV_Voltage' in df.columns:
    mask_voltage = df['HV_Voltage'].notna()
    if use_time_limits:
        mask_voltage &= time_mask
    if mask_voltage.any():
        ax.plot(df['Time'][mask_voltage], df['HV_Voltage'][mask_voltage], 'r--', label='HV_Voltage')
if 'BMS_Voltage' in df.columns:
    mask_bms_voltage = df['BMS_Voltage'].notna()
    if use_time_limits:
        mask_bms_voltage &= time_mask
    if mask_bms_voltage.any():
        ax.plot(df['Time'][mask_bms_voltage], df['BMS_Voltage'][mask_bms_voltage], 'm-', label='BMS_Voltage')
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.set_title("HV and BMS Voltage")
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Voltage")
ax.legend()
ax.grid(True)


# Plot 5: APPS and BPPS (left) + RTD (right)
ax = axs[4]
# Left axis: APPS and BPPS
lines = []
labels = []
if 'APPS' in df.columns:
    mask_apps = df['APPS'].notna()
    if use_time_limits:
        mask_apps &= time_mask
    if mask_apps.any():
        l, = ax.plot(df['Time'][mask_apps], df['APPS'][mask_apps], 'c-', label='APPS')
        lines.append(l)
        labels.append('APPS')
if 'BPPS' in df.columns:
    mask_bpps = df['BPPS'].notna()
    if use_time_limits:
        mask_bpps &= time_mask
    if mask_bpps.any():
        l, = ax.plot(df['Time'][mask_bpps], df['BPPS'][mask_bpps], 'y-', label='BPPS')
        lines.append(l)
        labels.append('BPPS')
ax.set_ylabel("Pedal Position (%)")
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.set_xlabel("Time (ms)")
ax.grid(True)
ax.set_title("Pedal Positions and RTD")

# Right axis for RTD
ax_rtd = ax.twinx()
lines2 = []
labels2 = []
if 'RTD' in df.columns:
    mask_rtd = df['RTD'].notna()
    if use_time_limits:
        mask_rtd &= time_mask
    if mask_rtd.any():
        l2, = ax_rtd.plot(df['Time'][mask_rtd], df['RTD'][mask_rtd], 'k--', label='RTD')
        lines2.append(l2)
        labels2.append('RTD')
ax_rtd.set_ylabel("RTD State")
ax_rtd.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))

# Combine legends
if lines or lines2:
    ax.legend(lines + lines2, labels + labels2, loc='upper right')


#
#
# Plot 6: RPM and Speed (shared axis, left) and Inverter_motor_torque (right)
ax = axs[5]
# Left axis: RPM
lines = []
labels = []

# Right axis for Inverter_motor_torque
ax_torque = ax.twinx()
lines2 = []
labels2 = []

if 'Inverter_motor_rpm' in df.columns:
    mask_rpm = df['Inverter_motor_rpm'].notna()
    if use_time_limits:
        mask_rpm &= time_mask
    if mask_rpm.any():
        l, = ax.plot(df['Time'][mask_rpm], df['Inverter_motor_rpm'][mask_rpm], 'b-', label='RPM')
        lines.append(l)
        labels.append('RPM')
ax.set_ylabel("RPM / Speed (km/h)")
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.set_xlabel("Time (ms)")
ax.grid(True)
ax.set_title("RPM and Speed")

if 'Inverter_motor_torque' in df.columns:
    mask_torque = df['Inverter_motor_torque'].notna()
    if use_time_limits:
        mask_torque &= time_mask
    if mask_torque.any():
        l2, = ax_torque.plot(df['Time'][mask_torque], df['Inverter_motor_torque'][mask_torque], 'g--', label='Torque')
        lines2.append(l2)
        labels2.append('Torque')
ax_torque.set_ylabel("Torque (Nm)")
ax_torque.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))

# Configure combined RPM and Speed tick labels and align axis limits
if 'Inverter_motor_rpm' in df.columns and 'mask_rpm' in locals() and mask_rpm.any():
    max_rpm = df['Inverter_motor_rpm'][mask_rpm].max() * 1.1
    ax.set_ylim(bottom=0, top=max_rpm)
    #ax_torque.set_ylim(bottom=0)  # só fixa o zero, e deixa o topo automático
    ticks = ax.get_yticks()
    ax.set_yticks(ticks)
    speed_labels = [str(int(t * 0.0196)) for t in ticks]
    combined_labels = [f"{int(rpm)}\n{speed}" for rpm, speed in zip(ticks, speed_labels)]
    ax.set_yticklabels(combined_labels)

# Combine all legends
if lines or lines2:
    ax.legend(lines + lines2, labels + labels2, loc='upper right')

plt.tight_layout()

# --- Second Plot Group: Power, Speed, and Torque ---
# This plot group shows data from the selected time frame, but with the
# time axis starting from 0.

# Filter data for this plot group based on the time limits
if use_time_limits:
    plot2_df = df[time_mask].copy()
else:
    plot2_df = df.copy()

# Normalize time for this specific plot to start from 0, if there's data
if not plot2_df.empty:
    plot2_df['Time_normalized'] = plot2_df['Time'] - plot2_df['Time'].min()
else:
    # Handle case where the time window has no data
    plot2_df['Time_normalized'] = pd.Series(dtype='float64')

# Create a new figure for the second plot group
fig2, axs2 = plt.subplots(2, 1, figsize=(8, 10))

# Plot 1: Power
ax_power = axs2[0]
for signal in ['Motor_Output_Power', 'Inverter_Output_Power']:
    if signal in plot2_df.columns:
        mask = plot2_df[signal].notna()
        if mask.any():
            ax_power.plot(plot2_df['Time_normalized'][mask], plot2_df[signal][mask], label=signal_labels.get(signal, signal))
ax_power.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax_power.set_xlabel("System Time (s)")
ax_power.set_ylabel("Power (W)")
ax_power.legend()
ax_power.grid(True)

# Plot 2: Speed and Torque
ax_speed = axs2[1]
ax_torque = ax_speed.twinx()

# Calculate Speed if not present
if 'Inverter_motor_rpm' in plot2_df.columns and 'Speed' not in plot2_df.columns:
    plot2_df['Speed'] = plot2_df['Inverter_motor_rpm'] * 0.0196

# Plot Speed
lines, labels = [], []
if 'Speed' in plot2_df.columns:
    mask_speed = plot2_df['Speed'].notna()
    if mask_speed.any():
        l, = ax_speed.plot(plot2_df['Time_normalized'][mask_speed], plot2_df['Speed'][mask_speed], 'b-', label='Speed (km/h)')
        lines.append(l)
        labels.append('Speed (km/h)')
ax_speed.set_xlabel("System Time (s)")
ax_speed.set_ylabel("Speed (km/h)")
ax_speed.tick_params(axis='y')
ax_speed.grid(True) # Grid for the primary y-axis

# Plot Torque
if 'Inverter_motor_torque' in plot2_df.columns:
    mask_torque = plot2_df['Inverter_motor_torque'].notna()
    if mask_torque.any():
        l, = ax_torque.plot(plot2_df['Time_normalized'][mask_torque], plot2_df['Inverter_motor_torque'][mask_torque], 'g--', label='Torque (Nm)')
        lines.append(l)
        labels.append('Torque (Nm)')
ax_torque.set_ylabel("Torque (Nm)")
ax_torque.tick_params(axis='y')
ax_torque.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))

ax_speed.legend(lines, labels, loc='upper left')

# Adjust layout for the second figure
fig2.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust for suptitle

# --- Third Plot: Inverter Temperature and Power ---
# A dedicated plot for Inverter Temperature and Power analysis within the selected time window.

fig3, ax_inv_temp = plt.subplots(figsize=(8, 5))

lines, labels = [], []

# Plot Inverter Temperature on the primary y-axis
signal = 'Inverter_Temp'
if signal in plot2_df.columns:
    mask = plot2_df[signal].notna()
    if mask.any():
        l, = ax_inv_temp.plot(plot2_df['Time_normalized'][mask], plot2_df[signal][mask], color='C0', label='Inverter Temperature')
        lines.append(l)
        labels.append('Inverter Temperature')
        ax_inv_temp.set_xlabel("System Time (s)")
        ax_inv_temp.set_ylabel("Temperature (°C)")
        ax_inv_temp.tick_params(axis='y')
        ax_inv_temp.grid(True)
    else:
        ax_inv_temp.text(0.5, 0.5, f'No data for {signal} in the selected time frame.',
                         horizontalalignment='center', verticalalignment='center', transform=ax_inv_temp.transAxes)
else:
    ax_inv_temp.text(0.5, 0.5, f'{signal} column not found in data.',
                     horizontalalignment='center', verticalalignment='center', transform=ax_inv_temp.transAxes)

# Create a second y-axis for Inverter Power
ax_inv_power = ax_inv_temp.twinx()
power_signal = 'Inverter_Output_Power'
if power_signal in plot2_df.columns:
    mask_power = plot2_df[power_signal].notna()
    if mask_power.any():
        power_label = signal_labels.get(power_signal, power_signal)
        l, = ax_inv_power.plot(plot2_df['Time_normalized'][mask_power], plot2_df[power_signal][mask_power], color='C1', label=power_label)
        lines.append(l)
        labels.append(power_label)
        ax_inv_power.set_ylabel("Power (W)")
        ax_inv_power.tick_params(axis='y')
        ax_inv_power.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))

# Add combined legend
if lines:
    ax_inv_temp.legend(lines, labels, loc='upper right')

ax_inv_temp.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
fig3.tight_layout(rect=[0, 0.03, 1, 0.95])

plt.show()