#!/usr/bin/env python3
"""
HP-150 Image Manager GUI - Extensiones de funcionalidad
Implementaciones completas para manipulación de archivos
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext
from .hp150_gui import HP150ImageManager
from .config_manager import ConfigManager
from .greasewazle_config_dialog import show_greasewazle_config
import os
import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

# Importar HP150FAT
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.tools.hp150_fat import HP150FAT

# Importar el módulo base
from src.gui.hp150_gui import HP150ImageManager
from src.gui.app_icon import APP_ICON, SPLASH_ART, get_dialog_title, get_app_banner

class HP150ImageManagerExtended(HP150ImageManager):
    """Versión extendida del administrador con funcionalidades completas"""
    
    def __init__(self, root):
        super().__init__(root)
        
        # Inicializar sistema de configuración
        self.config_manager = ConfigManager()
        
        # Variables adicionales para funcionalidades extendidas
        self.temp_dir = tempfile.mkdtemp(prefix="hp150_gui_")
        self.file_editors = {}  # Ventanas de edición abiertas
        self.has_temp_files = False  # Indica si hay archivos temporales pendientes
        self.temp_scp_file = None  # Archivo SCP temporal
        self.temp_img_file = None  # Archivo IMG temporal
        
        # Configurar cierre para limpiar archivos temporales
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_extended)
        
        # Mostrar el icono al iniciar
        print(APP_ICON)

        # Reset automático de GreaseWeazle (solo si está configurado)
        self.reset_greaseweazle()

        # Configurar icono de la ventana
        self.setup_window_icon()

        # Actualizar título
        self.root.title(get_app_banner())
        
        # Agregar botones adicionales después de que la GUI base esté construida
        self.root.after(100, self.add_floppy_buttons)
        
        # Agregar lógica de guardado correcta
        self.root.bind('<Command-s>', lambda e: self.save_action())
        
        # Deshabilitar botones no implementados después de que la GUI esté construida
        self.root.after(200, self.disable_unimplemented_buttons)
    
    def setup_window_icon(self):
        """Configurar icono de la ventana"""
        try:
            # Buscar archivos de icono en el directorio de la GUI
            icon_dir = os.path.dirname(__file__)
            
            # Intentar diferentes formatos de icono
            icon_files = [
                os.path.join(icon_dir, "hp150_icon.ico"),  # Windows ICO
                os.path.join(icon_dir, "hp150_icon.icns"), # macOS ICNS
                os.path.join(icon_dir, "hp150_icon.png")   # PNG fallback
            ]
            
            icon_set = False
            
            # Para macOS, intentar usar ICNS primero
            if sys.platform == "darwin":
                icns_path = os.path.join(icon_dir, "hp150_icon.icns")
                if os.path.exists(icns_path):
                    try:
                        # En macOS, tkinter no soporta ICNS directamente,
                        # pero podemos usar el PNG
                        png_path = os.path.join(icon_dir, "hp150_icon.png")
                        if os.path.exists(png_path):
                            from tkinter import PhotoImage
                            icon_image = PhotoImage(file=png_path)
                            self.root.iconphoto(True, icon_image)
                            icon_set = True
                            print(f"Icon set using PNG: {png_path}")
                    except Exception as e:
                        print(f"Could not set PNG icon: {e}")
            
            # Intentar ICO para compatibilidad general
            if not icon_set:
                ico_path = os.path.join(icon_dir, "hp150_icon.ico")
                if os.path.exists(ico_path):
                    try:
                        self.root.iconbitmap(ico_path)
                        icon_set = True
                        print(f"Icon set using ICO: {ico_path}")
                    except Exception as e:
                        print(f"Could not set ICO icon: {e}")
            
            # Si no se pudo establecer el icono, usar PNG como PhotoImage
            if not icon_set:
                png_path = os.path.join(icon_dir, "hp150_icon.png")
                if os.path.exists(png_path):
                    try:
                        from tkinter import PhotoImage
                        # Redimensionar para uso como icono de ventana
                        icon_image = PhotoImage(file=png_path)
                        # Usar subsample para hacer más pequeño si es necesario
                        if icon_image.width() > 32:
                            factor = icon_image.width() // 32
                            icon_image = icon_image.subsample(factor, factor)
                        
                        self.root.iconphoto(True, icon_image)
                        # Guardar referencia para evitar garbage collection
                        self.root.icon_image = icon_image
                        icon_set = True
                        print(f"Icon set using PNG PhotoImage: {png_path}")
                    except Exception as e:
                        print(f"Could not set PNG PhotoImage icon: {e}")
            
            # Como último recurso, agregar emoji al título
            if not icon_set:
                current_title = self.root.title()
                if '💾' not in current_title:
                    self.root.title(f"💾 {current_title}")
                print("Using emoji in title as fallback")
            
        except Exception as e:
            print(f"Warning: Could not set window icon: {e}")
            # Fallback: solo agregar emoji al título
            try:
                current_title = self.root.title()
                if '💾' not in current_title:
                    self.root.title(f"💾 {current_title}")
            except:
                pass
    
    def add_floppy_buttons(self):
        """Agregar sección de Floppy a la columna derecha del panel de botones"""
        print("[DEBUG] Ejecutando add_floppy_buttons()")
        
        # Buscar el panel de botones principal
        def find_button_frame(widget, depth=0):
            print(f"[DEBUG] Buscando en widget: {type(widget).__name__}, depth: {depth}")
            if isinstance(widget, ttk.LabelFrame):
                text = widget.cget('text')
                print(f"[DEBUG] LabelFrame encontrado con texto: '{text}'")
                if text == 'Acciones':
                    print(f"[DEBUG] ¡Panel de Acciones encontrado!")
                    return widget
            
            for child in widget.winfo_children():
                result = find_button_frame(child, depth + 1)
                if result:
                    return result
            return None
        
        button_frame = find_button_frame(self.root)
        print(f"[DEBUG] button_frame encontrado: {button_frame}")
        
        if button_frame:
            print(f"[DEBUG] Agregando sección de Floppy a la columna derecha")
            
            # Crear sección de Floppy en la columna izquierda (row=0, column=0) - arriba de archivos
            floppy_section = ttk.LabelFrame(button_frame, text="Floppy", padding="5")
            floppy_section.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 5), pady=(0, 10))
            floppy_section.columnconfigure(0, weight=1)
            
            print(f"[DEBUG] Sección Floppy creada en columna derecha")
            
            # Agregar los botones de floppy
            self.read_floppy_btn = ttk.Button(
                floppy_section, 
                text="📀 Leer Floppy", 
                command=self.read_from_floppy,
                width=14
            )
            self.read_floppy_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
            print(f"[DEBUG] Botón Leer Floppy creado")
            
            self.write_floppy_btn = ttk.Button(
                floppy_section, 
                text="💾 Escribir Floppy", 
                command=self.write_to_floppy,
                state='disabled',
                width=14
            )
            self.write_floppy_btn.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
            print(f"[DEBUG] Botón Escribir Floppy creado")
            
            # Botón de configuración de GreaseWeazle
            self.config_gw_btn = ttk.Button(
                floppy_section, 
                text="⚙️ Configurar GW", 
                command=self.show_greasewazle_config,
                width=14
            )
            self.config_gw_btn.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
            print(f"[DEBUG] Botón Configurar GreaseWeazle creado")
            
            print(f"[DEBUG] ✅ Botones de floppy agregados exitosamente a la columna derecha!")
        else:
            print(f"[DEBUG] ERROR: No se encontró el panel de botones 'Acciones'")
            # Como fallback, vamos a agregarlo directamente al frame principal
            main_frame = None
            
            def find_main_frame(widget):
                if isinstance(widget, ttk.Frame):
                    # Buscar el frame que contiene otros LabelFrames
                    has_labelframes = any(isinstance(child, ttk.LabelFrame) for child in widget.winfo_children())
                    if has_labelframes:
                        return widget
                
                for child in widget.winfo_children():
                    result = find_main_frame(child)
                    if result:
                        return result
                return None
            
            main_frame = find_main_frame(self.root)
            if main_frame:
                print(f"[DEBUG] Usando main_frame como fallback")
                
                # Crear panel de botones de floppy independiente
                floppy_frame = ttk.LabelFrame(main_frame, text="Floppy", padding="10")
                floppy_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N), padx=(10, 0))
                floppy_frame.columnconfigure(0, weight=1)
                
                self.read_floppy_btn = ttk.Button(
                    floppy_frame, 
                    text="📀 Leer Floppy", 
                    command=self.read_from_floppy,
                    width=18
                )
                self.read_floppy_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
                
                self.write_floppy_btn = ttk.Button(
                    floppy_frame, 
                    text="💾 Escribir Floppy", 
                    command=self.write_to_floppy,
                    state='disabled',
                    width=18
                )
                self.write_floppy_btn.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
                
                print(f"[DEBUG] Panel independiente de floppy creado")
    
    def disable_unimplemented_buttons(self):
        """Deshabilitar permanentemente botones de funciones no implementadas"""
        def find_and_disable_buttons(widget):
            """Buscar recursivamente botones y deshabilitarlos según el texto"""
            if isinstance(widget, ttk.Button):
                button_text = widget.cget('text')
                # Lista de botones que NO están implementados
                unimplemented_buttons = [
                    "Verificar Integridad",
                    "Reparar Imagen", 
                    "Crear Backup",
                    "Restaurar Backup",
                    "Información Detallada"
                ]
                
                if button_text in unimplemented_buttons:
                    widget.config(state='disabled')
                    print(f"Deshabilitando botón: {button_text}")
            
            # Buscar recursivamente en hijos
            for child in widget.winfo_children():
                find_and_disable_buttons(child)
        
        # Aplicar a toda la ventana
        find_and_disable_buttons(self.root)
        
        # También deshabilitar el botón Analizar del toolbar si existe
        if hasattr(self, 'analyze_btn'):
            self.analyze_btn.config(state='disabled')
    
    def reset_greaseweazle(self):
        """Configurar y resetear GreaseWeazle al iniciar la GUI"""
        if not self.config_manager.is_greasewazle_configured():
            print("⚠️ GreaseWeazle no configurado. Configure desde el menú de configuración.")
            return
        
        import subprocess
        import threading
        
        def do_reset():
            try:
                # Paso 1: Configurar delays
                print("⚙️ Configurando delays de GreaseWeazle...")
                gw_path = self.config_manager.get_greasewazle_path()
                delays_result = subprocess.run(
                    [gw_path, 'delays', '--step', '20000'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if delays_result.returncode == 0:
                    print("✅ Delays configurados exitosamente (--step 20000)")
                else:
                    print(f"⚠️ Warning configurando delays: {delays_result.stderr}")
                
                # Paso 2: Reset
                print("🔄 Reseteando GreaseWeazle...")
                reset_result = subprocess.run(
                    [gw_path, 'reset'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if reset_result.returncode == 0:
                    print("✅ GreaseWeazle reseteado exitosamente")
                else:
                    print(f"⚠️ Warning en reset de GreaseWeazle: {reset_result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("⚠️ Timeout en configuración de GreaseWeazle - continuando de todos modos")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Error en configuración de GreaseWeazle: {e}")
            except FileNotFoundError:
                print("⚠️ GreaseWeazle no encontrado - ¿está instalado y en PATH?")
            except Exception as e:
                print(f"⚠️ Error inesperado en configuración de GreaseWeazle: {e}")
        
        # Ejecutar reset en hilo separado para no bloquear la GUI
        threading.Thread(target=do_reset, daemon=True).start()
    
    
    def update_button_states(self):
        """Actualizar estado de los botones según el contexto - Versión extendida"""
        # Llamar al método padre primero
        super().update_button_states()
        
        # Luego sobrescribir los botones que SÍ están implementados
        has_image = self.fat_handler is not None
        has_selection = len(self.file_tree.selection()) > 0
        
        # Botones que están IMPLEMENTADOS en la versión extendida (toolbar)
        if hasattr(self, 'add_btn'):
            self.add_btn.config(state='normal' if has_image else 'disabled')
        if hasattr(self, 'extract_btn'):
            self.extract_btn.config(state='normal' if (has_image and has_selection) else 'disabled')
        if hasattr(self, 'extract_all_btn'):
            self.extract_all_btn.config(state='normal' if has_image else 'disabled')
        if hasattr(self, 'edit_btn'):
            self.edit_btn.config(state='normal' if (has_image and has_selection) else 'disabled')
        if hasattr(self, 'delete_btn'):
            self.delete_btn.config(state='normal' if (has_image and has_selection) else 'disabled')
        
        # Botones que NO están implementados - siempre deshabilitados
        if hasattr(self, 'analyze_btn'):
            self.analyze_btn.config(state='disabled')
        
        # Botón de escritura de floppy - solo habilitado si hay imagen cargada
        if hasattr(self, 'write_floppy_btn'):
            self.write_floppy_btn.config(state='normal' if has_image else 'disabled')
    
    def get_selected_file(self):
        """Obtener archivo seleccionado en la lista"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return None
        
        item = self.file_tree.item(selection[0])
        filename = item['values'][0]  # Primera columna es el nombre
        return filename
    
    def calculate_space_needed(self, data_size):
        """Calcular espacio necesario en clusters"""
        cluster_size = self.fat_handler.cluster_size
        clusters_needed = (data_size + cluster_size - 1) // cluster_size
        return clusters_needed * cluster_size
    
    def check_space_available(self, needed_space):
        """Verificar si hay espacio disponible"""
        info = self.fat_handler.get_disk_info()
        return info['free_space'] >= needed_space
    
    # Implementación completa de agregar archivo
    def add_file(self):
        """Agregar archivo a la imagen"""
        if not self.fat_handler:
            messagebox.showwarning("Advertencia", "No hay imagen cargada")
            return
        
        # Seleccionar archivo a agregar
        source_file = filedialog.askopenfilename(
            title="Seleccionar archivo para agregar",
            filetypes=[("Todos los archivos", "*.*")]
        )
        
        if not source_file:
            return
        
        # Verificar tamaño del archivo
        file_size = os.path.getsize(source_file)
        space_needed = self.calculate_space_needed(file_size)
        
        if not self.check_space_available(space_needed):
            messagebox.showerror(
                "Error de Espacio",
                f"No hay suficiente espacio en el disco.\\n"
                f"Necesario: {space_needed:,} bytes\\n"
                f"Disponible: {self.fat_handler.get_disk_info()['free_space']:,} bytes"
            )
            return
        
        # Pedir nombre para el archivo en el disco (formato 8.3)
        suggested_name = os.path.basename(source_file).upper()
        
        # Verificar formato 8.3
        if '.' in suggested_name:
            name_part, ext_part = suggested_name.rsplit('.', 1)
            if len(name_part) > 8 or len(ext_part) > 3:
                name_part = name_part[:8]
                ext_part = ext_part[:3]
                suggested_name = f"{name_part}.{ext_part}"
        else:
            if len(suggested_name) > 8:
                suggested_name = suggested_name[:8]
        
        target_name = simpledialog.askstring(
            "Nombre del archivo",
            f"Ingresa el nombre en formato 8.3 para el archivo:\\n"
            f"Archivo origen: {os.path.basename(source_file)}\\n"
            f"Tamaño: {file_size:,} bytes",
            initialvalue=suggested_name
        )
        
        if not target_name:
            return
        
        # Validar formato 8.3
        if not self.validate_filename_83(target_name):
            messagebox.showerror(
                "Error de Formato",
                "El nombre debe estar en formato 8.3 (máximo 8 caracteres, "
                "punto, máximo 3 caracteres de extensión)"
            )
            return
        
        # Verificar si el archivo ya existe
        existing_file = self.fat_handler.get_file(target_name.upper())
        if existing_file:
            if not messagebox.askyesno(
                "Archivo Existente",
                f"El archivo {target_name} ya existe. ¿Deseas reemplazarlo?"
            ):
                return
        
        try:
            # Leer datos del archivo origen
            with open(source_file, 'rb') as f:
                file_data = f.read()
            
            # Escribir al disco HP-150
            if existing_file:
                # Reemplazar archivo existente
                if len(file_data) > existing_file.size:
                    messagebox.showerror(
                        "Error de Tamaño",
                        f"El archivo nuevo ({len(file_data):,} bytes) es más grande "
                        f"que el existente ({existing_file.size:,} bytes). "
                        f"No se puede expandir."
                    )
                    return
                
                success = self.fat_handler.write_file(target_name.upper(), file_data)
            else:
                # Crear archivo nuevo
                try:
                    success = self.fat_handler.write_file(target_name.upper(), file_data, attr=0x20)
                except Exception as e:
                    messagebox.showerror("Error", f"Error creando archivo: {e}")
                    return
            
            if success:
                self.set_modified(True)
                self.refresh_file_list()
                self.update_status(f"Archivo {target_name} agregado exitosamente")
                messagebox.showinfo("Éxito", f"Archivo {target_name} agregado exitosamente")
            else:
                messagebox.showerror("Error", f"Error agregando archivo {target_name}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error agregando archivo: {e}")
    
    def validate_filename_83(self, filename):
        """Validar formato de nombre 8.3"""
        if not filename:
            return False
        
        # Verificar caracteres válidos
        invalid_chars = '<>:"/\\|?*'
        if any(c in filename for c in invalid_chars):
            return False
        
        if '.' in filename:
            parts = filename.split('.')
            if len(parts) != 2:
                return False
            name_part, ext_part = parts
            return len(name_part) <= 8 and len(ext_part) <= 3 and name_part and ext_part
        else:
            return len(filename) <= 8
    
    # Implementación completa de editar archivo
    def edit_file(self):
        """Editar archivo seleccionado"""
        filename = self.get_selected_file()
        if not filename:
            return
        
        if not self.fat_handler:
            messagebox.showwarning("Advertencia", "No hay imagen cargada")
            return
        
        # Verificar si el archivo ya está siendo editado
        if filename in self.file_editors:
            # Traer ventana al frente
            self.file_editors[filename].lift()
            return
        
        try:
            # Leer contenido del archivo
            file_data = self.fat_handler.read_file(filename)
            file_entry = self.fat_handler.get_file(filename)
            
            # Crear ventana de edición
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Editando: {filename}")
            edit_window.geometry("800x600")
            
            # Frame principal
            main_frame = ttk.Frame(edit_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Información del archivo
            info_frame = ttk.LabelFrame(main_frame, text="Información del Archivo", padding="5")
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(info_frame, text=f"Archivo: {filename}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Tamaño: {len(file_data):,} bytes").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Tamaño máximo: {file_entry.size:,} bytes").pack(anchor=tk.W)
            
            # Detectar tipo de archivo
            is_text = self.is_text_file(file_data)
            
            if is_text:
                # Editor de texto
                self.create_text_editor(main_frame, edit_window, filename, file_data, file_entry)
            else:
                # Visor hexadecimal
                self.create_hex_viewer(main_frame, edit_window, filename, file_data, file_entry)
            
            # Registrar ventana de edición
            self.file_editors[filename] = edit_window
            
            # Configurar cierre
            def on_edit_close():
                if filename in self.file_editors:
                    del self.file_editors[filename]
                edit_window.destroy()
            
            edit_window.protocol("WM_DELETE_WINDOW", on_edit_close)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error abriendo archivo {filename}: {e}")
    
    def is_text_file(self, data):
        """Detectar si un archivo es texto"""
        try:
            # Intentar decodificar como texto
            data.decode('ascii')
            return True
        except UnicodeDecodeError:
            # Verificar si tiene muchos caracteres imprimibles
            printable_count = sum(1 for b in data if 32 <= b <= 126 or b in [9, 10, 13])
            return printable_count / len(data) > 0.7 if data else False
    
    def create_text_editor(self, parent, window, filename, data, file_entry):
        """Crear editor de texto"""
        # Frame del editor
        editor_frame = ttk.LabelFrame(parent, text="Editor de Texto", padding="5")
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área de texto con scroll
        text_area = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Courier', 10)
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        
        # Insertar contenido
        try:
            text_content = data.decode('ascii', errors='replace')
            text_area.insert(tk.INSERT, text_content)
        except Exception as e:
            text_area.insert(tk.INSERT, f"Error decodificando archivo: {e}")
        
        # Botones
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_changes():
            try:
                new_content = text_area.get('1.0', tk.END).rstrip('\\n')
                new_data = new_content.encode('ascii', errors='replace')
                
                if len(new_data) > file_entry.size:
                    messagebox.showerror(
                        "Error de Tamaño",
                        f"El contenido nuevo ({len(new_data)} bytes) excede el "
                        f"tamaño máximo del archivo ({file_entry.size} bytes)"
                    )
                    return
                
                # Rellenar con espacios hasta el tamaño original si es menor
                if len(new_data) < file_entry.size:
                    new_data += b'\\x00' * (file_entry.size - len(new_data))
                
                success = self.fat_handler.write_file(filename, new_data)
                
                if success:
                    self.set_modified(True)
                    self.refresh_file_list()
                    messagebox.showinfo("Éxito", f"Archivo {filename} guardado exitosamente")
                    window.destroy()
                else:
                    messagebox.showerror("Error", f"Error guardando archivo {filename}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando archivo: {e}")
        
        ttk.Button(button_frame, text="💾 Guardar", command=save_changes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="❌ Cancelar", command=window.destroy).pack(side=tk.LEFT)
    
    def create_hex_viewer(self, parent, window, filename, data, file_entry):
        """Crear visor hexadecimal"""
        # Frame del visor
        viewer_frame = ttk.LabelFrame(parent, text="Visor Hexadecimal (Solo Lectura)", padding="5")
        viewer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área de texto con scroll
        hex_area = scrolledtext.ScrolledText(
            viewer_frame,
            wrap=tk.NONE,
            width=80,
            height=25,
            font=('Courier', 9),
            state=tk.DISABLED
        )
        hex_area.pack(fill=tk.BOTH, expand=True)
        
        # Generar vista hexadecimal
        hex_content = self.generate_hex_dump(data)
        
        hex_area.config(state=tk.NORMAL)
        hex_area.insert(tk.INSERT, hex_content)
        hex_area.config(state=tk.DISABLED)
        
        # Botón de cerrar
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="❌ Cerrar", command=window.destroy).pack(side=tk.LEFT)
    
    def generate_hex_dump(self, data):
        """Generar dump hexadecimal de los datos"""
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            
            # Offset
            offset = f"{i:08x}"
            
            # Bytes en hex
            hex_bytes = ' '.join(f"{b:02x}" for b in chunk)
            hex_bytes = hex_bytes.ljust(47)  # Pad para alinear
            
            # ASCII representation
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            
            lines.append(f"{offset}  {hex_bytes}  |{ascii_repr}|")
        
        return '\\n'.join(lines)
    
    # Implementación completa de eliminar archivo
    def delete_file(self):
        """Eliminar archivo seleccionado"""
        filename = self.get_selected_file()
        if not filename:
            return
        
        if not self.fat_handler:
            messagebox.showwarning("Advertencia", "No hay imagen cargada")
            return
        
        file_entry = self.fat_handler.get_file(filename)
        if not file_entry:
            messagebox.showerror("Error", f"Archivo {filename} no encontrado")
            return
        
        # Verificar si es archivo de sistema
        if file_entry.attr & 0x04:  # System file
            if not messagebox.askyesno(
                "Archivo de Sistema",
                f"¿Estás seguro de que quieres eliminar el archivo de sistema {filename}?\\n"
                "Esto podría hacer que el disco no sea booteable."
            ):
                return
        
        if not messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar {filename}?\\n"
            f"Esta acción no se puede deshacer."
        ):
            return
        
        try:
            # Usar la función de eliminación completa
            success = self.fat_handler.delete_file(filename)
            
            if success:
                self.set_modified(True)
                self.refresh_file_list()
                self.update_status(f"Archivo {filename} eliminado completamente")
                messagebox.showinfo("Éxito", f"Archivo {filename} eliminado exitosamente")
            else:
                messagebox.showerror("Error", f"Error eliminando archivo {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error eliminando archivo: {e}")
    
    # Implementación completa de extraer archivo
    def extract_file(self):
        """Extraer archivo seleccionado"""
        filename = self.get_selected_file()
        if not filename:
            return
        
        if not self.fat_handler:
            messagebox.showwarning("Advertencia", "No hay imagen cargada")
            return
        
        # Seleccionar destino - usar initialfile en lugar de initialvalue
        output_file = filedialog.asksaveasfilename(
            title=f"Guardar {filename} como",
            initialfile=filename.lower(),
            filetypes=[("Todos los archivos", "*.*")],
            initialdir=os.path.expanduser("~/Desktop")
        )
        
        if not output_file:
            return
        
        try:
            # Leer y guardar archivo
            file_data = self.fat_handler.read_file(filename)
            
            with open(output_file, 'wb') as f:
                f.write(file_data)
            
            self.update_status(f"Archivo {filename} extraído a {output_file}")
            messagebox.showinfo("Éxito", f"Archivo extraído exitosamente a:\n{output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error extrayendo archivo: {e}")
    
    def extract_all_files(self):
        """Extraer todos los archivos"""
        if not self.fat_handler:
            messagebox.showwarning("Advertencia", "No hay imagen cargada")
            return
        
        # Contar archivos extraíbles primero
        try:
            files = self.fat_handler.list_files()
            extractable_files = [f for f in files if not f.is_volume]
            
            if not extractable_files:
                messagebox.showinfo("Sin archivos", "No hay archivos para extraer en esta imagen")
                return
            
            # Confirmar extracción
            if not messagebox.askyesno(
                "Extraer todos los archivos",
                f"¿Extraer {len(extractable_files)} archivos?\n\n"
                "Se creará una carpeta con todos los archivos."
            ):
                return
        
        except Exception as e:
            messagebox.showerror("Error", f"Error listando archivos: {e}")
            return
        
        # Seleccionar directorio destino
        output_dir = filedialog.askdirectory(
            title="Seleccionar carpeta de destino",
            initialdir=os.path.expanduser("~/Desktop")
        )
        if not output_dir:
            return
        
        # Crear subdirectorio con nombre de la imagen
        if self.current_image:
            img_name = os.path.splitext(os.path.basename(self.current_image))[0]
            extraction_dir = os.path.join(output_dir, f"{img_name}_extracted")
        else:
            extraction_dir = os.path.join(output_dir, "hp150_extracted")
        
        try:
            # Crear directorio de extracción
            os.makedirs(extraction_dir, exist_ok=True)
            
            # Crear ventana de progreso
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Extrayendo archivos...")
            progress_window.geometry("500x300")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            main_frame = ttk.Frame(progress_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text="📤 Extrayendo todos los archivos", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
            
            # Información
            info_label = ttk.Label(main_frame, text=f"Destino: {extraction_dir}")
            info_label.pack(anchor=tk.W, pady=(0, 10))
            
            # Progreso
            progress_frame = ttk.Frame(main_frame)
            progress_frame.pack(fill=tk.X, pady=(0, 10))
            
            current_file_label = ttk.Label(progress_frame, text="Iniciando...")
            current_file_label.pack(anchor=tk.W)
            
            progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
            progress_bar.pack(fill=tk.X, pady=(5, 0))
            progress_bar['maximum'] = len(extractable_files)
            
            # Lista de archivos procesados
            list_frame = ttk.LabelFrame(main_frame, text="Archivos extraídos", padding="5")
            list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            file_listbox = tk.Listbox(list_frame, height=8)
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=file_listbox.yview)
            file_listbox.configure(yscrollcommand=scrollbar.set)
            
            file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Botón cerrar (inicialmente deshabilitado)
            close_btn = ttk.Button(main_frame, text="Cerrar", command=progress_window.destroy, state='disabled')
            close_btn.pack()
            
            # Función para extraer archivos
            def extract_files():
                extracted = 0
                errors = []
                
                for i, file_entry in enumerate(extractable_files):
                    try:
                        current_file_label.config(text=f"Extrayendo: {file_entry.full_name}")
                        progress_window.update_idletasks()
                        
                        file_data = self.fat_handler.read_file(file_entry.full_name)
                        output_path = os.path.join(extraction_dir, file_entry.full_name.lower())
                        
                        with open(output_path, 'wb') as f:
                            f.write(file_data)
                        
                        extracted += 1
                        file_listbox.insert(tk.END, f"✅ {file_entry.full_name} ({len(file_data):,} bytes)")
                        file_listbox.see(tk.END)
                        
                    except Exception as e:
                        errors.append(f"{file_entry.full_name}: {e}")
                        file_listbox.insert(tk.END, f"❌ {file_entry.full_name} (ERROR)")
                        file_listbox.see(tk.END)
                    
                    progress_bar['value'] = i + 1
                    progress_window.update_idletasks()
                
                # Completado
                current_file_label.config(text=f"Completado: {extracted}/{len(extractable_files)} archivos")
                close_btn.config(state='normal')
                
                # Mostrar resumen
                summary = f"Extracción completada\n\n"
                summary += f"Archivos extraídos: {extracted}\n"
                summary += f"Errores: {len(errors)}\n"
                summary += f"Carpeta: {extraction_dir}"
                
                if errors:
                    summary += f"\n\nErrores:\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        summary += f"\n... y {len(errors) - 5} más"
                
                self.update_status(f"Extraídos {extracted} archivos a {extraction_dir}")
                messagebox.showinfo("Extracción completada", summary)
            
            # Ejecutar extracción en hilo separado
            import threading
            threading.Thread(target=extract_files, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la extracción: {e}")
    
    # Sobrescribir funciones NO implementadas para deshabilitarlas
    def verify_integrity(self):
        """Función no implementada - deshabilitada"""
        messagebox.showwarning("No Implementado", "Esta función no está implementada en esta versión")
    
    def repair_image(self):
        """Función no implementada - deshabilitada"""
        messagebox.showwarning("No Implementado", "Esta función no está implementada en esta versión")
    
    def create_backup(self):
        """Función no implementada - deshabilitada"""
        messagebox.showwarning("No Implementado", "Esta función no está implementada en esta versión")
    
    def restore_backup(self):
        """Función no implementada - deshabilitada"""
        messagebox.showwarning("No Implementado", "Esta función no está implementada en esta versión")
    
    def analyze_image(self):
        """Función no implementada - deshabilitada"""
        messagebox.showwarning("No Implementado", "Esta función no está implementada en esta versión")
    
    def show_disk_info(self):
        """Función no implementada - deshabilitada"""
        messagebox.showwarning("No Implementado", "Esta función no está implementada en esta versión")
    
    def save_action(self):
        """Acción de guardar basada en contexto (CMD+S en macOS)"""
        if self.has_temp_files:
            if messagebox.askyesno("Guardar Proyecto", "¿Deseas guardar el proyecto completo con SCP e IMG?"):
                self.save_floppy_project(self.temp_scp_file, self.temp_img_file)
            else:
                self.save_img_only(self.temp_img_file)
        elif self.modified:
            self.save_image_as()

    def save_image_as(self):
        """Sobrescribir método para manejar guardado correcto según contexto"""
        if not self.current_image:
            messagebox.showwarning("Advertencia", "No hay imagen cargada")
            return
        
        # Si tenemos archivos temporales, ofrecer guardar proyecto
        if self.has_temp_files:
            result = messagebox.askyesnocancel(
                "Guardar Proyecto",
                "Tienes archivos temporales de la lectura del floppy.\n\n"
                "¿Deseas guardar el proyecto completo?\n\n"
                "• SÍ: Guardar proyecto (SCP + IMG + README)\n"
                "• NO: Guardar solo imagen IMG\n"
                "• CANCELAR: No guardar"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - guardar proyecto completo
                self.save_floppy_project(self.temp_scp_file, self.temp_img_file)
            else:  # No - guardar solo IMG
                self.save_img_only(self.temp_img_file)
        else:
            # Imagen normal abierta desde archivo - guardar solo como IMG
            filename = filedialog.asksaveasfilename(
                title="Guardar Imagen HP-150",
                defaultextension=".img",
                filetypes=[
                    ("Imágenes HP-150", "*.img"),
                    ("Todos los archivos", "*.*")
                ],
                initialdir=os.path.expanduser("~/Desktop")
            )
            
            if filename:
                try:
                    self.update_status("Guardando imagen...")
                    
                    # Asegurar extensión .img
                    if not filename.lower().endswith('.img'):
                        filename = os.path.splitext(filename)[0] + '.img'
                    
                    # Copiar archivo actual al nuevo destino
                    import shutil
                    shutil.copy2(self.current_image, filename)
                    
                    # Actualizar imagen actual y marcar como no modificada
                    self.current_image = filename
                    self.set_modified(False)
                    
                    # Actualizar información
                    self.update_info_panel()
                    
                    self.update_status(f"Imagen guardada como: {os.path.basename(filename)}")
                    messagebox.showinfo("Éxito", f"Imagen guardada exitosamente como:\n{filename}")
                    
                except Exception as e:
                    self.update_status("Error guardando imagen")
                    messagebox.showerror("Error", f"Error guardando imagen como:\n{e}")

    def on_closing_extended(self):
        """Cierre extendido con limpieza"""
        # Cerrar editores abiertos
        for editor in list(self.file_editors.values()):
            editor.destroy()
        
        # Verificar si hay archivos temporales sin guardar
        if self.has_temp_files and self.temp_scp_file and self.temp_img_file:
            if os.path.exists(self.temp_scp_file) and os.path.exists(self.temp_img_file):
                result = messagebox.askyesnocancel(
                    "Archivos Temporales",
                    "Tienes archivos temporales de la lectura del floppy.\n\n"
                    "¿Deseas guardar el proyecto antes de salir?\n\n"
                    "• SÍ: Guardar proyecto completo (SCP + IMG)\n"
                    "• NO: Salir sin guardar (se perderán los datos)\n"
                    "• CANCELAR: No salir"
                )
                
                if result is None:  # Cancel - no salir
                    return
                elif result:  # Yes - guardar proyecto completo
                    self.save_floppy_project(self.temp_scp_file, self.temp_img_file)
                # Si dice No, simplemente continúa sin guardar
                
                # Marcar como guardado
                self.has_temp_files = False
        
        # Si hay cambios en imagen ya guardada, preguntar sobre guardar en floppy
        elif self.modified and self.current_image:
            result = messagebox.askyesnocancel(
                "Imagen Modificada",
                "Hay cambios sin guardar. ¿Qué deseas hacer?\n\n"
                "• SÍ: Guardar en floppy con GreaseWeazle\n"
                "• NO: Guardar solo el archivo de imagen\n"
                "• CANCELAR: No salir"
            )
            
            if result is None:  # Cancel - no salir
                return
            elif result:  # Yes - guardar en floppy
                if self.write_to_floppy():
                    self.set_modified(False)
                else:
                    # Si falla, preguntar si quiere guardar solo el archivo
                    if messagebox.askyesno(
                        "Error en Floppy", 
                        "Error escribiendo al floppy. ¿Guardar solo el archivo de imagen?"
                    ):
                        self.save_image()
            else:  # No - guardar solo archivo
                self.save_image()
        
        # Limpiar archivos temporales
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Cerrar aplicación
        self.root.destroy()
    
    def check_temp_files_before_action(self, action_name="continuar"):
        """Verificar si hay archivos temporales sin guardar antes de una acción"""
        if self.has_temp_files and self.temp_scp_file and self.temp_img_file:
            if os.path.exists(self.temp_scp_file) and os.path.exists(self.temp_img_file):
                result = messagebox.askyesnocancel(
                    "Archivos Temporales Sin Guardar",
                    f"Tienes archivos temporales de la lectura del floppy sin guardar.\n\n"
                    f"¿Deseas guardar el proyecto antes de {action_name}?\n\n"
                    f"• SÍ: Guardar proyecto completo (SCP + IMG)\n"
                    f"• NO: Continuar sin guardar (se perderán los datos)\n"
                    f"• CANCELAR: No {action_name}"
                )
                
                if result is None:  # Cancel - no continuar
                    return False
                elif result:  # Yes - guardar proyecto completo
                    self.save_floppy_project(self.temp_scp_file, self.temp_img_file)
                    return True
                else:  # No - continuar sin guardar
                    self.has_temp_files = False
                    self.temp_scp_file = None
                    self.temp_img_file = None
                    return True
        return True  # No hay archivos temporales, continuar normalmente
    
    def read_from_floppy(self):
        """Leer imagen desde floppy usando GreaseWeazle - flujo simplificado"""
        # Verificar que GreaseWeazle esté configurado
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
        
        # Verificar archivos temporales antes de continuar
        if not self.check_temp_files_before_action("leer un nuevo floppy"):
            return
            
        print("[DEBUG] Iniciando read_from_floppy()")
        import subprocess
        from datetime import datetime
        import tempfile
        
        print("[DEBUG] Imports completados")
        
        # Diálogo simple solo para seleccionar drive - MÁS GRANDE
        print("[DEBUG] Creando diálogo...")
        dialog = tk.Toplevel(self.root)
        dialog.title("Leer Floppy HP-150")
        dialog.geometry("500x400")
        dialog.minsize(480, 380)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar grid en la ventana principal
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        
        print("[DEBUG] Diálogo creado exitosamente")
        
        # Variables
        drive_var = tk.IntVar(value=0)
        print("[DEBUG] Variables creadas")
        
        # Frame principal con grid
        main_frame = ttk.Frame(dialog, padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid del frame principal
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=0)  # Título
        main_frame.grid_rowconfigure(1, weight=0)  # Drive selection
        main_frame.grid_rowconfigure(2, weight=1)  # Info (expandible)
        main_frame.grid_rowconfigure(3, weight=0, minsize=60)  # Botones (altura fija)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 25))
        title_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(title_frame, text="📀 Leer Floppy HP-150", font=('Arial', 16, 'bold')).grid(row=0, column=0)
        ttk.Label(title_frame, text="Seleccionar drive y configuración", font=('Arial', 10), foreground='gray').grid(row=1, column=0, pady=(5, 0))
        
        # Selección de drive
        drive_frame = ttk.LabelFrame(main_frame, text="Seleccionar Drive", padding="15")
        drive_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        drive_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Radiobutton(drive_frame, text="🔄 Drive 0 (principal)", variable=drive_var, value=0).grid(row=0, column=0, sticky=tk.W, pady=3)
        ttk.Radiobutton(drive_frame, text="🔄 Drive 1 (secundario)", variable=drive_var, value=1).grid(row=1, column=0, sticky=tk.W, pady=3)
        
        # Información expandible
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="15")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(0, weight=1)
        
        info_text = tk.Text(
            info_frame,
            height=4,
            width=50,
            wrap=tk.WORD,
            relief=tk.FLAT,
            bg=dialog.cget('bg'),
            font=('Arial', 10),
            state=tk.DISABLED,
            cursor='arrow'
        )
        info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Insertar texto informativo
        info_text.config(state=tk.NORMAL)
        info_text.insert('1.0', 
            "🔍 Se detectará automáticamente el formato HP-150\n"
            "📀 La imagen se cargará automáticamente en la GUI\n"
            "💾 Se preguntará dónde guardarla después\n"
            "⚙️ GreaseWeazle se configurará automáticamente"
        )
        info_text.config(state=tk.DISABLED)
        
        # Frame de botones con altura fija garantizada
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        button_frame.grid_columnconfigure(1, weight=1)  # Espaciador
        
        # Separador
        separator = ttk.Separator(button_frame, orient='horizontal')
        separator.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Botones
        ttk.Button(
            button_frame, 
            text="📀 Iniciar Lectura", 
            command=lambda: start_read(),
            width=18,
            style='Accent.TButton'
        ).grid(row=1, column=0, padx=(0, 10), pady=5, ipadx=5, ipady=3)
        
        ttk.Button(
            button_frame, 
            text="❌ Cancelar", 
            command=lambda: dialog.destroy(),
            width=15
        ).grid(row=1, column=2, padx=(10, 0), pady=5, ipadx=5, ipady=3)
        
        def start_read():
            drive = drive_var.get()
            
            # Crear archivos temporales
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_name = f"floppy_drive_{drive}_{timestamp}"
            
            scp_file = os.path.join(self.temp_dir, f"{temp_name}.scp")
            img_file = os.path.join(self.temp_dir, f"{temp_name}.img")
            
            # Cerrar diálogo y mostrar progreso
            dialog.destroy()
            
            # Crear ventana de progreso con consola
            progress_window = tk.Toplevel(self.root)
            progress_window.title("📀 Leyendo Floppy desde Drive " + str(drive))
            progress_window.geometry("900x700")
            progress_window.minsize(800, 600)
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            main_frame = ttk.Frame(progress_window, padding="15")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Header con información
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(header_frame, text="📀 Lectura de Floppy HP-150", font=('Arial', 14, 'bold')).pack()
            ttk.Label(header_frame, text=f"Drive: {drive} → Temporal: {temp_name}", font=('Arial', 10)).pack(pady=(5, 0))
            ttk.Label(header_frame, text="Los archivos se cargarán automáticamente en la GUI", font=('Arial', 9), foreground='blue').pack(pady=(0, 0))
            
            # Proceso actual
            status_frame = ttk.LabelFrame(main_frame, text="Estado Actual", padding="10")
            status_frame.pack(fill=tk.X, pady=(0, 10))
            
            current_step = ttk.Label(status_frame, text="Iniciando lectura...", font=('Arial', 11, 'bold'))
            current_step.pack(anchor=tk.W)
            
            progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
            progress_bar.pack(fill=tk.X, pady=(10, 0))
            progress_bar.start()
            
            # Consola de salida - altura fija pero scrollable
            console_frame = ttk.LabelFrame(main_frame, text="Salida de GreaseWeazle", padding="10")
            console_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            
            console_text = scrolledtext.ScrolledText(
                console_frame,
                height=10,  # Altura fija más pequeña
                font=('Monaco', 9),
                wrap=tk.WORD
            )
            console_text.pack(fill=tk.BOTH, expand=True)
            
            # Frame de botones con altura fija y padding generoso
            button_frame = ttk.Frame(main_frame, padding="15")
            button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
            
            # Separador visual
            separator = ttk.Separator(button_frame, orient='horizontal')
            separator.pack(fill=tk.X, pady=(0, 15))
            
            # Variable para controlar cancelación
            cancel_requested = {'value': False}
            current_process = {'process': None}
            
            def cancel_read():
                cancel_requested['value'] = True
                if current_process['process']:
                    try:
                        current_process['process'].terminate()
                        console_text.insert(tk.END, "\n❌ Lectura cancelada por el usuario\n")
                        console_text.see(tk.END)
                    except:
                        pass
                progress_window.destroy()
            
            # Información adicional
            info_label = ttk.Label(
                button_frame, 
                text="Puedes cancelar la operación en cualquier momento",
                font=('Arial', 10),
                foreground='gray'
            )
            info_label.pack(side=tk.LEFT, pady=5)
            
            # Botón cancelar con tamaño generoso y padding
            cancel_btn = ttk.Button(
                button_frame, 
                text="❌ Cancelar Lectura", 
                command=cancel_read,
                width=25,  # Más ancho
                style='Accent.TButton'  # Estilo destacado
            )
            cancel_btn.pack(side=tk.RIGHT, padx=(20, 0), pady=5, ipadx=10, ipady=5)
            
            def on_read_complete(return_code):
                """Callback cuando termina la lectura"""
                # NO destruir la ventana automáticamente - dejar que el usuario la cierre
                progress_bar.stop()
                
                # Cambiar el botón cancelar por cerrar
                cancel_btn.config(text="✅ Cerrar", command=progress_window.destroy)
                
                if return_code == 0:
                    # Éxito - mostrar resumen y cargar imagen
                    scp_size = os.path.getsize(scp_file) if os.path.exists(scp_file) else 0
                    img_size = os.path.getsize(img_file) if os.path.exists(img_file) else 0
                    
                    success_message = (
                        f"Lectura completada exitosamente\n\n"
                        f"Archivos temporales creados:\n"
                        f"• {os.path.basename(scp_file)} ({scp_size:,} bytes) - Flujo magnético raw\n"
                        f"• {os.path.basename(img_file)} ({img_size:,} bytes) - Imagen HP-150\n\n"
                        f"La imagen se cargará automáticamente en la GUI.\n"
                        f"Después podrás guardarla donde desees."
                    )
                    
                    messagebox.showinfo("Lectura completada", success_message)
                    
                    # Cargar automáticamente la imagen sin preguntar nada
                    if os.path.exists(img_file):
                        self.load_image_file(img_file)
                        
                        # Marcar que tenemos archivos temporales pendientes
                        self.temp_scp_file = scp_file
                        self.temp_img_file = img_file
                        self.has_temp_files = True
                else:
                    messagebox.showerror(
                        "Error de Lectura", 
                        f"Error leyendo el floppy (código: {return_code})\n"
                        f"Revisa la consola para más detalles."
                    )
            
            # Ejecutar secuencia de lectura personalizada
            self.run_floppy_read_sequence(drive, scp_file, img_file, console_text, current_step, progress_bar, on_read_complete, cancel_requested, current_process)
        
    
    def write_to_floppy(self):
        """Escribir imagen actual al floppy usando GreaseWeazle"""
        # Verificar que GreaseWeazle esté configurado
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
        
        import subprocess
        
        print("[DEBUG] Iniciando write_to_floppy()")
        print(f"[DEBUG] current_image: {self.current_image}")
        
        if not self.current_image:
            print("[DEBUG] ERROR: No hay imagen cargada")
            messagebox.showwarning("Advertencia", "No hay imagen cargada para escribir")
            return
        
        print(f"[DEBUG] Verificando si el archivo existe: {self.current_image}")
        if not os.path.exists(self.current_image):
            print(f"[DEBUG] ERROR: Archivo no existe: {self.current_image}")
            messagebox.showerror("Error", f"El archivo de imagen no existe: {self.current_image}")
            return
        
        file_size = os.path.getsize(self.current_image)
        print(f"[DEBUG] Tamaño del archivo: {file_size} bytes")
        
        # Diálogo para seleccionar drive y confirmación
        dialog = tk.Toplevel(self.root)
        dialog.title("Escribir a Floppy")
        dialog.geometry("600x550")
        dialog.minsize(600, 550)  # Tamaño mínimo aumentado para mejor visibilidad
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar grid para que sea responsive
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        # Variables
        drive_var = tk.IntVar(value=0)
        verify_var = tk.BooleanVar(value=True)
        
        # Frame principal con configuración responsive
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid weights para expansión
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)  # Row de botones puede expandirse
        
        # Título y advertencia
        ttk.Label(main_frame, text="💾 Escribir a Floppy", font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        warning_frame = ttk.Frame(main_frame)
        warning_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_text = (
            "⚠️  ADVERTENCIA: Esta operación sobrescribirá\n"
            "completamente el contenido del floppy.\n"
            "¡Esta acción no se puede deshacer!"
        )
        ttk.Label(warning_frame, text=warning_text, foreground='red', font=('Arial', 10, 'bold')).pack()
        
        # Información de la imagen
        info_frame = ttk.LabelFrame(main_frame, text="Imagen a Escribir", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Archivo: {os.path.basename(self.current_image)}").pack(anchor=tk.W)
        if os.path.exists(self.current_image):
            size = os.path.getsize(self.current_image)
            ttk.Label(info_frame, text=f"Tamaño: {size:,} bytes").pack(anchor=tk.W)
        
        # Selección de drive
        drive_frame = ttk.LabelFrame(main_frame, text="Seleccionar Drive", padding="10")
        drive_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(drive_frame, text="Drive 0 (principal)", variable=drive_var, value=0).pack(anchor=tk.W)
        ttk.Radiobutton(drive_frame, text="Drive 1 (secundario)", variable=drive_var, value=1).pack(anchor=tk.W)
        
        # Opciones
        options_frame = ttk.LabelFrame(main_frame, text="Opciones", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="Verificar escritura", variable=verify_var).pack(anchor=tk.W)
        
        # Espaciador flexible para empujar botones hacia abajo
        spacer_frame = ttk.Frame(main_frame)
        spacer_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Botones con más espacio
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def start_write():
            drive = drive_var.get()
            verify = verify_var.get()
            
            # Confirmación final
            if not messagebox.askyesno(
                "Confirmación Final",
                f"¿Está SEGURO de que desea escribir al drive {drive}?\n\n"
                "Esta operación sobrescribirá todo el contenido del floppy."
            ):
                return
            
            # Cerrar diálogo y mostrar progreso
            dialog.destroy()
            
            # Crear ventana de progreso con consola
            progress_window = tk.Toplevel(self.root)
            progress_window.title("💾 Escribiendo Floppy a Drive " + str(drive))
            progress_window.geometry("600x500")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            main_frame = ttk.Frame(progress_window, padding="15")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Header con información
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(header_frame, text="💾 Escritura de Floppy HP-150", font=('Arial', 14, 'bold')).pack()
            ttk.Label(header_frame, text=f"Imagen: {os.path.basename(self.current_image)} → Drive: {drive}", font=('Arial', 10)).pack(pady=(5, 0))
            
            # Proceso actual
            status_frame = ttk.LabelFrame(main_frame, text="Estado Actual", padding="10")
            status_frame.pack(fill=tk.X, pady=(0, 10))
            
            current_step = ttk.Label(status_frame, text="Paso 1: Convirtiendo IMG a SCP...", font=('Arial', 11, 'bold'))
            current_step.pack(anchor=tk.W)
            
            progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
            progress_bar.pack(fill=tk.X, pady=(10, 0))
            progress_bar.start()
            
            # Consola de salida
            console_frame = ttk.LabelFrame(main_frame, text="Salida de GreaseWeazle", padding="10")
            console_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            console_text = scrolledtext.ScrolledText(
                console_frame,
                height=15,
                font=('Monaco', 9),
                bg='#1e1e1e' if self.is_dark_mode() else '#ffffff',
                fg='#00ff00' if self.is_dark_mode() else '#000000',
                insertbackground='#00ff00' if self.is_dark_mode() else '#000000'
            )
            console_text.pack(fill=tk.BOTH, expand=True)
            
            # Botón cancelar
            cancel_frame = ttk.Frame(main_frame)
            cancel_frame.pack(fill=tk.X)
            
            # Variable para controlar cancelación
            cancel_requested = {'value': False}
            current_process = {'process': None}
            
            def cancel_write():
                cancel_requested['value'] = True
                if current_process['process']:
                    try:
                        current_process['process'].terminate()
                        console_text.insert(tk.END, "\n❌ Escritura cancelada por el usuario\n")
                        console_text.see(tk.END)
                    except:
                        pass
                progress_window.destroy()
            
            cancel_btn = ttk.Button(cancel_frame, text="❌ Cancelar", command=cancel_write)
            cancel_btn.pack(side=tk.RIGHT)
            
            def on_write_complete(return_code):
                """Callback cuando termina la escritura"""
                print(f"[DEBUG] on_write_complete llamado con return_code: {return_code}")
                
                # NO destruir la ventana automáticamente - dejar que el usuario la cierre
                progress_bar.stop()
                
                # Cambiar el botón cancelar por cerrar
                cancel_btn.config(text="✅ Cerrar", command=progress_window.destroy)
                
                if return_code == 0:
                    print(f"[DEBUG] Escritura exitosa")
                    # Éxito
                    self.set_modified(False)  # Marcar como guardado
                    messagebox.showinfo(
                        "Éxito", 
                        f"Imagen escrita exitosamente al drive {drive}\n"
                        f"El floppy está listo para usar en el HP-150"
                    )
                else:
                    print(f"[DEBUG] Error en escritura, código: {return_code}")
                    messagebox.showerror(
                        "Error de Escritura", 
                        f"Error escribiendo al floppy (código: {return_code})\n"
                        f"Revisa la consola para más detalles."
                    )
            
            # Ejecutar comando con consola en tiempo real
            # Obtener ruta del script - compatible con PyInstaller bundle
            def get_script_path():
                """Obtener ruta del script compatible con bundle y desarrollo"""
                script_name = 'write_hp150_floppy.sh'
                
                # En aplicación bundleada con PyInstaller
                if hasattr(sys, '_MEIPASS'):
                    bundle_script_path = os.path.join(sys._MEIPASS, 'scripts', script_name)
                    if os.path.exists(bundle_script_path):
                        return bundle_script_path
                
                # En desarrollo - relativo al directorio del proyecto
                current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                dev_script_path = os.path.join(current_dir, 'scripts', script_name)
                if os.path.exists(dev_script_path):
                    return dev_script_path
                
                # Búsqueda adicional en directorios comunes
                possible_paths = [
                    os.path.join(os.getcwd(), 'scripts', script_name),
                    os.path.join(os.path.dirname(sys.executable), 'scripts', script_name),
                    script_name  # En PATH
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        return path
                
                return None
            
            script_path = get_script_path()
            
            print(f"[DEBUG] Construyendo comando de escritura...")
            print(f"[DEBUG] script_path: {script_path}")
            print(f"[DEBUG] ¿Existe script?: {script_path and os.path.exists(script_path)}")
            print(f"[DEBUG] current_image: {self.current_image}")
            print(f"[DEBUG] drive: {drive}")
            print(f"[DEBUG] verify: {verify}")
            
            console_text.insert(tk.END, f"[DEBUG] Script path: {script_path}\n")
            console_text.insert(tk.END, f"[DEBUG] ¿Script existe?: {script_path and os.path.exists(script_path)}\n")
            console_text.insert(tk.END, f"[DEBUG] Directorio actual: {os.getcwd()}\n")
            
            # Si el script no existe, usar directamente GreaseWeazle
            if not script_path or not os.path.exists(script_path):
                console_text.insert(tk.END, f"⚠️ Script no encontrado, usando GreaseWeazle directamente\n")
                console_text.see(tk.END)
                self.write_directly_with_greasewazle(drive, verify, console_text, current_step, progress_bar, on_write_complete, cancel_requested, current_process)
                return
            
            cmd = [script_path, self.current_image, f'--drive={drive}', '--force']
            
            if verify:
                cmd.append('--verify')
            
            print(f"[DEBUG] Comando final: {cmd}")
            
            console_text.insert(tk.END, f"Ejecutando: {' '.join(cmd)}\n")
            console_text.see(tk.END)
            
            try:
                print(f"[DEBUG] Iniciando run_command_with_console...")
                self.run_command_with_console(cmd, console_text, current_step, progress_bar, on_write_complete, cancel_requested, current_process)
                print(f"[DEBUG] run_command_with_console iniciado")
            except Exception as e:
                print(f"[DEBUG] ERROR en run_command_with_console: {e}")
                console_text.insert(tk.END, f"ERROR iniciando comando: {e}\n")
                console_text.see(tk.END)
                on_write_complete(1)
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="💾 Escribir", command=start_write).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Cancelar", command=cancel).pack(side=tk.LEFT)
        
        return True  # Para indicar que se intentó la escritura
    
    def is_dark_mode(self):
        """Detectar si macOS está en modo oscuro"""
        if sys.platform == "darwin":
            try:
                import subprocess
                result = subprocess.run(
                    ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0 and 'Dark' in result.stdout
            except:
                return False
        return False
    
    def run_command_with_console(self, cmd, console_text, current_step, progress_bar, on_complete, cancel_requested=None, current_process=None):
        """Ejecutar comando mostrando salida en tiempo real en la consola"""
        import subprocess
        import queue
        import threading
        
        def enqueue_output(out, queue):
            for line in iter(out.readline, ''):
                queue.put(line)
            out.close()
        
        def update_console():
            try:
                while True:
                    # Verificar si fue cancelado
                    if cancel_requested and cancel_requested['value']:
                        try:
                            process.terminate()
                        except:
                            pass
                        return
                        
                    try:
                        line = q.get_nowait()
                    except queue.Empty:
                        # Verificar si el proceso ha terminado
                        if process.poll() is not None:
                            # Proceso terminado, leer cualquier salida restante con cuidado
                            try:
                                remaining_output = process.stdout.read()
                                if remaining_output:
                                    console_text.insert(tk.END, remaining_output)
                            except (ValueError, OSError):
                                pass  # El pipe ya está cerrado
                            
                            try:
                                remaining_error = process.stderr.read()
                                if remaining_error:
                                    console_text.insert(tk.END, "ERROR: " + remaining_error)
                            except (ValueError, OSError):
                                pass  # El pipe ya está cerrado
                            
                            console_text.see(tk.END)
                            progress_bar.stop()
                            
                            # Llamar callback de completación
                            on_complete(process.returncode)
                            return
                        
                        # Programar siguiente verificación
                        console_text.after(100, update_console)
                        return
                    else:
                        # Agregar línea a la consola
                        line_text = line  # Ya es string en modo texto
                        console_text.insert(tk.END, line_text)
                        console_text.see(tk.END)
                        
                        # Actualizar step según la salida específica del script
                        if "Paso 1: Leyendo disco en formato SCP" in line_text:
                            current_step.config(text="📀 Paso 1: Leyendo disco a SCP...")
                        elif "Iniciando lectura del floppy" in line_text:
                            current_step.config(text="🔄 Ejecutando GreaseWeazle...")
                        elif "Reading cylinder" in line_text or "Reading track" in line_text:
                            current_step.config(text="📀 Leyendo pistas del disco...")
                        elif "Paso 2: Convirtiendo de SCP a IMG" in line_text:
                            current_step.config(text="🔄 Paso 2: Convirtiendo SCP a IMG...")
                        elif "Conversión completada exitosamente" in line_text:
                            current_step.config(text="✅ Conversión completada!")
                        elif "Archivo creado:" in line_text:
                            current_step.config(text="✅ Archivo creado exitosamente!")
                        elif "Tamaño correcto:" in line_text:
                            current_step.config(text="✅ Proceso completado - Imagen válida!")
                        
                        # Para escritura
                        elif "Paso 1: Convirtiendo IMG a formato SCP" in line_text:
                            current_step.config(text="🔄 Paso 1: Convirtiendo IMG a SCP...")
                        elif "Conversión completada:" in line_text:
                            current_step.config(text="✅ Conversión a SCP completada!")
                        elif "Paso 2: Escribiendo formato SCP al disco" in line_text:
                            current_step.config(text="💾 Paso 2: Escribiendo SCP al disco...")
                        elif "Iniciando escritura del floppy" in line_text:
                            current_step.config(text="🔄 Ejecutando GreaseWeazle...")
                        elif "Escritura completada exitosamente" in line_text:
                            current_step.config(text="✅ Escritura completada!")
            except Exception as e:
                console_text.insert(tk.END, f"Error en consola: {e}\n")
                console_text.see(tk.END)
        
        print(f"[DEBUG] run_command_with_console iniciando...")
        print(f"[DEBUG] cmd: {cmd}")
        print(f"[DEBUG] cwd: {os.getcwd()}")
        
        try:
            # Iniciar proceso
            print(f"[DEBUG] Creando subprocess.Popen...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
                universal_newlines=True,  # Use text mode
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 with replacement characters
                bufsize=1
            )
            print(f"[DEBUG] Proceso creado con PID: {process.pid}")
            
            # Guardar proceso para cancelación
            if current_process:
                current_process['process'] = process
            
            # Cola para la salida
            q = queue.Queue()
            
            # Hilos para leer stdout y stderr
            threading.Thread(target=enqueue_output, args=(process.stdout, q), daemon=True).start()
            threading.Thread(target=enqueue_output, args=(process.stderr, q), daemon=True).start()
            
            # Iniciar actualización de consola
            update_console()
            
        except Exception as e:
            print(f"[DEBUG] EXCEPCIÓN en run_command_with_console: {e}")
            print(f"[DEBUG] Tipo de excepción: {type(e)}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            
            console_text.insert(tk.END, f"Error iniciando proceso: {e}\n")
            console_text.insert(tk.END, f"Tipo: {type(e)}\n")
            console_text.see(tk.END)
            
            try:
                progress_bar.stop()
            except:
                pass
            on_complete(1)  # Código de error
    
    def run_floppy_read_sequence(self, drive, scp_file, img_file, console_text, current_step, progress_bar, on_complete, cancel_requested, current_process):
        """Ejecutar secuencia de lectura: SCP + conversión a IMG"""
        import subprocess
        import threading
        
        def step1_read_scp():
            """Paso 1: Leer a formato SCP"""
            if cancel_requested['value']:
                return
                
            # Primero hacer reset de GreaseWeazle
            current_step.config(text="🔄 Reseteando GreaseWeazle...")
            console_text.insert(tk.END, f"Reseteando GreaseWeazle antes de lectura...\n")
            console_text.see(tk.END)
            
            try:
                # Paso 1: Configurar delays
                gw_path = self.config_manager.get_greasewazle_path()
                delays_process = subprocess.run(
                    [gw_path, 'delays', '--step', '20000'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if delays_process.returncode == 0:
                    console_text.insert(tk.END, "\u2705 Delays configurados (--step 20000)\n")
                else:
                    console_text.insert(tk.END, f"\u26a0\ufe0f Warning configurando delays: {delays_process.stderr}\n")
                
                # Paso 2: Reset
                reset_process = subprocess.run(
                    [gw_path, 'reset'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if reset_process.returncode == 0:
                    console_text.insert(tk.END, "\u2705 GreaseWeazle reseteado exitosamente\n")
                else:
                    console_text.insert(tk.END, f"\u26a0\ufe0f Warning en reset: {reset_process.stderr}\n")
                
                console_text.see(tk.END)
                
            except subprocess.TimeoutExpired:
                console_text.insert(tk.END, "⚠️ Timeout en reset - continuando...\n")
                console_text.see(tk.END)
            except Exception as e:
                console_text.insert(tk.END, f"⚠️ Error en reset: {e} - continuando...\n")
                console_text.see(tk.END)
            
            # Verificar si fue cancelado después del reset
            if cancel_requested['value']:
                return
                
            current_step.config(text="📀 Paso 1: Leyendo flujo magnético...")
            console_text.insert(tk.END, f"\nPaso 1: Leyendo desde drive {drive} a SCP...\n")
            console_text.see(tk.END)
            
            gw_path = self.config_manager.get_greasewazle_path()
            cmd = [
                gw_path, "read", 
                f"--drive={drive}", 
                "--tracks=c=0-76:h=0-1:step=1",
                "--retries=3",
                scp_file
            ]
            
            console_text.insert(tk.END, f"Comando: {' '.join(cmd)}\n")
            console_text.see(tk.END)
            
            try:
                # Usar subprocess.Popen para salida en tiempo real
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Guardar proceso para cancelación
                current_process['process'] = process
                
                # Leer salida línea por línea en tiempo real (stdout y stderr)
                import select
                import os
                
                # Configurar descriptores para select
                stdout_fd = process.stdout.fileno()
                stderr_fd = process.stderr.fileno()
                
                # Hacer los pipes no bloqueantes (compatibilidad Windows/Unix)
                try:
                    # En Unix/Linux/macOS
                    os.set_blocking(stdout_fd, False)
                    os.set_blocking(stderr_fd, False)
                except AttributeError:
                    # En Windows, os.set_blocking no existe
                    # Usar fcntl si está disponible, sino continuar sin modo no bloqueante
                    try:
                        import fcntl
                        fcntl.fcntl(stdout_fd, fcntl.F_SETFL, os.O_NONBLOCK)
                        fcntl.fcntl(stderr_fd, fcntl.F_SETFL, os.O_NONBLOCK)
                    except (ImportError, OSError):
                        # En Windows sin fcntl, usar un enfoque alternativo
                        pass
                
                while True:
                    if cancel_requested['value']:
                        try:
                            process.terminate()
                        except:
                            pass
                        return
                    
                    # Verificar si el proceso terminó
                    if process.poll() is not None:
                        # Leer cualquier salida restante
                        try:
                            remaining_stdout = process.stdout.read()
                            if remaining_stdout:
                                console_text.insert(tk.END, remaining_stdout)
                                console_text.see(tk.END)
                        except:
                            pass
                        
                        try:
                            remaining_stderr = process.stderr.read()
                            if remaining_stderr:
                                console_text.insert(tk.END, remaining_stderr)
                                console_text.see(tk.END)
                        except:
                            pass
                        break
                    
                    # Usar select para verificar si hay datos disponibles
                    try:
                        ready, _, _ = select.select([stdout_fd, stderr_fd], [], [], 0.1)
                        
                        for fd in ready:
                            if fd == stdout_fd:
                                try:
                                    output = process.stdout.readline()
                                    if output:
                                        console_text.insert(tk.END, output)
                                        console_text.see(tk.END)
                                        console_text.update_idletasks()
                                        
                                        # Actualizar progreso basado en la salida
                                        if "Reading cylinder" in output or "Reading track" in output:
                                            current_step.config(text="📀 Leyendo pistas del disco...")
                                        elif "T" in output and "H" in output and "R" in output:
                                            # Formato típico de GreaseWeazle: T0.0 R0
                                            current_step.config(text="📀 Leyendo pistas del disco...")
                                except:
                                    pass
                            
                            elif fd == stderr_fd:
                                try:
                                    error_output = process.stderr.readline()
                                    if error_output:
                                        console_text.insert(tk.END, error_output)
                                        console_text.see(tk.END)
                                        console_text.update_idletasks()
                                        
                                        # También buscar progreso en stderr
                                        if "Reading cylinder" in error_output or "Reading track" in error_output:
                                            current_step.config(text="📀 Leyendo pistas del disco...")
                                        elif "T" in error_output and "H" in error_output:
                                            current_step.config(text="📀 Leyendo pistas del disco...")
                                except:
                                    pass
                        
                        # Si no hay datos listos, dar una pequeña pausa
                        if not ready:
                            import time
                            time.sleep(0.05)
                            
                    except (select.error, OSError):
                        # Si select falla, volver al método anterior
                        try:
                            output = process.stdout.readline()
                            if output:
                                console_text.insert(tk.END, output)
                                console_text.see(tk.END)
                                console_text.update_idletasks()
                            elif process.poll() is not None:
                                break
                        except tk.TclError:
                            break  # Widget destruido
                        except:
                            pass
                
                # Verificar si fue cancelado antes de continuar
                if cancel_requested['value']:
                    return
                    
                # Obtener código de salida
                return_code = process.wait()
                
                # Leer stderr si hay
                stderr_output = process.stderr.read()
                if stderr_output:
                    try:
                        console_text.insert(tk.END, f"STDERR: {stderr_output}")
                        console_text.see(tk.END)
                    except tk.TclError:
                        pass
                
                if return_code == 0:
                    try:
                        console_text.insert(tk.END, "✅ Lectura SCP completada\n")
                        console_text.see(tk.END)
                    except tk.TclError:
                        pass
                    # Continuar con detección de formato y conversión si no fue cancelado
                    if not cancel_requested['value']:
                        threading.Thread(target=step1_5_detect_format, daemon=True).start()
                else:
                    try:
                        console_text.insert(tk.END, f"❌ Error en lectura SCP (código: {return_code})\n")
                        console_text.see(tk.END)
                    except tk.TclError:
                        pass
                    try:
                        progress_bar.stop()
                    except tk.TclError:
                        pass
                    on_complete(return_code)
                    
            except Exception as e:
                try:
                    console_text.insert(tk.END, f"❌ Error ejecutando GreaseWeazle: {e}\n")
                    console_text.see(tk.END)
                except tk.TclError:
                    # Widget ya fue destruido, no hacer nada
                    pass
                
                try:
                    progress_bar.stop()
                except tk.TclError:
                    pass
                    
                on_complete(1)
        
        def step1_5_detect_format():
            """Paso 1.5: Convertir y detectar formato HP-150 automáticamente"""
            if cancel_requested['value']:
                return
            
            current_step.config(text="🔄 Convirtiendo y detectando formato...")
            console_text.insert(tk.END, f"\nPaso 1.5: Convirtiendo SCP a IMG con ibm.scan...\n")
            console_text.see(tk.END)
            
            # Usar directamente ibm.scan que sabemos que funciona
            gw_path = self.config_manager.get_greasewazle_path()
            cmd = [
                gw_path, "convert", 
                "--format=ibm.scan",
                scp_file,
                img_file
            ]
            
            console_text.insert(tk.END, f"Comando: {' '.join(cmd)}\n")
            console_text.see(tk.END)
            
            try:
                # Usar Popen para poder cancelar el proceso
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Guardar proceso para cancelación
                current_process['process'] = process
                
                # Esperar a que termine o se cancele
                while process.poll() is None:
                    if cancel_requested['value']:
                        try:
                            process.terminate()
                            console_text.insert(tk.END, "\n❌ Conversión cancelada\n")
                            console_text.see(tk.END)
                        except:
                            pass
                        return
                    # Pequeña pausa para no consumir mucha CPU
                    import time
                    time.sleep(0.1)
                
                # Verificar si fue cancelado
                if cancel_requested['value']:
                    return
                
                # Leer salida
                stdout, stderr = process.communicate()
                
                console_text.insert(tk.END, stdout)
                if stderr:
                    console_text.insert(tk.END, f"STDERR: {stderr}")
                console_text.see(tk.END)
                
                # Verificar si la conversión fue exitosa
                if process.returncode == 0 and os.path.exists(img_file):
                    # Analizar el tamaño del archivo para detectar formato
                    img_size = os.path.getsize(img_file)
                    
                    # Definiciones de formatos HP-150 por tamaño
                    format_by_size = {
                        270336: ('hp150', 'Estándar (77 cyl, 7 sec/track)'),
                        348160: ('hp150ext', 'Extendido (85 cyl, 8 sec/track)'),
                        368640: ('hp150hd', 'Alta densidad (80 cyl, 9 sec/track)'),
                        394240: ('hp150dd', 'Doble densidad (77 cyl, 10 sec/track)')
                    }
                    
                    detected_format = 'hp150'  # Por defecto
                    format_description = 'Estándar (77 cyl, 7 sec/track)'
                    
                    # Buscar coincidencia exacta
                    if img_size in format_by_size:
                        detected_format, format_description = format_by_size[img_size]
                        console_text.insert(tk.END, f"\n🎯 Formato detectado: {detected_format}\n")
                        console_text.insert(tk.END, f"   Descripción: {format_description}\n")
                        console_text.insert(tk.END, f"   Tamaño: {img_size:,} bytes (coincidencia exacta)\n")
                    else:
                        # Buscar el más cercano
                        closest_size = min(format_by_size.keys(), key=lambda x: abs(x - img_size))
                        detected_format, format_description = format_by_size[closest_size]
                        
                        console_text.insert(tk.END, f"\n🎯 Formato detectado: {detected_format} (aproximado)\n")
                        console_text.insert(tk.END, f"   Descripción: {format_description}\n")
                        console_text.insert(tk.END, f"   Tamaño real: {img_size:,} bytes\n")
                        console_text.insert(tk.END, f"   Tamaño esperado: {closest_size:,} bytes\n")
                        console_text.insert(tk.END, f"   Diferencia: {abs(img_size - closest_size):,} bytes\n")
                    
                    console_text.see(tk.END)
                    
                    # La conversión ya está hecha, continuar al paso final
                    if not cancel_requested['value']:
                        threading.Thread(target=lambda: step2_finalize_conversion(detected_format, format_description), daemon=True).start()
                
                else:
                    console_text.insert(tk.END, f"❌ Error en conversión (código: {process.returncode})\n")
                    progress_bar.stop()
                    on_complete(process.returncode)
                
            except Exception as e:
                try:
                    console_text.insert(tk.END, f"❌ Error en conversión: {e}\n")
                    console_text.see(tk.END)
                except tk.TclError:
                    pass
                
                try:
                    progress_bar.stop()
                except tk.TclError:
                    pass
                    
                on_complete(1)
        
        def step2_finalize_conversion(detected_format, format_description):
            """Paso 2: Finalizar conversión exitosa"""
            if cancel_requested['value']:
                return
            
            current_step.config(text="✅ Finalización exitosa!")
            console_text.insert(tk.END, f"\n✅ Conversión finalizada exitosamente\n")
            console_text.insert(tk.END, f"   Formato HP-150: {detected_format}\n")
            console_text.insert(tk.END, f"   Descripción: {format_description}\n")
            console_text.see(tk.END)
            
            # Completar proceso exitosamente
            progress_bar.stop()
            on_complete(0)
        
        def step2_convert_to_img(hp150_format='hp150'):
            """Paso 2: Convertir SCP a IMG"""
            if cancel_requested['value']:
                return
                
            current_step.config(text="🔄 Paso 2: Convirtiendo a formato HP-150...")
            console_text.insert(tk.END, f"\nPaso 2: Convirtiendo SCP a IMG...\n")
            console_text.see(tk.END)
            
            # Usar GreaseWeazle con el formato detectado
            gw_path = self.config_manager.get_greasewazle_path()
            cmd = [
                gw_path, "convert", 
                f"--diskdef=hp150.diskdef:{hp150_format}",
                "--format=ibm.scan",
                scp_file,
                img_file
            ]
            
            console_text.insert(tk.END, f"Comando: {' '.join(cmd)}\n")
            console_text.see(tk.END)
            
            try:
                # Usar Popen para poder cancelar el proceso
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Guardar proceso para cancelación
                current_process['process'] = process
                
                # Esperar a que termine o se cancele
                while process.poll() is None:
                    if cancel_requested['value']:
                        try:
                            process.terminate()
                            console_text.insert(tk.END, "\n❌ Conversión cancelada\n")
                            console_text.see(tk.END)
                        except:
                            pass
                        return
                    # Pequeña pausa para no consumir mucha CPU
                    import time
                    time.sleep(0.1)
                
                # Verificar si fue cancelado
                if cancel_requested['value']:
                    return
                
                # Leer salida
                stdout, stderr = process.communicate()
                
                console_text.insert(tk.END, stdout)
                if stderr:
                    console_text.insert(tk.END, f"STDERR: {stderr}")
                console_text.see(tk.END)
                
                # Verificar si la conversión fue exitosa basándose en la salida, no solo en el código
                conversion_successful = False
                
                if process.returncode == 0:
                    conversion_successful = True
                elif "✅ Conversión completada:" in stdout:
                    # A veces el proceso devuelve código != 0 pero la conversión fue exitosa
                    conversion_successful = True
                    console_text.insert(tk.END, "⚠️ Warning: Código de salida no-cero pero conversión exitosa\n")
                
                if conversion_successful:
                    console_text.insert(tk.END, "✅ Conversión HP-150 completada\n")
                    current_step.config(text="✅ Proceso completado exitosamente!")
                    progress_bar.stop()
                    on_complete(0)  # Forzar éxito si la conversión fue exitosa
                else:
                    console_text.insert(tk.END, f"❌ Error en conversión (código: {process.returncode})\n")
                    progress_bar.stop()
                    on_complete(process.returncode)
                
            except Exception as e:
                try:
                    console_text.insert(tk.END, f"❌ Error en conversión: {e}\n")
                    console_text.see(tk.END)
                except tk.TclError:
                    # Widget ya fue destruido, no hacer nada
                    pass
                
                try:
                    progress_bar.stop()
                except tk.TclError:
                    pass
                    
                on_complete(1)
        
        # Iniciar proceso en hilo separado
        threading.Thread(target=step1_read_scp, daemon=True).start()
    
    def load_image_file(self, filename):
        """Cargar archivo de imagen (usado internamente después de leer floppy)"""
        try:
            # Usar la función open_image_file existente pero sin diálogo
            self.current_image = filename
            self.fat_handler = HP150FAT(filename)
            self.refresh_file_list()
            self.set_modified(False)
            self.update_status(f"Imagen cargada: {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando imagen: {e}")
            self.current_image = None
            self.fat_handler = None
    
    def save_floppy_project(self, scp_file, img_file):
        """Guardar proyecto de floppy (archivos SCP e IMG) permanentemente"""
        from tkinter import filedialog
        from datetime import datetime
        import shutil
        import re
        
        # Solicitar directorio y nombre del proyecto
        output_dir = filedialog.askdirectory(
            title="Seleccionar carpeta para guardar el proyecto",
            initialdir=os.path.expanduser("~/Desktop")
        )
        
        if not output_dir:
            return
        
        # Pedir nombre del proyecto
        project_name = tk.simpledialog.askstring(
            "Nombre del proyecto",
            "Ingrese un nombre para este proyecto de floppy:",
            initialvalue=f"floppy_project_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )
        
        if not project_name:
            return
            
        # Validar nombre del proyecto (quitar caracteres especiales)
        project_name = re.sub(r'[^\w\-_]', '_', project_name)
        
        # Crear carpeta del proyecto
        project_folder = os.path.join(output_dir, project_name)
        
        try:
            if os.path.exists(project_folder):
                if not messagebox.askyesno(
                    "Carpeta existe", 
                    f"La carpeta '{project_name}' ya existe. ¿Sobrescribir?"
                ):
                    return
            else:
                os.makedirs(project_folder, exist_ok=True)
            
            # Copiar archivos
            final_scp_file = os.path.join(project_folder, f"{project_name}.scp")
            final_img_file = os.path.join(project_folder, f"{project_name}.img")
            
            shutil.copy2(scp_file, final_scp_file)
            shutil.copy2(img_file, final_img_file)
            
            # Actualizar la imagen actual para apuntar al archivo permanente
            self.current_image = final_img_file
            
            # Crear archivo README con información
            readme_file = os.path.join(project_folder, "README.txt")
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"Proyecto de Floppy HP-150\n")
                f.write(f"========================\n\n")
                f.write(f"Creado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Proyecto: {project_name}\n\n")
                f.write(f"Archivos:\n")
                f.write(f"• {project_name}.scp - Flujo magnético raw de GreaseWeazle\n")
                f.write(f"  (Para análisis avanzado o re-conversión)\n\n")
                f.write(f"• {project_name}.img - Imagen HP-150 convertida\n")
                f.write(f"  (Para uso normal en la GUI o escritura a floppy)\n\n")
                f.write(f"Para cargar en la GUI:\n")
                f.write(f"  python3 run_gui.py --extended\n")
                f.write(f"  Archivo → Abrir → {project_name}.img\n")
            
            # Obtener tamaños
            scp_size = os.path.getsize(final_scp_file)
            img_size = os.path.getsize(final_img_file)
            
            success_message = (
                f"Proyecto guardado exitosamente:\n\n"
                f"Carpeta: {project_folder}\n\n"
                f"Archivos creados:\n"
                f"• {project_name}.scp ({scp_size:,} bytes)\n"
                f"• {project_name}.img ({img_size:,} bytes)\n"
                f"• README.txt (información del proyecto)\n\n"
                f"La imagen permanente se ha cargado en la GUI."
            )
            
            messagebox.showinfo("Proyecto guardado", success_message)
            
            # Marcar que ya no hay archivos temporales pendientes
            self.has_temp_files = False
            self.temp_scp_file = None
            self.temp_img_file = None
            
            # Marcar imagen como no modificada ya que se guardó
            self.set_modified(False)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando proyecto: {e}")
    
    def save_img_only(self, img_file):
        """Guardar solo la imagen HP-150 (sin archivo SCP)"""
        from tkinter import filedialog
        import shutil
        
        # Solicitar dónde guardar la imagen
        output_file = filedialog.asksaveasfilename(
            title="Guardar imagen HP-150",
            defaultextension=".img",
            filetypes=[
                ("Imágenes HP-150", "*.img"),
                ("Todos los archivos", "*.*")
            ],
            initialdir=os.path.expanduser("~/Desktop"),
            initialfile="floppy_hp150.img"
        )
        
        if not output_file:
            return
        
        try:
            # Copiar archivo
            shutil.copy2(img_file, output_file)
            
            # Actualizar la imagen actual para apuntar al archivo permanente
            self.current_image = output_file
            
            # Obtener tamaño
            img_size = os.path.getsize(output_file)
            
            success_message = (
                f"Imagen guardada exitosamente:\n\n"
                f"Archivo: {output_file}\n"
                f"Tamaño: {img_size:,} bytes\n\n"
                f"La imagen permanente se ha cargado en la GUI."
            )
            
            messagebox.showinfo("Imagen guardada", success_message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando imagen: {e}")
    
    def write_directly_with_greasewazle(self, drive, verify, console_text, current_step, progress_bar, on_write_complete, cancel_requested, current_process):
        """Escribir directamente con GreaseWeazle sin usar script"""
        import subprocess
        import threading
        import tempfile
        
        def write_process():
            try:
                # Paso 1: Convertir IMG a SCP
                current_step.config(text="🔄 Paso 1: Convirtiendo IMG a SCP...")
                console_text.insert(tk.END, "Paso 1: Convirtiendo IMG a formato SCP\n")
                console_text.see(tk.END)
                
                # Crear archivo SCP temporal
                temp_scp = tempfile.mktemp(suffix='.scp', dir=self.temp_dir)
                
                gw_path = self.config_manager.get_greasewazle_path()
                convert_cmd = [
                    gw_path, "convert",
                    "--format=ibm.scan", 
                    self.current_image,
                    temp_scp
                ]
                
                console_text.insert(tk.END, f"Comando: {' '.join(convert_cmd)}\n")
                console_text.see(tk.END)
                
                # Ejecutar conversión
                convert_process = subprocess.run(
                    convert_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if convert_process.returncode != 0:
                    console_text.insert(tk.END, f"❌ Error en conversión: {convert_process.stderr}\n")
                    on_write_complete(convert_process.returncode)
                    return
                
                console_text.insert(tk.END, "✅ Conversión a SCP completada\n")
                console_text.see(tk.END)
                
                if cancel_requested['value']:
                    return
                
                # Paso 2: Escribir SCP al floppy
                current_step.config(text="💾 Paso 2: Escribiendo al floppy...")
                console_text.insert(tk.END, f"\nPaso 2: Escribiendo SCP al drive {drive}\n")
                console_text.see(tk.END)
                
                write_cmd = [
                    gw_path, "write",
                    f"--drive={drive}",
                    "--force",
                    temp_scp
                ]
                
                if verify:
                    write_cmd.append("--verify")
                
                console_text.insert(tk.END, f"Comando: {' '.join(write_cmd)}\n")
                console_text.see(tk.END)
                
                # Ejecutar escritura
                write_process = subprocess.Popen(
                    write_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    universal_newlines=True
                )
                
                current_process['process'] = write_process
                
                # Leer salida en tiempo real
                while True:
                    if cancel_requested['value']:
                        try:
                            write_process.terminate()
                        except:
                            pass
                        return
                    
                    output = write_process.stdout.readline()
                    if output:
                        console_text.insert(tk.END, output)
                        console_text.see(tk.END)
                        
                        # Actualizar progreso
                        if "Writing cylinder" in output or "Writing track" in output:
                            current_step.config(text="💾 Escribiendo pistas al disco...")
                    
                    # Verificar si el proceso terminó
                    if write_process.poll() is not None:
                        # Leer salida restante
                        remaining_output = write_process.stdout.read()
                        if remaining_output:
                            console_text.insert(tk.END, remaining_output)
                        
                        remaining_error = write_process.stderr.read()
                        if remaining_error:
                            console_text.insert(tk.END, f"STDERR: {remaining_error}")
                        
                        console_text.see(tk.END)
                        break
                
                # Limpiar archivo temporal
                try:
                    if os.path.exists(temp_scp):
                        os.remove(temp_scp)
                except:
                    pass
                
                # Verificar resultado
                if write_process.returncode == 0:
                    console_text.insert(tk.END, "✅ Escritura completada exitosamente\n")
                    current_step.config(text="✅ Escritura completada!")
                else:
                    console_text.insert(tk.END, f"❌ Error en escritura (código: {write_process.returncode})\n")
                
                on_write_complete(write_process.returncode)
                
            except subprocess.TimeoutExpired:
                console_text.insert(tk.END, "❌ Timeout en operación\n")
                on_write_complete(1)
            except Exception as e:
                console_text.insert(tk.END, f"❌ Error: {e}\n")
                on_write_complete(1)
        
        # Ejecutar en hilo separado
        threading.Thread(target=write_process, daemon=True).start()
    
    def show_greasewazle_config(self):
        """Mostrar diálogo de configuración de GreaseWeazle"""
        chosen_path = show_greasewazle_config(self.root, self.config_manager)
        if chosen_path:
            messagebox.showinfo(
                "Configuración actualizada",
                f"GreaseWeazle configurado en:\n{chosen_path}\n\nYa puedes usar las funciones de lectura y escritura de floppy."
            )

def main():
    """Función principal para la versión extendida"""
    root = tk.Tk()
    app = HP150ImageManagerExtended(root)
    root.mainloop()

if __name__ == "__main__":
    main()
