import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Atualizar o tamanho da fonte
plt.rcParams.update({'font.size': 6})  # Ajuste este valor conforme necessário

# Variáveis de controle para filtragem por intervalo de tempo
filter_time = True  # Defina como True para habilitar a filtragem por intervalo de tempo
start_time = 20   # Tempo inicial para filtragem (em unidades do tempo do sistema)
end_time = 550     # Tempo final para filtragem (em unidades do tempo do sistema)

# Variáveis para espessura da linha e tamanho dos marcadores
linewidth = 0.75
markersize = 0.25

# Carregar os dados do arquivo CSV
file_path = 'lovelace0308-ecpa3_part_38.csv'
data = pd.read_csv(file_path)

# Converter tempo do sistema de milissegundos para segundos e ajustar para começar em zero
data['tempoDoSistema'] = (data['tempoDoSistema'] - data['tempoDoSistema'].min()) / 1000

# Filtrar mensagens com msgId 47 (para potência do inversor, potência do motor, torque e RPM)
filtered_data = data[data['msgId'] == 47]

# Converter data0 a data7 de hexadecimal para inteiro
for i in range(8):
    filtered_data[f'data{i}'] = filtered_data[f'data{i}'].apply(lambda x: int(str(x), 16))

# Calcular a potência do inversor combinando data4 (LSB) e data5 (MSB) e remover o offset de 20000
filtered_data['power'] = filtered_data.apply(lambda row: row['data4'] + (row['data5'] << 8) - 20000, axis=1)

# Calcular a potência do motor combinando data2 (LSB) e data3 (MSB) e remover o offset de 20000
filtered_data['motor_power'] = filtered_data.apply(lambda row: row['data2'] + (row['data3'] << 8) - 20000, axis=1)

# Calcular o torque do motor combinando data0 (LSB) e data1 (MSB), dividir por 10 e remover 1000
filtered_data['torque'] = filtered_data.apply(lambda row: (row['data0'] + (row['data1'] << 8)) / 10 - 1000, axis=1)

# Calcular a rotação do motor combinando data6 (LSB) e data7 (MSB) e remover 1000
filtered_data['motor_rpm'] = filtered_data.apply(lambda row: row['data6'] + (row['data7'] << 8) - 1000, axis=1)

# Filtrar mensagens com msgId 46 (para corrente, temperaturas e tensão do barramento)
current_data = data[data['msgId'] == 46]

# Converter data0 a data7 de hexadecimal para inteiro
for i in range(8):
    current_data[f'data{i}'] = current_data[f'data{i}'].apply(lambda x: int(str(x), 16))

# Calcular a corrente combinando data2 (LSB) e data3 (MSB), dividir por 10 e remover 1000
current_data['current'] = current_data.apply(lambda row: (row['data2'] + (row['data3'] << 8)) / 10 - 1000, axis=1)

# Calcular a temperatura do motor combinando data4 (LSB) e data5 (MSB) e dividir por 10
current_data['motor_temp'] = current_data.apply(lambda row: (row['data4'] + (row['data5'] << 8)) / 10, axis=1)

# Calcular a temperatura do inversor combinando data6 (LSB) e data7 (MSB) e dividir por 10
current_data['inverter_temp'] = current_data.apply(lambda row: (row['data6'] + (row['data7'] << 8)) / 10, axis=1)

# Filtrar mensagens com msgId 42 (para acelerador e flag Ready to Drive)
accelerator_data = data[data['msgId'] == 42]

# Converter data0, data1 e data5 de hexadecimal para inteiro
for i in [0, 1, 5]:
    accelerator_data[f'data{i}'] = accelerator_data[f'data{i}'].apply(lambda x: int(str(x), 16))

# Calcular a porcentagem do acelerador combinando data0 (LSB) e data1 (MSB) e escalando para 0-100%
accelerator_data['accelerator'] = accelerator_data.apply(lambda row: ((row['data0'] + (row['data1'] << 8)) / 65535) * 100, axis=1)

# Extrair o estado da flag Ready to Drive do byte 5
accelerator_data['ready_to_drive'] = accelerator_data['data5']

