#!/bin/bash
#
# Script para leer floppies HP-150 usando GreaseWeazle
# Formato específico del HP-150: 256 bytes/sector, 1056 sectores totales
#

# Verificar que se proporcione el nombre del archivo de salida
if [ $# -eq 0 ]; then
    echo "Uso: $0 <archivo_salida.img> [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --verify        Verificar la lectura releyendo y comparando"
    echo "  --retry=N       Número de reintentos por sector (default: 3)"
    echo "  --verbose       Mostrar información detallada"
    echo "  --info          Solo mostrar información del disco sin leer"
    echo "  --drive=N       Seleccionar drive (0 o 1, default: 0)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 disco_leido.img"
    echo "  $0 disco_hp150.img --verify --drive=1"
    echo "  $0 mi_backup.img --retry=5 --verbose --drive=0"
    echo "  $0 --info --drive=1          # Solo información del drive 1"
    exit 1
fi

ARCHIVO_SALIDA="$1"
shift  # Remover el primer argumento para procesar las opciones

# Variables por defecto
VERIFY=""
RETRY="3"
VERBOSE=""
INFO_ONLY=""
DRIVE="0"
OVERWRITE=""

# Procesar opciones adicionales
while [[ $# -gt 0 ]]; do
    case $1 in
        --verify)
            VERIFY="--verify"
            shift
            ;;
        --retry=*)
            RETRY="${1#*=}"
            shift
            ;;
        --overwrite)
            OVERWRITE="true"
            shift
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --info)
            INFO_ONLY="true"
            shift
            ;;
        --drive=*)
            DRIVE="${1#*=}"
            # Validar que sea 0 o 1
            if [[ ! "$DRIVE" =~ ^[01]$ ]]; then
                echo "Error: Drive debe ser 0 o 1, recibido: $DRIVE"
                exit 1
            fi
            shift
            ;;
        *)
            echo "Opción desconocida: $1"
            echo "Use '$0' sin argumentos para ver la ayuda"
            exit 1
            ;;
    esac
done

echo "=== Lectura de floppy HP-150 ==="
echo "Drive seleccionado: $DRIVE"
echo ""

# Solo mostrar información si se solicita
if [ "$INFO_ONLY" = "true" ]; then
    echo "Obteniendo información del disco en drive $DRIVE..."
    echo ""
    echo "Comando: gw info --drive=$DRIVE"
    gw info --drive=$DRIVE
    exit 0
fi

echo "Archivo de salida: $ARCHIVO_SALIDA"
echo "Formato: HP-150 (256 bytes/sector, 1056 sectores)"
echo "Reintentos por sector: $RETRY"
if [ -n "$VERIFY" ]; then
    echo "Verificación: ACTIVADA"
fi
if [ -n "$VERBOSE" ]; then
    echo "Modo verbose: ACTIVADO"
fi
echo ""

# Verificar si el archivo de salida ya existe
if [ -f "$ARCHIVO_SALIDA" ]; then
    echo "¡ADVERTENCIA! El archivo '$ARCHIVO_SALIDA' ya existe."
    
    if [ "$OVERWRITE" = "true" ]; then
        echo "Sobrescribiendo automáticamente (--overwrite especificado)..."
    else
        echo -n "¿Desea sobrescribirlo? (s/N): "
        read -r respuesta
        if [[ ! "$respuesta" =~ ^[sS]$ ]]; then
            echo "Operación cancelada."
            exit 1
        fi
    fi
    echo ""
fi

# Usar formato SCP nativo de GreaseWeazle primero
ARCHIVO_BASE="${ARCHIVO_SALIDA%.*}"
ARCHIVO_SCP="${ARCHIVO_BASE}.scp"

# Construir el comando GreaseWeazle para leer en formato SCP nativo
# Sintaxis correcta: gw read [opciones] archivo.scp
# Obtener directorio del script para encontrar el archivo diskdef
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" \u0026\u0026 pwd)"
DISKDEF_FILE="$SCRIPT_DIR/../hp150.diskdef"

# Verificar que existe el archivo de definición
if [ ! -f "$DISKDEF_FILE" ]; then
    echo "❌ Error: No se encuentra el archivo de definición HP-150: $DISKDEF_FILE"
    exit 1
fi

echo "📁 Usando definición de disco: $DISKDEF_FILE"
echo ""

CMD="gw read --drive=$DRIVE"

