#!/usr/bin/env python3
"""
Create an application icon for the HP-150 toolkit
This script generates a simple floppy disk icon
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL/Pillow not installed. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

import os

def create_hp150_icon():
    """Create a simple HP-150 floppy disk icon"""
    
    # Create a 64x64 image with transparent background
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    floppy_color = (45, 45, 45)      # Dark gray
    label_color = (240, 240, 240)    # Light gray
    text_color = (0, 0, 0)           # Black
    hole_color = (20, 20, 20)        # Very dark gray
    metal_color = (180, 180, 180)    # Light gray for metal
    
    # Draw floppy disk body (rounded rectangle)
    margin = 4
    draw.rounded_rectangle(
        [margin, margin, size-margin, size-margin], 
        radius=6, 
        fill=floppy_color, 
        outline=(0, 0, 0), 
        width=2
    )
    
    # Draw label area (white rectangle)
    label_margin = 12
    label_height = 18
    draw.rounded_rectangle(
        [label_margin, label_margin, size-label_margin, label_margin + label_height], 
        radius=2, 
        fill=label_color, 
        outline=(0, 0, 0), 
        width=1
    )
    
    # Draw write-protect notch
    notch_width = 8
    notch_height = 4
    notch_x = size - margin - notch_width
    notch_y = margin
    draw.rectangle(
        [notch_x, notch_y, notch_x + notch_width, notch_y + notch_height], 
        fill=(0, 0, 0)
    )
    
    # Draw center hub (circle)
    hub_radius = 8
    hub_center = size // 2
    draw.ellipse(
        [hub_center - hub_radius, hub_center + 6, 
         hub_center + hub_radius, hub_center + 6 + hub_radius * 2], 
        fill=hole_color, 
        outline=(0, 0, 0), 
        width=1
    )
    
    # Draw small center hole
    hole_radius = 3
    draw.ellipse(
        [hub_center - hole_radius, hub_center + 6 + hub_radius - hole_radius, 
         hub_center + hole_radius, hub_center + 6 + hub_radius + hole_radius], 
        fill=(0, 0, 0)
    )
    
    # Draw metal shutter (bottom part)
    shutter_height = 6
    shutter_y = size - margin - shutter_height
    draw.rectangle(
        [margin + 8, shutter_y, size - margin - 8, size - margin], 
        fill=metal_color, 
        outline=(0, 0, 0), 
        width=1
    )
    
    # Try to add text "HP" on the label
    try:
        # Try to use a system font
        font_size = 12
        try:
            # Try different font paths for macOS
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf", 
                "/Library/Fonts/Arial.ttf"
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        text = "HP"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size - text_width) // 2
        text_y = label_margin + (label_height - text_height) // 2
        
        # Draw text
        draw.text((text_x, text_y), text, fill=text_color, font=font)
        
    except Exception as e:
        print(f"Could not add text: {e}")
        # Draw simple dots instead
        dot_size = 2
        dot1_x = size // 2 - 6
        dot2_x = size // 2 + 2
        dot_y = label_margin + label_height // 2
        draw.ellipse([dot1_x, dot_y, dot1_x + dot_size, dot_y + dot_size], fill=text_color)
        draw.ellipse([dot2_x, dot_y, dot2_x + dot_size, dot2_y + dot_size], fill=text_color)
    
    return img

def main():
    """Create and save the icon"""
    # Create the icon
    icon_img = create_hp150_icon()
    
    # Save as PNG first (for viewing)
    current_dir = os.path.dirname(__file__)
    png_path = os.path.join(current_dir, "hp150_icon.png")
    icon_img.save(png_path, "PNG")
    print(f"PNG icon saved: {png_path}")
    
    # Create different sizes for ICO format
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    ico_images = []
    
    for size in sizes:
        resized = icon_img.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(resized)
    
    # Save as ICO (Windows format, but tkinter can use it)
    ico_path = os.path.join(current_dir, "hp150_icon.ico")
    ico_images[0].save(ico_path, "ICO", sizes=[(img.width, img.height) for img in ico_images])
    print(f"ICO icon saved: {ico_path}")
    
    # For macOS, also create ICNS format if possible
    try:
        # Create larger sizes for ICNS
        icns_sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512)]
        
        # Create temporary directory for iconutil
        import tempfile
        temp_dir = tempfile.mkdtemp()
        iconset_dir = os.path.join(temp_dir, "hp150_icon.iconset")
        os.makedirs(iconset_dir)
        
        # Generate all required sizes
        for size in icns_sizes:
            resized = icon_img.resize(size, Image.Resampling.LANCZOS)
            
            # Save normal resolution
            filename = f"icon_{size[0]}x{size[1]}.png"
            resized.save(os.path.join(iconset_dir, filename), "PNG")
            
            # Save @2x resolution for retina displays (except for largest sizes)
            if size[0] <= 256:
                retina_size = (size[0] * 2, size[1] * 2)
                retina_resized = icon_img.resize(retina_size, Image.Resampling.LANCZOS)
                retina_filename = f"icon_{size[0]}x{size[1]}@2x.png"
                retina_resized.save(os.path.join(iconset_dir, retina_filename), "PNG")
        
        # Use iconutil to create ICNS (macOS only)
        if os.system('which iconutil > /dev/null 2>&1') == 0:
            icns_path = os.path.join(current_dir, "hp150_icon.icns")
            os.system(f'iconutil -c icns "{iconset_dir}" -o "{icns_path}"')
            print(f"ICNS icon saved: {icns_path}")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"Could not create ICNS: {e}")
    
    print("\nIcon creation complete!")
    print("The icons can now be used by the HP-150 GUI application.")

if __name__ == "__main__":
    main()