# Ordenar os dataframes por 'tempoDoSistema' antes de mesclar
filtered_data = filtered_data.sort_values('tempoDoSistema')
current_data = current_data.sort_values('tempoDoSistema')
accelerator_data = accelerator_data.sort_values('tempoDoSistema')

# Mesclar todos os dados com base nos valores de tempoDoSistema mais próximos
final_merged_data = pd.merge_asof(filtered_data[['tempoDoSistema', 'power', 'motor_power', 'torque', 'motor_rpm']], 
                                  current_data[['tempoDoSistema', 'current', 'inverter_temp', 'motor_temp']], 
                                  on='tempoDoSistema', 
                                  direction='nearest')

final_merged_data = pd.merge_asof(final_merged_data, 
                                  accelerator_data[['tempoDoSistema', 'accelerator', 'ready_to_drive']], 
                                  on='tempoDoSistema', 
                                  direction='nearest')

# Aplicar filtragem por intervalo de tempo se habilitado
if filter_time:
    final_merged_data = final_merged_data[(final_merged_data['tempoDoSistema'] >= start_time) & (final_merged_data['tempoDoSistema'] <= end_time)]

# Remover valores fora do normal (outliers)
final_merged_data.loc[final_merged_data['inverter_temp'] >= 100, 'inverter_temp'] = np.nan
final_merged_data.loc[final_merged_data['motor_temp'] >= 100, 'motor_temp'] = np.nan
final_merged_data.loc[(final_merged_data['torque'] < -30) | (final_merged_data['torque'] > 100), 'torque'] = np.nan
final_merged_data.loc[(final_merged_data['power'] < -2000) | (final_merged_data['power'] > 30000), 'power'] = np.nan
final_merged_data.loc[(final_merged_data['motor_power'] < -2000) | (final_merged_data['motor_power'] > 30000), 'motor_power'] = np.nan
final_merged_data.loc[(final_merged_data['motor_rpm'] < 0) | (final_merged_data['motor_rpm'] > 5000), 'motor_rpm'] = np.nan

# Calculate the average inverter power excluding zero values
non_zero_power = final_merged_data['power'][final_merged_data['power'] != 0]
average_inverter_power = non_zero_power.mean()

non_zero_rpm = final_merged_data['motor_rpm'][final_merged_data['motor_rpm'] != 0]
average_rpm = non_zero_rpm.mean()

# Print the average inverter power
print(f"Média da Potência do Inversor (W) excluindo zeros: {average_inverter_power:.2f}")
print(f"Média da rotação do motor excluindo zeros: {average_rpm:.2f}")

# Calcular a energia total integrada (em kWh) da potência do inversor ao longo do tempo
final_merged_data['delta_t'] = final_merged_data['tempoDoSistema'].diff().fillna(0)  # Diferença de tempo entre pontos
final_merged_data['energy'] = (final_merged_data['power'] * final_merged_data['delta_t']) / 3600000  # Energia em kWh
total_energy_kwh = final_merged_data['energy'].sum()

# Imprimir os valores máximos de cada variável e a energia total em kWh
print("Valores Máximos:")
print("Potência do Inversor (W):", final_merged_data['power'].max())
print("Potência do Motor (W):", final_merged_data['motor_power'].max())
print("Corrente Ajustada (A):", final_merged_data['current'].max())
print("Torque do Motor (N.m):", final_merged_data['torque'].max())
print("Rotação do Motor (RPM):", final_merged_data['motor_rpm'].max())
print("Acelerador (%):", final_merged_data['accelerator'].max())
print("Ready to Drive (Flag):", final_merged_data['ready_to_drive'].max())
print("Temperatura do Inversor (°C):", final_merged_data['inverter_temp'].max())
print("Temperatura do Motor (°C):", final_merged_data['motor_temp'].max())
print(f"Total de Energia consumida pelo Inversor: {total_energy_kwh:.4f} kWh")

# Plotar os dados ajustados de acordo com as novas especificações
fig, axes = plt.subplots(2, 2, figsize=(20, 12))

