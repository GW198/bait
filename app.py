import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import re

# Configuración de la página
st.set_page_config(
    page_title="Procesador de Llamadas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .stat-card {
        background: #f8f9ff;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .stat-number {
        font-size: 32px;
        font-weight: bold;
        color: #667eea;
    }
    .stat-label {
        color: #666;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# Título
st.markdown('<div class="main-header"><h1>📊 Procesador de Llamadas</h1><p>Sube tu archivo de llamadas y genera reportes automáticos</p></div>', unsafe_allow_html=True)

# Mapeo de agentes
MAPEO_AGENTES = {
    'FALCANTARA': 'Fergie Zoe Alcantara',
    'JCARDENAS': 'Jorge Cardenas',
    'MGONZALEZ': 'Maria Gonzalez',
    'AGRAMONTE': 'Ana Gramonte',
    'RPEREZ': 'Roberto Perez',
    'LSANCHEZ': 'Laura Sanchez',
    'EDUARDO REYES ABASOLO': 'Eduardo Reyes Abasolo',
    'BRECECA CARMONA MARTELL': 'Brebeca Carmona Martell',
    'KAELAN ANDRE GUTIERREZ GONZALEZ': 'Kaelan Andre Gutierrez Gonzalez',
    'LEONEL PRECIADO MARTINEZ': 'Leonel Preciado Martínez',
    'ANA KAREN PADILLA MARTINEZ': 'Ana Karen Padilla Martínez',
    'EMMANUEL RUIZ VERA': 'Emmanuel Ruiz Vera',
}

AGENTES_ORDER = [
    'Eduardo Reyes Abasolo',
    'Brebeca Carmona Martell',
    'Kaelan Andre Gutierrez Gonzalez',
    'Leonel Preciado Martínez',
    'Ana Karen Padilla Martínez',
    'Emmanuel Ruiz Vera'
]

RANGOS_HORA = [
    '9:00 A 10:00', '10:00 A 11:00', '11:00 A 12:00',
    '12:00 A 13:00', '13:00 A 14:00', '14:00 A 15:00',
    '15:00 A 16:00', '16:00 A 17:00', '17:00 A 18:00'
]

# Mapeo de horas para el archivo de tiempos
HORAS_ARCHIVO = {
    '6 AM': '6:00 A 7:00',
    '7 AM': '7:00 A 8:00',
    '8 AM': '8:00 A 9:00',
    '9 AM': '9:00 A 10:00',
    '10 AM': '10:00 A 11:00',
    '11 AM': '11:00 A 12:00',
    '12 PM': '12:00 A 13:00',
    '1 PM': '13:00 A 14:00',
    '2 PM': '14:00 A 15:00',
    '3 PM': '15:00 A 16:00',
    '4 PM': '16:00 A 17:00',
    '5 PM': '17:00 A 18:00',
    '6 PM': '18:00 A 19:00',
    '7 PM': '19:00 A 20:00',
    '8 PM': '20:00 A 21:00',
    '9 PM': '21:00 A 22:00',
    '10 PM': '22:00 A 23:00',
    '11 PM': '23:00 A 0:00',
}

# Funciones de procesamiento
@st.cache_data
def convertir_agente(agente):
    """Convierte el código del agente a nombre completo"""
    if pd.isna(agente):
        return None
    clave = str(agente).upper().strip()
    # Buscar en el mapeo
    for key, value in MAPEO_AGENTES.items():
        if key in clave or clave in key:
            return value
    return str(agente)

@st.cache_data
def procesar_fecha(fecha_str):
    """Procesa la fecha en diferentes formatos"""
    if pd.isna(fecha_str):
        return None
    
    try:
        if isinstance(fecha_str, str):
            # Limpiar el string
            fecha_str = fecha_str.replace('a. m.', 'AM').replace('p. m.', 'PM')
            fecha_str = fecha_str.replace('a.m.', 'AM').replace('p.m.', 'PM')
            fecha_str = fecha_str.replace('a. m', 'AM').replace('p. m', 'PM')
            
            # Intentar diferentes formatos
            formatos = [
                '%d/%m/%Y %I:%M:%S %p',
                '%d/%m/%Y %I:%M %p',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %I:%M:%S %p',
                '%m/%d/%Y %I:%M %p',
                '%d-%m-%Y %I:%M:%S %p',
                '%d-%m-%Y %I:%M %p',
            ]
            
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_str, formato)
                except:
                    continue
            
            # Intentar con dateutil si está disponible
            try:
                from dateutil import parser
                return parser.parse(fecha_str)
            except:
                pass
        
        # Si ya es datetime
        if isinstance(fecha_str, datetime):
            return fecha_str
            
        # Si es pandas Timestamp
        if hasattr(fecha_str, 'to_pydatetime'):
            return fecha_str.to_pydatetime()
            
        return None
    except Exception as e:
        return None

