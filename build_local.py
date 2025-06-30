#!/usr/bin/env python3
"""
Script para construir binarios localmente usando PyInstaller
Útil para probar antes de hacer push al repositorio
"""

import sys
import subprocess
import platform
from pathlib import Path

def install_pyinstaller():
    """Instalar PyInstaller si no está disponible"""
    try:
        import PyInstaller
        print("✅ PyInstaller ya está instalado")
        return True
    except ImportError:
        print("📦 Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller instalado correctamente")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando PyInstaller: {e}")
            return False

def build_executable():
    """Construir el ejecutable usando PyInstaller"""
    
    if not install_pyinstaller():
        return False
    
    # Detectar plataforma
    system = platform.system()
    arch = platform.machine()
    
    print(f"🔨 Construyendo para {system} ({arch})...")
    
    # Comandos base de PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=HP150-Toolkit",
        "--add-data=src:src" if system != "Windows" else "--add-data=src;src",
        "--add-data=assets:assets" if system != "Windows" else "--add-data=assets;assets",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.simpledialog",
        "--collect-all=tkinter",
        "run_gui.py"
    ]
    
    # Configuraciones específicas por plataforma
    if system == "Darwin":  # macOS
        cmd.extend([
            "--windowed",
            f"--icon=assets/icon.icns"
        ])
        if arch == "arm64":
            print("🍎 Construyendo para Apple Silicon...")
        else:
            print("🍎 Construyendo para Intel Mac...")
            
    elif system == "Windows":
        cmd.extend([
            "--windowed",
            "--console",  # Mantener consola para debugging
            "--icon=assets/icon.ico"
        ])
        print("🪟 Construyendo para Windows...")
        
    elif system == "Linux":
        cmd.extend([
            "--icon=assets/icon.png"
        ])
        print("🐧 Construyendo para Linux...")
    
    # Ejecutar PyInstaller
    try:
        print(f"Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Construcción exitosa!")
            
            # Mostrar información del archivo generado
            if system == "Windows":
                exe_path = Path("dist/HP150-Toolkit.exe")
            else:
                exe_path = Path("dist/HP150-Toolkit")
            
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📁 Ejecutable creado: {exe_path}")
                print(f"📊 Tamaño: {size_mb:.2f} MB")
                
                # Instrucciones de uso
                print("\n🚀 Cómo ejecutar:")
                if system == "Windows":
                    print("   HP150-Toolkit.exe")
                    print("   HP150-Toolkit.exe --extended  (modo extendido)")
                else:
                    print("   ./HP150-Toolkit")
                    print("   ./HP150-Toolkit --extended  (modo extendido)")
                
                return True
            else:
                print("❌ No se encontró el ejecutable generado")
                return False
        else:
            print("❌ Error en la construcción:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando PyInstaller: {e}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller no encontrado. Asegúrate de que esté instalado.")
        return False

def main():
    """Función principal"""
    print("🏗️  HP-150 Toolkit - Constructor Local")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not Path("run_gui.py").exists():
        print("❌ Error: No se encontró run_gui.py")
        print("   Asegúrate de ejecutar este script desde la raíz del proyecto")
        return False
    
    # Verificar estructura de directorios
    if not Path("src").exists():
        print("❌ Error: No se encontró el directorio src/")
        return False
    
    if not Path("assets").exists():
        print("⚠️  Advertencia: No se encontró el directorio assets/")
        print("   Ejecutando create_icons.py...")
        try:
            subprocess.check_call([sys.executable, "create_icons.py"])
        except:
            print("❌ Error creando iconos. Continuando sin iconos...")
    
    # Construir el ejecutable
    success = build_executable()
    
    if success:
        print("\n✅ ¡Construcción completada exitosamente!")
        print("\n💡 Para crear binarios para múltiples plataformas:")
        print("   1. Haz push de tu código a GitHub")
        print("   2. Crea un tag: git tag v1.0.0 && git push origin v1.0.0")
        print("   3. Los binarios se generarán automáticamente en GitHub Actions")
    else:
        print("\n❌ La construcción falló")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
