#!/usr/bin/env python3
"""
Conversor entre formatos PC 720K estándar y HP-150
Permite convertir de formato de 720K estándar de PC a HP-150 y viceversa

Especificaciones:
- PC 720K: 80 cilindros, 2 cabezas, 9 sectores/pista, 512 bytes/sector = 737,280 bytes
- HP-150: 77 cilindros, 2 cabezas, 7 sectores/pista, 256 bytes/sector = 270,336 bytes
"""

import sys
import os
import struct
import argparse
from pathlib import Path

class PC720HP150Converter:
    """Conversor entre formatos PC 720K y HP-150"""
    
    # Especificaciones PC 720K
    PC720_CYLINDERS = 80
    PC720_HEADS = 2
    PC720_SECTORS_PER_TRACK = 9
    PC720_BYTES_PER_SECTOR = 512
    PC720_TOTAL_SIZE = PC720_CYLINDERS * PC720_HEADS * PC720_SECTORS_PER_TRACK * PC720_BYTES_PER_SECTOR  # 737,280 bytes
    
    # Especificaciones HP-150
    HP150_CYLINDERS = 77
    HP150_HEADS = 2
    HP150_SECTORS_PER_TRACK = 7
    HP150_BYTES_PER_SECTOR = 256
    HP150_TOTAL_SECTORS = 1056  # Especificación exacta del HP-150
    HP150_TOTAL_SIZE = HP150_TOTAL_SECTORS * HP150_BYTES_PER_SECTOR  # 270,336 bytes
    
    def __init__(self, input_file, output_file, direction):
        self.input_file = input_file
        self.output_file = output_file
        self.direction = direction  # 'pc_to_hp' o 'hp_to_pc'
        
    def log(self, message):
        """Log mensaje a stdout"""
        print(message)
        sys.stdout.flush()
        
    def pc720_to_hp150(self):
        """Convertir de PC 720K a HP-150"""
        self.log("🔄 Convirtiendo de PC 720K a HP-150...")
        
        # Verificar archivo de entrada
        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"Archivo no encontrado: {self.input_file}")
            
        file_size = os.path.getsize(self.input_file)
        self.log(f"📏 Tamaño del archivo PC: {file_size:,} bytes")
        
        if file_size != self.PC720_TOTAL_SIZE:
            self.log(f"⚠️  Advertencia: Tamaño esperado {self.PC720_TOTAL_SIZE:,} bytes")
        
        # Leer imagen PC
        with open(self.input_file, 'rb') as f:
            pc_data = f.read()
        
        # Crear imagen HP-150 vacía
        hp150_image = bytearray(self.HP150_TOTAL_SIZE)
        
        # Estrategia de conversión:
        # 1. Extraer el sector de boot (primer sector)
        # 2. Extraer la FAT y directorio root
        # 3. Extraer archivos de datos
        # 4. Reorganizar para formato HP-150
        
        sectors_converted = 0
        data_sectors_used = 0
        
        # Procesar sector por sector desde PC
        for pc_lba in range(min(self.PC720_TOTAL_SIZE // self.PC720_BYTES_PER_SECTOR, 1440)):  # Límite de sectores PC
            pc_offset = pc_lba * self.PC720_BYTES_PER_SECTOR
            
            if pc_offset + self.PC720_BYTES_PER_SECTOR > len(pc_data):
                break
                
            pc_sector = pc_data[pc_offset:pc_offset + self.PC720_BYTES_PER_SECTOR]
            
            # Verificar si el sector tiene datos útiles
            if not self.is_empty_sector(pc_sector):
                # Intentar mapear a HP-150
                hp150_lba = self.map_pc_to_hp150_sector(pc_lba, data_sectors_used)
                
                if hp150_lba < self.HP150_TOTAL_SECTORS:
                    # Dividir sector PC (512 bytes) en 2 sectores HP-150 (256 bytes cada uno)
                    for part in range(2):
                        part_lba = hp150_lba + part
                        if part_lba < self.HP150_TOTAL_SECTORS:
                            part_offset = part * self.HP150_BYTES_PER_SECTOR
                            part_data = pc_sector[part_offset:part_offset + self.HP150_BYTES_PER_SECTOR]
                            
                            hp150_offset = part_lba * self.HP150_BYTES_PER_SECTOR
                            hp150_image[hp150_offset:hp150_offset + self.HP150_BYTES_PER_SECTOR] = part_data
                            sectors_converted += 1
                    
                    data_sectors_used += 2  # Usamos 2 sectores HP por cada sector PC
        
        # Escribir imagen HP-150
        with open(self.output_file, 'wb') as f:
            f.write(hp150_image)
        
        self.log(f"✅ Conversión completada")
        self.log(f"📊 Sectores convertidos: {sectors_converted}")
        self.log(f"📁 Archivo HP-150 creado: {self.output_file}")
        self.log(f"📏 Tamaño: {len(hp150_image):,} bytes")
        
        return True
    
    def hp150_to_pc720(self):
        """Convertir de HP-150 a PC 720K"""
        self.log("🔄 Convirtiendo de HP-150 a PC 720K...")
        
        # Verificar archivo de entrada
        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"Archivo no encontrado: {self.input_file}")
            
        file_size = os.path.getsize(self.input_file)
        self.log(f"📏 Tamaño del archivo HP-150: {file_size:,} bytes")
        
        if file_size != self.HP150_TOTAL_SIZE:
            self.log(f"⚠️  Advertencia: Tamaño esperado {self.HP150_TOTAL_SIZE:,} bytes")
        
        # Leer imagen HP-150
        with open(self.input_file, 'rb') as f:
            hp150_data = f.read()
        
        # Verificar si la imagen HP-150 tiene un sistema de archivos válido
        has_hp150_filesystem = self.check_hp150_filesystem(hp150_data)
        
        if has_hp150_filesystem:
            self.log("📁 Detectado sistema de archivos HP-150, intentando preservar estructura")
            return self.hp150_to_pc720_with_filesystem(hp150_data)
        else:
            self.log("📄 No se detectó sistema de archivos HP-150, creando imagen PC vacía")
            return self.hp150_to_pc720_raw_copy(hp150_data)
    
    def check_hp150_filesystem(self, hp150_data):
        """Verificar si la imagen HP-150 contiene un sistema de archivos válido"""
        try:
            # Probar a cargar con HP150FAT para ver si tiene archivos
            import tempfile
            import sys
            import os
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(hp150_data)
                temp_hp150_path = temp_file.name
            
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
            from hp150_fat import HP150FAT
            
            try:
                hp150_fs = HP150FAT(temp_hp150_path)
                files = hp150_fs.list_files()
                # Si encuentra archivos válidos, tiene filesystem
                valid_files = [f for f in files if not f.is_volume and f.size > 0]
                os.unlink(temp_hp150_path)
                return len(valid_files) > 0
            except:
                os.unlink(temp_hp150_path)
                return False
                
        except:
            return False
    
    def hp150_to_pc720_with_filesystem(self, hp150_data):
        """Convertir HP-150 con sistema de archivos a PC 720K válido"""
        try:
            # Usar HP150FAT para leer los archivos
            import tempfile
            
            # Crear archivo temporal con los datos HP-150
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(hp150_data)
                temp_hp150_path = temp_file.name
            
            # Importar la clase HP150FAT
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
            from hp150_fat import HP150FAT
            
            # Leer archivos del HP-150
            try:
                hp150_fs = HP150FAT(temp_hp150_path)
                files = hp150_fs.list_files()
                self.log(f"📁 Encontrados {len(files)} archivos en HP-150")
                
                # Filtrar archivos válidos (no volumen, no directorio)
                valid_files = [f for f in files if not f.is_volume and not f.is_directory and f.size > 0]
                self.log(f"📝 Archivos válidos a convertir: {len(valid_files)}")
                
                for file_entry in valid_files:
                    self.log(f"  {file_entry.full_name} ({file_entry.size:,} bytes)")
                
                # Crear imagen PC 720K con FAT12 válida
                pc720_image = self.create_pc720_with_files(valid_files, hp150_fs)
                
                # Limpiar archivo temporal
                os.unlink(temp_hp150_path)
                
                # Escribir imagen PC 720K
                with open(self.output_file, 'wb') as f:
                    f.write(pc720_image)
                
                self.log(f"✅ Conversión con filesystem completada")
                self.log(f"📊 Archivos copiados: {len(valid_files)}")
                self.log(f"📁 Archivo PC 720K creado: {self.output_file}")
                self.log(f"📏 Tamaño: {len(pc720_image):,} bytes")
                
                return True
                
            except Exception as e:
                self.log(f"⚠️  Error leyendo HP-150 filesystem: {e}")
                # Fallback a copia raw
                os.unlink(temp_hp150_path)
                return self.hp150_to_pc720_raw_copy(hp150_data)
                
        except Exception as e:
            self.log(f"⚠️  Error en conversión con filesystem: {e}")
            # Fallback a copia raw
            return self.hp150_to_pc720_raw_copy(hp150_data)
    
    def hp150_to_pc720_raw_copy(self, hp150_data):
        """Copia simple de HP-150 a PC 720K (para datos sin filesystem)"""
        # Crear imagen PC 720K vacía
        pc720_image = bytearray(self.PC720_TOTAL_SIZE)
        
        # Crear FAT12 básica válida
        boot_sector = self.create_fat12_boot_sector()
        pc720_image[0:512] = boot_sector
        
        fat_data = self.create_fat12_tables()
        pc720_image[512:512+len(fat_data)] = fat_data
        pc720_image[512*10:512*10+len(fat_data)] = fat_data
        
        root_dir = self.create_root_directory()
        pc720_image[512*19:512*19+len(root_dir)] = root_dir
        
        # Copiar datos HP-150 al área de datos
        data_start = 512 * 33
        bytes_to_copy = min(len(hp150_data), self.PC720_TOTAL_SIZE - data_start)
        
        if bytes_to_copy > 0:
            pc720_image[data_start:data_start + bytes_to_copy] = hp150_data[:bytes_to_copy]
        
        # Escribir imagen PC 720K
        with open(self.output_file, 'wb') as f:
            f.write(pc720_image)
        
        self.log(f"✅ Conversión raw completada")
        self.log(f"📊 Bytes copiados: {bytes_to_copy:,}")
        self.log(f"📁 Archivo PC 720K creado: {self.output_file}")
        self.log(f"📏 Tamaño: {len(pc720_image):,} bytes")
        
        return True
    
    def create_fat12_boot_sector(self):
        """Crear sector de boot FAT12 válido para PC 720K"""
        boot_sector = bytearray(512)
        
        # Código de boot básico
        boot_sector[0:3] = b'\xEB\x3C\x90'  # JMP instruction
        
        # OEM name
        boot_sector[3:11] = b'MSDOS5.0'
        
        # BIOS Parameter Block (BPB)
        struct.pack_into('<H', boot_sector, 11, 512)      # Bytes per sector
        struct.pack_into('<B', boot_sector, 13, 2)        # Sectors per cluster
        struct.pack_into('<H', boot_sector, 14, 1)        # Reserved sectors
        struct.pack_into('<B', boot_sector, 16, 2)        # Number of FATs
        struct.pack_into('<H', boot_sector, 17, 112)      # Root directory entries
        struct.pack_into('<H', boot_sector, 19, 1440)     # Total sectors
        struct.pack_into('<B', boot_sector, 21, 0xF9)     # Media descriptor
        struct.pack_into('<H', boot_sector, 22, 9)        # Sectors per FAT
        struct.pack_into('<H', boot_sector, 24, 9)        # Sectors per track
        struct.pack_into('<H', boot_sector, 26, 2)        # Number of heads
        struct.pack_into('<L', boot_sector, 28, 0)        # Hidden sectors
        struct.pack_into('<L', boot_sector, 32, 0)        # Large sectors
        
        # Extended boot signature
        boot_sector[38] = 0x29  # Extended boot signature
        struct.pack_into('<L', boot_sector, 39, 0x12345678)  # Serial number
        boot_sector[43:54] = b'HP150CONV  '                  # Volume label
        boot_sector[54:62] = b'FAT12   '                     # File system type
        
        # Boot signature
        boot_sector[510:512] = b'\x55\xAA'
        
        return boot_sector
    
    def create_fat12_tables(self):
        """Crear tablas FAT12 para PC 720K"""
        # FAT12 para 720K: 9 sectores por FAT
        fat_size = 9 * 512
        fat_data = bytearray(fat_size)
        
        # Primeros tres bytes de la FAT
        fat_data[0] = 0xF9  # Media descriptor
        fat_data[1] = 0xFF
        fat_data[2] = 0xFF
        
        # Marcar los primeros clusters como ocupados por el sistema
        # Cluster 2 es el primer cluster de datos disponible
        # Vamos a marcar algunos clusters como usados para simular archivos
        fat_data[3] = 0xFF  # End of chain para cluster 2
        fat_data[4] = 0x0F
        
        return fat_data
    
    def create_root_directory(self):
        """Crear directorio root para PC 720K"""
        # Directorio root: 14 sectores (112 entradas de 32 bytes cada una)
        root_size = 14 * 512
        root_dir = bytearray(root_size)
        
        # Crear entrada de volumen
        volume_entry = bytearray(32)
        volume_entry[0:11] = b'HP150CONV  '  # Nombre del volumen
        volume_entry[11] = 0x08              # Atributo de volumen
        root_dir[0:32] = volume_entry
        
        # Crear entrada de archivo de ejemplo
        file_entry = bytearray(32)
        file_entry[0:8] = b'README  '       # Nombre del archivo
        file_entry[8:11] = b'TXT'           # Extensión
        file_entry[11] = 0x20               # Atributo de archivo
        struct.pack_into('<H', file_entry, 26, 2)  # Primer cluster
        struct.pack_into('<L', file_entry, 28, 512) # Tamaño del archivo
        root_dir[32:64] = file_entry
        
        return root_dir
    
    def is_empty_sector(self, sector_data):
        """Verificar si un sector está vacío (todo ceros o todo 0xFF)"""
        if not sector_data:
            return True
        return (sector_data == b'\x00' * len(sector_data) or 
                sector_data == b'\xFF' * len(sector_data))
    
    def map_pc_to_hp150_sector(self, pc_lba, hp150_sectors_used):
        """Mapear sector PC a sector HP-150"""
        # Mapeo simple: mantener orden pero ajustar por tamaño
        # Cada sector PC (512 bytes) se convierte en 2 sectores HP-150 (256 bytes cada uno)
        return hp150_sectors_used
    
    def create_pc720_with_files(self, valid_files, hp150_fs):
        """Crear imagen PC 720K con archivos extraídos de HP-150"""
        # Crear imagen PC 720K vacía
        pc720_image = bytearray(self.PC720_TOTAL_SIZE)
        
        # Crear sector de boot FAT12
        boot_sector = self.create_fat12_boot_sector()
        pc720_image[0:512] = boot_sector
        
        # Crear directorio root con archivos reales
        root_dir = self.create_root_directory_with_files(valid_files)
        pc720_image[512*19:512*19+len(root_dir)] = root_dir
        
        # Escribir archivos en el área de datos y crear FAT
        fat_entries = {}
        current_cluster = 2  # Primer cluster de datos disponible
        data_area_start = 512 * 33  # Sector 33 es donde empiezan los datos
        current_data_offset = data_area_start
        
        for i, file_entry in enumerate(valid_files):
            try:
                # Leer datos del archivo desde HP-150
                file_data = hp150_fs.read_file(file_entry.full_name)
                if not file_data:
                    continue
                
                # Calcular clusters necesarios (1024 bytes por cluster en 720K)
                cluster_size = 1024  # 2 sectores de 512 bytes
                clusters_needed = (len(file_data) + cluster_size - 1) // cluster_size
                
                # Verificar que no excedamos el espacio disponible
                if current_data_offset + (clusters_needed * cluster_size) > len(pc720_image):
                    self.log(f"⚠️  No hay espacio para {file_entry.full_name}, omitiendo")
                    continue
                
                # Guardar info del archivo para la FAT
                fat_entries[i] = {
                    'start_cluster': current_cluster,
                    'clusters': list(range(current_cluster, current_cluster + clusters_needed)),
                    'size': len(file_data)
                }
                
                # Escribir datos del archivo
                file_data_padded = file_data + b'\x00' * (clusters_needed * cluster_size - len(file_data))
                pc720_image[current_data_offset:current_data_offset + len(file_data_padded)] = file_data_padded
                
                self.log(f"  ✅ {file_entry.full_name}: cluster {current_cluster}, {clusters_needed} clusters")
                
                # Avanzar posiciones
                current_cluster += clusters_needed
                current_data_offset += clusters_needed * cluster_size
                
            except Exception as e:
                self.log(f"  ❌ Error leyendo {file_entry.full_name}: {e}")
                continue
        
        # Crear y escribir tabla FAT actualizada
        fat_data = self.create_fat12_tables_with_files(fat_entries)
        # Primera copia de FAT
        pc720_image[512:512+len(fat_data)] = fat_data
        # Segunda copia de FAT  
        pc720_image[512*10:512*10+len(fat_data)] = fat_data
        
        return pc720_image
    
    def create_root_directory_with_files(self, valid_files):
        """Crear directorio root con entradas de archivos reales"""
        # Directorio root: 14 sectores (112 entradas de 32 bytes cada una)
        root_size = 14 * 512
        root_dir = bytearray(root_size)
        
        # Crear entrada de volumen
        volume_entry = bytearray(32)
        volume_entry[0:11] = b'HP150GAMES '  # Nombre del volumen
        volume_entry[11] = 0x08              # Atributo de volumen
        root_dir[0:32] = volume_entry
        
        # Crear entradas para archivos reales
        current_cluster = 2
        entry_offset = 32
        
        for file_entry in valid_files:
            if entry_offset + 32 > len(root_dir):
                break  # No más espacio en el directorio
            
            # Formatear nombre de archivo para FAT (8.3)
            name_parts = file_entry.full_name.upper().split('.')
            if len(name_parts) == 2:
                fat_name = name_parts[0][:8].ljust(8)
                fat_ext = name_parts[1][:3].ljust(3)
            else:
                fat_name = file_entry.full_name[:8].ljust(8)
                fat_ext = '   '
            
            # Crear entrada de directorio
            dir_entry = bytearray(32)
            dir_entry[0:8] = fat_name.encode('ascii')
            dir_entry[8:11] = fat_ext.encode('ascii')
            dir_entry[11] = 0x20  # Atributo de archivo
            
            # Calcular clusters necesarios
            cluster_size = 1024
            clusters_needed = (file_entry.size + cluster_size - 1) // cluster_size
            
            struct.pack_into('<H', dir_entry, 26, current_cluster)  # Primer cluster
            struct.pack_into('<L', dir_entry, 28, file_entry.size)    # Tamaño
            
            root_dir[entry_offset:entry_offset + 32] = dir_entry
            
            current_cluster += clusters_needed
            entry_offset += 32
        
        return root_dir
    
    def create_fat12_tables_with_files(self, fat_entries):
        """Crear tablas FAT12 con entradas de archivos reales"""
        # FAT12 para 720K: 9 sectores por FAT
        fat_size = 9 * 512
        fat_data = bytearray(fat_size)
        
        # Inicializar FAT
        fat_table = [0] * (fat_size * 2 // 3)  # Aproximadamente el número de entradas FAT12
        
        # Primeras entradas especiales
        fat_table[0] = 0xFF9  # Media descriptor
        fat_table[1] = 0xFFF  # End of chain
        
        # Procesar archivos
        for file_info in fat_entries.values():
            clusters = file_info['clusters']
            for i, cluster in enumerate(clusters):
                if i < len(clusters) - 1:
                    # Apuntar al siguiente cluster
                    fat_table[cluster] = clusters[i + 1]
                else:
                    # Último cluster del archivo
                    fat_table[cluster] = 0xFFF
        
        # Convertir tabla a formato FAT12 (12 bits por entrada)
        for i in range(0, len(fat_table), 2):
            if i + 1 < len(fat_table):
                val1 = fat_table[i] & 0xFFF
                val2 = fat_table[i + 1] & 0xFFF
                
                # Combinar dos entradas de 12 bits en 3 bytes
                combined = val1 | (val2 << 12)
                byte_offset = (i * 3) // 2
                
                if byte_offset + 2 < len(fat_data):
                    fat_data[byte_offset] = combined & 0xFF
                    fat_data[byte_offset + 1] = (combined >> 8) & 0xFF
                    fat_data[byte_offset + 2] = (combined >> 16) & 0xFF
        
        return fat_data
    
    def convert(self):
        """Método principal de conversión"""
        try:
            self.log(f"🔄 Conversor PC 720K ↔ HP-150")
            self.log(f"📂 Entrada: {self.input_file}")
            self.log(f"📁 Salida: {self.output_file}")
            self.log(f"🔄 Dirección: {self.direction}")
            self.log("")
            
            self.log("📋 Especificaciones:")
            self.log(f"   PC 720K: {self.PC720_CYLINDERS}c×{self.PC720_HEADS}h×{self.PC720_SECTORS_PER_TRACK}s×{self.PC720_BYTES_PER_SECTOR}b = {self.PC720_TOTAL_SIZE:,} bytes")
            self.log(f"   HP-150: {self.HP150_CYLINDERS}c×{self.HP150_HEADS}h×{self.HP150_SECTORS_PER_TRACK}s×{self.HP150_BYTES_PER_SECTOR}b = {self.HP150_TOTAL_SIZE:,} bytes")
            self.log("")
            
            if self.direction == 'pc_to_hp':
                return self.pc720_to_hp150()
            elif self.direction == 'hp_to_pc':
                return self.hp150_to_pc720()
            else:
                raise ValueError(f"Dirección inválida: {self.direction}")
                
        except Exception as e:
            self.log(f"❌ Error: {e}")
            return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Conversor entre formatos PC 720K estándar y HP-150",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Convertir de PC 720K a HP-150
  python3 pc720_hp150_converter.py --pc-to-hp disk.img hp150_disk.img
  
  # Convertir de HP-150 a PC 720K  
  python3 pc720_hp150_converter.py --hp-to-pc hp150_disk.img disk.img
  
  # Usando formato corto
  python3 pc720_hp150_converter.py -p disk.img hp150_disk.img
  python3 pc720_hp150_converter.py -H hp150_disk.img disk.img

Especificaciones:
  PC 720K: 80 cilindros × 2 cabezas × 9 sectores × 512 bytes = 737,280 bytes
  HP-150:  77 cilindros × 2 cabezas × 7 sectores × 256 bytes = 270,336 bytes
        """
    )
    
    # Grupo de argumentos mutuamente exclusivos para la dirección
    direction_group = parser.add_mutually_exclusive_group(required=True)
    direction_group.add_argument('--pc-to-hp', '-p', action='store_true',
                                help='Convertir de PC 720K a HP-150')
    direction_group.add_argument('--hp-to-pc', '-H', action='store_true',
                                help='Convertir de HP-150 a PC 720K')
    
    parser.add_argument('input_file', help='Archivo de entrada')
    parser.add_argument('output_file', help='Archivo de salida')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    # Determinar dirección de conversión
    if args.pc_to_hp:
        direction = 'pc_to_hp'
        direction_desc = "PC 720K → HP-150"
    else:
        direction = 'hp_to_pc' 
        direction_desc = "HP-150 → PC 720K"
    
    print("=" * 60)
    print("🔄 CONVERSOR PC 720K ↔ HP-150")
    print("=" * 60)
    print(f"Conversión: {direction_desc}")
    print()
    
    # Crear conversor
    converter = PC720HP150Converter(args.input_file, args.output_file, direction)
    success = converter.convert()
    
    print()
    if success:
        print("🎉 ¡Conversión completada exitosamente!")
        print(f"📁 Archivo de salida: {args.output_file}")
        sys.exit(0)
    else:
        print("💥 Error en la conversión")
        sys.exit(1)

if __name__ == "__main__":
    main()
