import pandas as pd
import matplotlib.pyplot as plt

# Carregar o arquivo CSV
file_path = 'lovelace1707-ufsc_part_5.csv'
df = pd.read_csv(file_path)

# Converter colunas de dados para inteiros
for col in ['data0', 'data1', 'data2', 'data3', 'data4', 'data5', 'data6', 'data7']:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# Adicionar colunas para os valores extraídos
df['accel_value'] = 0
df['brake_value'] = 0
df['regen_brake_flag'] = 0
df['rtd_flag'] = 0
df['mode'] = 0
df['generic_flag'] = 0
df['DCL_value'] = 0
df['CCL_value'] = 0
df['battery_pack_value'] = 0
df['hv_voltage'] = 0.0
df['motor_current'] = 0.0
df['motor_temp'] = 0.0
df['controller_temp'] = 0.0
df['motor_torque'] = 0.0
df['motor_power_out'] = 0.0
df['motor_power_in'] = 0.0
df['motor_rpm'] = 0.0

# Funções para extrair os valores
def extract_values_042(row):
    dataL = row['data0'] | (row['data1'] << 8) | (row['data2'] << 16) | (row['data3'] << 24)
    dataH = row['data4'] | (row['data5'] << 8) | (row['data6'] << 16) | (row['data7'] << 24)
    accel_value = dataL & 0xFFFF
    brake_value = (dataL >> 16) & 0xFFFF
    regen_brake_flag = dataH & 0xFF
    rtd_flag = (dataH >> 8) & 0xFF
    mode = (dataH >> 16) & 0xFF
    generic_flag = (dataH >> 24) & 0xFF
    return accel_value, brake_value, regen_brake_flag, rtd_flag, mode, generic_flag

def extract_values_043(row):
    dataL = row['data0'] | (row['data1'] << 8) | (row['data2'] << 16) | (row['data3'] << 24)
    dataH = row['data4'] | (row['data5'] << 8) | (row['data6'] << 16) | (row['data7'] << 24)
    DCL_value = dataL & 0xFFFF
    CCL_value = (dataL >> 16) & 0xFFFF
    battery_pack_value = dataH & 0xFFFF
    return DCL_value, CCL_value, battery_pack_value

def extract_values_046(row):
    dataL = row['data0'] | (row['data1'] << 8) | (row['data2'] << 16) | (row['data3'] << 24)
    dataH = row['data4'] | (row['data5'] << 8) | (row['data6'] << 16) | (row['data7'] << 24)
    hv_voltage = (dataL & 0xFFFF) / 10.0
    motor_current = (dataL >> 16) / 10.0
    motor_temp = (dataH & 0xFFFF) / 10.0
    controller_temp = (dataH >> 16) / 10.0
    return hv_voltage, motor_current, motor_temp, controller_temp

def extract_values_047(row):
    dataL = row['data0'] | (row['data1'] << 8) | (row['data2'] << 16) | (row['data3'] << 24)
    dataH = row['data4'] | (row['data5'] << 8) | (row['data6'] << 16) | (row['data7'] << 24)
    motor_torque = (dataL & 0xFFFF) / 10.0
    motor_power_out = (dataL >> 16) & 0xFFFF
    motor_power_in = (dataH & 0xFFFF)
    motor_rpm = ((dataH >> 16) & 0xFFFF)*25
    return motor_torque, motor_power_out, motor_power_in, motor_rpm

# Processar cada linha do DataFrame
for index, row in df.iterrows():
    if row['msgId'] == 42:  # Corrigido para 42
        accel_value, brake_value, regen_brake_flag, rtd_flag, mode, generic_flag = extract_values_042(row)
        df.at[index, 'accel_value'] = accel_value * 2
        df.at[index, 'brake_value'] = brake_value
        df.at[index, 'regen_brake_flag'] = regen_brake_flag
        df.at[index, 'rtd_flag'] = rtd_flag
        df.at[index, 'mode'] = mode
        df.at[index, 'generic_flag'] = generic_flag
    elif row['msgId'] == 43:  # Corrigido para 43
        DCL_value, CCL_value, battery_pack_value = extract_values_043(row)
        df.at[index, 'DCL_value'] = DCL_value
        df.at[index, 'CCL_value'] = CCL_value
        df.at[index, 'battery_pack_value'] = battery_pack_value
    elif row['msgId'] == 46:  # Corrigido para 46
        hv_voltage, motor_current, motor_temp, controller_temp = extract_values_046(row)
        df.at[index, 'hv_voltage'] = hv_voltage
        df.at[index, 'motor_current'] = motor_current
        df.at[index, 'motor_temp'] = motor_temp
        df.at[index, 'controller_temp'] = controller_temp
    elif row['msgId'] == 47:  # Nova mensagem 47
        motor_torque, motor_power_out, motor_power_in, motor_rpm = extract_values_047(row)
        df.at[index, 'motor_torque'] = motor_torque
        df.at[index, 'motor_power_out'] = motor_power_out
        df.at[index, 'motor_power_in'] = motor_power_in
        df.at[index, 'motor_rpm'] = motor_rpm

# Função para plotar os gráficos com intervalo de tempo selecionado
def plot_data(start_time, end_time):
    # Filtrar os dados para o intervalo de tempo selecionado
    df_filtered = df[(df['tempoDoSistema'] >= start_time) & (df['tempoDoSistema'] <= end_time)]
    
    # Filtrar os dados para plotagem
    df_042 = df_filtered[df_filtered['msgId'] == 42]
    df_046 = df_filtered[df_filtered['msgId'] == 46]
    df_047 = df_filtered[df_filtered['msgId'] == 47]

    # Plotar os gráficos com os valores extraídos
    plt.figure(figsize=(12, 8))

    # Acelerador, Freio e RPM
    plt.subplot(2, 2, 1)
    #plt.plot(df_042['tempoDoSistema'], df_042['accel_value'], label='Accel Value')
    #plt.plot(df_042['tempoDoSistema'], df_042['brake_value'], label='Brake Value')
    plt.plot(df_047['tempoDoSistema'], df_047['motor_rpm'], label='Motor RPM')
    plt.xlabel('Time (ms)')
    plt.ylabel('Value')
    plt.title('Accel, Brake, and RPM')
    plt.legend()

    # Temperaturas
    plt.subplot(2, 2, 2)
    plt.plot(df_046['tempoDoSistema'], df_046['motor_temp'], label='Motor Temp')
    plt.plot(df_046['tempoDoSistema'], df_046['controller_temp'], label='Controller Temp')
    plt.xlabel('Time (ms)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperatures')
    plt.legend()

    # Torque e Corrente
    plt.subplot(2, 2, 3)
    plt.plot(df_047['tempoDoSistema'], df_047['motor_torque'], label='Motor Torque')
    plt.plot(df_046['tempoDoSistema'], df_046['motor_current'], label='Motor Current')
    plt.xlabel('Time (ms)')
    plt.ylabel('Value')
    plt.title('Torque and Current')
    plt.legend()

    # Potências
    plt.subplot(2, 2, 4)
    plt.plot(df_047['tempoDoSistema'], df_047['motor_power_out'], label='Motor Power Out')
    plt.plot(df_047['tempoDoSistema'], df_047['motor_power_in'], label='Motor Power In')
    plt.xlabel('Time (ms)')
    plt.ylabel('Power (W)')
    plt.title('Motor Power In and Out')
    plt.legend()

    plt.tight_layout()
    plt.show()

plot_data(100000, 221727)