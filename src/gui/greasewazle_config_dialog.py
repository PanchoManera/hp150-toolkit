#!/usr/bin/env python3
"""
HP-150 Toolkit - GreaseWeazle Configuration Dialog
Diálogo para configurar la ruta de GreaseWeazle
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable
from .config_manager import ConfigManager

class GreaseWazleConfigDialog:
    """Diálogo para configurar GreaseWeazle"""
    
    def __init__(self, parent, config_manager: ConfigManager, callback: Optional[Callable] = None):
        self.parent = parent
        self.config_manager = config_manager
        self.callback = callback
        self.result = None
        
        # Crear ventana
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuración de GreaseWeazle")
        self.dialog.geometry("600x450")
        self.dialog.resizable(True, True)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar en el padre
        self.center_window()
        
        # Variables
        self.selected_path = tk.StringVar()
        self.manual_path = tk.StringVar()
        
        # Crear interfaz
        self.create_widgets()
        
        # Buscar candidatos automáticamente
        self.search_candidates()
        
        # Configurar eventos
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def center_window(self):
        """Centra la ventana en el padre"""
        self.dialog.update_idletasks()
        
        # Obtener dimensiones
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        # Obtener posición del padre
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calcular posición centrada
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """Crea la interfaz del diálogo"""
        # Frame principal con padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configurar grid
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Título y descripción
        title_label = ttk.Label(main_frame, 
                               text="🔧 Configuración de GreaseWeazle", 
                               style="Heading.TLabel",
                               font=("", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        desc_text = """Para usar las funciones de lectura y escritura de floppies, necesitas configurar 
la ubicación del ejecutable de GreaseWeazle (gw).

