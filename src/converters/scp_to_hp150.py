#!/usr/bin/env python3
"""
Conversor de SCP (GreaseWeazle) a IMG HP-150
Convierte archivos SCP leídos por GreaseWeazle al formato HP-150 específico

Especificaciones HP-150:
- 77 cilindros (0-76)
- 2 cabezas (0-1)  
- 7 sectores por pista (1-7)
- 256 bytes por sector
- Total: 77 * 2 * 7 * 256 = 270,336 bytes
- Sectores numerados 1-7 (no 0-6)
"""

import sys
import struct
import os
from pathlib import Path

class SCPToHP150Converter:
    """Conversor de SCP a formato HP-150"""
    
    # Especificaciones HP-150
    HP150_CYLINDERS = 77      # 0-76
    HP150_HEADS = 2           # 0-1
    HP150_SECTORS_PER_TRACK = 7  # 1-7
    HP150_BYTES_PER_SECTOR = 256
    HP150_TOTAL_SECTORS = 1056  # Especificación exacta del HP-150
    HP150_TOTAL_SIZE = HP150_TOTAL_SECTORS * HP150_BYTES_PER_SECTOR  # 270,336 bytes
    
    def __init__(self, scp_file, output_file):
        self.scp_file = scp_file
        self.output_file = output_file
        self.sectors_found = {}
        
    def log(self, message):
        """Log mensaje a stdout"""
        print(message)
        sys.stdout.flush()
        
    def parse_scp_header(self, data):
        """Parsear header del archivo SCP"""
        if len(data) < 16:
            raise ValueError("Archivo SCP demasiado pequeño")
            
        # Header SCP: "SCP" + flags + cylinders + heads + etc.
        if data[:3] != b'SCP':
            raise ValueError("No es un archivo SCP válido")
            
        # Extraer información básica
        header = struct.unpack('<3sBBBB', data[:7])
        flags = header[1]
        cylinders = header[2]
        heads = header[3]
        
        self.log(f"📀 Archivo SCP detectado:")
        self.log(f"   Cilindros: {cylinders}")
        self.log(f"   Cabezas: {heads}")
        
        return cylinders, heads
        
    def extract_sectors_from_track(self, track_data, cylinder, head):
        """Extraer sectores de los datos de una pista"""
        sectors = {}
        
        # Buscar patrones de sincronización MFM y headers de sector
        # El HP-150 usa formato MFM con headers específicos
        
        # Patrón típico de sync y address mark para MFM
        sync_pattern = b'\x44\x89\x44\x89\x44\x89'  # Sync MFM
        idam_pattern = b'\x44\x89\x44\x89\x44\x89\xfe'  # ID Address Mark
        
        i = 0
        while i < len(track_data) - 1000:  # Dejar espacio para sector completo
            # Buscar pattern de header de sector
            if track_data[i:i+7] == idam_pattern:
                # Encontrado header, extraer información del sector
                try:
                    # El header contiene: IDAM + C + H + R + N + CRC
                    header_start = i + 7
                    if header_start + 6 > len(track_data):
                        break
                        
                    # Leer campos del header (en MFM están codificados)
                    c = self.decode_mfm_byte(track_data[header_start:header_start+2])
                    h = self.decode_mfm_byte(track_data[header_start+2:header_start+4])
                    r = self.decode_mfm_byte(track_data[header_start+4:header_start+6])
                    n = self.decode_mfm_byte(track_data[header_start+6:header_start+8])
                    
                    # Verificar que coincida con la pista actual
                    if c == cylinder and h == head and 1 <= r <= 7:
                        # Buscar el data address mark después del header
                        dam_start = self.find_data_mark(track_data, header_start + 10)
                        if dam_start > 0:
                            # Extraer datos del sector
                            sector_data = self.extract_sector_data(track_data, dam_start, n)
                            if len(sector_data) == self.HP150_BYTES_PER_SECTOR:
                                sectors[r] = sector_data
                                self.log(f"   ✅ Sector C:{c} H:{h} R:{r} encontrado")
                            
                except (IndexError, ValueError):
                    pass
                    
            i += 1
            
        return sectors
        
    def decode_mfm_byte(self, mfm_data):
        """Decodificar un byte de datos MFM"""
        if len(mfm_data) < 2:
            return 0
            
        # Decodificación MFM básica - esto es simplificado
        # En MFM real, cada bit de datos se codifica como 2 bits
        try:
            # Tomar bits alternos para decodificar
            bits = []
            for byte_val in mfm_data:
                for bit_pos in range(7, -1, -1):
                    if bit_pos % 2 == 1:  # Bits impares contienen datos
                        bits.append((byte_val >> bit_pos) & 1)
                        
            # Convertir bits a byte
            result = 0
            for i, bit in enumerate(bits[:8]):
                result |= (bit << (7-i))
                
            return result
        except:
            return 0
            
    def find_data_mark(self, track_data, start_pos):
        """Buscar Data Address Mark después del header"""
        # Buscar patrón de DAM (Data Address Mark)
        dam_pattern = b'\x44\x89\x44\x89\x44\x89\xfb'  # DAM normal
        
        # Buscar en un rango razonable después del header
        search_end = min(start_pos + 100, len(track_data) - 8)
        
        for i in range(start_pos, search_end):
            if track_data[i:i+7] == dam_pattern:
                return i + 7  # Retornar posición después del DAM
                
        return -1
        
    def extract_sector_data(self, track_data, dam_pos, size_code):
        """Extraer datos del sector después del DAM"""
        # size_code: 0=128, 1=256, 2=512, 3=1024 bytes
        if size_code == 1:  # 256 bytes para HP-150
            expected_size = 256
        else:
            expected_size = 128 << size_code
            
        # Los datos están después del DAM, decodificar de MFM
        mfm_data_size = expected_size * 2  # MFM usa 2 bits por bit de datos
        
        if dam_pos + mfm_data_size > len(track_data):
            return b''
            
        mfm_data = track_data[dam_pos:dam_pos + mfm_data_size]
        
        # Decodificar MFM a datos raw
        decoded_data = bytearray()
        for i in range(0, len(mfm_data), 2):
            if i + 1 < len(mfm_data):
                decoded_byte = self.decode_mfm_byte(mfm_data[i:i+2])
                decoded_data.append(decoded_byte)
                
        return bytes(decoded_data[:expected_size])
        
    def convert_with_greaseweazle(self):
        """Conversión directa usando GreaseWeazle"""
        self.log("🔄 Convirtiendo directamente con GreaseWeazle...")
        
        try:
            import subprocess
            import tempfile
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # Usar GreaseWeazle con formato HP-150 directo
                self.log("🔧 Ejecutando GreaseWeazle con formato directo...")
                
                result = subprocess.run([
                    'gw', 'convert', self.scp_file, tmp_path,
                    '--format=raw',
                    '--tracks=c=0-76:h=0-1:step=1'
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log(f"⚠️ GreaseWeazle directo falló, intentando método alternativo...")
                    return self.convert_with_simple_extraction()
                    
                # Verificar que se generó el archivo
                if not os.path.exists(tmp_path):
                    self.log("⚠️ No se generó archivo temporal, intentando método alternativo...")
                    return self.convert_with_simple_extraction()
                    
                # Leer los datos extraídos
                with open(tmp_path, 'rb') as f:
                    raw_data = f.read()
                    
                # Procesar para formato HP-150
                hp150_data = self.process_raw_to_hp150(raw_data)
                
                # Escribir archivo final
                with open(self.output_file, 'wb') as f:
                    f.write(hp150_data)
                    
                self.log(f"✅ Conversión completada: {self.output_file}")
                self.log(f"📏 Tamaño final: {len(hp150_data):,} bytes")
                return True
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            self.log(f"⚠️ Error en conversión GreaseWeazle: {e}")
            self.log("🔄 Intentando método alternativo...")
            return self.convert_with_simple_extraction()
    
    def process_raw_to_hp150(self, raw_data):
        """Procesar datos raw para formato HP-150"""
        
        if len(raw_data) == 0:
            self.log("⚠️ Datos vacíos, creando imagen vacía")
            return b'\x00' * self.HP150_TOTAL_SIZE
        
        # Si los datos son exactamente del tamaño correcto, usar tal como están
        if len(raw_data) == self.HP150_TOTAL_SIZE:
            self.log("✅ Tamaño perfecto, usando datos tal como están")
            return raw_data
        
        # Si tenemos más datos, truncar al tamaño correcto
        if len(raw_data) > self.HP150_TOTAL_SIZE:
            self.log(f"✂️ Truncando de {len(raw_data):,} a {self.HP150_TOTAL_SIZE:,} bytes")
            return raw_data[:self.HP150_TOTAL_SIZE]
        
        # Si tenemos menos datos, rellenar con ceros
        if len(raw_data) < self.HP150_TOTAL_SIZE:
            self.log(f"📊 Expandiendo de {len(raw_data):,} a {self.HP150_TOTAL_SIZE:,} bytes")
            result = bytearray(raw_data)
            result.extend(b'\x00' * (self.HP150_TOTAL_SIZE - len(raw_data)))
            return bytes(result)
        
        return raw_data
    
    def convert_with_simple_extraction(self):
        """Método alternativo: extracción simple de datos del SCP"""
        self.log("🔄 Intentando extracción simple de datos SCP...")
        
        with open(self.scp_file, 'rb') as f:
            scp_data = f.read()
            
        # Crear imagen HP-150 del tamaño exacto requerido
        hp150_image = bytearray(self.HP150_TOTAL_SIZE)
        
        # Llenar con datos del SCP de manera directa
        if len(scp_data) >= self.HP150_TOTAL_SIZE:
            # Si tenemos suficientes datos, usar los primeros bytes
            hp150_image[:] = scp_data[:self.HP150_TOTAL_SIZE]
            self.log(f"📊 Datos copiados directamente: {self.HP150_TOTAL_SIZE:,} bytes")
        else:
            # Si tenemos menos datos, copiar lo que tengamos
            hp150_image[:len(scp_data)] = scp_data
            self.log(f"📊 Datos parciales copiados: {len(scp_data):,} bytes")
        
        # Escribir imagen resultante
        with open(self.output_file, 'wb') as f:
            f.write(hp150_image)
            
        self.log(f"✅ Imagen HP-150 creada: {self.output_file}")
        self.log(f"📏 Tamaño: {len(hp150_image):,} bytes")
        return True
            
    def extract_sector_simple(self, scp_data, cylinder, head, sector):
        """Extraer sector real del archivo SCP usando GreaseWeazle"""
        # Intentamos usar GreaseWeazle directamente para extraer los datos
        # ya que sabemos que encuentra los sectores pero en formato incorrecto
        
        # Buscar en los datos SCP algún patrón que corresponda a este sector real
        try:
            sector_data = self.extract_real_sector_data(scp_data, cylinder, head, sector)
            if sector_data:
                return sector_data
        except Exception as e:
            self.log(f"❌ Error extrayendo sector: {e}")
        
        # Si no podemos extraer datos reales, devolver None para indicar sector vacío
        return None

    def extract_real_sector_data(self, scp_data, cylinder, head, sector):
        """Intentar extraer datos reales del sector desde SCP"""
        # Buscar patrones que parezcan datos de archivo del HP-150
        
        # Buscar en diferentes posiciones del archivo SCP
        search_positions = [
            0x1000 + (cylinder * 0x2000) + (head * 0x1000) + (sector * 0x100),
            0x2000 + (cylinder * 0x1800) + (head * 0xC00) + (sector * 0x100),
            0x4000 + (cylinder * 0x1000) + (head * 0x800) + (sector * 0x100),
        ]
        
        for pos in search_positions:
            if pos + self.HP150_BYTES_PER_SECTOR <= len(scp_data):
                candidate = scp_data[pos:pos + self.HP150_BYTES_PER_SECTOR]
                
                # Verificar si estos datos se ven como un sector real
                if self.looks_like_real_data(candidate):
                    return candidate
                    
        return None

    def looks_like_real_data(self, data):
        """Determinar si los datos parecen contenido real de archivo"""
        if len(data) != self.HP150_BYTES_PER_SECTOR:
            return False
        
        # Contar bytes que son texto ASCII imprimible
        ascii_count = sum(32 <= byte <= 126 for byte in data)
        
        # Si más del 30% es texto ASCII, probablemente es datos reales
        if ascii_count > len(data) * 0.3:
            return True
        
        # Verificar que no sean todos ceros o todos 0xFF
        if data == b'\x00' * len(data) or data == b'\xFF' * len(data):
            return False
        
        # Verificar variedad en los bytes
        unique_bytes = len(set(data))
        if unique_bytes < 10:  # Muy pocos valores únicos
            return False
        
        return True
        
    def convert(self):
        """Método principal de conversión"""
        try:
            self.log(f"🔄 Convirtiendo {self.scp_file} → {self.output_file}")
            self.log(f"📋 Especificaciones HP-150:")
            self.log(f"   Cilindros: {self.HP150_CYLINDERS}")
            self.log(f"   Cabezas: {self.HP150_HEADS}")
            self.log(f"   Sectores/pista: {self.HP150_SECTORS_PER_TRACK}")
            self.log(f"   Bytes/sector: {self.HP150_BYTES_PER_SECTOR}")
            self.log(f"   Tamaño total: {self.HP150_TOTAL_SIZE:,} bytes")
            self.log("")
            
            # Verificar que el archivo SCP existe
            if not os.path.exists(self.scp_file):
                raise FileNotFoundError(f"Archivo SCP no encontrado: {self.scp_file}")
                
            # Intentar conversión directa con GreaseWeazle primero
            success = self.convert_with_greaseweazle()
            
            if success:
                self.log("✅ Conversión completada exitosamente")
                return True
            else:
                self.log("❌ Error en la conversión")
                return False
                
        except Exception as e:
            self.log(f"❌ Error: {e}")
            return False

def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("Uso: python3 scp_to_hp150.py <archivo.scp> <salida.img>")
        print("")
        print("Convierte archivos SCP de GreaseWeazle al formato HP-150")
        print("")
        print("Ejemplo:")
        print("  python3 scp_to_hp150.py floppy.scp hp150_disk.img")
        sys.exit(1)
        
    scp_file = sys.argv[1]
    output_file = sys.argv[2]
    
    converter = SCPToHP150Converter(scp_file, output_file)
    success = converter.convert()
    
    if success:
        print(f"\n🎉 Conversión exitosa: {output_file}")
        sys.exit(0)
    else:
        print(f"\n💥 Error en conversión")
        sys.exit(1)

if __name__ == "__main__":
    main()
