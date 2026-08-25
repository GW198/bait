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
# CLASE VALIDADORA CRM
# ============================================

class CRMValidator:
    """Validador de ventas contra archivo CRM"""
    
    def __init__(self, crm_df=None):
        self.crm_df = crm_df
        self._preprocess_crm()
    
    def _preprocess_crm(self):
        """Preprocesa los datos del CRM"""
        if self.crm_df is not None and len(self.crm_df) > 0:
            # Limpiar usuarios: RRS-AFIGUEROA -> BT-CREBECA
            if 'USUARIO' in self.crm_df.columns:
                self.crm_df['USUARIO_STR'] = self.crm_df['USUARIO'].astype(str)
                self.crm_df['USUARIO_LIMPIO'] = self.crm_df['USUARIO_STR'].str.replace('RRS-', 'BT-', regex=False)
            
            # Convertir fechas
            if 'FECHA_REGISTRO' in self.crm_df.columns:
                try:
                    self.crm_df['FECHA_REGISTRO'] = pd.to_datetime(self.crm_df['FECHA_REGISTRO'])
                    self.crm_df['FECHA_SIMPLE'] = self.crm_df['FECHA_REGISTRO'].dt.date
                except Exception as e:
                    st.warning(f"Error al convertir fechas en CRM: {e}")
    
    def validate_sale(self, agente, fecha_venta, numero_llamado=None, duracion=0):
        """
        Valida si una venta existe en CRM
        Retorna: (es_valida, mensaje, nivel_confianza)
        """
        if self.crm_df is None or len(self.crm_df) == 0:
            return False, "No hay datos CRM cargados", "NULA"
        
        # Buscar coincidencias por agente
        agente_limpio = str(agente).strip()
        
        # Intentar mapeo inverso: nombre agente -> usuario CRM
        usuario_crm = None
        for key, value in MAPEO_AGENTES.items():
            if value == agente_limpio:
                usuario_crm = key
                break
        
        if not usuario_crm:
            # Intentar coincidencia parcial
            for key, value in MAPEO_AGENTES.items():
                if value in agente_limpio or agente_limpio in value:
                    usuario_crm = key
                    break
        
        if not usuario_crm:
            return False, f"Agente '{agente_limpio}' no encontrado en mapeo CRM", "NULA"
        
        # Buscar en CRM
        crm_matches = pd.DataFrame()
        
        if 'USUARIO_LIMPIO' in self.crm_df.columns:
            crm_matches = self.crm_df[self.crm_df['USUARIO_LIMPIO'] == usuario_crm]
        
        if len(crm_matches) == 0 and 'USUARIO_STR' in self.crm_df.columns:
            crm_matches = self.crm_df[self.crm_df['USUARIO_STR'].str.contains(usuario_crm.replace('BT-', ''), case=False, na=False)]
        
        if len(crm_matches) == 0 and 'USUARIO' in self.crm_df.columns:
            usuario_orig = usuario_crm.replace('BT-', '')
            crm_matches = self.crm_df[self.crm_df['USUARIO'].astype(str).str.contains(usuario_orig, case=False, na=False)]
        
        if len(crm_matches) == 0:
            return False, f"Usuario '{usuario_crm}' no encontrado en CRM", "NULA"
        
        # Verificar fecha
        if fecha_venta:
            try:
                fecha_venta_dt = pd.to_datetime(fecha_venta).date() if not isinstance(fecha_venta, datetime) else fecha_venta.date()
                
                if 'FECHA_SIMPLE' in crm_matches.columns:
                    crm_fechas = crm_matches['FECHA_SIMPLE'].dropna().unique()
                else:
                    crm_fechas = pd.to_datetime(crm_matches['FECHA_REGISTRO']).dt.date.dropna().unique()
                
                if fecha_venta_dt in crm_fechas:
                    return True, f"Venta confirmada en CRM para {usuario_crm} el {fecha_venta_dt}", "ALTA"
                else:
                    fechas_crm = sorted(crm_fechas)
                    if len(fechas_crm) > 0:
                        for fecha_crm in fechas_crm:
                            diff = (fecha_venta_dt - fecha_crm).days
                            if abs(diff) <= 1:
                                return True, f"Venta probable en CRM (fecha cercana: {fecha_crm})", "MEDIA"
                    
                    return False, f"Usuario encontrado pero sin coincidencia de fecha", "BAJA"
            except Exception as e:
                return False, f"Error al validar fecha: {str(e)}", "BAJA"
        
        return False, "Sin fecha para validar", "BAJA"

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
    
    # Buscar coincidencia exacta primero
    for key, value in MAPEO_AGENTES.items():
        if key.upper() == agente_upper:
            return value
    
    # Buscar coincidencia parcial
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
                '%Y-%m-%d %H:%M:%S',  # Tu formato: 2026-08-01 09:03:21
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
                '%Y-%m-%d',  # Solo fecha
                '%d/%m/%Y',  # Solo fecha
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
def leer_archivo_crm(archivo):
    """Lee el archivo CRM específicamente"""
    df = leer_archivo(archivo)
    
    if df is not None:
        columnas_esperadas = ['USUARIO', 'NOMBRE_USUARIO', 'FECHA_REGISTRO']
        columnas_encontradas = [col for col in columnas_esperadas if col in df.columns]
        
        if len(columnas_encontradas) < 3:
            st.warning(f"El archivo CRM no tiene todas las columnas esperadas. Encontradas: {columnas_encontradas}")
        else:
            st.success(f"✅ Archivo CRM cargado: {len(df):,} registros")
    
    return df

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
                    
                    # Convertir tiempo HH:MM:SS a minutos
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
def procesar_datos_completos(df_llamadas, df_tiempos=None, df_crm=None, incluir_tiempos=True, validar_crm=False):
    """Procesa los datos y genera el reporte detallado y el resumen consolidado"""
    
    with st.spinner('Procesando datos...'):
        progress_bar = st.progress(0)
        
        # 0. Inicializar validador CRM
        validador = None
        if validar_crm and df_crm is not None and len(df_crm) > 0:
            validador = CRMValidator(df_crm)
            st.success("✅ Validador CRM inicializado")
            progress_bar.progress(5)
        
        # 1. Identificar columnas - CORREGIDO para tu archivo
        columnas = df_llamadas.columns.tolist()
        st.write("Columnas encontradas:", columnas)  # Debug
        
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
        
        # Buscar columna de disposición
        disposition_col = None
        for col in columnas:
            col_lower = str(col).lower()
            if 'disposition' in col_lower or 'disposition__pospago_bait' in col_lower:
                disposition_col = col
                break
        
        st.write(f"Fecha col: {fecha_col}, Agente col: {agente_col}, Disposition col: {disposition_col}")  # Debug
        
        if not fecha_col or not agente_col:
            st.error(f"No se encontraron las columnas necesarias. Fecha: {fecha_col}, Agente: {agente_col}")
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
        
        if len(df_llamadas) == 0:
            st.error("No se pudieron convertir agentes válidos.")
            return None, None
        
        progress_bar.progress(50)
        
        # 4. Agregar columnas de Campaña y SITE
        df_llamadas['Campaña'] = df_llamadas['Agente_Nombre'].apply(obtener_campana)
        df_llamadas['SITE'] = df_llamadas['Agente_Nombre'].apply(obtener_site)
        
        # 5. Clasificar contactos y ventas
        if disposition_col:
            # Usar la columna de disposición para clasificar
            df_llamadas['Es_Contacto'] = df_llamadas[disposition_col].apply(es_contacto)
            df_llamadas['Es_Venta'] = df_llamadas[disposition_col].apply(es_venta)
        else:
            # Si no hay disposición, marcar todas como contacto pero no venta
            df_llamadas['Es_Contacto'] = True
            df_llamadas['Es_Venta'] = False
        
        progress_bar.progress(60)
        
        # 6. Validar ventas contra CRM
        if validar_crm and validador:
            st.info("🔍 Validando ventas contra CRM...")
            
            def validar_fila(row):
                if row['Es_Venta']:
                    es_valida, mensaje, nivel = validador.validate_sale(
                        row['Agente_Nombre'],
                        row['Fecha_Solo'],
                        row.get('Número llamado', None),
                        row.get('Duración (segundos)', 0)
                    )
                    return f"{'✅' if es_valida else '❌'} {mensaje}"
                return "No es venta"
            
            df_llamadas['Validacion_CRM'] = df_llamadas.apply(validar_fila, axis=1)
            df_llamadas['Venta_Confirmada'] = df_llamadas['Validacion_CRM'].str.contains('✅', na=False)
            
            total_ventas = df_llamadas['Es_Venta'].sum()
            ventas_confirmadas = df_llamadas[df_llamadas['Es_Venta'] == True]['Venta_Confirmada'].sum()
            
            st.success(f"✅ Ventas validadas: {ventas_confirmadas}/{total_ventas} confirmadas en CRM")
            
            progress_bar.progress(70)
        
        # 7. Agrupar por fecha, agente y rango de hora
        fechas_disponibles = sorted(df_llamadas['Fecha_Solo'].unique())
        
        agrupado = df_llamadas.groupby(['Fecha_Solo', 'Agente_Nombre', 'Campaña', 'SITE', 'Rango_Hora']).agg({
            'Es_Contacto': ['count', 'sum'],
            'Es_Venta': 'sum'
        }).reset_index()
        
        agrupado.columns = ['FECHA', 'AGENTE', 'CAMPAÑA', 'SITE', 'Rango_Hora', 'Registros', 'Contacto', 'Ventas']
        agrupado['AGENTE'] = agrupado['AGENTE'].astype(str)
        
        # 8. Agregar métricas de validación
        if validar_crm and validador:
            ventas_confirmadas_por_grupo = df_llamadas.groupby(['Fecha_Solo', 'Agente_Nombre', 'Rango_Hora']).agg({
                'Venta_Confirmada': 'sum'
            }).reset_index()
            ventas_confirmadas_por_grupo.columns = ['FECHA', 'AGENTE', 'Rango_Hora', 'Ventas_Confirmadas']
            
            agrupado = agrupado.merge(ventas_confirmadas_por_grupo, on=['FECHA', 'AGENTE', 'Rango_Hora'], how='left')
            agrupado['Ventas_Confirmadas'] = agrupado['Ventas_Confirmadas'].fillna(0).astype(int)
            agrupado['%_CRM'] = (agrupado['Ventas_Confirmadas'] / agrupado['Ventas'] * 100).round(2)
            agrupado['%_CRM'] = agrupado['%_CRM'].fillna(0).replace([np.inf, -np.inf], 0)
        
        progress_bar.progress(80)
        
        # 9. Crear reporte detallado
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
                        if validar_crm:
                            row['Ventas_Confirmadas'] = 0
                            row['%_CRM'] = 0
                    
                    row['Llamadas'] = row['Registros']
                    row['Conversión'] = (row['Ventas'] / row['Contacto'] * 100) if row['Contacto'] > 0 else 0
                    row['Total conexión'] = 0.0
                    row['VPH'] = 0.0
                    
                    if validar_crm and 'Ventas_Confirmadas' not in row:
                        row['Ventas_Confirmadas'] = 0
                        row['%_CRM'] = 0
                    
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
        
        if validar_crm and 'Ventas_Confirmadas' in reporte_detalle.columns:
            reporte_detalle['Ventas_Confirmadas'] = reporte_detalle['Ventas_Confirmadas'].fillna(0).astype(int)
            reporte_detalle['%_CRM'] = reporte_detalle['%_CRM'].fillna(0).round(2)
        
        progress_bar.progress(90)
        
        # 10. Procesar tiempos de conexión
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
        
        progress_bar.progress(95)
        
        # 11. Redondear y reordenar
        reporte_detalle['Conversión'] = reporte_detalle['Conversión'].round(2)
        reporte_detalle['VPH'] = reporte_detalle['VPH'].round(2)
        reporte_detalle['Total conexión'] = reporte_detalle['Total conexión'].round(2)
        
        columnas_base = ['FECHA', 'AGENTE', 'CAMPAÑA', 'SITE', 'Rango_Hora', 'Total conexión', 'Registros', 'Llamadas', 'Contacto', 'Ventas', 'Conversión', 'VPH']
        
        if validar_crm and 'Ventas_Confirmadas' in reporte_detalle.columns:
            columnas_crm = ['Ventas_Confirmadas', '%_CRM']
            columnas_detalle = columnas_base[:10] + columnas_crm + columnas_base[10:]
        else:
            columnas_detalle = columnas_base
        
        reporte_detalle = reporte_detalle[columnas_detalle]
        
        # 12. Generar resumen consolidado
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
    
    archivo_tiempos = st.file_uploader(
        "Archivo de tiempos de agentes (Opcional)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo con los tiempos de conexión por agente y hora"
    )
    
    archivo_crm = st.file_uploader(
        "📋 Archivo CRM (Opcional - Para validación de ventas)",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo de CRM para validar que las ventas sean reales"
    )

