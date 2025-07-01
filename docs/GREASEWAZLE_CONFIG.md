# Sistema de Configuración de GreaseWeazle

## 📝 Descripción

El HP-150 Toolkit ahora incluye un sistema de configuración persistente para GreaseWeazle que resuelve los problemas de PATH en aplicaciones empaquetadas (bundles) y proporciona una interfaz amigable para configurar la ubicación del ejecutable `gw`.

## 🎯 Problema Resuelto

**Antes**: 
- Error `[Errno 2] No such file or directory: 'gw'` en bundles compilados
- El comando `gw` no estaba disponible en el PATH de la aplicación empaquetada
- No había forma de configurar la ruta de GreaseWeazle

**Ahora**:
- ✅ Sistema de configuración persistente
- ✅ Auto-detección de GreaseWeazle en ubicaciones comunes
- ✅ Interfaz gráfica para configuración manual
- ✅ Verificación automática antes de operaciones de lectura/escritura

## 🏗️ Arquitectura

### Componentes

1. **ConfigManager** (`src/gui/config_manager.py`)
   - Maneja la configuración persistente
   - Auto-detección de GreaseWeazle
   - Verificación de rutas
   - Almacenamiento en JSON

2. **GreaseWazleConfigDialog** (`src/gui/greasewazle_config_dialog.py`)
   - Interfaz gráfica de configuración
   - Lista de candidatos auto-detectados
   - Configuración manual con explorador de archivos
   - Pruebas en tiempo real

3. **Integración en GUI** (en `hp150_gui_extended.py` y `hp150_gui.py`)
   - Verificación automática antes de operaciones
   - Botón de configuración en la interfaz
   - Uso de rutas configuradas en lugar de `"gw"` hardcodeado

### Ubicación de Configuración

La configuración se guarda en:

- **macOS/Linux**: `~/.config/hp150toolkit/settings.json`
- **Windows**: `%LOCALAPPDATA%/HP150Toolkit/settings.json`

Estructura del archivo de configuración:
```json
{
  "greasewazle_path": "/opt/homebrew/bin/gw",
  "greasewazle_configured": true,
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
```

## 🔍 Auto-detección

El sistema busca GreaseWeazle en estas ubicaciones:

### 1. PATH del Sistema
- Usa `shutil.which("gw")` para verificar si está en PATH

### 2. Ubicaciones Comunes por SO

**macOS**:
- `/usr/local/bin/gw`
- `/opt/homebrew/bin/gw` (Apple Silicon)
- `/usr/bin/gw`
- `~/bin/gw`
- `~/.local/bin/gw`
- `/Applications/GreaseWeazle/gw`

**Windows**:
- `C:\Program Files\GreaseWeazle\gw.exe`
- `C:\Program Files (x86)\GreaseWeazle\gw.exe`
- `%LOCALAPPDATA%\Programs\GreaseWeazle\gw.exe`

**Linux**:
- `/usr/local/bin/gw`
- `/usr/bin/gw`
- `~/bin/gw`
- `~/.local/bin/gw`
- `/opt/greasewazle/gw`

## 🎮 Uso

### Configuración Inicial

1. **Automática**: Al intentar leer/escribir un floppy por primera vez, se mostrará el diálogo de configuración si GreaseWeazle no está configurado.

2. **Manual**: Hacer clic en el botón "⚙️ Configurar GW" en la sección Floppy.

### Flujo de Configuración

1. **Auto-detección**: El sistema busca automáticamente GreaseWeazle
2. **Selección**: El usuario puede elegir de las opciones encontradas
3. **Configuración Manual**: O especificar una ruta personalizada
4. **Verificación**: Cada opción se puede probar con el botón 🧪
5. **Guardado**: La configuración se guarda permanentemente

### Verificación Antes de Operaciones

Antes de cualquier operación de lectura o escritura:

```python
if not self.config_manager.is_greasewazle_configured():
    result = messagebox.askyesno(
        "GreaseWeazle no configurado",
        "GreaseWeazle no está configurado. ¿Deseas configurarlo ahora?"
    )
    if result:
        chosen_path = show_greasewazle_config(self.root, self.config_manager)
        if not chosen_path:
            return
    else:
        return
```

## 🧪 Testing

Para probar el sistema de configuración:

```bash
# Test básico del ConfigManager
python test_config.py

# Test con interfaz gráfica
python test_config.py --gui
```

## 📁 Archivos Modificados

### Nuevos Archivos
- `src/gui/config_manager.py` - Gestor de configuración
- `src/gui/greasewazle_config_dialog.py` - Diálogo de configuración
- `test_config.py` - Script de pruebas
- `docs/GREASEWAZLE_CONFIG.md` - Esta documentación

### Archivos Modificados
- `src/gui/hp150_gui_extended.py`:
  - Integración completa del sistema de configuración
  - Reemplazo de `"gw"` por rutas configuradas
  - Botón de configuración en la GUI
  - Verificación antes de operaciones

- `src/gui/hp150_gui.py`:
  - Integración básica del sistema de configuración
  - Importaciones necesarias

- `run_gui.py`:
  - Corrección de imports para consistencia

## 🔧 Detalles Técnicos

### ConfigManager

```python
class ConfigManager:
    def __init__(self):
        # Detecta SO y configura directorio apropiado
        
    def find_greasewazle_candidates(self) -> List[Dict[str, str]]:
        # Busca GreaseWeazle en ubicaciones comunes
        
    def verify_greasewazle_path(self, path: str) -> bool:
        # Verifica si una ruta es válida ejecutando `gw --help`
        
    def set_greasewazle_path(self, path: str) -> bool:
        # Guarda configuración y marca como configurado
```

### GreaseWazleConfigDialog

- Interfaz modal con auto-detección
- Radio buttons para candidatos encontrados
- Campo manual con explorador de archivos
- Botones de prueba para cada opción
- Guardado automático al confirmar

### Integración en Comandos

Todos los comandos que antes usaban `"gw"` ahora usan:

```python
gw_path = self.config_manager.get_greasewazle_path()
cmd = [gw_path, "read", ...]
```

## ✅ Beneficios

1. **Compatibilidad con Bundles**: Funciona en aplicaciones empaquetadas
2. **Experiencia de Usuario**: Configuración intuitiva con auto-detección
3. **Flexibilidad**: Soporta instalaciones personalizadas de GreaseWeazle
4. **Persistencia**: La configuración se mantiene entre sesiones
5. **Verificación**: Prueba automática de rutas para evitar errores
6. **Multiplataforma**: Funciona en macOS, Windows y Linux

## 🚀 Próximos Pasos

- [ ] Integración en el workflow de GitHub Actions
- [ ] Auto-actualización de configuración cuando se detecten cambios
- [ ] Soporte para múltiples versiones de GreaseWeazle
- [ ] Configuración de parámetros adicionales (delays, retries, etc.)
