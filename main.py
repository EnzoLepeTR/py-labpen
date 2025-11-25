import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import time
import gzip
import zlib
import hashlib
import threading
import queue
import signal
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from clases.utils import Utils
from clases.fallo import Fallo
from clases.configuracion import Configuracion
from clases.processIA import ProcessIA

import undetected_chromedriver as uc
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, \
    TimeoutException

# ========================================
# CONFIGURACIÓN RÁPIDA
# ========================================
MODO_HEADLESS = True  # 🔴 False = Ver navegador | 🟢 True = Modo invisible

MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

DIAS_POR_BLOQUE = 10
ESPERA_INICIAL = 20
MAX_REINTENTOS = 3
TIMEOUT_AJAX = 30
RANGE_DAYS = 100  # 365 días
NUMERO_CARACTERES = 5000 #numero de caracteres minimos para inyectar el fallo.


class Navegador(Enum):
    CHROME = "chrome"
    EDGE = "edge"


# ========================================
# ESTADO GLOBAL PARA MANEJO DE ARCHIVOS Y DRIVERS
# ========================================
class EstadoProceso:
    def __init__(self):
        self.archivos_guardados = set()
        self.lock = threading.Lock()
        self.drivers_activos = []
        self.shutdown_requested = False

    def agregar_driver(self, driver):
        """Registra un driver activo"""
        with self.lock:
            self.drivers_activos.append(driver)

    def remover_driver(self, driver):
        """Remueve un driver de la lista de activos"""
        with self.lock:
            if driver in self.drivers_activos:
                self.drivers_activos.remove(driver)

    def cerrar_todos_drivers(self):
        """Cierra todos los drivers activos"""
        with self.lock:
            print("\n🛑 Cerrando todos los navegadores...")
            for driver in self.drivers_activos:
                try:
                    driver.quit()
                    print("✅ Navegador cerrado")
                except Exception as e:
                    print(f"⚠️ Error cerrando navegador: {e}")
            self.drivers_activos.clear()

    def obtener_nombre_unico(self, carpeta, navegador, fecha_inicio, fecha_fin, pagina, worker_id=None):
        """Genera un nombre único para evitar colisiones entre procesos paralelos"""
        with self.lock:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            worker_str = f"_w{worker_id}" if worker_id else ""
            base_nombre = f"sentencias_{navegador}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}_pag{pagina}{worker_str}_{timestamp}"
            contador = 1
            nombre_final = f"{base_nombre}.json"

            while nombre_final in self.archivos_guardados:
                nombre_final = f"{base_nombre}_v{contador}.json"
                contador += 1

            self.archivos_guardados.add(nombre_final)
            return os.path.join(carpeta, nombre_final)


estado_global = EstadoProceso()


# ========================================
# MANEJADOR DE SEÑALES
# ========================================
def signal_handler(signum, frame):
    """Maneja la interrupción con Ctrl+C"""
    print("\n\n⚠️ Interrupción detectada (Ctrl+C)")
    print("🛑 Iniciando cierre ordenado...")

    estado_global.shutdown_requested = True
    estado_global.cerrar_todos_drivers()

    print("✅ Cierre completado")
    sys.exit(0)


# Registrar el manejador de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ========================================
# FUNCIONES DE UTILIDAD
# ========================================
def limpiar_requests(driver):
    """Limpia todos los requests almacenados"""
    print("🧹 Limpiando cache de requests...")
    try:
        driver.requests.clear()
        del driver.requests[:]
        time.sleep(1)
        print("✅ Cache de requests limpiado")
    except Exception as e:
        print(f"⚠️ Error limpiando requests: {e}")


def dividir_rango_fechas(fecha_inicio, fecha_fin, dias_por_bloque=DIAS_POR_BLOQUE):
    """Divide un rango de fechas en bloques de X días"""
    bloques = []
    fecha_actual = fecha_inicio

    while fecha_actual <= fecha_fin:
        fecha_fin_bloque = min(fecha_actual + timedelta(days=dias_por_bloque - 1), fecha_fin)
        bloques.append((fecha_actual, fecha_fin_bloque))
        fecha_actual = fecha_fin_bloque + timedelta(days=1)

    return bloques


def verificar_status_ajax(driver, timeout=TIMEOUT_AJAX):
    """Verifica que la llamada AJAX a buscar_sentencias devuelva 200"""
    print("🔍 Verificando status de buscar_sentencias...")
    tiempo_inicio = time.time()

    while time.time() - tiempo_inicio < timeout:
        for request in driver.requests:
            if "buscar_sentencias" in request.url and request.response:
                status = request.response.status_code
                print(f"📡 Status de buscar_sentencias: {status}")
                return status == 200
        time.sleep(1)

    print("⚠️ Timeout esperando respuesta de buscar_sentencias")
    return False


def recargar_pagina(driver):
    """Recarga la página actual"""
    print("🔄 Recargando página...")
    driver.refresh()
    time.sleep(5)


