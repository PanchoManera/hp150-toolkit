#!/usr/bin/env python3
"""
HP-150 Image Manager GUI
Una interfaz gráfica para manipular imágenes de disco HP-150
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import sys
import threading
from pathlib import Path

# Importar nuestros módulos
from src.tools.hp150_fat import HP150FAT
from .config_manager import ConfigManager
from .greasewazle_config_dialog import show_greasewazle_config

class HP150ImageManager:
    def __init__(self, root):
        self.root = root
        self.root.title("HP-150 Image Manager")
        self.root.geometry("1000x700")
        
        # Configuraciones específicas de macOS
        if sys.platform == "darwin":
            # Configurar para ventana nativa de macOS
            try:
                # Intentar configurar la ventana como nativa de macOS
                self.root.tk.call('::tk::unsupported::MacWindowStyle', 'style', self.root._w, 'documentProc')
            except:
                pass
            
            # Configurar la barra de menú para macOS (opcional)
            try:
                from tkinter import Menu
                menubar = Menu(self.root)
                self.root.config(menu=menubar)
                
                # Menú de aplicación (aparecerá en la barra de menú del sistema)
                app_menu = Menu(menubar, name='apple')
                menubar.add_cascade(menu=app_menu)
                app_menu.add_command(label='Acerca de HP-150 Manager')
                app_menu.add_separator()
                
                # Menú Archivo
                file_menu = Menu(menubar, tearoff=0)
                menubar.add_cascade(label="Archivo", menu=file_menu)
                file_menu.add_command(label="Abrir...", command=self.open_image, accelerator="Cmd+O")
                file_menu.add_command(label="Guardar", command=self.save_image, accelerator="Cmd+S")
                file_menu.add_command(label="Guardar Como...", command=self.save_image_as, accelerator="Shift+Cmd+S")
                file_menu.add_separator()
                file_menu.add_command(label="Cerrar", command=self.on_closing, accelerator="Cmd+W")
                
            except:
                pass
        
        # Variables
        self.current_image = None
        self.fat_handler = None
        self.modified = False
        
        # Inicializar sistema de configuración
        self.config_manager = ConfigManager()
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear interfaz
        self.create_widgets()
        
        # Configurar eventos
        self.setup_events()
    
    def setup_styles(self):
        """Configurar estilos para la interfaz - macOS nativo con soporte para modo oscuro"""
        style = ttk.Style()
        
        # Usar tema aqua nativo de macOS si está disponible
        available_themes = style.theme_names()
        if 'aqua' in available_themes:
            style.theme_use('aqua')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # Detectar modo oscuro en macOS
        is_dark_mode = self.is_dark_mode()
        
        # Fuentes nativas de macOS
        title_font = ('SF Pro Display', 18, 'bold')  # Sistema principal de macOS
        header_font = ('SF Pro Text', 13, 'bold')
        body_font = ('SF Pro Text', 11)
        mono_font = ('SF Mono', 11)
        
        # Fallbacks para sistemas sin SF Pro
        try:
            import tkinter.font as tkfont
            # Verificar si SF Pro está disponible
            test_font = tkfont.Font(family='SF Pro Display')
        except:
            # Fallback a fuentes estándar de macOS
            title_font = ('Helvetica Neue', 18, 'bold')
            header_font = ('Helvetica Neue', 13, 'bold')
            body_font = ('Helvetica Neue', 11)
            mono_font = ('Monaco', 11)
        
        # Colores adaptativos según el modo
        if is_dark_mode:
            # Colores para modo oscuro
            bg_color = '#1e1e1e'        # Fondo principal oscuro
            fg_color = '#ffffff'        # Texto principal blanco
            secondary_fg = '#b3b3b3'    # Texto secundario gris claro
            accent_color = '#0a84ff'    # Azul de sistema modo oscuro
            frame_bg = '#2a2a2a'        # Fondo de frames
            tree_bg = '#1e1e1e'         # Fondo de treeview
            tree_heading_bg = '#2a2a2a' # Encabezados de treeview
        else:
            # Colores para modo claro
            bg_color = '#f2f2f7'        # Fondo principal claro
            fg_color = '#000000'        # Texto principal negro
            secondary_fg = '#333333'    # Texto secundario gris oscuro
            accent_color = '#007aff'    # Azul de sistema modo claro
            frame_bg = '#f2f2f7'        # Fondo de frames
            tree_bg = '#ffffff'         # Fondo de treeview blanco
            tree_heading_bg = '#f2f2f7' # Encabezados de treeview
        
        # Estilos personalizados con colores de macOS
        style.configure('Title.TLabel', 
                       font=title_font,
                       foreground='#000000',  # Negro sólido para mejor contraste
                       background='#f2f2f7')  # Fondo explícito
        
        style.configure('Header.TLabel', 
                       font=header_font,
                       foreground='#000000',  # Negro sólido
                       background='#f2f2f7')
        
        style.configure('Status.TLabel', 
                       font=body_font,
                       foreground='#333333',  # Gris más oscuro para mejor legibilidad
                       background='#f2f2f7')
        
        # Colores para el treeview - estilo macOS
        style.configure('Treeview', 
                       rowheight=26,
                       font=body_font,
                       background='#ffffff',
                       foreground='#1d1d1f',
                       fieldbackground='#ffffff',
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Treeview.Heading', 
                       font=header_font,
                       background='#f2f2f7',  # Color de fondo de encabezados de macOS
                       foreground='#1d1d1f',
                       relief='flat')
        
        # Estilo para botones - más parecido a macOS
        style.configure('TButton',
                       font=body_font,
                       padding=(12, 8),
                       relief='flat')
        
        # Estilo para frames
        style.configure('TLabelFrame',
                       background='#f2f2f7',
                       relief='flat',
                       borderwidth=1)
        
        style.configure('TLabelFrame.Label',
                       font=header_font,
                       foreground='#1d1d1f',
                       background='#f2f2f7')
        
        # Configurar colores de selección para que se vean como macOS
        style.map('Treeview',
                 background=[('selected', '#007aff')],  # Azul de sistema de macOS
                 foreground=[('selected', '#ffffff')])
        
        # Aplicar colores adaptativos
        style.configure('Title.TLabel', 
                       font=title_font,
                       foreground=fg_color,
                       background=bg_color)
        
        style.configure('Header.TLabel', 
                       font=header_font,
                       foreground=fg_color,
                       background=bg_color)
        
        style.configure('Status.TLabel', 
                       font=body_font,
                       foreground=secondary_fg,
                       background=bg_color)
        
        # Colores para el treeview - adaptativos
        style.configure('Treeview', 
                       rowheight=26,
                       font=body_font,
                       background=tree_bg,
                       foreground=fg_color,
                       fieldbackground=tree_bg,
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Treeview.Heading', 
                       font=header_font,
                       background=tree_heading_bg,
                       foreground=fg_color,
                       relief='flat')
        
        # Estilo para botones - adaptativo
        style.configure('TButton',
                       font=body_font,
                       padding=(12, 8),
                       relief='flat')
        
        # Estilo para frames - adaptativo
        style.configure('TLabelFrame',
                       background=frame_bg,
                       relief='flat',
                       borderwidth=1)
        
        style.configure('TLabelFrame.Label',
                       font=header_font,
                       foreground=fg_color,
                       background=frame_bg)
        
        # Configurar colores de selección adaptativos
        style.map('Treeview',
                 background=[('selected', accent_color)],
                 foreground=[('selected', '#ffffff')])
        
        # Configurar la ventana principal con color adaptativo
        self.root.configure(bg=bg_color)
    
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
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="HP-150 Image Manager", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Panel de botones/acciones (izquierda)
        self.create_button_panel(main_frame)
        
        # Lista de archivos (centro-derecha)
        self.create_file_list(main_frame)
        
        # Panel de información (abajo)
        self.create_info_panel(main_frame)
        
        # Barra de estado
        self.create_status_bar(main_frame)
    
    def create_button_panel(self, parent):
        """Crear panel de botones a la izquierda con layout de dos columnas"""
        button_frame = ttk.LabelFrame(parent, text="Acciones", padding="10")
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # COLUMNA IZQUIERDA
        
        # Operaciones de archivo (columna izquierda)
        
        # Operaciones de archivos en imagen (columna izquierda)
        files_section = ttk.LabelFrame(button_frame, text="Archivos", padding="5")
        files_section.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 5), pady=(0, 10))
        files_section.columnconfigure(0, weight=1)
        
        self.add_btn = ttk.Button(files_section, text="➕ Agregar", command=self.add_file, state='disabled', width=14)
        self.add_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        self.edit_btn = ttk.Button(files_section, text="✏️ Editar", command=self.edit_file, state='disabled', width=14)
        self.edit_btn.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        self.extract_btn = ttk.Button(files_section, text="📤 Extraer", command=self.extract_file, state='disabled', width=14)
        self.extract_btn.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        self.extract_all_btn = ttk.Button(files_section, text="📦 Extraer Todo", command=self.extract_all_files, state='disabled', width=14)
        self.extract_all_btn.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        self.delete_btn = ttk.Button(files_section, text="🗑️ Eliminar", command=self.delete_file, state='disabled', width=14)
        self.delete_btn.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # COLUMNA DERECHA
        
        # Información y análisis (columna derecha)
        info_section = ttk.LabelFrame(button_frame, text="Información", padding="5")
        info_section.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=(5, 0), pady=(0, 10))
        info_section.columnconfigure(0, weight=1)
        
        self.info_btn = ttk.Button(info_section, text="📋 Info Detallada", command=self.show_disk_info, state='disabled', width=14)
        self.info_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        self.analyze_btn = ttk.Button(info_section, text="🔍 Analizar", command=self.analyze_image, state='disabled', width=14)
        self.analyze_btn.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
    
    def create_info_panel(self, parent):
        """Crear panel de información del disco en la parte inferior"""
        info_frame = ttk.LabelFrame(parent, text="Información del Disco", padding="10")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        info_frame.columnconfigure(1, weight=1)
        
        # Labels de información en columnas
        self.info_vars = {
            'image_name': tk.StringVar(value="Ninguna imagen cargada"),
            'total_size': tk.StringVar(value="Total: --"),
            'used_space': tk.StringVar(value="Usado: --"),
            'free_space': tk.StringVar(value="Libre: --"),
            'file_count': tk.StringVar(value="Archivos: --"),
            'modified_status': tk.StringVar(value="Sin modificar")
        }
        
        # Primera columna
        col1_frame = ttk.Frame(info_frame)
        col1_frame.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 20))
        
        ttk.Label(col1_frame, textvariable=self.info_vars['image_name'], style='Status.TLabel').pack(anchor=tk.W, pady=2)
        ttk.Label(col1_frame, textvariable=self.info_vars['file_count'], style='Status.TLabel').pack(anchor=tk.W, pady=2)
        ttk.Label(col1_frame, textvariable=self.info_vars['modified_status'], style='Status.TLabel').pack(anchor=tk.W, pady=2)
        
        # Segunda columna
        col2_frame = ttk.Frame(info_frame)
        col2_frame.grid(row=0, column=1, sticky=(tk.W, tk.N), padx=(0, 20))
        
        ttk.Label(col2_frame, textvariable=self.info_vars['total_size'], style='Status.TLabel').pack(anchor=tk.W, pady=2)
        ttk.Label(col2_frame, textvariable=self.info_vars['used_space'], style='Status.TLabel').pack(anchor=tk.W, pady=2)
        ttk.Label(col2_frame, textvariable=self.info_vars['free_space'], style='Status.TLabel').pack(anchor=tk.W, pady=2)
        
        # Tercera columna - Barra de progreso
        col3_frame = ttk.Frame(info_frame)
        col3_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N))
        col3_frame.columnconfigure(0, weight=1)
        
        ttk.Label(col3_frame, text="Uso del disco:", style='Status.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        self.space_progress = ttk.Progressbar(col3_frame, length=200, mode='determinate')
        self.space_progress.pack(fill=tk.X, pady=(0, 5))
        
        self.space_label = ttk.Label(col3_frame, text="0%", style='Status.TLabel')
        self.space_label.pack(anchor=tk.W)
    
    def create_file_list(self, parent):
        """Crear lista de archivos"""
        list_frame = ttk.LabelFrame(parent, text="Archivos en la Imagen", padding="10")
        list_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview con scrollbars
        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Configurar columnas
        columns = ('name', 'size', 'cluster', 'attributes', 'type')
        self.file_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configurar encabezados
        self.file_tree.heading('name', text='Nombre')
        self.file_tree.heading('size', text='Tamaño')
        self.file_tree.heading('cluster', text='Cluster')
        self.file_tree.heading('attributes', text='Atributos')
        self.file_tree.heading('type', text='Tipo')
        
        # Configurar anchos de columna
        self.file_tree.column('name', width=150)
        self.file_tree.column('size', width=80, anchor='e')
        self.file_tree.column('cluster', width=60, anchor='e')
        self.file_tree.column('attributes', width=80, anchor='center')
        self.file_tree.column('type', width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.file_tree.xview)
        
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind eventos
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        self.file_tree.bind('<Button-3>', self.on_file_right_click)  # Right click
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_select)  # Selection change
    
    
    def create_status_bar(self, parent):
        """Crear barra de estado"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Listo - Selecciona una imagen HP-150 para comenzar")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel')
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Indicador de modificación
        self.modified_var = tk.StringVar(value="")
        modified_label = ttk.Label(status_frame, textvariable=self.modified_var, style='Status.TLabel')
        modified_label.grid(row=0, column=1, sticky=tk.E)
    
    def setup_events(self):
        """Configurar eventos de la ventana"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Atajos de teclado - adaptar para macOS
        if sys.platform == "darwin":
            # Atajos con Cmd en macOS
            self.root.bind('<Command-o>', lambda e: self.open_image())
            self.root.bind('<Command-s>', lambda e: self.save_image())
            self.root.bind('<Command-n>', lambda e: self.add_file())
            self.root.bind('<Command-w>', lambda e: self.on_closing())
            self.root.bind('<Shift-Command-s>', lambda e: self.save_image_as())
        else:
            # Atajos con Ctrl en otros sistemas
            self.root.bind('<Control-o>', lambda e: self.open_image())
            self.root.bind('<Control-s>', lambda e: self.save_image())
            self.root.bind('<Control-n>', lambda e: self.add_file())
            self.root.bind('<Control-w>', lambda e: self.on_closing())
        
        # Atajos universales
        self.root.bind('<Delete>', lambda e: self.delete_file())
        self.root.bind('<F5>', lambda e: self.refresh_file_list())
    
    def update_status(self, message):
        """Actualizar mensaje de estado"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def set_modified(self, modified=True):
        """Marcar imagen como modificada"""
        self.modified = modified
        if modified:
            self.modified_var.set("● MODIFICADO")
            self.info_vars['modified_status'].set("Modificado - No guardado")
        else:
            self.modified_var.set("")
            self.info_vars['modified_status'].set("Sin modificar")
        
        self.update_button_states()
    
    def update_button_states(self):
        """Actualizar estado de los botones según el contexto"""
        has_image = self.fat_handler is not None
        
        # Los botones de archivo ahora están en el menú, no necesitamos actualizarlos aquí
        # Solo actualizar botones del panel de acciones
        
        # Botones que están implementados en la versión extendida
        # Los mantenemos desactivados en la versión base
        extended_state = 'disabled'  # Cambiar a 'normal' cuando esté implementado
        if hasattr(self, 'add_btn'):
            self.add_btn.config(state=extended_state)
        if hasattr(self, 'edit_btn'):
            self.edit_btn.config(state=extended_state)
        if hasattr(self, 'delete_btn'):
            self.delete_btn.config(state=extended_state)
        if hasattr(self, 'extract_btn'):
            self.extract_btn.config(state=extended_state)
        if hasattr(self, 'extract_all_btn'):
            self.extract_all_btn.config(state=extended_state)
        if hasattr(self, 'info_btn'):
            self.info_btn.config(state='disabled')  # Info detallada no implementado
        if hasattr(self, 'analyze_btn'):
            self.analyze_btn.config(state=extended_state)
    
    def update_info_panel(self):
        """Actualizar panel de información"""
        if not self.fat_handler:
            return
        
        try:
            info = self.fat_handler.get_disk_info()
            files = self.fat_handler.list_files()
            
            # Actualizar información
            if self.current_image:
                self.info_vars['image_name'].set(f"Imagen: {os.path.basename(self.current_image)}")
            
            self.info_vars['total_size'].set(f"Total: {info['total_size']:,} bytes")
            
            used_space = info['total_size'] - info['free_space']
            self.info_vars['used_space'].set(f"Usado: {used_space:,} bytes")
            self.info_vars['free_space'].set(f"Libre: {info['free_space']:,} bytes")
            
            # Filtrar archivos de volumen
            file_count = len([f for f in files if not f.is_volume])
            self.info_vars['file_count'].set(f"Archivos: {file_count}")
            
            # Actualizar barra de progreso
            usage_percent = (used_space / info['total_size']) * 100 if info['total_size'] > 0 else 0
            self.space_progress['value'] = usage_percent
            self.space_label.config(text=f"{usage_percent:.1f}%")
            
            # Cambiar color según uso
            if usage_percent > 90:
                self.space_progress.configure(style='Danger.Horizontal.TProgressbar')
            elif usage_percent > 75:
                self.space_progress.configure(style='Warning.Horizontal.TProgressbar')
            else:
                self.space_progress.configure(style='TProgressbar')
                
        except Exception as e:
            self.update_status(f"Error actualizando información: {e}")
    
    def refresh_file_list(self):
        """Actualizar lista de archivos"""
        if not self.fat_handler:
            return
        
        # Limpiar lista actual
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        try:
            files = self.fat_handler.list_files()
            
            for file_entry in files:
                # Determinar tipo de archivo
                if file_entry.is_volume:
                    file_type = "Volumen"
                elif file_entry.is_directory:
                    file_type = "Directorio"
                elif file_entry.ext.upper() in ['EXE', 'COM']:
                    file_type = "Ejecutable"
                elif file_entry.ext.upper() in ['SYS']:
                    file_type = "Sistema"
                elif file_entry.ext.upper() in ['BAT']:
                    file_type = "Batch"
                elif file_entry.ext.upper() in ['TXT', 'MSG']:
                    file_type = "Texto"
                else:
                    file_type = "Archivo"
                
                # Crear string de atributos
                attrs = []
                if file_entry.attr & 0x01: attrs.append("R")  # Read-only
                if file_entry.attr & 0x02: attrs.append("H")  # Hidden
                if file_entry.attr & 0x04: attrs.append("S")  # System
                if file_entry.attr & 0x08: attrs.append("V")  # Volume
                if file_entry.attr & 0x10: attrs.append("D")  # Directory
                if file_entry.attr & 0x20: attrs.append("A")  # Archive
                attr_str = "".join(attrs) if attrs else "-"
                
                # Insertar en el tree
                self.file_tree.insert('', 'end', values=(
                    file_entry.full_name,
                    f"{file_entry.size:,}",
                    file_entry.cluster,
                    attr_str,
                    file_type
                ))
            
            self.update_info_panel()
            self.update_status(f"Lista actualizada - {len(files)} archivos")
            
        except Exception as e:
            self.update_status(f"Error actualizando lista: {e}")
            messagebox.showerror("Error", f"Error actualizando lista de archivos:\n{e}")
    
    # Métodos de archivo (implementaremos en la siguiente parte)
    def open_image(self):
        """Abrir imagen HP-150"""
        if self.modified:
            if not messagebox.askyesno("Imagen Modificada", 
                                     "Hay cambios sin guardar. ¿Continuar sin guardar?"):
                return
        
        filename = filedialog.askopenfilename(
            title="Abrir Imagen HP-150",
            filetypes=[
                ("Imágenes HP-150", "*.img"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if filename:
            self.load_image(filename)
    
    def load_image(self, filename):
        """Cargar imagen especificada"""
        try:
            self.update_status("Cargando imagen...")
            self.fat_handler = HP150FAT(filename)
            self.current_image = filename
            self.set_modified(False)
            
            self.refresh_file_list()
            self.update_button_states()
            self.update_status(f"Imagen cargada: {os.path.basename(filename)}")
            
        except Exception as e:
            self.update_status("Error cargando imagen")
            messagebox.showerror("Error", f"Error cargando imagen:\n{e}")
            self.fat_handler = None
            self.current_image = None
            self.update_button_states()
    
    def save_image(self):
        """Guardar imagen actual"""
        if not self.current_image:
            messagebox.showwarning("Advertencia", "No hay imagen cargada para guardar")
            return
        
        if not self.modified:
            messagebox.showinfo("Información", "No hay cambios para guardar")
            return
        
        try:
            self.update_status("Guardando imagen...")
            # Aquí implementaremos el guardado real
            self.set_modified(False)
            self.update_status("Imagen guardada exitosamente")
            messagebox.showinfo("Éxito", "Imagen guardada exitosamente")
            
        except Exception as e:
            self.update_status("Error guardando imagen")
            messagebox.showerror("Error", f"Error guardando imagen:\n{e}")
    
    def save_image_as(self):
        """Guardar imagen como archivo nuevo"""
        if not self.current_image:
            messagebox.showwarning("Advertencia", "No hay imagen cargada")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Guardar Imagen Como",
            defaultextension=".img",
            filetypes=[
                ("Imágenes HP-150", "*.img"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if filename:
            try:
                self.update_status("Guardando imagen como...")
                
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
    
    # Métodos de archivos (implementaremos después)
    def add_file(self):
        """Agregar archivo a la imagen"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def edit_file(self):
        """Editar archivo seleccionado"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def delete_file(self):
        """Eliminar archivo seleccionado"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def extract_file(self):
        """Extraer archivo seleccionado"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def extract_all_files(self):
        """Extraer todos los archivos"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def analyze_image(self):
        """Analizar imagen actual"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def show_disk_info(self):
        """Mostrar información detallada del disco"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def verify_integrity(self):
        """Verificar integridad de la imagen"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def repair_image(self):
        """Reparar imagen si es necesario"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def create_backup(self):
        """Crear backup de la imagen"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def restore_backup(self):
        """Restaurar desde backup"""
        messagebox.showinfo("En desarrollo", "Función en desarrollo")
    
    def on_file_double_click(self, event):
        """Manejar doble click en archivo"""
        self.edit_file()
    
    def on_file_select(self, event):
        """Manejar cambio de selección en archivo"""
        self.update_button_states()
    
    def on_file_right_click(self, event):
        """Manejar click derecho en archivo"""
        # Crear menú contextual
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Ver/Editar", command=self.edit_file)
        context_menu.add_command(label="Extraer", command=self.extract_file)
        context_menu.add_separator()
        context_menu.add_command(label="Eliminar", command=self.delete_file)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def on_closing(self):
        """Manejar cierre de la aplicación"""
        if self.modified:
            result = messagebox.askyesnocancel(
                "Imagen Modificada",
                "Hay cambios sin guardar. ¿Deseas guardar antes de salir?"
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes
                self.save_image()
        
        self.root.destroy()

def main():
    """Función principal"""
    root = tk.Tk()
    app = HP150ImageManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
