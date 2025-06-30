#!/usr/bin/env python3
"""
Conversor SCP a HP-150 usando formato ibm.scan de GreaseWeazle
"""

import sys
import os
import subprocess
import tempfile

def log(message):
    """Log mensaje a stdout"""
    print(message)
    sys.stdout.flush()

def convert_scp_to_hp150_scan(scp_file, output_file):
    """Convertir SCP a HP-150 usando ibm.scan"""
    
    log(f"🔄 Convirtiendo {scp_file} → {output_file}")
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Usar ibm.scan para extraer todos los sectores
        log("🔍 Ejecutando GreaseWeazle con formato ibm.scan...")
        
        result = subprocess.run([
            'gw', 'convert', scp_file, tmp_path,
            '--format=ibm.scan'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            log(f"❌ Error en GreaseWeazle: {result.stderr}")
            return False
            
        # Verificar que se generó el archivo
        if not os.path.exists(tmp_path):
            log("❌ No se generó archivo temporal")
            return False
            
        file_size = os.path.getsize(tmp_path)
        log(f"✅ GreaseWeazle extrajo {file_size:,} bytes")
        
        # Leer los datos extraídos
        with open(tmp_path, 'rb') as f:
            scan_data = f.read()
            
        # Procesar para formato HP-150
        hp150_data = process_scan_to_hp150(scan_data)
        
        # Escribir archivo final
        with open(output_file, 'wb') as f:
            f.write(hp150_data)
            
        log(f"✅ Conversión completada: {output_file}")
        log(f"📏 Tamaño final: {len(hp150_data):,} bytes")
        return True
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def process_scan_to_hp150(scan_data):
    """Procesar datos de ibm.scan para formato HP-150"""
    
    # Especificaciones HP-150
    HP150_TOTAL_SIZE = 270336  # 77 * 2 * 7 * 256 = 270,336 bytes
    
    if len(scan_data) == 0:
        log("⚠️ Datos vacíos, creando imagen vacía")
        return b'\x00' * HP150_TOTAL_SIZE
    
    # Si los datos son exactamente del tamaño correcto, usar tal como están
    if len(scan_data) == HP150_TOTAL_SIZE:
        log("✅ Tamaño perfecto, usando datos tal como están")
        return scan_data
    
    # Si tenemos más datos, truncar al tamaño correcto
    if len(scan_data) > HP150_TOTAL_SIZE:
        log(f"✂️ Truncando de {len(scan_data):,} a {HP150_TOTAL_SIZE:,} bytes")
        return scan_data[:HP150_TOTAL_SIZE]
    
    # Si tenemos menos datos, rellenar con ceros
    if len(scan_data) < HP150_TOTAL_SIZE:
        log(f"📊 Expandiendo de {len(scan_data):,} a {HP150_TOTAL_SIZE:,} bytes")
        result = bytearray(scan_data)
        result.extend(b'\x00' * (HP150_TOTAL_SIZE - len(scan_data)))
        return bytes(result)
    
    return scan_data

def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("Uso: python3 scp_to_hp150_scan.py <archivo.scp> <salida.img>")
        print("")
        print("Convierte archivos SCP a formato HP-150 usando ibm.scan")
        print("")
        print("Ejemplo:")
        print("  python3 scp_to_hp150_scan.py floppy.scp hp150_disk.img")
        sys.exit(1)
    
    scp_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(scp_file):
        print(f"❌ Archivo no encontrado: {scp_file}")
        sys.exit(1)
    
    success = convert_scp_to_hp150_scan(scp_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