def crear_driver(navegador, worker_id=None):
    """Crea el driver según el navegador especificado"""

    # Configuración mejorada para selenium-wire
    seleniumwire_options = {
        'verify_ssl': False,
        'suppress_connection_errors': False,
        'connection_timeout': None,
        'request_storage': 'memory',
        'request_storage_max_size': 100,  # Guardar hasta 100 requests
    }

    driver = None

    try:
        if navegador == Navegador.CHROME:
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--ignore-ssl-errors")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Agregar user-agent personalizado para evitar detección
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            if MODO_HEADLESS:
                print(f"🤖 Chrome en modo HEADLESS (Worker {worker_id})")
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
            else:
                print(f"🖥️ Chrome en modo VISIBLE (Worker {worker_id})")

            driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)

        elif navegador == Navegador.EDGE:
            # Para Edge, necesitamos importar los módulos específicos
            try:
                from msedge.selenium_tools import Edge, EdgeOptions

                options = EdgeOptions()
                options.use_chromium = True
                options.add_argument("--start-maximized")

                if MODO_HEADLESS:
                    print("🤖 Edge en modo HEADLESS")
                    options.add_argument("--headless")
                    options.add_argument("--window-size=1920,1080")
                else:
                    print("🖥️ Edge en modo VISIBLE")

                # Crear driver de Edge con selenium-wire
                from seleniumwire import webdriver as sw_webdriver
                driver = sw_webdriver.Edge(options=options, seleniumwire_options=seleniumwire_options)

            except ImportError:
                print("⚠️ No se pudo importar Edge, usando Chrome como fallback")
                return crear_driver(Navegador.CHROME, worker_id)

        driver.set_window_size(1920, 1080)

        # Habilitar captura de requests
        driver.scopes = ['.*buscar_sentencias.*']  # Solo capturar requests relevantes

        # Registrar el driver
        estado_global.agregar_driver(driver)

        return driver

    except Exception as e:
        print(f"❌ Error creando driver: {e}")
        if driver:
            driver.quit()
        raise


# ========================================
# FUNCIONES DE ENTRADA DE USUARIO
# ========================================
def pedir_fecha(mensaje):
    while True:
        fecha_str = input(mensaje).strip()
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            return fecha
        except Exception:
            print("Fecha inválida. Usa formato YYYY-MM-DD.")


def pedir_tipo_busqueda():

    opciones = [
        ("Laborales", "https://juris.pjud.cl/busqueda?Laborales", "Lab"),
        #("Cobranza", "https://juris.pjud.cl/busqueda?Cobranza", "Cob"),
        ("Penales", "https://juris.pjud.cl/busqueda?Penales", "Pen"),
        #("Familia", "https://juris.pjud.cl/busqueda?Familia", "Fam"),
        #("Civiles", "https://juris.pjud.cl/busqueda?Civiles", "Civ"),
    ]

    return opciones

def pedir_carpeta(key):

    opciones = {
        "Laborales": r"C:\temp\fallos\Json\Laborales",
        # "Cobranza": r"C:\temp\fallos\Json\Cobranza",
        "Penales": r"C:\temp\fallos\Json\Penal",
        # "Familia": r"C:\temp\fallos\Json\Familia",
        # "Civiles": r"C:\temp\fallos\Json\Civiles",
    }

    # Devuelve la ruta si la clave existe, sino None
    return opciones.get(key)



# ========================================
# FUNCIONES DE INTERACCIÓN CON SELENIUM
# ========================================
def expandir_mejorado(driver, boton):
    """Versión mejorada con más robustez para headless"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton)
        time.sleep(0.5)

        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(boton))

        try:
            boton.click()
        except Exception:
            print("    ⚠️ Click normal falló, usando JavaScript")
            driver.execute_script("arguments[0].click();", boton)

        time.sleep(0.5)
    except Exception as e:
        print(f"    ⚠️ Error en expandir: {e}")


def seleccionar_checkbox_mejorado(driver, checkbox):
    """Versión mejorada para headless con más verificaciones"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", checkbox)
        time.sleep(0.3)

        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(checkbox))

        if not checkbox.is_selected():
            try:
                checkbox.click()
            except Exception:
                print("    ⚠️ Click en checkbox falló, usando JavaScript")
                driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(0.2)

    except Exception as e:
        print(f"    ⚠️ Error seleccionando checkbox: {e}")


