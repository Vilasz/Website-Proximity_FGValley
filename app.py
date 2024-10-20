import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objs as go

# Carregar a matriz simétrica
matriz_simetrica = pd.read_csv('data/matriz_simetrica.csv', index_col=0)

# Calculate the integration score "dado" (row sum) and "recebido" (column sum)
integration_score_dado = matriz_simetrica.sum(axis=1)  # Soma da linha (valores que a pessoa dá)
integration_score_recebido = matriz_simetrica.sum(axis=0)  # Soma da coluna (valores que a pessoa recebe)

# Definir limites para classificar "mais bem relacionadas" e "menos bem relacionadas"
top_n = 5  # Quantidade de pessoas a exibir

# KPIs: Pessoas mais e menos bem relacionadas com base nos scores de integração
most_related_dado = integration_score_dado.nlargest(top_n).index.tolist()
least_related_dado = integration_score_dado.nsmallest(top_n).index.tolist()

most_related_recebido = integration_score_recebido.nlargest(top_n).index.tolist()
least_related_recebido = integration_score_recebido.nsmallest(top_n).index.tolist()

# Exibir KPIs no painel lateral
st.sidebar.subheader("Pessoas mais bem relacionadas (Dado)")
st.sidebar.write(most_related_dado)

st.sidebar.subheader("Pessoas menos bem relacionadas (Dado)")
st.sidebar.write(least_related_dado)

st.sidebar.subheader("Pessoas mais bem relacionadas (Recebido)")
st.sidebar.write(most_related_recebido)

st.sidebar.subheader("Pessoas menos bem relacionadas (Recebido)")
st.sidebar.write(least_related_recebido)

# Filtros para os scores "dado" e "recebido"
min_integration_dado = st.sidebar.slider(
    "Filtrar pessoas pelo score de integração (Dado)",
    min_value=int(integration_score_dado.min()),
    max_value=int(integration_score_dado.max()),
    value=(int(integration_score_dado.min()), int(integration_score_dado.max()))
)

min_integration_recebido = st.sidebar.slider(
    "Filtrar pessoas pelo score de integração (Recebido)",
    min_value=int(integration_score_recebido.min()),
    max_value=int(integration_score_recebido.max()),
    value=(int(integration_score_recebido.min()), int(integration_score_recebido.max()))
)

# Sidebar filters for selecting people (nodes)
selected_people = st.sidebar.multiselect(
    "Selecione pessoas para filtrar a rede:",
    options=matriz_simetrica.index.tolist(),
    default=matriz_simetrica.index.tolist()  # Mostrar todas por padrão
)

# Filtro adicional para pessoas com poucas ou nenhuma conexão forte
strong_threshold = 3
min_strong_connections = st.sidebar.slider(
    "Filtrar pessoas com no mínimo conexões fortes",
    min_value=0,
    max_value=int((matriz_simetrica > strong_threshold).sum(axis=1).max()),
    value=0
)

# Filtrar pessoas com base no número de conexões fortes
strong_connections_filter = (matriz_simetrica > strong_threshold).sum(axis=1) >= min_strong_connections

# Filter the graph based on the selected integration ranges e conexões fortes
filtered_people_dado = integration_score_dado[
    (integration_score_dado >= min_integration_dado[0]) & 
    (integration_score_dado <= min_integration_dado[1])
].index.tolist()

filtered_people_recebido = integration_score_recebido[
    (integration_score_recebido >= min_integration_recebido[0]) & 
    (integration_score_recebido <= min_integration_recebido[1])
].index.tolist()

filtered_people_strong = strong_connections_filter[strong_connections_filter].index.tolist()

# Final filtered people are those who satisfy all conditions
filtered_people = list(set(filtered_people_dado) & set(filtered_people_recebido) & set(selected_people) & set(filtered_people_strong))

# Create a subgraph based on the filtered nodes
G = nx.from_pandas_adjacency(matriz_simetrica)
G_filtered = G.subgraph(filtered_people)

# Ajustar spring_layout para espalhar os nós e evitar sobreposição
pos = nx.spring_layout(G_filtered, weight=None, k=0.5, iterations=200)

# Desenhar a rede (usando Plotly para interatividade)
edge_trace_list = []  # Armazenar os traços de arestas individualmente

for edge in G_filtered.edges(data=True):
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x = [x0, x1, None]
    edge_y = [y0, y1, None]

    # Adicionar texto ao passar o mouse e a espessura
    strength = matriz_simetrica.loc[edge[0], edge[1]]
    hover_edge_text = f"{edge[0]} ↔ {edge[1]}: {strength}"

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5 * strength, color='#888'),  # Ajuste da espessura
        hoverinfo='text',
        mode='lines',
        hovertext=hover_edge_text
    )
    
    edge_trace_list.append(edge_trace)

# Traçar os nós sem círculos visíveis e remover o texto
node_x = []
node_y = []
hover_text = []
node_integration_dado = []

for node in G_filtered.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    
    # Obter informações para o hover
    weak_connections = matriz_simetrica.loc[node][matriz_simetrica.loc[node] < 3].dropna().index.tolist()
    hover_info = f"Nome: {node}<br>Integração Dado: {integration_score_dado[node]:.2f}<br>Integração Recebido: {integration_score_recebido[node]:.2f}<br>Conexões Fracas: {', '.join(weak_connections)}"
    
    hover_text.append(hover_info)
    node_integration_dado.append(integration_score_dado[node])

# Criar os nós com apenas cor e hover
node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',  # Apenas marcadores (sem texto ou círculos)
    hoverinfo='text',
    marker=dict(
        showscale=True,
        colorscale='YlGnBu',
        colorbar=dict(
            thickness=15,
            title='Integration Dado',
            xanchor='left',
            titleside='right'
        ),
        size=12,  # Tamanho fixo para os nós
        color=node_integration_dado,  # Cor baseada no score de integração "dado"
        line_width=0),
    hovertext=hover_text
)

# Layout do grafo
fig = go.Figure(data=[node_trace] + edge_trace_list,
                layout=go.Layout(
                    title="Rede Filtrada por Integração e Conexões Fortes",
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=0),
                    annotations=[dict(
                        showarrow=False,
                        xref="paper", yref="paper",
                        text="",
                        x=0.005, y=-0.002
                    )],
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=False, zeroline=False)))

# Título e interface no Streamlit
st.title("Visualização de Rede com KPIs e Filtros de Integração")
st.plotly_chart(fig)

# Mostrar a matriz simétrica original para referência
st.subheader("Matriz Simétrica Original")
st.write(matriz_simetrica)

# Tabela de integração com scores "dado" e "recebido"
st.subheader("Tabela de Integração")
df_integration = pd.DataFrame({
    'Pessoa': matriz_simetrica.index,
    'Integração Dado': integration_score_dado,
    'Integração Recebido': integration_score_recebido
})
st.write(df_integration)
