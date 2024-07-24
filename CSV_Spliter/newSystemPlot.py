import pandas as pd
import matplotlib.pyplot as plt

# Atualizar o tamanho da fonte
plt.rcParams.update({'font.size': 14})  # Ajuste este valor conforme necessário

# Variáveis de controle para filtragem por intervalo de tempo
filter_time = True  # Defina como True para habilitar a filtragem por intervalo de tempo
start_time = 68   # Tempo inicial para filtragem (em unidades do tempo do sistema)
end_time = 78     # Tempo final para filtragem (em unidades do tempo do sistema)

# Variáveis para espessura da linha e tamanho dos marcadores
linewidth = 0.75
markersize = 0.25

# Carregar os dados do arquivo CSV
file_path = 'lovelace2207-ufsc1_part_7.csv'
data = pd.read_csv(file_path)

# Converter tempo do sistema de milissegundos para segundos e ajustar para começar em zero
data['tempoDoSistema'] = (data['tempoDoSistema'] - data['tempoDoSistema'].min()) / 1000

# Filtrar mensagens com msgId 47 (para potência do inversor, potência do motor, torque e RPM)
filtered_data = data[data['msgId'] == 47]

# Converter data0, data1, data2, data3, data4, data5, data6 e data7 de hexadecimal para inteiro
filtered_data['data0'] = filtered_data['data0'].apply(lambda x: int(str(x), 16))
filtered_data['data1'] = filtered_data['data1'].apply(lambda x: int(str(x), 16))
filtered_data['data2'] = filtered_data['data2'].apply(lambda x: int(str(x), 16))
filtered_data['data3'] = filtered_data['data3'].apply(lambda x: int(str(x), 16))
filtered_data['data4'] = filtered_data['data4'].apply(lambda x: int(str(x), 16))
filtered_data['data5'] = filtered_data['data5'].apply(lambda x: int(str(x), 16))
filtered_data['data6'] = filtered_data['data6'].apply(lambda x: int(str(x), 16))
filtered_data['data7'] = filtered_data['data7'].apply(lambda x: int(str(x), 16))

# Calcular a potência do inversor combinando data4 (LSB) e data5 (MSB) e remover o offset de 20000
filtered_data['power'] = filtered_data.apply(lambda row: row['data4'] + (row['data5'] << 8) - 20000, axis=1)

# Calcular a potência do motor combinando data2 (LSB) e data3 (MSB) e remover o offset de 20000
filtered_data['motor_power'] = filtered_data.apply(lambda row: row['data2'] + (row['data3'] << 8) - 20000, axis=1)

# Calcular o torque do motor combinando data0 (LSB) e data1 (MSB) e dividir por 10
filtered_data['torque'] = filtered_data.apply(lambda row: (row['data0'] + (row['data1'] << 8)) / 10, axis=1)

# Calcular a rotação do motor combinando data6 (LSB) e data7 (MSB)
filtered_data['motor_rpm'] = filtered_data.apply(lambda row: row['data6'] + (row['data7'] << 8), axis=1) * 0

# Filtrar mensagens com msgId 46 (para corrente e tensão)
current_data = data[data['msgId'] == 46]

# Converter data0, data1, data2 e data3 de hexadecimal para inteiro
current_data['data0'] = current_data['data0'].apply(lambda x: int(str(x), 16))
current_data['data1'] = current_data['data1'].apply(lambda x: int(str(x), 16))
current_data['data2'] = current_data['data2'].apply(lambda x: int(str(x), 16))
current_data['data3'] = current_data['data3'].apply(lambda x: int(str(x), 16))

# Calcular a tensão combinando data0 (LSB) e data1 (MSB)
current_data['voltage'] = current_data.apply(lambda row: row['data0'] + (row['data1'] << 8), axis=1) * 0.1

# Calcular a corrente combinando data2 (LSB) e data3 (MSB), adicionar o offset de 1000, dividir por 10 e remover 900
current_data['current'] = current_data.apply(lambda row: (row['data2'] + (row['data3'] << 8)) / 10 - 1000, axis=1)

# Filtrar mensagens com msgId 42 (para acelerador e flag Ready to Drive)
accelerator_data = data[data['msgId'] == 42]

# Converter data0, data1 e data5 de hexadecimal para inteiro
accelerator_data['data0'] = accelerator_data['data0'].apply(lambda x: int(str(x), 16))
accelerator_data['data1'] = accelerator_data['data1'].apply(lambda x: int(str(x), 16))
accelerator_data['data5'] = accelerator_data['data5'].apply(lambda x: int(str(x), 16))

# Calcular a porcentagem do acelerador combinando data0 (LSB) e data1 (MSB) e escalando para 0-100%
accelerator_data['accelerator'] = accelerator_data.apply(lambda row: ((row['data0'] + (row['data1'] << 8)) / 65535) * 100, axis=1)

# Extrair o estado da flag Ready to Drive do byte 5
accelerator_data['ready_to_drive'] = accelerator_data['data5']

