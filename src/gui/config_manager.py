#!/usr/bin/env python3
"""
HP-150 Toolkit - Configuration Manager
Maneja la configuración persistente de la aplicación
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

class ConfigManager:
    """Maneja la configuración de la aplicación"""
    
    def __init__(self):
        # Directorio de configuración específico del usuario
        if os.name == 'nt':  # Windows
            config_dir = Path.home() / "AppData" / "Local" / "HP150Toolkit"
        elif os.name == 'posix':  # macOS/Linux
            config_dir = Path.home() / ".config" / "hp150toolkit"
        else:
            config_dir = Path.home() / ".hp150toolkit"
            
        self.config_dir = config_dir
        self.config_file = config_dir / "settings.json"
        
        # Crear directorio si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración por defecto
        self.default_config = {
            "greasewazle_path": "",
            "greasewazle_configured": False,
            "last_used_paths": {
                "open_image": "",
                "save_file": "",
                "extract_dir": ""
            },
            "gui_settings": {
                "window_geometry": "",
                "theme": "default"
            }
        }
        
        self.config = self.load_config()
        
        # Re-validar configuración existente si es necesario
        self._revalidate_existing_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge con configuración por defecto para agregar nuevas opciones
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"⚠️ Error cargando configuración: {e}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Guarda la configuración a archivo"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
            return False
    
    def get_greasewazle_path(self) -> Optional[str]:
        """Obtiene la ruta configurada de GreaseWeazle"""
        return self.config.get("greasewazle_path", "") or None
    
    def set_greasewazle_path(self, path: str) -> bool:
        """Establece la ruta de GreaseWeazle"""
        self.config["greasewazle_path"] = path
        self.config["greasewazle_configured"] = bool(path and self.verify_greasewazle_path(path))
        return self.save_config()
    
    def is_greasewazle_configured(self) -> bool:
        """Verifica si GreaseWeazle está configurado"""
        return self.config.get("greasewazle_configured", False)
    
    def verify_greasewazle_path(self, path: str) -> bool:
        """Verifica si la ruta de GreaseWeazle es válida"""
        if not path:
            return False
            
        try:
            # Intentar ejecutar gw --help
            result = subprocess.run([path, "--help"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            # GreaseWeazle puede devolver código 1 con --help pero aún funcionar correctamente
            # Verificar que la salida contenga texto típico de GreaseWeazle
            output_text = (result.stdout + result.stderr).lower()
            return ("greaseweazle" in output_text or 
                   "usage:" in output_text or 
                   "actions:" in output_text or
                   "read" in output_text and "write" in output_text)
        except Exception:
            return False
    
    def find_greasewazle_candidates(self) -> List[Dict[str, str]]:
        """Busca posibles ubicaciones de GreaseWeazle"""
        candidates = []
        
        # 1. Verificar si está en PATH
        gw_in_path = shutil.which("gw")
        if gw_in_path:
            candidates.append({
                "path": gw_in_path,
                "description": "GreaseWeazle en PATH del sistema",
                "priority": 1
            })
        
        # 2. Ubicaciones comunes según el OS
        common_paths = []
        
        if os.name == 'nt':  # Windows
            common_paths = [
                "C:\\Program Files\\GreaseWeazle\\gw.exe",
                "C:\\Program Files (x86)\\GreaseWeazle\\gw.exe",
                str(Path.home() / "AppData" / "Local" / "Programs" / "GreaseWeazle" / "gw.exe"),
                "gw.exe"  # En caso de que esté en el directorio actual
            ]
        elif os.name == 'posix':
            if os.uname().sysname == 'Darwin':  # macOS
                common_paths = [
                    "/usr/local/bin/gw",
                    "/opt/homebrew/bin/gw",
                    "/usr/bin/gw",
                    str(Path.home() / "bin" / "gw"),
                    str(Path.home() / ".local" / "bin" / "gw"),
                    "/Applications/GreaseWeazle/gw"
                ]
            else:  # Linux
                common_paths = [
                    "/usr/local/bin/gw",
                    "/usr/bin/gw",
                    str(Path.home() / "bin" / "gw"),
                    str(Path.home() / ".local" / "bin" / "gw"),
                    "/opt/greasewazle/gw"
                ]
        
        # Verificar rutas comunes
        for path in common_paths:
            if Path(path).exists() and self.verify_greasewazle_path(path):
                candidates.append({
                    "path": path,
                    "description": f"Encontrado en: {path}",
                    "priority": 2
                })
        
        # Ordenar por prioridad
        candidates.sort(key=lambda x: x["priority"])
        
        return candidates
    
    def auto_detect_greasewazle(self) -> Optional[str]:
        """Intenta detectar automáticamente GreaseWeazle"""
        candidates = self.find_greasewazle_candidates()
        if candidates:
            # Retornar el candidato con mayor prioridad
            return candidates[0]["path"]
        return None
    
    def get_last_used_path(self, path_type: str) -> str:
        """Obtiene la última ruta usada para un tipo específico"""
        return self.config.get("last_used_paths", {}).get(path_type, "")
    
    def set_last_used_path(self, path_type: str, path: str):
        """Establece la última ruta usada para un tipo específico"""
        if "last_used_paths" not in self.config:
            self.config["last_used_paths"] = {}
        self.config["last_used_paths"][path_type] = path
        self.save_config()
    
    def get_window_geometry(self) -> str:
        """Obtiene la geometría guardada de la ventana"""
        return self.config.get("gui_settings", {}).get("window_geometry", "")
    
    def set_window_geometry(self, geometry: str):
        """Guarda la geometría de la ventana"""
        if "gui_settings" not in self.config:
            self.config["gui_settings"] = {}
        self.config["gui_settings"]["window_geometry"] = geometry
        self.save_config()
    
    def _revalidate_existing_config(self):
        """Re-validar configuración existente si es necesario"""
        # Si hay una ruta configurada pero marcada como no válida, re-verificar
        current_path = self.config.get("greasewazle_path", "")
        is_configured = self.config.get("greasewazle_configured", False)
        
        if current_path and not is_configured:
            # Re-verificar la ruta
            if self.verify_greasewazle_path(current_path):
                print(f"✅ Re-validando configuración: {current_path} ahora es válida")
                self.config["greasewazle_configured"] = True
                self.save_config()
