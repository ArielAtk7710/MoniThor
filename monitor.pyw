import os
import time
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pyautogui
import keyboard
import sys
import winreg as reg

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASENA_ACCESO = "6525"  
COMBINACION_TECLAS = "ctrl+alt+m"  

# --- RUTA POR DEFECTO ---
CARPETA_DEFAULT = os.path.join(os.path.expanduser("~"), "Desktop", "Capturas")

# --- CLAVES DEL REGISTRO ---
REG_RUTA_BASE = r"Software\MoniThorM"
REG_KEY_ACTIVADO = "Activado"
REG_KEY_CARPETA = "CarpetaDestino"
REG_KEY_INTERVALO = "IntervaloSegundos"
REG_KEY_INICIO_AUTO = "InicioAutomatico"

# --- LISTA DE 50 SERIALES VÁLIDOS ---
SERIALES_VALIDOS = [
    "7xKqW2", "M9bVf1", "z4RnP8", "tG7mK5", "X2vYh9", "L6wBf3", "p8N1vG", "k4XmW9", "Z3vRj5", "H8fLq2",
    "c1M9xV", "F7nTz4", "r2G6hK", "W9vPj3", "b5XmN1", "Y8kTz4", "v3RfG9", "h6M1xK", "P7vNq2", "z4XmW8",
    "G9fTj1", "c3KbV5", "R8vNq2", "m1XfK7", "V9hTj4", "k2BmN6", "Z8fLq3", "x1M5vG", "H7nTz2", "r4KbV9",
    "W6vPj1", "b3XmN8", "Y9kTz5", "v2RfG4", "h7M1xK", "P8vNq3", "z5XmW9", "G1fTj6", "c4KbV2", "R9vNq5",
    "m2XfK8", "V1hTj7", "k3BmN4", "Z9fLq5", "x2M6vG", "H8nTz5", "r5KbV1", "W7vPj3", "b4XmN9", "Y1kTz6"
]