def seleccionar_rango_fechas_mejorado(driver, fecha_inicio, fecha_fin):
    """Versión mejorada con más tiempo para headless"""
    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
        print(f"⚠️ Fechas intercambiadas automáticamente: inicio={fecha_inicio}, fin={fecha_fin}")

    anio_inicio = fecha_inicio.year
    anio_fin = fecha_fin.year

    print(f"📅 Seleccionando fechas desde {fecha_inicio} hasta {fecha_fin}")

    ESPERA_EXPANSION = 1.0
    ESPERA_MES = 0.5

    for anio in range(anio_inicio, anio_fin + 1):
        if estado_global.shutdown_requested:
            return

        print(f"🔍 Procesando año {anio}")

        try:
            boton_anio = driver.find_element(By.XPATH,
                                             f'//span[@class="btn_expandir_faceta_fecha" and @data-id_hijos="arbol_facetas_{anio}"]')
            expandir_mejorado(driver, boton_anio)
        except Exception:
            pass
        time.sleep(ESPERA_EXPANSION)

        mes_inicio_anio = fecha_inicio.month if anio == anio_inicio else 1
        mes_fin_anio = fecha_fin.month if anio == anio_fin else 12

        if anio != anio_inicio and anio != anio_fin:
            try:
                print(f"✅ Seleccionando año completo {anio}")
                checkbox_anio = driver.find_element(By.ID, f'fecha_{anio}')
                seleccionar_checkbox_mejorado(driver, checkbox_anio)
                continue
            except Exception:
                print(f"⚠️ No se pudo seleccionar año completo {anio}, seleccionando por meses")

        for mes in range(mes_inicio_anio, mes_fin_anio + 1):
            if estado_global.shutdown_requested:
                return

            nombre_mes = MESES[mes]
            print(f"  🔍 Procesando mes {nombre_mes} ({mes})")

            try:
                boton_mes = driver.find_element(By.XPATH,
                                                f'//span[@class="btn_expandir_faceta_fecha" and @data-id_hijos="arbol_facetas_{anio}_{nombre_mes}"]')
                expandir_mejorado(driver, boton_mes)
            except Exception:
                pass
            time.sleep(ESPERA_MES)

            dia_inicio_mes = fecha_inicio.day if (anio == anio_inicio and mes == mes_inicio_anio) else 1
            dia_fin_mes = fecha_fin.day if (anio == anio_fin and mes == mes_fin_anio) else 31

            necesita_dias_especificos = (
                    (anio == anio_inicio and mes == mes_inicio_anio and dia_inicio_mes > 1) or
                    (anio == anio_fin and mes == mes_fin_anio and dia_fin_mes < 31)
            )

            if not necesita_dias_especificos:
                try:
                    print(f"    ✅ Seleccionando mes completo {nombre_mes}")
                    checkbox_mes = driver.find_element(By.ID, f'fecha_{anio}{str(mes).zfill(2)}')
                    seleccionar_checkbox_mejorado(driver, checkbox_mes)
                    continue
                except Exception:
                    print(f"    ⚠️ No se pudo seleccionar mes completo {nombre_mes}, seleccionando por días")

            print(f"    🔍 Seleccionando días del {dia_inicio_mes} al {dia_fin_mes}")
            for dia in range(dia_inicio_mes, dia_fin_mes + 1):
                if estado_global.shutdown_requested:
                    return

                id_dia = f"fecha_{anio}{str(mes).zfill(2)}{str(dia).zfill(2)}"
                try:
                    checkbox_dia = driver.find_element(By.ID, id_dia)
                    seleccionar_checkbox_mejorado(driver, checkbox_dia)
                    print(f"      ✅ Día {dia} seleccionado")
                except Exception:
                    print(f"      ⚠️ No se pudo seleccionar día {dia}")
                    continue


def intentar_click_mejorado(driver, by, valor, descripcion, max_reintentos=5, espera=3):
    """Versión mejorada con más tiempo y estrategias para headless"""
    for intento in range(max_reintentos):
        if estado_global.shutdown_requested:
            return False

        try:
            print(f"Intentando click en '{descripcion}' (intento {intento + 1}/{max_reintentos})")

            elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((by, valor)))

            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
            time.sleep(1)

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((by, valor)))

            try:
                elem.click()
                print(f"✔️ Click exitoso en '{descripcion}' con click normal")
                return True
            except Exception:
                print(f"⚠️ Click normal falló, intentando con JavaScript")
                driver.execute_script("arguments[0].click();", elem)
                print(f"✔️ Click exitoso en '{descripcion}' con JavaScript")
                return True

        except Exception as e:
            print(f"⚠️ Falló click en '{descripcion}' ({e}), reintentando en {espera}s...")
            time.sleep(espera)

    print(f"❌ No se pudo hacer click en '{descripcion}' después de {max_reintentos} reintentos.")
    return False


def esperar_ajax(driver, timeout=30):
    for _ in range(timeout * 2):
        if estado_global.shutdown_requested:
            return False

        try:
            ajax_activo = driver.execute_script("return (window.jQuery && jQuery.active) || 0")
            if ajax_activo == 0:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print("⚠️ Timeout esperando AJAX.")
    return False


def verificar_paginacion_disponible(driver):
    """Verifica si hay más páginas disponibles"""
    try:
        boton_siguiente = driver.find_element(By.ID, "btnPaginador_pagina_adelante")
        if not boton_siguiente.is_enabled() or "disabled" in boton_siguiente.get_attribute("class"):
            print("🛑 Botón 'siguiente' deshabilitado - no hay más páginas")
            return False

        try:
            elementos_paginacion = driver.find_elements(By.CSS_SELECTOR,
                                                        "[class*='pagina'], [class*='paginador'], [id*='pagina']")
            for elem in elementos_paginacion:
                texto = elem.text.lower()
                if "página" in texto and "de" in texto:
                    print(f"📄 Información de paginación: {elem.text}")
                    if "página 1 de 1" in texto:
                        print("🛑 Solo hay 1 página disponible")
                        return False
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"⚠️ Error verificando paginación: {e}")
        return False


