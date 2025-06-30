#!/bin/bash
#
# HP-150 Manager - Script principal para gestionar floppies HP-150
# Incluye funciones para leer, escribir y convertir imágenes de disco
#

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para mostrar el banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                        HP-150 MANAGER                           ║"
    echo "║                   Gestión de Floppies HP-150                    ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para mostrar el menú principal
show_menu() {
    echo -e "${CYAN}=== MENÚ PRINCIPAL ===${NC}"
    echo ""
    echo "1) 💾 Leer floppy físico a imagen"
    echo "2) 📀 Escribir imagen a floppy físico"
    echo "3) 🔄 Convertir archivo TD0 a imagen"
    echo "4) 🖥️  Abrir GUI (explorador de imágenes)"
    echo "5) ℹ️  Información del hardware"
    echo "6) 📋 Listar archivos de imagen"
    echo "7) 🏛️  Descargar software del museo HP"
    echo "8) 🛠️  Herramientas avanzadas"
    echo "9) ❓ Ayuda"
    echo "0) 🚪 Salir"
    echo ""
    echo -n "Seleccione una opción [0-9]: "
}

# Función para leer desde floppy
read_floppy() {
    clear
    echo -e "${GREEN}=== LEER DESDE FLOPPY FÍSICO ===${NC}"
    echo ""
    
    # Seleccionar drive
    echo "Seleccione el drive:"
    echo "0) Drive 0 (principal)"
    echo "1) Drive 1 (secundario)"
    echo ""
    echo -n "Drive (0-1): "
    read -r drive_num
    
    if [[ ! "$drive_num" =~ ^[01]$ ]]; then
        echo -e "${RED}Error: Debe seleccionar drive 0 o 1${NC}"
        return 1
    fi
    
    echo ""
    echo -n "Nombre del archivo de salida (.img): "
    read -r filename
    
    if [ -z "$filename" ]; then
        echo -e "${RED}Error: Debe especificar un nombre de archivo${NC}"
        return 1
    fi
    
    # Agregar extensión .img si no la tiene
    if [[ ! "$filename" =~ \.img$ ]]; then
        filename="${filename}.img"
    fi
    
    echo ""
    echo "Opciones de lectura:"
    echo "1) Lectura básica"
    echo "2) Lectura con verificación"
    echo "3) Lectura con más reintentos (para discos dañados)"
    echo "4) Solo información del disco"
    echo ""
    echo -n "Seleccione opción [1-4]: "
    read -r option
    
    # Usar EXACTAMENTE los mismos comandos que la GUI
    echo ""
    echo "=== PROCESO DE LECTURA (Como en la GUI) ==="
    echo "Paso 1: Leyendo disco en formato SCP nativo..."
    
    # Crear nombres de archivos temporales
    base_name="${filename%.*}"
    scp_file="${base_name}.scp"
    
    # Verificar opciones y construir comando GreaseWeazle
    cmd="gw read --drive=$drive_num --tracks=c=0-76:h=0-1:step=1 --retries=3"
    
    case $option in
        2)
            cmd="$cmd --verify"
            echo "Modo: Con verificación"
            ;;
        3)
            cmd="$cmd --retries=10"
            echo "Modo: Múltiples reintentos para discos dañados"
            ;;
        4)
            echo "Solo mostrando información del disco..."
            gw info --drive=$drive_num
            return 0
            ;;
        *)
            echo "Modo: Lectura básica"
            ;;
    esac
    
    cmd="$cmd \"$scp_file\""
    
    echo "Comando: $cmd"
    echo "Iniciando lectura del floppy..."
    echo "Esto puede tardar varios minutos dependiendo del estado del disco."
    echo ""
    
    # Ejecutar paso 1 - igual que la GUI
    eval $cmd
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Lectura SCP completada"
        echo ""
        echo "Paso 2: Convirtiendo SCP a formato HP-150..."
        
        # Paso 2 - Convertir usando el mismo convertidor que la GUI
        converter_path="src/converters/scp_to_hp150_scan.py"
        cmd2="python3 \"$converter_path\" \"$scp_file\" \"$filename\""
        
        echo "Comando: $cmd2"
        echo ""
        
        eval $cmd2
        
        if [ $? -eq 0 ]; then
            echo "✅ Conversión HP-150 completada"
            echo "✅ Proceso completado exitosamente!"
            
            # Mostrar información del archivo creado
            if [ -f "$filename" ]; then
                size=$(ls -lh "$filename" | awk '{print $5}')
                echo "Archivo creado: $filename"
                echo "Tamaño: $size"
                
                # Verificar tamaño
                size_bytes=$(stat -f%z "$filename" 2>/dev/null || stat -c%s "$filename" 2>/dev/null)
                expected_size=270336
                
                if [ "$size_bytes" -eq "$expected_size" ]; then
                    echo "✅ Tamaño correcto: $size_bytes bytes"
                else
                    echo "⚠️  Tamaño inesperado: $size_bytes bytes (esperado: $expected_size bytes)"
                fi
            fi
        else
            echo "❌ Error en conversión HP-150"
            echo "📁 Archivo SCP disponible: $scp_file"
        fi
    else
        echo ""
        echo "❌ Error durante la lectura del floppy"
        echo "Verifique:"
        echo "  - Que haya un disco insertado en la unidad"
        echo "  - Que el disco no esté dañado"
        echo "  - Que GreaseWeazle esté conectado correctamente"
        echo "  - Los permisos de escritura en el directorio actual"
    fi
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para escribir a floppy
write_floppy() {
    clear
    echo -e "${GREEN}=== ESCRIBIR A FLOPPY FÍSICO ===${NC}"
    echo ""
    
    # Seleccionar drive
    echo "Seleccione el drive:"
    echo "0) Drive 0 (principal)"
    echo "1) Drive 1 (secundario)"
    echo ""
    echo -n "Drive (0-1): "
    read -r drive_num
    
    if [[ ! "$drive_num" =~ ^[01]$ ]]; then
        echo -e "${RED}Error: Debe seleccionar drive 0 o 1${NC}"
        return 1
    fi
    
    # Listar archivos .img disponibles
    echo "Archivos .img disponibles:"
    echo ""
    ls -la *.img 2>/dev/null | awk '{print "  " $9 "  (" $5 " bytes)"}' | grep -v "^  $"
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}No hay archivos .img en el directorio actual${NC}"
    fi
    
    echo ""
    echo -n "Nombre del archivo de imagen: "
    read -r filename
    
    if [ -z "$filename" ]; then
        echo -e "${RED}Error: Debe especificar un archivo${NC}"
        return 1
    fi
    
    if [ ! -f "$filename" ]; then
        echo -e "${RED}Error: El archivo '$filename' no existe${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${YELLOW}¡ADVERTENCIA!${NC}"
    echo "Esta operación sobrescribirá completamente el contenido del floppy."
    echo -n "¿Está seguro de continuar? (escriba 'SI' para confirmar): "
    read -r confirm
    
    if [ "$confirm" != "SI" ]; then
        echo "Operación cancelada."
        return 1
    fi
    
    # Usar EXACTAMENTE el mismo comando que la GUI
    echo ""
    echo "=== PROCESO DE ESCRITURA (Como en la GUI) ==="
    echo "Opciones de escritura:"
    echo "1) Escritura básica"
    echo "2) Escritura con verificación"
    echo ""
    echo -n "Seleccione opción [1-2]: "
    read -r write_option
    
    # Construir comando igual que la GUI
    cmd="scripts/write_hp150_floppy.sh \"$filename\" --drive=$drive_num --force"
    
    case $write_option in
        2)
            cmd="$cmd --verify"
            echo "Modo: Con verificación"
            ;;
        *)
            echo "Modo: Escritura básica"
            ;;
    esac
    
    echo ""
    echo "Comando: $cmd"
    echo "Iniciando escritura del floppy..."
    echo "Esto puede tardar varios minutos."
    echo ""
    
    # Ejecutar - igual que la GUI
    eval $cmd
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función unificada para conversiones TD0 ↔ IMG
convert_disk_formats() {
    clear
    echo -e "${GREEN}=== CONVERSOR DE FORMATOS DE DISCO ===${NC}"
    echo ""
    echo -e "${CYAN}Conversiones bidireccionales entre formatos${NC}"
    echo ""
    echo "Opciones de conversión:"
    echo "1) 📀 TD0 → IMG (Teledisk a imagen)"
    echo "2) 💾 IMG → TD0 (Imagen a Teledisk)"
    echo "3) 🔙 Volver al menú principal"
    echo ""
    echo -n "Seleccione opción [1-3]: "
    read -r conversion_type
    
    case $conversion_type in
        1)
            convert_td0_to_img
            ;;
        2)
            convert_img_to_td0
            ;;
        3)
            return 0
            ;;
        *)
            echo -e "${RED}Opción inválida${NC}"
            echo -e "${GREEN}Presione Enter para continuar...${NC}"
            read -r
            ;;
    esac
}

