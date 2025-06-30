# Sistema de Fallback Inteligente para Análisis de Discos

## 🎯 Concepto

El sistema de fallback inteligente permite analizar cualquier disco cuasi-IBM y, basándose en el análisis, crear automáticamente definiciones diskdef para GreaseWeazle.

## 🔍 Cómo Funciona

### 1. Intento de Parseo BPB Estándar
```python
def parse_boot_sector(self):
    """Parsea el sector de boot para determinar los parámetros del disco"""
    try:
        # Bytes por sector (puede ser 256 para HP-150 o 512 para PC estándar)
        self.bytes_per_sector = struct.unpack('<H', self.boot_sector[11:13])[0]
        if self.bytes_per_sector not in [256, 512]:
            raise ValueError(f"Bytes por sector no soportado: {self.bytes_per_sector}")

        self.sectors_per_cluster = self.boot_sector[13]
        self.reserved_sectors = struct.unpack('<H', self.boot_sector[14:16])[0]
        self.fat_copies = self.boot_sector[16]
        self.root_entries = struct.unpack('<H', self.boot_sector[17:19])[0]
        self.fat_sectors = struct.unpack('<H', self.boot_sector[22:24])[0]
        
        # Validación
        if self.sectors_per_cluster == 0:
            raise ValueError("Sectores por cluster no puede ser 0")
        if self.fat_copies == 0:
            raise ValueError("Número de FATs no puede ser 0")

    except Exception as e:
        # AQUÍ ENTRA EL FALLBACK INTELIGENTE
        print(f"[WARN] No se pudo parsear BPB, asumiendo formato HP-150: {e}")
        self.bytes_per_sector = 256
        self.sectors_per_cluster = 4
        self.reserved_sectors = 2
        self.fat_copies = 2
        self.fat_sectors = 3
        self.root_entries = 128
```

### 2. Cálculo Dinámico del Tamaño
```python
# Calcular sectores máximos basado en el tamaño del archivo
file_size = os.path.getsize(image_path)
self.max_sectors = file_size // self.bytes_per_sector
```

### 3. Detección Automática de Formato por Tamaño
```bash
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
            # Intentar calcular basándose en múltiplos de bytes_per_sector
            local sectors=$((size / 256))
            if [ $((size % 256)) -eq 0 ] && [ $sectors -gt 500 ] && [ $sectors -lt 2000 ]; then
                echo "custom:c=0-X:h=0-1:Formato estimado ($sectors sectores)"
            else
                echo "unknown:c=0-76:h=0-1:Formato desconocido"
            fi
            ;;
    esac
}
```

## 🛠️ Expansión para Análisis Universal

### Algoritmo Propuesto para Cualquier Disco

```python
def analyze_unknown_disk(image_path):
    """Analiza un disco desconocido y genera diskdef automáticamente"""
    
    file_size = os.path.getsize(image_path)
    
    # 1. Detectar bytes por sector más probable
    possible_bps = [128, 256, 512, 1024]  # Tamaños comunes
    
    for bps in possible_bps:
        total_sectors = file_size // bps
        if file_size % bps == 0 and 100 < total_sectors < 10000:
            # 2. Calcular geometrías posibles
            geometries = calculate_possible_geometries(total_sectors)
            
            # 3. Verificar si hay estructuras FAT válidas
            for geom in geometries:
                if validate_fat_structure(image_path, bps, geom):
                    return create_diskdef(geom, bps)
    
    return None

def calculate_possible_geometries(total_sectors):
    """Calcula geometrías posibles basándose en el total de sectores"""
    geometries = []
    
    # Probar diferentes combinaciones de cilindros/cabezas/sectores
    for heads in [1, 2]:  # 1 o 2 cabezas es lo más común
        for spt in range(7, 32):  # Sectores por pista entre 7 y 31
            cylinders = total_sectors // (heads * spt)
            if cylinders * heads * spt == total_sectors:
                if 35 <= cylinders <= 85:  # Rango típico de cilindros
                    geometries.append({
                        'cylinders': cylinders,
                        'heads': heads,
                        'sectors_per_track': spt
                    })
    
    return geometries

def validate_fat_structure(image_path, bps, geometry):
    """Valida si una geometría produce una estructura FAT válida"""
    try:
        # Intentar leer y parsear FAT con esta geometría
        with open(image_path, 'rb') as f:
            boot_sector = f.read(bps)
            
        # Buscar patrones FAT típicos
        # - Entradas de directorio válidas
        # - Estructura de FAT coherente
        # - Boot signature si existe
        
        return True  # Simplificado para el ejemplo
    except:
        return False

def create_diskdef(geometry, bps):
    """Genera un diskdef para GreaseWeazle"""
    
    diskdef = f"""
# Formato detectado automáticamente
disk custom
    cyls = {geometry['cylinders']}
    heads = {geometry['heads']}
    tracks * ibm.mfm
        secs = {geometry['sectors_per_track']}
        bps = {bps}
        gap3 = 22
        rate = 250
        iam = no
    end
end
"""
    
    return {
        'diskdef': diskdef,
        'tracks_spec': f"c=0-{geometry['cylinders']-1}:h=0-{geometry['heads']-1}",
        'total_size': geometry['cylinders'] * geometry['heads'] * geometry['sectors_per_track'] * bps
    }
```

