#!/usr/bin/env python3
"""
HP-150 Toolkit - Ejecutor de GUI
Script principal para iniciar la interfaz gráfica desde la raíz del proyecto
"""

import sys
import os
from pathlib import Path

# Agregar src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Función principal para ejecutar la GUI"""
    
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        print("Error: tkinter no está disponible. En algunas distribuciones de Linux:")
        print("sudo apt-get install python3-tk")
        print("O en macOS con Homebrew:")
        print("brew install python-tk")
        sys.exit(1)
    
    # Verificar si se debe usar la GUI extendida o básica
    if len(sys.argv) > 1 and sys.argv[1] == "--extended":
        # GUI extendida con más funcionalidades
        from src.gui.hp150_gui_extended_museum import HP150ImageManagerExtendedMuseum
        
        root = tk.Tk()
        app = HP150ImageManagerExtendedMuseum(root)
        print("🚀 Iniciando HP-150 GUI (Modo Experimental - Con Catálogo del Museo)...")
        
    else:
        # GUI básica
        from src.gui.hp150_gui import HP150ImageManager
        
        root = tk.Tk()
        app = HP150ImageManager(root)
        print("🚀 Iniciando HP-150 GUI (Modo Básico)...")
    
    # Mostrar ayuda inicial
    print("""
┌─────────────────────────────────────────────────────────────┐
│                      HP-150 GUI TOOLKIT                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📂 Para empezar:                                           │
│    1. Usa 'Abrir Imagen' para cargar un archivo .img       │
│    2. Explora los archivos en la lista                     │
│    3. Usa los botones para extraer/editar archivos         │
│                                                             │
│ 💡 Modos disponibles:                                      │
│    • Básico: python3 run_gui.py                           │
│    • Extendido: python3 run_gui.py --extended             │
│    • Experimental: python3 run_gui_experimental.py --extended │
│                                                             │
│ 🎯 Archivos convertidos disponibles:                      │
│    • Revisa la carpeta HP150_CONVERTED/                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
    """)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error ejecutando la GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