# Función para convertir TD0 a IMG
convert_td0_to_img() {
    clear
    echo -e "${GREEN}=== CONVERTIR TD0 → IMG ===${NC}"
    echo ""
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        echo "Ejecute primero: python3 -m venv venv"
        return 1
    fi
    
    # Listar archivos TD0 disponibles
    echo "Archivos TD0 disponibles:"
    echo ""
    find . -name "*.TD0" -o -name "*.td0" 2>/dev/null | head -10 | while read -r file; do
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        echo "  $file  (${size:--} bytes)"
    done
    
    echo ""
    echo -n "Archivo TD0 a convertir: "
    read -r td0_file
    
    if [ -z "$td0_file" ]; then
        echo -e "${RED}Error: Debe especificar un archivo TD0${NC}"
        return 1
    fi
    
    if [ ! -f "$td0_file" ]; then
        echo -e "${RED}Error: El archivo '$td0_file' no existe${NC}"
        return 1
    fi
    
    echo -n "Nombre del archivo de salida (.img): "
    read -r output_file
    
    if [ -z "$output_file" ]; then
        # Generar nombre automáticamente
        output_file=$(basename "$td0_file" .TD0).img
        output_file=$(basename "$output_file" .td0).img
        echo "Usando nombre automático: $output_file"
    fi
    
    # Agregar extensión .img si no la tiene
    if [[ ! "$output_file" =~ \.img$ ]]; then
        output_file="${output_file}.img"
    fi
    
    echo ""
    echo "Iniciando conversión TD0 → IMG..."
    
    # Activar entorno virtual y convertir
    source venv/bin/activate
    python3 src/converters/smart_td0_converter.py "$td0_file" "$output_file"
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para convertir IMG a TD0
convert_img_to_td0() {
    clear
    echo -e "${GREEN}=== CONVERTIR IMG → TD0 ===${NC}"
    echo ""
    echo -e "${CYAN}Crea archivos TD0 compatibles con Teledisk/SAMdisk${NC}"
    echo ""
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        return 1
    fi
    
    # Listar archivos IMG disponibles
    echo "Archivos de imagen disponibles:"
    echo ""
    for img_file in *.img; do
        if [ -f "$img_file" ]; then
            size=$(stat -f%z "$img_file" 2>/dev/null || stat -c%s "$img_file" 2>/dev/null)
            if [ "$size" = "270336" ]; then
                echo "  $img_file  (HP-150 format, $size bytes)"
            else
                echo "  $img_file  ($size bytes - verificar formato)"
            fi
        fi
    done
    
    echo ""
    echo -n "Archivo IMG de entrada: "
    read -r input_file
    
    if [ -z "$input_file" ]; then
        echo -e "${RED}Error: Debe especificar un archivo${NC}"
        return 1
    fi
    
    if [ ! -f "$input_file" ]; then
        echo -e "${RED}Error: El archivo '$input_file' no existe${NC}"
        return 1
    fi
    
    echo -n "Archivo TD0 de salida (.TD0): "
    read -r output_file
    
    if [ -z "$output_file" ]; then
        # Generar nombre automáticamente
        output_file=$(basename "$input_file" .img).TD0
        echo "Usando nombre automático: $output_file"
    fi
    
    # Agregar extensión .TD0 si no la tiene
    if [[ ! "$output_file" =~ \.(TD0|td0)$ ]]; then
        output_file="${output_file}.TD0"
    fi
    
    echo ""
    echo "Método de conversión:"
    echo "1) 🚀 Automático (detecta herramientas disponibles)"
    echo "2) 💻 SAMdisk (recomendado si está instalado)"
    echo "3) 🔧 GreaseWeazle (alternativo)"
    echo "4) ✋ Manual (básico, siempre funciona)"
    echo ""
    echo -n "Seleccione método [1-4]: "
    read -r method_choice
    
    case $method_choice in
        1) method="auto" ;;
        2) method="samdisk" ;;
        3) method="greaseweazle" ;;
        4) method="manual" ;;
        *) method="auto" ;;
    esac
    
    echo ""
    echo "Iniciando conversión IMG → TD0..."
    
    # Activar entorno virtual y convertir
    source venv/bin/activate
    python3 src/converters/hp150_to_td0.py "$input_file" "$output_file" --method $method
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para abrir GUI
open_gui() {
    clear
    echo -e "${GREEN}=== ABRIENDO GUI ===${NC}"
    echo ""
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        return 1
    fi
    
    source venv/bin/activate
    echo "Abriendo GUI (explorador de imágenes)..."
    python3 run_gui.py --extended
}

