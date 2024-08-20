from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import os

token = os.environ.get("INFLUXDB_TOKEN")
org = "Data"
host = "https://us-east-1-1.aws.cloud2.influxdata.com"
bucket = "Ampera"

# Cliente do InfluxDB
client = InfluxDBClient(url=host, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Carregar os dados do arquivo CSV
file_path = 'lovelace1707-ufsc_part_5.csv'
data = pd.read_csv(file_path)

# Converter tempo do sistema de milissegundos para segundos e ajustar para começar em zero
data['tempoDoSistema'] = (data['tempoDoSistema'] - data['tempoDoSistema'].min()) / 1000

# Filtrar mensagens com msgId 47 (para potência do inversor, potência do motor, torque e RPM)
filtered_data = data[data['msgId'] == 47].copy()

# Converter data0, data1, data2, data3, data4, data5, data6 e data7 de hexadecimal para inteiro
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

# Filtrar mensagens com msgId 46 (para corrente, tensão e temperaturas)
current_data = data[data['msgId'] == 46].copy()

# Converter data0, data1, data2, data3, data4, data5, data6 e data7 de hexadecimal para inteiro
for i in range(8):
    current_data[f'data{i}'] = current_data[f'data{i}'].apply(lambda x: int(str(x), 16))

# Calcular a tensão combinando data0 (LSB) e data1 (MSB) e dividir por 10
current_data['voltage'] = current_data.apply(lambda row: (row['data0'] + (row['data1'] << 8)) / 10, axis=1)

# Calcular a corrente combinando data2 (LSB) e data3 (MSB), adicionar o offset de 1000 e remover 1000
current_data['current'] = current_data.apply(lambda row: (row['data2'] + (row['data3'] << 8)) / 10 - 1000, axis=1)

# Calcular a temperatura do motor combinando data4 (LSB) e data5 (MSB) e dividir por 10
current_data['motor_temp'] = current_data.apply(lambda row: (row['data4'] + (row['data5'] << 8)) / 10, axis=1)

# Calcular a temperatura do controlador combinando data6 (LSB) e data7 (MSB) e dividir por 10
current_data['controller_temp'] = current_data.apply(lambda row: (row['data6'] + (row['data7'] << 8)) / 10, axis=1)

# Filtrar mensagens com msgId 42 (para acelerador e outras flags)
accelerator_data = data[data['msgId'] == 42].copy()

# Converter data0, data1, data2, data3, data4, data5, data6 e data7 de hexadecimal para inteiro
for i in range(8):
    accelerator_data[f'data{i}'] = accelerator_data[f'data{i}'].apply(lambda x: int(str(x), 16))

# Calcular a porcentagem do acelerador combinando data0 (LSB) e data1 (MSB) e escalando para 0-100%
accelerator_data['accelerator'] = accelerator_data.apply(lambda row: ((row['data0'] + (row['data1'] << 8)) / 65535) * 100, axis=1)

# Extrair o estado da flag Ready to Drive do byte 5
accelerator_data['ready_to_drive'] = accelerator_data['data5']

# Extrair o estado da flag TorqueRequestDisable do byte 7
accelerator_data['torque_request_disable'] = accelerator_data['data7']

# Extrair o modo de prova do byte 6
accelerator_data['test_mode'] = accelerator_data['data6']

# Extrair o estado da flag RegenRequest do byte 4
accelerator_data['regen_request'] = accelerator_data['data4']

# Calcular o freio combinando data2 (LSB) e data3 (MSB)
accelerator_data['brake'] = accelerator_data.apply(lambda row: row['data2'] + (row['data3'] << 8), axis=1)

# Mesclar todos os dados com base nos valores de tempoDoSistema mais próximos
final_merged_data = pd.merge_asof(
    filtered_data[['tempoDoSistema', 'power', 'motor_power', 'torque', 'motor_rpm']], 
    current_data[['tempoDoSistema', 'voltage', 'current', 'motor_temp', 'controller_temp']], 
    on='tempoDoSistema', 
    direction='nearest'
)

final_merged_data = pd.merge_asof(
    final_merged_data, 
    accelerator_data[['tempoDoSistema', 'accelerator', 'ready_to_drive', 'torque_request_disable', 'test_mode', 'regen_request', 'brake']], 
    on='tempoDoSistema', 
    direction='nearest'
)

# Enviar os dados para o InfluxDB
points = []
for _, row in final_merged_data.iterrows():
    point = Point("car_data") \
        .tag("source", "datalogger") \
        .field("power", row['power']) \
        .field("motor_power", row['motor_power']) \
        .field("torque", row['torque']) \
        .field("motor_rpm", row['motor_rpm']) \
        .field("voltage", row['voltage']) \
        .field("current", row['current']) \
        .field("motor_temp", row['motor_temp']) \
        .field("controller_temp", row['controller_temp']) \
        .field("accelerator", row['accelerator']) \
        .field("ready_to_drive", row['ready_to_drive']) \
        .field("torque_request_disable", row['torque_request_disable']) \
        .field("test_mode", row['test_mode']) \
        .field("regen_request", row['regen_request']) \
        .field("brake", row['brake']) \
        .time(int(row['tempoDoSistema'] * 1e9), WritePrecision.NS)  # Tempo em nanosegundos
    points.append(point)

write_api.write(bucket=bucket, org=org, record=points)

print(f"Dados inseridos com sucesso no InfluxDB em '{bucket}'.")

# Fechar o cliente
client.close()