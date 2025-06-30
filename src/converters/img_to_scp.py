#!/usr/bin/env python3
"""
Conversor de IMG (imagen HP-150) a SCP (formato GreaseWeazle)
Para escribir imágenes HP-150 a floppies físicos usando GreaseWeazle
"""

import sys
import os
import subprocess
import tempfile

def log(message):
    """Log mensaje a stdout"""
    print(message)
    sys.stdout.flush()

def convert_img_to_scp(img_file, scp_file):
    """
    Convertir imagen HP-150 (.img) a formato SCP para GreaseWeazle
    
    Este proceso es el inverso del convertidor scp_to_hp150_scan.py:
    1. Tomar el archivo IMG (formato HP-150)
    2. Convertirlo a formato SCP usando GreaseWeazle con formato ibm.scan
    
    Formato HP-150:
    - 77 cilindros (0-76)
    - 2 cabezas (0-1)
    - 7 sectores por pista (0-6)
    - 256 bytes por sector
    - Total: 1056 sectores = 270,336 bytes
    """
    
    log(f"🔄 Convirtiendo IMG a SCP para escritura")
    log(f"Entrada: {img_file}")
    log(f"Salida: {scp_file}")
    
    # Verificar archivo de entrada
    if not os.path.exists(img_file):
        log(f"❌ ERROR: Archivo {img_file} no existe")
        return False
    
    file_size = os.path.getsize(img_file)
    expected_size = 270336  # 1056 sectores * 256 bytes
    
    log(f"📏 Tamaño del archivo: {file_size} bytes")
    log(f"📏 Tamaño esperado: {expected_size} bytes")
    
    if file_size != expected_size:
        log(f"⚠️ ADVERTENCIA: Tamaño no estándar para HP-150")
    
    try:
        # Para convertir IMG a SCP necesitamos usar GreaseWeazle en modo reverso
        # El formato ibm.scan debe ser usado como formato de SALIDA, no de entrada
        log("🔍 Ejecutando GreaseWeazle convert IMG→SCP...")
        
        # Usar GreaseWeazle convert para convertir de IMG a SCP
        # Necesitamos especificar un formato IBM que sea compatible con IMG de entrada
        # El HP-150 usa formato similar a IBM PC pero con geometría diferente
        cmd = [
            "gw", "convert",
            img_file,
            scp_file,
            "--format=ibm.360",  # Formato IBM compatible como base
            "--tracks=c=0-76:h=0-1"
        ]
        
        log(f"💻 Comando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            log("✅ Conversión GreaseWeazle completada")
            
            if os.path.exists(scp_file):
                scp_size = os.path.getsize(scp_file)
                log(f"📁 Archivo SCP creado: {scp_size:,} bytes")
                log(f"✅ Conversión completada: {scp_file}")
                return True
            else:
                log("❌ ERROR: Archivo SCP no fue creado")
                return False
        else:
            log(f"❌ ERROR en GreaseWeazle convert:")
            log(f"STDOUT: {result.stdout}")
            log(f"STDERR: {result.stderr}")
            
            # Si falla la conversión directa, intentar método alternativo
            log("🔄 Intentando método alternativo...")
            return try_alternative_conversion(img_file, scp_file)
            
    except Exception as e:
        log(f"❌ ERROR durante la conversión: {e}")
        return False

def try_alternative_conversion(img_file, scp_file):
    """
    Método alternativo de conversión usando formato raw
    """
    try:
        log("🔧 Probando conversión con formato raw...")
        
        # Intentar con formato raw y especificar geometría
        cmd = [
            "gw", "convert",
            img_file,
            scp_file,
            "--format=raw",
            "--tracks=c=0-76:h=0-1"
        ]
        
        log(f"💻 Comando alternativo: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(scp_file):
            scp_size = os.path.getsize(scp_file)
            log(f"✅ Conversión alternativa exitosa: {scp_size:,} bytes")
            return True
        else:
            log(f"❌ Conversión alternativa falló: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"❌ ERROR en conversión alternativa: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 img_to_scp.py <archivo.img> <archivo.scp>")
        print("Convierte imagen HP-150 a formato SCP para GreaseWeazle")
        sys.exit(1)
    
    img_file = sys.argv[1]
    scp_file = sys.argv[2]
    
    print("=== Conversor IMG → SCP para HP-150 ===")
    print()
    
    success = convert_img_to_scp(img_file, scp_file)
    
    if success:
        print()
        print("✅ Conversión completada exitosamente")
        print(f"Archivo SCP listo para escribir con GreaseWeazle: {scp_file}")
        sys.exit(0)
    else:
        print()
        print("❌ Error en la conversión")
        sys.exit(1)

if __name__ == "__main__":
    main()