# Función para mostrar información del hardware
hardware_info() {
    clear
    echo -e "${GREEN}=== INFORMACIÓN DEL HARDWARE ===${NC}"
    echo ""
    
    echo "Verificando GreaseWeazle..."
    if command -v gw >/dev/null 2>&1; then
        echo -e "${GREEN}✅ GreaseWeazle encontrado${NC}"
        echo ""
        gw --help | head -5
        echo ""
        echo "Información del dispositivo:"
        gw info 2>/dev/null || echo -e "${YELLOW}⚠️  No se pudo obtener información del dispositivo${NC}"
    else
        echo -e "${RED}❌ GreaseWeazle no encontrado${NC}"
        echo ""
        echo "Para instalar GreaseWeazle:"
        echo "1. Descargue desde: https://github.com/keirf/greaseweazle"
        echo "2. Siga las instrucciones de instalación"
        echo "3. Conecte el dispositivo GreaseWeazle"
    fi
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para listar archivos de imagen
list_images() {
    clear
    echo -e "${GREEN}=== ARCHIVOS DE IMAGEN DISPONIBLES ===${NC}"
    echo ""
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        return 1
    fi
    
    source venv/bin/activate
    
    echo "Archivos .img en el directorio actual:"
    echo ""
    
    for img_file in *.img; do
        if [ -f "$img_file" ]; then
            size=$(ls -lh "$img_file" | awk '{print $5}')
            echo -e "${CYAN}📁 $img_file${NC} ($size)"
            
            # Intentar mostrar información básica
            echo "   Analizando contenido..."
            python3 -c "
import sys
sys.path.append('src')
from tools.hp150_fat import HP150FileSystem
try:
    fs = HP150FileSystem('$img_file')
    files = fs.list_files()
    print(f'   📊 {len(files)} archivos encontrados')
    free_space = fs.get_free_space()
    print(f'   💾 Espacio libre: {free_space} KB')
except Exception as e:
    print(f'   ❌ Error al leer: {str(e)}')
" 2>/dev/null
            echo ""
        fi
    done
    
    if ! ls *.img 1> /dev/null 2>&1; then
        echo -e "${YELLOW}No hay archivos .img en el directorio actual${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para descarga del museo
museum_download() {
    clear
    echo -e "${GREEN}=== DESCARGA DEL MUSEO HP ===${NC}"
    echo ""
    echo -e "${CYAN}El museo HP contiene 75 elementos de software para HP-150${NC}"
    echo -e "${CYAN}incluyendo sistema, aplicaciones, juegos y herramientas.${NC}"
    echo ""
    echo "Opciones disponibles:"
    echo "1) 📋 Prueba: Descargar solo 3 elementos (recomendado primero)"
    echo "2) 📦 Descarga completa: Todos los 75 elementos del museo"
    echo "3) 🔙 Volver al menú principal"
    echo ""
    echo -n "Seleccione opción [1-3]: "
    read -r option
    
    case $option in
        1)
            echo ""
            echo -e "${CYAN}Ejecutando descarga de prueba (3 elementos)...${NC}"
            echo ""
            if [ -f "scripts/test_museum_download.sh" ]; then
                scripts/test_museum_download.sh
            else
                echo -e "${RED}Error: No se encontró scripts/test_museum_download.sh${NC}"
            fi
            ;;
        2)
            echo ""
            echo -e "${YELLOW}¡ADVERTENCIA!${NC}"
            echo "La descarga completa puede tardar varias horas y usar varios GB."
            echo -n "¿Está seguro de continuar? (escriba 'SI' para confirmar): "
            read -r confirm
            
            if [ "$confirm" = "SI" ]; then
                echo ""
                echo -e "${CYAN}Ejecutando descarga completa (75 elementos)...${NC}"
                echo ""
                if [ -f "scripts/download_hp150_museum.sh" ]; then
                    scripts/download_hp150_museum.sh
                else
                    echo -e "${RED}Error: No se encontró scripts/download_hp150_museum.sh${NC}"
                fi
            else
                echo "Operación cancelada."
            fi
            ;;
        3)
            return 0
            ;;
        *)
            echo -e "${RED}Opción inválida${NC}"
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para herramientas avanzadas
advanced_tools() {
    while true; do
        clear
        echo -e "${GREEN}=== HERRAMIENTAS AVANZADAS ===${NC}"
        echo ""
        echo "1) 🔄 Convertir entre PC 720K ↔ HP-150"
        echo "2) 🔍 Verificar integridad de imagen"
        echo "3) 📊 Análisis detallado de imagen"
        echo "4) 🔧 Reparar imagen dañada"
        echo "5) 📂 Comparar dos imágenes"
        echo "6) 🔙 Volver al menú principal"
        echo ""
        echo -n "Seleccione opción [1-6]: "
        read -r option
        
        case $option in
            1)
                pc720_hp150_converter
                ;;
            2|3|4|5)
                echo -e "${YELLOW}Funcionalidad en desarrollo...${NC}"
                echo -e "${GREEN}Presione Enter para continuar...${NC}"
                read -r
                ;;
            6)
                return 0
                ;;
            *)
                echo -e "${RED}Opción inválida. Presione Enter para continuar...${NC}"
                read -r
                ;;
        esac
    done
}

