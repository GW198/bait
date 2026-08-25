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
st.markdown('<div class="main-header"><h1>📊 Procesador de Llamadas</h1></div>', unsafe_allow_html=True)

# ============================================
# MAPEO DE AGENTES CON CAMPAÑA Y SITE
# ============================================
MAPEO_AGENTES = {
    'BMG_GYHV':'Greisi Yenifer Hernandez Valenzuela',
    'BMG_LPVH':'Lorenys Patricia Villarroel Hernandez',
    'BT-CREBECA': 'Rebeca Carmona Martell',
    'BT-ERUIZ': 'Emmanuel Ruiz Vera',
    'BT-KGUTIERREZ': 'Kaelan Andre Gutierrez Gonzalez',
    'AVILLALBA': 'Astrid Milena Villalba Gómez',
    'BMAURERA':'Barbara Camila Maurera campos',
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
    'JLSANCHEZ': 'Jorge Luis Sanchez Becerril',
}

# ============================================
# CONFIGURACIÓN DE CAMPAÑA Y SITE POR AGENTE
# ============================================
AGENTE_CAMPANA_SITE = {
    'Rebeca Carmona Martell': {
        'Campaña': 'Portabilidad',
        'SITE': 'México'
    },
    'Eduardo Reyes Abasolo': {
        'Campaña': 'Portabilidad',
        'SITE': 'México'
    },
    'Kaelan Andre Gutierrez Gonzalez': {
        'Campaña': 'Portabilidad',
        'SITE': 'México'
    },
    'Leonel Martinez Preciado':{
        'Campaña': 'Portabilidad',
        'SITE': 'México'
    },
    'Ana Karen Padilla Martinez':{
        'Campaña': 'Portabilidad',
        'SITE': 'México'
    },
    'Emmanuel Ruiz Vera':{
        'Campaña': 'Portabilidad',
        'SITE': 'México'
    },
    'Fergie Zoe Alcantara García':{
        'Campaña': 'Migración',
        'SITE': 'México'
    },
    'Carlos Alexis Viveros Garcia':{
        'Campaña': 'Migración',
        'SITE': 'México'
    },
    'Daniel Alejandro Perez Rivera':{
        'Campaña': 'Migración',
        'SITE': 'México'
    },
    'Angel Erubiel Gutierrez Martinez':{
        'Campaña': 'Migración',
        'SITE': 'México'
    },
    'Roberto Patricio Yañez Bajonero':{
        'Campaña': 'Migración',
        'SITE': 'México'
    },
    'Jorge Luis Sanchez Becerril':{
        'Campaña': 'Migración',
        'SITE': 'México'
    },
    'Bryan Abundis Romo':{
        'Campaña': 'Migración',
        'SITE': 'México'
    },
    'Greisi Yenifer Hernandez Valenzuela':{
        'Campaña': 'Migración',
        'SITE': 'Externo'
    },
    'Vanessa Valentina Pinto Salinas':{
        'Campaña': 'Migración',
        'SITE': 'Externo'
    },
    'Joaly Scarlet Garcia Noguera':{
        'Campaña': 'Migración',
        'SITE': 'Externo'
    },
    'Barbara Camila Maurera campos':{
        'Campaña': 'Migración',
        'SITE': 'Externo'
    },
    'Astrid Milena Villalba Gómez':{
        'Campaña': 'Migración',
        'SITE': 'Externo'
    },
    'Lorenys Patricia Villarroel Hernandez':{
        'Campaña': 'Migración',
        'SITE': 'Externo'
    }
}

def obtener_campana(agente):
    """Obtiene la campaña del agente"""
    if pd.isna(agente):
        return 'No Asignado'
    agente_str = str(agente).strip()
    info = AGENTE_CAMPANA_SITE.get(agente_str, {})
    return info.get('Campaña', 'No Asignado')