class MonitorApp:
    def __init__(self):
        self.monitoreando = False
        self.hilo_captura = None
        self.ventana_login = None  
        
        self.tiempos_map = {
            "3 segundos": 3, "5 segundos": 5, "10 segundos": 10, "15 segundos": 15,
            "30 segundos": 30, "60 segundos": 60, "1.5 minutos": 90, "3 minutos": 180,
            "5 minutos": 300, "10 minutos": 600, "15 minutos": 900, "30 minutos": 1800,
            "60 minutos": 3600, "120 minutos": 7200
        }
        
        # Mapeo inverso para recuperar la etiqueta del OptionMenu
        self.segundos_map = {v: k for k, v in self.tiempos_map.items()}

        # Cargar configuraciones persistentes del registro al iniciar
        self.cargar_configuraciones_registro()

        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.title("MoniThor M - Panel de Control")
        self.root.geometry("520x460")
        self.root.resizable(False, False)
        
        self.crear_interfaz_pestanas()
        self.root.withdraw()
        
        # --- VERIFICACIÓN DE ACTIVACIÓN LOCAL ---
        if not self.verificar_activacion_local():
            self.pedir_serial_activacion()
        else:
            # Si ya está activado anteriormente, arranca oculto y escucha el atajo
            keyboard.add_hotkey(COMBINACION_TECLAS, self.mostrar_ventana_autenticacion)
            self.root.mainloop()

    def cargar_configuraciones_registro(self):
        """Carga las configuraciones guardadas en el registro de Windows"""
        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE, 0, reg.KEY_READ)
            
            # Carpeta destino
            try:
                val_carpeta, _ = reg.QueryValueEx(clave, REG_KEY_CARPETA)
                self.carpeta_destino = val_carpeta if val_carpeta else CARPETA_DEFAULT
            except FileNotFoundError:
                self.carpeta_destino = CARPETA_DEFAULT

            # Intervalo en segundos
            try:
                val_intervalo, _ = reg.QueryValueEx(clave, REG_KEY_INTERVALO)
                self.intervalo_segundos = int(val_intervalo) if val_intervalo else 10
            except FileNotFoundError:
                self.intervalo_segundos = 10

            # Inicio automático
            try:
                val_inicio, _ = reg.QueryValueEx(clave, REG_KEY_INICIO_AUTO)
                self.inicio_automatico = (val_inicio == "True")
            except FileNotFoundError:
                self.inicio_automatico = False

            reg.CloseKey(clave)
        except FileNotFoundError:
            self.carpeta_destino = CARPETA_DEFAULT
            self.intervalo_segundos = 10
            self.inicio_automatico = False

    def guardar_configuracion_individual(self, nombre_clave, valor):
        """Guarda una clave y valor específico en el registro de Windows"""
        try:
            clave = reg.CreateKey(reg.HKEY_CURRENT_USER, REG_RUTA_BASE)
            reg.SetValueEx(clave, nombre_clave, 0, reg.REG_SZ, str(valor))
            reg.CloseKey(clave)
            return True
        except Exception as e:
            print(f"Error guardando en registro ({nombre_clave}): {e}")
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
        return self.guardar_configuracion_individual(REG_KEY_ACTIVADO, "True")

    def pedir_serial_activacion(self):
        """Muestra una ventana obligatoria para ingresar el número de serie si no está activado"""
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
        self.tabview = ctk.CTkTabview(self.root, width=480, height=380)
        self.tabview.pack(pady=10, padx=10)
        
        self.tabview.add("Monitoreo")
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

        # --- PESTAÑA 2: CONFIGURACIÓN ---
        lbl_tiempo = ctk.CTkLabel(self.tabview.tab("Configuración"), text="Intervalo de capturas de pantalla:", font=("Arial", 13, "bold"))
        lbl_tiempo.pack(anchor="w", padx=20, pady=(10, 2))
        
        self.combo_tiempo = ctk.CTkOptionMenu(self.tabview.tab("Configuración"), values=list(self.tiempos_map.keys()), command=self.cambiar_tiempo)
        
        # Seleccionar en la interfaz el valor cargado del registro
        etiqueta_actual = self.segundos_map.get(self.intervalo_segundos, "10 segundos")
        self.combo_tiempo.set(etiqueta_actual)
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

        self.check_inicio = ctk.CTkCheckBox(self.tabview.tab("Configuración"), text="Iniciar de forma oculta con Windows")
        if self.inicio_automatico:
            self.check_inicio.select()
        self.check_inicio.pack(pady=20)
        self.check_inicio.configure(command=self.configurar_inicio_automatico)

        # --- PESTAÑA 3: ACERCA DE... ---
        frame_creditos = ctk.CTkFrame(self.tabview.tab("Acerca de..."))
        frame_creditos.pack(fill="both", expand=True, padx=15, pady=15)

        fecha_hoy = datetime.now().strftime("%d/%m/%Y")

        info_texto = (
            f"Programa: MoniThor M\n"
            f"Descripción: Software de monitoreo laboral en Python que realiza capturas de pantalla automáticas cada cierto tiempo.\n\n"
            f"Creador: Attack7710 - Desarrollador\n"
            f"Versión: V1.4\n"
            f"Ubicación: Bolivia\n"
            f"Contacto: +591 69856525\n"
            f"Fecha: {fecha_hoy}"
        )

        lbl_info = ctk.CTkLabel(frame_creditos, text=info_texto, font=("Arial", 13), justify="left", wraplength=420)
        lbl_info.pack(pady=15, padx=15, anchor="w")

        self.root.protocol("WM_DELETE_WINDOW", self.ocultar_ventana)

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
            # Guardado automático de la carpeta en el registro
            self.guardar_configuracion_individual(REG_KEY_CARPETA, carpeta)

    def cambiar_tiempo(self, valor_seleccionado):
        self.intervalo_segundos = self.tiempos_map[valor_seleccionado]
        # Guardado automático del intervalo en el registro
        self.guardar_configuracion_individual(REG_KEY_INTERVALO, self.intervalo_segundos)

    def alternar_monitoreo(self):
        if not self.monitoreando:
            self.carpeta_destino = self.entry_carpeta.get()
            self.guardar_configuracion_individual(REG_KEY_CARPETA, self.carpeta_destino)
            
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
        try:
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, clave_ruta, 0, reg.KEY_SET_VALUE)
            is_checked = (self.check_inicio.get() == 1)
            
            # Guardar estado en el registro de la app
            self.guardar_configuracion_individual(REG_KEY_INICIO_AUTO, str(is_checked))

            if is_checked:
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