## 🔧 Implementación Práctica

### Script de Análisis Automático
```bash
#!/bin/bash
# analyze_disk.sh - Analiza cualquier disco y genera diskdef

analyze_disk() {
    local image_file="$1"
    local file_size=$(stat -f%z "$image_file" 2>/dev/null || stat -c%s "$image_file")
    
    echo "Analizando: $image_file"
    echo "Tamaño: $file_size bytes"
    
    # Detectar bytes por sector
    for bps in 128 256 512 1024; do
        local sectors=$((file_size / bps))
        if [ $((file_size % bps)) -eq 0 ] && [ $sectors -gt 100 ] && [ $sectors -lt 10000 ]; then
            echo "Probando $bps bytes/sector → $sectors sectores totales"
            
            # Calcular geometrías posibles
            detect_geometry $sectors $bps
        fi
    done
}

detect_geometry() {
    local total_sectors=$1
    local bps=$2
    
    for heads in 1 2; do
        for spt in $(seq 7 31); do
            local cylinders=$((total_sectors / (heads * spt)))
            local remainder=$((total_sectors % (heads * spt)))
            
            if [ $remainder -eq 0 ] && [ $cylinders -ge 35 ] && [ $cylinders -le 85 ]; then
                echo "  ✅ Geometría válida: $cylinders cil × $heads cabezas × $spt sec/pista"
                generate_diskdef_template $cylinders $heads $spt $bps
            fi
        done
    done
}

generate_diskdef_template() {
    local cyls=$1
    local heads=$2
    local spt=$3
    local bps=$4
    
    echo "disk custom_${cyls}_${heads}_${spt}_${bps}"
    echo "    cyls = $cyls"
    echo "    heads = $heads"
    echo "    tracks * ibm.mfm"
    echo "        secs = $spt"
    echo "        bps = $bps"
    echo "        gap3 = 22"
    echo "        rate = 250"
    echo "        iam = no"
    echo "    end"
    echo "end"
    echo ""
}
```

## 🚀 Ventajas del Sistema

1. **Adaptabilidad**: Funciona con formatos conocidos y desconocidos
2. **Automático**: No requiere configuración manual
3. **Robusto**: Fallback graceful cuando falla el análisis estándar
4. **Extensible**: Fácil agregar nuevos formatos
5. **Genera diskdefs**: Crea automáticamente definiciones para GreaseWeazle

## 📋 Casos de Uso

- **HP-150**: Formato no estándar, detectado automáticamente
- **Discos CP/M**: Geometrías variables
- **Formatos propietarios**: Análisis por tamaño y estructura
- **Discos dañados**: Estimación basada en tamaño físico

## 🎯 Futuras Mejoras

1. **Base de datos de firmas**: Reconocimiento por patrones de boot
2. **Análisis de FAT**: Validación de estructura de sistema de archivos
3. **Heurísticas avanzadas**: Machine learning para detección de formatos
4. **Interfaz gráfica**: Visualización del análisis paso a paso

Este sistema convierte el HP-150 toolkit en una herramienta universal para analizar y escribir cualquier formato de disco vintage.
