#!/usr/bin/env python3
"""
Conversor de HP-150 IMG a TD0 usando SAMdisk
Permite crear archivos TD0 compatibles con Teledisk desde imágenes HP-150
"""

import sys
import os
import subprocess
import tempfile
import shutil
import argparse
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HP150ToTD0Converter:
    """Conversor de HP-150 IMG a TD0"""
    
    # Especificaciones HP-150
    HP150_CYLINDERS = 77
    HP150_HEADS = 2
    HP150_SECTORS_PER_TRACK = 7
    HP150_BYTES_PER_SECTOR = 256
    HP150_TOTAL_SIZE = HP150_CYLINDERS * HP150_HEADS * HP150_SECTORS_PER_TRACK * HP150_BYTES_PER_SECTOR
    
    def __init__(self):
        self.temp_dir = None
        
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
    
    def check_samdisk_available(self) -> bool:
        """Verificar si SAMdisk está disponible"""
        try:
            result = subprocess.run(['samdisk', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ SAMdisk encontrado: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("❌ SAMdisk no encontrado")
        return False
    
    def check_greaseweazle_available(self) -> bool:
        """Verificar si GreaseWeazle está disponible como alternativa"""
        try:
            result = subprocess.run(['gw', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ GreaseWeazle encontrado")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("❌ GreaseWeazle no encontrado")
        return False
    
    def validate_hp150_image(self, img_file: str) -> bool:
        """Validar que sea una imagen HP-150 válida"""
        try:
            file_size = os.path.getsize(img_file)
            logger.info(f"📏 Tamaño del archivo: {file_size:,} bytes")
            
            if file_size == self.HP150_TOTAL_SIZE:
                logger.info("✅ Tamaño correcto para HP-150")
                return True
            elif file_size > 0:
                logger.warning(f"⚠️  Tamaño no estándar (esperado: {self.HP150_TOTAL_SIZE:,} bytes)")
                return True  # Permitir conversión de todos modos
            else:
                logger.error("❌ Archivo vacío")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validando imagen: {e}")
            return False
    
    def convert_with_samdisk(self, input_file: str, output_file: str) -> bool:
        """Convertir usando SAMdisk"""
        try:
            logger.info("🔄 Convirtiendo con SAMdisk...")
            
            # Comando SAMdisk para convertir IMG a TD0
            cmd = [
                'samdisk',
                input_file,
                output_file,
                '--format=td0'
            ]
            
            # Opciones adicionales para HP-150
            # SAMdisk puede necesitar especificaciones de geometría
            extended_cmd = [
                'samdisk',
                input_file,
                output_file,
                '--format=td0',
                f'--cyls={self.HP150_CYLINDERS}',
                f'--heads={self.HP150_HEADS}',
                f'--sectors={self.HP150_SECTORS_PER_TRACK}',
                '--size=256'
            ]
            
            logger.info(f"Comando: {' '.join(extended_cmd)}")
            
            # Intentar con especificaciones de geometría primero
            result = subprocess.run(
                extended_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("✅ Conversión con SAMdisk exitosa")
                return True
            else:
                logger.warning(f"⚠️  Conversión con geometría falló: {result.stderr}")
                
                # Intentar conversión simple
                logger.info("🔄 Intentando conversión simple...")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    logger.info("✅ Conversión simple con SAMdisk exitosa")
                    return True
                else:
                    logger.error(f"❌ SAMdisk falló: {result.stderr}")
                    return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ SAMdisk timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Error con SAMdisk: {e}")
            return False
    
    def convert_with_greaseweazle(self, input_file: str, output_file: str) -> bool:
        """Convertir usando GreaseWeazle como alternativa"""
        try:
            logger.info("🔄 Convirtiendo con GreaseWeazle...")
            
            # GreaseWeazle puede convertir a SCP y luego a TD0
            temp_scp = os.path.join(self.temp_dir, 'temp.scp')
            
            # Primero convertir IMG a SCP
            cmd_img_to_scp = [
                'gw', 'convert',
                '--format=ibm.scan',
                f'--tracks=c=0-{self.HP150_CYLINDERS-1}:h=0-{self.HP150_HEADS-1}',
                input_file,
                temp_scp
            ]
            
            logger.info(f"Paso 1 - IMG→SCP: {' '.join(cmd_img_to_scp)}")
            
            result = subprocess.run(
                cmd_img_to_scp,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Error IMG→SCP: {result.stderr}")
                return False
            
            # Luego convertir SCP a TD0 (si GreaseWeazle lo soporta)
            cmd_scp_to_td0 = [
                'gw', 'convert',
                '--format=td0',
                temp_scp,
                output_file
            ]
            
            logger.info(f"Paso 2 - SCP→TD0: {' '.join(cmd_scp_to_td0)}")
            
            result = subprocess.run(
                cmd_scp_to_td0,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ Conversión con GreaseWeazle exitosa")
                return True
            else:
                logger.error(f"❌ Error SCP→TD0: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ GreaseWeazle timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Error con GreaseWeazle: {e}")
            return False
    
    def create_td0_manual(self, input_file: str, output_file: str) -> bool:
        """Crear TD0 manualmente (implementación básica)"""
        try:
            logger.info("🔄 Creando TD0 manualmente...")
            
            # Leer imagen HP-150
            with open(input_file, 'rb') as f:
                img_data = f.read()
            
            # Crear header TD0 básico
            td0_data = bytearray()
            
            # Header TD0 (12 bytes mínimo)
            td0_data.extend(b'TD')           # Signature
            td0_data.append(0)               # Sequence
            td0_data.append(0)               # Check signature
            td0_data.append(0x15)            # Version (1.5)
            td0_data.append(0x00)            # Data rate (500 kbps)
            td0_data.append(0x01)            # Drive type (3.5" HD)
            td0_data.append(0x00)            # Stepping
            td0_data.append(0x01)            # DOS allocation
            td0_data.append(self.HP150_HEADS) # Sides
            td0_data.extend(b'\x00\x00')     # CRC (calculado después)
            
            # Comment CRC (no comment)
            td0_data.extend(b'\x00\x00')
            
            # Procesar pistas
            sector_size = self.HP150_BYTES_PER_SECTOR
            
            for cylinder in range(self.HP150_CYLINDERS):
                for head in range(self.HP150_HEADS):
                    # Track header
                    td0_data.append(self.HP150_SECTORS_PER_TRACK)  # Sectors
                    td0_data.append(cylinder)                      # Cylinder
                    td0_data.append(head)                         # Head
                    td0_data.append(0)                            # CRC
                    
                    # Sectores de esta pista
                    for sector in range(1, self.HP150_SECTORS_PER_TRACK + 1):
                        # Sector header
                        td0_data.append(cylinder)    # C
                        td0_data.append(head)        # H
                        td0_data.append(sector)      # R
                        td0_data.append(1)           # N (256 bytes = 2^1 * 128)
                        td0_data.append(0x30)        # Flags (datos presentes)
                        td0_data.append(0)           # CRC
                        td0_data.extend(struct.pack('<H', sector_size))  # Data length
                        
                        # Datos del sector
                        offset = ((cylinder * self.HP150_HEADS + head) * 
                                self.HP150_SECTORS_PER_TRACK + (sector - 1)) * sector_size
                        
                        if offset + sector_size <= len(img_data):
                            sector_data = img_data[offset:offset + sector_size]
                        else:
                            sector_data = b'\x00' * sector_size
                        
                        td0_data.extend(sector_data)
            
            # Marcador de fin
            td0_data.append(0xFF)
            td0_data.extend(b'\x00\x00\x00')
            
            # Escribir archivo TD0
            with open(output_file, 'wb') as f:
                f.write(td0_data)
            
            logger.info(f"✅ TD0 manual creado: {len(td0_data):,} bytes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando TD0 manual: {e}")
            return False
    
    def convert(self, input_file: str, output_file: str, method: str = 'auto') -> bool:
        """Convertir HP-150 IMG a TD0"""
        
        # Validar archivo de entrada
        if not os.path.exists(input_file):
            logger.error(f"❌ Archivo no encontrado: {input_file}")
            return False
        
        if not self.validate_hp150_image(input_file):
            return False
        
        logger.info(f"🔄 Convirtiendo {input_file} → {output_file}")
        
        # Determinar método a usar
        if method == 'auto':
            if self.check_samdisk_available():
                method = 'samdisk'
            elif self.check_greaseweazle_available():
                method = 'greaseweazle'
            else:
                method = 'manual'
                logger.warning("⚠️  No se encontraron herramientas externas, usando método manual")
        
        # Intentar conversión según el método
        success = False
        
        if method == 'samdisk':
            success = self.convert_with_samdisk(input_file, output_file)
        elif method == 'greaseweazle':
            success = self.convert_with_greaseweazle(input_file, output_file)
        elif method == 'manual':
            success = self.create_td0_manual(input_file, output_file)
        else:
            logger.error(f"❌ Método desconocido: {method}")
            return False
        
        # Si el método preferido falla, intentar alternativas
        if not success and method != 'manual':
            logger.warning("🔄 Método principal falló, intentando método manual...")
            success = self.create_td0_manual(input_file, output_file)
        
        return success

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Conversor de HP-150 IMG a TD0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Conversión automática (detecta herramientas disponibles)
  python3 hp150_to_td0.py imagen.img salida.TD0
  
  # Forzar uso de SAMdisk
  python3 hp150_to_td0.py imagen.img salida.TD0 --method samdisk
  
  # Usar método manual (sin herramientas externas)
  python3 hp150_to_td0.py imagen.img salida.TD0 --method manual

Herramientas soportadas:
  - SAMdisk (recomendado): https://simonowen.com/samdisk/
  - GreaseWeazle (alternativo): https://github.com/keirf/greaseweazle
  - Método manual (básico, siempre disponible)
        """
    )
    
    parser.add_argument('input_file', help='Archivo IMG HP-150 de entrada')
    parser.add_argument('output_file', help='Archivo TD0 de salida')
    
    parser.add_argument('--method', choices=['auto', 'samdisk', 'greaseweazle', 'manual'],
                       default='auto', help='Método de conversión (default: auto)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 60)
    print("🔄 CONVERSOR HP-150 IMG → TD0")
    print("=" * 60)
    print(f"Entrada: {args.input_file}")
    print(f"Salida: {args.output_file}")
    print(f"Método: {args.method}")
    print()
    
    # Verificar si el archivo de salida existe
    if os.path.exists(args.output_file):
        response = input(f"¿Sobrescribir {args.output_file}? (y/N): ")
        if response.lower() != 'y':
            print("Operación cancelada")
            sys.exit(0)
    
    # Realizar conversión
    try:
        with HP150ToTD0Converter() as converter:
            success = converter.convert(args.input_file, args.output_file, args.method)
            
            print()
            if success:
                output_size = os.path.getsize(args.output_file)
                print("🎉 ¡Conversión completada exitosamente!")
                print(f"📁 Archivo TD0 creado: {args.output_file}")
                print(f"📏 Tamaño: {output_size:,} bytes")
                sys.exit(0)
            else:
                print("💥 Error en la conversión")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n⚠️ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import struct  # Importar struct que se usa en create_td0_manual
    main()
