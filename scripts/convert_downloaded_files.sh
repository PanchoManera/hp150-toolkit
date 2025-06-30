#!/bin/bash
#
# Script para convertir archivos ya descargados del museo HP-150
#

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Directorios
ORIGINAL_DIR="HP150_ALL_ORIGINAL"
CONVERTED_DIR="HP150_CONVERTED"

echo "=== CONVERSOR DE ARCHIVOS DESCARGADOS ==="
echo ""

# Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: No se encontro el entorno virtual${NC}"
    echo "Ejecute primero: python3 -m venv venv && source venv/bin/activate"
    exit 1
fi

source venv/bin/activate

# Verificar directorio original
if [ ! -d "$ORIGINAL_DIR" ]; then
    echo -e "${RED}Error: No se encontro el directorio $ORIGINAL_DIR${NC}"
    echo "Ejecute primero el descargador del museo"
    exit 1
fi

# Crear directorio convertido
mkdir -p "$CONVERTED_DIR"

echo "Procesando archivos en $ORIGINAL_DIR..."
echo ""

# Procesar cada archivo
for file in "$ORIGINAL_DIR"/*; do
    if [ -f "$file" ]; then
        basename_file=$(basename "$file")
        software_name="${basename_file%_*}"
        
        echo -e "${GREEN}=== Procesando: $basename_file ===${NC}"
        
        # Crear directorio para este software
        convert_dir="$CONVERTED_DIR/$software_name"
        mkdir -p "$convert_dir"
        
        # Si es un ZIP, extraerlo primero
        if [[ "$file" == *.zip ]]; then
            echo -e "${CYAN}Extrayendo ZIP: $basename_file${NC}"
            
            # Crear directorio temporal
            temp_dir=$(mktemp -d)
            
            if unzip -q "$file" -d "$temp_dir"; then
                echo -e "${GREEN}ZIP extraido exitosamente${NC}"
                
                # Buscar archivos TD0
                find "$temp_dir" -name "*.TD0" -o -name "*.td0" | while read -r td0_file; do
                    td0_basename=$(basename "$td0_file" .TD0)
                    td0_basename=$(basename "$td0_basename" .td0)
                    output_img="$convert_dir/${td0_basename}.img"
                    
                    echo -e "${CYAN}Convirtiendo: $(basename "$td0_file") -> $(basename "$output_img")${NC}"
                    
                    if python3 src/converters/smart_td0_converter.py "$td0_file" "$output_img"; then
                        echo -e "${GREEN}Conversion exitosa: $output_img${NC}"
                    else
                        echo -e "${RED}Error en conversion: $td0_file${NC}"
                    fi
                done
                
                # Limpiar directorio temporal
                rm -rf "$temp_dir"
            else
                echo -e "${RED}Error al extraer ZIP: $basename_file${NC}"
            fi
            
        # Si es directamente un TD0
        elif [[ "$file" == *.TD0 ]] || [[ "$file" == *.td0 ]]; then
            td0_basename=$(basename "$file" .TD0)
            td0_basename=$(basename "$td0_basename" .td0)
            output_img="$convert_dir/${td0_basename}.img"
            
            echo -e "${CYAN}Convirtiendo TD0: $(basename "$file") -> $(basename "$output_img")${NC}"
            
            if python3 src/converters/smart_td0_converter.py "$file" "$output_img"; then
                echo -e "${GREEN}Conversion exitosa: $output_img${NC}"
            else
                echo -e "${RED}Error en conversion: $file${NC}"
            fi
        else
            echo -e "${YELLOW}Archivo no procesable: $basename_file${NC}"
        fi
        
        echo ""
    fi
done

echo "=== RESUMEN ==="
echo ""
echo "Directorios de software convertidos:"
ls -d "$CONVERTED_DIR"/*/ 2>/dev/null | wc -l | xargs echo "Total:"

echo ""
echo "Imagenes .img generadas:"
find "$CONVERTED_DIR" -name "*.img" | wc -l | xargs echo "Total:"

echo ""
echo "Para explorar las imagenes convertidas:"
echo "  ./hp150_manager.sh"
echo "  # O directamente:"
echo "  python3 run_gui.py --extended"