# Función para conversión PC 720K ↔ HP-150
pc720_hp150_converter() {
    clear
    echo -e "${GREEN}=== CONVERSOR PC 720K ↔ HP-150 ===${NC}"
    echo ""
    echo -e "${CYAN}Especificaciones:${NC}"
    echo "• PC 720K: 80c×2h×9s×512b = 737,280 bytes"
    echo "• HP-150:  77c×2h×7s×256b = 270,336 bytes"
    echo ""
    echo "Opciones de conversión:"
    echo "1) 🔄 PC 720K → HP-150"
    echo "2) 🔄 HP-150 → PC 720K"
    echo "3) 🔙 Volver al menú anterior"
    echo ""
    echo -n "Seleccione opción [1-3]: "
    read -r option
    
    case $option in
        1)
            convert_pc_to_hp150
            ;;
        2)
            convert_hp150_to_pc
            ;;
        3)
            return 0
            ;;
        *)
            echo -e "${RED}Opción inválida${NC}"
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para convertir PC 720K a HP-150
convert_pc_to_hp150() {
    echo ""
    echo -e "${CYAN}=== Conversión PC 720K → HP-150 ===${NC}"
    echo ""
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        return 1
    fi
    
    # Listar archivos PC disponibles
    echo "Archivos de disco disponibles:"
    echo ""
    ls -la *.img *.dsk *.ima 2>/dev/null | awk '{print "  " $9 "  (" $5 " bytes)"}' | grep -v "^  $"
    
    echo ""
    echo -n "Archivo PC 720K de entrada: "
    read -r input_file
    
    if [ -z "$input_file" ]; then
        echo -e "${RED}Error: Debe especificar un archivo${NC}"
        return 1
    fi
    
    if [ ! -f "$input_file" ]; then
        echo -e "${RED}Error: El archivo '$input_file' no existe${NC}"
        return 1
    fi
    
    echo -n "Archivo HP-150 de salida (.img): "
    read -r output_file
    
    if [ -z "$output_file" ]; then
        # Generar nombre automáticamente
        output_file=$(basename "$input_file" .img)_hp150.img
        output_file=$(basename "$output_file" .dsk)_hp150.img
        output_file=$(basename "$output_file" .ima)_hp150.img
        echo "Usando nombre automático: $output_file"
    fi
    
    # Agregar extensión .img si no la tiene
    if [[ ! "$output_file" =~ \.img$ ]]; then
        output_file="${output_file}.img"
    fi
    
    echo ""
    echo "Iniciando conversión..."
    
    # Activar entorno virtual y convertir
    source venv/bin/activate
    python3 src/converters/pc720_hp150_converter.py --pc-to-hp "$input_file" "$output_file"
}

