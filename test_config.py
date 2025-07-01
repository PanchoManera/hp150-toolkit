#!/usr/bin/env python3
"""
Test script para verificar el sistema de configuración de GreaseWeazle
"""

import sys
import os
from pathlib import Path

# Agregar src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_config_manager():
    """Probar ConfigManager"""
    print("🧪 Probando ConfigManager...")
    
    from gui.config_manager import ConfigManager
    
    config = ConfigManager()
    print(f"✅ ConfigManager creado")
    print(f"   Directorio de config: {config.config_dir}")
    print(f"   Archivo de config: {config.config_file}")
    
    # Verificar estado inicial
    print(f"   GreaseWeazle configurado: {config.is_greasewazle_configured()}")
    print(f"   Ruta actual: {config.get_greasewazle_path()}")
    
    # Buscar candidatos
    print(f"\n🔍 Buscando candidatos de GreaseWeazle...")
    candidates = config.find_greasewazle_candidates()
    print(f"   Encontrados {len(candidates)} candidatos:")
    
    for i, candidate in enumerate(candidates, 1):
        print(f"   {i}. {candidate['description']}")
        print(f"      Ruta: {candidate['path']}")
        print(f"      Prioridad: {candidate['priority']}")
        
        # Verificar si funciona
        is_valid = config.verify_greasewazle_path(candidate['path'])
        print(f"      Válido: {'✅' if is_valid else '❌'}")
        print()
    
    # Auto-detección
    auto_path = config.auto_detect_greasewazle()
    if auto_path:
        print(f"🎯 Auto-detección encontró: {auto_path}")
    else:
        print(f"❌ Auto-detección no encontró GreaseWeazle")
    
    return config

def test_gui():
    """Probar GUI con configuración"""
    print("\n🖥️ Iniciando GUI de prueba...")
    
    import tkinter as tk
    from gui.config_manager import ConfigManager
    from gui.greasewazle_config_dialog import show_greasewazle_config
    
    root = tk.Tk()
    root.title("Test GreaseWeazle Config")
    root.geometry("400x300")
    
    config_manager = ConfigManager()
    
    def show_config():
        result = show_greasewazle_config(root, config_manager)
        if result:
            status_label.config(text=f"Configurado: {result}")
        else:
            status_label.config(text="Configuración cancelada")
    
    def check_status():
        is_configured = config_manager.is_greasewazle_configured()
        path = config_manager.get_greasewazle_path()
        
        if is_configured:
            status_label.config(text=f"✅ Configurado: {path}")
        else:
            status_label.config(text="❌ No configurado")
    
    # Interfaz simple
    tk.Label(root, text="Test de Configuración GreaseWeazle", font=("", 16, "bold")).pack(pady=20)
    
    tk.Button(root, text="🔧 Configurar GreaseWeazle", command=show_config, width=25).pack(pady=10)
    tk.Button(root, text="🔍 Verificar Estado", command=check_status, width=25).pack(pady=5)
    
    status_label = tk.Label(root, text="", wraplength=350)
    status_label.pack(pady=20)
    
    # Verificar estado inicial
    check_status()
    
    print("💡 GUI iniciada. Prueba los botones para verificar el funcionamiento.")
    root.mainloop()

def main():
    print("🚀 Test del Sistema de Configuración HP-150 Toolkit")
    print("=" * 50)
    
    try:
        # Test 1: ConfigManager
        config = test_config_manager()
        
        # Test 2: GUI si se solicita
        if len(sys.argv) > 1 and sys.argv[1] == "--gui":
            test_gui()
        else:
            print("\n💡 Para probar la GUI, ejecuta: python test_config.py --gui")
        
        print("\n✅ Todos los tests completados")
        
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