@st.cache_data
def obtener_rango_hora(hora):
    """Obtiene el rango de hora según la hora dada"""
    if hora >= 9 and hora < 10:
        return '9:00 A 10:00'
    elif hora >= 10 and hora < 11:
        return '10:00 A 11:00'
    elif hora >= 11 and hora < 12:
        return '11:00 A 12:00'
    elif hora >= 12 and hora < 13:
        return '12:00 A 13:00'
    elif hora >= 13 and hora < 14:
        return '13:00 A 14:00'
    elif hora >= 14 and hora < 15:
        return '14:00 A 15:00'
    elif hora >= 15 and hora < 16:
        return '15:00 A 16:00'
    elif hora >= 16 and hora < 17:
        return '16:00 A 17:00'
    elif hora >= 17 and hora < 18:
        return '17:00 A 18:00'
    else:
        return None

@st.cache_data
def es_contacto(valor):
    """Determina si un valor es contacto (TODO excepto vacío y OTROS-BUZÓN DE VOZ)"""
    if pd.isna(valor):
        return False
    valor_str = str(valor).upper().strip()
    if valor_str == '' or valor_str == 'OTROS-BUZÓN DE VOZ':
        return False
    return True

@st.cache_data
def es_venta(valor):
    """Determina si un valor es venta (solo VENTA exacto)"""
    if pd.isna(valor):
        return False
    valor_str = str(valor).upper().strip()
    return valor_str == 'VENTA'

@st.cache_data
def leer_archivo(archivo):
    """Lee un archivo Excel o CSV"""
    extension = archivo.name.split('.')[-1].lower()
    
    try:
        if extension == 'csv':
            # Para CSV grandes, leer con chunks
            df = pd.read_csv(archivo, encoding='utf-8-sig', low_memory=False)
        else:
            # Intentar con openpyxl primero, si falla usar xlrd
            try:
                df = pd.read_excel(archivo, engine='openpyxl')
            except:
                df = pd.read_excel(archivo, engine='xlrd')
        
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

@st.cache_data
def limpiar_valor_numerico(valor):
    """Limpia un valor para convertirlo a número"""
    if pd.isna(valor):
        return 0
    
    # Si ya es número
    if isinstance(valor, (int, float)):
        return float(valor) if not pd.isna(valor) else 0
    
    # Si es string, limpiar
    if isinstance(valor, str):
        # Quitar espacios y caracteres no numéricos excepto punto y coma
        valor = valor.strip()
        # Reemplazar comas por puntos (formato europeo)
        valor = valor.replace(',', '.')
        # Extraer solo números y puntos
        valor = re.sub(r'[^0-9.]', '', valor)
        if valor == '':
            return 0
        try:
            return float(valor)
        except:
            return 0
    
    return 0