def obtener_site(agente):
    """Obtiene el SITE del agente"""
    if pd.isna(agente):
        return 'No Asignado'
    agente_str = str(agente).strip()
    info = AGENTE_CAMPANA_SITE.get(agente_str, {})
    return info.get('SITE', 'No Asignado')

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
        if key.upper() == agente_upper:
            return value
    
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
                '%Y-%m-%d %H:%M:%S',
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
                '%Y-%m-%d',
                '%d/%m/%Y',
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
def leer_archivo(archivo):
    """Lee un archivo Excel o CSV"""
    extension = archivo.name.split('.')[-1].lower()
    
    try:
        if extension == 'csv':
            try:
                df = pd.read_csv(archivo, encoding='utf-8-sig', low_memory=False)
            except:
                df = pd.read_csv(archivo, encoding='latin-1', low_memory=False)
        else:
            try:
                df = pd.read_excel(archivo, engine='openpyxl')
            except:
                try:
                    df = pd.read_excel(archivo, engine='xlrd')
                except:
                    df = pd.read_excel(archivo)
        
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
                    
                    if isinstance(valor, str) and ':' in valor:
                        partes = valor.split(':')
                        if len(partes) == 3:
                            minutos = int(partes[0]) * 60 + int(partes[1]) + int(partes[2]) / 60
                        else:
                            minutos = limpiar_valor_numerico(valor)
                    else:
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
    keywords = ['fecha', 'date', 'fech', 'día', 'dia', 'inicio', 'hora']
    
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

def calcular_vph(ventas, horas_conexion, min_horas=0.25):
    """Calcula el VPH (Ventas por Hora)"""
    if ventas == 0:
        return 0.0
    
    if horas_conexion < min_horas:
        return 0.0
    
    vph = ventas / horas_conexion
    return round(vph, 2)

