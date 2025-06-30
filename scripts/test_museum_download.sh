#!/bin/bash
#
# Script de prueba para descargar solo los primeros 3 elementos del museo HP-150
#

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorios de trabajo
ORIGINAL_DIR="HP150_TEST_ORIGINAL"
CONVERTED_DIR="HP150_TEST_CONVERTED"

# Solo los primeros 3 elementos para prueba
declare -a SOFTWARE_IDS=(
    "68:System_Demo_Disc_for_150_1983"
    "85:DSN_Link_for_150_1983"
    "162:Lotus_1-2-3_v_1A_1983"
)

# Función para obtener el enlace de descarga real de una página de software
get_download_link() {
    local sw_id="$1"
    local url="https://hpmuseum.net/display_item.php?sw=$sw_id"
    
    echo -e "${CYAN}Obteniendo enlace de descarga para sw=$sw_id...${NC}"
    
    # Descargar la página completa
    local page_content=$(curl -s "$url")
    
    # Buscar el patrón específico: "Download software" con enlace
    local download_link=$(echo "$page_content" | grep -i "Download software" | sed -n 's/.*href="\([^"]*\)".*/\1/p')
    
    # Si el enlace es relativo, convertirlo a absoluto
    if [[ "$download_link" == software/* ]]; then
        download_link="https://hpmuseum.net/$download_link"
    fi
    
    echo "$download_link"
}

# Función para descargar un archivo individual
download_software() {
    local sw_entry="$1"
    local sw_id="${sw_entry%%:*}"
    local sw_name="${sw_entry##*:}"
    
    echo -e "${GREEN}=== Descargando: $sw_name (ID: $sw_id) ===${NC}"
    
    # Obtener el enlace de descarga
    local download_url=$(get_download_link "$sw_id")
    
    if [ -z "$download_url" ]; then
        echo -e "${RED}❌ No se pudo encontrar enlace de descarga para $sw_name${NC}"
        return 1
    fi
    
    echo -e "${CYAN}URL encontrada: $download_url${NC}"
    
    # Obtener el nombre del archivo
    local filename=$(basename "$download_url")
    local output_path="$ORIGINAL_DIR/${sw_name}_${filename}"
    
    # Descargar el archivo
    echo -e "${CYAN}Descargando a: $output_path${NC}"
    if curl -L -o "$output_path" "$download_url"; then
        echo -e "${GREEN}✅ Descarga exitosa: $output_path${NC}"
        
        # Verificar el tamaño del archivo
        local file_size=$(ls -lh "$output_path" | awk '{print $5}')
        echo -e "${CYAN}Tamaño: $file_size${NC}"
        
        return 0
    else
        echo -e "${RED}❌ Error al descargar $sw_name${NC}"
        return 1
    fi
}

# Función principal
main() {
    echo -e "${BLUE}=== PRUEBA DE DESCARGA HP-150 MUSEUM ===${NC}"
    echo ""
    
    # Crear directorios
    mkdir -p "$ORIGINAL_DIR"
    mkdir -p "$CONVERTED_DIR"
    
    echo -e "${GREEN}✅ Directorios de prueba creados:${NC}"
    echo "  📁 $ORIGINAL_DIR"
    echo "  📁 $CONVERTED_DIR"
    echo ""
    
    local successful_downloads=0
    local failed_downloads=0
    
    # Descargar cada software de prueba
    for sw_entry in "${SOFTWARE_IDS[@]}"; do
        if download_software "$sw_entry"; then
            ((successful_downloads++))
        else
            ((failed_downloads++))
        fi
        echo ""
        sleep 1  # Pausa breve
    done
    
    echo -e "${CYAN}=== RESULTADO DE LA PRUEBA ===${NC}"
    echo -e "${GREEN}✅ Exitosas: $successful_downloads${NC}"
    echo -e "${RED}❌ Fallidas: $failed_downloads${NC}"
    echo ""
    
    if [ $successful_downloads -gt 0 ]; then
        echo -e "${GREEN}Archivos descargados:${NC}"
        ls -la "$ORIGINAL_DIR"/
        echo ""
        
        echo -e "${CYAN}¿Desea convertir los archivos TD0 a imágenes HP-150? (s/N): ${NC}"
        read -r convert_response
        
        if [[ "$convert_response" =~ ^[sS]$ ]]; then
            if [ ! -d "venv" ]; then
                echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
                echo "Ejecute primero: python3 -m venv venv && source venv/bin/activate"
                return 1
            fi
            
            source venv/bin/activate
            
            for file in "$ORIGINAL_DIR"/*.TD0; do
                if [ -f "$file" ]; then
                    local basename_file=$(basename "$file")
                    local software_name="${basename_file%_*}"
                    local convert_dir="$CONVERTED_DIR/$software_name"
                    mkdir -p "$convert_dir"
                    
                    local td0_basename=$(basename "$file" .TD0)
                    local output_img="$convert_dir/${td0_basename}.img"
                    
                    echo -e "${CYAN}Convirtiendo: $basename_file -> $(basename "$output_img")${NC}"
                    
                    if python3 smart_td0_converter.py "$file" "$output_img"; then
                        echo -e "${GREEN}✅ Conversión exitosa: $output_img${NC}"
                    else
                        echo -e "${RED}❌ Error en conversión: $file${NC}"
                    fi
                fi
            done
        fi
    fi
    
    echo ""
    echo -e "${CYAN}Si la prueba fue exitosa, ejecute el script completo:${NC}"
    echo "  ./download_hp150_museum.sh"
}

# Ejecutar función principal
main "$@"
