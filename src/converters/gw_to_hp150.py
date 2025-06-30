#!/usr/bin/env python3
"""
Conversor que usa GreaseWeazle directamente para extraer datos del HP-150
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def log(message):
    """Log mensaje a stdout"""
    print(message)
    sys.stdout.flush()

def convert_scp_to_hp150(scp_file, output_file):
    """Convertir SCP a HP-150 usando GreaseWeazle como herramienta de extracción"""
    
    log(f"🔄 Convirtiendo {scp_file} → {output_file}")
    log("📋 Usando GreaseWeazle para extraer datos...")
    
    # Crear archivo temporal para la conversión
    with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Intentar varios formatos para extraer los datos
        formats_to_try = [
            'ibm.360',
            'ibm.720', 
            'ibm.1440',
            'raw.250',
            'ibm.320'
        ]
        
        best_result = None
        best_sectors = 0
        
        for fmt in formats_to_try:
            log(f"⚙️ Probando formato: {fmt}")
            
            try:
                # Ejecutar conversión de GreaseWeazle
                result = subprocess.run([
                    'gw', 'convert', scp_file, tmp_path,
                    '--format', fmt
                ], capture_output=True, text=True)
                
                # Debug: mostrar output
                log(f"   🔍 Return code: {result.returncode}")
                if result.stdout:
                    log(f"   📝 STDOUT: {result.stdout[:200]}...")
                if result.stderr:
                    log(f"   ⚠️ STDERR: {result.stderr[:200]}...")
                    
                if result.returncode == 0:
                    # Contar sectores extraídos - GreaseWeazle pone info en stderr
                    sector_count = count_extracted_sectors(result.stderr)
                    file_size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
                    log(f"   ✅ {sector_count} sectores extraídos, archivo: {file_size} bytes")
                    
                    # Usar tamaño de archivo como métrica si no hay sectores contados
                    metric = sector_count if sector_count > 0 else file_size
                    
                    if metric > best_sectors:
                        best_sectors = sector_count
                        best_result = (fmt, tmp_path)
                        
                        # Hacer una copia del mejor resultado
                        with open(tmp_path, 'rb') as src:
                            with open(f"{tmp_path}.best", 'wb') as dst:
                                dst.write(src.read())
                else:
                    log(f"   ❌ Error con formato {fmt}")
                    
            except Exception as e:
                log(f"   ❌ Error: {e}")
        
        if best_result:
            fmt, tmp_path = best_result
            log(f"🎯 Mejor resultado: {fmt} con {best_sectors} sectores")
            
            # Leer el mejor resultado
            best_path = f"{tmp_path}.best"
            if os.path.exists(best_path):
                with open(best_path, 'rb') as src:
                    data = src.read()
                    
                # Procesar los datos para formato HP-150
                hp150_data = process_for_hp150(data, best_sectors)
                
                # Escribir archivo final
                with open(output_file, 'wb') as f:
                    f.write(hp150_data)
                    
                log(f"✅ Conversión completada: {output_file}")
                log(f"📏 Tamaño: {len(hp150_data):,} bytes")
                return True
        else:
            log("❌ No se pudo extraer datos con ningún formato")
            return False
            
    finally:
        # Limpiar archivos temporales
        for temp_file in [tmp_path, f"{tmp_path}.best"]:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

def count_extracted_sectors(gw_output):
    """Contar sectores extraídos del output de GreaseWeazle"""
    import re
    sectors = 0
    
    # Buscar varios patrones de sectores
    patterns = [
        r'\((\d+)/\d+ sectors\)',  # (9/9 sectors)
        r'IBM MFM \((\d+)/\d+ sectors\)',  # IBM MFM (9/9 sectors)
        r'Found (\d+) sectors',  # Found 360 sectors
    ]
    
    for line in gw_output.split('\n'):
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                sectors += int(match.group(1))
                break
    
    # Si no encontramos sectores, asumir que el archivo existe si no hubo error
    if sectors == 0 and 'Format' in gw_output and 'Converting' in gw_output:
        # Al menos se ejecutó la conversión
        sectors = 1  # Indicar que se intentó una conversión
    
    return sectors

def process_for_hp150(data, sector_count):
    """Procesar datos extraídos para formato HP-150"""
    
    # Especificaciones HP-150
    HP150_TOTAL_SIZE = 270336  # 77 * 2 * 7 * 256
    
    if len(data) == 0:
        log("⚠️ No hay datos para procesar, creando imagen vacía")
        return b'\x00' * HP150_TOTAL_SIZE
    
    if len(data) >= HP150_TOTAL_SIZE:
        log("✂️ Truncando datos al tamaño HP-150")
        return data[:HP150_TOTAL_SIZE]
    
    if len(data) < HP150_TOTAL_SIZE:
        log(f"📏 Expandiendo datos de {len(data)} a {HP150_TOTAL_SIZE} bytes")
        # Rellenar con ceros
        result = bytearray(data)
        result.extend(b'\x00' * (HP150_TOTAL_SIZE - len(data)))
        return bytes(result)
    
    return data

def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("Uso: python3 gw_to_hp150.py <archivo.scp> <salida.img>")
        print("")
        print("Convierte archivos SCP a formato HP-150 usando GreaseWeazle")
        sys.exit(1)
    
    scp_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(scp_file):
        print(f"❌ Archivo no encontrado: {scp_file}")
        sys.exit(1)
    
    success = convert_scp_to_hp150(scp_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
