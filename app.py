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
    .success-box {
        background: #d4edda;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    .warning-box {
        background: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Título
st.markdown('<div class="main-header"><h1>📊 Procesador de Llamadas</h1><p>Sube tu archivo de llamadas y genera reportes automáticos</p></div>', unsafe_allow_html=True)

# ============================================
# MAPEO DE AGENTES (ACTUALIZADO)
# ============================================
MAPEO_AGENTES = {
    # Códigos de usuario estándar
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
    'ADM-LPRECIADO': 'Leonel Martinez Preciado'
    

    
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

# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================

@st.cache_data
def convertir_agente(agente):
    """Convierte el código del agente a nombre completo"""
    if pd.isna(agente):
        return None
    
    agente_str = str(agente).strip()
    if not agente_str:
        return None
    
    agente_upper = agente_str.upper()
    
    # Buscar coincidencia exacta o parcial en el mapeo
    for key, value in MAPEO_AGENTES.items():
        key_upper = key.upper()
        # Coincidencia exacta
        if agente_upper == key_upper:
            return value
        # Coincidencia parcial (el código está contenido en el nombre o viceversa)
        if key_upper in agente_upper or agente_upper in key_upper:
            return value
    
    # Si no encuentra, devolver el valor original
    return agente_str

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
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%Y-%m-%d',
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
            # Para CSV, leer con diferentes codificaciones
            try:
                df = pd.read_csv(archivo, encoding='utf-8-sig', low_memory=False, dtype=str)
            except:
                df = pd.read_csv(archivo, encoding='latin-1', low_memory=False, dtype=str)
        else:
            # Intentar con openpyxl primero
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
        
        # Buscar columnas que contienen "a. m." o "p. m."
        if 'a. m.' in col_str or 'p. m.' in col_str:
            columnas_horas.append(col)
            continue
        
        # Buscar columnas que contienen "AM" o "PM"
        if ' AM' in col_str or ' PM' in col_str:
            columnas_horas.append(col)
            continue
        
        # Buscar columnas con formato de hora
        if ':' in col_str and re.search(r'\d{1,2}:\d{2}', col_str):
            columnas_horas.append(col)
            continue
        
        # Buscar columnas que son números de hora
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
        '06:00 a. m.': '6:00 A 7:00',
        '07:00 a. m.': '7:00 A 8:00',
        '08:00 a. m.': '8:00 A 9:00',
        '09:00 a. m.': '9:00 A 10:00',
        '10:00 a. m.': '10:00 A 11:00',
        '11:00 a. m.': '11:00 A 12:00',
        '12:00 p. m.': '12:00 A 13:00',
        '01:00 p. m.': '13:00 A 14:00',
        '02:00 p. m.': '14:00 A 15:00',
        '03:00 p. m.': '15:00 A 16:00',
        '04:00 p. m.': '16:00 A 17:00',
        '05:00 p. m.': '17:00 A 18:00',
        '06:00 p. m.': '18:00 A 19:00',
        '07:00 p. m.': '19:00 A 20:00',
        '08:00 p. m.': '20:00 A 21:00',
        '09:00 p. m.': '21:00 A 22:00',
        '10:00 p. m.': '22:00 A 23:00',
        '11:00 p. m.': '23:00 A 0:00',
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
    
    # 1. Mapeo directo
    if col_hora_str in mapeo_directo:
        return mapeo_directo[col_hora_str]
    
    # 2. Buscar por hora numérica
    hora_match = re.search(r'(\d{1,2}):(\d{2})', col_hora_str)
    if hora_match:
        hora = int(hora_match.group(1))
        minuto = int(hora_match.group(2))
        
        es_pm = 'p. m.' in col_hora_str.lower() or 'pm' in col_hora_str.lower()
        es_am = 'a. m.' in col_hora_str.lower() or 'am' in col_hora_str.lower()
        
        if not es_am and not es_pm:
            if hora >= 6 and hora < 12:
                es_am = True
            elif hora >= 12 and hora < 24:
                es_pm = True
                if hora > 12:
                    hora = hora - 12
            elif hora == 0 or hora == 24:
                hora = 12
                es_am = True
        
        if es_pm and hora != 12:
            hora_24 = hora + 12
        elif es_am and hora == 12:
            hora_24 = 0
        else:
            hora_24 = hora if es_am else hora + 12
        
        if 6 <= hora_24 < 24:
            inicio = f"{hora_24:02d}:00"
            fin = f"{(hora_24 + 1):02d}:00"
            return f"{inicio} A {fin}"
    
    # 3. Buscar por número de hora
    try:
        hora_num = float(col_hora_str.replace(',', '.'))
        if 0 <= hora_num <= 24:
            hora_int = int(hora_num)
            inicio = f"{hora_int:02d}:00"
            fin = f"{(hora_int + 1):02d}:00"
            return f"{inicio} A {fin}"
    except:
        pass
    
    return None

def procesar_archivo_tiempos(df_tiempos):
    """Procesa el archivo de tiempos de agentes."""
    tiempos_dict = {}
    
    # Identificar columnas de horas
    columnas_horas = identificar_columnas_horas(df_tiempos)
    
    if not columnas_horas:
        st.warning("No se encontraron columnas de horas en el archivo de tiempos")
        return tiempos_dict
    
    # Buscar columna de Estatus
    estatus_col = None
    for col in df_tiempos.columns:
        col_str = str(col).strip()
        if 'Estatus' in col_str or 'estatus' in col_str.lower():
            estatus_col = col
            break
    
    if not estatus_col:
        st.warning("No se encontró la columna de Estatus en el archivo de tiempos")
        return tiempos_dict
    
    # Buscar columna de nombre
    nombre_col = None
    for col in df_tiempos.columns:
        col_str = str(col).strip()
        if 'Nombre' in col_str:
            nombre_col = col
            break
    
    if not nombre_col:
        st.warning("No se encontró la columna de Nombre en el archivo de tiempos")
        return tiempos_dict
    
    # Filtrar solo filas con Estatus = "TOTAL"
    df_tiempos['Estatus_Str'] = df_tiempos[estatus_col].astype(str).str.upper().str.strip()
    df_total = df_tiempos[df_tiempos['Estatus_Str'] == 'TOTAL']
    
    if len(df_total) == 0:
        st.warning("No se encontraron filas con Estatus = 'TOTAL' en el archivo de tiempos")
        return tiempos_dict
    
    # Procesar cada fila de TOTAL
    for idx, row in df_total.iterrows():
        try:
            agente_val = row[nombre_col]
            if pd.isna(agente_val):
                continue
            
            agente = str(agente_val).strip()
            if not agente or agente == '':
                continue
            
            agente_limpio = agente.replace('"', '').strip()
            agente_convertido = convertir_agente(agente_limpio)
            
            if not agente_convertido:
                continue
            
            # Procesar cada columna de hora
            for col_hora in columnas_horas:
                try:
                    valor = row[col_hora]
                    if pd.isna(valor):
                        continue
                    
                    minutos = limpiar_valor_numerico(valor)
                    if minutos == 0:
                        continue
                    
                    col_hora_str = str(col_hora).strip()
                    rango_hora = mapear_hora_a_rango(col_hora_str)
                    
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
    # Palabras clave para buscar columnas de fecha
    keywords = ['fecha', 'date', 'fech', 'día', 'dia', 'fechahora', 'fecha hora']
    
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in keywords:
            if keyword in col_lower:
                return col
    
    # Si no encuentra, buscar columnas que contengan fechas
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

@st.cache_data
def procesar_datos_por_fecha(df_llamadas, df_tiempos=None, incluir_tiempos=True):
    """Procesa los datos de llamadas y genera el reporte agrupado por fecha"""
    
    with st.spinner('Procesando datos...'):
        progress_bar = st.progress(0)
        
        # 1. Identificar columnas
        columnas = df_llamadas.columns.tolist()
        
        # Identificar columna de fecha
        fecha_col = identificar_columna_fecha(df_llamadas)
        
        # Si no se encontró, buscar por nombre específico
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
        
        if not fecha_col:
            st.error("❌ No se encontró la columna de fecha. Asegúrate de que el archivo contenga una columna con fechas.")
            return None
        
        if not agente_col:
            st.error("❌ No se encontró la columna de agente. Asegúrate de que el archivo contenga una columna de agente/usuario.")
            return None
        
        st.info(f"✅ Columnas identificadas: Fecha='{fecha_col}', Agente='{agente_col}'")
        
        progress_bar.progress(10)
        
        # 2. Procesar fechas
        df_llamadas['Fecha_Procesada'] = df_llamadas[fecha_col].apply(procesar_fecha)
        df_llamadas = df_llamadas.dropna(subset=['Fecha_Procesada'])
        
        if len(df_llamadas) == 0:
            st.error("No se pudieron procesar fechas válidas. Verifica el formato de fecha.")
            return None
        
        # Extraer fecha y hora
        df_llamadas['Fecha_Solo'] = df_llamadas['Fecha_Procesada'].dt.date
        df_llamadas['Hora'] = df_llamadas['Fecha_Procesada'].dt.hour
        df_llamadas['Rango_Hora'] = df_llamadas['Hora'].apply(obtener_rango_hora)
        df_llamadas = df_llamadas.dropna(subset=['Rango_Hora'])
        
        if len(df_llamadas) == 0:
            st.error("No hay registros en el rango de 9:00 a 18:00")
            return None
        
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
        
        # 8. Crear reporte completo con fechas
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
        
        reporte = pd.DataFrame(reporte_list)
        reporte['FECHA'] = pd.to_datetime(reporte['FECHA']).dt.date
        reporte['AGENTE'] = reporte['AGENTE'].astype(str)
        reporte['Rango_Hora'] = reporte['Rango_Hora'].astype(str)
        
        progress_bar.progress(80)
        
        # 9. Procesar tiempos de conexión (si existe)
        if incluir_tiempos and df_tiempos is not None and len(df_tiempos) > 0:
            try:
                tiempos_dict = procesar_archivo_tiempos(df_tiempos)
                
                if tiempos_dict:
                    for idx, row in reporte.iterrows():
                        key = f"{row['AGENTE']}|{row['Rango_Hora']}"
                        horas = tiempos_dict.get(key, 0.0)
                        reporte.at[idx, 'Total conexión'] = round(horas, 2)
                        reporte.at[idx, 'VPH'] = round(row['Ventas'] / horas, 2) if horas > 0 else 0.0
                    
                    st.success(f"✅ Tiempos procesados: {len(tiempos_dict)} combinaciones agente-hora")
            except Exception as e:
                st.warning(f"Error al procesar tiempos: {e}. Continuando sin tiempos.")
        
        progress_bar.progress(90)
        
        # 10. Redondear valores
        reporte['Conversión'] = reporte['Conversión'].round(2)
        reporte['VPH'] = reporte['VPH'].round(2)
        reporte['Total conexión'] = reporte['Total conexión'].round(2)
        
        # 11. Reordenar columnas
        columnas_finales = ['FECHA', 'AGENTE', 'Rango_Hora', 'Total conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
        reporte = reporte[columnas_finales]
        
        progress_bar.progress(100)
        
        return reporte

def guardar_excel(reporte):
    """Guarda el reporte en un archivo Excel"""
    output = io.BytesIO()
    
    try:
        try:
            import openpyxl
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                reporte.to_excel(writer, sheet_name='Reporte', index=False)
                
                worksheet = writer.sheets['Reporte']
                for idx, col in enumerate(reporte.columns):
                    max_len = max(reporte[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 50)
        except:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                reporte.to_excel(writer, sheet_name='Reporte', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Reporte']
                for idx, col in enumerate(reporte.columns):
                    max_len = max(reporte[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(idx, idx, min(max_len, 50))
        
        output.seek(0)
        return output
        
    except Exception as e:
        st.error(f"Error al guardar el archivo Excel: {e}")
        try:
            csv_output = io.BytesIO()
            reporte.to_csv(csv_output, index=False)
            csv_output.seek(0)
            return csv_output
        except:
            return None

# ============================================
# INTERFAZ PRINCIPAL
# ============================================

# Configuración de la interfaz
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
            
            # Mostrar información del archivo
            with st.expander("🔍 Ver estructura del archivo de llamadas"):
                st.write("📋 Columnas disponibles:")
                st.code(", ".join(df_llamadas.columns.tolist()))
                st.write("📊 Muestra de los primeros 5 registros:")
                st.dataframe(df_llamadas.head(), use_container_width=True)
            
            df_tiempos = None
            if archivo_tiempos and incluir_tiempos:
                df_tiempos = leer_archivo(archivo_tiempos)
                if df_tiempos is not None:
                    st.success(f"✅ Archivo de tiempos cargado: {len(df_tiempos):,} registros")
                    
                    with st.expander("🔍 Ver estructura del archivo de tiempos"):
                        st.write("📋 Columnas disponibles:")
                        st.code(", ".join(df_tiempos.columns.tolist()))
                        st.write("📊 Muestra de los primeros 5 registros:")
                        st.dataframe(df_tiempos.head(), use_container_width=True)
            
            # Procesar datos con fechas
            reporte = procesar_datos_por_fecha(df_llamadas, df_tiempos, incluir_tiempos)
            
            if reporte is not None and len(reporte) > 0:
                st.balloons()
                
                # ============================================
                # ESTADÍSTICAS GENERALES
                # ============================================
                st.subheader("📈 Estadísticas del Reporte")
                
                fechas_disponibles = sorted(reporte['FECHA'].unique())
                total_dias = len(fechas_disponibles)
                
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{total_dias}</div>
                            <div class="stat-label">Días</div>
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
                
                with col6:
                    promedio_diario = total_registros / total_dias if total_dias > 0 else 0
                    st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-number">{promedio_diario:.1f}</div>
                            <div class="stat-label">Promedio Diario</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # ============================================
                # FILTROS Y VISUALIZACIÓN
                # ============================================
                st.subheader("📊 Reporte por Fecha y Agente")
                
                col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                
                with col_filtro1:
                    fechas_opciones = ['Todas'] + [f.strftime('%Y-%m-%d') for f in fechas_disponibles]
                    filtro_fecha = st.selectbox("📅 Filtrar por fecha:", fechas_opciones)
                
                with col_filtro2:
                    agentes_unicos = [str(a) for a in reporte['AGENTE'].unique() if a and str(a) != 'nan' and str(a) != 'None']
                    agentes_unicos = sorted(agentes_unicos)
                    agentes_opciones = ['Todos'] + agentes_unicos
                    filtro_agente = st.selectbox("👤 Filtrar por agente:", agentes_opciones)
                
                with col_filtro3:
                    mostrar_resumen = st.checkbox("📊 Mostrar resumen por fecha", value=True)
                
                # Aplicar filtros
                reporte_filtrado = reporte.copy()
                
                if filtro_fecha != 'Todas':
                    fecha_filtro = datetime.strptime(filtro_fecha, '%Y-%m-%d').date()
                    reporte_filtrado = reporte_filtrado[reporte_filtrado['FECHA'] == fecha_filtro]
                
                if filtro_agente != 'Todos':
                    reporte_filtrado = reporte_filtrado[reporte_filtrado['AGENTE'] == filtro_agente]
                
                # ============================================
                # RESUMEN POR FECHA
                # ============================================
                if mostrar_resumen:
                    st.subheader("📊 Resumen por Fecha")
                    
                    resumen_fecha = reporte_filtrado.groupby('FECHA').agg({
                        'Registros': 'sum',
                        'Contacto': 'sum',
                        'Ventas': 'sum'
                    }).reset_index()
                    
                    resumen_fecha['Conversión'] = (resumen_fecha['Ventas'] / resumen_fecha['Contacto'] * 100).round(2)
                    resumen_fecha['FECHA'] = resumen_fecha['FECHA'].astype(str)
                    
                    st.dataframe(
                        resumen_fecha,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "FECHA": st.column_config.TextColumn("Fecha"),
                            "Registros": st.column_config.NumberColumn("Registros"),
                            "Contacto": st.column_config.NumberColumn("Contactos"),
                            "Ventas": st.column_config.NumberColumn("Ventas"),
                            "Conversión": st.column_config.NumberColumn("Conversión", format="%.2f%%"),
                        }
                    )
                
                # ============================================
                # DETALLE COMPLETO
                # ============================================
                st.subheader("📋 Detalle por Agente y Hora")
                
                st.dataframe(
                    reporte_filtrado,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "FECHA": st.column_config.TextColumn("Fecha"),
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
                
                # ============================================
                # DESCARGA DE REPORTE
                # ============================================
                st.subheader("📥 Descargar Reporte")
                
                output = guardar_excel(reporte)
                
                if output is not None:
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
                        file_name=f"reporte_agentes_por_fecha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                        mime=mime_type,
                        use_container_width=True
                    )
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
        <p>✨ Ahora con agrupación por fecha y mapeo mejorado de agentes</p>
    </div>
""", unsafe_allow_html=True)
