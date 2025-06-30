#!/bin/bash
#
# Script para descargar automaticamente todas las imagenes HP-150 del museo HP
# URL base: https://hpmuseum.net/exhibit.php?swc=5
#

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorios de trabajo
ORIGINAL_DIR="HP150_ALL_ORIGINAL"
CONVERTED_DIR="HP150_CONVERTED"

# Array con todos los IDs de software y sus nombres
declare -a SOFTWARE_IDS=(
    "68:System_Demo_Disc_for_150_1983"
    "85:DSN_Link_for_150_1983"
    "162:Lotus_1-2-3_v_1A_1983"
    "87:Series_100_Graphics_for_150_1983"
    "90:Context_MBA_for_150_1983"
    "155:Reflection_Ver_1.3_1983"
    "94:MailMerge_1983"
    "95:9125_Disc_Drive_Utilities_for_150_1983"
    "104:Condor_20-3_for_150_1983"
    "99:Wordstar_for_150_1983"
    "100:Multiplan_Demo_for_150_1983"
    "160:NWA_StatPak_v_3.11_1983"
    "84:Personal_Card_File_for_150_1983"
    "83:Financial_Calculator_for_150_1983"
    "149:150_Programmers_Tools_1983"
    "75:Systems_Discs_for_150_version_A_1983"
    "76:Diagraph_and_Picture_Perfect_for_150_1983"
    "77:HP_BASIC_for_150_1983"
    "78:MemoMaker_for_150_1983"
    "79:Type_Attack_for_150_1983"
    "158:Microsoft_Compiled_BASIC_1983"
    "493:150_Firmware_1983"
    "81:Visicalc_for_150_1983"
    "89:Various_Games_for_150_1983"
    "156:AdvanceWrite_Plus_1984"
    "152:Zork_I_and_III_1984"
    "157:BASIC_Programmers_Library_1984"
    "150:Cross_Reference_Utility_1984"
    "153:WITNESS_1984"
    "147:Lattice_C_Compiler_1984"
    "154:Knowledge_Manager_1984"
    "161:Kermit_for_150-110_1984"
    "595:LaserJet_Demo_on_the_HP-150_1984"
    "572:Etherlink-150_Software_1984"
    "374:Macro_Assembler_1984"
    "373:VT100_Emulation_1984"
    "319:Extended_IO_Application_Software_1984"
    "312:Touch_Games_I_1984"
    "251:Microsoft_Word_1984"
    "621:MS-DOS_for_the_Series_100_1984"
    "596:ThinkJet_Demo_on_the_HP-150_1984"
    "146:PFS_Write_1984"
    "145:PFS_Graph_1984"
    "86:DBaseII_for_150_1984"
    "80:Winning_Deal_for_150_1984"
    "159:Microsoft_PASCAL_for_150_1984"
    "148:Microsoft_COBOL_for_150_1984"
    "144:PFS_File_And_Report_1984"
    "253:Drawing_Gallery_for_150_1985"
    "254:Executive_Card_Manager_Templates_1985"
    "255:Charting_Gallery_for_150_1985"
    "372:8087_Coprocessor_Utilities_1985"
    "310:HP_Message_for_150_1985"
    "311:Systems_Work_Disc_for_150II_1985"
    "309:AutoCAD_for_150_1985"
    "575:150_Loaded_Hard_Disc_Image_1985"
    "594:Protocol_Analyzer_Control_Demo_1985"
    "316:System_Demo_Disc_for_150II_1985"
    "320:PC_Instruments_150_1985"
    "317:HP-HIL_Development_Tools_1985"
    "318:HP_PCLPak_1985"
    "308:Open_Access_for_150_1985"
    "256:HPWORD-150_1985"
    "314:RBASE_5000_for_150_1985"
    "151:Microsoft_FORTRAN_for_150_1985"
    "252:AdvanceLink_for_150_1985"
    "313:Executive_Card_Manager_for_150_1985"
    "315:Microsoft_Spell_for_150_1985"
    "371:Systems_Discs_for_150_version_E_1986"
    "370:Wordcraft_for_150_1986"
    "622:GW_BASIC_for_100_Series_1986"
    "257:Microsoft_Windows_For_150_1986"
    "249:3000-70_Console_Emulator_1986"
    "250:Execudesk_for_150_1986"
    "258:Graphics_Gallery_for_150_1987"
)

