import json
import os
import datetime
import hashlib
import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler('fat_system.log'),
                       logging.StreamHandler()
                   ])

class FatFileSystem:
    def __init__(self):
        self.fatTable = []
        self.currentUser = "admin"
        self.dataDirectory = "data_blocks"
        self.fatTableFile = "fat_table.json"
        self.usersFile = "users.json"
        self.cargarTablaFat()
        self.cargarUsuarios()
        Path(self.dataDirectory).mkdir(exist_ok=True)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validar_nombre_archivo(self, nombre):
        if not nombre or not nombre.strip():
            return False, "El nombre no puede estar vacío"
        
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(car in nombre for car in caracteres_invalidos):
            return False, "El nombre contiene caracteres inválidos (/ \\ : * ? \" < > |)"
        if len(nombre) > 255:
            return False, "El nombre es demasiado largo (máximo 255 caracteres)"
        if nombre.strip() != nombre:
            return False, "El nombre no puede empezar o terminar con espacios"
        return True, "OK"
    
    def cargarTablaFat(self):
        try:
            if os.path.exists(self.fatTableFile):
                with open(self.fatTableFile, 'r', encoding='utf-8') as file:
                    datos = json.load(file)
                    # Convertir strings de fecha a objetos datetime
                    for entry in datos:
                        if 'fechaCreacion' in entry and isinstance(entry['fechaCreacion'], str):
                            try:
                                entry['fechaCreacion'] = datetime.datetime.fromisoformat(entry['fechaCreacion'])
                            except:
                                entry['fechaCreacion'] = datetime.datetime.now()
                        if 'fechaModificacion' in entry and isinstance(entry['fechaModificacion'], str):
                            try:
                                entry['fechaModificacion'] = datetime.datetime.fromisoformat(entry['fechaModificacion'])
                            except:
                                entry['fechaModificacion'] = datetime.datetime.now()
                        if 'fechaEliminacion' in entry and entry['fechaEliminacion'] and isinstance(entry['fechaEliminacion'], str):
                            try:
                                entry['fechaEliminacion'] = datetime.datetime.fromisoformat(entry['fechaEliminacion'])
                            except:
                                entry['fechaEliminacion'] = None
                    self.fatTable = datos
                logging.info("Tabla FAT cargada exitosamente")
        except Exception as e:
            logging.error(f"Error al cargar la tabla FAT: {e}")
            self.fatTable = []
    
    def guardarTablaFat(self):
        try:
            with open(self.fatTableFile, 'w', encoding='utf-8') as file:
                # Convertir datetime a string para JSON
                tabla_serializable = []
                for entry in self.fatTable:
                    entry_copy = entry.copy()
                    if 'fechaCreacion' in entry_copy and isinstance(entry_copy['fechaCreacion'], datetime.datetime):
                        entry_copy['fechaCreacion'] = entry_copy['fechaCreacion'].isoformat()
                    if 'fechaModificacion' in entry_copy and isinstance(entry_copy['fechaModificacion'], datetime.datetime):
                        entry_copy['fechaModificacion'] = entry_copy['fechaModificacion'].isoformat()
                    if 'fechaEliminacion' in entry_copy and entry_copy['fechaEliminacion'] and isinstance(entry_copy['fechaEliminacion'], datetime.datetime):
                        entry_copy['fechaEliminacion'] = entry_copy['fechaEliminacion'].isoformat()
                    else:
                        entry_copy['fechaEliminacion'] = None
                    tabla_serializable.append(entry_copy)
                
                json.dump(tabla_serializable, file, indent=2, ensure_ascii=False)
            logging.info("Tabla FAT guardada exitosamente")
        except Exception as e:
            logging.error(f"Error al guardar la tabla FAT: {e}")
            raise
    
    def cargarUsuarios(self):
        try:
            if os.path.exists(self.usersFile):
                with open(self.usersFile, 'r', encoding='utf-8') as file:
                    self.users = json.load(file)
            else:
                # Usuarios por defecto (contraseñas hasheadas)
                self.users = {
                    "admin": {"password": self.hash_password("admin123"), "rol": "admin"},
                    "usuario1": {"password": self.hash_password("123"), "rol": "user"},
                    "usuario2": {"password": self.hash_password("123"), "rol": "user"}
                }
                self.guardarUsuarios()
            logging.info("Usuarios cargados exitosamente")
        except Exception as e:
            logging.error(f"Error al cargar usuarios: {e}")
            self.users = {
                "admin": {"password": self.hash_password("admin123"), "rol": "admin"},
                "usuario1": {"password": self.hash_password("123"), "rol": "user"},
                "usuario2": {"password": self.hash_password("123"), "rol": "user"}
            }
    
    def guardarUsuarios(self):
        try:
            with open(self.usersFile, 'w', encoding='utf-8') as file:
                json.dump(self.users, file, indent=2, ensure_ascii=False)
            logging.info("Usuarios guardados exitosamente")
        except Exception as e:
            logging.error(f"Error al guardar usuarios: {e}")
            raise
    
    def crearUsuario(self, username, password, rol="user"):
        if username in self.users:
            return False, "El usuario ya existe"
        
        if len(password) < 3:
            return False, "La contraseña debe tener al menos 3 caracteres"
        
        # Validar nombre de usuario
        is_valid, msg = self.validar_nombre_archivo(username)
        if not is_valid:
            return False, f"Nombre de usuario inválido: {msg}"
        
        self.users[username] = {"password": self.hash_password(password), "rol": rol}
        self.guardarUsuarios()
        logging.info(f"Usuario '{username}' creado exitosamente")
        return True, "Usuario creado exitosamente"
    
    def verificarUsuario(self, username, password):
        if username in self.users and self.users[username]["password"] == self.hash_password(password):
            logging.info(f"Login exitoso para usuario '{username}'")
            return True, "Login exitoso"
        logging.warning(f"Intento de login fallido para usuario '{username}'")
        return False, "Usuario o contraseña incorrectos"
    
    def esAdmin(self, username):
        return username in self.users and self.users[username]["rol"] == "admin"
    
    def generarBloque(self, baseName, index):
        safe_name = "".join(c for c in baseName if c.isalnum() or c in ('_', '-')).rstrip()
        return f"{self.dataDirectory}/{safe_name}_block_{index}.json"
    
    def crearDataBlocks(self, content, baseName, chunk_size=20):
        blocks = []
        contentLength = len(content)
        
        # Validar tamaño máximo (1MB)
        if contentLength > 1024 * 1024:
            raise ValueError("El archivo es demasiado grande (máximo 1MB)")
        
        for i in range(0, contentLength, chunk_size):
            blockContent = content[i:i+chunk_size]
            blockFileName = self.generarBloque(baseName, len(blocks))
            
            blockData = {
                "datos": blockContent,
                "siguiente": self.generarBloque(baseName, len(blocks) + 1) if i + chunk_size < contentLength else "",
                "eof": i + chunk_size >= contentLength
            }
            
            try:
                with open(blockFileName, 'w', encoding='utf-8') as blockFile:
                    json.dump(blockData, blockFile, indent=2, ensure_ascii=False)
                logging.debug(f"Bloque creado: {blockFileName}")
                blocks.append(blockFileName)
            except Exception as e:
                logging.error(f"Error al crear bloque {blockFileName}: {e}")
                # Limpiar bloques creados en caso de error
                for block in blocks:
                    try:
                        if os.path.exists(block):
                            os.remove(block)
                    except:
                        pass
                raise
        
        return blocks
    
    def leerContenido(self, fileEntry):
        if not fileEntry or not fileEntry.get("archivoDatosInicial"):
            return ""
        
        content = ""
        currentBlock = fileEntry["archivoDatosInicial"]
        max_blocks = 1000  # Prevenir loops infinitos
        block_count = 0
        
        while currentBlock and block_count < max_blocks:
            try:
                if not os.path.exists(currentBlock):
                    logging.warning(f"Bloque no encontrado: {currentBlock}")
                    break
                    
                with open(currentBlock, 'r', encoding='utf-8') as blockFile:
                    blockData = json.load(blockFile)
                
                content += blockData.get("datos", "")
                
                if blockData.get("eof", False):
                    break
                
                currentBlock = blockData.get("siguiente", "")
                block_count += 1
                
            except Exception as e:
                logging.error(f"Error leyendo bloque {currentBlock}: {e}")
                break
        
        if block_count >= max_blocks:
            logging.warning("Se alcanzó el límite máximo de bloques al leer archivo")
        
        return content
    
    def borrarBloquesViejos(self, initialBlock):
        currentBlock = initialBlock
        max_blocks = 1000
        block_count = 0
        
        while currentBlock and block_count < max_blocks:
            try:
                if os.path.exists(currentBlock):
                    with open(currentBlock, 'r', encoding='utf-8') as blockFile:
                        blockData = json.load(blockFile)
                    
                    nextBlock = blockData.get("siguiente", "")
                    os.remove(currentBlock)
                    logging.debug(f"Bloque eliminado: {currentBlock}")
                    currentBlock = nextBlock
                    block_count += 1
                else:
                    break
            except Exception as e:
                logging.error(f"Error al eliminar bloque {currentBlock}: {e}")
                break
        
        if block_count >= max_blocks:
            logging.warning("Se alcanzó el límite máximo de bloques al eliminar")

