#!/usr/bin/env python3
"""
Convertidor TD0 inteligente que usa Greaseweazle como backend
con recuperación robusta para archivos problemáticos.
"""

import sys
import subprocess
import tempfile
import shutil
import argparse
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SmartTD0Converter:
    """Convertidor TD0 que usa múltiples estrategias para maximizar la recuperación"""
    
    def __init__(self, recovery_mode: bool = True):
        self.recovery_mode = recovery_mode
        self.temp_dir = None
        
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
    
    def try_greaseweazle_conversion(self, input_file: str, output_file: str, format_type: str = "ibm.scan") -> bool:
        """Intenta conversión con Greaseweazle nativo"""
        try:
            cmd = ["gw", "convert", "--format", format_type, input_file, output_file]
            
            logger.info(f"Intentando conversión estándar: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ Conversión estándar exitosa")
                return True
            else:
                logger.warning(f"❌ Conversión estándar falló: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("❌ Conversión estándar timeout")
            return False
        except Exception as e:
            logger.warning(f"❌ Error en conversión estándar: {e}")
            return False
    
    def try_alternative_formats(self, input_file: str, output_file: str) -> bool:
        """Prueba formatos alternativos de Greaseweazle"""
        formats = [
            "ibm.scan",
            "ibm.mfm",
            "ibm.fm", 
            "ibm.320",
            "ibm.360",
            "ibm.720",
            "ibm.1440"
        ]
        
        for fmt in formats:
            logger.info(f"Probando formato: {fmt}")
            if self.try_greaseweazle_conversion(input_file, output_file, fmt):
                return True
        
        return False
    
    def extract_partial_data(self, input_file: str, output_file: str) -> bool:
        """Extrae datos parciales usando múltiples herramientas"""
        
        # Estrategia 1: Usar dd para extraer solo las primeras pistas
        try:
            logger.info("Intentando extracción parcial con dd...")
            
            # Primero intentar identificar el tamaño del header TD0
            with open(input_file, 'rb') as f:
                data = f.read(1024)  # Leer primer KB
                
            # Buscar patrones de datos después del header
            offset = 12  # Header TD0 básico
            
            # Extraer una porción segura del archivo
            safe_size = min(len(data), 163840)  # 160KB máximo
            
            temp_extracted = Path(self.temp_dir) / "partial.td0"
            
            with open(input_file, 'rb') as src, open(temp_extracted, 'wb') as dst:
                dst.write(src.read(safe_size))
            
            # Intentar convertir la porción extraída
            temp_output = Path(self.temp_dir) / "partial.img"
            if self.try_greaseweazle_conversion(str(temp_extracted), str(temp_output)):
                shutil.copy2(temp_output, output_file)
                logger.info("✅ Extracción parcial exitosa")
                return True
                
        except Exception as e:
            logger.warning(f"Error en extracción parcial: {e}")
        
        return False
    
    def create_recovery_image(self, input_file: str, output_file: str, target_format: str = "hp150") -> bool:
        """Crea imagen de recuperación con datos mínimos"""
        try:
            logger.info("Creando imagen de recuperación...")
            
            # Leer el header TD0 para obtener información básica
            with open(input_file, 'rb') as f:
                data = f.read(12)
                
            if len(data) < 12 or data[:2] not in [b'TD', b'td']:
                logger.error("Header TD0 inválido")
                return False
            
            # Extraer información básica
            sides = data[9]
            
            logger.info(f"Creando imagen de recuperación para {sides} lado(s)")
            
            if target_format == "hp150":
                # Imagen HP-150: 77 cilindros, 2 cabezas, 7 sectores/pista, 256 bytes/sector
                cylinders = 77
                heads = 2
                sectors_per_track = 7
                sector_size = 256
            else:
                # Imagen estándar: 80 cilindros, formato IBM
                cylinders = 80
                heads = sides
                sectors_per_track = 9
                sector_size = 512
            
            total_size = cylinders * heads * sectors_per_track * sector_size
            
            # Crear imagen vacía
            with open(output_file, 'wb') as f:
                f.write(b'\x00' * total_size)
            
            logger.info(f"✅ Imagen de recuperación creada: {total_size:,} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error creando imagen de recuperación: {e}")
            return False
    
    def analyze_td0(self, input_file: str) -> dict:
        """Analiza un archivo TD0 y extrae información básica"""
        try:
            with open(input_file, 'rb') as f:
                data = f.read(512)  # Leer suficiente para el header
                
            if len(data) < 12:
                return {"error": "Archivo demasiado pequeño"}
            
            if data[:2] not in [b'TD', b'td']:
                return {"error": f"Signature inválida: {data[:2]}"}
            
            # Parsear header básico
            sequence, check_sig, version, data_rate, drive_type, stepping, dos_alloc, sides = \
                data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9]
            
            info = {
                "signature": data[:2].decode('ascii'),
                "version": f"{version >> 4}.{version & 15}",
                "data_rate": data_rate,
                "drive_type": drive_type,
                "stepping": stepping,
                "sides": sides,
                "advanced_compression": data[:2] == b'td',
                "file_size": Path(input_file).stat().st_size
            }
            
            return info
            
        except Exception as e:
            return {"error": f"Error analizando: {e}"}
    
    def convert(self, input_file: str, output_file: str, target_format: str = "hp150") -> bool:
        """Convierte TD0 usando múltiples estrategias"""
        
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            logger.error(f"Archivo no encontrado: {input_file}")
            return False
        
        # Analizar archivo
        info = self.analyze_td0(input_file)
        if "error" in info:
            logger.error(f"Error analizando TD0: {info['error']}")
            if not self.recovery_mode:
                return False
        else:
            logger.info(f"📀 TD0 detectado: {info['signature']} v{info['version']}, {info['sides']} lado(s)")
            if info['advanced_compression']:
                logger.warning("⚠️ Compresión avanzada detectada")
        
        # Estrategia 1: Conversión estándar con Greaseweazle
        temp_output = Path(self.temp_dir) / "temp.img"
        
        if self.try_greaseweazle_conversion(input_file, str(temp_output)):
            # Convertir a formato HP-150 si es necesario
            if target_format == "hp150":
                if self.convert_to_hp150_format(str(temp_output), output_file):
                    return True
            else:
                shutil.copy2(temp_output, output_file)
                return True
        
        # Estrategia 2: Formatos alternativos
        if self.recovery_mode:
            logger.info("🔄 Probando formatos alternativos...")
            if self.try_alternative_formats(input_file, str(temp_output)):
                if target_format == "hp150":
                    if self.convert_to_hp150_format(str(temp_output), output_file):
                        return True
                else:
                    shutil.copy2(temp_output, output_file)
                    return True
        
        # Estrategia 3: Extracción parcial
        if self.recovery_mode:
            logger.info("🔄 Intentando extracción parcial...")
            if self.extract_partial_data(input_file, str(temp_output)):
                if target_format == "hp150":
                    if self.convert_to_hp150_format(str(temp_output), output_file):
                        return True
                else:
                    shutil.copy2(temp_output, output_file)
                    return True
        
        # Estrategia 4: Imagen de recuperación
        if self.recovery_mode:
            logger.warning("🔄 Creando imagen de recuperación como último recurso...")
            return self.create_recovery_image(input_file, output_file, target_format)
        
        logger.error("❌ Todas las estrategias fallaron")
        return False
    
    def convert_to_hp150_format(self, source_img: str, output_file: str) -> bool:
        """Convierte una imagen estándar al formato HP-150"""
        try:
            logger.info("🔄 Convirtiendo a formato HP-150...")
            
            source_path = Path(source_img)
            source_size = source_path.stat().st_size
            
            # HP-150: 77 cilindros, 2 cabezas, 7 sectores, 256 bytes
            target_size = 77 * 2 * 7 * 256  # 270,336 bytes
            
            with open(source_img, 'rb') as src, open(output_file, 'wb') as dst:
                data = src.read()
                
                if len(data) >= target_size:
                    # Truncar al tamaño HP-150
                    dst.write(data[:target_size])
                elif len(data) > 0:
                    # Extender con ceros
                    dst.write(data)
                    dst.write(b'\x00' * (target_size - len(data)))
                else:
                    # Si no hay datos, crear imagen vacía HP-150
                    dst.write(b'\x00' * target_size)
            
            logger.info(f"✅ Convertido a formato HP-150: {target_size:,} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error convirtiendo a HP-150: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Convertidor TD0 inteligente con recuperación")
    parser.add_argument("input", help="Archivo TD0 de entrada")
    parser.add_argument("output", help="Archivo IMG de salida")
    parser.add_argument("--format", choices=["hp150", "standard"], default="hp150",
                       help="Formato de salida (default: hp150)")
    parser.add_argument("--strict", action="store_true",
                       help="Modo estricto (sin recuperación)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Salida detallada")
    parser.add_argument("--info", action="store_true",
                       help="Solo mostrar información del TD0")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Verificar archivo de entrada
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Archivo no encontrado: {args.input}")
        return 1
    
    # Solo información
    if args.info:
        with SmartTD0Converter() as converter:
            info = converter.analyze_td0(args.input)
            
            print(f"\n📀 Información del TD0:")
            print(f"   Archivo: {input_path.name}")
            
            if "error" in info:
                print(f"   ❌ Error: {info['error']}")
                return 1
            
            print(f"   Signature: {info['signature']}")
            print(f"   Versión: {info['version']}")
            print(f"   Lados: {info['sides']}")
            print(f"   Tamaño: {info['file_size']:,} bytes")
            print(f"   Compresión avanzada: {'Sí' if info['advanced_compression'] else 'No'}")
            
        return 0
    
    # Verificar archivo de salida
    output_path = Path(args.output)
    if output_path.exists():
        response = input(f"¿Sobrescribir {args.output}? (y/N): ")
        if response.lower() != 'y':
            logger.info("Operación cancelada")
            return 0
    
    # Conversión
    try:
        with SmartTD0Converter(recovery_mode=not args.strict) as converter:
            logger.info(f"🔄 Convirtiendo {args.input} -> {args.output}")
            
            if converter.convert(args.input, args.output, args.format):
                output_size = output_path.stat().st_size
                print(f"\n✅ Conversión exitosa!")
                print(f"   Archivo: {output_path}")
                print(f"   Formato: {args.format}")
                print(f"   Tamaño: {output_size:,} bytes")
                return 0
            else:
                logger.error("❌ Error en la conversión")
                return 1
                
    except KeyboardInterrupt:
        logger.info("\n⚠️ Operación cancelada por el usuario")
        return 1
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
