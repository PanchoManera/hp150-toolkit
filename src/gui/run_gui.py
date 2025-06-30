#!/usr/bin/env python3
"""
HP-150 Toolkit - Ejecutor de GUI
Script para iniciar fácilmente la interfaz gráfica
"""

import sys
import tkinter as tk
from pathlib import Path

# Añadir directorios necesarios al path
project_root = Path(__file__).parent.parent.parent  # Subir dos niveles desde src/gui/
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

def main():
    """Función principal para ejecutar la GUI"""
    
    # Verificar si se debe usar la GUI extendida o básica
    if len(sys.argv) > 1 and sys.argv[1] == "--extended":
        # GUI extendida con más funcionalidades
        from hp150_gui_extended import HP150ImageManagerExtended
        
        root = tk.Tk()
        app = HP150ImageManagerExtended(root)
        print("🚀 Iniciando HP-150 GUI (Modo Extendido)...")
        
    else:
        # GUI básica
        from hp150_gui import HP150ImageManager
        
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
│                                                             │
│ 🎯 Archivos de ejemplo:                                    │
│    • games_correct.img (imagen de prueba)                 │
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