def obtener_json_pagina_actual(driver, pagina_esperada, jsons_procesados, timeout=60):
    """Obtiene el JSON de la página actual con múltiples protecciones"""
    print(f"🔍 Buscando JSON único para página {pagina_esperada}...")
    tiempo_inicio = time.time()

    # Contador de duplicados consecutivos
    duplicados_consecutivos = 0
    max_duplicados = 3

    # Contador de errores 419
    errores_419_consecutivos = 0
    max_errores_419 = 3

    while time.time() - tiempo_inicio < timeout:
        if estado_global.shutdown_requested:
            return None

        time.sleep(3)
        esperar_ajax(driver, 10)

        # Buscar SOLO requests con status 200
        requests_validos = []
        tiene_error_419 = False

        print(f"\n🔍 Analizando últimos requests...")

        # Revisar solo los últimos 10 requests para evitar procesar viejos
        for req in driver.requests[-10:]:
            if req.response and "buscar_sentencias" in req.url:
                status = req.response.status_code
                print(f"  Request encontrado - Status: {status}")

                if status == 200:
                    requests_validos.append(req)
                    print(f"  ✅ Request válido agregado")
                elif status == 419:
                    print(f"  ⚠️ Error 419 detectado - Token expirado")
                    tiene_error_419 = True
                    errores_419_consecutivos += 1

        # Si hay error 419 y no hay requests válidos, señalar para recargar
        if tiene_error_419 and not requests_validos:
            if errores_419_consecutivos >= max_errores_419:
                print(f"  🚨 {errores_419_consecutivos} errores 419 consecutivos sin requests válidos")
                return "ERROR_419"
            print(f"  ⏳ Solo errores 419, esperando más requests...")
            continue

        if not requests_validos:
            print(f"  ⏳ No hay requests válidos (status 200)...")
            continue

        # Resetear contador de errores 419 si encontramos requests válidos
        errores_419_consecutivos = 0

        # Procesar SOLO el más reciente request válido (status 200)
        req = requests_validos[-1]

        try:
            body = req.response.body
            encoding = req.response.headers.get('Content-Encoding', '')

            if encoding == 'gzip':
                body = gzip.decompress(body)
            elif encoding == 'deflate':
                body = zlib.decompress(body)

            # Verificar que el body no esté vacío
            if not body:
                print(f"  ❌ Body vacío, continuando...")
                continue

            # Intentar decodificar JSON
            try:
                json_data = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError as e:
                print(f"  ❌ No es JSON válido: {e}")
                print(f"  Body preview: {body[:100].decode('utf-8', errors='ignore')}...")
                continue

            # Verificar estructura esperada
            if not isinstance(json_data, dict) or "response" not in json_data:
                print(f"  ❌ JSON no tiene estructura esperada")
                continue

            response = json_data.get("response", {})
            docs = response.get("docs", [])
            num_found = response.get("numFound", 0)
            start = response.get("start", 0)

            print(f"  📦 JSON válido: {len(docs)} documentos, start={start}, total={num_found}")

            # Verificar si estamos en la última página
            if start + len(docs) >= num_found:
                print(f"  🏁 Última página detectada: mostrando {start + len(docs)} de {num_found} documentos")
                # Guardar este último JSON antes de retornar
                return json_data

            if not docs:
                print(f"  ❌ JSON sin documentos, continuando...")
                continue

            # Verificar duplicados
            contenido_str = json.dumps(docs, sort_keys=True)
            hash_contenido = hashlib.md5(contenido_str.encode()).hexdigest()

            if hash_contenido in jsons_procesados:
                print(f"  🔄 JSON duplicado detectado (hash: {hash_contenido[:12]}...)")
                duplicados_consecutivos += 1

                if duplicados_consecutivos >= max_duplicados:
                    print(f"  🛑 {duplicados_consecutivos} duplicados consecutivos - asumiendo última página")
                    return "ULTIMA_PAGINA"
                continue

            # Si encontramos un JSON nuevo, resetear contador
            duplicados_consecutivos = 0
            jsons_procesados.add(hash_contenido)
            print(f"  🎉 JSON nuevo encontrado: {len(docs)} documentos (hash: {hash_contenido[:12]}...)")
            return json_data

        except Exception as e:
            print(f"  ❌ Error procesando request: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"  ⏰ Timeout: No se encontró JSON válido")
    return None


def verificar_ultima_pagina(driver, json_data):
    """Verifica si estamos en la última página basándose en el JSON"""
    if not json_data or json_data == "ULTIMA_PAGINA":
        return True

    if isinstance(json_data, dict):
        response = json_data.get("response", {})
        num_found = response.get("numFound", 0)
        docs = response.get("docs", [])
        start = response.get("start", 0)

        # Si start + docs >= numFound, estamos en la última página
        if start + len(docs) >= num_found:
            print(f"📊 Última página detectada: {start + len(docs)} de {num_found} documentos")
            return True

    return False


# ========================================
# FUNCIONES DE CONFIGURACIÓN
# ========================================
def aplicar_configuracion_inicial(driver, wait):
    """Aplica la configuración inicial: 50 resultados, orden recientes"""
    # Cambiar a 50 resultados
    for intento in range(5):
        if estado_global.shutdown_requested:
            return

        try:
            select_elem = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "resultados_busqueda_registros_por_pagina"))
            )
            select = Select(select_elem)
            select.select_by_value('50')
            print("✅ Cambiado a 50 resultados por página")
            break
        except Exception as e:
            print(f"⚠️ Reintentando cambiar a 50 resultados... ({e})")
            time.sleep(2)

    esperar_ajax(driver, 10)
    time.sleep(2)

    # Cambiar orden a recientes
    for intento in range(5):
        if estado_global.shutdown_requested:
            return

        try:
            orden_elem = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "orden_resultados_busqueda"))
            )
            orden_select = Select(orden_elem)
            orden_select.select_by_value('recientes')
            print("✅ Cambiado orden a 'recientes'")
            break
        except Exception as e:
            print(f"⚠️ Reintentando cambiar a 'recientes'... ({e})")
            time.sleep(2)

    esperar_ajax(driver, 10)
    time.sleep(2)


