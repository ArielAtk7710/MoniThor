# MoniThor M 🖥️

**MoniThor M** es un software de monitoreo de actividad laboral desarrollado en Python. Está diseñado para realizar capturas de pantalla automáticas de forma silenciosa y eficiente en sistemas operativos Windows 10/11, permitiendo a los administradores supervisar el rendimiento y uso de los equipos de la organización.

## ✨ Características Principales
* **Monitoreo en Segundo Plano:** El programa se ejecuta de forma totalmente oculta (interfaz invisible) tras el inicio.
* **Acceso Protegido por Hotkey:** Despliegue del panel de administración únicamente mediante la combinación de teclas `Ctrl + Alt + M`.
* **Seguridad por Contraseña:** Interfaz de acceso restringida mediante clave oculta con asteriscos (`*`).
* **Configuración Flexible:** Menú desplegable para ajustar el intervalo de capturas (desde 3 segundos hasta 120 minutos) y selector de carpetas locales de destino.
* **Persistencia Local:** Mecanismo de inicio automático con Windows a través del Registro (`winreg`) y sistema de licenciamiento local por seriales de un solo uso con periodo de prueba de 2 días.

## 🛠️ Tecnologías Utilizadas
* **Python 3** (Lenguaje principal)
* **CustomTkinter** (Interfaz gráfica moderna y responsiva)
* **PyAutoGUI & Pillow** (Captura de pantalla y procesamiento de imágenes)
* **Keyboard** (Escucha global de atajos de teclado en segundo plano)
* **PyInstaller** (Compilación y empaquetamiento a binario autónomo)

## 🚀 Instalación y Uso Local

### Requisitos Previos
Tener Python instalado y las dependencias del entorno configuradas:
```bash
pip install customtkinter keyboard pillow pyautogui pyinstaller
```

### Ejecución del Código Fuente
Para lanzar la aplicación en modo de desarrollo:
```bash
python monitor.pyw
```

### Compilación a Ejecutable (.exe)
Para generar el archivo ejecutable independiente que solicita privilegios de administrador nativos en Windows:
```bash
pyinstaller --noconsole --onefile --uac-admin monitor.pyw
```

## 📋 Créditos y Soporte
* **Creador:** Attack7710
* **Versión actual:** V1.0
* **Ubicación:** Bolivia 🇧🇴
* **Contacto de Soporte:** +591 69856525