def procesar_archivo_tiempos(df_tiempos):
    """
    Procesa el archivo de tiempos de agentes y devuelve un diccionario con las horas por agente y rango
    """
    tiempos_dict = {}
    
    # Identificar las columnas de horas
    columnas_horas = [col for col in df_tiempos.columns if ' AM' in col or ' PM' in col]
    
    # Buscar la columna de nombre de usuario
    nombre_col = None
    for col in df_tiempos.columns:
        if 'Nombre' in col or 'nombre' in col.lower():
            nombre_col = col
            break
    
    if not nombre_col:
        # Si no encuentra 'Nombre', buscar 'Nombre de usuario'
        for col in df_tiempos.columns:
            if 'usuario' in col.lower():
                nombre_col = col
                break
    
    if not nombre_col:
        st.warning("No se encontró la columna de nombre de agente en el archivo de tiempos")
        return tiempos_dict
    
    # Procesar cada fila
    for _, row in df_tiempos.iterrows():
        agente = str(row[nombre_col]).strip()
        if not agente or pd.isna(agente):
            continue
        
        # Limpiar nombre del agente
        agente_limpio = agente.replace('"', '').strip()
        
        # Convertir nombre si está en el mapeo
        for key, value in MAPEO_AGENTES.items():
            if key in agente_limpio.upper() or agente_limpio.upper() in key:
                agente_limpio = value
                break
        
        # Procesar cada columna de hora
        for col_hora in columnas_horas:
            # Obtener valor en minutos
            valor = row[col_hora]
            if pd.isna(valor) or valor == 0:
                continue
            
            minutos = limpiar_valor_numerico(valor)
            if minutos == 0:
                continue
            
            # Obtener el rango de hora correspondiente
            rango_hora = HORAS_ARCHIVO.get(col_hora)
            if not rango_hora:
                continue
            
            # Solo nos interesan los rangos de 9 AM a 6 PM
            if rango_hora not in RANGOS_HORA:
                continue
            
            # Acumular minutos
            key = f"{agente_limpio}|{rango_hora}"
            tiempos_dict[key] = tiempos_dict.get(key, 0) + minutos
    
    return tiempos_dict

