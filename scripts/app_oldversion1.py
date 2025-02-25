# Importar Streamlit y otras bibliotecas
import streamlit as st
import pandas as pd
import numpy as np
from numpy.linalg import eig, inv

# Configurar Streamlit
st.set_page_config(page_title="Predicción demanda de producto con cadenas de Markov", page_icon=":bar_chart:")

# Leer los datos desde un archivo Parquet
@st.cache_data  # Caché para acelerar la lectura de datos
def cargar_datos():
    data = pd.read_parquet('/Users/tonitojuarez/Documents/GitHub/Predicting-product-demand-using-Markov-chains/data/tec_estocasticos.parquet', engine='pyarrow')
    data['periodo'] = pd.to_datetime(data['periodo'])
    data.sort_values(by='periodo', inplace=True)
    data.dropna(inplace=True)
    data.reset_index(inplace=True)
    data.drop('index', axis=1, inplace=True)
    return data

data = cargar_datos()

# Función para obtener la matriz de transición
def matriz_transicion(tipo_cliente, cliente_id, material_id):
        
    # Subset

    cliente_tipo = data.loc[data['tipo_cliente'] == tipo_cliente]
    pruducto = cliente_tipo.loc[cliente_tipo['material_id'] == material_id]
    id_cliente = pruducto.loc[pruducto['cliente_id'] == cliente_id]
    id_cliente.reset_index(inplace = True)
    id_cliente.drop('index', axis = 1, inplace = True)
    
    # Fecha de primer registro
    
    fecha_inicio = pd.Timestamp(2021, 1, 1)
    # Fecha del último registro 
    
    fecha_fin = pd.Timestamp(2023, 9, 1)

    frecuencia = pd.DateOffset(months=1)

    fechas = []

    while fecha_inicio <= fecha_fin:
        fechas.append(fecha_inicio)
        fecha_inicio += frecuencia

    periodos = {}

    for k,v in enumerate(fechas):
        periodos[v] = k 

    t = [1 for x in range(len(fechas))]

    indices = [periodos[x] for x in id_cliente['periodo']]

    for i in indices:
        t[i] = 0
    
    estados = pd.DataFrame()

    estados['t'] = t
    estados['t_1'] = t
    
    Xt = estados['t'][0:-1].reset_index(drop=True).rename('X_t')
    Xt_1 = estados['t_1'][1::].reset_index(drop=True).rename('X_t+1')
    
    new_data=pd.concat((Xt, Xt_1), axis=1)
    
    matriz_transicion = new_data.groupby('X_t').value_counts(normalize=True).unstack(level='X_t+1')
    matriz_transicion= matriz_transicion.fillna(0)
    
    return matriz_transicion

# Filtrar los datos en función del tipo de cliente seleccionado
def filtrar_cliente_id(tipo_cliente):
    return data[data['tipo_cliente'] == tipo_cliente]['cliente_id'].unique()

# Filtrar los materiales en función del cliente_id seleccionado
def filtrar_material_id(cliente_id):
    return data[data['cliente_id'] == cliente_id]['material_id'].unique()

# Menú desplegable para seleccionar parámetros
st.sidebar.title("Menú de Parámetros")
tipo_cliente = st.sidebar.selectbox('Tipo de Cliente:', list(data['tipo_cliente'].unique()))
cliente_ids_disponibles = filtrar_cliente_id(tipo_cliente)
cliente_id = st.sidebar.selectbox('Cliente ID:', cliente_ids_disponibles)
materiales_disponibles = filtrar_material_id(cliente_id)
material_id = st.sidebar.selectbox('Material ID:', materiales_disponibles)
pasos_t = st.sidebar.slider('Pasos (t):', 1, 50, 1)

# Botón para generar resultados
if st.sidebar.button('Generar Resultados'):
    
    try:
        # Llama a la función valores y muestra los resultados
        #st.subheader("Resultados")
        matriz = matriz_transicion(tipo_cliente, cliente_id, material_id)
        Lambda, Q = eig(matriz)
        Q_1 = inv(Q)
        Lambda = np.diag(Lambda)
        PP = np.matmul(np.matmul(Q, Lambda), Q_1)
        Lambda_n = Lambda**pasos_t
        P_n = np.matmul(np.matmul(Q, Lambda_n), Q_1)
        df = pd.DataFrame(P_n.round(decimals=4), index=['Compra', 'No compra'])
        df.rename(columns={0: 'Compra'}, inplace=True)
        df.rename(columns={1: 'No Compra'}, inplace=True)
    except:
        #st.subheader("No existe información de ese cliente comprando ese producto")
        None
    #st.write(df)
    #st.dataframe(df)
    
# Notas adicionales o explicaciones
st.sidebar.info("Esta aplicación permite calcular la probabilidad de que un cliente compre o no compre un producto en determinado número de pasos (meses)")

# Créditos y fuente de datos
st.sidebar.text("Siguenos en twitter: 👇")
st.sidebar.text("Autores: @manuelsolan_o, @tonito, @ale, @mayra, @yamuni")
#st.sidebar.text("Fuente de Datos: 'data/tec_estocasticos.parquet'")

# Código para ejecutar la aplicación de Streamlit
if __name__ == "__main__":
    st.title("Predicción demanda de producto con cadenas de Markov")
    
if 'df' in locals():
    st.subheader("Resultados")
    st.write(df)
else:
    st.subheader("No existe información de ese cliente comprando ese producto")
