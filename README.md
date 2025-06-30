# HP-150 Toolkit

**Conjunto completo de herramientas para trabajar con floppies y imágenes de disco HP-150**

## 🎯 ¿Qué es?

El HP-150 Toolkit es una suite completa para:
- Leer y escribir floppies físicos HP-150 con GreaseWeazle
- Convertir archivos TD0 (Teledisk) a imágenes funcionales
- Explorar y extraer archivos de imágenes HP-150
- Gestionar colecciones de software vintage
- Analizar y reparar discos dañados

## 🚀 Inicio Rápido

### 1. Manager Interactivo (Recomendado)
```bash
# Un solo comando para todo
./hp150_manager.sh
```
**El manager incluye menú completo con todas las funciones disponibles**

### 2. GUI para Explorar Imágenes
```bash
# Interfaz gráfica para manipular archivos
source venv/bin/activate
python3 run_gui.py --extended
```

### 3. Comandos Directos
```bash
# Leer floppy físico
scripts/read_hp150_floppy.sh mi_disco.img

# Escribir imagen a floppy
scripts/write_hp150_floppy.sh mi_disco.img

# Convertir TD0 a imagen
python3 src/converters/smart_td0_converter.py archivo.TD0 salida.img
```

## 🎮 Componentes Principales

### HP-150 Manager (`hp150_manager.sh`)
**Script maestro interactivo con menú completo:**
- 💾 Leer/escribir floppies físicos con GreaseWeazle
- 🔄 Conversión bidireccional TD0 ↔ IMG
- 🖥️ Lanzador de GUI extendida
- 🏛️ Descargador del museo HP (75 programas)
- 🛠️ Herramientas avanzadas y análisis
- 📊 Información de hardware y diagnósticos

### GUI Toolkit (`run_gui.py`)
**Interfaz gráfica para manipulación de imágenes:**
- 📂 **Explorador de archivos**: Lista completa con detalles
- 📤 **Extractor**: Archivos individuales o completos
- ✏️ **Editor**: Ver y editar archivos de texto
- 📊 **Análisis**: Espacio usado/libre, estructura del disco
- 🔍 **Compatibilidad**: Formato HP-150 nativo

### Sistema de Conversión
**Convertidores inteligentes con fallback automático:**
- `smart_td0_converter.py`: TD0 → IMG con recuperación
- `hp150_to_td0.py`: IMG → TD0 con múltiples métodos
- `scp_to_hp150_scan.py`: SCP → IMG (desde GreaseWeazle)
- Soporte para archivos corruptos o no estándar

## 🏗️ Arquitectura del Sistema

### Formato HP-150
- **Geometría**: 77 cilindros × 2 cabezas × 7 sectores/pista
- **Tamaño sector**: 256 bytes
- **Capacidad**: 270,336 bytes (264 KB)
- **Sistema de archivos**: FAT12 modificado

### Flujo de Trabajo Típico
```
Floppy Físico → [GreaseWeazle] → SCP → [Convertidor] → IMG
       ↓
TD0 Archive → [smart_td0_converter] → IMG → [GUI] → Archivos
       ↓
   Museo HP → [Descargador] → TD0 → [Batch Converter] → IMG
```

### Sistema de Fallback Inteligente
**Basado en `FALLBACK_INTELIGENTE.md`:**
- Análisis automático de discos desconocidos
- Detección de geometría por tamaño de archivo
- Generación automática de diskdefs para GreaseWeazle
- Recuperación de archivos con estructura dañada
- Soporte para formatos no estándar

## 🛠️ Características Avanzadas

### Conversión Bidireccional
- **TD0 → IMG**: Múltiples estrategias, recuperación de corruptos
- **IMG → TD0**: Compatible con Teledisk/SAMdisk
- **PC 720K ↔ HP-150**: Conversión entre formatos
- **SCP → IMG**: Desde capturas GreaseWeazle

### Gestión de Hardware
- **GreaseWeazle**: Lectura/escritura de floppies reales
- **Detección automática**: Drives y dispositivos
- **Verificación**: Integridad de lectura/escritura
- **Reintentos**: Para discos dañados

### Museo HP Integration
- **Descarga automática**: 75 programas del archivo HP
- **Conversión batch**: TD0 → IMG automático
- **Organización**: Por categorías de software
- **Modo prueba**: 3 elementos para testing

## 📁 Estructura del Proyecto

```
hp150_toolkit/
├── hp150_manager.sh             # 🎯 Manager principal interactivo
├── run_gui.py                   # 🖥️ Lanzador de GUI
├── FALLBACK_INTELIGENTE.md      # 🧠 Sistema de análisis automático
├── src/
│   ├── gui/
│   │   ├── hp150_gui_extended.py    # GUI extendida (principal)
│   │   ├── hp150_gui.py             # GUI básica
│   │   └── hp150_gui_extended_museum.py # GUI con integración museo
│   ├── tools/
│   │   └── hp150_fat.py             # Sistema de archivos HP-150
│   └── converters/
│       ├── smart_td0_converter.py   # Convertidor TD0 inteligente
│       ├── scp_to_hp150_scan.py     # SCP → IMG desde GreaseWeazle
│       ├── hp150_to_td0.py          # IMG → TD0 con múltiples métodos
│       └── pc720_hp150_converter.py # Conversión PC ↔ HP-150
├── scripts/
│   ├── read_hp150_floppy.sh         # Lectura de floppies físicos
│   ├── write_hp150_floppy.sh        # Escritura a floppies físicos
│   ├── download_hp150_museum.sh     # Descargador museo HP
│   └── test_museum_download.sh      # Descarga de prueba
└── HP150_CONVERTED/                 # Imágenes convertidas del museo
```

## 🔧 Requisitos

### Software
- **Python 3.7+** con tkinter
- **GreaseWeazle** (para floppies físicos)
- **SAMdisk** (opcional, para conversión TD0)

### Hardware (opcional)
- **GreaseWeazle v4** o superior
- **Floppy drive 3.5"** compatible
- **Floppies HP-150** originales o formateados

## 💡 Casos de Uso

### Para Coleccionistas
- Preservar colección de floppies HP-150
- Convertir archivos TD0 del museo HP
- Crear backups de software vintage

### Para Desarrolladores
- Analizar estructura de archivos HP-150
- Extraer código fuente histórico
- Estudiar sistemas de archivos vintage

### Para Usuarios HP-150
- Transferir archivos entre sistemas modernos y HP-150
- Acceder a software histórico
- Mantener sistema HP-150 operativo

## 🎓 Documentación Técnica

Consulta `FALLBACK_INTELIGENTE.md` para detalles sobre:
- Sistema de análisis automático de discos
- Algoritmos de detección de geometría
- Generación automática de diskdefs
- Técnicas de recuperación de datos

---

**🚀 ¡Perfecto para preservar y explorar el legado del HP-150!**