with col2:
    st.subheader("⚙️ Configuración")
    
    incluir_tiempos = st.checkbox("Incluir tiempos de conexión", value=True)
    
    validar_crm = st.checkbox("✅ Validar ventas contra CRM", value=False, 
                              help="Marca para validar que las ventas existan en el CRM")
    
    if validar_crm and not archivo_crm:
        st.warning("⚠️ Necesitas cargar el archivo CRM para validar")
    
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
            
            df_crm = None
            if archivo_crm and validar_crm:
                df_crm = leer_archivo_crm(archivo_crm)
            
            reporte_detalle, reporte_resumen = procesar_datos_completos(
                df_llamadas, 
                df_tiempos, 
                df_crm, 
                incluir_tiempos, 
                validar_crm
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
                
                # Mostrar estadísticas de validación CRM
                if validar_crm and 'Ventas_Confirmadas' in reporte_detalle.columns:
                    st.subheader("🔍 Validación CRM")
                    
                    total_ventas = reporte_detalle['Ventas'].sum()
                    ventas_confirmadas = reporte_detalle['Ventas_Confirmadas'].sum()
                    
                    col_crm1, col_crm2, col_crm3 = st.columns(3)
                    with col_crm1:
                        st.metric("Ventas Totales", f"{total_ventas:,}")
                    with col_crm2:
                        st.metric("Ventas Confirmadas", f"{ventas_confirmadas:,}")
                    with col_crm3:
                        pct_crm = (ventas_confirmadas / total_ventas * 100) if total_ventas > 0 else 0
                        st.metric("Tasa de Confirmación", f"{pct_crm:.1f}%")
                    
                    ventas_no_confirmadas = total_ventas - ventas_confirmadas
                    if ventas_no_confirmadas > 0:
                        st.warning(f"⚠️ {ventas_no_confirmadas} ventas NO confirmadas en CRM. Revisa el detalle.")
                
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
                    st.info("✅ HC = Número de agentes que trabajaron en esa hora\n✅ Hrs conexión = Promedio de horas por agente (máximo 1 hora por rango)\n✅ VPH = Ventas / Horas de Conexión (mínimo 15 minutos de conexión)")
                    
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
                
                column_config = {
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
                
                if validar_crm and 'Ventas_Confirmadas' in detalle_filtrado.columns:
                    column_config["Ventas_Confirmadas"] = st.column_config.NumberColumn("Ventas CRM")
                    column_config["%_CRM"] = st.column_config.NumberColumn("% CRM", format="%.1f%%")
                
                st.dataframe(
                    detalle_filtrado,
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
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
        Procesador de Llamadas v2.0 - Con validación CRM
    </div>
""", unsafe_allow_html=True)
