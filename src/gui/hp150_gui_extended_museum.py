#!/usr/bin/env python3
"""
HP-150 Image Manager GUI - Extensiones de funcionalidad
Implementaciones completas para manipulación de archivos
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, scrolledtext
import os
import sys
import struct
import threading
import tempfile
import shutil
from pathlib import Path

# Importar HP150FAT
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.tools.hp150_fat import HP150FAT

# Importar el módulo base
from src.gui.hp150_gui import HP150ImageManager
from src.gui.app_icon import APP_ICON, SPLASH_ART, get_dialog_title, get_app_banner

class HP150ImageManagerExtendedMuseum(HP150ImageManager):
    """Versión extendida del administrador con funcionalidades completas"""
    
    def __init__(self, root):
        super().__init__(root)
        
        # Variables adicionales para funcionalidades extendidas
        self.temp_dir = tempfile.mkdtemp(prefix="hp150_gui_")
        self.file_editors = {}  # Ventanas de edición abiertas
        self.has_temp_files = False  # Indica si hay archivos temporales pendientes
        self.temp_scp_file = None  # Archivo SCP temporal
        self.temp_img_file = None  # Archivo IMG temporal
        
        # Variables para el catálogo del museo
        self.museum_catalog = {}  # Catálogo de elementos del museo
        self.museum_tree = None  # Árbol del catálogo
        self.museum_click_in_progress = False  # Evitar múltiples clicks simultáneos
        
        # Configurar ventana más grande y responsiva
        self.setup_responsive_window()
        
        # Configurar cierre para limpiar archivos temporales
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_extended)
        
        # Mostrar el icono al iniciar
        print(APP_ICON)

        # Configurar icono de la ventana
        self.setup_window_icon()

        # Actualizar título
        self.root.title(get_app_banner())
        
        # Agregar botones adicionales después de que la GUI base esté construida
        self.root.after(100, self.add_floppy_buttons)
        
        # Agregar lógica de guardado correcta
        self.root.bind('<Command-s>', lambda e: self.save_action())
        
        # Cargar catálogo del museo
        self.root.after(150, self.load_museum_catalog)
        
        # Agregar panel del museo después de cargar el catálogo
        self.root.after(250, self.add_museum_panel)
        
        # Deshabilitar botones no implementados después de que la GUI esté construida
        self.root.after(300, self.disable_unimplemented_buttons)
        
        # Configurar GreaseWeazle después de inicializar
        self.root.after(350, self.reset_greaseweazle)
    
    def setup_responsive_window(self):
        """Configurar ventana responsiva más grande"""
        try:
            # Obtener dimensiones de la pantalla
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calcular tamaño de ventana (85% de la pantalla)
            window_width = int(screen_width * 0.85)
            window_height = int(screen_height * 0.85)
            
            # Asegurar tamaños mínimos
            window_width = max(window_width, 1400)
            window_height = max(window_height, 900)
            
            # Centrar ventana
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # Configurar geometría
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Tamaño mínimo
            self.root.minsize(1200, 800)
            
            print(f"[DEBUG] Ventana configurada: {window_width}x{window_height} (pantalla: {screen_width}x{screen_height})")
            
        except Exception as e:
            print(f"[WARNING] Error configurando ventana responsiva: {e}")
            # Fallback a tamaño fijo grande
            self.root.geometry("1400x900+100+100")
            self.root.minsize(1200, 800)
    
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
    
    def reset_greaseweazle(self):
        """Configurar y resetear GreaseWeazle al iniciar la GUI"""
        import subprocess
        import threading
        
        def do_reset():
            try:
                # Paso 1: Configurar delays
                print("⚙️ Configurando delays de GreaseWeazle...")
                delays_result = subprocess.run(
                    ['gw', 'delays', '--step', '20000'],
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
                    ['gw', 'reset'],
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
    
    def read_from_floppy(self):
        """Leer imagen desde floppy usando GreaseWeazle - flujo simplificado"""
        import subprocess
        from datetime import datetime
        import tempfile
        
        # Diálogo simple solo para seleccionar drive - MÁS GRANDE
        dialog = tk.Toplevel(self.root)
        dialog.title("Leer Floppy HP-150")
        dialog.geometry("500x400")
        dialog.minsize(480, 380)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar grid en la ventana principal
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        
        # Variables
        drive_var = tk.IntVar(value=0)
        
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
            
            # Configurar grid para controlar mejor los tamaños
            main_frame.grid_rowconfigure(2, weight=1)  # Consola expandible
            main_frame.grid_rowconfigure(3, weight=0, minsize=80)  # Botones tamaño fijo
            main_frame.grid_columnconfigure(0, weight=1)
            
            # Re-empaquetar usando grid en lugar de pack para mejor control
            # Header ya está empaquetado con pack, lo dejamos así
            # Status frame ya está empaquetado con pack, lo dejamos así
            
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
                progress_window.destroy()
                
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
        """Escribir imagen actual al floppy usando GreaseWeazle con detección automática de formato"""
        import subprocess
        
        print("\n" + "="*80)
        print("[DEBUG WRITE_TO_FLOPPY] INICIO DE FUNCIÓN")
        print("="*80)
        print(f"[DEBUG WRITE_TO_FLOPPY] current_image: {self.current_image}")
        print(f"[DEBUG WRITE_TO_FLOPPY] Tipo de current_image: {type(self.current_image)}")
        print(f"[DEBUG WRITE_TO_FLOPPY] Existe archivo: {os.path.exists(self.current_image) if self.current_image else 'N/A'}")
        if self.current_image:
            print(f"[DEBUG WRITE_TO_FLOPPY] Tamaño archivo: {os.path.getsize(self.current_image)} bytes")
        print("="*80)
        
        if not self.current_image:
            print("[DEBUG] ERROR: No hay imagen cargada")
            messagebox.showwarning("Advertencia", "No hay imagen cargada para escribir")
            return
        
        print(f"[DEBUG] Verificando si el archivo existe: {self.current_image}")
        if not os.path.exists(self.current_image):
            print(f"[DEBUG] ERROR: Archivo no existe: {self.current_image}")
            messagebox.showerror("Error", f"El archivo de imagen no existe: {self.current_image}")
            return
        
        # Detectar formato de la imagen
        format_info = self.detect_image_format(self.current_image)
        print(f"[DEBUG] Formato detectado: {format_info}")
        
        # Determinar script y proceso según el formato
        if format_info['type'] == 'HP150_FAT':
            script_name = 'write_hp150_floppy.sh'
            process_description = 'HP-150 FAT (256 bytes/sector)'
            print(f"[DEBUG] Usando script HP-150: {script_name}")
        elif format_info['type'] == 'PC_FAT':
            script_name = 'write_standard_floppy.sh'
            process_description = 'FAT estándar (512 bytes/sector)'
            print(f"[DEBUG] Usando script FAT estándar: {script_name}")
        else:
            print(f"[DEBUG] ERROR: Formato no soportado: {format_info['type']}")
            messagebox.showerror(
                "Formato No Soportado",
                f"No se puede escribir este tipo de imagen al floppy:\n\n"
                f"Formato: {format_info['name']}\n"
                f"Descripción: {format_info['description']}\n\n"
                f"Solo se pueden escribir imágenes FAT:\n"
                f"• HP-150 FAT (256 bytes/sector)\n"
                f"• FAT estándar (512 bytes/sector)"
            )
            return
        
        file_size = os.path.getsize(self.current_image)
        print(f"[DEBUG] Tamaño del archivo: {file_size} bytes")
        print(f"[DEBUG] Proceso a usar: {process_description}")
        
        # Diálogo para seleccionar drive y confirmación
        dialog = tk.Toplevel(self.root)
        dialog.title("Escribir a Floppy")
        dialog.geometry("500x450")
        dialog.minsize(500, 450)  # Tamaño mínimo aumentado
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        drive_var = tk.IntVar(value=0)
        verify_var = tk.BooleanVar(value=True)
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
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
        
        # Mostrar información del formato detectado
        ttk.Label(info_frame, text=f"Formato: {format_info['name']}", foreground='blue').pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Proceso: {process_description}", foreground='green').pack(anchor=tk.W)
        
        # Selección de drive
        drive_frame = ttk.LabelFrame(main_frame, text="Seleccionar Drive", padding="10")
        drive_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(drive_frame, text="Drive 0 (principal)", variable=drive_var, value=0).pack(anchor=tk.W)
        ttk.Radiobutton(drive_frame, text="Drive 1 (secundario)", variable=drive_var, value=1).pack(anchor=tk.W)
        
        # Opciones
        options_frame = ttk.LabelFrame(main_frame, text="Opciones", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="Verificar escritura", variable=verify_var).pack(anchor=tk.W)
        
        # Botones
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
                
                try:
                    progress_window.destroy()
                    print(f"[DEBUG] Ventana de progreso destruida")
                except Exception as e:
                    print(f"[DEBUG] Error destruyendo ventana: {e}")
                
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
            script_path = os.path.join(os.getcwd(), 'scripts', script_name)
            
            print("\n" + "#"*100)
            print("[DEBUG WRITE COMANDO] INFORMACIÓN COMPLETA DEL COMANDO A EJECUTAR")
            print("#"*100)
            print(f"[DEBUG WRITE COMANDO] script_name: {script_name}")
            print(f"[DEBUG WRITE COMANDO] script_path: {script_path}")
            print(f"[DEBUG WRITE COMANDO] ¿Existe script?: {os.path.exists(script_path)}")
            print(f"[DEBUG WRITE COMANDO] current_image: {self.current_image}")
            print(f"[DEBUG WRITE COMANDO] current_image tipo: {type(self.current_image)}")
            print(f"[DEBUG WRITE COMANDO] current_image longitud: {len(self.current_image) if self.current_image else 'N/A'}")
            print(f"[DEBUG WRITE COMANDO] drive: {drive}")
            print(f"[DEBUG WRITE COMANDO] drive tipo: {type(drive)}")
            print(f"[DEBUG WRITE COMANDO] verify: {verify}")
            print(f"[DEBUG WRITE COMANDO] verify tipo: {type(verify)}")
            print(f"[DEBUG WRITE COMANDO] cwd: {os.getcwd()}")
            
            # Crear comando paso a paso para debug completo
            cmd = []
            cmd.append(script_path)
            cmd.append(self.current_image)
            cmd.append(f'--drive={drive}')
            cmd.append('--force')
            
            print(f"[DEBUG WRITE COMANDO] cmd después de args básicos: {cmd}")
            print(f"[DEBUG WRITE COMANDO] cmd[0] (script): '{cmd[0]}'")
            print(f"[DEBUG WRITE COMANDO] cmd[1] (imagen): '{cmd[1]}'")
            print(f"[DEBUG WRITE COMANDO] cmd[2] (drive): '{cmd[2]}'")
            print(f"[DEBUG WRITE COMANDO] cmd[3] (force): '{cmd[3]}'")
            
            if verify:
                cmd.append('--verify')
                print(f"[DEBUG WRITE COMANDO] cmd después de verify: {cmd}")
                print(f"[DEBUG WRITE COMANDO] cmd[4] (verify): '{cmd[4]}'")
            
            print(f"\n[DEBUG WRITE COMANDO] COMANDO FINAL:")
            print(f"[DEBUG WRITE COMANDO] Comando completo: {cmd}")
            print(f"[DEBUG WRITE COMANDO] Comando como string: {' '.join(cmd)}")
            print(f"[DEBUG WRITE COMANDO] Número total de argumentos: {len(cmd)}")
            for i, arg in enumerate(cmd):
                print(f"[DEBUG WRITE COMANDO] arg[{i}]: '{arg}' (tipo: {type(arg)})")
            print("#"*100)
            
            console_text.insert(tk.END, f"[DEBUG] Script path: {script_path}\n")
            console_text.insert(tk.END, f"[DEBUG] ¿Script existe?: {os.path.exists(script_path)}\n")
            console_text.insert(tk.END, f"[DEBUG] Directorio actual: {os.getcwd()}\n")
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
        
        print(f"\n" + "*"*120)
        print(f"[DEBUG RUN_COMMAND] INFORMACIÓN COMPLETA ANTES DE EJECUTAR")
        print(f"*"*120)
        print(f"[DEBUG RUN_COMMAND] cmd: {cmd}")
        print(f"[DEBUG RUN_COMMAND] cmd tipo: {type(cmd)}")
        print(f"[DEBUG RUN_COMMAND] cmd longitud: {len(cmd)}")
        print(f"[DEBUG RUN_COMMAND] cwd: {os.getcwd()}")
        
        # Verificar cada elemento del comando
        for i, arg in enumerate(cmd):
            print(f"[DEBUG RUN_COMMAND] cmd[{i}]: '{arg}' (tipo: {type(arg)}, longitud: {len(arg)})")
            if i == 0:  # Script
                print(f"[DEBUG RUN_COMMAND]   Script existe: {os.path.exists(arg)}")
                if os.path.exists(arg):
                    print(f"[DEBUG RUN_COMMAND]   Script ejecutable: {os.access(arg, os.X_OK)}")
                    print(f"[DEBUG RUN_COMMAND]   Script tamaño: {os.path.getsize(arg)} bytes")
            elif i == 1:  # Imagen
                print(f"[DEBUG RUN_COMMAND]   Imagen existe: {os.path.exists(arg)}")
                if os.path.exists(arg):
                    print(f"[DEBUG RUN_COMMAND]   Imagen tamaño: {os.path.getsize(arg)} bytes")
        
        # Verificar variables de entorno importantes
        print(f"[DEBUG RUN_COMMAND] PATH: {os.environ.get('PATH', 'No definido')}")
        print(f"[DEBUG RUN_COMMAND] PWD: {os.environ.get('PWD', 'No definido')}")
        print(f"[DEBUG RUN_COMMAND] USER: {os.environ.get('USER', 'No definido')}")
        print(f"*"*120)
        
        try:
            # Iniciar proceso
            print(f"[DEBUG RUN_COMMAND] Creando subprocess.Popen...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
                universal_newlines=True,  # Use text mode
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 with replacement characters
                bufsize=1,
                env=os.environ.copy()  # Copiar variables de entorno
            )
            print(f"[DEBUG RUN_COMMAND] Proceso creado exitosamente con PID: {process.pid}")
            
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
                
            current_step.config(text="📀 Paso 1: Leyendo flujo magnético...")
            console_text.insert(tk.END, f"Paso 1: Leyendo desde drive {drive} a SCP...\n")
            console_text.see(tk.END)
            
            cmd = [
                "gw", "read", 
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
                
                # Hacer los pipes no bloqueantes
                os.set_blocking(stdout_fd, False)
                os.set_blocking(stderr_fd, False)
                
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
                    # Continuar con paso 2 si no fue cancelado
                    if not cancel_requested['value']:
                        threading.Thread(target=step2_convert_to_img, daemon=True).start()
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
        
        def step2_convert_to_img():
            """Paso 2: Detectar formato y convertir SCP a IMG"""
            if cancel_requested['value']:
                return
                
            current_step.config(text="🔍 Paso 2: Detectando formato del disco...")
            console_text.insert(tk.END, f"\nPaso 2: Detectando formato del disco...\n")
            console_text.see(tk.END)
            
            # Detectar formato del disco desde el archivo SCP
            format_result = self.detect_scp_format(scp_file, console_text)
            
            # Desempaquetar resultado
            if isinstance(format_result, tuple):
                format_type, specific_format = format_result
            else:
                # Compatibilidad con versión anterior
                format_type = format_result
                specific_format = None
            
            if format_type == 'HP150_FAT':
                current_step.config(text="🔄 Paso 2: Convirtiendo con parser HP-150...")
                console_text.insert(tk.END, f"Formato detectado: HP-150 FAT (256 bytes/sector)\n")
                console_text.insert(tk.END, f"Usando convertidor HP-150...\n")
                console_text.see(tk.END)
                
                # Usar convertidor HP-150
                converter_path = os.path.join(os.getcwd(), "src", "converters", "scp_to_hp150_scan.py")
                cmd = ["python3", converter_path, scp_file, img_file]
                
            elif format_type == 'PC_FAT':
                # Usar formato específico detectado o fallback
                if specific_format and specific_format != 'ibm.auto':
                    format_to_use = specific_format
                    format_desc = {
                        'ibm.720': '720KB (baja densidad)',
                        'ibm.360': '360KB (baja densidad)', 
                        'ibm.1440': '1.44MB (alta densidad)'
                    }.get(specific_format, specific_format)
                else:
                    # Auto-detectar probando formatos comunes
                    format_to_use = 'ibm.720'  # Más común para época del HP-150
                    format_desc = '720KB (baja densidad) - auto-detectado'
                
                current_step.config(text=f"🔄 Paso 2: Convirtiendo {format_desc}...")
                console_text.insert(tk.END, f"Formato detectado: PC FAT {format_desc}\n")
                console_text.insert(tk.END, f"Usando convertidor GreaseWeazle con formato {format_to_use}...\n")
                console_text.see(tk.END)
                
                # Usar convertidor estándar de GreaseWeazle con formato específico
                cmd = ["gw", "convert", f"--format={format_to_use}", scp_file, img_file]
                
            else:
                # Formato no reconocido, intentar HP-150 por defecto
                current_step.config(text="⚠️ Paso 2: Formato desconocido, usando parser HP-150...")
                console_text.insert(tk.END, f"Formato no reconocido, intentando con convertidor HP-150...\n")
                console_text.see(tk.END)
                
                converter_path = os.path.join(os.getcwd(), "src", "converters", "scp_to_hp150_scan.py")
                cmd = ["python3", converter_path, scp_file, img_file]
            
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
                
                if process.returncode == 0:
                    console_text.insert(tk.END, "✅ Conversión HP-150 completada\n")
                    current_step.config(text="✅ Proceso completado exitosamente!")
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
    
    def is_compatible_image(self, image_path):
        """Verificar si una imagen es compatible con formato FAT estándar"""
        try:
            with open(image_path, 'rb') as f:
                boot_sector = f.read(512)
            
            # Verificar si es formato CS80 (incompatible)
            if len(boot_sector) >= 6 and boot_sector[2:6] == b'CS80':
                return False
            
            # Verificar BPB básico
            if len(boot_sector) < 24:
                return False
                
            # Verificar bytes por sector (debe ser 512 o compatible)
            bytes_per_sector = struct.unpack('<H', boot_sector[11:13])[0]
            if bytes_per_sector not in [256, 512]:  # HP-150 usa 256, otros usan 512
                return False
            
            # Verificar sectores por cluster
            sectors_per_cluster = boot_sector[13]
            if sectors_per_cluster == 0 or sectors_per_cluster > 128:
                return False
            
            # Verificar número de FATs
            num_fats = boot_sector[16]
            if num_fats == 0:
                return False
                
            return True
            
        except Exception as e:
            print(f"[DEBUG] Error verificando compatibilidad de {image_path}: {e}")
            return False
    
    def detect_image_format(self, image_path):
        """Detectar el formato de una imagen con información detallada"""
        try:
            with open(image_path, 'rb') as f:
                boot_sector = f.read(512)
            
            # Detectar formato CS80
            if len(boot_sector) >= 6 and boot_sector[2:6] == b'CS80':
                return {
                    'type': 'CS80',
                    'name': 'HP CS80 (Sistema de disco duro HP)',
                    'supported': False,
                    'bytes_per_sector': None,
                    'description': 'Formato especializado de HP para discos duros'
                }
            
            # Detectar otros formatos por BPB
            if len(boot_sector) >= 24:
                try:
                    bytes_per_sector = struct.unpack('<H', boot_sector[11:13])[0]
                    sectors_per_cluster = boot_sector[13]
                    num_fats = boot_sector[16]
                    
                    # Validaciones básicas
                    if bytes_per_sector in [256, 512] and sectors_per_cluster > 0 and num_fats > 0:
                        if bytes_per_sector == 256:
                            return {
                                'type': 'HP150_FAT',
                                'name': 'HP-150 FAT (256 bytes/sector)',
                                'supported': True,
                                'bytes_per_sector': 256,
                                'description': 'Formato nativo del HP-150'
                            }
                        elif bytes_per_sector == 512:
                            return {
                                'type': 'PC_FAT',
                                'name': 'FAT estándar (512 bytes/sector)',
                                'supported': True,
                                'bytes_per_sector': 512,
                                'description': 'Formato FAT estándar de PC'
                            }
                        else:
                            return {
                                'type': 'UNKNOWN_FAT',
                                'name': f'FAT no estándar ({bytes_per_sector} bytes/sector)',
                                'supported': False,
                                'bytes_per_sector': bytes_per_sector,
                                'description': 'Formato FAT con tamaño de sector no soportado'
                            }
                    else:
                        return {
                            'type': 'INVALID_BPB',
                            'name': 'BPB inválido',
                            'supported': False,
                            'bytes_per_sector': bytes_per_sector if bytes_per_sector > 0 else None,
                            'description': 'Sector de boot con parámetros inválidos'
                        }
                except struct.error:
                    pass
            
            # Si no se puede detectar el formato
            return {
                'type': 'UNKNOWN',
                'name': 'Formato desconocido',
                'supported': False,
                'bytes_per_sector': None,
                'description': 'No se pudo determinar el formato del disco'
            }
                
        except Exception:
            return {
                'type': 'ERROR',
                'name': 'Error de lectura',
                'supported': False,
                'bytes_per_sector': None,
                'description': 'Error leyendo el archivo de imagen'
            }
    
    def load_museum_catalog(self):
        """Cargar catálogo de imágenes del museo HP agrupado por formato"""
        print("[DEBUG] Cargando catálogo del museo...")
        museum_dir = os.path.join(os.getcwd(), "HP150_CONVERTED")
        
        if not os.path.exists(museum_dir):
            print(f"[DEBUG] No se encontró directorio del museo: {museum_dir}")
            return
        
        # Reinicializar catálogo como diccionario de formatos
        self.museum_catalog = {}
        total_items = 0
        total_images = 0
        
        try:
            for item in os.listdir(museum_dir):
                item_path = os.path.join(museum_dir, item)
                if os.path.isdir(item_path):
                    total_items += 1
                    
                    # Extraer información del nombre del directorio
                    parts = item.split('_')
                    year = None
                    title = item.replace('_', ' ')
                    
                    for part in parts:
                        if part.isdigit() and len(part) == 4 and part.startswith('19'):
                            year = part
                            break
                    
                    # Buscar archivos .img en este directorio
                    img_files_by_format = {}
                    
                    for img_file in os.listdir(item_path):
                        if img_file.lower().endswith('.img'):
                            img_path = os.path.join(item_path, img_file)
                            total_images += 1
                            
                            # Detectar formato
                            format_info = self.detect_image_format(img_path)
                            format_type = format_info['type']
                            
                            print(f"[DEBUG] {format_info['name']}: {item}/{img_file}")
                            
                            # Agrupar por formato
                            if format_type not in img_files_by_format:
                                img_files_by_format[format_type] = []
                            
                            img_files_by_format[format_type].append({
                                'name': img_file,
                                'path': img_path,
                                'size': os.path.getsize(img_path),
                                'format_info': format_info
                            })
                    
                    # Agregar al catálogo agrupado por formato
                    for format_type, img_files in img_files_by_format.items():
                        # Inicializar formato si no existe
                        if format_type not in self.museum_catalog:
                            format_info = img_files[0]['format_info']  # Tomar info del primer archivo
                            self.museum_catalog[format_type] = {
                                'format_info': format_info,
                                'software': {}
                            }
                        
                        # Agregar software a este formato
                        self.museum_catalog[format_type]['software'][item] = {
                            'title': title,
                            'year': year,
                            'images': img_files,
                            'path': item_path
                        }
            
            # Estadísticas
            total_software = sum(len(fmt['software']) for fmt in self.museum_catalog.values())
            supported_formats = sum(1 for fmt in self.museum_catalog.values() if fmt['format_info']['supported'])
            total_formats = len(self.museum_catalog)
            
            print(f"[DEBUG] Catálogo cargado:")
            print(f"[DEBUG]   - {total_items} directorios de software")
            print(f"[DEBUG]   - {total_images} imágenes de disco")
            print(f"[DEBUG]   - {total_formats} formatos detectados")
            print(f"[DEBUG]   - {supported_formats} formatos soportados")
            
            # Mostrar desglose por formato
            for format_type, format_data in self.museum_catalog.items():
                software_count = len(format_data['software'])
                image_count = sum(len(sw['images']) for sw in format_data['software'].values())
                supported = "✅" if format_data['format_info']['supported'] else "❌"
                print(f"[DEBUG]   {supported} {format_data['format_info']['name']}: {software_count} software, {image_count} imágenes")
            
        except Exception as e:
            print(f"[DEBUG] Error cargando catálogo: {e}")
    
    def add_museum_panel(self):
        """Agregar panel del catálogo del museo HP"""
        print("[DEBUG] Agregando panel del museo...")
        
        if not self.museum_catalog:
            print("[DEBUG] No hay catálogo del museo para mostrar")
            return
        
        # Buscar el frame principal
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
            # Reconfigurar el layout para 4 columnas balanceadas
            # Columna 0: Panel de botones (fijo)
            # Columna 1: Lista de archivos (expandible)
            # Columna 2: Separador pequeño
            # Columna 3: Museo (expandible)
            
            main_frame.columnconfigure(0, weight=0, minsize=280)   # Panel botones - tamaño fijo
            main_frame.columnconfigure(1, weight=2, minsize=400)   # Lista archivos - peso 2
            main_frame.columnconfigure(2, weight=0, minsize=10)    # Separador pequeño
            main_frame.columnconfigure(3, weight=1, minsize=320)   # Museo - peso 1
            
            # Crear panel del museo en la columna 3
            museum_frame = ttk.LabelFrame(main_frame, text="🏛️ Museo HP (Software Convertido)", padding="10")
            museum_frame.grid(row=1, column=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
            museum_frame.columnconfigure(0, weight=1)
            museum_frame.rowconfigure(1, weight=1)
            
            # Información del museo
            total_software = sum(len(fmt['software']) for fmt in self.museum_catalog.values())
            total_images = sum(sum(len(sw['images']) for sw in fmt['software'].values()) for fmt in self.museum_catalog.values())
            supported_formats = sum(1 for fmt in self.museum_catalog.values() if fmt['format_info']['supported'])
            
            info_label = ttk.Label(
                museum_frame, 
                text=f"Catálogo: {total_software} aplicaciones ({total_images} imágenes)\n{supported_formats}/{len(self.museum_catalog)} formatos soportados - Doble-click para cargar",
                font=('Arial', 9)
            )
            info_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Crear Treeview para el catálogo
            tree_frame = ttk.Frame(museum_frame)
            tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            tree_frame.columnconfigure(0, weight=1)
            tree_frame.rowconfigure(0, weight=1)
            
            # Treeview con scrollbar - altura adaptativa
            # Agregamos 'file_path' como columna oculta para guardar las rutas
            self.museum_tree = ttk.Treeview(
                tree_frame,
                columns=('year', 'disks', 'file_path'),
                show='tree headings',
                height=25  # Más alto para aprovechar el espacio
            )
            
            # Configurar columnas con mejor proporción
            self.museum_tree.heading('#0', text='Software')
            self.museum_tree.heading('year', text='Año')
            self.museum_tree.heading('disks', text='Discos')
            # file_path es una columna oculta, no necesita heading
            
            # Columnas más anchas para aprovechar el espacio
            self.museum_tree.column('#0', width=220, minwidth=180)
            self.museum_tree.column('year', width=70, minwidth=60)
            self.museum_tree.column('disks', width=80, minwidth=70)
            # Columna file_path oculta (width=0)
            self.museum_tree.column('file_path', width=0, minwidth=0, stretch=False)
            
            # Scrollbar vertical
            scrollbar_v = ttk.Scrollbar(tree_frame, orient="vertical", command=self.museum_tree.yview)
            self.museum_tree.configure(yscrollcommand=scrollbar_v.set)
            
            # Scrollbar horizontal
            scrollbar_h = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.museum_tree.xview)
            self.museum_tree.configure(xscrollcommand=scrollbar_h.set)
            
            # Grid layout
            self.museum_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
            scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
            
            # Poblar el árbol
            self.populate_museum_tree()
            
            # Eventos
            self.museum_tree.bind('<Double-1>', self.on_museum_item_double_click)
            
            print(f"[DEBUG] Panel del museo agregado exitosamente")
        else:
            print(f"[DEBUG] No se pudo encontrar el frame principal")
    
    def populate_museum_tree(self):
        """Poblar el árbol del catálogo del museo organizado por formato"""
        if not self.museum_tree:
            return
        
        print(f"[DEBUG] Poblando árbol del museo con {len(self.museum_catalog)} formatos")
        
        # Limpiar árbol existente
        for item in self.museum_tree.get_children():
            self.museum_tree.delete(item)
        
        # Ordenar formatos: soportados primero, luego por nombre
        sorted_formats = sorted(
            self.museum_catalog.items(),
            key=lambda x: (not x[1]['format_info']['supported'], x[1]['format_info']['name'])
        )
        
        for format_type, format_data in sorted_formats:
            try:
                format_info = format_data['format_info']
                software_count = len(format_data['software'])
                total_images = sum(len(sw['images']) for sw in format_data['software'].values())
                
                # Crear icono según soporte
                icon = "✅" if format_info['supported'] else "❌"
                format_name = f"{icon} {format_info['name']}"
                
                print(f"[DEBUG] Agregando formato: {format_name} ({software_count} software, {total_images} imágenes)")
                
                # Agregar nodo del formato
                format_node = self.museum_tree.insert(
                    '',
                    'end',
                    text=format_name,
                    values=('', f"{software_count} software", ''),
                    tags=('format',),
                    open=format_info['supported']  # Expandir solo formatos soportados
                )
                
                # Agregar software bajo este formato
                sorted_software = sorted(format_data['software'].items(), key=lambda x: x[1]['title'])
                
                for software_id, software_data in sorted_software:
                    title = software_data['title']
                    year = software_data['year'] or '????'
                    disk_count = len(software_data['images'])
                    
                    # Solo mostrar software de formatos soportados por defecto
                    if not format_info['supported']:
                        # Para formatos no soportados, mostrar en gris
                        software_icon = "🚫"
                        software_tags = ('software_unsupported',)
                    else:
                        software_icon = "📦"
                        software_tags = ('software',)
                    
                    print(f"[DEBUG]   - Agregando software: {title} ({disk_count} discos)")
                    
                    # Agregar nodo del software
                    software_node = self.museum_tree.insert(
                        format_node,
                        'end',
                        text=f"{software_icon} {title}",
                        values=(year, f"{disk_count} discos", ''),
                        tags=software_tags,
                        open=False
                    )
                    
                    # Agregar discos bajo el software
                    for i, img_data in enumerate(software_data['images'], 1):
                        disk_name = img_data['name']
                        size_mb = img_data['size'] / (1024 * 1024)
                        
                        # Crear nombre más descriptivo para el disco
                        disk_display_name = disk_name
                        if disk_count > 1:
                            disk_display_name = f"Disco {i}: {disk_name}"
                        
                        disk_tags = ('disk',) if format_info['supported'] else ('disk_unsupported',)
                        disk_icon = "💾" if format_info['supported'] else "🚫"
                        
                        disk_item = self.museum_tree.insert(
                            software_node,
                            'end',
                            text=f"{disk_icon} {disk_display_name}",
                            values=('', f"{size_mb:.1f}MB", img_data['path'] if format_info['supported'] else ''),
                            tags=disk_tags
                        )
                        
                        print(f"[DEBUG]     - Disco: {disk_display_name} -> {img_data['path']}")
                    
                    # Si solo hay un disco soportado, también guardar la ruta en el elemento del software
                    if disk_count == 1 and format_info['supported']:
                        # Actualizar el software con la ruta del único disco
                        self.museum_tree.item(software_node, values=(year, f"{disk_count} discos", software_data['images'][0]['path']))
                        print(f"[DEBUG]     - Software actualizado con ruta única: {software_data['images'][0]['path']}")
                    
            except Exception as e:
                print(f"[DEBUG] ERROR agregando formato {format_type}: {e}")
                import traceback
                print(f"[DEBUG] Traceback: {traceback.format_exc()}")
                continue  # Continuar con el siguiente formato
        
        # Configurar estilos adaptativos
        is_dark = self.is_dark_mode()
        
        if is_dark:
            # Colores para modo oscuro
            software_color = '#4A90E2'  # Azul más claro para modo oscuro
            disk_color = '#B0B0B0'     # Gris más claro para modo oscuro
        else:
            # Colores para modo claro
            software_color = '#0066cc'  # Azul estándar
            disk_color = '#666666'     # Gris estándar
        
        self.museum_tree.tag_configure('format', foreground=software_color, font=('Arial', 11, 'bold'))
        self.museum_tree.tag_configure('software', foreground=software_color, font=('Arial', 10, 'bold'))
        self.museum_tree.tag_configure('disk', foreground=disk_color, font=('Arial', 9))
        
        # Estilos para elementos no soportados
        unsupported_color = '#888888' if is_dark else '#CCCCCC'
        self.museum_tree.tag_configure('software_unsupported', foreground=unsupported_color, font=('Arial', 10))
        self.museum_tree.tag_configure('disk_unsupported', foreground=unsupported_color, font=('Arial', 9))
        
        print(f"[DEBUG] Árbol poblado con {len(self.museum_tree.get_children())} elementos visibles")
    
    def detect_scp_format(self, scp_file, console_text=None):
        """Detectar formato del disco desde archivo SCP usando GreaseWeazle"""
        import subprocess
        import tempfile
        import os
        
        try:
            # Primero intentar usar GreaseWeazle info para obtener información del disco
            info_cmd = ["gw", "info", scp_file]
            
            if console_text:
                console_text.insert(tk.END, f"Analizando formato con: {' '.join(info_cmd)}\n")
                console_text.see(tk.END)
                console_text.update_idletasks()
            
            result = subprocess.run(
                info_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if console_text:
                console_text.insert(tk.END, f"Salida gw info:\n{result.stdout}\n")
                if result.stderr:
                    console_text.insert(tk.END, f"Errores gw info:\n{result.stderr}\n")
                console_text.see(tk.END)
                console_text.update_idletasks()
            
            # Analizar la salida para determinar el formato
            info_output = result.stdout.lower()
            
            # Buscar pistas sobre el formato IBM/PC
            detected_format = None
            if "ibm" in info_output or "mfm" in info_output:
                # Detectar densidad específica
                if "1440" in info_output or "1.44" in info_output:
                    detected_format = 'ibm.1440'  # Alta densidad 1.44MB
                elif "720" in info_output or "0.72" in info_output:
                    detected_format = 'ibm.720'   # Baja densidad 720KB
                elif "360" in info_output or "0.36" in info_output:
                    detected_format = 'ibm.360'   # Baja densidad 360KB
                else:
                    # Formato IBM genérico, intentar detectar automáticamente
                    detected_format = 'ibm.auto'
                
                if console_text:
                    console_text.insert(tk.END, f"Detectado formato IBM/PC: {detected_format}\n")
                    console_text.see(tk.END)
                
                return ('PC_FAT', detected_format)
            
            # Si no hay información clara, intentar detectar por conversiones de prueba
            if console_text:
                console_text.insert(tk.END, "No se detectó formato IBM directo, probando conversiones...\n")
                console_text.see(tk.END)
                console_text.update_idletasks()
            
            # Crear archivo temporal para pruebas
            with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as temp_img:
                temp_img_path = temp_img.name
            
            try:
                # Lista de formatos a probar en orden de probabilidad
                formats_to_try = [
                    ('ibm.720', '720KB (baja densidad)'),    # Más común para HP-150
                    ('ibm.360', '360KB (baja densidad)'),    # También común
                    ('ibm.1440', '1.44MB (alta densidad)'),  # Menos común pero posible
                ]
                
                for format_name, format_desc in formats_to_try:
                    if console_text:
                        console_text.insert(tk.END, f"Probando conversión {format_desc}: {format_name}\n")
                        console_text.see(tk.END)
                        console_text.update_idletasks()
                    
                    convert_cmd = ["gw", "convert", f"--format={format_name}", scp_file, temp_img_path]
                    
                    result = subprocess.run(
                        convert_cmd,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0 and os.path.exists(temp_img_path):
                        # Verificar si el archivo resultante tiene estructura FAT válida
                        try:
                            with open(temp_img_path, 'rb') as f:
                                boot_sector = f.read(512)
                            
                            if len(boot_sector) >= 24:
                                bytes_per_sector = struct.unpack('<H', boot_sector[11:13])[0]
                                if bytes_per_sector == 512:
                                    if console_text:
                                        console_text.insert(tk.END, f"✅ Conversión {format_desc} exitosa - formato PC FAT detectado\n")
                                        console_text.see(tk.END)
                                    return ('PC_FAT', format_name)
                        except:
                            pass
                    else:
                        if console_text:
                            console_text.insert(tk.END, f"❌ Conversión {format_desc} falló\n")
                            console_text.see(tk.END)
                
                # Si todas las conversiones IBM fallan, asumir HP-150
                if console_text:
                    console_text.insert(tk.END, "Todas las conversiones IBM fallaron\n")
                    console_text.insert(tk.END, "Asumiendo formato HP-150 FAT\n")
                    console_text.see(tk.END)
                return ('HP150_FAT', None)
                
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(temp_img_path)
                except:
                    pass
        
        except subprocess.TimeoutExpired:
            if console_text:
                console_text.insert(tk.END, "Timeout en detección de formato - asumiendo HP-150\n")
                console_text.see(tk.END)
            return ('HP150_FAT', None)
        except Exception as e:
            if console_text:
                console_text.insert(tk.END, f"Error en detección de formato: {e}\n")
                console_text.insert(tk.END, "Asumiendo formato HP-150 FAT por defecto\n")
                console_text.see(tk.END)
            return ('HP150_FAT', None)
        
        # Por defecto, asumir HP-150
        if console_text:
            console_text.insert(tk.END, "No se pudo determinar formato - asumiendo HP-150 FAT\n")
            console_text.see(tk.END)
        return ('HP150_FAT', None)
    
    def on_museum_item_double_click(self, event):
        """Manejar doble click en elemento del museo"""
        print("[DEBUG] Doble click detectado en museo")
        
        # Evitar múltiples clicks simultáneos
        if self.museum_click_in_progress:
            print("[DEBUG] Click ya en progreso, ignorando")
            return
        
        self.museum_click_in_progress = True
        
        try:
            selected = self.museum_tree.selection()
            if not selected:
                print("[DEBUG] No hay selección")
                return
            
            item = selected[0]
            item_text = self.museum_tree.item(item, 'text')
            item_tags = self.museum_tree.item(item, 'tags')
            
            print(f"[DEBUG] Item seleccionado: {item_text}, tags: {item_tags}")
            
            # Obtener la ruta del archivo desde la columna file_path (tercera columna, índice 2)
            item_values = self.museum_tree.item(item, 'values')
            print(f"[DEBUG] item_values: {item_values}")
            
            file_path = ''
            if len(item_values) >= 3:
                file_path = item_values[2]  # file_path está en el índice 2
            
            print(f"[DEBUG] file_path inicial: '{file_path}'")
            
            if not file_path or file_path.strip() == '':
                # Si no hay ruta directa, verificar si es un elemento padre
                children = self.museum_tree.get_children(item)
                print(f"[DEBUG] Hijos encontrados: {len(children)}")
                if children:
                    # Tiene hijos, seleccionar el primero
                    child_values = self.museum_tree.item(children[0], 'values')
                    if len(child_values) >= 3:
                        file_path = child_values[2]
                    print(f"[DEBUG] file_path del primer hijo: '{file_path}'")
            
            if not file_path:
                print("[DEBUG] ERROR: No se pudo obtener file_path")
                messagebox.showwarning(
                    "Error",
                    "No se pudo determinar la ruta del archivo de imagen."
                )
                return
            
            if not os.path.exists(file_path):
                print(f"[DEBUG] ERROR: Archivo no existe: {file_path}")
                messagebox.showerror(
                    "Archivo no encontrado",
                    f"El archivo no existe:\n{file_path}"
                )
                return
            
            print(f"[DEBUG] Archivo válido encontrado: {file_path}")
            
            # Confirmar carga
            if not messagebox.askyesno(
                "Cargar desde Museo HP",
                f"¿Cargar imagen del museo?\n\n"
                f"Software: {item_text}\n"
                f"Archivo: {os.path.basename(file_path)}\n\n"
                f"Esto cerrará la imagen actual si hay una abierta."
            ):
                print("[DEBUG] Usuario canceló la carga")
                return
            
            try:
                print(f"[DEBUG] Intentando cargar imagen: {file_path}")
                
                # Cargar la imagen
                self.load_image_file(file_path)
                
                # Actualizar información en el status
                self.update_status(f"Imagen del museo cargada: {os.path.basename(file_path)}")
                
                print(f"[DEBUG] Imagen cargada exitosamente")
                
                # No mostrar diálogo adicional - la carga ya es suficiente confirmación
                
            except Exception as load_error:
                print(f"[DEBUG] ERROR cargando imagen: {load_error}")
                import traceback
                print(f"[DEBUG] Traceback: {traceback.format_exc()}")
                messagebox.showerror(
                    "Error",
                    f"Error cargando imagen del museo:\n{load_error}"
                )
                
        except Exception as e:
            print(f"[DEBUG] ERROR cargando imagen: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            messagebox.showerror(
                "Error",
                f"Error cargando imagen del museo:\n{e}"
            )
        
        finally:
            # Liberar el lock después de procesar el click
            self.museum_click_in_progress = False

def main():
    """Función principal para la versión extendida"""
    root = tk.Tk()
    app = HP150ImageManagerExtendedMuseum(root)
    root.mainloop()

if __name__ == "__main__":
    main()