# Primeiro Gráfico: Potências no mesmo eixo
ax = axes[0, 0]
ax.plot(final_merged_data['tempoDoSistema'], final_merged_data['power'], label='Potência do Inversor', marker='o', linestyle='-', color='tab:orange', linewidth=linewidth, markersize=markersize)
ax.plot(final_merged_data['tempoDoSistema'], final_merged_data['motor_power'], label='Potência do Motor', marker='s', linestyle='-', color='tab:red', linewidth=linewidth, markersize=markersize)
ax.set_xlabel('Tempo do Sistema (s)')
ax.set_ylabel('Potência (W)')
ax.set_title('Potências do Inversor e do Motor ao longo do tempo')
ax.legend()
ax.grid(True)

# Segundo Gráfico: Acelerador e Torque do Motor com eixos alinhados no zero
ax = axes[0, 1]
ax.plot(final_merged_data['tempoDoSistema'], final_merged_data['accelerator'], label='Acelerador (%)', marker='^', linestyle='-', color='tab:green', linewidth=linewidth, markersize=markersize)
ax.set_xlabel('Tempo do Sistema (s)')
ax.set_ylabel('Acelerador (%)', color='tab:green')
ax.tick_params(axis='y', labelcolor='tab:green')
ax.set_ylim(0, 100)  # Fixar o eixo Y do acelerador entre 0 e 100

ax_twin = ax.twinx()
ax_twin.plot(final_merged_data['tempoDoSistema'], final_merged_data['torque'], label='Torque do Motor (N.m)', marker='v', linestyle='-', color='tab:purple', linewidth=linewidth, markersize=markersize)
ax_twin.set_ylabel('Torque do Motor (N.m)', color='tab:purple')
ax_twin.tick_params(axis='y', labelcolor='tab:purple')
ax_twin.set_ylim(-30, 100)  # Fixar o eixo Y do torque entre -30 e 100

ax.set_title('Acelerador (%) e Torque do Motor ao longo do tempo')
ax.grid(True)

# Combinar legendas
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax_twin.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

# Terceiro Gráfico: Rotação do Motor (RPM)
ax = axes[1, 0]
ax.plot(final_merged_data['tempoDoSistema'], final_merged_data['motor_rpm'], label='Rotação do Motor (RPM)', marker='d', linestyle='-', color='tab:brown', linewidth=linewidth, markersize=markersize)
ax.set_xlabel('Tempo do Sistema (s)')
ax.set_ylabel('Rotação do Motor (RPM)', color='tab:brown')
ax.tick_params(axis='y', labelcolor='tab:brown')
ax.set_title('Rotação do Motor ao longo do tempo')
ax.legend()
ax.grid(True)

# Quarto Gráfico: Temperaturas do Motor e Inversor
ax = axes[1, 1]
ax.plot(final_merged_data['tempoDoSistema'], final_merged_data['inverter_temp'], label='Temperatura do Inversor (°C)', marker='o', linestyle='-', color='tab:blue', linewidth=linewidth, markersize=markersize)
ax.plot(final_merged_data['tempoDoSistema'], final_merged_data['motor_temp'], label='Temperatura do Motor (°C)', marker='s', linestyle='-', color='tab:orange', linewidth=linewidth, markersize=markersize)
ax.set_xlabel('Tempo do Sistema (s)')
ax.set_ylabel('Temperatura (°C)')
ax.set_title('Temperaturas do Inversor e do Motor ao longo do tempo')
ax.legend()
ax.grid(True)

# Ajustar o layout para evitar sobreposição
plt.tight_layout()
plt.show()

# Selecionando as colunas que serão exportadas
final_merged_data_to_export = final_merged_data[['tempoDoSistema', 'power', 'motor_power', 'torque', 'motor_rpm', 'current', 'inverter_temp', 'motor_temp', 'accelerator', 'ready_to_drive']]

# Salvando o DataFrame final como CSV
file_export_path = 'enduro2024_Data_V1.csv'  # Substitua 'caminho_do_arquivo' pelo caminho desejado
final_merged_data_to_export.to_csv(file_export_path, index=False)

# Mensagem de sucesso
print(f"Arquivo CSV salvo em: {file_export_path}")