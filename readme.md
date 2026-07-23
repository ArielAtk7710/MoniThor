&lt;div align="center"&gt;

# ⚡ ATTACK7710 ⚡
## 🖥️ MoniThor M — Versión 2.1

*Software de Monitoreo Laboral Silencioso, Captura de Pantalla Automática y Registro de Teclado para Windows*

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Platform](https://img.shields.io/badge/OS-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#)
[![Author](https://img.shields.io/badge/Developer-ATTACK7710-red?style=for-the-badge&logo=github)](#)
[![Version](https://img.shields.io/badge/Version-V2.1-brightgreen?style=for-the-badge)](#)
[![Country](https://img.shields.io/badge/Ubicación-Bolivia%20%F0%9F%87%A7%F0%9F%87%B4-yellow?style=for-the-badge)](#)

---

&lt;/div&gt;

## 📌 Descripción General

**MoniThor M** es un software integral de supervisión de actividad laboral desarrollado en Python por **ATTACK7710**. Diseñado para ejecutarse de manera silenciosa, discreta y eficiente en entornos Windows (10/11), permite a los administradores de sistemas y supervisores auditar el rendimiento, uso de equipos y actividad del teclado en tiempo real.

---

## ✨ Características Principales (V2.1)

| Función | Descripción |
| :--- | :--- |
| 📸 **Capturas Automáticas** | Toma capturas de pantalla periódicas en intervalos personalizables (desde 3 segundos hasta 120 minutos). |
| ⌨️ **Keylogger Integrado** | Registra pulsaciones de teclas con *timestamps* en reportes diarios organizados (`Logs_Teclado/Reporte_Teclado_YYYY-MM-DD.txt`). |
| 🎬 **Generador de Video** | Convierte las capturas de pantalla en videos WebM (VP9) con opciones de FPS, calidad y resolución ajustables. |
| 🥷 **Ejecución Invisible** | Modo de monitoreo en segundo plano totalmente oculto al inicio. |
| 🔑 **Acceso Protegido** | Apertura del panel mediante la combinación global `Ctrl + Alt + M` y autenticación por contraseña. |
| 📝 **Persistencia y Registro** | Sistema de licencia permanente mediante el Registro de Windows (`winreg`) y opción de inicio automático con el sistema. |
| 🎨 **Panel Moderno** | Interfaz oscura e intuitiva construida sobre **CustomTkinter** con pestañas para control total. |
| 🔔 **Icono de Bandeja** | Acceso rápido desde la bandeja del sistema con menú contextual y doble clic para mostrar/ocultar. |
| 🔒 **Anti-Duplicado** | Sistema de mutex global que impide la ejecución de múltiples instancias simultáneas. |

---

## 🎮 Controles y Credenciales por Defecto

| Elemento | Detalle |
| :--- | :--- |
| ⌨️ **Atajo de despliegue** | `Ctrl + Alt + M` |
| 🔑 **Contraseña por defecto** | `VER CONTRASENA_ACCESO codigo fuente` |
| 📁 **Ruta / Ubicación** | `Escritorio/Capturas` y `Escritorio/Capturas/Logs_Teclado/` |
| 📹 **Videos Generados** | `Escritorio/Capturas/Videos_Generados/` |

---

## 🧩 Pestañas del Panel de Control

| Pestaña | Funcionalidad |
| :--- | :--- |
| **Monitoreo** | Iniciar/Detener capturas automáticas, ver estado en tiempo real y ocultar a bandeja. |
| **Keylogger** | Activar/Desactivar registro de teclas, contador de pulsaciones diarias, ver reporte del día y abrir carpeta de logs. |
| **Generar Video** | Seleccionar carpeta de imágenes, elegir imágenes individuales, configurar FPS (1-30), calidad (Baja/Media/Alta) y resolución (Original/HD/480p/360p). |
| **Configuración** | Ajustar intervalo de capturas (3s a 120min), cambiar carpeta de destino, activar inicio automático con Windows. |
| **Acerca de...** | Información del desarrollador, versión, contacto y fecha actual. |

---

## ⚙️ Configuración de Video

| Parámetro | Opciones |
| :--- | :--- |
| **FPS** | 1, 2, 5, 10, 15, 24, 30 |
| **Calidad** | Baja (800 Kbps), Media (2 Mbps), Alta (5 Mbps) |
| **Resolución** | Original, HD (1280x720), 480p (854x480), 360p (640x360) |
| **Formato** | WebM (VP9) — compatible con navegadores modernos |

---

## 📞 Créditos y Soporte

| Información | Detalle |
| :--- | :--- |
| 👨‍💻 **Desarrollador / Creador** | `ATTACK7710` |
| 🏷️ **Versión** | `V2.1` |
| 🌍 **País** | Bolivia 🇧🇴 |
| 📱 **Contacto de Soporte** | `+591 69856525` |

---

## 🧰 Tecnologías Utilizadas

| Tecnología | Propósito |
| :--- | :--- |
| **Python 3.x** | Lenguaje de desarrollo principal |
| **CustomTkinter** | Interfaz gráfica moderna, responsiva y en modo oscuro |
| **PyAutoGUI & Pillow** | Captura de pantalla y manipulación de imágenes |
| **Keyboard** | Captura global de atajos e hiper-escucha en segundo plano |
| **Winreg** | Gestión de configuración, licenciamiento e inicio en el Registro de Windows |
| **OpenCV (cv2)** | Generación de video WebM/MP4 desde secuencia de imágenes |
| **NumPy** | Procesamiento de matrices de imagen para conversión de formatos |
| **PyStray** | Icono de bandeja del sistema con menú contextual |
| **CTypes** | Gestión de mutex global y DPI awareness en Windows |
| **PyInstaller** | Empaquetado y compilación a ejecutable independiente (`.exe`) |

---

## 🚀 Guía de Instalación y Uso

### 1. Requisitos Previos
Asegúrate de contar con **Python 3.8+** instalado en tu sistema. Instala las librerías necesarias ejecutando:

```bash
pip install customtkinter keyboard pillow pyautogui pyinstaller pystray opencv-python numpy
```

### 2. Ejecutar Código Fuente

Para lanzar la aplicación en modo desarrollo:
```bash
python monitor.pyw
```
### 3. Compilar a Ejecutable (.exe)
Para generar un binario autónomo para Windows que solicite privilegios de administrador automáticamente:
```bash
pyinstaller --noconsole --onefile --uac-admin monitor.pyw
```
## 📋 Notas de la Versión 2.0
Nuevo: Generador de video integrado con soporte WebM (VP9) y fallback a MP4.\
Nuevo: Icono de bandeja del sistema con menú contextual.\
Nuevo: Sistema anti-duplicado mediante mutex global.\
Mejorado: Interfaz con pestañas organizadas por funcionalidad.\
Mejorado: Persistencia de configuración en Registro de Windows.


<div align="center">

*Desarrollado con ❤️ por ATTACK7710 — Todos los derechos reservados.*

</div>