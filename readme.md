<div align="center">

# ⚡ ATTACK7710 ⚡
## 🖥️ MoniThor M — Versión 2.0

*Software de Monitoreo Laboral Silencioso, Captura de Pantalla Automática y Registro de Teclado para Windows*

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Platform](https://img.shields.io/badge/OS-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#)
[![Author](https://img.shields.io/badge/Developer-ATTACK7710-red?style=for-the-badge&logo=github)](#)
[![Version](https://img.shields.io/badge/Version-V2.0-brightgreen?style=for-the-badge)](#)
[![Country](https://img.shields.io/badge/Ubicación-Bolivia%20%F0%9F%87%A7%F0%9F%87%B4-yellow?style=for-the-badge)](#)

---

</div>

## 📌 Descripción General

**MoniThor M** es un software integral de supervisión de actividad laboral desarrollado en Python por **ATTACK7710**. Diseñado para ejecutarse de manera silenciosa, discreta y eficiente en entornos Windows (10/11), permite a los administradores de sistemas y supervisores auditar el rendimiento, uso de equipos y actividad del teclado en tiempo real.

---

## ✨ Características Principales (V2.0)

| Función | Descripción |
| :--- | :--- |
| 📸 **Capturas Automáticas** | Toma capturas de pantalla periódicas en intervalos personalizables (desde 3 segundos hasta 120 minutos). |
| ⌨️ **Keylogger Integrado** | Registra pulsaciones de teclas con *timestamps* en reportes diarios organizados (`Logs_Teclado/Reporte_Teclado_YYYY-MM-DD.txt`). |
| 🥷 **Ejecución Invisible** | Modo de monitoreo en segundo plano totalmente oculto al inicio. |
| 🔑 **Acceso Protegido** | Apertura del panel mediante la combinación global `Ctrl + Alt + M` y autenticación por contraseña. |
| 📝 **Persistencia y Registro** | Sistema de licencia permanente mediante el Registro de Windows (`winreg`) y opción de inicio automático con el sistema. |
| 🎨 **Panel Moderno** | Interfaz oscura e intuitiva construida sobre **CustomTkinter** con pestañas para control total. |

---

## 🧰 Tecnologías Utilizadas

| Tecnología | Propósito |
| :--- | :--- |
| **Python 3.x** | Lenguaje de desarrollo principal |
| **CustomTkinter** | Interfaz gráfica moderna, responsiva y en modo oscuro |
| **PyAutoGUI & Pillow** | Captura de pantalla y manipulación de imágenes |
| **Keyboard** | Captura global de atajos e hiper-escucha en segundo plano |
| **Winreg** | Gestión de configuración, licenciamiento e inicio en el Registro de Windows |
| **PyInstaller** | Empaquetado y compilación a ejecutable independiente (`.exe`) |

---

## 🚀 Guía de Instalación y Uso

1. Requisitos Previos
Asegúrate de contar con **Python 3.8+** instalado en tu sistema. Instala las librerías necesarias ejecutando:

```bash
pip install customtkinter keyboard pillow pyautogui pyinstaller

2. Ejecutar Código Fuente

Para lanzar la aplicación en modo desarrollo:
terminal: python monitor.pyw

3. Compilar a Ejecutable (.exe)
Para generar un binario autónomo para Windows que solicite privilegios de administrador automáticamente:
terminal: pyinstaller --noconsole --onefile --uac-admin monitor.pyw

## 🎮 Controles y Credenciales por Defecto

| Elemento | Detalle |
| :--- | :--- |
| ⌨️ **Atajo de despliegue** | `Ctrl + Alt + M` |
| 🔑 **Contraseña por defecto** | Configurada en la variable del código fuente al inicio según la versión |
| 🎫 **Licencia / Seriales** | Utiliza una de las claves de activación del listado interno en el primer inicio |
| 📁 **Ruta / Ubicación** | `Escritorio/Capturas` y `Escritorio/Capturas/Logs_Teclado/` |

---

## 📞 Créditos y Soporte

| Información | Detalle |
| :--- | :--- |
| 👨‍💻 **Desarrollador / Creador** | `ATTACK7710` |
| 🏷️ **Versión** | `V2.0` |
| 🌍 **País** | Bolivia 🇧🇴 |
| 📱 **Contacto de Soporte** | `+591 69856525` |

<div align="center">

---
*Desarrollado con ❤️ por ATTACK7710 — Todos los derechos reservados.*

</div>