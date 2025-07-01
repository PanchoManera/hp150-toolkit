#!/bin/bash
#
# Script para escribir imágenes HP-150 a floppy usando GreaseWeazle
# Formato específico del HP-150: 256 bytes/sector, 1056 sectores totales
#

# Verificar que se proporcione el archivo de imagen
if [ $# -eq 0 ]; then
    echo "Uso: $0 <archivo_imagen.img> [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --verify        Verificar la escritura releyendo y comparando"
    echo "  --verbose       Mostrar información detallada"
    echo "  --force         Forzar escritura sin confirmación"
    echo "  --drive=N       Seleccionar drive (0 o 1, default: 0)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 disco_hp150.img"
    echo "  $0 mi_backup.img --verify --drive=1"
    echo "  $0 software.img --force --verbose --drive=0"
    exit 1
fi

IMAGEN="$1"
shift  # Remover el primer argumento para procesar las opciones

# Variables por defecto
VERIFY=""
VERBOSE=""
FORCE=""
DRIVE="0"

# Procesar opciones adicionales
while [[ $# -gt 0 ]]; do
    case $1 in
        --verify)
            VERIFY="--verify"
            shift
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --force)
            FORCE="true"
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

# Verificar que el archivo existe
if [ ! -f "$IMAGEN" ]; then
    echo "Error: El archivo '$IMAGEN' no existe"
    exit 1
fi

echo "=== Escritura de imagen HP-150 a floppy ==="
echo "Drive seleccionado: $DRIVE"
echo "Archivo: $IMAGEN"
echo "Formato: HP-150 (256 bytes/sector, 1056 sectores)"
if [ -n "$VERIFY" ]; then
    echo "Verificación: ACTIVADA"
fi
if [ -n "$VERBOSE" ]; then
    echo "Modo verbose: ACTIVADO"
fi
echo ""

# Detectar formato HP-150 basado en el tamaño del archivo
TAMANO_BYTES=$(stat -f%z "$IMAGEN" 2>/dev/null || stat -c%s "$IMAGEN" 2>/dev/null)

# Detectar formato automáticamente
detect_hp150_format() {
    local size=$1
    case $size in
        270336)  # 77×2×7×256 = 1,056 sectores
            echo "hp150:c=0-76:h=0-1:Estándar (77 cil, 7 sec/pista)"
            ;;
        348160)  # 85×2×8×256 = 1,360 sectores  
            echo "hp150ext:c=0-84:h=0-1:Extendido (85 cil, 8 sec/pista)"
            ;;
        368640)  # 80×2×9×256 = 1,440 sectores
            echo "hp150hd:c=0-79:h=0-1:Alta densidad (80 cil, 9 sec/pista)"
            ;;
        394240)  # 77×2×10×256 = 1,540 sectores
            echo "hp150dd:c=0-76:h=0-1:Doble densidad (77 cil, 10 sec/pista)"
            ;;
        *)
            # Intentar calcular basándose en múltiplos de 256
            local sectors=$((size / 256))
            if [ $((size % 256)) -eq 0 ] && [ $sectors -gt 500 ] && [ $sectors -lt 2000 ]; then
                echo "hp150:c=0-76:h=0-1:Formato estimado ($sectors sectores)"
            else
                echo "unknown:c=0-76:h=0-1:Formato desconocido"
            fi
            ;;
    esac
}

FORMATO_INFO=$(detect_hp150_format $TAMANO_BYTES)
FORMATO_DISK=$(echo "$FORMATO_INFO" | cut -d: -f1)
TRACKS_SPEC=$(echo "$FORMATO_INFO" | cut -d: -f2)
DESCRIPCION=$(echo "$FORMATO_INFO" | cut -d: -f3-)

echo "📊 Detección automática de formato:"
echo "    Tamaño: $TAMANO_BYTES bytes"
echo "    Formato: $DESCRIPCION"
echo "    Diskdef: $FORMATO_DISK"
echo "    Pistas: $TRACKS_SPEC"
echo ""

