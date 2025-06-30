# HP-150 Toolkit - Instrucciones de Build

Este documento explica cómo crear binarios ejecutables multiplataforma para HP-150 Toolkit.

## 🚀 Build Automático (Recomendado)

### Usando GitHub Actions

El método más sencillo es usar el workflow automático de GitHub Actions que crea binarios para todas las plataformas:

1. **Haz push de tu código a GitHub:**
   ```bash
   git add .
   git commit -m "Preparar release"
   git push origin main
   ```

2. **Crea un tag de versión:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. **¡Listo!** GitHub Actions construirá automáticamente los binarios para:
   - 🍎 **macOS Universal** (Intel + Apple Silicon)
   - 🪟 **Windows 64-bit**
   - 🪟 **Windows 32-bit**
   - 🐧 **Linux 64-bit**

4. **Descarga los binarios:**
   - Ve a la pestaña "Releases" de tu repositorio
   - O descarga desde "Actions" → "Artifacts"

### Ejecutar manualmente el workflow

También puedes ejecutar el workflow sin crear un tag:

1. Ve a la pestaña "Actions" en GitHub
2. Selecciona "Build HP-150 Toolkit Binaries"
3. Haz clic en "Run workflow"

## 🔨 Build Local

### Para testing rápido

Si quieres probar el build localmente antes de hacer push:

```bash
python3 build_local.py
```

Este script:
- Instala PyInstaller automáticamente si no está disponible
- Detecta tu plataforma automáticamente
- Crea el binario apropiado para tu sistema
- Te da instrucciones de cómo ejecutarlo

### Build manual con PyInstaller

Si prefieres control total sobre el proceso:

1. **Instala PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Para macOS:**
   ```bash
   pyinstaller --onefile --windowed \
     --name="HP150-Toolkit" \
     --icon="assets/icon.icns" \
     --target-arch=universal2 \
     --add-data="src:src" \
     --add-data="assets:assets" \
     --hidden-import=tkinter \
     --collect-all=tkinter \
     run_gui.py
   ```

3. **Para Windows:**
   ```bash
   pyinstaller --onefile --windowed --console ^
     --name="HP150-Toolkit" ^
     --icon="assets/icon.ico" ^
     --add-data="src;src" ^
     --add-data="assets;assets" ^
     --hidden-import=tkinter ^
     --collect-all=tkinter ^
     run_gui.py
   ```

4. **Para Linux:**
   ```bash
   pyinstaller --onefile \
     --name="HP150-Toolkit" \
     --icon="assets/icon.png" \
     --add-data="src:src" \
     --add-data="assets:assets" \
     --hidden-import=tkinter \
     --collect-all=tkinter \
     run_gui.py
   ```

## 📁 Estructura de Archivos

```
hp150_toolkit/
├── .github/
│   └── workflows/
│       └── build-binaries.yml    # Workflow de GitHub Actions
├── assets/
│   ├── icon.png                  # Icono para Linux
│   ├── icon.ico                  # Icono para Windows
│   └── icon.icns                 # Icono para macOS
├── src/                          # Código fuente
├── run_gui.py                    # Script principal
├── requirements.txt              # Dependencias
├── build_local.py               # Script de build local
├── create_icons.py              # Script para crear iconos
└── BUILD_INSTRUCTIONS.md        # Este archivo
```

## 🎯 Binarios Generados

Los binarios se crean en el directorio `dist/` con los siguientes nombres:

- **macOS**: `HP150-Toolkit` (binario universal)
- **Windows**: `HP150-Toolkit.exe`
- **Linux**: `HP150-Toolkit`

### Cómo ejecutar los binarios:

```bash
# Modo básico
./HP150-Toolkit                    # macOS/Linux
HP150-Toolkit.exe                  # Windows

# Modo extendido
./HP150-Toolkit --extended         # macOS/Linux
HP150-Toolkit.exe --extended       # Windows
```

## 🔧 Personalización

### Cambiar iconos

1. Reemplaza los archivos en `assets/`:
   - `icon.png` (Linux)
   - `icon.ico` (Windows)
   - `icon.icns` (macOS)

2. O ejecuta `python3 create_icons.py` para crear iconos básicos

### Agregar dependencias

1. Agrega las dependencias a `requirements.txt`
2. Si usas librerías nativas, agrega los imports necesarios en el workflow

### Modificar configuración de PyInstaller

Edita los comandos de PyInstaller en:
- `.github/workflows/build-binaries.yml` (builds automáticos)
- `build_local.py` (builds locales)

## 🐛 Troubleshooting

### Error: "tkinter not found"
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS con Homebrew
brew install python-tk
```

### Error: "PyInstaller not found"
```bash
pip install pyinstaller
```

### Error: "Icon file not found"
```bash
python3 create_icons.py
```

### El binario no se ejecuta
- Verifica que tienes permisos de ejecución: `chmod +x HP150-Toolkit`
- En macOS, podrías necesitar permitir la ejecución en "Preferencias del Sistema" → "Seguridad"

## 📝 Notas

- Los binarios de macOS son universales (funcionan en Intel y Apple Silicon)
- Los binarios de Windows incluyen tanto modo consola como ventana para mejor debugging
- Los binarios de Linux están compilados para x86_64
- El tamaño típico de los binarios es de 15-30 MB dependiendo de la plataforma

## 🎉 ¡Listo!

Con esta configuración, puedes crear fácilmente binarios para todas las plataformas principales. ¡Solo haz push y deja que GitHub Actions haga el trabajo pesado!
