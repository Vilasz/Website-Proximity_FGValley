import pandas as pd

def process_data(df):
    # Filtrar apenas as colunas relevantes (nome e níveis de proximidade)
    df = df.drop(columns=[col for col in df.columns if 'Carimbo' in col or 'Seu nome' in col], errors='ignore')

    # Ajustar os nomes das colunas para remover espaços e caracteres especiais
    df.columns = df.columns.str.strip()

    # Criar uma matriz simétrica de proximidade
    df_matrix = df.set_index(df.columns[0])
    df_matrix = df_matrix.apply(pd.to_numeric, errors='coerce')
    return df_matrix
