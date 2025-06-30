#!/usr/bin/env python3
"""
Convertidor TD0 a HP-150 IMG - Implementación Directa
Basado en la especificación TeleDisk con optimizaciones para HP-150
"""

import struct
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import zlib

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TD0Header:
    """Header principal del archivo TD0"""
    signature: str          # 'TD' o 'td'
    sequence: int          # Número de secuencia
    check_sig: int         # Checksum del header
    version: int           # Versión TeleDisk
    data_rate: int         # Velocidad de datos
    drive_type: int        # Tipo de drive
    stepping: int          # Stepping
    dos_allocation: int    # Asignación DOS
    sides: int            # Número de lados
    crc: int              # CRC del header

@dataclass
class TrackHeader:
    """Header de pista"""
    sectors: int          # Número de sectores
    cylinder: int         # Cilindro
    head: int            # Cabeza
    crc: int             # CRC

@dataclass
class SectorHeader:
    """Header de sector"""
    cylinder: int         # C
    head: int            # H
    sector: int          # R
    size_code: int       # N (código de tamaño)
    flags: int           # Flags del sector
    crc: int             # CRC
    data_length: int     # Longitud de datos

class TD0Converter:
    """Convertidor TD0 con implementación directa del formato"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reiniciar el estado del convertidor"""
        self.header = None
        self.tracks = {}
        self.advanced_compression = False
        self.current_pos = 0
        self.data = b''
    
    def read_header(self, data: bytes, offset: int = 0) -> Tuple[TD0Header, int]:
        """Leer y parsear el header TD0"""
        if len(data) < offset + 12:
            raise ValueError("Archivo demasiado corto para header TD0")
        
        # Leer campos básicos del header
        sig = data[offset:offset+2]
        sequence = data[offset+2]
        check_sig = data[offset+3]
        version = data[offset+4]
        data_rate = data[offset+5]
        drive_type = data[offset+6]
        stepping = data[offset+7]
        dos_allocation = data[offset+8]
        sides = data[offset+9]
        crc = struct.unpack('<H', data[offset+10:offset+12])[0]
        
        # Verificar signature
        if sig not in [b'TD', b'td']:
            raise ValueError(f"Signature TD0 inválida: {sig}")
        
        # Detectar compresión avanzada
        self.advanced_compression = (sig == b'td')
        
        header = TD0Header(
            signature=sig.decode('ascii'),
            sequence=sequence,
            check_sig=check_sig,
            version=version,
            data_rate=data_rate,
            drive_type=drive_type,
            stepping=stepping,
            dos_allocation=dos_allocation,
            sides=sides,
            crc=crc
        )
        
        logger.info(f"Header TD0: {header.signature}, versión {header.version >> 4}.{header.version & 15}")
        logger.info(f"Lados: {header.sides}, Compresión avanzada: {self.advanced_compression}")
        
        # Saltar comentario si existe
        next_offset = offset + 12
        if len(data) > next_offset + 2:
            comment_crc = struct.unpack('<H', data[next_offset:next_offset+2])[0]
            if comment_crc != 0:
                # Hay comentario, calculamos su tamaño
                comment_length = struct.unpack('<H', data[next_offset+2:next_offset+4])[0]
                next_offset += 4 + comment_length
                logger.info(f"Saltando comentario de {comment_length} bytes")
            else:
                next_offset += 2
        
        return header, next_offset
    
    def sector_size_from_code(self, size_code: int) -> int:
        """Convertir código de tamaño a bytes"""
        if size_code <= 6:
            return 128 << size_code
        else:
            # Códigos especiales o no estándar
            return 256  # Default para HP-150
    
    def read_track_header(self, data: bytes, offset: int) -> Tuple[Optional[TrackHeader], int]:
        """Leer header de pista"""
        if offset >= len(data):
            return None, offset
        
        if len(data) < offset + 4:
            logger.warning("Datos insuficientes para header de pista")
            return None, offset
        
        sectors = data[offset]
        cylinder = data[offset + 1]
        head = data[offset + 2]
        crc = data[offset + 3]
        
        # Verificar si es el marcador de fin
        if sectors == 0xFF:
            logger.info("Marcador de fin de archivo encontrado")
            return None, offset + 4
        
        header = TrackHeader(
            sectors=sectors,
            cylinder=cylinder,
            head=head,
            crc=crc
        )
        
        logger.debug(f"Pista C:{cylinder} H:{head}, {sectors} sectores")
        return header, offset + 4
    
    def decompress_rle(self, data: bytes, expected_length: int) -> bytes:
        """Descomprimir datos RLE (Run Length Encoding)"""
        result = bytearray()
        i = 0
        
        while i < len(data) and len(result) < expected_length:
            if i + 1 >= len(data):
                break
                
            # Leer par de control
            pair = struct.unpack('<H', data[i:i+2])[0]
            i += 2
            
            if pair == 0x0000:
                # Datos literales
                if i >= len(data):
                    break
                length = data[i]
                i += 1
                
                if i + length > len(data):
                    logger.warning(f"RLE: datos literales truncados")
                    length = len(data) - i
                
                result.extend(data[i:i+length])
                i += length
                
            else:
                # Repetición RLE
                count = pair >> 8
                value = pair & 0xFF
                
                if count == 0:
                    count = 256
                
                result.extend([value] * count)
        
        # Rellenar si es necesario
        while len(result) < expected_length:
            result.append(0)
        
        return bytes(result[:expected_length])
    
    def read_sector_data(self, data: bytes, offset: int, sector_header: SectorHeader) -> Tuple[bytes, int]:
        """Leer y descomprimir datos de sector"""
        if offset >= len(data):
            logger.warning("Offset fuera de rango para datos de sector")
            return b'\x00' * self.sector_size_from_code(sector_header.size_code), offset
        
        # Determinar tamaño esperado
        expected_size = self.sector_size_from_code(sector_header.size_code)
        
        # Leer datos según el tipo de codificación
        encoding = sector_header.flags & 0x07
        
        if encoding == 0:
            # Datos raw sin compresión
            end_offset = offset + sector_header.data_length
            if end_offset > len(data):
                logger.warning(f"Datos raw truncados")
                end_offset = len(data)
            
            sector_data = data[offset:end_offset]
            
            # Rellenar si es necesario
            if len(sector_data) < expected_size:
                sector_data += b'\x00' * (expected_size - len(sector_data))
            
            return sector_data[:expected_size], end_offset
        
        elif encoding == 1:
            # Datos repetidos (todos el mismo valor)
            if offset < len(data):
                fill_value = data[offset]
                return bytes([fill_value] * expected_size), offset + 1
            else:
                return b'\x00' * expected_size, offset
        
        elif encoding == 2:
            # Compresión RLE
            end_offset = offset + sector_header.data_length
            if end_offset > len(data):
                logger.warning(f"Datos RLE truncados")
                end_offset = len(data)
            
            compressed_data = data[offset:end_offset]
            
            try:
                sector_data = self.decompress_rle(compressed_data, expected_size)
                return sector_data, end_offset
            except Exception as e:
                logger.warning(f"Error descomprimiendo RLE: {e}")
                return b'\x00' * expected_size, end_offset
        
        else:
            logger.warning(f"Codificación desconocida: {encoding}")
            return b'\x00' * expected_size, offset + sector_header.data_length
    
    def read_sector_header(self, data: bytes, offset: int) -> Tuple[Optional[SectorHeader], int]:
        """Leer header de sector"""
        if len(data) < offset + 6:
            logger.warning("Datos insuficientes para header de sector")
            return None, offset
        
        cylinder = data[offset]
        head = data[offset + 1]
        sector = data[offset + 2]
        size_code = data[offset + 3]
        flags = data[offset + 4]
        crc = data[offset + 5]
        
        # Calcular longitud de datos
        if flags & 0x30:  # Datos presentes
            if len(data) < offset + 8:
                logger.warning("Datos insuficientes para longitud de datos")
                return None, offset
            data_length = struct.unpack('<H', data[offset + 6:offset + 8])[0]
            header_size = 8
        else:
            data_length = 0
            header_size = 6
        
        header = SectorHeader(
            cylinder=cylinder,
            head=head,
            sector=sector,
            size_code=size_code,
            flags=flags,
            crc=crc,
            data_length=data_length
        )
        
        return header, offset + header_size
    
    def parse_td0(self, data: bytes) -> Dict:
        """Parsear completamente un archivo TD0"""
        logger.info("Iniciando parseo de archivo TD0...")
        
        # Leer header principal
        self.header, offset = self.read_header(data)
        
        # Inicializar estructura de datos
        disk_data = {}
        track_count = 0
        sector_count = 0
        
        # Leer pistas
        while offset < len(data):
            # Leer header de pista
            track_header, offset = self.read_track_header(data, offset)
            
            if track_header is None:
                break
            
            track_key = (track_header.cylinder, track_header.head)
            track_data = []
            
            # Leer sectores de esta pista
            for sector_idx in range(track_header.sectors):
                # Leer header de sector
                sector_header, offset = self.read_sector_header(data, offset)
                
                if sector_header is None:
                    logger.warning(f"Header de sector inválido en pista {track_key}")
                    break
                
                # Leer datos de sector
                sector_data, offset = self.read_sector_data(data, offset, sector_header)
                
                track_data.append({
                    'header': sector_header,
                    'data': sector_data
                })
                
                sector_count += 1
                logger.debug(f"Sector C:{sector_header.cylinder} H:{sector_header.head} R:{sector_header.sector}")
            
            disk_data[track_key] = track_data
            track_count += 1
            
            if track_count % 10 == 0:
                logger.info(f"Procesadas {track_count} pistas...")
        
        logger.info(f"Parseo completado: {track_count} pistas, {sector_count} sectores")
        return disk_data
    
    def create_hp150_image(self, disk_data: Dict, output_size: int = 304640) -> bytes:
        """Crear imagen HP-150 estándar"""
        logger.info("Creando imagen HP-150...")
        
        # HP-150: 70 pistas, 1 lado, 17 sectores/pista, 256 bytes/sector
        hp150_data = bytearray(output_size)
        
        sectors_written = 0
        
        for cylinder in range(70):  # HP-150 usa 70 pistas
            for head in range(1):   # Solo 1 lado
                track_key = (cylinder, head)
                
                if track_key in disk_data:
                    track = disk_data[track_key]
                    
                    # Ordenar sectores por número de sector
                    track.sort(key=lambda s: s['header'].sector)
                    
                    for sector_idx, sector_info in enumerate(track):
                        if sector_idx >= 17:  # HP-150 tiene máximo 17 sectores
                            break
                        
                        # Calcular posición en la imagen
                        logical_sector = cylinder * 17 + sector_idx
                        offset = logical_sector * 256
                        
                        if offset + 256 <= len(hp150_data):
                            sector_data = sector_info['data'][:256]  # HP-150 usa 256 bytes
                            hp150_data[offset:offset+len(sector_data)] = sector_data
                            sectors_written += 1
        
        logger.info(f"Imagen HP-150 creada: {sectors_written} sectores escritos")
        return bytes(hp150_data)
    
    def convert_td0_to_hp150(self, input_path: str, output_path: str) -> bool:
        """Función principal de conversión"""
        try:
            logger.info(f"Convirtiendo {input_path} -> {output_path}")
            
            # Leer archivo TD0
            with open(input_path, 'rb') as f:
                td0_data = f.read()
            
            logger.info(f"Archivo TD0 leído: {len(td0_data):,} bytes")
            
            # Parsear TD0
            disk_data = self.parse_td0(td0_data)
            
            if not disk_data:
                logger.error("No se pudieron extraer datos del archivo TD0")
                return False
            
            # Crear imagen HP-150
            hp150_image = self.create_hp150_image(disk_data)
            
            # Escribir imagen de salida
            with open(output_path, 'wb') as f:
                f.write(hp150_image)
            
            logger.info(f"Conversión exitosa: {output_path} ({len(hp150_image):,} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error en conversión: {e}")
            return False

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Convertidor TD0 a HP-150 IMG con implementación directa"
    )
    parser.add_argument("input", help="Archivo TD0 de entrada")
    parser.add_argument("output", help="Archivo IMG HP-150 de salida")
    parser.add_argument("-v", "--verbose", action="store_true", help="Salida detallada")
    parser.add_argument("--info", action="store_true", help="Solo mostrar información del TD0")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Verificar archivo de entrada
    if not Path(args.input).exists():
        logger.error(f"Archivo no encontrado: {args.input}")
        return 1
    
    converter = TD0Converter()
    
    if args.info:
        # Solo mostrar información
        try:
            with open(args.input, 'rb') as f:
                data = f.read()
            
            header, _ = converter.read_header(data)
            
            print(f"\n📁 Información del archivo TD0: {args.input}")
            print(f"   Signature: {header.signature}")
            print(f"   Versión: {header.version >> 4}.{header.version & 15}")
            print(f"   Lados: {header.sides}")
            print(f"   Tipo de drive: {header.drive_type}")
            print(f"   Compresión avanzada: {'Sí' if converter.advanced_compression else 'No'}")
            print(f"   Tamaño archivo: {len(data):,} bytes")
            
        except Exception as e:
            logger.error(f"Error leyendo archivo: {e}")
            return 1
    else:
        # Realizar conversión
        success = converter.convert_td0_to_hp150(args.input, args.output)
        return 0 if success else 1

if __name__ == "__main__":
    exit(main())
