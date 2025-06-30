#!/bin/bash
#
# Script para escribir imagen FAT estándar (512 bytes/sector) a floppy usando GreaseWeazle
# Uso: write_standard_floppy.sh <imagen.img> [--drive=N] [--force] [--verify]
#

# Configuración de colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes con colores
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Verificar argumentos
if [ $# -lt 1 ]; then
    log_error "Uso: $0 <imagen.img> [--drive=N] [--force] [--verify]"
    exit 1
fi

IMG_FILE="$1"
DRIVE=0
FORCE=false
VERIFY=false

# Procesar argumentos opcionales
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --drive=*)
            DRIVE="${1#*=}"
            ;;
        --force)
            FORCE=true
            ;;
        --verify)
            VERIFY=true
            ;;
        *)
            log_warning "Argumento desconocido: $1"
            ;;
    esac
    shift
done

# Verificar si el archivo de imagen existe
if [ ! -f "$IMG_FILE" ]; then
    log_error "El archivo de imagen no existe: $IMG_FILE"
    exit 1
fi

# Obtener información del archivo
IMG_SIZE=$(stat -f%z "$IMG_FILE" 2>/dev/null || stat -c%s "$IMG_FILE" 2>/dev/null)
log_info "Archivo de imagen: $IMG_FILE"
log_info "Tamaño: $IMG_SIZE bytes"

# Verificar que el tamaño sea apropiado para un floppy estándar
if [ "$IMG_SIZE" -gt 1474560 ]; then  # 1.44MB estándar
    log_warning "Imagen grande ($IMG_SIZE bytes) - podría no caber en floppy estándar"
fi

# Verificar que GreaseWeazle esté disponible
if ! command -v gw &> /dev/null; then
    log_error "GreaseWeazle (gw) no está disponible. Instalar desde: https://github.com/keirf/greaseweazle"
    exit 1
fi

# Verificar formato de la imagen (debe ser FAT estándar)
log_info "Verificando formato de imagen..."

# Leer sector de boot y verificar BPB
BPS=$(xxd -l 2 -s 11 -p "$IMG_FILE" | xxd -r -p | od -t u2 -N 2 --endian=little | awk 'NR==1 {print $2}')
SPC=$(xxd -l 1 -s 13 -p "$IMG_FILE" | xxd -r -p | od -t u1 -N 1 | awk 'NR==1 {print $2}')

if [ "$BPS" != "512" ]; then
    log_error "Esta imagen no es FAT estándar (bytes por sector: $BPS, esperado: 512)"
    log_error "Use write_hp150_floppy.sh para imágenes HP-150 (256 bytes/sector)"
    exit 1
fi

log_success "Formato verificado: FAT estándar (512 bytes/sector, $SPC sectores/cluster)"

# Mostrar información del proceso
log_info "=== ESCRITURA FAT ESTÁNDAR ==="
log_info "Drive destino: $DRIVE"
log_info "Forzar: $FORCE"
log_info "Verificar: $VERIFY"

# Advertencia de seguridad
if [ "$FORCE" != "true" ]; then
    log_warning "ADVERTENCIA: Esta operación sobrescribirá completamente el floppy"
    log_warning "Use --force para omitir esta confirmación"
    read -p "¿Continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operación cancelada"
        exit 0
    fi
fi

# Crear directorio temporal
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

SCP_FILE="$TEMP_DIR/temp_standard.scp"

log_info "Archivos temporales en: $TEMP_DIR"

# Paso 1: Convertir IMG a formato SCP compatible
log_info "Paso 1: Convirtiendo IMG a formato SCP compatible"
echo "Paso 1: Convirtiendo IMG a formato SCP compatible"

# Para FAT estándar, podemos usar GreaseWeazle directamente para escribir
# ya que maneja el formato de 512 bytes/sector nativamente
log_info "IMG FAT estándar puede escribirse directamente"

# Paso 2: Escribir al floppy
log_info "Paso 2: Escribiendo imagen FAT al disco"
echo "Paso 2: Escribiendo imagen FAT al disco"

log_info "Iniciando escritura del floppy en drive $DRIVE"
echo "Iniciando escritura del floppy"

# Usar GreaseWeazle para escribir directamente desde IMG
# Para formato estándar de 1.44MB floppy
gw_cmd="gw write --drive=$DRIVE --format=ibm.1440 \"$IMG_FILE\""

if [ "$VERIFY" == "true" ]; then
    gw_cmd="$gw_cmd --verify"
fi

log_info "Ejecutando: $gw_cmd"

# Ejecutar comando
if eval $gw_cmd; then
    log_success "Escritura completada exitosamente"
    echo "Escritura completada exitosamente"
    
    if [ "$VERIFY" == "true" ]; then
        log_success "Verificación exitosa"
        echo "Verificación exitosa"
    fi
    
    log_success "Floppy FAT estándar listo para usar"
    exit 0
else
    log_error "Error durante la escritura"
    echo "Error durante la escritura"
    exit 1
fi