def generar_resumen_consolidado(reporte_detalle):
    """Genera un resumen consolidado por fecha y hora"""
    if reporte_detalle is None or len(reporte_detalle) == 0:
        return None
    
    df = reporte_detalle.copy()
    df['Tiene_Actividad'] = (df['Registros'] > 0) | (df['Contacto'] > 0) | (df['Ventas'] > 0)
    
    resumen = df.groupby(['FECHA', 'Rango_Hora']).agg({
        'AGENTE': lambda x: x[df.loc[x.index, 'Tiene_Actividad']].nunique(),
        'Total conexión': lambda x: (x / df.loc[x.index, 'AGENTE'].nunique()).mean() if df.loc[x.index, 'AGENTE'].nunique() > 0 else 0,
        'Registros': 'sum',
        'Llamadas': 'sum',
        'Contacto': 'sum',
        'Ventas': 'sum'
    }).reset_index()
    
    resumen.columns = ['FECHA', 'Rango_Hora', 'HC', 'Hrs conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas']
    resumen['Hrs conexión'] = resumen['Hrs conexión'].clip(upper=1.0)
    resumen['Conversión'] = (resumen['Ventas'] / resumen['Contacto'] * 100).round(2)
    resumen['Conversión'] = resumen['Conversión'].fillna(0).replace([np.inf, -np.inf], 0)
    resumen['VPH'] = resumen.apply(lambda row: calcular_vph(row['Ventas'], row['Hrs conexión']), axis=1)
    resumen['Conversión'] = resumen['Conversión'].apply(lambda x: f"{x}%")
    
    columnas_orden = ['FECHA', 'Rango_Hora', 'HC', 'Hrs conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
    resumen = resumen[columnas_orden]
    resumen = resumen.sort_values(['FECHA', 'Rango_Hora'])
    
    return resumen

def generar_tablas_por_campana_site(reporte_detalle):
    """Genera tablas separadas para cada combinación de Campaña y SITE"""
    if reporte_detalle is None or len(reporte_detalle) == 0:
        return {}
    
    tablas = {}
    combinaciones = reporte_detalle[['CAMPAÑA', 'SITE']].drop_duplicates()
    
    for _, row in combinaciones.iterrows():
        campana = row['CAMPAÑA']
        site = row['SITE']
        
        df_filtrado = reporte_detalle[
            (reporte_detalle['CAMPAÑA'] == campana) & 
            (reporte_detalle['SITE'] == site)
        ]
        
        if len(df_filtrado) == 0:
            continue
        
        resumen_agente = df_filtrado.groupby(['FECHA', 'AGENTE']).agg({
            'Total conexión': 'sum',
            'Registros': 'sum',
            'Llamadas': 'sum',
            'Contacto': 'sum',
            'Ventas': 'sum'
        }).reset_index()
        
        resumen_agente['Conversión'] = (resumen_agente['Ventas'] / resumen_agente['Contacto'] * 100).round(2)
        resumen_agente['Conversión'] = resumen_agente['Conversión'].fillna(0).replace([np.inf, -np.inf], 0)
        resumen_agente['VPH'] = resumen_agente.apply(lambda row: calcular_vph(row['Ventas'], row['Total conexión']), axis=1)
        
        totales_fecha = df_filtrado.groupby('FECHA').agg({
            'Registros': 'sum',
            'Llamadas': 'sum',
            'Contacto': 'sum',
            'Ventas': 'sum'
        }).reset_index()
        
        totales_fecha['AGENTE'] = 'TOTAL'
        totales_fecha['Total conexión'] = 0
        totales_fecha['Conversión'] = (totales_fecha['Ventas'] / totales_fecha['Contacto'] * 100).round(2)
        totales_fecha['Conversión'] = totales_fecha['Conversión'].fillna(0).replace([np.inf, -np.inf], 0)
        totales_fecha['VPH'] = 0
        
        columnas_orden = ['FECHA', 'AGENTE', 'Total conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
        resumen_agente = resumen_agente[columnas_orden]
        totales_fecha = totales_fecha[columnas_orden]
        
        nombre_tabla = f"{campana}_{site}".replace(' ', '_')
        tablas[nombre_tabla] = {
            'campana': campana,
            'site': site,
            'detalle': resumen_agente,
            'totales': totales_fecha
        }
    
    return tablas

def guardar_excel_con_tablas(reporte_detalle, reporte_resumen):
    """Guarda el reporte en formato Excel con múltiples hojas"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            reporte_detalle.to_excel(writer, sheet_name='Detalle_Agentes', index=False)
            
            if reporte_resumen is not None and len(reporte_resumen) > 0:
                reporte_resumen.to_excel(writer, sheet_name='Resumen_Consolidado', index=False)
            
            tablas = generar_tablas_por_campana_site(reporte_detalle)
            
            for nombre_tabla, info in tablas.items():
                sheet_name = f"{info['campana']}_{info['site']}"[:31]
                info['detalle'].to_excel(writer, sheet_name=sheet_name, index=False)
                
                if len(info['totales']) > 0:
                    totales_df = info['totales']
                    startrow = len(info['detalle']) + 2
                    totales_df.to_excel(writer, sheet_name=sheet_name, startrow=startrow, index=False, header=['TOTALES'] + [''] * (len(totales_df.columns) - 1))
            
            st.success(f"✅ Tablas generadas: {len(tablas)} combinaciones de Campaña y SITE")
            
            if tablas:
                nombres = [f"{info['campana']} - {info['site']}" for info in tablas.values()]
                st.info(f"📄 Hojas creadas: {', '.join(nombres)}")
        
        output.seek(0)
        return output
        
    except Exception as e:
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlwt') as writer:
                reporte_detalle.to_excel(writer, sheet_name='Detalle_Agentes', index=False)
                if reporte_resumen is not None and len(reporte_resumen) > 0:
                    reporte_resumen.to_excel(writer, sheet_name='Resumen_Consolidado', index=False)
                
                tablas = generar_tablas_por_campana_site(reporte_detalle)
                for i, (nombre_tabla, info) in enumerate(list(tablas.items())[:3]):
                    sheet_name = f"{info['campana']}_{info['site']}"[:31]
                    info['detalle'].to_excel(writer, sheet_name=sheet_name, index=False)
            
            output.seek(0)
            st.warning("⚠️ Usando formato .xls (solo se incluyeron 3 tablas)")
            return output
            
        except Exception as e2:
            st.error(f"❌ No se pudo generar el archivo Excel: {e2}")
            st.code("pip install openpyxl")
            return None

@st.cache_data
def procesar_datos_completos(df_llamadas, df_crm=None, df_tiempos=None, incluir_tiempos=True):
    """Procesa los datos y genera el reporte detallado"""
    
    with st.spinner('Procesando datos...'):
        progress_bar = st.progress(0)
        
        # ============================================
        # PASO 1: Preparar CRM para identificar ventas
        # ============================================
        ventas_crm = pd.DataFrame()
        if df_crm is not None and len(df_crm) > 0:
            st.info("🔍 Identificando ventas desde CRM...")
            
            # Limpiar CRM
            df_crm_clean = df_crm.copy()
            
            # Convertir fechas
            if 'FECHA_REGISTRO' in df_crm_clean.columns:
                df_crm_clean['FECHA_REGISTRO'] = pd.to_datetime(df_crm_clean['FECHA_REGISTRO'])
                df_crm_clean['FECHA_SIMPLE'] = df_crm_clean['FECHA_REGISTRO'].dt.date
            
            # ============================================
            # IMPORTANTE: Usar NOMBRE_USUARIO para buscar
            # ============================================
            if 'NOMBRE_USUARIO' in df_crm_clean.columns:
                # Crear columna de agente nombre desde NOMBRE_USUARIO
                df_crm_clean['AGENTE_NOMBRE'] = df_crm_clean['NOMBRE_USUARIO'].astype(str).str.strip()
                
                st.success(f"✅ Usando NOMBRE_USUARIO para identificar ventas: {df_crm_clean['AGENTE_NOMBRE'].nunique()} agentes únicos")
            else:
                st.warning("⚠️ No se encontró columna NOMBRE_USUARIO en CRM")
                df_crm_clean['AGENTE_NOMBRE'] = None
            
            # Filtrar solo registros válidos
            df_crm_clean = df_crm_clean.dropna(subset=['AGENTE_NOMBRE'])
            
            # Crear dataframe de ventas CRM
            ventas_crm = df_crm_clean[['AGENTE_NOMBRE', 'FECHA_SIMPLE', 'USUARIO', 'NOMBRE_USUARIO']].copy()
            ventas_crm['ES_VENTA_CRM'] = True
            
            # Mostrar información de las ventas encontradas
            if len(ventas_crm) > 0:
                st.success(f"✅ Ventas encontradas en CRM: {len(ventas_crm)}")
                
                # Mostrar resumen por agente
                resumen_agentes = ventas_crm.groupby('AGENTE_NOMBRE').size().reset_index(name='VENTAS_CRM')
                st.write("**Ventas por agente en CRM:**")
                st.dataframe(resumen_agentes)
            else:
                st.warning("⚠️ No se encontraron ventas válidas en CRM")
            
            progress_bar.progress(10)
        
        # ============================================
        # PASO 2: Identificar columnas en llamadas
        # ============================================
        columnas = df_llamadas.columns.tolist()
        
        # Buscar columna de fecha
        fecha_col = None
        for col in columnas:
            col_lower = str(col).lower()
            if 'fecha y hora inicio' in col_lower or 'fecha y hora' in col_lower:
                fecha_col = col
                break
        
        if not fecha_col:
            fecha_col = identificar_columna_fecha(df_llamadas)
        
        # Buscar columna de agente
        agente_col = None
        for col in columnas:
            col_lower = str(col).lower()
            if col_lower == 'agente' or 'agente' in col_lower:
                agente_col = col
                break
        
        if not fecha_col or not agente_col:
            st.error(f"No se encontraron las columnas necesarias. Fecha: {fecha_col}, Agente: {agente_col}")
            return None, None
        
        progress_bar.progress(20)
        
        # ============================================
        # PASO 3: Procesar fechas
        # ============================================
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
        
        # ============================================
        # PASO 4: Convertir agentes
        # ============================================
        df_llamadas['Agente_Nombre'] = df_llamadas[agente_col].apply(convertir_agente)
        df_llamadas = df_llamadas.dropna(subset=['Agente_Nombre'])
        df_llamadas['Agente_Nombre'] = df_llamadas['Agente_Nombre'].astype(str)
        
        if len(df_llamadas) == 0:
            st.error("No se pudieron convertir agentes válidos.")
            return None, None
        
        progress_bar.progress(40)
        
        # ============================================
        # PASO 5: MARCAR VENTAS DESDE CRM usando NOMBRE_USUARIO
        # ============================================
        # Crear columna de venta
        df_llamadas['Es_Venta'] = False
        df_llamadas['Es_Contacto'] = True
        df_llamadas['Venta_CRM'] = False
        df_llamadas['Validacion_CRM'] = ''
        df_llamadas['CRM_Usuario'] = ''
        df_llamadas['CRM_Nombre'] = ''
        
        if len(ventas_crm) > 0:
            # Crear conjunto de agentes con ventas en CRM
            agentes_con_ventas = set(ventas_crm['AGENTE_NOMBRE'].unique())
            st.info(f"🔍 Agentes con ventas en CRM: {len(agentes_con_ventas)}")
            
            # Crear diccionario de fechas de ventas por agente
            ventas_por_agente = {}
            for _, row in ventas_crm.iterrows():
                agente = row['AGENTE_NOMBRE']
                fecha = row['FECHA_SIMPLE']
                if agente not in ventas_por_agente:
                    ventas_por_agente[agente] = set()
                ventas_por_agente[agente].add(fecha)
            
            # Marcar ventas en llamadas
            def marcar_venta(row):
                agente = row['Agente_Nombre']
                fecha = row['Fecha_Solo']
                
                if agente in ventas_por_agente:
                    if fecha in ventas_por_agente[agente]:
                        # Buscar información del CRM
                        info_crm = ventas_crm[
                            (ventas_crm['AGENTE_NOMBRE'] == agente) & 
                            (ventas_crm['FECHA_SIMPLE'] == fecha)
                        ]
                        
                        if len(info_crm) > 0:
                            crm_row = info_crm.iloc[0]
                            return {
                                'Es_Venta': True,
                                'Venta_CRM': True,
                                'Validacion_CRM': f"✅ Venta confirmada en CRM para {agente} el {fecha}",
                                'CRM_Usuario': crm_row.get('USUARIO', ''),
                                'CRM_Nombre': crm_row.get('NOMBRE_USUARIO', '')
                            }
                
                return {
                    'Es_Venta': False,
                    'Venta_CRM': False,
                    'Validacion_CRM': 'No es venta CRM',
                    'CRM_Usuario': '',
                    'CRM_Nombre': ''
                }
            
            # Aplicar marca de venta
            resultados = df_llamadas.apply(marcar_venta, axis=1, result_type='expand')
            df_llamadas['Es_Venta'] = resultados['Es_Venta']
            df_llamadas['Venta_CRM'] = resultados['Venta_CRM']
            df_llamadas['Validacion_CRM'] = resultados['Validacion_CRM']
            df_llamadas['CRM_Usuario'] = resultados['CRM_Usuario']
            df_llamadas['CRM_Nombre'] = resultados['CRM_Nombre']
            
            ventas_totales = df_llamadas['Es_Venta'].sum()
            st.success(f"✅ Ventas marcadas desde CRM: {ventas_totales}")
            
            # Mostrar detalle de ventas encontradas
            if ventas_totales > 0:
                st.write("**Ventas identificadas en llamadas:**")
                ventas_df = df_llamadas[df_llamadas['Es_Venta'] == True][['Agente_Nombre', 'Fecha_Solo', 'CRM_Usuario', 'CRM_Nombre']]
                st.dataframe(ventas_df)
        else:
            st.warning("⚠️ No se cargaron ventas desde CRM. Todas las llamadas se marcarán como contacto.")
        
        progress_bar.progress(50)
        
        # ============================================
        # PASO 6: Agregar Campaña y SITE
        # ============================================
        df_llamadas['Campaña'] = df_llamadas['Agente_Nombre'].apply(obtener_campana)
        df_llamadas['SITE'] = df_llamadas['Agente_Nombre'].apply(obtener_site)
        
        progress_bar.progress(60)
        
        # ============================================
        # PASO 7: Agrupar datos
        # ============================================
        fechas_disponibles = sorted(df_llamadas['Fecha_Solo'].unique())
        
        # Agrupar por fecha, agente y rango
        agrupado = df_llamadas.groupby(['Fecha_Solo', 'Agente_Nombre', 'Campaña', 'SITE', 'Rango_Hora']).agg({
            'Es_Contacto': ['count', 'sum'],
            'Es_Venta': 'sum'
        }).reset_index()
        
        agrupado.columns = ['FECHA', 'AGENTE', 'CAMPAÑA', 'SITE', 'Rango_Hora', 'Registros', 'Contacto', 'Ventas']
        agrupado['AGENTE'] = agrupado['AGENTE'].astype(str)
        
        progress_bar.progress(70)
        
        # ============================================
        # PASO 8: Crear reporte detallado
        # ============================================
        reporte_list = []
        
        for fecha in fechas_disponibles:
            df_fecha = agrupado[agrupado['FECHA'] == fecha]
            agentes_activos = df_fecha[df_fecha['Registros'] > 0]['AGENTE'].unique().tolist()
            
            if not agentes_activos:
                continue
            
            for agente in agentes_activos:
                campana = obtener_campana(agente)
                site = obtener_site(agente)
                
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
                            'CAMPAÑA': campana,
                            'SITE': site,
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
        
        if len(reporte_detalle) == 0:
            st.warning("No se encontraron datos para ningún agente")
            return None, None
        
        reporte_detalle['FECHA'] = pd.to_datetime(reporte_detalle['FECHA']).dt.date
        reporte_detalle['AGENTE'] = reporte_detalle['AGENTE'].astype(str)
        reporte_detalle['CAMPAÑA'] = reporte_detalle['CAMPAÑA'].astype(str)
        reporte_detalle['SITE'] = reporte_detalle['SITE'].astype(str)
        reporte_detalle['Rango_Hora'] = reporte_detalle['Rango_Hora'].astype(str)
        
        progress_bar.progress(80)
        
        # ============================================
        # PASO 9: Procesar tiempos de conexión
        # ============================================
        if incluir_tiempos and df_tiempos is not None and len(df_tiempos) > 0:
            try:
                tiempos_dict = procesar_archivo_tiempos(df_tiempos)
                
                if tiempos_dict:
                    for idx, row in reporte_detalle.iterrows():
                        key = f"{row['AGENTE']}|{row['Rango_Hora']}"
                        horas = tiempos_dict.get(key, 0.0)
                        reporte_detalle.at[idx, 'Total conexión'] = round(min(horas, 1.0), 2)
                        
                        ventas = row['Ventas']
                        horas_conn = reporte_detalle.at[idx, 'Total conexión']
                        reporte_detalle.at[idx, 'VPH'] = calcular_vph(ventas, horas_conn)
                    
                    st.success(f"✅ Tiempos procesados: {len(tiempos_dict)} combinaciones agente-hora")
            except Exception as e:
                st.warning(f"Error al procesar tiempos: {e}. Continuando sin tiempos.")
        
        progress_bar.progress(90)
        
        # ============================================
        # PASO 10: Formatear resultado final
        # ============================================
        reporte_detalle['Conversión'] = reporte_detalle['Conversión'].round(2)
        reporte_detalle['VPH'] = reporte_detalle['VPH'].round(2)
        reporte_detalle['Total conexión'] = reporte_detalle['Total conexión'].round(2)
        
        columnas_orden = ['FECHA', 'AGENTE', 'CAMPAÑA', 'SITE', 'Rango_Hora', 'Total conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
        reporte_detalle = reporte_detalle[columnas_orden]
        
        # Generar resumen consolidado
        reporte_resumen = generar_resumen_consolidado(reporte_detalle)
        
        progress_bar.progress(100)
        
        return reporte_detalle, reporte_resumen

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
    
    archivo_crm = st.file_uploader(
        "📋 Archivo CRM (Opcional - Para identificar ventas)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo de CRM para identificar qué llamadas fueron ventas"
    )
    
    archivo_tiempos = st.file_uploader(
        "Archivo de tiempos de agentes (Opcional)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo con los tiempos de conexión por agente y hora"
    )

with col2:
    st.subheader("⚙️ Configuración")
    
    incluir_tiempos = st.checkbox("Incluir tiempos de conexión", value=True)
    
    st.info("💡 Las ventas se identifican automáticamente desde el archivo CRM usando NOMBRE_USUARIO")
    
    procesar = st.button("🚀 Procesar Datos", type="primary", use_container_width=True)

# ============================================
# PROCESAMIENTO DE DATOS
# ============================================

if procesar and archivo_llamadas:
    try:
        df_llamadas = leer_archivo(archivo_llamadas)
        
        if df_llamadas is not None and len(df_llamadas) > 0:
            st.success(f"✅ Archivo de llamadas cargado: {len(df_llamadas):,} registros")
            
            df_crm = None
            if archivo_crm:
                df_crm = leer_archivo(archivo_crm)
                if df_crm is not None:
                    st.success(f"✅ Archivo CRM cargado: {len(df_crm):,} registros")
                    # Mostrar columnas del CRM
                    st.write("**Columnas del CRM:**", df_crm.columns.tolist())
                    
                    # Mostrar ejemplo de NOMBRE_USUARIO
                    if 'NOMBRE_USUARIO' in df_crm.columns:
                        st.write("**Ejemplos de NOMBRE_USUARIO:**", df_crm['NOMBRE_USUARIO'].head(5).tolist())
            
            df_tiempos = None
            if archivo_tiempos and incluir_tiempos:
                df_tiempos = leer_archivo(archivo_tiempos)
                if df_tiempos is not None:
                    st.success(f"✅ Archivo de tiempos cargado: {len(df_tiempos):,} registros")
            
            reporte_detalle, reporte_resumen = procesar_datos_completos(
                df_llamadas, 
                df_crm, 
                df_tiempos, 
                incluir_tiempos
            )
            
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
                    st.metric("Días", total_dias)
                with col2:
                    st.metric("Agentes", agentes_unicos)
                with col3:
                    st.metric("Registros", f"{reporte_detalle['Registros'].sum():,}")
                with col4:
                    st.metric("Contactos", f"{reporte_detalle['Contacto'].sum():,}")
                with col5:
                    total_ventas = reporte_detalle['Ventas'].sum()
                    st.metric("Ventas", f"{total_ventas:,}")
                with col6:
                    conversion = (total_ventas / reporte_detalle['Contacto'].sum() * 100) if reporte_detalle['Contacto'].sum() > 0 else 0
                    st.metric("Conversión", f"{conversion:.2f}%")
                
                # ============================================
                # RESUMEN POR CAMPAÑA Y SITE
                # ============================================
                st.subheader("📊 Resumen por Campaña y SITE")
                
                resumen_campana = reporte_detalle.groupby(['CAMPAÑA', 'SITE']).agg({
                    'Registros': 'sum',
                    'Contacto': 'sum',
                    'Ventas': 'sum'
                }).reset_index()
                
                resumen_campana['Conversión'] = (resumen_campana['Ventas'] / resumen_campana['Contacto'] * 100).round(2)
                resumen_campana['Conversión'] = resumen_campana['Conversión'].fillna(0)
                
                st.dataframe(
                    resumen_campana,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "CAMPAÑA": st.column_config.TextColumn("Campaña"),
                        "SITE": st.column_config.TextColumn("SITE"),
                        "Registros": st.column_config.NumberColumn("Registros"),
                        "Contacto": st.column_config.NumberColumn("Contactos"),
                        "Ventas": st.column_config.NumberColumn("Ventas"),
                        "Conversión": st.column_config.NumberColumn("Conversión", format="%.2f%%"),
                    }
                )
                
                # ============================================
                # TABLAS POR CAMPAÑA Y SITE
                # ============================================
                st.subheader("📋 Tablas por Campaña y SITE")
                
                tablas = generar_tablas_por_campana_site(reporte_detalle)
                
                if tablas:
                    tab_names = [f"{info['campana']} - {info['site']}" for info in tablas.values()]
                    tabs = st.tabs(tab_names)
                    
                    for i, (nombre_tabla, info) in enumerate(tablas.items()):
                        with tabs[i]:
                            st.markdown(f"### {info['campana']} - {info['site']}")
                            
                            total_contactos = info['detalle']['Contacto'].sum()
                            total_ventas = info['detalle']['Ventas'].sum()
                            conversion = (total_ventas / total_contactos * 100) if total_contactos > 0 else 0
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Contactos", f"{total_contactos:,}")
                            with col2:
                                st.metric("Ventas", f"{total_ventas:,}")
                            with col3:
                                st.metric("Conversión", f"{conversion:.2f}%")
                            
                            st.dataframe(
                                info['detalle'],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "FECHA": st.column_config.TextColumn("Fecha"),
                                    "AGENTE": st.column_config.TextColumn("Agente"),
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
                # RESUMEN CONSOLIDADO
                # ============================================
                if reporte_resumen is not None and len(reporte_resumen) > 0:
                    st.subheader("📊 Resumen Consolidado por Fecha y Hora")
                    
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
                            "HC": st.column_config.NumberColumn("HC"),
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
                
                col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                
                with col_filtro1:
                    fechas_opciones_detalle = ['Todas'] + [f.strftime('%Y-%m-%d') for f in fechas_disponibles]
                    filtro_fecha_detalle = st.selectbox("📅 Filtrar detalle por fecha:", fechas_opciones_detalle, key="filtro_detalle")
                
                with col_filtro2:
                    agentes_opciones = ['Todos'] + sorted([str(a) for a in reporte_detalle['AGENTE'].unique() if a and str(a) != 'nan'])
                    filtro_agente = st.selectbox("👤 Filtrar por agente:", agentes_opciones)
                
                with col_filtro3:
                    campanas_opciones = ['Todas'] + sorted([str(c) for c in reporte_detalle['CAMPAÑA'].unique() if c and str(c) != 'nan'])
                    filtro_campana = st.selectbox("📢 Filtrar por campaña:", campanas_opciones)
                
                detalle_filtrado = reporte_detalle.copy()
                
                if filtro_fecha_detalle != 'Todas':
                    fecha_filtro = datetime.strptime(filtro_fecha_detalle, '%Y-%m-%d').date()
                    detalle_filtrado = detalle_filtrado[detalle_filtrado['FECHA'] == fecha_filtro]
                
                if filtro_agente != 'Todos':
                    detalle_filtrado = detalle_filtrado[detalle_filtrado['AGENTE'] == filtro_agente]
                
                if filtro_campana != 'Todas':
                    detalle_filtrado = detalle_filtrado[detalle_filtrado['CAMPAÑA'] == filtro_campana]
                
                st.dataframe(
                    detalle_filtrado,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "FECHA": st.column_config.TextColumn("Fecha"),
                        "AGENTE": st.column_config.TextColumn("Agente"),
                        "CAMPAÑA": st.column_config.TextColumn("Campaña"),
                        "SITE": st.column_config.TextColumn("SITE"),
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
                
                output = guardar_excel_con_tablas(reporte_detalle, reporte_resumen)
                
                if output is not None:
                    output.seek(0)
                    header = output.read(4)
                    output.seek(0)
                    
                    if header == b'PK\x03\x04':
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        file_ext = "xlsx"
                    else:
                        mime_type = "application/vnd.ms-excel"
                        file_ext = "xls"
                    
                    st.download_button(
                        label=f"⬇️ Descargar Reporte",
                        data=output,
                        file_name=f"reporte_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                        mime=mime_type,
                        use_container_width=True
                    )
                    
                    st.info("📄 El archivo contiene múltiples hojas:\n- **Detalle_Agentes**: Desglose por agente, fecha y hora\n- **Resumen_Consolidado**: Resumen con HC y Hrs conexión promedio\n- **Campaña_SITE**: Tablas separadas por Campaña y SITE")
                else:
                    st.error("❌ No se pudo generar el archivo de descarga")
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
        Procesador de Llamadas v2.0 - Ventas identificadas desde CRM usando NOMBRE_USUARIO
    </div>
""", unsafe_allow_html=True)