def navegar_a_pagina(driver, pagina_destino, pagina_actual):
    """Navega a una página específica desde la página actual"""
    print(f"🚀 Navegando de página {pagina_actual} a página {pagina_destino}")

    if pagina_destino == pagina_actual:
        return True

    # Si necesitamos retroceder
    if pagina_destino < pagina_actual:
        diferencia = pagina_actual - pagina_destino
        for _ in range(diferencia):
            if estado_global.shutdown_requested:
                return False
            if not intentar_click_mejorado(driver, By.ID, "btnPaginador_pagina_atras", "Página anterior"):
                return False
            esperar_ajax(driver, 10)
            time.sleep(3)

    # Si necesitamos avanzar
    elif pagina_destino > pagina_actual:
        diferencia = pagina_destino - pagina_actual
        for _ in range(diferencia):
            if estado_global.shutdown_requested:
                return False
            if not intentar_click_mejorado(driver, By.ID, "btnPaginador_pagina_adelante", "Página siguiente"):
                return False
            esperar_ajax(driver, 10)
            time.sleep(3)

    return True


# ========================================
# MANEJO DE ERRORES
# ========================================
def manejar_error_pagina(driver, wait, url_busqueda, fecha_inicio, fecha_fin, pagina_actual, pagina_objetivo):
    """Maneja errores en páginas según la lógica especificada"""
    print(f"🚨 Manejando error en página {pagina_actual}")

    if estado_global.shutdown_requested:
        return False

    if pagina_actual == 1:
        # Primera página: recargar y reiniciar
        print("📍 Error en primera página - recargando y reiniciando")
        recargar_pagina(driver)
        time.sleep(5)
        return None  # Señal para reiniciar todo el proceso

    else:
        # Páginas 2+: retroceder y avanzar
        print(f"📍 Error en página {pagina_actual} - aplicando estrategia retroceder/avanzar")

        for intento in range(MAX_REINTENTOS):
            if estado_global.shutdown_requested:
                return False

            print(f"🔄 Intento {intento + 1}/{MAX_REINTENTOS}")

            # Retroceder una página
            if navegar_a_pagina(driver, pagina_actual - 1, pagina_actual):
                time.sleep(3)

                # Avanzar nuevamente
                if navegar_a_pagina(driver, pagina_objetivo, pagina_actual - 1):
                    time.sleep(ESPERA_INICIAL)

                    # Verificar status
                    if verificar_status_ajax(driver):
                        print("✅ Recuperación exitosa")
                        return True

            # Si falla, recargar y reaplicar todo
            print("⚠️ Recargando página y reaplicando filtros")
            driver.get(url_busqueda)
            time.sleep(5)

            # Reaplicar configuración
            aplicar_configuracion_inicial(driver, wait)

            # Reaplicar filtros de fecha
            wait.until(EC.presence_of_element_located((By.ID, "capa_arbol_facetas_fechas")))
            time.sleep(1.5)

            try:
                panel = driver.find_element(By.XPATH, '//div[@id="capa_arbol_facetas_fechas"]')
                if not panel.is_displayed():
                    driver.find_element(By.XPATH, '//i[contains(@class,"fa-plus-square")]').click()
                    time.sleep(0.5)
            except Exception:
                pass

            seleccionar_rango_fechas_mejorado(driver, fecha_inicio, fecha_fin)

            # Limpiar requests antes de buscar
            limpiar_requests(driver)

            # Buscar
            if intentar_click_mejorado(driver, By.XPATH, '//button[contains(text(), "Buscar")]', "Buscar"):
                time.sleep(ESPERA_INICIAL)

                # Navegar a la página objetivo
                if navegar_a_pagina(driver, pagina_objetivo, 1):
                    if verificar_status_ajax(driver):
                        print("✅ Recuperación completa exitosa")
                        return True

        print("❌ Fallo después de todos los reintentos")
        return False