class FatFileSystemGUI:
    def __init__(self, root):
        self.root = root
        self.fileSystem = FatFileSystem()
        self.current_input_frame = None
        self.statusBar = None
        self.textArea = None
        self.setup_window()
        self.mostrarLogin()
    
    def setup_window(self):
        self.root.title("Sistema de Archivos FAT")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def limpiarInputFrames(self):
        if self.current_input_frame:
            self.current_input_frame.destroy()
            self.current_input_frame = None
    
    def actualizarStatus(self, mensaje):
        if self.statusBar:
            self.statusBar.config(text=mensaje)
        logging.info(f"Status: {mensaje}")
    
    def mostrarLogin(self):
        self.limpiarVentana()
        
        loginFrame = tk.Frame(self.root)
        loginFrame.pack(expand=True, padx=50, pady=50)
        
        tk.Label(loginFrame, text="Sistema de Archivos FAT", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        tk.Label(loginFrame, text="Usuario:").pack(pady=5)
        self.usuarioEntry = tk.Entry(loginFrame, width=30, font=("Arial", 10))
        self.usuarioEntry.pack(pady=5)
        self.usuarioEntry.insert(0, "admin")
        self.usuarioEntry.focus()
        
        tk.Label(loginFrame, text="Contraseña:").pack(pady=5)
        self.passwordEntry = tk.Entry(loginFrame, width=30, show="*", font=("Arial", 10))
        self.passwordEntry.pack(pady=5)
        self.passwordEntry.insert(0, "admin123")
        
        buttonFrame = tk.Frame(loginFrame)
        buttonFrame.pack(pady=20)
        
        tk.Button(buttonFrame, text="Iniciar Sesión", 
                 command=self.iniciarSesion, bg="#4CAF50", fg="white", 
                 width=15, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="Crear Usuario", 
                 command=self.mostrarCrearUsuarioDesdeLogin, bg="#2196F3", fg="white", 
                 width=15, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        self.usuarioEntry.bind('<Return>', lambda e: self.iniciarSesion())
        self.passwordEntry.bind('<Return>', lambda e: self.iniciarSesion())
    
    def mostrarCrearUsuarioDesdeLogin(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Crear Nuevo Usuario")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text="CREAR NUEVO USUARIO", 
                font=("Arial", 14, "bold")).pack(pady=15)
        
        formFrame = tk.Frame(dialog)
        formFrame.pack(pady=15, padx=20, fill=tk.BOTH)
        
        tk.Label(formFrame, text="Nuevo Usuario:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        nuevoUserEntry = tk.Entry(formFrame, width=25, font=("Arial", 10))
        nuevoUserEntry.grid(row=0, column=1, padx=5, pady=8)
        nuevoUserEntry.focus()
        
        tk.Label(formFrame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        nuevoPassEntry = tk.Entry(formFrame, width=25, show="*", font=("Arial", 10))
        nuevoPassEntry.grid(row=1, column=1, padx=5, pady=8)
        
        tk.Label(formFrame, text="Confirmar Contraseña:").grid(row=2, column=0, padx=5, pady=8, sticky="w")
        confirmPassEntry = tk.Entry(formFrame, width=25, show="*", font=("Arial", 10))
        confirmPassEntry.grid(row=2, column=1, padx=5, pady=8)
        
        rolVar = tk.StringVar(value="user")
        tk.Label(formFrame, text="Tipo de usuario:").grid(row=3, column=0, padx=5, pady=8, sticky="w")
        rolFrame = tk.Frame(formFrame)
        rolFrame.grid(row=3, column=1, padx=5, pady=8, sticky="w")
        tk.Radiobutton(rolFrame, text="Usuario Normal", variable=rolVar, value="user").pack(anchor="w")
        tk.Radiobutton(rolFrame, text="Administrador", variable=rolVar, value="admin").pack(anchor="w")
        
        def crear():
            username = nuevoUserEntry.get().strip()
            password = nuevoPassEntry.get().strip()
            confirm_password = confirmPassEntry.get().strip()
            rol = rolVar.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Complete todos los campos")
                return
            
            if password != confirm_password:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            if len(password) < 3:
                messagebox.showerror("Error", "La contraseña debe tener al menos 3 caracteres")
                return
            
            success, mensaje = self.fileSystem.crearUsuario(username, password, rol)
            if success:
                messagebox.showinfo("Éxito", mensaje)
                dialog.destroy()
            else:
                messagebox.showerror("Error", mensaje)
        
        def cancelar():
            dialog.destroy()
        
        buttonFrame = tk.Frame(dialog)
        buttonFrame.pack(pady=20)
        
        tk.Button(buttonFrame, text="✅ Crear Usuario", command=crear, 
                 bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)
    
    def iniciarSesion(self):
        username = self.usuarioEntry.get().strip()
        password = self.passwordEntry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Complete todos los campos")
            return
        
        success, mensaje = self.fileSystem.verificarUsuario(username, password)
        if success:
            self.fileSystem.currentUser = username
            self.setupGUI()
        else:
            messagebox.showerror("Error", mensaje)
    
    def setupGUI(self):
        self.limpiarVentana()
        
        self.root.title(f"Sistema de Archivos FAT - Usuario: {self.fileSystem.currentUser}")
        
        # Frame principal
        mainFrame = tk.Frame(self.root)
        mainFrame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Información del usuario actual
        userFrame = tk.Frame(mainFrame)
        userFrame.pack(fill=tk.X, pady=5)
        
        tk.Label(userFrame, text="Usuario actual:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.userLabel = tk.Label(userFrame, text=self.fileSystem.currentUser, font=("Arial", 10))
        self.userLabel.pack(side=tk.LEFT, padx=5)
        
        if self.fileSystem.esAdmin(self.fileSystem.currentUser):
            tk.Label(userFrame, text="(Administrador)", font=("Arial", 10, "bold"), fg="red").pack(side=tk.LEFT, padx=5)
        
        tk.Button(userFrame, text="Cerrar Sesión", command=self.mostrarLogin, 
                 bg="#FF5722", fg="white", font=("Arial", 9)).pack(side=tk.RIGHT)
        
        # Botones principales
        buttonFrame = tk.Frame(mainFrame)
        buttonFrame.pack(fill=tk.X, pady=10)
        
        tk.Button(buttonFrame, text="📄 Crear Archivo", command=self.menuCrear, 
                 bg="#4CAF50", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="📋 Listar Archivos", command=self.menuListar,
                 bg="#2196F3", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="🗑️ Papelera", command=self.menuPapelera,
                 bg="#FF9800", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="🔓 Abrir Archivo", command=self.menuAbrir,
                 bg="#009688", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="✏️ Modificar Archivo", command=self.menuModificar,
                 bg="#FFC107", fg="black", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        buttonFrame2 = tk.Frame(mainFrame)
        buttonFrame2.pack(fill=tk.X, pady=5)
        
        tk.Button(buttonFrame2, text="❌ Eliminar Archivo", command=self.menuEliminar,
                 bg="#F44336", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame2, text="↩️ Recuperar Archivo", command=self.menuRecuperar,
                 bg="#9C27B0", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        if self.fileSystem.esAdmin(self.fileSystem.currentUser):
            tk.Button(buttonFrame2, text="🔐 Gestionar Permisos", command=self.menuPermisos,
                     bg="#607D8B", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
            tk.Button(buttonFrame2, text="👥 Crear Usuario", command=self.mostrarCrearUsuario,
                     bg="#795548", fg="white", width=15, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Área de texto para mostrar resultados
        self.textArea = scrolledtext.ScrolledText(mainFrame, height=25, width=100, 
                                                 font=("Consolas", 10), wrap=tk.WORD)
        self.textArea.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Status bar
        self.statusBar = tk.Label(mainFrame, text="Sistema listo", bd=1, 
                                 relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9))
        self.statusBar.pack(fill=tk.X)
        
        # Mostrar lista de archivos al iniciar
        self.menuListar()
    
    def limpiarVentana(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.statusBar = None
        self.textArea = None
        self.current_input_frame = None
    
    def limpiarTexto(self):
        if self.textArea:
            self.textArea.delete(1.0, tk.END)
    
    def mostrarTexto(self, texto):
        self.limpiarTexto()
        if self.textArea:
            self.textArea.insert(tk.END, texto)
    
    def menuCrear(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== CREAR NUEVO ARCHIVO ===\n\n")
        self.textArea.insert(tk.END, "Complete el formulario a continuación:\n\n")
        
        # Frame para entrada de datos
        self.current_input_frame = tk.Frame(self.root)
        self.current_input_frame.pack(pady=10, fill=tk.X)
        
        formFrame = tk.Frame(self.current_input_frame)
        formFrame.pack(pady=10)
        
        tk.Label(formFrame, text="📝 Nombre del archivo:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        nombreEntry = tk.Entry(formFrame, width=50, font=("Arial", 10))
        nombreEntry.grid(row=0, column=1, padx=5, pady=5)
        nombreEntry.focus()
        
        tk.Label(formFrame, text="📄 Contenido del archivo:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        contenidoText = scrolledtext.ScrolledText(formFrame, width=60, height=15, font=("Consolas", 10))
        contenidoText.grid(row=1, column=1, padx=5, pady=5)
        
        def crear():
            nombre = nombreEntry.get().strip()
            contenido = contenidoText.get(1.0, tk.END).strip()
            
            if not nombre:
                messagebox.showerror("Error", "❌ El nombre del archivo no puede estar vacío")
                return
            
            # Validar nombre de archivo
            is_valid, msg = self.fileSystem.validar_nombre_archivo(nombre)
            if not is_valid:
                messagebox.showerror("Error", f"❌ {msg}")
                return
            
            if not contenido:
                messagebox.showerror("Error", "❌ El contenido del archivo no puede estar vacío")
                return
            
            # Verificar si el archivo ya existe
            for fileEntry in self.fileSystem.fatTable:
                if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                    messagebox.showerror("Error", "❌ Ya existe un archivo con ese nombre")
                    return
            
            try:
                # Crear bloques de datos
                baseName = nombre.replace(" ", "_").lower()
                dataBlocks = self.fileSystem.crearDataBlocks(contenido, baseName)
                
                # Crear entrada en tabla FAT
                fileEntry = {
                    "nombreArchivo": nombre,
                    "archivoDatosInicial": dataBlocks[0] if dataBlocks else "",
                    "enPapelera": False,
                    "totalCaracteres": len(contenido),
                    "fechaCreacion": datetime.datetime.now(),
                    "fechaModificacion": datetime.datetime.now(),
                    "fechaEliminacion": None,
                    "owner": self.fileSystem.currentUser,
                    "permisos": {
                        "lectura": [self.fileSystem.currentUser],
                        "escritura": [self.fileSystem.currentUser]
                    }
                }
                
                self.fileSystem.fatTable.append(fileEntry)
                self.fileSystem.guardarTablaFat()
                
                self.limpiarInputFrames()
                messagebox.showinfo("Éxito", f"✅ Archivo '{nombre}' creado exitosamente\n📊 Tamaño: {len(contenido)} caracteres\n🔢 Bloques creados: {len(dataBlocks)}")
                self.actualizarStatus(f"Archivo '{nombre}' creado - {len(contenido)} caracteres")
                self.menuListar()
                
            except Exception as e:
                messagebox.showerror("Error", f"❌ Error al crear archivo: {str(e)}")
        
        def cancelar():
            self.limpiarInputFrames()
            self.actualizarStatus("Operación cancelada")
            self.menuListar()
        
        buttonFrame = tk.Frame(self.current_input_frame)
        buttonFrame.pack(pady=20)
        
        tk.Button(buttonFrame, text="✅ Guardar Archivo", command=crear, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#F44336", fg="white", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=10)
    
    def menuListar(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== ARCHIVOS DISPONIBLES ===\n\n")
        
        filesFound = False
        for fileEntry in self.fileSystem.fatTable:
            if not fileEntry["enPapelera"]:
                filesFound = True
                self.textArea.insert(tk.END, f"📄 Nombre: {fileEntry['nombreArchivo']}\n")
                self.textArea.insert(tk.END, f"   👤 Propietario: {fileEntry['owner']}\n")
                self.textArea.insert(tk.END, f"   📊 Tamaño: {fileEntry['totalCaracteres']} caracteres\n")
                self.textArea.insert(tk.END, f"   🕐 Creado: {fileEntry['fechaCreacion'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.textArea.insert(tk.END, f"   ✏️ Modificado: {fileEntry['fechaModificacion'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # Mostrar permisos de forma más legible
                lectores = fileEntry['permisos']['lectura']
                escritores = fileEntry['permisos']['escritura']
                self.textArea.insert(tk.END, f"   👁️ Lectura: {', '.join(lectores) if lectores else 'Ninguno'}\n")
                self.textArea.insert(tk.END, f"   📝 Escritura: {', '.join(escritores) if escritores else 'Ninguno'}\n")
                self.textArea.insert(tk.END, "-" * 60 + "\n\n")
        
        if not filesFound:
            self.textArea.insert(tk.END, "📭 No hay archivos disponibles.\n")
        
        self.actualizarStatus("Listados todos los archivos disponibles")
    
    def menuPapelera(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== PAPELERA DE RECICLAJE ===\n\n")
        
        filesFound = False
        for fileEntry in self.fileSystem.fatTable:
            if fileEntry["enPapelera"]:
                filesFound = True
                self.textArea.insert(tk.END, f"🗑️ Nombre: {fileEntry['nombreArchivo']}\n")
                self.textArea.insert(tk.END, f"   👤 Propietario: {fileEntry['owner']}\n")
                if fileEntry['fechaEliminacion']:
                    self.textArea.insert(tk.END, f"   🕐 Eliminado: {fileEntry['fechaEliminacion'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.textArea.insert(tk.END, f"   📊 Tamaño: {fileEntry['totalCaracteres']} caracteres\n")
                self.textArea.insert(tk.END, "-" * 50 + "\n\n")
        
        if not filesFound:
            self.textArea.insert(tk.END, "✅ La papelera de reciclaje está vacía.\n")
        
        self.actualizarStatus("Mostrado contenido de la papelera")
    
    def menuAbrir(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== ABRIR ARCHIVO ===\n\n")
        
        # Crear lista de archivos disponibles
        archivosDisponibles = []
        for fileEntry in self.fileSystem.fatTable:
            if not fileEntry["enPapelera"]:
                archivosDisponibles.append(fileEntry["nombreArchivo"])
        
        if not archivosDisponibles:
            self.textArea.insert(tk.END, "📭 No hay archivos disponibles para abrir.\n")
            return
        
        self.current_input_frame = tk.Frame(self.root)
        self.current_input_frame.pack(pady=10)
        
        formFrame = tk.Frame(self.current_input_frame)
        formFrame.pack(pady=10)
        
        tk.Label(formFrame, text="Seleccione archivo:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        
        archivoVar = tk.StringVar()
        archivoCombo = ttk.Combobox(formFrame, textvariable=archivoVar, values=archivosDisponibles, width=40, state="readonly")
        archivoCombo.grid(row=0, column=1, padx=5, pady=5)
        archivoCombo.current(0)
        
        def abrir():
            nombre = archivoVar.get().strip()
            if not nombre:
                messagebox.showerror("Error", "❌ Seleccione un archivo")
                return
            
            for fileEntry in self.fileSystem.fatTable:
                if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                    # Verificar permisos
                    if (self.fileSystem.currentUser not in fileEntry["permisos"]["lectura"] and 
                        self.fileSystem.currentUser != fileEntry["owner"] and
                        not self.fileSystem.esAdmin(self.fileSystem.currentUser)):
                        messagebox.showerror("Error", "❌ No tiene permisos de lectura para este archivo")
                        return
                    
                    # Mostrar metadatos
                    self.limpiarTexto()
                    self.textArea.insert(tk.END, f"=== METADATOS DE '{nombre}' ===\n\n")
                    self.textArea.insert(tk.END, f"👤 Propietario: {fileEntry['owner']}\n")
                    self.textArea.insert(tk.END, f"📊 Tamaño: {fileEntry['totalCaracteres']} caracteres\n")
                    self.textArea.insert(tk.END, f"🕐 Creado: {fileEntry['fechaCreacion'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    self.textArea.insert(tk.END, f"✏️ Modificado: {fileEntry['fechaModificacion'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    # Leer y mostrar contenido
                    contenido = self.fileSystem.leerContenido(fileEntry)
                    self.textArea.insert(tk.END, f"\n=== CONTENIDO ===\n\n")
                    self.textArea.insert(tk.END, contenido)
                    
                    self.limpiarInputFrames()
                    self.actualizarStatus(f"Archivo '{nombre}' abierto")
                    return
            
            messagebox.showerror("Error", "❌ Archivo no encontrado")
        
        def cancelar():
            self.limpiarInputFrames()
            self.actualizarStatus("Operación cancelada")
            self.menuListar()
        
        buttonFrame = tk.Frame(self.current_input_frame)
        buttonFrame.pack(pady=10)
        
        tk.Button(buttonFrame, text="🔓 Abrir Archivo", command=abrir, 
                 bg="#009688", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=5)
    
    def menuModificar(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== MODIFICAR ARCHIVO ===\n\n")
        
        # Crear lista de archivos con permisos de escritura
        archivosDisponibles = []
        for fileEntry in self.fileSystem.fatTable:
            if (not fileEntry["enPapelera"] and 
                (self.fileSystem.currentUser in fileEntry["permisos"]["escritura"] or 
                 self.fileSystem.currentUser == fileEntry["owner"] or
                 self.fileSystem.esAdmin(self.fileSystem.currentUser))):
                archivosDisponibles.append(fileEntry["nombreArchivo"])
        
        if not archivosDisponibles:
            self.textArea.insert(tk.END, "📭 No hay archivos disponibles para modificar.\n")
            return
        
        self.current_input_frame = tk.Frame(self.root)
        self.current_input_frame.pack(pady=10)
        
        formFrame = tk.Frame(self.current_input_frame)
        formFrame.pack(pady=10)
        
        tk.Label(formFrame, text="Seleccione archivo:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        archivoVar = tk.StringVar()
        archivoCombo = ttk.Combobox(formFrame, textvariable=archivoVar, values=archivosDisponibles, width=40, state="readonly")
        archivoCombo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(formFrame, text="Nuevo contenido:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        contenidoText = scrolledtext.ScrolledText(formFrame, width=60, height=15, font=("Consolas", 10))
        contenidoText.grid(row=1, column=1, padx=5, pady=5)
        
        def cargarContenido():
            nombre = archivoVar.get().strip()
            if not nombre:
                return
            
            for fileEntry in self.fileSystem.fatTable:
                if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                    contenido = self.fileSystem.leerContenido(fileEntry)
                    contenidoText.delete(1.0, tk.END)
                    contenidoText.insert(tk.END, contenido)
                    return
        
        def modificar():
            nombre = archivoVar.get().strip()
            nuevoContenido = contenidoText.get(1.0, tk.END).strip()
            
            if not nombre:
                messagebox.showerror("Error", "❌ Seleccione un archivo")
                return
            
            if not nuevoContenido:
                messagebox.showerror("Error", "❌ El contenido no puede estar vacío")
                return
            
            for i, fileEntry in enumerate(self.fileSystem.fatTable):
                if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                    try:
                        # Eliminar bloques antiguos
                        if fileEntry["archivoDatosInicial"]:
                            self.fileSystem.borrarBloquesViejos(fileEntry["archivoDatosInicial"])
                        
                        # Crear nuevos bloques
                        baseName = nombre.replace(" ", "_").lower()
                        dataBlocks = self.fileSystem.crearDataBlocks(nuevoContenido, baseName)
                        
                        # Actualizar tabla FAT
                        self.fileSystem.fatTable[i]["archivoDatosInicial"] = dataBlocks[0] if dataBlocks else ""
                        self.fileSystem.fatTable[i]["totalCaracteres"] = len(nuevoContenido)
                        self.fileSystem.fatTable[i]["fechaModificacion"] = datetime.datetime.now()
                        
                        self.fileSystem.guardarTablaFat()
                        
                        self.limpiarInputFrames()
                        messagebox.showinfo("Éxito", f"✅ Archivo '{nombre}' modificado exitosamente")
                        self.actualizarStatus(f"Archivo '{nombre}' modificado")
                        self.menuListar()
                        
                    except Exception as e:
                        messagebox.showerror("Error", f"❌ Error al modificar archivo: {str(e)}")
                    return
            
            messagebox.showerror("Error", "❌ Archivo no encontrado")
        
        def cancelar():
            self.limpiarInputFrames()
            self.actualizarStatus("Operación cancelada")
            self.menuListar()
        
        archivoCombo.bind('<<ComboboxSelected>>', lambda e: cargarContenido())
        if archivosDisponibles:
            archivoCombo.current(0)
            cargarContenido()
        
        buttonFrame = tk.Frame(self.current_input_frame)
        buttonFrame.pack(pady=10)
        
        tk.Button(buttonFrame, text="💾 Guardar Cambios", command=modificar, 
                 bg="#FFC107", fg="black", width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=5)
    
    def menuEliminar(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== ELIMINAR ARCHIVO ===\n\n")
        
        # Crear lista de archivos del usuario actual
        archivosUsuario = []
        for fileEntry in self.fileSystem.fatTable:
            if (not fileEntry["enPapelera"] and 
                (self.fileSystem.currentUser == fileEntry["owner"] or
                 self.fileSystem.esAdmin(self.fileSystem.currentUser))):
                archivosUsuario.append(fileEntry["nombreArchivo"])
        
        if not archivosUsuario:
            self.textArea.insert(tk.END, "📭 No tiene archivos para eliminar.\n")
            return
        
        self.current_input_frame = tk.Frame(self.root)
        self.current_input_frame.pack(pady=10)
        
        formFrame = tk.Frame(self.current_input_frame)
        formFrame.pack(pady=10)
        
        tk.Label(formFrame, text="Seleccione archivo a eliminar:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        archivoVar = tk.StringVar()
        archivoCombo = ttk.Combobox(formFrame, textvariable=archivoVar, values=archivosUsuario, width=40, state="readonly")
        archivoCombo.grid(row=0, column=1, padx=5, pady=5)
        archivoCombo.current(0)
        
        def eliminar():
            nombre = archivoVar.get().strip()
            if not nombre:
                messagebox.showerror("Error", "❌ Seleccione un archivo")
                return
            
            # Confirmación de eliminación
            confirmar = messagebox.askyesno("Confirmar", f"¿Está seguro de que desea eliminar el archivo '{nombre}'?")
            if not confirmar:
                return
            
            for i, fileEntry in enumerate(self.fileSystem.fatTable):
                if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                    if (self.fileSystem.currentUser != fileEntry["owner"] and 
                        not self.fileSystem.esAdmin(self.fileSystem.currentUser)):
                        messagebox.showerror("Error", "❌ Solo el propietario o administrador puede eliminar el archivo")
                        return
                    
                    self.fileSystem.fatTable[i]["enPapelera"] = True
                    self.fileSystem.fatTable[i]["fechaEliminacion"] = datetime.datetime.now()
                    self.fileSystem.guardarTablaFat()
                    
                    self.limpiarInputFrames()
                    messagebox.showinfo("Éxito", f"✅ Archivo '{nombre}' movido a la papelera de reciclaje")
                    self.actualizarStatus(f"Archivo '{nombre}' eliminado")
                    self.menuListar()
                    return
            
            messagebox.showerror("Error", "❌ Archivo no encontrado")
        
        def cancelar():
            self.limpiarInputFrames()
            self.actualizarStatus("Operación cancelada")
            self.menuListar()
        
        buttonFrame = tk.Frame(self.current_input_frame)
        buttonFrame.pack(pady=10)
        
        tk.Button(buttonFrame, text="🗑️ Eliminar", command=eliminar, 
                 bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#666666", fg="white", width=15).pack(side=tk.LEFT, padx=5)
    
    def menuRecuperar(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== RECUPERAR ARCHIVO ===\n\n")
        
        # Crear lista de archivos en papelera del usuario actual
        archivosPapelera = []
        for fileEntry in self.fileSystem.fatTable:  # ← Corrección aquí
            if (fileEntry["enPapelera"] and 
                (self.fileSystem.currentUser == fileEntry["owner"] or
                 self.fileSystem.esAdmin(self.fileSystem.currentUser))):
                archivosPapelera.append(fileEntry["nombreArchivo"])
        
        if not archivosPapelera:
            self.textArea.insert(tk.END, "📭 No tiene archivos en la papelera para recuperar.\n")
            return
        
        self.current_input_frame = tk.Frame(self.root)
        self.current_input_frame.pack(pady=10)
        
        formFrame = tk.Frame(self.current_input_frame)
        formFrame.pack(pady=10)
        
        tk.Label(formFrame, text="Seleccione archivo a recuperar:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        archivoVar = tk.StringVar()
        archivoCombo = ttk.Combobox(formFrame, textvariable=archivoVar, values=archivosPapelera, width=40, state="readonly")
        archivoCombo.grid(row=0, column=1, padx=5, pady=5)
        archivoCombo.current(0)
        
        def recuperar():
            nombre = archivoVar.get().strip()
            if not nombre:
                messagebox.showerror("Error", "❌ Seleccione un archivo")
                return
            
            # CORRECCIÓN: Paréntesis correctos en enumerate
            for i, fileEntry in enumerate(self.fileSystem.fatTable):  # ← Corrección aplicada
                if fileEntry["nombreArchivo"] == nombre and fileEntry["enPapelera"]:
                    if (self.fileSystem.currentUser != fileEntry["owner"] and 
                        not self.fileSystem.esAdmin(self.fileSystem.currentUser)):
                        messagebox.showerror("Error", "❌ Solo el propietario o administrador puede recuperar el archivo")
                        return
                    
                    self.fileSystem.fatTable[i]["enPapelera"] = False
                    self.fileSystem.fatTable[i]["fechaEliminacion"] = None
                    self.fileSystem.guardarTablaFat()
                    
                    self.limpiarInputFrames()
                    messagebox.showinfo("Éxito", f"✅ Archivo '{nombre}' recuperado de la papelera")
                    self.actualizarStatus(f"Archivo '{nombre}' recuperado")
                    self.menuListar()
                    return
            
            messagebox.showerror("Error", "❌ Archivo no encontrado en la papelera")
        
        def cancelar():
            self.limpiarInputFrames()
            self.actualizarStatus("Operación cancelada")
            self.menuListar()
        
        buttonFrame = tk.Frame(self.current_input_frame)
        buttonFrame.pack(pady=10)
        
        tk.Button(buttonFrame, text="↩️ Recuperar", command=recuperar, 
                 bg="#9C27B0", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#666666", fg="white", width=15).pack(side=tk.LEFT, padx=5)
    
    def menuPermisos(self):
        if not self.fileSystem.esAdmin(self.fileSystem.currentUser):
            messagebox.showerror("Error", "❌ Solo el administrador puede gestionar permisos")
            return
        
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== GESTIONAR PERMISOS ===\n\n")
        
        # Crear lista de archivos disponibles
        archivosDisponibles = []
        for fileEntry in self.fileSystem.fatTable:
            if not fileEntry["enPapelera"]:
                archivosDisponibles.append(fileEntry["nombreArchivo"])
        
        if not archivosDisponibles:
            self.textArea.insert(tk.END, "📭 No hay archivos disponibles.\n")
            return
        
        # Crear lista de usuarios disponibles
        usuariosDisponibles = list(self.fileSystem.users.keys())
        
        self.current_input_frame = tk.Frame(self.root)
        self.current_input_frame.pack(pady=10)
        
        formFrame = tk.Frame(self.current_input_frame)
        formFrame.pack(pady=10)
        
        tk.Label(formFrame, text="Archivo:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        archivoVar = tk.StringVar()
        archivoCombo = ttk.Combobox(formFrame, textvariable=archivoVar, values=archivosDisponibles, width=40, state="readonly")
        archivoCombo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(formFrame, text="Usuario:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5)
        usuarioCombo = ttk.Combobox(formFrame, values=usuariosDisponibles, width=40, state="readonly")
        usuarioCombo.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(formFrame, text="Operación:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=5, pady=5)
        operacionVar = tk.StringVar(value="otorgar_lectura")
        operacionFrame = tk.Frame(formFrame)
        operacionFrame.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Radiobutton(operacionFrame, text="✅ Otorgar permiso de lectura", variable=operacionVar, value="otorgar_lectura").pack(anchor=tk.W)
        tk.Radiobutton(operacionFrame, text="❌ Revocar permiso de lectura", variable=operacionVar, value="revocar_lectura").pack(anchor=tk.W)
        tk.Radiobutton(operacionFrame, text="✅ Otorgar permiso de escritura", variable=operacionVar, value="otorgar_escritura").pack(anchor=tk.W)
        tk.Radiobutton(operacionFrame, text="❌ Revocar permiso de escritura", variable=operacionVar, value="revocar_escritura").pack(anchor=tk.W)
        
        def gestionar():
            nombre = archivoVar.get().strip()
            usuario = usuarioCombo.get().strip()
            operacion = operacionVar.get()
            
            if not nombre or not usuario:
                messagebox.showerror("Error", "❌ Complete todos los campos")
                return
            
            if usuario not in self.fileSystem.users:
                messagebox.showerror("Error", "❌ El usuario no existe")
                return
            
            for i, fileEntry in enumerate(self.fileSystem.fatTable):
                if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                    try:
                        if operacion == "otorgar_lectura" and usuario not in fileEntry["permisos"]["lectura"]:
                            self.fileSystem.fatTable[i]["permisos"]["lectura"].append(usuario)
                        elif operacion == "revocar_lectura" and usuario in fileEntry["permisos"]["lectura"]:
                            self.fileSystem.fatTable[i]["permisos"]["lectura"].remove(usuario)
                        elif operacion == "otorgar_escritura" and usuario not in fileEntry["permisos"]["escritura"]:
                            self.fileSystem.fatTable[i]["permisos"]["escritura"].append(usuario)
                        elif operacion == "revocar_escritura" and usuario in fileEntry["permisos"]["escritura"]:
                            self.fileSystem.fatTable[i]["permisos"]["escritura"].remove(usuario)
                        else:
                            messagebox.showerror("Error", "❌ Operación inválida o no aplicable")
                            return
                        
                        self.fileSystem.guardarTablaFat()
                        self.limpiarInputFrames()
                        messagebox.showinfo("Éxito", "✅ Permisos actualizados exitosamente")
                        self.actualizarStatus(f"Permisos actualizados para '{nombre}'")
                        self.menuListar()
                        
                    except Exception as e:
                        messagebox.showerror("Error", f"❌ Error al gestionar permisos: {str(e)}")
                    return
            
            messagebox.showerror("Error", "❌ Archivo no encontrado")
        
        def cancelar():
            self.limpiarInputFrames()
            self.actualizarStatus("Operación cancelada")
            self.menuListar()
        
        buttonFrame = tk.Frame(self.current_input_frame)
        buttonFrame.pack(pady=10)
        
        tk.Button(buttonFrame, text="💾 Aplicar Permisos", command=gestionar, 
                 bg="#607D8B", fg="white", width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#666666", fg="white", width=15).pack(side=tk.LEFT, padx=5)
    
    def mostrarCrearUsuario(self):
        self.limpiarTexto()
        self.limpiarInputFrames()
        
        self.textArea.insert(tk.END, "=== CREAR NUEVO USUARIO ===\n\n")
        
        self.current_input_frame = tk.Frame(self.root)
        self.current_input_frame.pack(pady=20)
        
        tk.Label(self.current_input_frame, text="CREAR NUEVO USUARIO", 
                font=("Arial", 14, "bold")).pack(pady=15)
        
        formFrame = tk.Frame(self.current_input_frame)
        formFrame.pack(pady=15, padx=20)
        
        tk.Label(formFrame, text="Nuevo Usuario:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        nuevoUserEntry = tk.Entry(formFrame, width=25, font=("Arial", 10))
        nuevoUserEntry.grid(row=0, column=1, padx=5, pady=8)
        nuevoUserEntry.focus()
        
        tk.Label(formFrame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        nuevoPassEntry = tk.Entry(formFrame, width=25, show="*", font=("Arial", 10))
        nuevoPassEntry.grid(row=1, column=1, padx=5, pady=8)
        
        tk.Label(formFrame, text="Confirmar Contraseña:").grid(row=2, column=0, padx=5, pady=8, sticky="w")
        confirmPassEntry = tk.Entry(formFrame, width=25, show="*", font=("Arial", 10))
        confirmPassEntry.grid(row=2, column=1, padx=5, pady=8)
        
        rolVar = tk.StringVar(value="user")
        tk.Label(formFrame, text="Tipo de usuario:").grid(row=3, column=0, padx=5, pady=8, sticky="w")
        rolFrame = tk.Frame(formFrame)
        rolFrame.grid(row=3, column=1, padx=5, pady=8, sticky="w")
        tk.Radiobutton(rolFrame, text="Usuario Normal", variable=rolVar, value="user").pack(anchor="w")
        tk.Radiobutton(rolFrame, text="Administrador", variable=rolVar, value="admin").pack(anchor="w")
        
        def crear():
            username = nuevoUserEntry.get().strip()
            password = nuevoPassEntry.get().strip()
            confirm_password = confirmPassEntry.get().strip()
            rol = rolVar.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Complete todos los campos")
                return
            
            if password != confirm_password:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            if len(password) < 3:
                messagebox.showerror("Error", "La contraseña debe tener al menos 3 caracteres")
                return
            
            success, mensaje = self.fileSystem.crearUsuario(username, password, rol)
            if success:
                messagebox.showinfo("Éxito", mensaje)
                self.limpiarInputFrames()
                self.actualizarStatus(f"Usuario '{username}' creado exitosamente")
                self.menuListar()
            else:
                messagebox.showerror("Error", mensaje)
        
        def cancelar():
            self.limpiarInputFrames()
            self.actualizarStatus("Creación de usuario cancelada")
            self.menuListar()
        
        buttonFrame = tk.Frame(self.current_input_frame)
        buttonFrame.pack(pady=20)
        
        tk.Button(buttonFrame, text="✅ Crear Usuario", command=crear, 
                 bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(buttonFrame, text="❌ Cancelar", command=cancelar, 
                 bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FatFileSystemGUI(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Error crítico en la aplicación: {e}")
        messagebox.showerror("Error Crítico", f"La aplicación encontró un error y debe cerrarse:\n{str(e)}")