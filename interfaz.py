import json
import os
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext

class FatFileSystemGUI:
    def __init__(self, root):
        self.fs = FatFileSystem()
        self.root = root
        self.root.title("Sistema de Archivos FAT")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Botones de operaciones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        buttons = [
            ("Crear Archivo", self.crear_archivo),
            ("Listar Archivos", self.listar_archivos),
            ("Abrir Archivo", self.abrir_archivo),
            ("Modificar Archivo", self.modificar_archivo),
            ("Eliminar Archivo", self.eliminar_archivo),
            ("Papelera", self.mostrar_papelera),
            ("Recuperar Archivo", self.recuperar_archivo),
            ("Gestionar Permisos", self.gestionar_permisos),
            ("Cambiar Usuario", self.cambiar_usuario),
            ("Salir", self.salir)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(button_frame, text=text, command=command).grid(
                row=i//2, column=i%2, sticky=(tk.W, tk.E), padx=5, pady=2
            )
        
        # Área de texto para mostrar información
        self.text_area = scrolledtext.ScrolledText(main_frame, width=60, height=25)
        self.text_area.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
    
    def update_status(self):
        self.status_var.set(f"Usuario actual: {self.fs.currentUser} | Archivos en sistema: {len([f for f in self.fs.fatTable if not f['enPapelera']])}")
    
    def mostrar_mensaje(self, titulo, mensaje):
        self.text_area.insert(tk.END, f"\n=== {titulo} ===\n{mensaje}\n")
        self.text_area.see(tk.END)
    
    def limpiar_texto(self):
        self.text_area.delete(1.0, tk.END)
    
    def crear_archivo(self):
        nombre = simpledialog.askstring("Crear Archivo", "Ingrese el nombre del archivo:")
        if not nombre:
            return
        
        # Verificar si ya existe
        for fileEntry in self.fs.fatTable:
            if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                messagebox.showerror("Error", "Ya existe un archivo con ese nombre.")
                return
        
        contenido = simpledialog.askstring("Crear Archivo", "Ingrese el contenido del archivo:")
        if contenido is None:
            return
        
        baseName = nombre.replace(" ", "_").lower()
        dataBlocks = self.fs.crearDataBlocks(contenido, baseName)
        
        fileEntry = {
            "nombreArchivo": nombre,
            "archivoDatosInicial": dataBlocks[0] if dataBlocks else "",
            "enPapelera": False,
            "totalCaracteres": len(contenido),
            "fechaCreacion": datetime.datetime.now(),
            "fechaModificacion": datetime.datetime.now(),
            "fechaEliminacion": None,
            "owner": self.fs.currentUser,
            "permisos": {
                "lectura": [self.fs.currentUser],
                "escritura": [self.fs.currentUser]
            }
        }
        
        self.fs.fatTable.append(fileEntry)
        self.fs.guardarTablaFat()
        self.mostrar_mensaje("ÉXITO", f"Archivo '{nombre}' creado exitosamente.")
        self.update_status()
    
    def listar_archivos(self):
        self.limpiar_texto()
        self.mostrar_mensaje("ARCHIVOS DISPONIBLES", "")
        
        filesFound = False
        for fileEntry in self.fs.fatTable:
            if not fileEntry["enPapelera"]:
                contenido = f"""Nombre: {fileEntry['nombreArchivo']}
Propietario: {fileEntry['owner']}
Tamaño: {fileEntry['totalCaracteres']} caracteres
Creado: {fileEntry['fechaCreacion']}
Modificado: {fileEntry['fechaModificacion']}
Permisos:
  Lectura: {', '.join(fileEntry['permisos']['lectura'])}
  Escritura: {', '.join(fileEntry['permisos']['escritura'])}
{'-'*40}"""
                self.mostrar_mensaje("", contenido)
                filesFound = True
        
        if not filesFound:
            self.mostrar_mensaje("", "No hay archivos disponibles.")
    
    def abrir_archivo(self):
        nombre = simpledialog.askstring("Abrir Archivo", "Ingrese el nombre del archivo:")
        if not nombre:
            return
        
        for fileEntry in self.fs.fatTable:
            if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                if self.fs.currentUser not in fileEntry["permisos"]["lectura"] and self.fs.currentUser != fileEntry["owner"]:
                    messagebox.showerror("Error", "No tiene permisos de lectura para este archivo.")
                    return
                
                self.limpiar_texto()
                contenido = f"""=== METADATOS DE '{nombre}' ===
Propietario: {fileEntry['owner']}
Tamaño: {fileEntry['totalCaracteres']} caracteres
Creado: {fileEntry['fechaCreacion']}
Modificado: {fileEntry['fechaModificacion']}

=== CONTENIDO ===
{self.fs.leerContenido(fileEntry)}"""
                self.mostrar_mensaje("", contenido)
                return
        
        messagebox.showerror("Error", "Archivo no encontrado o está en la papelera.")
    
    def modificar_archivo(self):
        nombre = simpledialog.askstring("Modificar Archivo", "Ingrese el nombre del archivo:")
        if not nombre:
            return
        
        for i, fileEntry in enumerate(self.fs.fatTable):
            if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                if self.fs.currentUser not in fileEntry["permisos"]["escritura"] and self.fs.currentUser != fileEntry["owner"]:
                    messagebox.showerror("Error", "No tiene permisos de escritura para este archivo.")
                    return
                
                contenido_actual = self.fs.leerContenido(fileEntry)
                nuevo_contenido = simpledialog.askstring(
                    "Modificar Archivo", 
                    f"Contenido actual:\n{contenido_actual}\n\nIngrese el nuevo contenido:"
                )
                
                if nuevo_contenido is None:
                    return
                
                self.fs.borrarBloquesViejos(fileEntry["archivoDatosInicial"])
                baseName = nombre.replace(" ", "_").lower()
                dataBlocks = self.fs.crearDataBlocks(nuevo_contenido, baseName)
                
                self.fs.fatTable[i]["archivoDatosInicial"] = dataBlocks[0] if dataBlocks else ""
                self.fs.fatTable[i]["totalCaracteres"] = len(nuevo_contenido)
                self.fs.fatTable[i]["fechaModificacion"] = datetime.datetime.now()
                
                self.fs.guardarTablaFat()
                self.mostrar_mensaje("ÉXITO", f"Archivo '{nombre}' modificado exitosamente.")
                return
        
        messagebox.showerror("Error", "Archivo no encontrado o está en la papelera.")
    
    def eliminar_archivo(self):
        nombre = simpledialog.askstring("Eliminar Archivo", "Ingrese el nombre del archivo:")
        if not nombre:
            return
        
        for i, fileEntry in enumerate(self.fs.fatTable):
            if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                if self.fs.currentUser != fileEntry["owner"]:
                    messagebox.showerror("Error", "Solo el propietario puede eliminar el archivo.")
                    return
                
                self.fs.fatTable[i]["enPapelera"] = True
                self.fs.fatTable[i]["fechaEliminacion"] = datetime.datetime.now()
                self.fs.guardarTablaFat()
                self.mostrar_mensaje("ÉXITO", f"Archivo '{nombre}' movido a la papelera de reciclaje.")
                self.update_status()
                return
        
        messagebox.showerror("Error", "Archivo no encontrado.")
    
    def mostrar_papelera(self):
        self.limpiar_texto()
        self.mostrar_mensaje("PAPELERA DE RECICLAJE", "")
        
        filesFound = False
        for fileEntry in self.fs.fatTable:
            if fileEntry["enPapelera"]:
                contenido = f"""Nombre: {fileEntry['nombreArchivo']}
Propietario: {fileEntry['owner']}
Eliminado: {fileEntry['fechaEliminacion']}
Tamaño: {fileEntry['totalCaracteres']} caracteres
{'-'*40}"""
                self.mostrar_mensaje("", contenido)
                filesFound = True
        
        if not filesFound:
            self.mostrar_mensaje("", "La papelera de reciclaje está vacía.")
    
    def recuperar_archivo(self):
        nombre = simpledialog.askstring("Recuperar Archivo", "Ingrese el nombre del archivo a recuperar:")
        if not nombre:
            return
        
        for i, fileEntry in enumerate(self.fs.fatTable):
            if fileEntry["nombreArchivo"] == nombre and fileEntry["enPapelera"]:
                if self.fs.currentUser != fileEntry["owner"]:
                    messagebox.showerror("Error", "Solo el propietario puede recuperar el archivo.")
                    return
                
                self.fs.fatTable[i]["enPapelera"] = False
                self.fs.fatTable[i]["fechaEliminacion"] = None
                self.fs.guardarTablaFat()
                self.mostrar_mensaje("ÉXITO", f"Archivo '{nombre}' recuperado de la papelera.")
                self.update_status()
                return
        
        messagebox.showerror("Error", "Archivo no encontrado en la papelera.")
    
    def gestionar_permisos(self):
        if self.fs.currentUser != "admin":
            messagebox.showerror("Error", "Solo el administrador puede gestionar permisos.")
            return
        
        nombre = simpledialog.askstring("Gestionar Permisos", "Ingrese el nombre del archivo:")
        if not nombre:
            return
        
        usuario = simpledialog.askstring("Gestionar Permisos", "Ingrese el nombre del usuario:")
        if not usuario:
            return
        
        for i, fileEntry in enumerate(self.fs.fatTable):
            if fileEntry["nombreArchivo"] == nombre and not fileEntry["enPapelera"]:
                opcion = simpledialog.askstring(
                    "Gestionar Permisos",
                    "Seleccione una opción:\n\n"
                    "1. Otorgar permiso de lectura\n"
                    "2. Revocar permiso de lectura\n"
                    "3. Otorgar permiso de escritura\n"
                    "4. Revocar permiso de escritura"
                )
                
                if opcion == "1" and usuario not in fileEntry["permisos"]["lectura"]:
                    self.fs.fatTable[i]["permisos"]["lectura"].append(usuario)
                elif opcion == "2" and usuario in fileEntry["permisos"]["lectura"]:
                    self.fs.fatTable[i]["permisos"]["lectura"].remove(usuario)
                elif opcion == "3" and usuario not in fileEntry["permisos"]["escritura"]:
                    self.fs.fatTable[i]["permisos"]["escritura"].append(usuario)
                elif opcion == "4" and usuario in fileEntry["permisos"]["escritura"]:
                    self.fs.fatTable[i]["permisos"]["escritura"].remove(usuario)
                else:
                    messagebox.showerror("Error", "Opción inválida o no aplicable.")
                    return
                
                self.fs.guardarTablaFat()
                self.mostrar_mensaje("ÉXITO", "Permisos actualizados exitosamente.")
                return
        
        messagebox.showerror("Error", "Archivo no encontrado.")
    
    def cambiar_usuario(self):
        nuevo_usuario = simpledialog.askstring("Cambiar Usuario", f"Usuario actual: {self.fs.currentUser}\n\nIngrese el nuevo usuario:")
        if nuevo_usuario:
            self.fs.currentUser = nuevo_usuario
            self.mostrar_mensaje("ÉXITO", f"Usuario cambiado a: {self.fs.currentUser}")
            self.update_status()
    
    def salir(self):
        if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir?"):
            self.root.destroy()

# Mantener la clase FatFileSystem original sin cambios
class FatFileSystem:
    def __init__(self):
        self.fatTable = []
        self.currentUser = "admin"
        self.dataDirectory = "data_blocks"
        self.fatTableFile = "fat_table.json"
        self.cargarTablaFat()
        Path(self.dataDirectory).mkdir(exist_ok=True)
    
    def cargarTablaFat(self):
        try:
            if os.path.exists(self.fatTableFile):
                with open(self.fatTableFile, 'r') as file:
                    self.fatTable = json.load(file)
        except Exception as e:
            print(f"Error al cargar la tabla FAT: {e}")
            self.fatTable = []
    
    def guardarTablaFat(self):
        try:
            with open(self.fatTableFile, 'w') as file:
                json.dump(self.fatTable, file, indent=2, default=str)
        except Exception as e:
            print(f"Error al guardar la tabla FAT: {e}")
    
    def generarBloque(self, baseName, index):
        return f"{self.dataDirectory}/{baseName}_block_{index}.json"
    
    def crearDataBlocks(self, content, baseName):
        blocks = []
        contentLength = len(content)
        
        for i in range(0, contentLength, 20):
            blockContent = content[i:i+20]
            blockFileName = self.generarBloque(baseName, len(blocks))
            
            blockData = {
                "datos": blockContent,
                "siguiente": self.generarBloque(baseName, len(blocks) + 1) if i + 20 < contentLength else "",
                "eof": i + 20 >= contentLength
            }
            
            with open(blockFileName, 'w') as blockFile:
                json.dump(blockData, blockFile, indent=2)
            
            blocks.append(blockFileName)
        
        return blocks
    
    def leerContenido(self, fileEntry):
        if not fileEntry["archivoDatosInicial"]:
            return ""
        
        content = ""
        currentBlock = fileEntry["archivoDatosInicial"]
        
        while currentBlock:
            try:
                with open(currentBlock, 'r') as blockFile:
                    blockData = json.load(blockFile)
                
                content += blockData["datos"]
                
                if blockData["eof"]:
                    break
                
                currentBlock = blockData["siguiente"]
            except Exception as e:
                print(f"Error al leer bloque {currentBlock}: {e}")
                break
        
        return content
    
    def borrarBloquesViejos(self, initialBlock):
        currentBlock = initialBlock
        
        while currentBlock:
            try:
                if os.path.exists(currentBlock):
                    with open(currentBlock, 'r') as blockFile:
                        blockData = json.load(blockFile)
                    
                    nextBlock = blockData["siguiente"]
                    os.remove(currentBlock)
                    currentBlock = nextBlock
                else:
                    break
            except Exception as e:
                print(f"Error al eliminar bloque {currentBlock}: {e}")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = FatFileSystemGUI(root)
    root.mainloop()