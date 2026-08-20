import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

# ============================================
# MAPEO DE AGENTES
# ============================================
MAPEO_AGENTES = {
    'BMG_GYHV':'Greisi Yenifer Hernandez Valenzuela',
    'BMG_LPVH':'Lorenys Patricia Villarroel Hernandez',
    'BT-CREBECA': 'Rebeca Carmona Martell',
    'BT-ERUIZ': 'Emmanuel Ruiz Vera',
    'BT-KGUTIERREZ': 'Kaelan Andre Gutierrez Gonzalez',
    'AVILLALBA': 'Astrid Milena Villalba Gómez',
    'BMAURERA':'Barbara Camila	Maurera campos',
    'BT-AEDUARDO': 'Eduardo Abasolo Reyes',
    'JSGARCIA': 'Joaly Scarlet Garcia Noguera',
    'MRODRIGUEZ': 'Meyling Yamilet Rodríguez',
    'TKM-2701': 'Ana Karen Padilla Martinez',
    'ZHERNANDEZ': 'Zara Stephanie Hernández Díaz',
    'BT-FALCANTARA':'Fergie Zoe Alcantara García',
    'AEGUTIERREZ': 'Angel Erubiel Gutierrez Martinez',
    'BABUNDIS':'Bryan Abundis Romo',
    'CVIVEROS':'Carlos Alexis Viveros Garcia',
    'DAPEREZ': 'Daniel Alejandro Perez Rivera',
    'GORTEGA':'Guadalupe Ortega Perez',
    'RPYANEZ': 'Roberto Patricio Yañez Bajonero',
    'ADM-LPRECIADO': 'Leonel Martinez Preciado',
    'BMG_VVPS':'Vanessa Valentina Pinto Salinas',
    'JLSANCHEZ': 'Jorge Luis Sanchez Becerril'

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

# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================

@st.cache_data
def convertir_agente(agente):
    """Convierte el código del agente a nombre completo"""
    if pd.isna(agente):
        return None
    agente_str = str(agente).strip()
    agente_upper = agente_str.upper()
    
    for key, value in MAPEO_AGENTES.items():
        if key.upper() in agente_upper or agente_upper in key.upper():
            return value
    
    return agente_str

@st.cache_data
def procesar_fecha(fecha_str):
    """Procesa la fecha en diferentes formatos"""
    if pd.isna(fecha_str):
        return None
    
    try:
        if isinstance(fecha_str, str):
            fecha_str = fecha_str.replace('a. m.', 'AM').replace('p. m.', 'PM')
            fecha_str = fecha_str.replace('a.m.', 'AM').replace('p.m.', 'PM')
            
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
            
            try:
                from dateutil import parser
                return parser.parse(fecha_str)
            except:
                pass
        
        if isinstance(fecha_str, datetime):
            return fecha_str
            
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
    """Determina si un valor es contacto"""
    if pd.isna(valor):
        return False
    valor_str = str(valor).upper().strip()
    if valor_str == '' or valor_str == 'OTROS-BUZÓN DE VOZ':
        return False
    return True

@st.cache_data
def es_venta(valor):
    """Determina si un valor es venta"""
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
            try:
                df = pd.read_csv(archivo, encoding='utf-8-sig', low_memory=False, dtype=str)
            except:
                df = pd.read_csv(archivo, encoding='latin-1', low_memory=False, dtype=str)
        else:
            try:
                df = pd.read_excel(archivo, engine='openpyxl', dtype=str)
            except:
                df = pd.read_excel(archivo, engine='xlrd', dtype=str)
        
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

@st.cache_data
def limpiar_valor_numerico(valor):
    """Limpia un valor para convertirlo a número flotante"""
    if pd.isna(valor):
        return 0.0
    
    if isinstance(valor, (int, float)):
        return float(valor)
    
    if isinstance(valor, str):
        valor = valor.strip()
        if valor == '':
            return 0.0
        
        valor = valor.replace(',', '.')
        valor = re.sub(r'[^0-9.]', '', valor)
        if valor == '':
            return 0.0
        
        try:
            return float(valor)
        except:
            return 0.0
    
    return 0.0

def identificar_columnas_horas(df_tiempos):
    """Identifica las columnas de horas en el DataFrame"""
    columnas_horas = []
    
    for col in df_tiempos.columns:
        col_str = str(col).strip()
        
        if 'a. m.' in col_str or 'p. m.' in col_str:
            columnas_horas.append(col)
            continue
        
        if ' AM' in col_str or ' PM' in col_str:
            columnas_horas.append(col)
            continue
        
        if ':' in col_str and re.search(r'\d{1,2}:\d{2}', col_str):
            columnas_horas.append(col)
            continue
        
        try:
            num = float(col_str.replace(',', '.'))
            if 0 <= num <= 24:
                columnas_horas.append(col)
                continue
        except:
            pass
    
    return columnas_horas

def mapear_hora_a_rango(col_hora_str):
    """Convierte el nombre de la columna de hora a un rango estándar"""
    col_hora_str = col_hora_str.strip()
    
    mapeo_directo = {
        '09:00 a. m.': '9:00 A 10:00',
        '10:00 a. m.': '10:00 A 11:00',
        '11:00 a. m.': '11:00 A 12:00',
        '12:00 p. m.': '12:00 A 13:00',
        '01:00 p. m.': '13:00 A 14:00',
        '02:00 p. m.': '14:00 A 15:00',
        '03:00 p. m.': '15:00 A 16:00',
        '04:00 p. m.': '16:00 A 17:00',
        '05:00 p. m.': '17:00 A 18:00',
        '9 AM': '9:00 A 10:00',
        '10 AM': '10:00 A 11:00',
        '11 AM': '11:00 A 12:00',
        '12 PM': '12:00 A 13:00',
        '1 PM': '13:00 A 14:00',
        '2 PM': '14:00 A 15:00',
        '3 PM': '15:00 A 16:00',
        '4 PM': '16:00 A 17:00',
        '5 PM': '17:00 A 18:00',
    }
    
    if col_hora_str in mapeo_directo:
        return mapeo_directo[col_hora_str]
    
    hora_match = re.search(r'(\d{1,2}):(\d{2})', col_hora_str)
    if hora_match:
        hora = int(hora_match.group(1))
        
        es_pm = 'p. m.' in col_hora_str.lower() or 'pm' in col_hora_str.lower()
        es_am = 'a. m.' in col_hora_str.lower() or 'am' in col_hora_str.lower()
        
        if es_pm and hora != 12:
            hora_24 = hora + 12
        elif es_am and hora == 12:
            hora_24 = 0
        else:
            hora_24 = hora if es_am else hora + 12
        
        if 9 <= hora_24 <= 17:
            inicio = f"{hora_24:02d}:00"
            fin = f"{(hora_24 + 1):02d}:00"
            return f"{inicio} A {fin}"
    
    return None

def procesar_archivo_tiempos(df_tiempos):
    """Procesa el archivo de tiempos de agentes."""
    tiempos_dict = {}
    
    columnas_horas = identificar_columnas_horas(df_tiempos)
    
    if not columnas_horas:
        st.warning("No se encontraron columnas de horas en el archivo de tiempos")
        return tiempos_dict
    
    estatus_col = None
    for col in df_tiempos.columns:
        col_str = str(col).strip()
        if 'Estatus' in col_str or 'estatus' in col_str.lower():
            estatus_col = col
            break
    
    if not estatus_col:
        st.warning("No se encontró la columna de Estatus en el archivo de tiempos")
        return tiempos_dict
    
    nombre_col = None
    for col in df_tiempos.columns:
        col_str = str(col).strip()
        if 'Nombre' in col_str:
            nombre_col = col
            break
    
    if not nombre_col:
        st.warning("No se encontró la columna de Nombre en el archivo de tiempos")
        return tiempos_dict
    
    df_tiempos['Estatus_Str'] = df_tiempos[estatus_col].astype(str).str.upper().str.strip()
    df_total = df_tiempos[df_tiempos['Estatus_Str'] == 'TOTAL']
    
    if len(df_total) == 0:
        st.warning("No se encontraron filas con Estatus = 'TOTAL' en el archivo de tiempos")
        return tiempos_dict
    
    for idx, row in df_total.iterrows():
        try:
            agente_val = row[nombre_col]
            if pd.isna(agente_val):
                continue
            
            agente = str(agente_val).strip()
            if not agente:
                continue
            
            agente_convertido = convertir_agente(agente)
            
            if not agente_convertido:
                continue
            
            for col_hora in columnas_horas:
                try:
                    valor = row[col_hora]
                    if pd.isna(valor):
                        continue
                    
                    minutos = limpiar_valor_numerico(valor)
                    if minutos == 0:
                        continue
                    
                    rango_hora = mapear_hora_a_rango(str(col_hora).strip())
                    
                    if not rango_hora:
                        continue
                    
                    if rango_hora not in RANGOS_HORA:
                        continue
                    
                    key = f"{agente_convertido}|{rango_hora}"
                    tiempos_dict[key] = round(minutos / 60.0, 4)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            continue
    
    return tiempos_dict

def identificar_columna_fecha(df):
    """Identifica automáticamente la columna de fecha"""
    keywords = ['fecha', 'date', 'fech', 'día', 'dia']
    
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in keywords:
            if keyword in col_lower:
                return col
    
    for col in df.columns:
        try:
            sample = df[col].dropna().head(5)
            converted = 0
            for val in sample:
                if procesar_fecha(val) is not None:
                    converted += 1
            if converted >= 3:
                return col
        except:
            continue
    
    return None

def generar_resumen_consolidado(reporte_detalle):
    """
    Genera un resumen consolidado por fecha y hora con las columnas:
    HC, Hrs conexión, Registros, Llamadas, Contacto, Ventas, Conversión, VPH
    """
    if reporte_detalle is None or len(reporte_detalle) == 0:
        return None
    
    # Agrupar por FECHA y Rango_Hora
    resumen = reporte_detalle.groupby(['FECHA', 'Rango_Hora']).agg({
        'AGENTE': 'nunique',  # HC = número de agentes únicos
        'Total conexión': 'sum',  # Suma de horas de conexión
        'Registros': 'sum',
        'Llamadas': 'sum',
        'Contacto': 'sum',
        'Ventas': 'sum'
    }).reset_index()
    
    # Renombrar columnas
    resumen.columns = ['FECHA', 'Rango_Hora', 'HC', 'Hrs conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas']
    
    # Calcular Conversión y VPH
    resumen['Conversión'] = (resumen['Ventas'] / resumen['Contacto'] * 100).round(2)
    resumen['VPH'] = (resumen['Ventas'] / resumen['Hrs conexión']).round(2)
    
    # Reemplazar infinitos y NaN
    resumen['Conversión'] = resumen['Conversión'].fillna(0).replace([np.inf, -np.inf], 0)
    resumen['VPH'] = resumen['VPH'].fillna(0).replace([np.inf, -np.inf], 0)
    
    # Formatear Conversión como porcentaje
    resumen['Conversión'] = resumen['Conversión'].apply(lambda x: f"{x}%")
    
    # Reordenar columnas
    columnas_orden = ['FECHA', 'Rango_Hora', 'HC', 'Hrs conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
    resumen = resumen[columnas_orden]
    
    # Ordenar por fecha y hora
    resumen = resumen.sort_values(['FECHA', 'Rango_Hora'])
    
    return resumen

@st.cache_data
def procesar_datos_completos(df_llamadas, df_tiempos=None, incluir_tiempos=True):
    """Procesa los datos y genera el reporte detallado y el resumen consolidado"""
    
    with st.spinner('Procesando datos...'):
        progress_bar = st.progress(0)
        
        # 1. Identificar columnas
        columnas = df_llamadas.columns.tolist()
        
        fecha_col = identificar_columna_fecha(df_llamadas)
        
        if not fecha_col:
            for col in columnas:
                if 'Fecha' in col and 'inicio' in col:
                    fecha_col = col
                    break
        
        agente_col = None
        disposition_col = None
        
        for col in columnas:
            if col != fecha_col and ('agente' in col.lower() or 'usuario' in col.lower()):
                agente_col = col
            if 'Disposition' in col or 'POSPAGO' in col or 'Resultado' in col:
                disposition_col = col
        
        if not fecha_col or not agente_col:
            st.error("No se encontraron las columnas necesarias: 'Fecha' y 'Agente'")
            return None, None
        
        progress_bar.progress(10)
        
        # 2. Procesar fechas
        df_llamadas['Fecha_Procesada'] = df_llamadas[fecha_col].apply(procesar_fecha)
        df_llamadas = df_llamadas.dropna(subset=['Fecha_Procesada'])
        
        if len(df_llamadas) == 0:
            st.error("No se pudieron procesar fechas válidas.")
            return None, None
        
        df_llamadas['Fecha_Solo'] = df_llamadas['Fecha_Procesada'].dt.date
        df_llamadas['Hora'] = df_llamadas['Fecha_Procesada'].dt.hour
        df_llamadas['Rango_Hora'] = df_llamadas['Hora'].apply(obtener_rango_hora)
        df_llamadas = df_llamadas.dropna(subset=['Rango_Hora'])
        
        if len(df_llamadas) == 0:
            st.error("No hay registros en el rango de 9:00 a 18:00")
            return None, None
        
        progress_bar.progress(30)
        
        # 3. Convertir agentes
        df_llamadas['Agente_Nombre'] = df_llamadas[agente_col].apply(convertir_agente)
        df_llamadas = df_llamadas.dropna(subset=['Agente_Nombre'])
        df_llamadas['Agente_Nombre'] = df_llamadas['Agente_Nombre'].astype(str)
        
        progress_bar.progress(50)
        
        # 4. Clasificar contactos y ventas
        if disposition_col:
            df_llamadas['Es_Contacto'] = df_llamadas[disposition_col].apply(es_contacto)
            df_llamadas['Es_Venta'] = df_llamadas[disposition_col].apply(es_venta)
        else:
            df_llamadas['Es_Contacto'] = True
            df_llamadas['Es_Venta'] = False
        
        progress_bar.progress(60)
        
        # 5. Obtener lista de fechas disponibles
        fechas_disponibles = sorted(df_llamadas['Fecha_Solo'].unique())
        
        # 6. Agrupar por fecha, agente y rango de hora
        agrupado = df_llamadas.groupby(['Fecha_Solo', 'Agente_Nombre', 'Rango_Hora']).agg({
            'Es_Contacto': ['count', 'sum'],
            'Es_Venta': 'sum'
        }).reset_index()
        
        agrupado.columns = ['FECHA', 'AGENTE', 'Rango_Hora', 'Registros', 'Contacto', 'Ventas']
        agrupado['AGENTE'] = agrupado['AGENTE'].astype(str)
        
        progress_bar.progress(70)
        
        # 7. Obtener lista de agentes
        agentes_disponibles = agrupado['AGENTE'].unique().tolist()
        agentes_disponibles = [a for a in agentes_disponibles if a and a != 'nan' and a != 'None']
        
        agentes_finales = [a for a in AGENTES_ORDER if a in agentes_disponibles]
        agentes_finales.extend([a for a in agentes_disponibles if a not in agentes_finales])
        
        # 8. Crear reporte detallado
        reporte_list = []
        
        for fecha in fechas_disponibles:
            for agente in agentes_finales:
                for rango in RANGOS_HORA:
                    dato = agrupado[
                        (agrupado['FECHA'] == fecha) & 
                        (agrupado['AGENTE'] == agente) & 
                        (agrupado['Rango_Hora'] == rango)
                    ]
                    
                    if len(dato) > 0:
                        row = dato.iloc[0].copy()
                    else:
                        row = pd.Series({
                            'FECHA': fecha,
                            'AGENTE': agente,
                            'Rango_Hora': rango,
                            'Registros': 0,
                            'Contacto': 0,
                            'Ventas': 0
                        })
                    
                    row['Llamadas'] = row['Registros']
                    row['Conversión'] = (row['Ventas'] / row['Contacto'] * 100) if row['Contacto'] > 0 else 0
                    row['Total conexión'] = 0.0
                    row['VPH'] = 0.0
                    
                    reporte_list.append(row)
        
        reporte_detalle = pd.DataFrame(reporte_list)
        reporte_detalle['FECHA'] = pd.to_datetime(reporte_detalle['FECHA']).dt.date
        reporte_detalle['AGENTE'] = reporte_detalle['AGENTE'].astype(str)
        reporte_detalle['Rango_Hora'] = reporte_detalle['Rango_Hora'].astype(str)
        
        progress_bar.progress(80)
        
        # 9. Procesar tiempos de conexión
        if incluir_tiempos and df_tiempos is not None and len(df_tiempos) > 0:
            try:
                tiempos_dict = procesar_archivo_tiempos(df_tiempos)
                
                if tiempos_dict:
                    for idx, row in reporte_detalle.iterrows():
                        key = f"{row['AGENTE']}|{row['Rango_Hora']}"
                        horas = tiempos_dict.get(key, 0.0)
                        reporte_detalle.at[idx, 'Total conexión'] = round(horas, 2)
                        reporte_detalle.at[idx, 'VPH'] = round(row['Ventas'] / horas, 2) if horas > 0 else 0.0
                    
                    st.success(f"✅ Tiempos procesados: {len(tiempos_dict)} combinaciones agente-hora")
            except Exception as e:
                st.warning(f"Error al procesar tiempos: {e}. Continuando sin tiempos.")
        
        progress_bar.progress(90)
        
        # 10. Redondear valores
        reporte_detalle['Conversión'] = reporte_detalle['Conversión'].round(2)
        reporte_detalle['VPH'] = reporte_detalle['VPH'].round(2)
        reporte_detalle['Total conexión'] = reporte_detalle['Total conexión'].round(2)
        
        # 11. Reordenar columnas del detalle
        columnas_detalle = ['FECHA', 'AGENTE', 'Rango_Hora', 'Total conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
        reporte_detalle = reporte_detalle[columnas_detalle]
        
        # 12. Generar resumen consolidado
        reporte_resumen = generar_resumen_consolidado(reporte_detalle)
        
        progress_bar.progress(100)
        
        return reporte_detalle, reporte_resumen

def guardar_excel_completo(reporte_detalle, reporte_resumen):
    """Guarda el reporte detallado y el resumen en un archivo Excel con dos hojas"""
    output = io.BytesIO()
    
    try:
        try:
            import openpyxl
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja 1: Detalle por agente
                reporte_detalle.to_excel(writer, sheet_name='Detalle_Agentes', index=False)
                
                # Hoja 2: Resumen consolidado
                if reporte_resumen is not None:
                    reporte_resumen.to_excel(writer, sheet_name='Resumen_Consolidado', index=False)
                
                # Ajustar ancho de columnas para ambas hojas
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for idx, col in enumerate(writer.sheets[sheet_name].iter_cols(max_col=len(reporte_detalle.columns))):
                        max_len = 0
                        col_letter = chr(65 + idx)
                        for cell in col:
                            try:
                                if len(str(cell.value)) > max_len:
                                    max_len = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_len + 2, 50)
                        worksheet.column_dimensions[col_letter].width = adjusted_width
        except:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                reporte_detalle.to_excel(writer, sheet_name='Detalle_Agentes', index=False)
                
                if reporte_resumen is not None:
                    reporte_resumen.to_excel(writer, sheet_name='Resumen_Consolidado', index=False)
                
                workbook = writer.book
                
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for idx, col in enumerate(reporte_detalle.columns):
                        max_len = max(reporte_detalle[col].astype(str).str.len().max(), len(col)) + 2
                        worksheet.set_column(idx, idx, min(max_len, 50))
        
        output.seek(0)
        return output
        
    except Exception as e:
        st.error(f"Error al guardar el archivo Excel: {e}")
        return None

# ============================================
# INTERFAZ PRINCIPAL
# ============================================

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📁 Carga de archivos")
    
    archivo_llamadas = st.file_uploader(
        "Archivo de llamadas (Excel o CSV)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo con los datos de las llamadas"
    )
    
    archivo_tiempos = st.file_uploader(
        "Archivo de tiempos de agentes (Opcional)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo con los tiempos de conexión por agente y hora"
    )

with col2:
    st.subheader("⚙️ Configuración")
    
    incluir_tiempos = st.checkbox("Incluir tiempos de conexión", value=True)
    
    procesar = st.button("🚀 Procesar Datos", type="primary", use_container_width=True)

# ============================================
# PROCESAMIENTO DE DATOS
# ============================================

if procesar and archivo_llamadas:
    try:
        df_llamadas = leer_archivo(archivo_llamadas)
        
        if df_llamadas is not None and len(df_llamadas) > 0:
            st.success(f"✅ Archivo de llamadas cargado: {len(df_llamadas):,} registros")
            
            df_tiempos = None
            if archivo_tiempos and incluir_tiempos:
                df_tiempos = leer_archivo(archivo_tiempos)
                if df_tiempos is not None:
                    st.success(f"✅ Archivo de tiempos cargado: {len(df_tiempos):,} registros")
            
            # Procesar datos
            reporte_detalle, reporte_resumen = procesar_datos_completos(df_llamadas, df_tiempos, incluir_tiempos)
            
            if reporte_detalle is not None and len(reporte_detalle) > 0:
                st.balloons()
                
                # ============================================
                # ESTADÍSTICAS GENERALES
                # ============================================
                st.subheader("📈 Estadísticas del Reporte")
                
                fechas_disponibles = sorted(reporte_detalle['FECHA'].unique())
                total_dias = len(fechas_disponibles)
                agentes_unicos = reporte_detalle['AGENTE'].nunique()
                
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_dias}</div>
                            <div class="stat-label">Días</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{agentes_unicos}</div>
                            <div class="stat-label">Agentes</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    total_registros = reporte_detalle['Registros'].sum()
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_registros:,}</div>
                            <div class="stat-label">Total Registros</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    total_contactos = reporte_detalle['Contacto'].sum()
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_contactos:,}</div>
                            <div class="stat-label">Total Contactos</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    total_ventas = reporte_detalle['Ventas'].sum()
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_ventas:,}</div>
                            <div class="stat-label">Total Ventas</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col6:
                    conversion = (total_ventas / total_contactos * 100) if total_contactos > 0 else 0
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{conversion:.2f}%</div>
                            <div class="stat-label">Conversión Global</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # ============================================
                # RESUMEN CONSOLIDADO (HC por fecha y hora)
                # ============================================
                if reporte_resumen is not None and len(reporte_resumen) > 0:
                    st.subheader("📊 Resumen Consolidado por Fecha y Hora")
                    st.info("HC = Número de agentes que trabajaron en esa hora")
                    
                    # Filtro de fecha para el resumen
                    fechas_opciones = ['Todas'] + [f.strftime('%Y-%m-%d') for f in fechas_disponibles]
                    filtro_fecha_resumen = st.selectbox("📅 Filtrar resumen por fecha:", fechas_opciones, key="filtro_resumen")
                    
                    resumen_filtrado = reporte_resumen.copy()
                    if filtro_fecha_resumen != 'Todas':
                        fecha_filtro = datetime.strptime(filtro_fecha_resumen, '%Y-%m-%d').date()
                        resumen_filtrado = resumen_filtrado[resumen_filtrado['FECHA'] == fecha_filtro]
                    
                    st.dataframe(
                        resumen_filtrado,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "FECHA": st.column_config.TextColumn("Fecha"),
                            "Rango_Hora": st.column_config.TextColumn("Hora"),
                            "HC": st.column_config.NumberColumn("HC", help="Número de agentes"),
                            "Hrs conexión": st.column_config.NumberColumn("Hrs Conexión", format="%.2f"),
                            "Registros": st.column_config.NumberColumn("Registros"),
                            "Llamadas": st.column_config.NumberColumn("Llamadas"),
                            "Contacto": st.column_config.NumberColumn("Contactos"),
                            "Ventas": st.column_config.NumberColumn("Ventas"),
                            "Conversión": st.column_config.TextColumn("Conversión"),
                            "VPH": st.column_config.NumberColumn("VPH", format="%.2f"),
                        }
                    )
                
                # ============================================
                # DETALLE POR AGENTE
                # ============================================
                st.subheader("📋 Detalle por Agente")
                
                col_filtro1, col_filtro2 = st.columns(2)
                
                with col_filtro1:
                    fechas_opciones_detalle = ['Todas'] + [f.strftime('%Y-%m-%d') for f in fechas_disponibles]
                    filtro_fecha_detalle = st.selectbox("📅 Filtrar detalle por fecha:", fechas_opciones_detalle, key="filtro_detalle")
                
                with col_filtro2:
                    agentes_opciones = ['Todos'] + sorted([str(a) for a in reporte_detalle['AGENTE'].unique() if a and str(a) != 'nan'])
                    filtro_agente = st.selectbox("👤 Filtrar por agente:", agentes_opciones)
                
                detalle_filtrado = reporte_detalle.copy()
                
                if filtro_fecha_detalle != 'Todas':
                    fecha_filtro = datetime.strptime(filtro_fecha_detalle, '%Y-%m-%d').date()
                    detalle_filtrado = detalle_filtrado[detalle_filtrado['FECHA'] == fecha_filtro]
                
                if filtro_agente != 'Todos':
                    detalle_filtrado = detalle_filtrado[detalle_filtrado['AGENTE'] == filtro_agente]
                
                st.dataframe(
                    detalle_filtrado,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "FECHA": st.column_config.TextColumn("Fecha"),
                        "AGENTE": st.column_config.TextColumn("Agente"),
                        "Rango_Hora": st.column_config.TextColumn("Hora"),
                        "Total conexión": st.column_config.NumberColumn("Total Conexión", format="%.2f"),
                        "Registros": st.column_config.NumberColumn("Registros"),
                        "Llamadas": st.column_config.NumberColumn("Llamadas"),
                        "Contacto": st.column_config.NumberColumn("Contacto"),
                        "Ventas": st.column_config.NumberColumn("Ventas"),
                        "Conversión": st.column_config.NumberColumn("Conversión", format="%.2f%%"),
                        "VPH": st.column_config.NumberColumn("VPH", format="%.2f"),
                    }
                )
                
                # ============================================
                # DESCARGA DE REPORTE
                # ============================================
                st.subheader("📥 Descargar Reporte")
                
                output = guardar_excel_completo(reporte_detalle, reporte_resumen)
                
                if output is not None:
                    try:
                        import openpyxl
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        file_ext = "xlsx"
                    except:
                        mime_type = "text/csv"
                        file_ext = "csv"
                    
                    st.download_button(
                        label=f"⬇️ Descargar Reporte Completo (.{file_ext})",
                        data=output,
                        file_name=f"reporte_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                        mime=mime_type,
                        use_container_width=True
                    )
                    
                    st.info("📄 El archivo Excel contiene dos hojas:\n- **Detalle_Agentes**: Desglose por agente, fecha y hora\n- **Resumen_Consolidado**: Resumen por fecha y hora con HC (número de agentes)")
                else:
                    st.error("No se pudo generar el archivo de descarga")
            else:
                st.warning("No se generaron datos. Verifica que el archivo tenga información válida.")
                
    except Exception as e:
        st.error(f"❌ Error al procesar los datos: {str(e)}")
        import traceback
        with st.expander("Ver detalles del error"):
            st.code(traceback.format_exc())

elif procesar and not archivo_llamadas:
    st.warning("⚠️ Por favor, sube al menos el archivo de llamadas")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        <p>📊 Procesador de Llamadas - Desarrollado con Streamlit</p>
        <p>Soporta archivos Excel (.xlsx, .xls) y CSV</p>
        <p>✨ Incluye resumen consolidado con HC (número de agentes por hora)</p>
    </div>
""", unsafe_allow_html=True)
