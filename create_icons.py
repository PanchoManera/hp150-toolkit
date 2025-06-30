#!/usr/bin/env python3
"""
Script para crear iconos básicos para HP-150 Toolkit
Este script crea iconos simples en PNG que pueden ser convertidos a otros formatos
"""

import os
from pathlib import Path

def create_simple_icon():
    """Crear un icono simple para la aplicación"""
    
    try:
        from PIL import Image, ImageDraw
        
        # Crear imagen de 256x256 (tamaño estándar para iconos)
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Dibujar un icono simple representando HP-150
        # Fondo azul redondeado
        margin = 20
        draw.rounded_rectangle([margin, margin, size-margin, size-margin], 
                             radius=30, fill=(0, 122, 255, 255))
        
        # Texto "HP" en blanco
        try:
            from PIL import ImageFont
            # Intentar usar una fuente del sistema
            font_size = 80
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        except ImportError:
            font = None
            
        # Dibujar texto HP-150
        text = "HP"
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = 60
            text_height = 20
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 20
        
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        # Dibujar "150" más pequeño debajo
        text2 = "150"
        if font:
            try:
                font_small = ImageFont.truetype("Arial.ttf", 40) if font != ImageFont.load_default() else font
            except:
                font_small = font
            bbox2 = draw.textbbox((0, 0), text2, font=font_small)
            text2_width = bbox2[2] - bbox2[0]
        else:
            text2_width = 40
            font_small = font
        
        x2 = (size - text2_width) // 2
        y2 = y + text_height + 10
        
        draw.text((x2, y2), text2, fill=(255, 255, 255, 200), font=font_small)
        
        return img
        
    except ImportError:
        print("PIL no disponible, creando icono básico...")
        # Crear un archivo de texto como placeholder
        return None

def main():
    """Crear todos los iconos necesarios"""
    
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    try:
        img = create_simple_icon()
        
        if img:
            # Guardar como PNG principal
            img.save(assets_dir / "icon.png")
            print("✅ Creado: assets/icon.png")
            
            # Crear diferentes tamaños
            sizes = [16, 32, 48, 64, 128, 256, 512]
            for size in sizes:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(assets_dir / f"icon_{size}.png")
            
            print(f"✅ Creados iconos en tamaños: {sizes}")
            
            # Para macOS, necesitamos crear un archivo .icns
            # Esto requiere herramientas adicionales, por ahora crear placeholder
            icns_placeholder = """# Para crear un archivo .icns real en macOS:
# 1. Instala iconutil: viene con Xcode Command Line Tools
# 2. Crea una carpeta icon.iconset/
# 3. Copia los PNG con nombres específicos (icon_16x16.png, etc.)
# 4. Ejecuta: iconutil -c icns icon.iconset
"""
            with open(assets_dir / "create_icns.txt", "w") as f:
                f.write(icns_placeholder)
            
            # Para Windows, crear placeholder para .ico
            ico_placeholder = """# Para crear un archivo .ico real:
# 1. Usa Pillow: pip install Pillow
# 2. O convierte icon.png a .ico usando herramientas online
"""
            with open(assets_dir / "create_ico.txt", "w") as f:
                f.write(ico_placeholder)
                
        else:
            # Crear archivos placeholder sin PIL
            placeholder_content = "# Placeholder icon file - replace with actual icon"
            
            for ext in ['png', 'ico']:
                with open(assets_dir / f"icon.{ext}", "w") as f:
                    f.write(placeholder_content)
            
            with open(assets_dir / "icon.icns", "w") as f:
                f.write(placeholder_content)
                
        print("✅ Iconos básicos creados en assets/")
        print("💡 Puedes reemplazarlos con iconos más elaborados si lo deseas")
        
    except Exception as e:
        print(f"❌ Error creando iconos: {e}")
        print("Creando archivos placeholder...")
        
        # Crear archivos placeholder básicos
        placeholder_content = "# Placeholder icon file - replace with actual icon"
        
        for ext in ['png', 'ico', 'icns']:
            with open(assets_dir / f"icon.{ext}", "w") as f:
                f.write(placeholder_content)

if __name__ == "__main__":
    main()
