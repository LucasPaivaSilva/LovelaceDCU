import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Fonte Times New Roman e tamanho adequado
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 8
})

# Carregar os dados já pré-processados
file_path = 'lovelace0308-ecpa3_part_38.csv'
data = pd.read_csv(file_path)

# Ajuste de tempo
data['tempoDoSistema'] = (data['tempoDoSistema'] - data['tempoDoSistema'].min()) / 1000
filtered_data = data[data['msgId'] == 47]
for i in range(8):
    filtered_data[f'data{i}'] = filtered_data[f'data{i}'].apply(lambda x: int(str(x), 16))

# Calcular potências

filtered_data['power'] = filtered_data.apply(lambda row: row['data4'] + (row['data5'] << 8) - 20000, axis=1)
filtered_data['motor_power'] = filtered_data.apply(lambda row: row['data2'] + (row['data3'] << 8) - 20000, axis=1)


# Remover pontos de potência fisicamente inválidos (menores que -3000 W)
filtered_data = filtered_data[(filtered_data['power'] >= -3000) & (filtered_data['motor_power'] >= -3000)]


# Definir intervalo de tempo para plotagem (em segundos)
tempo_inicial = 100
tempo_final = 200

# Filtrar dados dentro do intervalo desejado
filtered_data = filtered_data[(filtered_data['tempoDoSistema'] >= tempo_inicial) & (filtered_data['tempoDoSistema'] <= tempo_final)]

fig, axes = plt.subplots(2, 1, figsize=(3.5*1.5, 5.0))  # Aproximadamente 88mm de largura e altura ajustada

axes[0].plot(filtered_data['tempoDoSistema'], filtered_data['power'], label='Inverter Power (W)', color='tab:blue', linewidth=0.8)
axes[0].plot(filtered_data['tempoDoSistema'], filtered_data['motor_power'], label='Motor Power (W)', color='tab:orange', linewidth=0.8)
axes[0].set_xlabel('System Time (s)')
axes[0].set_ylabel('Power (W)')
axes[0].grid(True)
axes[0].legend(loc='best', fontsize=7)

filtered_data['motor_rpm'] = filtered_data.apply(lambda row: (row['data6'] + (row['data7'] << 8) - 1000), axis=1)

axes[1].plot(filtered_data['tempoDoSistema'], filtered_data['motor_rpm'], label='Motor Speed (RPM)', color='tab:green', linewidth=0.8)
axes[1].set_xlabel('System Time (s)')
axes[1].set_ylabel('Motor Speed (RPM)')
axes[1].grid(True)
axes[1].legend(loc='best', fontsize=7)

# Ajuste final
plt.tight_layout()

# Salvar como PDF vetorial (melhor para o artigo)
plt.savefig('fig_power_plot.png', format='png', dpi=600)

# Exibir
plt.show()