# Mesclar todos os dados com base nos valores de tempoDoSistema mais próximos
final_merged_data = pd.merge_asof(filtered_data[['tempoDoSistema', 'power', 'motor_power', 'torque', 'motor_rpm']], 
                                  current_data[['tempoDoSistema', 'voltage']], 
                                  on='tempoDoSistema', 
                                  direction='nearest')

final_merged_data = pd.merge_asof(final_merged_data, 
                                  accelerator_data[['tempoDoSistema', 'accelerator', 'ready_to_drive']], 
                                  on='tempoDoSistema', 
                                  direction='nearest')

# Aplicar filtragem por intervalo de tempo se habilitado
if filter_time:
    final_merged_data = final_merged_data[(final_merged_data['tempoDoSistema'] >= start_time) & (final_merged_data['tempoDoSistema'] <= end_time)]

# Imprimir os valores máximos de cada variável
print("Valores Máximos:")
print("Potência do Inversor (W):", final_merged_data['power'].max())
print("Potência do Motor (W):", final_merged_data['motor_power'].max())
print("Tensão (V):", final_merged_data['voltage'].max())
print("Torque do Motor (N.m):", final_merged_data['torque'].max())
print("Rotação do Motor (RPM):", final_merged_data['motor_rpm'].max())
print("Acelerador (%):", final_merged_data['accelerator'].max())
print("Ready to Drive (Flag):", final_merged_data['ready_to_drive'].max())

# Plot the adjusted inverter power, motor power, motor RPM, voltage, accelerator percentage, torque, and ready to drive flag over time with thinner lines and smaller markers
fig, (ax1, ax3) = plt.subplots(1, 2, figsize=(24, 6))

# Plot inverter power, motor power, motor RPM, and voltage on the first subplot
ax1.set_xlabel('Tempo do Sistema (s)')
ax1.set_ylabel('Potências (W) e Tensão (V)', color='tab:orange')
line1 = ax1.plot(final_merged_data['tempoDoSistema'], final_merged_data['power'], label='Potência do Inversor', marker='o', linestyle='-', color='tab:orange', linewidth=linewidth, markersize=markersize)
line2 = ax1.plot(final_merged_data['tempoDoSistema'], final_merged_data['motor_power'], label='Potência do Motor', marker='s', linestyle='-', color='tab:red', linewidth=linewidth, markersize=markersize)
ax1.tick_params(axis='y', labelcolor='tab:orange')

# Create a secondary y-axis for motor RPM and voltage
ax2 = ax1.twinx()
ax2.set_ylabel('Rotação do Motor (RPM) e Tensão (V)', color='tab:brown')
line3 = ax2.plot(final_merged_data['tempoDoSistema'], final_merged_data['motor_rpm'], label='Rotação do Motor (RPM)', marker='d', linestyle='-', color='tab:brown', linewidth=linewidth, markersize=markersize)
line4 = ax2.plot(final_merged_data['tempoDoSistema'], final_merged_data['voltage'], label='Tensão (V)', marker='x', linestyle='-', color='tab:blue', linewidth=linewidth, markersize=markersize)
ax2.tick_params(axis='y', labelcolor='tab:brown')

# Adicionar legenda ao primeiro gráfico
lines = line1 + line2 + line3 + line4
labels = [line.get_label() for line in lines]
ax1.legend(lines, labels, loc='upper left')

ax1.set_title('Potência do Inversor, Potência do Motor, Rotação do Motor e Tensão ao longo do tempo')
ax1.grid(True)

# Plot accelerator percentage, motor torque, and ready to drive flag on the second subplot

ax3.set_xlabel("Tempo do Sistema (s)")
ax3.set_ylabel("Acelerador (%)", color="tab:green")
ax3.plot(final_merged_data["tempoDoSistema"], final_merged_data["accelerator"], label="Acelerador (%)", marker="^", linestyle="-", color="tab:green", linewidth=linewidth, markersize=markersize)
ax3.tick_params(axis="y", labelcolor="tab:green")

# Create a secondary y-axis for motor torque and ready to drive flag

ax4 = ax3.twinx()
ax4.set_ylabel("Torque do Motor (N.m) e Ready to Drive (Flag)", color="tab:purple")
line5 = ax4.plot(final_merged_data["tempoDoSistema"], final_merged_data["torque"], label="Torque do Motor", marker="v", linestyle="-", color="tab:purple", linewidth=linewidth, markersize=markersize)
line6 = ax4.plot(final_merged_data["tempoDoSistema"], final_merged_data["ready_to_drive"], label="Ready to Drive", marker="x", linestyle="-", color="tab:blue", linewidth=linewidth, markersize=markersize)
ax4.tick_params(axis="y", labelcolor="tab:purple")

# Adicionar legenda ao segundo gráfico

lines = ax3.get_lines() + ax4.get_lines()
labels = [line.get_label() for line in lines]
ax3.legend(lines, labels, loc="upper left")

# Title and grid for the second subplot

ax3.set_title("Acelerador (%), Torque do Motor e Ready to Drive ao longo do tempo")
ax3.grid(True)

# Adjust layout to prevent overlap

plt.tight_layout()
plt.show()