# Función para convertir HP-150 a PC 720K
convert_hp150_to_pc() {
    echo ""
    echo -e "${CYAN}=== Conversión HP-150 → PC 720K ===${NC}"
    echo ""
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        return 1
    fi
    
    # Listar archivos HP-150 disponibles
    echo "Archivos HP-150 disponibles:"
    echo ""
    for img_file in *.img; do
        if [ -f "$img_file" ]; then
            size=$(stat -f%z "$img_file" 2>/dev/null || stat -c%s "$img_file" 2>/dev/null)
            if [ "$size" = "270336" ]; then
                echo "  $img_file  (HP-150 format)"
            else
                echo "  $img_file  ($size bytes - verificar formato)"
            fi
        fi
    done
    
    echo ""
    echo -n "Archivo HP-150 de entrada: "
    read -r input_file
    
    if [ -z "$input_file" ]; then
        echo -e "${RED}Error: Debe especificar un archivo${NC}"
        return 1
    fi
    
    if [ ! -f "$input_file" ]; then
        echo -e "${RED}Error: El archivo '$input_file' no existe${NC}"
        return 1
    fi
    
    echo -n "Archivo PC 720K de salida (.img): "
    read -r output_file
    
    if [ -z "$output_file" ]; then
        # Generar nombre automáticamente
        output_file=$(basename "$input_file" .img)_pc720.img
        echo "Usando nombre automático: $output_file"
    fi
    
    # Agregar extensión .img si no la tiene
    if [[ ! "$output_file" =~ \.img$ ]]; then
        output_file="${output_file}.img"
    fi
    
    echo ""
    echo "Iniciando conversión..."
    
    # Activar entorno virtual y convertir
    source venv/bin/activate
    python3 src/converters/pc720_hp150_converter.py --hp-to-pc "$input_file" "$output_file"
}

