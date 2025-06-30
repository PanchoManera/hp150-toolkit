#!/usr/bin/env python3
"""
HP-150 Image Manager - Iconos ASCII para la aplicación
"""

# Icono principal de la aplicación - HP-150 con floppy
APP_ICON = """
    ╔══════════════════════════════════════╗
    ║       HP-150 IMAGE MANAGER           ║
    ╠══════════════════════════════════════╣
    ║  ┌─────────────┐    ┌──────────────┐ ║
    ║  │ ░░░░░░░░░░░ │    │   💾 FLOPPY  │ ║
    ║  │ ░ HP-150 ░░ │◄──►│  [########]  │ ║
    ║  │ ░░░░░░░░░░░ │    │  ############  │ ║
    ║  │             │    │              │ ║
    ║  └─────────────┘    └──────────────┘ ║
    ║                                      ║
    ║  📀 READ  💾 WRITE  🔧 MANAGE       ║
    ╚══════════════════════════════════════╝
"""

# Icono compacto para títulos de ventana
WINDOW_ICON = "💾🖥️"

# Icono para el HP-150
HP150_ICON = """
    ┌─────────────┐
    │ ░░░░░░░░░░░ │
    │ ░ HP-150 ░░ │
    │ ░░░░░░░░░░░ │
    │             │
    │ [████████]  │
    │             │
    └─────────────┘
"""

# Icono para floppy disk
FLOPPY_ICON = """
    ┌──────────────┐
    │   💾 FLOPPY  │
    │  [########]  │
    │  ############  │
    │  #    ####   │
    │  #    ####   │
    │  ############  │
    └──────────────┘
"""

# Icono para GreaseWeazle
GREASEWEAZLE_ICON = """
    ┌────────────┐
    │ ⚡ GREASY ⚡ │
    │  ┌──────┐   │
    │  │ USB  │   │
    │  └──┬───┘   │
    │     │ 📀    │
    │     └───────│
    └────────────┘
"""

# Iconos pequeños para mensajes
ICONS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'floppy': '💾',
    'hp150': '🖥️',
    'read': '📀',
    'write': '💾',
    'extract': '📤',
    'add': '➕',
    'edit': '✏️',
    'delete': '🗑️',
    'analyze': '🔍',
    'progress': '🔄',
    'complete': '✅',
    'cancel': '❌'
}

def get_dialog_title(base_title, icon_type='info'):
    """Crear título de diálogo con icono"""
    icon = ICONS.get(icon_type, ICONS['info'])
    return f"{icon} {base_title} - HP-150 Manager"

def get_app_banner():
    """Banner principal de la aplicación"""
    return f"{WINDOW_ICON} HP-150 Image Manager"

def get_compact_banner():
    """Banner compacto para espacios pequeños"""
    return f"{ICONS['hp150']}{ICONS['floppy']} HP-150"

# Arte ASCII para splash/about
SPLASH_ART = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║    🖥️💾  HP-150 IMAGE MANAGER  💾🖥️                              ║
    ║                                                                  ║
    ║         ┌─────────────┐    📀    ┌──────────────┐               ║
    ║         │ ░░░░░░░░░░░ │  ◄─────► │   💾 FLOPPY  │               ║
    ║         │ ░ HP-150 ░░ │          │  [########]  │               ║
    ║         │ ░░░░░░░░░░░ │          │  ############  │               ║
    ║         │             │          │              │               ║
    ║         │ [████████]  │          └──────────────┘               ║
    ║         │             │                                         ║
    ║         └─────────────┘          ⚡ GreaseWeazle ⚡              ║
    ║                                                                  ║
    ║    📀 READ • 💾 WRITE • 🔧 MANAGE • 📤 EXTRACT • ✏️ EDIT      ║
    ║                                                                  ║
    ║         Una herramienta moderna para discos vintage            ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
"""

# Mini-iconos para botones
BUTTON_ICONS = {
    'open': '📂',
    'save': '💾',
    'save_as': '💾',
    'read_floppy': '📀',
    'write_floppy': '💾',
    'add_file': '➕',
    'edit_file': '✏️',
    'extract_file': '📤',
    'extract_all': '📦',
    'delete_file': '🗑️',
    'info': '📋',
    'analyze': '🔍'
}

def get_button_text(action, text):
    """Obtener texto de botón con icono"""
    icon = BUTTON_ICONS.get(action, '')
    return f"{icon} {text}" if icon else text

# Para debugging y testing
if __name__ == "__main__":
    print("🎨 HP-150 Image Manager Icons 🎨")
    print()
    print("App Icon:")
    print(APP_ICON)
    print()
    print("Splash Art:")
    print(SPLASH_ART)
    print()
    print("Icons disponibles:")
    for key, icon in ICONS.items():
        print(f"  {key}: {icon}")
