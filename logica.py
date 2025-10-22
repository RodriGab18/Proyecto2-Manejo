import json
import os
import datetime
from pathlib import Path

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
    
    def crearArchivo(self):
        fileName = input("Ingrese el nombre del archivo: ")
        for fileEntry in self.fatTable:
            if fileEntry["nombreArchivo"] == fileName and not fileEntry["enPapelera"]:
                print("Error: Ya existe un archivo con ese nombre.")
                return
        
        content = input("Ingrese el contenido del archivo: ")
        
        baseName = fileName.replace(" ", "_").lower()
        dataBlocks = self.crearDataBlocks(content, baseName)
        
        fileEntry = {
            "nombreArchivo": fileName,
            "archivoDatosInicial": dataBlocks[0] if dataBlocks else "",
            "enPapelera": False,
            "totalCaracteres": len(content),
            "fechaCreacion": datetime.datetime.now(),
            "fechaModificacion": datetime.datetime.now(),
            "fechaEliminacion": None,
            "owner": self.currentUser,
            "permisos": {
                "lectura": [self.currentUser],
                "escritura": [self.currentUser]
            }
        }
        
        self.fatTable.append(fileEntry)
        self.guardarTablaFat()
        print(f"Archivo '{fileName}' creado exitosamente.")
    
    def listarArchivos(self):
        print("\n--- ARCHIVOS DISPONIBLES ---")
        filesFound = False
        
        for fileEntry in self.fatTable:
            if not fileEntry["enPapelera"]:
                print(f"Nombre: {fileEntry['nombreArchivo']}")
                print(f"  Propietario: {fileEntry['owner']}")
                print(f"  Tamaño: {fileEntry['totalCaracteres']} caracteres")
                print(f"  Creado: {fileEntry['fechaCreacion']}")
                print(f"  Modificado: {fileEntry['fechaModificacion']}")
                print("  Permisos:")
                print(f"    Lectura: {', '.join(fileEntry['permisos']['lectura'])}")
                print(f"    Escritura: {', '.join(fileEntry['permisos']['escritura'])}")
                print("-" * 40)
                filesFound = True
        
        if not filesFound:
            print("No hay archivos disponibles.")
    
    def listarPapeleraReciclaje(self):
        print("\n--- PAPELERA DE RECICLAJE ---")
        filesFound = False
        
        for fileEntry in self.fatTable:
            if fileEntry["enPapelera"]:
                print(f"Nombre: {fileEntry['nombreArchivo']}")
                print(f"  Propietario: {fileEntry['owner']}")
                print(f"  Eliminado: {fileEntry['fechaEliminacion']}")
                print(f"  Tamaño: {fileEntry['totalCaracteres']} caracteres")
                print("-" * 40)
                filesFound = True
        
        if not filesFound:
            print("La papelera de reciclaje está vacía.")
    
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
    
    def abrirArchivo(self):
        fileName = input("Ingrese el nombre del archivo a abrir: ")
        
        for fileEntry in self.fatTable:
            if fileEntry["nombreArchivo"] == fileName and not fileEntry["enPapelera"]:
                if self.currentUser not in fileEntry["permisos"]["lectura"] and self.currentUser != fileEntry["owner"]:
                    print("Error: No tiene permisos de lectura para este archivo.")
                    return
                
                print(f"\n--- METADATOS DE '{fileName}' ---")
                print(f"Propietario: {fileEntry['owner']}")
                print(f"Tamaño: {fileEntry['totalCaracteres']} caracteres")
                print(f"Creado: {fileEntry['fechaCreacion']}")
                print(f"Modificado: {fileEntry['fechaModificacion']}")
                
                content = self.leerContenido(fileEntry)
                print(f"\n--- CONTENIDO ---")
                print(content)
                return
        
        print("Error: Archivo no encontrado o está en la papelera.")
    
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
    
    def modificarArchivo(self):
        fileName = input("Ingrese el nombre del archivo a modificar: ")
        
        for i, fileEntry in enumerate(self.fatTable):
            if fileEntry["nombreArchivo"] == fileName and not fileEntry["enPapelera"]:
                if self.currentUser not in fileEntry["permisos"]["escritura"] and self.currentUser != fileEntry["owner"]:
                    print("Error: No tiene permisos de escritura para este archivo.")
                    return
                
                currentContent = self.leerContenido(fileEntry)
                print(f"\n--- CONTENIDO ACTUAL ---")
                print(currentContent)
                
                newContent = input("\nIngrese el nuevo contenido: ")
                
                self.borrarBloquesViejos(fileEntry["archivoDatosInicial"])
                
                baseName = fileName.replace(" ", "_").lower()
                dataBlocks = self.crearDataBlocks(newContent, baseName)
                
                self.fatTable[i]["archivoDatosInicial"] = dataBlocks[0] if dataBlocks else ""
                self.fatTable[i]["totalCaracteres"] = len(newContent)
                self.fatTable[i]["fechaModificacion"] = datetime.datetime.now()
                
                self.guardarTablaFat()
                print(f"Archivo '{fileName}' modificado exitosamente.")
                return
        
        print("Error: Archivo no encontrado o está en la papelera.")
    
    def eliminarArchivo(self):
        fileName = input("Ingrese el nombre del archivo a eliminar: ")
        
        for i, fileEntry in enumerate(self.fatTable):
            if fileEntry["nombreArchivo"] == fileName and not fileEntry["enPapelera"]:
                if self.currentUser != fileEntry["owner"]:
                    print("Error: Solo el propietario puede eliminar el archivo.")
                    return
                
                self.fatTable[i]["enPapelera"] = True
                self.fatTable[i]["fechaEliminacion"] = datetime.datetime.now()
                self.guardarTablaFat()
                print(f"Archivo '{fileName}' movido a la papelera de reciclaje.")
                return
        
        print("Error: Archivo no encontrado.")
    
    def restaurarArchivo(self):
        fileName = input("Ingrese el nombre del archivo a recuperar: ")
        
        for i, fileEntry in enumerate(self.fatTable):
            if fileEntry["nombreArchivo"] == fileName and fileEntry["enPapelera"]:
                if self.currentUser != fileEntry["owner"]:
                    print("Error: Solo el propietario puede recuperar el archivo.")
                    return
                
                self.fatTable[i]["enPapelera"] = False
                self.fatTable[i]["fechaEliminacion"] = None
                self.guardarTablaFat()
                print(f"Archivo '{fileName}' recuperado de la papelera.")
                return
        
        print("Error: Archivo no encontrado en la papelera.")
    
    def administrarPermisos(self):
        if self.currentUser != "admin":
            print("Error: Solo el administrador puede gestionar permisos.")
            return
        
        fileName = input("Ingrese el nombre del archivo: ")
        userName = input("Ingrese el nombre del usuario: ")
        
        for i, fileEntry in enumerate(self.fatTable):
            if fileEntry["nombreArchivo"] == fileName and not fileEntry["enPapelera"]:
                print("\n1. Otorgar permiso de lectura")
                print("2. Revocar permiso de lectura")
                print("3. Otorgar permiso de escritura")
                print("4. Revocar permiso de escritura")
                
                option = input("Seleccione una opción: ")
                
                if option == "1" and userName not in fileEntry["permisos"]["lectura"]:
                    self.fatTable[i]["permisos"]["lectura"].append(userName)
                elif option == "2" and userName in fileEntry["permisos"]["lectura"]:
                    self.fatTable[i]["permisos"]["lectura"].remove(userName)
                elif option == "3" and userName not in fileEntry["permisos"]["escritura"]:
                    self.fatTable[i]["permisos"]["escritura"].append(userName)
                elif option == "4" and userName in fileEntry["permisos"]["escritura"]:
                    self.fatTable[i]["permisos"]["escritura"].remove(userName)
                else:
                    print("Opción inválida o no aplicable.")
                    return
                
                self.guardarTablaFat()
                print("Permisos actualizados exitosamente.")
                return
        
        print("Error: Archivo no encontrado.")
    
    def mostrarMenu(self):
        print("\n=== SISTEMA DE ARCHIVOS FAT ===")
        print("1. Crear archivo")
        print("2. Listar archivos")
        print("3. Mostrar papelera de reciclaje")
        print("4. Abrir archivo")
        print("5. Modificar archivo")
        print("6. Eliminar archivo")
        print("7. Recuperar archivo")
        print("8. Gestionar permisos")
        print("9. Cambiar usuario")
        print("0. Salir")
    
    def cambiarUsuario(self):
        print(f"Usuario actual: {self.currentUser}")
        newUser = input("Ingrese el nuevo usuario: ")
        self.currentUser = newUser
        print(f"Usuario cambiado a: {self.currentUser}")
    
    def run(self):
        print("Bienvenido al Sistema de Archivos FAT")
        
        while True:
            self.mostrarMenu()
            option = input("Seleccione una opción: ")
            
            if option == "1":
                self.crearArchivo()
            elif option == "2":
                self.listarArchivos()
            elif option == "3":
                self.listarPapeleraReciclaje()
            elif option == "4":
                self.abrirArchivo()
            elif option == "5":
                self.modificarArchivo()
            elif option == "6":
                self.eliminarArchivo()
            elif option == "7":
                self.restaurarArchivo()
            elif option == "8":
                self.administrarPermisos()
            elif option == "9":
                self.cambiarUsuario()
            elif option == "0":
                print("¡Hasta luego!")
                break
            else:
                print("Opción inválida. Intente nuevamente.")

if __name__ == "__main__":
    fileSystem = FatFileSystem()
    fileSystem.run()