# Usar definición personalizada del HP-150
CMD="$CMD --diskdefs \"$DISKDEF_FILE\""
CMD="$CMD --format=hp150"
CMD="$CMD --tracks=c=0-76:h=0-1:step=1"

# Agregar opciones adicionales
if [ -n "$VERIFY" ]; then
    CMD="$CMD $VERIFY"
fi

if [ -n "$VERBOSE" ]; then
    CMD="$CMD $VERBOSE"
fi

CMD="$CMD --retries=$RETRY \"$ARCHIVO_SCP\""

# Mostrar el comando que se va a ejecutar
echo "Paso 1: Leyendo disco en formato SCP nativo..."
echo "$CMD"
echo ""

# Comandos alternativos comentados para referencia
echo "# Comando alternativo básico:"
echo "# gw read --drive=$DRIVE \"$ARCHIVO_SCP\""
echo ""
echo "# Con más revoluciones para discos dañados:"
echo "# gw read --drive=$DRIVE --tracks=c=0-76:h=0-1:step=1 --revs=5 --retries=10 \"$ARCHIVO_SCP\""
echo ""

# Ejecutar el comando real
echo "Iniciando lectura del floppy..."
echo "Esto puede tardar varios minutos dependiendo del estado del disco."
echo ""

# Usar eval para ejecutar el comando con las comillas correctas
eval $CMD

# Verificar el resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "=== Lectura en formato SCP completada ==="
    
    # Convertir de SCP a IMG usando GreaseWeazle con formato raw
    if [ -f "$ARCHIVO_SCP" ]; then
        echo ""
        echo "Paso 2: Convirtiendo SCP a formato HP-150..."
        
        # Obtener directorio del script
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" \u0026\u0026 pwd)"
        CONVERTER="$SCRIPT_DIR/../src/converters/scp_to_hp150.py"
        
        echo "Comando: python3 \"$CONVERTER\" \"$ARCHIVO_SCP\" \"$ARCHIVO_SALIDA\""
        echo ""
        
        # Usar el convertidor directo SCP a HP150 (sin ibm.scan)
        python3 "$CONVERTER" "$ARCHIVO_SCP" "$ARCHIVO_SALIDA"
        
        if [ $? -eq 0 ]; then
            echo "✅ Conversión HP-150 completada exitosamente"
        else
            echo "⚠️  Error en conversión HP-150, manteniendo archivo SCP..."
            echo "📁 Archivo SCP disponible: $ARCHIVO_SCP"
            # Copiar SCP para análisis posterior
            cp "$ARCHIVO_SCP" "${ARCHIVO_SALIDA}.scp"
            # Crear archivo IMG vacío como placeholder 
            touch "$ARCHIVO_SALIDA"
            echo "📁 Archivo SCP copiado como: ${ARCHIVO_SALIDA}.scp"
        fi
    fi
    
    # Mostrar información del archivo creado
    if [ -f "$ARCHIVO_SALIDA" ]; then
        TAMANO=$(ls -lh "$ARCHIVO_SALIDA" | awk '{print $5}')
        echo "Archivo creado: $ARCHIVO_SALIDA"
        echo "Tamaño: $TAMANO"
        
        # Verificar que el tamaño sea correcto (1056 sectores × 256 bytes = 270,336 bytes)
        TAMANO_BYTES=$(stat -f%z "$ARCHIVO_SALIDA" 2>/dev/null || stat -c%s "$ARCHIVO_SALIDA" 2>/dev/null)
        TAMANO_ESPERADO=270336
        
        if [ "$TAMANO_BYTES" -eq "$TAMANO_ESPERADO" ]; then
            echo "✅ Tamaño correcto: $TAMANO_BYTES bytes"
        else
            echo "⚠️  Tamaño inesperado: $TAMANO_BYTES bytes (esperado: $TAMANO_ESPERADO bytes)"
        fi
        
        echo ""
        echo "Para explorar el contenido, use:"
        echo "  python3 run_gui.py --extended"
        echo "  # Y luego abra el archivo: $ARCHIVO_SALIDA"
        echo ""
        echo "O use el manager interactivo:"
        echo "  ./hp150_manager.sh"
    fi
else
    echo ""
    echo "❌ Error durante la lectura del floppy"
    echo "Verifique:"
    echo "  - Que haya un disco insertado en la unidad"
    echo "  - Que el disco no esté dañado"
    echo "  - Que GreaseWeazle esté conectado correctamente"
    echo "  - Los permisos de escritura en el directorio actual"
    exit 1
fi