# Función para convertir HP-150 a TD0
hp150_to_td0_converter() {
    clear
    echo -e "${GREEN}=== CONVERSOR HP-150 IMG → TD0 ===${NC}"
    echo ""
    echo -e "${CYAN}Crea archivos TD0 compatibles con Teledisk/SAMdisk${NC}"
    echo ""
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        return 1
    fi
    
    # Listar archivos HP-150 disponibles
    echo "Archivos HP-150 disponibles:"
    echo ""
    for img_file in *.img; do
        if [ -f "$img_file" ]; then
            size=$(stat -f%z "$img_file" 2>/dev/null || stat -c%s "$img_file" 2>/dev/null)
            if [ "$size" = "270336" ]; then
                echo "  $img_file  (HP-150 format, $size bytes)"
            else
                echo "  $img_file  ($size bytes - verificar formato)"
            fi
        fi
    done
    
    echo ""
    echo -n "Archivo HP-150 de entrada: "
    read -r input_file
    
    if [ -z "$input_file" ]; then
        echo -e "${RED}Error: Debe especificar un archivo${NC}"
        return 1
    fi
    
    if [ ! -f "$input_file" ]; then
        echo -e "${RED}Error: El archivo '$input_file' no existe${NC}"
        return 1
    fi
    
    echo -n "Archivo TD0 de salida (.TD0): "
    read -r output_file
    
    if [ -z "$output_file" ]; then
        # Generar nombre automáticamente
        output_file=$(basename "$input_file" .img).TD0
        echo "Usando nombre automático: $output_file"
    fi
    
    # Agregar extensión .TD0 si no la tiene
    if [[ ! "$output_file" =~ \.(TD0|td0)$ ]]; then
        output_file="${output_file}.TD0"
    fi
    
    echo ""
    echo "Método de conversión:"
    echo "1) 🚀 Automático (detecta herramientas disponibles)"
    echo "2) 💻 SAMdisk (recomendado si está instalado)"
    echo "3) 🔧 GreaseWeazle (alternativo)"
    echo "4) ✋ Manual (básico, siempre funciona)"
    echo ""
    echo -n "Seleccione método [1-4]: "
    read -r method_choice
    
    case $method_choice in
        1) method="auto" ;;
        2) method="samdisk" ;;
        3) method="greaseweazle" ;;
        4) method="manual" ;;
        *) method="auto" ;;
    esac
    
    echo ""
    echo "Iniciando conversión..."
    
    # Activar entorno virtual y convertir
    source venv/bin/activate
    python3 src/converters/hp150_to_td0.py "$input_file" "$output_file" --method $method
    
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función para mostrar ayuda
show_help() {
    clear
    echo -e "${GREEN}=== AYUDA ===${NC}"
    echo ""
    echo -e "${CYAN}Formato HP-150:${NC}"
    echo "• 77 cilindros, 2 cabezas, 7 sectores por pista"
    echo "• 256 bytes por sector"
    echo "• Tamaño total: 270,336 bytes (1056 sectores)"
    echo ""
    echo -e "${CYAN}Archivos soportados:${NC}"
    echo "• .img - Imágenes de disco raw"
    echo "• .TD0 - Archivos Teledisk (convertibles)"
    echo ""
    echo -e "${CYAN}Hardware requerido:${NC}"
    echo "• GreaseWeazle (para leer/escribir floppies físicos)"
    echo "• Unidad de floppy de 3.5\" compatible"
    echo ""
    echo -e "${CYAN}Comandos directos:${NC}"
    echo "• scripts/read_hp150_floppy.sh archivo.img"
    echo "• scripts/write_hp150_floppy.sh archivo.img"
    echo "• python3 src/converters/smart_td0_converter.py archivo.TD0 salida.img"
    echo "• python3 run_gui.py --extended"
    echo ""
    echo -e "${GREEN}Presione Enter para continuar...${NC}"
    read -r
}

# Función principal
main() {
    # Verificar que estamos en el directorio correcto
    if [ ! -f "scripts/write_hp150_floppy.sh" ] || [ ! -f "scripts/read_hp150_floppy.sh" ]; then
        echo -e "${RED}Error: Execute este script desde el directorio hp150_toolkit${NC}"
        exit 1
    fi
    
    while true; do
        clear
        show_banner
        show_menu
        
        read -r choice
        
        case $choice in
            1)
                read_floppy
                ;;
            2)
                write_floppy
                ;;
            3)
                convert_disk_formats
                ;;
            4)
                open_gui extended
                ;;
            5)
                hardware_info
                ;;
            6)
                list_images
                ;;
            7)
                museum_download
                ;;
            8)
                advanced_tools
                ;;
            9)
                show_help
                ;;
            0)
                echo -e "${GREEN}¡Hasta luego!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opción inválida. Presione Enter para continuar...${NC}"
                read -r
                ;;
        esac
    done
}

# Ejecutar función principal
main "$@"
