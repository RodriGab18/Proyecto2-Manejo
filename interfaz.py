import tkinter as tk
from tkinter import messagebox

def mostrarMensaje(mensaje):
    messagebox.showinfo("Mensaje", mensaje)

def menuPrincipal():
    limpiarVentana()
    etiqueta.config(text="Selecciona una opción")
    crearBotonesPrincipales()

def menuCrear():
    limpiarVentana()
    etiqueta.config(text="Menú Crear")
    crearBotonRegresar(menuPrincipal)

def menuListar():
    limpiarVentana()
    etiqueta.config(text="Menú Listar")
    crearBotonRegresar(menuPrincipal)

def menuAbrir():
    limpiarVentana()
    etiqueta.config(text="Menú Abrir")
    crearBotonRegresar(menuPrincipal)

def menuModificar():
    limpiarVentana()
    etiqueta.config(text="Menú Modificar")
    crearBotonRegresar(menuPrincipal)

def menuEliminar():
    limpiarVentana()
    etiqueta.config(text="Menú Eliminar")
    crearBotonRegresar(menuPrincipal)

def menuRecuperar():
    limpiarVentana()
    etiqueta.config(text="Menú Recuperar")
    crearBotonRegresar(menuPrincipal)

def limpiarVentana():
    for widget in ventanaPrincipal.winfo_children():
        widget.destroy()

def crearBotonesPrincipales():
    botonCrear = tk.Button(ventanaPrincipal, text="Crear", command=menuCrear)
    botonCrear.pack(pady=10)
    botonListar = tk.Button(ventanaPrincipal, text="Listar", command=menuListar)
    botonListar.pack(pady=10)
    botonAbrir = tk.Button(ventanaPrincipal, text="Abrir", command=menuAbrir)
    botonAbrir.pack(pady=10)
    botonModificar = tk.Button(ventanaPrincipal, text="Modificar", command=menuModificar)
    botonModificar.pack(pady=10)
    botonEliminar = tk.Button(ventanaPrincipal, text="Eliminar", command=menuEliminar)
    botonEliminar.pack(pady=10)
    botonRecuperar = tk.Button(ventanaPrincipal, text="Recuperar", command=menuRecuperar)
    botonRecuperar.pack(pady=10)

def crearBotonRegresar(funcion):
    botonRegresar = tk.Button(ventanaPrincipal, text="Regresar", command=funcion)
    botonRegresar.pack(pady=10)

# Interfaz
ventanaPrincipal = tk.Tk()
ventanaPrincipal.title("Controlador de archivos")
ventanaPrincipal.geometry("600x400")

etiqueta = tk.Label(ventanaPrincipal, text="Selecciona una opción", font=("Arial", 16))
etiqueta.pack(pady=20)

crearBotonesPrincipales()

ventanaPrincipal.mainloop()