Puedes elegir una de las opciones encontradas automáticamente o especificar 
una ruta manualmente."""
        desc_label = ttk.Label(main_frame, text=desc_text, justify="left")
        desc_label.grid(row=1, column=0, sticky="w", pady=(0, 20))
        
        # Sección de detección automática
        auto_frame = ttk.LabelFrame(main_frame, text=" 🔍 Detección Automática ", padding="15")
        auto_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        auto_frame.columnconfigure(0, weight=1)
        
        # Lista de candidatos
        self.candidates_frame = ttk.Frame(auto_frame)
        self.candidates_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.candidates_frame.columnconfigure(0, weight=1)
        
        # Botón para buscar de nuevo
        refresh_btn = ttk.Button(auto_frame, text="🔄 Buscar de Nuevo", command=self.search_candidates)
        refresh_btn.grid(row=1, column=0, sticky="w")
        
        # Sección manual
        manual_frame = ttk.LabelFrame(main_frame, text=" ✏️ Configuración Manual ", padding="15")
        manual_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        manual_frame.columnconfigure(1, weight=1)
        
        ttk.Label(manual_frame, text="Ruta del ejecutable:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        path_entry = ttk.Entry(manual_frame, textvariable=self.manual_path, width=50)
        path_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        browse_btn = ttk.Button(manual_frame, text="📁 Examinar...", command=self.browse_executable)
        browse_btn.grid(row=0, column=2)
        
        # Test button para ruta manual
        test_manual_btn = ttk.Button(manual_frame, text="🧪 Probar Ruta", command=self.test_manual_path)
        test_manual_btn.grid(row=1, column=1, sticky="w", pady=(10, 0))
        
        # Frame de estado
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        
        self.status_label = ttk.Label(self.status_frame, text="", foreground="blue")
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Botones finales
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        
        # Botones a la derecha
        right_buttons = ttk.Frame(button_frame)
        right_buttons.grid(row=0, column=1, sticky="e")
        
        cancel_btn = ttk.Button(right_buttons, text="Cancelar", command=self.on_cancel)
        cancel_btn.grid(row=0, column=0, padx=(0, 10))
        
        save_btn = ttk.Button(right_buttons, text="💾 Guardar", command=self.on_save, style="Accent.TButton")
        save_btn.grid(row=0, column=1)
        
        # Configurar estilo para el botón de guardar
        try:
            style = ttk.Style()
            style.configure("Accent.TButton", font=("", 10, "bold"))
            style.configure("Heading.TLabel", font=("", 12, "bold"))
        except:
            pass
    
    def search_candidates(self):
        """Busca candidatos de GreaseWeazle"""
        self.update_status("🔍 Buscando GreaseWeazle...", "blue")
        self.dialog.update()
        
        # Limpiar candidatos anteriores
        for widget in self.candidates_frame.winfo_children():
            widget.destroy()
        
        # Buscar candidatos
        candidates = self.config_manager.find_greasewazle_candidates()
        
        if not candidates:
            no_candidates_label = ttk.Label(self.candidates_frame, 
                                           text="❌ No se encontró GreaseWeazle automáticamente.\nPor favor, especifica la ruta manualmente.", 
                                           foreground="red")
            no_candidates_label.grid(row=0, column=0, sticky="w")
            self.update_status("❌ No se encontraron candidatos automáticamente", "red")
        else:
            self.update_status(f"✅ Se encontraron {len(candidates)} candidato(s)", "green")
            
            # Crear radio buttons para cada candidato
            for i, candidate in enumerate(candidates):
                frame = ttk.Frame(self.candidates_frame)
                frame.grid(row=i, column=0, sticky="ew", pady=2)
                frame.columnconfigure(1, weight=1)
                
                # Radio button
                radio = ttk.Radiobutton(frame, 
                                      text="", 
                                      variable=self.selected_path, 
                                      value=candidate["path"])
                radio.grid(row=0, column=0, sticky="w")
                
                # Descripción
                desc_label = ttk.Label(frame, text=candidate["description"])
                desc_label.grid(row=0, column=1, sticky="w", padx=(5, 0))
                
                # Ruta (en gris más pequeño)
                path_label = ttk.Label(frame, text=candidate["path"], foreground="gray", font=("Courier", 9))
                path_label.grid(row=1, column=1, sticky="w", padx=(5, 0))
                
                # Test button
                test_btn = ttk.Button(frame, text="🧪", width=3, 
                                    command=lambda p=candidate["path"]: self.test_path(p))
                test_btn.grid(row=0, column=2, padx=(10, 0), rowspan=2)
                
                # Seleccionar el primero por defecto
                if i == 0:
                    self.selected_path.set(candidate["path"])
    
    def browse_executable(self):
        """Examinar para seleccionar ejecutable"""
        filetypes = [("Ejecutables", "*")]
        if tk.sys.platform == "win32":
            filetypes = [("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")]
        
        filename = filedialog.askopenfilename(
            title="Seleccionar ejecutable de GreaseWeazle",
            filetypes=filetypes
        )
        
        if filename:
            self.manual_path.set(filename)
    
    def test_path(self, path: str):
        """Prueba una ruta específica"""
        self.update_status(f"🧪 Probando: {path}...", "blue")
        self.dialog.update()
        
        if self.config_manager.verify_greasewazle_path(path):
            self.update_status(f"✅ GreaseWeazle funciona correctamente en: {path}", "green")
        else:
            self.update_status(f"❌ Error: No se puede ejecutar GreaseWeazle en: {path}", "red")
    
    def test_manual_path(self):
        """Prueba la ruta manual"""
        path = self.manual_path.get().strip()
        if not path:
            messagebox.showwarning("Ruta Vacía", "Por favor, especifica una ruta primero.")
            return
        
        self.test_path(path)
    
    def update_status(self, message: str, color: str = "black"):
        """Actualiza el mensaje de estado"""
        self.status_label.config(text=message, foreground=color)
    
    def on_save(self):
        """Guardar configuración"""
        # Determinar qué ruta usar
        selected_auto = self.selected_path.get().strip()
        manual = self.manual_path.get().strip()
        
        chosen_path = manual if manual else selected_auto
        
        if not chosen_path:
            messagebox.showwarning("Sin Selección", 
                                 "Por favor, selecciona una opción automática o especifica una ruta manual.")
            return
        
        # Verificar la ruta antes de guardar
        self.update_status(f"🔍 Verificando: {chosen_path}...", "blue")
        self.dialog.update()
        
        if not self.config_manager.verify_greasewazle_path(chosen_path):
            result = messagebox.askyesno("Ruta No Válida", 
                                       f"La ruta especificada no parece ser un ejecutable válido de GreaseWeazle:\n\n{chosen_path}\n\n¿Deseas guardarla de todos modos?")
            if not result:
                return
        
        # Guardar configuración
        if self.config_manager.set_greasewazle_path(chosen_path):
            self.update_status(f"✅ Configuración guardada: {chosen_path}", "green")
            self.result = chosen_path
            
            # Llamar callback si existe
            if self.callback:
                self.callback(chosen_path)
            
            # Cerrar diálogo después de un momento
            self.dialog.after(1000, self.on_close)
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración.")
    
    def on_cancel(self):
        """Cancelar diálogo"""
        self.result = None
        self.on_close()
    
    def on_close(self):
        """Cerrar diálogo"""
        self.dialog.grab_release()
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """Muestra el diálogo y retorna el resultado"""
        self.dialog.wait_window()
        return self.result


def show_greasewazle_config(parent, config_manager: ConfigManager, callback: Optional[Callable] = None) -> Optional[str]:
    """Función helper para mostrar el diálogo de configuración"""
    dialog = GreaseWazleConfigDialog(parent, config_manager, callback)
    return dialog.show()
