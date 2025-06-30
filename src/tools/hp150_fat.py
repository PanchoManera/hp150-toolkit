#!/usr/bin/env python3
"""
HP-150 FAT Filesystem Handler
Maneja el formato FAT personalizado del HP-150 con sectores de 256 bytes
"""

import struct
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class FileEntry:
    """Representa una entrada de archivo en el directorio"""
    name: str
    ext: str
    attr: int
    cluster: int
    size: int
    offset: int  # Offset en la imagen
    
    @property
    def full_name(self) -> str:
        if self.ext:
            return f"{self.name}.{self.ext}"
        return self.name
    
    @property 
    def is_directory(self) -> bool:
        return bool(self.attr & 0x10)
    
    @property
    def is_volume(self) -> bool:
        return bool(self.attr & 0x08)

class HP150FAT:
    """Maneja el sistema de archivos FAT del HP-150"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.file_handle = open(image_path, 'r+b')
        self.boot_sector = self.file_handle.read(512)
        
        # Parsear el sector de boot para obtener los parámetros del disco
        self.parse_boot_sector()
        
        # Calcular offsets basados en los parámetros leídos
        self.fat_start = self.reserved_sectors * self.bytes_per_sector
        self.fat_size = self.fat_sectors * self.bytes_per_sector
        
        self.root_dir_start = self.fat_start + (self.fat_copies * self.fat_size)
        self.root_dir_size = self.root_entries * 32
        self.data_start = self.root_dir_start + self.root_dir_size
        
        self.cluster_size = self.sectors_per_cluster * self.bytes_per_sector
        
        # Calcular sectores máximos basado en el tamaño del archivo
        file_size = os.path.getsize(image_path)
        self.max_sectors = file_size // self.bytes_per_sector
        
        # Cache
        self._files = {}
        self._fat_table = None
        self._dirty = False
        
        self._load_fat_table()
        self._load_directory()

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
            # Si falla el parseo, asumimos un formato HP-150 por defecto
            # Esto mantiene la compatibilidad con imágenes que no tienen un BPB claro
            print(f"[WARN] No se pudo parsear BPB, asumiendo formato HP-150: {e}")
            self.bytes_per_sector = 256
            self.sectors_per_cluster = 4
            self.reserved_sectors = 2
            self.fat_copies = 2
            self.fat_sectors = 3
            self.root_entries = 128
    
    def _load_fat_table(self):
        """Carga la tabla FAT"""
        with open(self.image_path, 'rb') as f:
            f.seek(self.fat_start)
            fat_data = f.read(self.fat_size)
            
        # La FAT en HP-150 es de 12 bits como FAT12 estándar
        self._fat_table = []
        for i in range(0, len(fat_data), 3):
            if i + 2 < len(fat_data):
                # Cada 3 bytes contienen 2 entradas de 12 bits
                val = struct.unpack('<I', fat_data[i:i+3] + b'\x00')[0]
                entry1 = val & 0xFFF
                entry2 = (val >> 12) & 0xFFF
                self._fat_table.extend([entry1, entry2])
    
    def _load_directory(self):
        """Carga el directorio raíz"""
        with open(self.image_path, 'rb') as f:
            f.seek(self.root_dir_start)
            root_data = f.read(self.root_dir_size)
        
        self._files = {}
        for i in range(0, len(root_data), 32):
            entry_data = root_data[i:i+32]
            if len(entry_data) < 32:
                break
            
            first_byte = entry_data[0]
            if first_byte == 0x00:  # Fin del directorio
                break
            if first_byte == 0xE5:  # Archivo borrado
                continue
            if first_byte == 0x2E:  # . o ..
                continue
            
            try:
                name = entry_data[0:8].decode('ascii', errors='ignore').rstrip()
                ext = entry_data[8:11].decode('ascii', errors='ignore').rstrip()
                attr = entry_data[11]
                cluster = struct.unpack('<H', entry_data[26:28])[0]
                size = struct.unpack('<L', entry_data[28:32])[0]
                
                if name and not name.startswith('\x00'):
                    entry = FileEntry(
                        name=name,
                        ext=ext,
                        attr=attr,
                        cluster=cluster,
                        size=size,
                        offset=self.root_dir_start + i
                    )
                    self._files[entry.full_name] = entry
            except:
                continue
    
    def list_files(self) -> List[FileEntry]:
        """Lista todos los archivos"""
        return list(self._files.values())
    
    def get_file(self, filename: str) -> Optional[FileEntry]:
        """Obtiene información de un archivo específico"""
        return self._files.get(filename)
    
    def read_file(self, filename: str) -> bytes:
        """Lee el contenido completo de un archivo"""
        entry = self.get_file(filename)
        if not entry:
            raise FileNotFoundError(f"File {filename} not found")
        
        if entry.size == 0:
            return b''
        
        # Seguir la cadena de clusters
        data = b''
        current_cluster = entry.cluster
        remaining_size = entry.size
        
        with open(self.image_path, 'rb') as f:
            while current_cluster < 0xFF0 and remaining_size > 0:
                # Calcular offset del cluster
                cluster_offset = self.data_start + (current_cluster - 2) * self.cluster_size
                f.seek(cluster_offset)
                
                # Leer datos del cluster
                to_read = min(self.cluster_size, remaining_size)
                cluster_data = f.read(to_read)
                data += cluster_data
                remaining_size -= len(cluster_data)
                
                # Siguiente cluster en la FAT
                if current_cluster < len(self._fat_table):
                    current_cluster = self._fat_table[current_cluster]
                else:
                    break
        
        return data[:entry.size]
    
    def write_file(self, filename: str, data: bytes, attr: int = 0x20) -> bool:
        """Escribe un archivo (simplificado - solo archivos que ya existen)"""
        entry = self.get_file(filename)
        if not entry:
            return self._create_new_file(filename, data, attr)
        
        if len(data) > entry.size:
            # Por simplicidad, no soportamos expandir archivos por ahora
            raise ValueError(f"File too large. Max size: {entry.size}, provided: {len(data)}")
        
        # Escribir datos en clusters existentes
        current_cluster = entry.cluster
        remaining_data = data
        
        with open(self.image_path, 'r+b') as f:
            while current_cluster < 0xFF0 and remaining_data:
                cluster_offset = self.data_start + (current_cluster - 2) * self.cluster_size
                f.seek(cluster_offset)
                
                to_write = min(self.cluster_size, len(remaining_data))
                f.write(remaining_data[:to_write])
                remaining_data = remaining_data[to_write:]
                
                if current_cluster < len(self._fat_table):
                    current_cluster = self._fat_table[current_cluster]
                else:
                    break
            
            # Actualizar tamaño en el directorio
            f.seek(entry.offset + 28)
            f.write(struct.pack('<L', len(data)))
        
        # Actualizar cache
        entry.size = len(data)
        self._dirty = True
        return True
    
    def get_disk_info(self) -> Dict[str, int]:
        """Obtener información del disco"""
        total_size = self.max_sectors * self.bytes_per_sector
        
        # Calcular espacio usado contando archivos
        used_space = 0
        for file_entry in self._files.values():
            if not file_entry.is_volume:
                # Calcular espacio en clusters
                clusters_needed = (file_entry.size + self.cluster_size - 1) // self.cluster_size
                used_space += clusters_needed * self.cluster_size
        
        # Agregar espacio del sistema (FAT + directorio)
        system_space = self.fat_size + self.root_dir_size + (self.reserved_sectors * self.bytes_per_sector)
        used_space += system_space
        
        free_space = max(0, total_size - used_space)
        
        return {
            'total_size': total_size,
            'used_space': used_space,
            'free_space': free_space,
            'system_space': system_space
        }
    
    def _create_new_file(self, filename: str, data: bytes, attr: int) -> bool:
        """Crea un nuevo archivo completo"""
        
        # Validar nombre de archivo
        if not self._validate_filename(filename):
            raise ValueError(f"Invalid filename format: {filename}")
        
        # Verificar si el archivo ya existe
        if filename.upper() in self._files:
            raise ValueError(f"File {filename} already exists")
        
        # Calcular clusters necesarios
        clusters_needed = (len(data) + self.cluster_size - 1) // self.cluster_size if data else 1
        
        # Encontrar clusters libres
        free_clusters = self._find_free_clusters(clusters_needed)
        if len(free_clusters) < clusters_needed:
            raise ValueError(f"Not enough free space. Need {clusters_needed} clusters, found {len(free_clusters)}")
        
        # Encontrar entrada libre en el directorio
        dir_entry_offset = self._find_free_directory_entry()
        if dir_entry_offset is None:
            raise ValueError("No free directory entries available")
        
        # Separar nombre y extensión
        if '.' in filename:
            name_part, ext_part = filename.rsplit('.', 1)
        else:
            name_part, ext_part = filename, ''
        
        # Formatear para FAT (8.3)
        fat_name = name_part.upper().ljust(8)[:8]
        fat_ext = ext_part.upper().ljust(3)[:3]
        
        # Escribir datos en clusters
        with open(self.image_path, 'r+b') as f:
            remaining_data = data
            
            for i, cluster in enumerate(free_clusters[:clusters_needed]):
                # Calcular offset del cluster
                cluster_offset = self.data_start + (cluster - 2) * self.cluster_size
                f.seek(cluster_offset)
                
                # Escribir datos del cluster
                to_write = min(self.cluster_size, len(remaining_data))
                cluster_data = remaining_data[:to_write]
                
                # Rellenar con ceros si es necesario
                if len(cluster_data) < self.cluster_size:
                    cluster_data += b'\x00' * (self.cluster_size - len(cluster_data))
                
                f.write(cluster_data)
                remaining_data = remaining_data[to_write:]
                
                # Actualizar FAT
                if i < len(free_clusters) - 1:
                    # Apuntar al siguiente cluster
                    self._fat_table[cluster] = free_clusters[i + 1]
                else:
                    # Último cluster
                    self._fat_table[cluster] = 0xFFF
            
            # Escribir entrada del directorio
            f.seek(dir_entry_offset)
            
            # Crear entrada de directorio (32 bytes)
            dir_entry = bytearray(32)
            dir_entry[0:8] = fat_name.encode('ascii')  # Nombre
            dir_entry[8:11] = fat_ext.encode('ascii')  # Extensión
            dir_entry[11] = attr  # Atributos
            dir_entry[12:22] = b'\x00' * 10  # Reservado
            
            # Timestamp actual (simplificado)
            import time
            now = time.time()
            dos_time = self._unix_to_dos_time(now)
            dir_entry[22:24] = struct.pack('<H', dos_time[0])  # Tiempo
            dir_entry[24:26] = struct.pack('<H', dos_time[1])  # Fecha
            
            dir_entry[26:28] = struct.pack('<H', free_clusters[0])  # Cluster inicial
            dir_entry[28:32] = struct.pack('<L', len(data))  # Tamaño
            
            f.write(dir_entry)
        
        # Escribir FAT actualizada
        self._write_fat_table()
        
        # Actualizar cache
        entry = FileEntry(
            name=name_part.upper(),
            ext=ext_part.upper(),
            attr=attr,
            cluster=free_clusters[0],
            size=len(data),
            offset=dir_entry_offset
        )
        self._files[filename.upper()] = entry
        self._dirty = True
        
        return True
    
    def get_free_space(self) -> int:
        """Calcula el espacio libre aproximado"""
        used_clusters = set()
        for entry in self._files.values():
            if entry.cluster > 0:
                current = entry.cluster
                while current < 0xFF0 and current < len(self._fat_table):
                    used_clusters.add(current)
                    current = self._fat_table[current]
        
        total_clusters = (self.max_sectors * self.bytes_per_sector - self.data_start) // self.cluster_size
        free_clusters = total_clusters - len(used_clusters)
        return max(0, free_clusters * self.cluster_size)
    
    
    def _validate_filename(self, filename: str) -> bool:
        """Valida formato de nombre 8.3"""
        if not filename or len(filename) > 12:  # 8 + 1 + 3
            return False
        
        # Caracteres inválidos
        invalid_chars = '<>:"/\\|?*'
        if any(c in filename for c in invalid_chars):
            return False
        
        if '.' in filename:
            parts = filename.split('.')
            if len(parts) != 2:
                return False
            name_part, ext_part = parts
            return len(name_part) <= 8 and len(ext_part) <= 3 and name_part and ext_part
        else:
            return len(filename) <= 8
    
    def _find_free_clusters(self, count: int) -> List[int]:
        """Encuentra clusters libres"""
        free_clusters = []
        
        # Obtener clusters usados
        used_clusters = set()
        for entry in self._files.values():
            if entry.cluster > 0:
                current = entry.cluster
                while current < 0xFF0 and current < len(self._fat_table):
                    used_clusters.add(current)
                    if current < len(self._fat_table):
                        current = self._fat_table[current]
                    else:
                        break
        
        # Buscar clusters libres (empezando desde 2)
        max_cluster = min(len(self._fat_table), (self.max_sectors * self.bytes_per_sector - self.data_start) // self.cluster_size + 2)
        
        for cluster in range(2, max_cluster):
            if cluster not in used_clusters and self._fat_table[cluster] == 0:
                free_clusters.append(cluster)
                if len(free_clusters) >= count:
                    break
        
        return free_clusters
    
    def _find_free_directory_entry(self) -> Optional[int]:
        """Encuentra una entrada libre en el directorio"""
        with open(self.image_path, 'rb') as f:
            f.seek(self.root_dir_start)
            
            for i in range(self.root_entries):
                f.seek(self.root_dir_start + i * 32)
                first_byte = f.read(1)
                
                if not first_byte or first_byte[0] == 0x00 or first_byte[0] == 0xE5:
                    return self.root_dir_start + i * 32
        
        return None
    
    def _write_fat_table(self):
        """Escribe la tabla FAT actualizada al disco"""
        # Convertir FAT de vuelta a formato de 12 bits
        fat_data = bytearray()
        
        for i in range(0, len(self._fat_table), 2):
            entry1 = self._fat_table[i] if i < len(self._fat_table) else 0
            entry2 = self._fat_table[i + 1] if i + 1 < len(self._fat_table) else 0
            
            # Combinar dos entradas de 12 bits en 3 bytes
            val = entry1 | (entry2 << 12)
            fat_data.extend(struct.pack('<I', val)[:3])
        
        # Escribir al disco
        with open(self.image_path, 'r+b') as f:
            f.seek(self.fat_start)
            f.write(fat_data[:self.fat_size])
    
    def _unix_to_dos_time(self, unix_time: float) -> Tuple[int, int]:
        """Convierte timestamp Unix a formato DOS"""
        import datetime
        dt = datetime.datetime.fromtimestamp(unix_time)
        
        # Formato DOS time: HHHHHMMMMMMSSSSS (horas, minutos, segundos/2)
        dos_time = ((dt.hour & 0x1F) << 11) | ((dt.minute & 0x3F) << 5) | ((dt.second // 2) & 0x1F)
        
        # Formato DOS date: YYYYYYYMMMMDDDDD (año-1980, mes, día)
        dos_date = (((dt.year - 1980) & 0x7F) << 9) | ((dt.month & 0x0F) << 5) | (dt.day & 0x1F)
        
        return dos_time, dos_date
    
    def delete_file(self, filename: str) -> bool:
        """Elimina un archivo del sistema de archivos"""
        entry = self.get_file(filename)
        if not entry:
            return False
        
        # Liberar clusters en la FAT
        current_cluster = entry.cluster
        while current_cluster < 0xFF0 and current_cluster < len(self._fat_table):
            next_cluster = self._fat_table[current_cluster]
            self._fat_table[current_cluster] = 0  # Marcar como libre
            current_cluster = next_cluster
        
        # Marcar entrada del directorio como eliminada
        with open(self.image_path, 'r+b') as f:
            f.seek(entry.offset)
            f.write(b'\xE5')  # Marcar como eliminado
        
        # Escribir FAT actualizada
        self._write_fat_table()
        
        # Actualizar cache
        del self._files[filename]
        self._dirty = True
        
        return True