if [ "$FORMATO_DISK" = "unknown" ]; then
    echo "⚠️  ADVERTENCIA: Formato no reconocido"
    echo "    Formatos soportados:"
    echo "    • 270,336 bytes - HP-150 Estándar (77×2×7×256)"
    echo "    • 348,160 bytes - HP-150 Extendido (85×2×8×256)"
    echo "    • 368,640 bytes - HP-150 Alta densidad (80×2×9×256)" 
    echo "    • 394,240 bytes - HP-150 Doble densidad (77×2×10×256)"
    echo ""
    if [ "$FORCE" != "true" ]; then
        echo -n "¿Continuar usando formato estándar? (s/N): "
        read -r respuesta
        if [[ ! "$respuesta" =~ ^[sS]$ ]]; then
            echo "Operación cancelada."
            exit 1
        fi
        FORMATO_DISK="hp150"
        TRACKS_SPEC="c=0-76:h=0-1"
    fi
fi

# Confirmación de escritura (a menos que se use --force)
if [ "$FORCE" != "true" ]; then
    echo "⚠️  ADVERTENCIA: Esta operación sobrescribirá el contenido del floppy en drive $DRIVE"
    echo -n "¿Está seguro de que desea continuar? (s/N): "
    read -r respuesta
    if [[ ! "$respuesta" =~ ^[sS]$ ]]; then
        echo "Operación cancelada."
        exit 1
    fi
    echo ""
fi

echo "Escribiendo imagen HP-150 directamente al floppy..."
echo ""

# Escribir usando definición personalizada HP-150
# HP-150: 77 cilindros (0-76), 2 cabezas (0-1), 7 sectores por pista (1-7), 256 bytes/sector

# Obtener archivo diskdef usando ruta relativa al script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISKDEF_FILE="$SCRIPT_DIR/../hp150.diskdef"

# Verificar que existe el archivo de definición
if [ ! -f "$DISKDEF_FILE" ]; then
    echo "❌ Error: No se encuentra el archivo de definición HP-150: $DISKDEF_FILE"
    exit 1
fi

echo "📁 Usando definición de disco: $DISKDEF_FILE"
echo ""

# Obtener la ruta configurada de GreaseWeazle
# Buscar el script de Python que puede leer la configuración  
GUI_DIR="$(dirname "$SCRIPT_DIR")/src/gui"

# Intentar obtener la ruta de GreaseWeazle desde la configuración
if [ -f "$GUI_DIR/config_manager.py" ]; then
    # Crear un script temporal para obtener la configuración
    GW_PATH=$(python3 -c "
import sys
sys.path.insert(0, '$GUI_DIR')
try:
    from config_manager import ConfigManager
    config = ConfigManager()
    print(config.get_greasewazle_path())
except:
    print('gw')
" 2>/dev/null)
    
    if [ -z "$GW_PATH" ] || [ "$GW_PATH" = "None" ]; then
        GW_PATH="gw"
    fi
else
    # Fallback: intentar encontrar gw en el PATH
    GW_PATH="gw"
fi

echo "🔧 Usando GreaseWeazle: $GW_PATH"
echo ""

CMD="\"$GW_PATH\" write --drive=$DRIVE"

# Usar definición personalizada del HP-150 detectada automáticamente
CMD="$CMD --diskdefs \"$DISKDEF_FILE\""
CMD="$CMD --format=$FORMATO_DISK"
CMD="$CMD --tracks=$TRACKS_SPEC:step=1"

# Agregar opciones básicas
# Nota: GreaseWeazle verifica por defecto, no necesitamos agregar --verify
# y no soporta --verbose, así que no agregamos nada para estas opciones

CMD="$CMD \"$IMAGEN\""

# Mostrar el comando que se va a ejecutar
echo "Comando de escritura: $CMD"
echo "Escribiendo '$IMAGEN' al drive $DRIVE..."
echo "Esto puede tardar varios minutos."
echo ""

# Ejecutar el comando real
eval $CMD

# Guardar el código de salida
WRITE_EXIT_CODE=$?

# Verificar el resultado
if [ $WRITE_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=== Escritura completada exitosamente ==="
    echo "✅ Imagen '$IMAGEN' escrita correctamente al drive $DRIVE"
    
    if [ -n "$VERIFY" ]; then
        echo "✅ Verificación completada"
    fi
    
    echo ""
    echo "El floppy está listo para usar en el HP-150."
else
    echo ""
    echo "❌ Error durante la escritura del floppy"
    echo "Verifique:"
    echo "  - Que haya un disco insertado en la unidad drive $DRIVE"
    echo "  - Que el disco no esté protegido contra escritura"
    echo "  - Que GreaseWeazle esté conectado correctamente"
    echo "  - Que el disco no esté dañado"
    exit 1
fi
