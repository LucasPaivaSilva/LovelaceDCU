import os
import pandas as pd

# Carregar o arquivo CSV
file_path = "lovelace0308-ecpa3.csv"
df = pd.read_csv(file_path)

# Obter o nome do arquivo sem a extensão
file_name, file_extension = os.path.splitext(file_path)

# Lista para armazenar DataFrames divididos
dfs = []

# Inicializar a lista de dataframes e o dataframe temporário
temp_df = []

# Iterar sobre as linhas do DataFrame original
previous_time = 0
for index, row in df.iterrows():
    current_time = row['tempoDoSistema']
    
    # Se o tempo atual for menor que o tempo anterior, significa que o sistema reiniciou
    if current_time < previous_time:
        # Adicionar o DataFrame temporário à lista e resetá-lo
        dfs.append(pd.DataFrame(temp_df, columns=df.columns))
        temp_df = []
    
    # Adicionar a linha atual ao DataFrame temporário
    temp_df.append(row)
    
    # Atualizar o tempo anterior
    previous_time = current_time

# Adicionar o último DataFrame temporário à lista
dfs.append(pd.DataFrame(temp_df, columns=df.columns))

# Salvar os DataFrames separados em arquivos CSV diferentes
for i, df_split in enumerate(dfs):
    df_split.to_csv(f"{file_name}_part_{i+1}.csv", index=False)

print("Arquivos separados com sucesso.")