# Función para mostrar banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                HP-150 MUSEUM DOWNLOADER                         ║"
    echo "║              Descarga automática de software                    ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para crear directorios
setup_directories() {
    echo -e "${CYAN}=== Configurando directorios ===${NC}"
    
    if [ -d "$ORIGINAL_DIR" ]; then
        echo -e "${YELLOW}El directorio $ORIGINAL_DIR ya existe${NC}"
        echo -n "¿Desea continuar? (s/N): "
        read -r response
        if [[ ! "$response" =~ ^[sS]$ ]]; then
            echo "Operación cancelada."
            exit 1
        fi
    fi
    
    mkdir -p "$ORIGINAL_DIR"
    mkdir -p "$CONVERTED_DIR"
    
    echo -e "${GREEN}✅ Directorios creados:${NC}"
    echo "  📁 $ORIGINAL_DIR - Archivos originales (ZIP/TD0)"
    echo "  📁 $CONVERTED_DIR - Imágenes convertidas (.img)"
    echo ""
}

# Función para obtener el enlace de descarga real de una página de software
get_download_link() {
    local sw_id="$1"
    local url="https://hpmuseum.net/display_item.php?sw=$sw_id"
    
    # Descargar la página completa (sin mostrar progreso)
    local page_content=$(curl -s "$url")
    
    # Buscar el patrón específico: "Download software" con enlace
    local download_link=$(echo "$page_content" | grep -i "Download software" | sed -n 's/.*href="\([^"]*\)".*/\1/p')
    
    # Si no se encuentra, buscar enlaces ZIP o TD0 directos
    if [ -z "$download_link" ]; then
        download_link=$(echo "$page_content" | grep -i "href.*\.zip" | head -1 | sed -n 's/.*href="\([^"]*\)".*/\1/p')
    fi
    
    if [ -z "$download_link" ]; then
        download_link=$(echo "$page_content" | grep -i "href.*\.\(td0\|img\|bin\)" | head -1 | sed -n 's/.*href="\([^"]*\)".*/\1/p')
    fi
    
    # Si el enlace es relativo, convertirlo a absoluto
    if [[ "$download_link" == software/* ]] || [[ "$download_link" == /* ]]; then
        download_link="https://hpmuseum.net/$download_link"
    elif [[ "$download_link" == ../* ]]; then
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

# Función para convertir archivos TD0 a IMG
convert_files() {
    echo -e "${CYAN}=== Iniciando conversión de archivos ===${NC}"
    
    # Verificar entorno virtual
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: No se encontró el entorno virtual${NC}"
        echo "Ejecute primero: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    
    source venv/bin/activate
    
    # Procesar cada archivo descargado
    for file in "$ORIGINAL_DIR"/*; do
        if [ -f "$file" ]; then
            local basename_file=$(basename "$file")
            local software_name="${basename_file%_*}"
            
            echo -e "${GREEN}=== Procesando: $basename_file ===${NC}"
            
            # Crear directorio para este software en CONVERTED
            local convert_dir="$CONVERTED_DIR/$software_name"
            mkdir -p "$convert_dir"
            
            # Si es un ZIP, extraerlo primero
            if [[ "$file" == *.zip ]]; then
                echo -e "${CYAN}Extrayendo ZIP: $basename_file${NC}"
                
                # Crear directorio temporal
                local temp_dir=$(mktemp -d)
                
                if unzip -q "$file" -d "$temp_dir"; then
                    echo -e "${GREEN}✅ ZIP extraído exitosamente${NC}"
                    
                    # Buscar archivos TD0 en el contenido extraído
                    find "$temp_dir" -name "*.TD0" -o -name "*.td0" | while read -r td0_file; do
                        local td0_basename=$(basename "$td0_file" .TD0)
                        td0_basename=$(basename "$td0_basename" .td0)
                        local output_img="$convert_dir/${td0_basename}.img"
                        
                        echo -e "${CYAN}Convirtiendo: $(basename "$td0_file") -> $(basename "$output_img")${NC}"
                        
                        if python3 smart_td0_converter.py "$td0_file" "$output_img"; then
                            echo -e "${GREEN}✅ Conversión exitosa: $output_img${NC}"
                        else
                            echo -e "${RED}❌ Error en conversión: $td0_file${NC}"
                        fi
                    done
                    
                    # Limpiar directorio temporal
                    rm -rf "$temp_dir"
                else
                    echo -e "${RED}❌ Error al extraer ZIP: $basename_file${NC}"
                fi
                
            # Si es directamente un TD0
            elif [[ "$file" == *.TD0 ]] || [[ "$file" == *.td0 ]]; then
                local td0_basename=$(basename "$file" .TD0)
                td0_basename=$(basename "$td0_basename" .td0)
                local output_img="$convert_dir/${td0_basename}.img"
                
                echo -e "${CYAN}Convirtiendo TD0 directo: $(basename "$file") -> $(basename "$output_img")${NC}"
                
                if python3 smart_td0_converter.py "$file" "$output_img"; then
                    echo -e "${GREEN}✅ Conversión exitosa: $output_img${NC}"
                else
                    echo -e "${RED}❌ Error en conversión: $file${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️ Archivo no procesable: $basename_file${NC}"
            fi
            
            echo ""
        fi
    done
}

# Función para mostrar resumen
show_summary() {
    echo -e "${CYAN}=== RESUMEN FINAL ===${NC}"
    echo ""
    
    echo -e "${GREEN}Archivos originales descargados:${NC}"
    ls -la "$ORIGINAL_DIR"/ | grep -v "^total" | wc -l | xargs echo "  📁 Total:"
    
    echo ""
    echo -e "${GREEN}Directorios de software convertidos:${NC}"
    ls -d "$CONVERTED_DIR"/*/ 2>/dev/null | wc -l | xargs echo "  📂 Total:"
    
    echo ""
    echo -e "${GREEN}Imágenes .img generadas:${NC}"
    find "$CONVERTED_DIR" -name "*.img" | wc -l | xargs echo "  💾 Total:"
    
    echo ""
    echo -e "${CYAN}Para explorar las imágenes convertidas:${NC}"
    echo "  ./hp150_manager.sh"
    echo "  # O directamente:"
    echo "  python3 run_gui.py --extended"
}

# Función principal
main() {
    show_banner
    
    echo -e "${YELLOW}Esta operación descargará automáticamente todo el software HP-150${NC}"
    echo -e "${YELLOW}del museo HP. Esto puede tardar mucho tiempo y usar mucho ancho de banda.${NC}"
    echo ""
    echo -n "¿Desea continuar? (s/N): "
    read -r response
    
    if [[ ! "$response" =~ ^[sS]$ ]]; then
        echo "Operación cancelada."
        exit 0
    fi
    
    setup_directories
    
    echo -e "${CYAN}=== Iniciando descarga de ${#SOFTWARE_IDS[@]} elementos de software ===${NC}"
    echo ""
    
    local successful_downloads=0
    local failed_downloads=0
    
    # Descargar cada software
    for sw_entry in "${SOFTWARE_IDS[@]}"; do
        if download_software "$sw_entry"; then
            ((successful_downloads++))
        else
            ((failed_downloads++))
        fi
        echo ""
        sleep 2  # Pausa para no sobrecargar el servidor
    done
    
    echo -e "${CYAN}=== Descarga completada ===${NC}"
    echo -e "${GREEN}✅ Exitosas: $successful_downloads${NC}"
    echo -e "${RED}❌ Fallidas: $failed_downloads${NC}"
    echo ""
    
    if [ $successful_downloads -gt 0 ]; then
        echo -e "${CYAN}¿Desea convertir los archivos TD0 a imágenes HP-150? (s/N): ${NC}"
        read -r convert_response
        
        if [[ "$convert_response" =~ ^[sS]$ ]]; then
            convert_files
        fi
    fi
    
    show_summary
}

# Ejecutar función principal
main "$@"