# ========================================
# PROCESAMIENTO DE BLOQUES
# ========================================
def procesar_bloque_fechas(navegador, url_busqueda, nombre_tipo, carpeta, fecha_inicio, fecha_fin, bloque_id, worker_id):
    """Procesa un bloque de fechas específico"""
    if estado_global.shutdown_requested:
        return False

    print(f"\n{'=' * 60}")
    print(f"🚀 Worker {worker_id} iniciando procesamiento del bloque {bloque_id}")
    print(f"📅 Fechas: {fecha_inicio} a {fecha_fin}")
    print(f"🌐 Navegador: {navegador.value}")
    print(f"{'=' * 60}\n")

    driver = None
    try:
        # Crear driver según el navegador
        driver = crear_driver(navegador, worker_id)
        wait = WebDriverWait(driver, 60)

        # Función auxiliar para aplicar todos los filtros
        def aplicar_filtros_completos():
            """Aplica configuración inicial y filtros de fecha"""
            aplicar_configuracion_inicial(driver, wait)

            # Aplicar filtros de fecha
            wait.until(EC.presence_of_element_located((By.ID, "capa_arbol_facetas_fechas")))
            time.sleep(1.5)

            try:
                panel = driver.find_element(By.XPATH, '//div[@id="capa_arbol_facetas_fechas"]')
                if not panel.is_displayed():
                    driver.find_element(By.XPATH, '//i[contains(@class,"fa-plus-square")]').click()
                    time.sleep(0.5)
            except Exception:
                pass

            seleccionar_rango_fechas_mejorado(driver, fecha_inicio, fecha_fin)

            # Limpiar requests antes de buscar
            limpiar_requests(driver)

            # Buscar
            if intentar_click_mejorado(driver, By.XPATH, '//button[contains(text(), "Buscar")]', "Buscar"):
                print(f"⏳ Esperando {ESPERA_INICIAL} segundos después de buscar...")
                time.sleep(ESPERA_INICIAL)
                return True
            return False

        # Inyectar JavaScript para capturar JSON
        script = """
        // Interceptar fetch
        const originalFetch = window.fetch;
        window.capturedResponses = [];

        window.fetch = function(...args) {
            return originalFetch.apply(this, args)
                .then(response => {
                    if (args[0].includes('buscar_sentencias')) {
                        response.clone().json().then(data => {
                            window.capturedResponses.push({
                                url: args[0],
                                data: data,
                                timestamp: Date.now()
                            });
                        }).catch(e => console.error('Error cloning response:', e));
                    }
                    return response;
                });
        };
        """

        # Proceso principal con reintentos
        reintentar_todo = True
        intentos_totales = 0
        max_intentos_totales = 3

        while reintentar_todo and intentos_totales < max_intentos_totales and not estado_global.shutdown_requested:
            reintentar_todo = False
            intentos_totales += 1

            # Cargar página
            driver.get(url_busqueda)
            time.sleep(5)

            # Inyectar el script después de cargar la página
            driver.execute_script(script)

            # Aplicar todos los filtros
            if not aplicar_filtros_completos():
                print("❌ No se pudieron aplicar los filtros")
                reintentar_todo = True
                continue

            # Verificar status inicial
            if not verificar_status_ajax(driver):
                print("❌ Error en status inicial - recargando página")
                recargar_pagina(driver)
                reintentar_todo = True
                continue

            # Procesar páginas
            pagina = 1
            jsons_procesados = set()
            pagina_con_error_419 = None

            while not estado_global.shutdown_requested:
                print(f"\n🔄 Worker {worker_id}: Procesando página {pagina}...")

                # Verificar si hay más páginas disponibles
                if pagina > 1 and not verificar_paginacion_disponible(driver):
                    print("🛑 No hay más páginas disponibles")
                    break

                # Intentar obtener JSON
                json_data = obtener_json_pagina_actual(driver, pagina, jsons_procesados, timeout=60)

                # Manejar error 419
                if json_data == "ERROR_419":
                    print(f"🚨 Error 419 detectado en página {pagina} - recargando y reintentando")
                    pagina_con_error_419 = pagina

                    # Recargar página completa
                    driver.get(url_busqueda)
                    time.sleep(5)
                    driver.execute_script(script)

                    # Reaplicar todos los filtros
                    if not aplicar_filtros_completos():
                        print("❌ No se pudieron reaplicar los filtros")
                        reintentar_todo = True
                        break

                    # Navegar a la página donde ocurrió el error
                    if pagina_con_error_419 > 1:
                        print(f"📍 Navegando a la página {pagina_con_error_419} donde ocurrió el error...")
                        if not navegar_a_pagina(driver, pagina_con_error_419, 1):
                            print("❌ No se pudo navegar a la página del error")
                            reintentar_todo = True
                            break
                        time.sleep(ESPERA_INICIAL)

                    # Reintentar obtener el JSON
                    continue

                # Verificar si es señal de última página
                if json_data == "ULTIMA_PAGINA":
                    print("🏁 Última página alcanzada - no hay más datos nuevos")
                    break

                # Si no funciona, intentar con JavaScript
                if not json_data:
                    print("🔍 Intentando capturar JSON con JavaScript...")
                    time.sleep(5)
                    captured = driver.execute_script("return window.capturedResponses;")
                    if captured and len(captured) > 0:
                        json_data = captured[-1]['data']
                        print(
                            f"  🎉 JSON capturado con JavaScript: {len(json_data.get('response', {}).get('docs', []))} documentos")

                if json_data and json_data != "ULTIMA_PAGINA" and json_data != "ERROR_419":
                    # Verificar si es la última página
                    if verificar_ultima_pagina(driver, json_data):
                        docs = json_data.get("response", {}).get("docs", [])
                        nombre_archivo = estado_global.obtener_nombre_unico(
                            carpeta, navegador.value, fecha_inicio, fecha_fin, pagina, worker_id
                        )
                        with open(nombre_archivo, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                        print(f"✅ Guardado {os.path.basename(nombre_archivo)} ({len(docs)} registros)")
                        print("🏁 Última página procesada - finalizando bloque")
                        break

                    # Si no es la última página, continuar normalmente
                    docs = json_data.get("response", {}).get("docs", [])
                    nombre_archivo = estado_global.obtener_nombre_unico(
                        carpeta, navegador.value, fecha_inicio, fecha_fin, pagina, worker_id
                    )

                    with open(nombre_archivo, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)

                    print(f"✅ Guardado {os.path.basename(nombre_archivo)} ({len(docs)} registros)")
                else:
                    # Manejar error según la página
                    resultado = manejar_error_pagina(
                        driver, wait, url_busqueda, fecha_inicio, fecha_fin,
                        pagina, pagina
                    )

                    if resultado is None:  # Primera página - reiniciar todo
                        reintentar_todo = True
                        break
                    elif not resultado:  # Fallo definitivo
                        print("❌ Fallo definitivo - deteniendo proceso")
                        break
                    else:
                        # Recuperación exitosa - continuar
                        continue

                # Limpiar requests antes de cambiar de página
                limpiar_requests(driver)

                # Limpiar capturas JavaScript
                driver.execute_script("window.capturedResponses = [];")

                # Ir a siguiente página
                print(f"➡️ Intentando ir a página {pagina + 1}...")
                if intentar_click_mejorado(driver, By.ID, "btnPaginador_pagina_adelante", f"Siguiente página"):
                    pagina += 1
                    time.sleep(ESPERA_INICIAL)

                    # Verificar status después de cambiar página
                    if not verificar_status_ajax(driver):
                        resultado = manejar_error_pagina(
                            driver, wait, url_busqueda, fecha_inicio, fecha_fin,
                            pagina - 1, pagina
                        )
                        if not resultado:
                            break
                else:
                    print("🛑 No se pudo avanzar a siguiente página")
                    break

        print(f"\n✅ Worker {worker_id}: Bloque {bloque_id} completado")
        return True

    except Exception as e:
        print(f"\n❌ Worker {worker_id}: Error en bloque {bloque_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            estado_global.remover_driver(driver)
            try:
                driver.quit()
            except Exception:
                pass

'''
'''


def cover():
    titulo = " CRAWLER PRIMER INSTANCIA "
    autores = [
        "Desarrollado por:",
        "Enzo Lepe <enzo.lepe@thomsonreuters.com>",
        "Aníbal Cataldo [anibal.cataldo@thomsonreuters.com]"
    ]

    # Crear un marco decorativo
    ancho = 60
    print("=" * ancho)
    print(titulo.center(ancho))
    print("-" * ancho)
    for autor in autores:
        print(autor.center(ancho))
    print("=" * ancho)
    print("\nProceso iniciado...\n")


# ========================================
# FUNCIÓN PRINCIPAL
# ========================================
def main():
    #Cargamos la configuracion
    conf = Configuracion()
    configData = conf.getConfig()

    cover()
    ia = ProcessIA()
    ia.setModelVoces()
    ia.setModelLegislacion()


    try:
        # POr defecto debe incluir el ultimo año fecha_ini = 2024-11-14, fecha_fin = 2025-11-13
        fecha_ini = (datetime.now() - timedelta(days=RANGE_DAYS))
        fecha_fin = datetime.now()

        fecha_ini_str = fecha_ini.strftime("%Y-%m-%d")
        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")

        print(f"Intervalo de fechas: {fecha_ini_str} a {fecha_fin_str}.")

        materias_busqueda = pedir_tipo_busqueda()
        for materia in materias_busqueda:

            elementosGuardados = 0
            carpeta = pedir_carpeta(materia[0])
            os.makedirs(carpeta, exist_ok=True)
            Utils.cleanWorkingDir(carpeta)

            # Dividir fechas en bloques
            bloques = dividir_rango_fechas(fecha_ini, fecha_fin, DIAS_POR_BLOQUE)
            print(f"\n📊 Se crearon {len(bloques)} bloques de fechas:")
            for i, (inicio, fin) in enumerate(bloques, 1):
                dias = (fin - inicio).days + 1
                print(f"   Bloque {i}: {inicio} a {fin} ({dias} días)")


            num_workers = 3
            print(f"\n🚀 Iniciando ejecución paralela con {num_workers} navegadores Chrome...")

            # Cola de trabajo con bloques pendientes
            cola_bloques = queue.Queue()
            for i, (fecha_inicio, fecha_fin) in enumerate(bloques, 1):
                cola_bloques.put((i, fecha_inicio, fecha_fin))

            # Función worker mejorada
            def worker(worker_id):
                """Worker que procesa bloques de la cola"""
                bloques_procesados = 0

                while not cola_bloques.empty() and not estado_global.shutdown_requested:
                    try:
                        bloque_id, fecha_inicio, fecha_fin = cola_bloques.get(timeout=1)
                        print(f"\n🔧 Worker {worker_id} tomando bloque {bloque_id} de la cola")
                        print(f"   📊 Bloques restantes en cola: {cola_bloques.qsize()}")

                        # Usar siempre Chrome
                        navegador = Navegador.CHROME
                                                                      #Url        #Materia
                        resultado = procesar_bloque_fechas(navegador, materia[1], materia[0], carpeta,fecha_inicio, fecha_fin, bloque_id, worker_id)

                        if resultado:
                            bloques_procesados += 1
                            print(
                                f"✅ Worker {worker_id}: Bloque {bloque_id} completado (Total procesados por este worker: {bloques_procesados})")
                        else:
                            print(f"❌ Worker {worker_id}: Bloque {bloque_id} falló")

                        cola_bloques.task_done()

                    except queue.Empty:
                        print(f"📭 Worker {worker_id}: No hay más bloques en la cola")
                        break
                    except Exception as e:
                        print(f"❌ Worker {worker_id} error: {e}")
                        cola_bloques.task_done()

                print(f"\n🏁 Worker {worker_id} finalizado. Procesó {bloques_procesados} bloques en total")

            # Ejecutar workers
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futuros = []

                print(f"\n🚀 Iniciando {num_workers} workers...")
                for i in range(num_workers):
                    futuro = executor.submit(worker, i + 1)
                    futuros.append(futuro)
                    print(f"   ✅ Worker {i + 1} iniciado")

                print(f"\n⏳ Esperando a que todos los workers terminen...")

                # Esperar a que terminen todos
                for i, futuro in enumerate(as_completed(futuros), 1):
                    try:
                        futuro.result()
                        print(f"   ✅ Worker completado ({i}/{num_workers})")
                    except Exception as e:
                        print(f"   ❌ Error en worker: {e}")

            print("\n✅ Todos los workers han finalizado")


            if not estado_global.shutdown_requested:
                print("\n🎉 Proceso completo finalizado")
                print(f"📁 Archivos guardados en: {carpeta}")

            '''
            Termina exploracion por materia  
            '''
            jsonFiles = Utils.readFolder(carpeta, "json")
            for jsonFile in jsonFiles:

                with open(jsonFile, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Acceder a la lista de documentos
                    docs = data["response"]["docs"]

                    for doc in docs:

                        print(f"Estamos procesando el fallo:{ doc["caratulado_s"] }.")

                        fallo = Fallo()
                        fallo.fecha = Utils.formatDate(doc["fec_sentencia_sup_dt"], '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S')  # Fecha sentencia
                        fallo.rol = doc["rol_era_sup_s"]  # Rol
                        fallo.partes = doc["caratulado_s"] # Partes

                        partes = Utils.getPartes(doc["caratulado_s"])
                        if len(partes) == 2:
                            fallo.parteActiva = partes[0]
                            fallo.partePasiva = partes[1]

                        tribunalId = Utils.getTribunalId(doc["gls_juz_s"]) #Tribunal
                        if tribunalId == "0":
                            print(f"El tribunal asociado al fallo({doc["gls_juz_s"]}), No se encuentra en el listado de tribunales requeridos.")
                            continue

                        fallo.tribunal = tribunalId
                        fallo.linkOrigen = doc["url_corta_acceso_sentencia"]
                        fallo.tag = materia[2]
                        if not fallo.exist():

                            texto_sentencia = Utils.getHtml(doc["texto_sentencia"])
                            fallo.numeroCaracteres = len(texto_sentencia)
                            fallo.texto = texto_sentencia

                            if fallo.numeroCaracteres < NUMERO_CARACTERES:
                                print(f"[!] EL fallo ROL: {fallo.rol}, y fecha: {fallo.fecha},  no supera los {NUMERO_CARACTERES} caractres .")
                                continue

                            if (fallo.save()):
                                print(f"[+] EL fallo ROL: {fallo.rol}, y fecha: {fallo.fecha}, ha sido registro.")
                                elementosGuardados+=1

                                #---------------------------------------------------------------------------------------
                                #Procedemos a analizar
                                # ---------------------------------------------------------------------------------------

                                print("Inicio proceso análisis de jurisprudencia.")

                                jsonAnalisis = ia.getAnalisis(fallo.texto)

                                if jsonAnalisis == '':
                                    print("[!] Problema en el JSON, posible timeout.")
                                    continue

                                jsonAnalisis = jsonAnalisis.replace("```json", "")
                                jsonAnalisis = jsonAnalisis.replace("```", "")

                                try:
                                    objAnalisis = json.loads(jsonAnalisis)
                                except Exception as e:
                                    print("[!] Error al convertir en Json:" + str(e))
                                    continue

                                fallo.titulo = objAnalisis.get("titulo_descriptor", "")
                                fallo.hecho = objAnalisis.get("tipo_de_hecho", "")
                                fallo.tipoRecurso = ia.getTipoRecurso(objAnalisis.get("tipo_de_recurso", 0))
                                fallo.resultado = ia.getResultado(objAnalisis.get("resultado", 0))

                                if fallo.update():

                                    fallo.delSumarios()
                                    sumarios = fallo.getSumarios(objAnalisis.get("sumarios", []))
                                    for sumario in sumarios:
                                        fallo.saveSumario(sumario)

                                    if len(sumarios) == 0:
                                        sumario = objAnalisis.get("sumarios", "")
                                        if sumario != "":
                                            fallo.saveSumario(sumario)

                                    fallo.delVoces(7352)
                                    voces = ia.getVoces(objAnalisis.get("voces", []))
                                    for voz in voces:
                                        fallo.saveVoces(voz["ID"], voz["Faceta"])

                                    fallo.saveVoces(7670, 'ANALISIS.IA')

                                    normas = objAnalisis.get("legislacion_aplicada", [])
                                    for norma in normas:
                                        lcon = ia.getLegislacion(norma)
                                        if lcon:
                                            text = f"IA - {norma}({lcon['Type']}:{lcon['Value']})"
                                            fallo.saveLegislacion(lcon["GUID"], text)

                                    arrIdEntidades = ia.getMinistros(objAnalisis)
                                    for idEntidad in arrIdEntidades:
                                        fallo.saveMinistro(idEntidad)

                                    print(f"[+] El fallo Id: {fallo.id}, ha sido registrado.")

                                else:
                                    print(f"[!] El fallo Id: {fallo.id}, no ha podido ser registrado")
                                fallo.updateFalloTerminado()

            #Enviar informacion por Telegram
            Utils.sendMessageTelegram(materia[0], elementosGuardados)

    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso interrumpido por el usuario")
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Error en el proceso principal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Asegurar que todos los drivers se cierren
        estado_global.cerrar_todos_drivers()

if __name__ == "__main__":
    main()