@st.cache_data
def procesar_datos(df_llamadas, df_tiempos=None, incluir_tiempos=True):
    """Procesa los datos de llamadas y genera el reporte"""
    
    with st.spinner('Procesando datos...'):
        progress_bar = st.progress(0)
        
        # 1. Identificar columnas en llamadas
        columnas = df_llamadas.columns.tolist()
        
        fecha_col = None
        agente_col = None
        disposition_col = None
        
        for col in columnas:
            if 'Fecha' in col and 'inicio' in col:
                fecha_col = col
            if 'agente' in col.lower():
                agente_col = col
            if 'Disposition' in col or 'POSPAGO' in col:
                disposition_col = col
        
        if not fecha_col or not agente_col:
            st.error("No se encontraron las columnas necesarias: 'Fecha y hora inicio' y 'Agente'")
            return None
        
        progress_bar.progress(10)
        
        # 2. Procesar fechas
        df_llamadas['Fecha_Procesada'] = df_llamadas[fecha_col].apply(procesar_fecha)
        df_llamadas = df_llamadas.dropna(subset=['Fecha_Procesada'])
        
        if len(df_llamadas) == 0:
            st.error("No se pudieron procesar fechas válidas. Verifica el formato de fecha.")
            return None
        
        progress_bar.progress(30)
        
        # 3. Extraer hora y rango
        df_llamadas['Hora'] = df_llamadas['Fecha_Procesada'].dt.hour
        df_llamadas['Rango_Hora'] = df_llamadas['Hora'].apply(obtener_rango_hora)
        df_llamadas = df_llamadas.dropna(subset=['Rango_Hora'])
        
        if len(df_llamadas) == 0:
            st.error("No hay registros en el rango de 9:00 a 18:00")
            return None
        
        progress_bar.progress(40)
        
        # 4. Convertir agentes - asegurar que todos sean strings
        df_llamadas['Agente_Nombre'] = df_llamadas[agente_col].apply(convertir_agente)
        # Eliminar filas con agentes nulos
        df_llamadas = df_llamadas.dropna(subset=['Agente_Nombre'])
        # Asegurar que todos los agentes sean strings
        df_llamadas['Agente_Nombre'] = df_llamadas['Agente_Nombre'].astype(str)
        
        progress_bar.progress(50)
        
        # 5. Clasificar contactos y ventas
        if disposition_col:
            df_llamadas['Es_Contacto'] = df_llamadas[disposition_col].apply(es_contacto)
            df_llamadas['Es_Venta'] = df_llamadas[disposition_col].apply(es_venta)
        else:
            df_llamadas['Es_Contacto'] = True
            df_llamadas['Es_Venta'] = False
        
        progress_bar.progress(60)
        
        # 6. Agrupar datos
        agrupado = df_llamadas.groupby(['Agente_Nombre', 'Rango_Hora']).agg({
            'Es_Contacto': ['count', 'sum'],
            'Es_Venta': 'sum'
        }).reset_index()
        
        agrupado.columns = ['AGENTE', 'Rango_Hora', 'Registros', 'Contacto', 'Ventas']
        
        # Asegurar que AGENTE sea string
        agrupado['AGENTE'] = agrupado['AGENTE'].astype(str)
        
        progress_bar.progress(70)
        
        # 7. Obtener lista de agentes
        agentes_disponibles = agrupado['AGENTE'].unique().tolist()
        # Filtrar agentes nulos o vacíos
        agentes_disponibles = [a for a in agentes_disponibles if a and a != 'nan' and a != 'None']
        
        # Ordenar agentes
        agentes_finales = [a for a in AGENTES_ORDER if a in agentes_disponibles]
        agentes_finales.extend([a for a in agentes_disponibles if a not in agentes_finales])
        
        # 8. Crear reporte completo
        reporte_list = []
        
        for agente in agentes_finales:
            for rango in RANGOS_HORA:
                dato = agrupado[(agrupado['AGENTE'] == agente) & (agrupado['Rango_Hora'] == rango)]
                
                if len(dato) > 0:
                    row = dato.iloc[0].copy()
                else:
                    row = pd.Series({
                        'AGENTE': agente,
                        'Rango_Hora': rango,
                        'Registros': 0,
                        'Contacto': 0,
                        'Ventas': 0
                    })
                
                row['Llamadas'] = row['Registros']
                row['Conversión'] = (row['Ventas'] / row['Contacto'] * 100) if row['Contacto'] > 0 else 0
                row['Total conexión'] = 0
                row['VPH'] = 0
                
                reporte_list.append(row)
        
        reporte = pd.DataFrame(reporte_list)
        
        # Asegurar que todas las columnas sean del tipo correcto
        reporte['AGENTE'] = reporte['AGENTE'].astype(str)
        reporte['Rango_Hora'] = reporte['Rango_Hora'].astype(str)
        
        progress_bar.progress(80)
        
        # 9. Procesar tiempos de conexión
        if incluir_tiempos and df_tiempos is not None and len(df_tiempos) > 0:
            try:
                st.info("⏱️ Procesando archivo de tiempos de agentes...")
                
                # Procesar el archivo de tiempos
                tiempos_dict = procesar_archivo_tiempos(df_tiempos)
                
                if tiempos_dict:
                    # Convertir minutos a horas (dividir entre 60)
                    tiempos_dict_horas = {k: v / 60 for k, v in tiempos_dict.items()}
                    
                    # Actualizar reporte
                    for idx, row in reporte.iterrows():
                        key = f"{row['AGENTE']}|{row['Rango_Hora']}"
                        horas = tiempos_dict_horas.get(key, 0)
                        reporte.at[idx, 'Total conexión'] = round(horas, 2)
                        reporte.at[idx, 'VPH'] = round(row['Ventas'] / horas, 2) if horas > 0 else 0
                    
                    st.success(f"✅ Tiempos procesados: {len(tiempos_dict)} combinaciones agente-hora")
                else:
                    st.warning("No se encontraron datos de tiempo en el archivo de conexiones")
                    
            except Exception as e:
                st.warning(f"Error al procesar tiempos: {e}. Continuando sin tiempos.")
        
        progress_bar.progress(90)
        
        # 10. Redondear valores
        reporte['Conversión'] = reporte['Conversión'].round(2)
        reporte['VPH'] = reporte['VPH'].round(2)
        reporte['Total conexión'] = reporte['Total conexión'].round(2)
        
        # 11. Reordenar columnas
        columnas_finales = ['AGENTE', 'Rango_Hora', 'Total conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
        reporte = reporte[columnas_finales]
        
        progress_bar.progress(100)
        
        return reporte

def guardar_excel(reporte):
    """Guarda el reporte en un archivo Excel"""
    output = io.BytesIO()
    
    try:
        # Intentar con openpyxl primero
        try:
            import openpyxl
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                reporte.to_excel(writer, sheet_name='Reporte', index=False)
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets['Reporte']
                for idx, col in enumerate(reporte.columns):
                    max_len = max(reporte[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 50)
        except:
            # Usar xlsxwriter como alternativa
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                reporte.to_excel(writer, sheet_name='Reporte', index=False)
                
                # Ajustar ancho de columnas
                workbook = writer.book
                worksheet = writer.sheets['Reporte']
                for idx, col in enumerate(reporte.columns):
                    max_len = max(reporte[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(idx, idx, min(max_len, 50))
        
        output.seek(0)
        return output
        
    except Exception as e:
        st.error(f"Error al guardar el archivo Excel: {e}")
        # Intentar con formato CSV como fallback
        try:
            csv_output = io.BytesIO()
            reporte.to_csv(csv_output, index=False)
            csv_output.seek(0)
            return csv_output
        except:
            return None

# Interfaz principal
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📁 Carga de archivos")
    
    # Archivo de llamadas
    archivo_llamadas = st.file_uploader(
        "Archivo de llamadas (Excel o CSV)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo con los datos de las llamadas"
    )
    
    # Archivo de tiempos
    archivo_tiempos = st.file_uploader(
        "Archivo de tiempos de agentes (Opcional)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo con los tiempos de conexión por agente y hora"
    )

with col2:
    st.subheader("⚙️ Configuración")
    
    incluir_tiempos = st.checkbox("Incluir tiempos de conexión", value=True, 
                                   help="Incluir horas de conexión en el reporte")
    
    procesar = st.button("🚀 Procesar Datos", type="primary", use_container_width=True)

# Información de columnas
if archivo_llamadas:
    st.info("📋 Columnas requeridas: 'Fecha y hora inicio', 'Agente' y 'Disposition - POSPAGO BAIT'")
    
    # Mostrar primeras filas
    with st.expander("🔍 Ver muestra de datos"):
        try:
            df_muestra = leer_archivo(archivo_llamadas)
            if df_muestra is not None:
                st.write("📊 Muestra de los primeros 5 registros:")
                st.dataframe(df_muestra.head(), use_container_width=True)
                
                st.write("📋 Columnas disponibles:")
                st.code(", ".join(df_muestra.columns.tolist()))
        except Exception as e:
            st.error(f"Error al mostrar muestra: {e}")

# Procesar datos
if procesar and archivo_llamadas:
    try:
        # Leer archivos
        df_llamadas = leer_archivo(archivo_llamadas)
        
        if df_llamadas is not None and len(df_llamadas) > 0:
            st.success(f"✅ Archivo de llamadas cargado: {len(df_llamadas):,} registros")
            
            df_tiempos = None
            if archivo_tiempos and incluir_tiempos:
                df_tiempos = leer_archivo(archivo_tiempos)
                if df_tiempos is not None:
                    st.success(f"✅ Archivo de tiempos cargado: {len(df_tiempos):,} registros")
                    
                    # Mostrar columnas del archivo de tiempos
                    with st.expander("🔍 Ver columnas del archivo de tiempos"):
                        st.write("📋 Columnas disponibles:")
                        st.code(", ".join(df_tiempos.columns.tolist()))
            
            # Procesar datos
            reporte = procesar_datos(df_llamadas, df_tiempos, incluir_tiempos)
            
            if reporte is not None and len(reporte) > 0:
                st.balloons()
                
                # Mostrar estadísticas
                st.subheader("📈 Estadísticas del Reporte")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{len(reporte)}</div>
                            <div class="stat-label">Total Filas</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    total_registros = reporte['Registros'].sum()
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_registros:,}</div>
                            <div class="stat-label">Total Registros</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    total_contactos = reporte['Contacto'].sum()
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_contactos:,}</div>
                            <div class="stat-label">Total Contactos</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    total_ventas = reporte['Ventas'].sum()
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_ventas:,}</div>
                            <div class="stat-label">Total Ventas</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    conversion = (total_ventas / total_contactos * 100) if total_contactos > 0 else 0
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{conversion:.2f}%</div>
                            <div class="stat-label">Conversión Global</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Mostrar tabla
                st.subheader("📊 Reporte de Agentes")
                
                # Obtener lista de agentes únicos y convertir a string
                agentes_unicos = reporte['AGENTE'].unique().tolist()
                agentes_unicos = [str(a) for a in agentes_unicos if a and str(a) != 'nan' and str(a) != 'None']
                agentes_unicos = sorted(agentes_unicos)
                
                if agentes_unicos:
                    agentes = ['Todos'] + agentes_unicos
                    filtro_agente = st.selectbox("Filtrar por agente:", agentes)
                    
                    if filtro_agente != 'Todos':
                        reporte_filtrado = reporte[reporte['AGENTE'] == filtro_agente]
                    else:
                        reporte_filtrado = reporte
                    
                    # Mostrar tabla
                    st.dataframe(
                        reporte_filtrado,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "AGENTE": st.column_config.TextColumn("Agente"),
                            "Rango_Hora": st.column_config.TextColumn("Rango Hora"),
                            "Total conexión": st.column_config.NumberColumn("Total Conexión", format="%.2f"),
                            "Registros": st.column_config.NumberColumn("Registros"),
                            "Llamadas": st.column_config.NumberColumn("Llamadas"),
                            "Contacto": st.column_config.NumberColumn("Contacto"),
                            "Ventas": st.column_config.NumberColumn("Ventas"),
                            "Conversión": st.column_config.NumberColumn("Conversión", format="%.2f%%"),
                            "VPH": st.column_config.NumberColumn("VPH", format="%.2f"),
                        }
                    )
                    
                    # Descargar Excel
                    st.subheader("📥 Descargar Reporte")
                    
                    # Guardar Excel
                    output = guardar_excel(reporte)
                    
                    if output is not None:
                        # Determinar el tipo de archivo
                        try:
                            import openpyxl
                            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            file_ext = "xlsx"
                        except:
                            mime_type = "text/csv"
                            file_ext = "csv"
                        
                        st.download_button(
                            label=f"⬇️ Descargar Reporte (.{file_ext})",
                            data=output,
                            file_name=f"reporte_agentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                            mime=mime_type,
                            use_container_width=True
                        )
                    else:
                        st.error("No se pudo generar el archivo de descarga")
                else:
                    st.warning("No se encontraron agentes en los datos procesados.")
            else:
                st.warning("No se generaron datos. Verifica que el archivo tenga información válida.")
                
    except Exception as e:
        st.error(f"❌ Error al procesar los datos: {str(e)}")
        import traceback
        with st.expander("Ver detalles del error"):
            st.code(traceback.format_exc())

elif procesar and not archivo_llamadas:
    st.warning("⚠️ Por favor, sube al menos el archivo de llamadas")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        <p>📊 Procesador de Llamadas - Desarrollado con Streamlit</p>
        <p>Soporta archivos Excel (.xlsx, .xls) y CSV</p>
    </div>
""", unsafe_allow_html=True)
