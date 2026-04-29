import hashlib
import hmac
import os
import json
import base64
import time
import sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ARCHIVO_BLOQUES = "blockchain.dat"
ARCHIVO_USUARIOS = "usuarios.dat"

class BlockchainMensaje:
    def __init__(self, indice, Hash_anterior, timestamp, datos):
        self.indice = indice
        self.Hash_anterior = Hash_anterior
        self.timestamp = timestamp
        self.datos = datos
        self.hash = self.calcular_hash()

    def calcular_hash(self):
        datos_crypto = str(self.indice) + str(self.Hash_anterior) + str(self.timestamp) + str(self.datos)
        return hashlib.sha256(datos_crypto.encode()).hexdigest()

    def to_dict(self):
        return {
            "indice": self.indice,
            "Hash_anterior": self.Hash_anterior,
            "timestamp": self.timestamp,
            "datos": self.datos,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(d):
        b = BlockchainMensaje(d["indice"], d["Hash_anterior"], d["timestamp"], d["datos"])
        return b

class RedAnonimaMensajeria:
    def __init__(self):
        self.cadena_bloques = []
        self.pin_correcto = "1049"
        self.usuario_actual = None
        self.intentos_fallidos = 0
        self.cargar_bloques()

    def cargar_bloques(self):
        if os.path.exists(ARCHIVO_BLOQUES):
            try:
                with open(ARCHIVO_BLOQUES, "r") as f:
                    data = json.load(f)
                    self.cadena_bloques = [BlockchainMensaje.from_dict(b) for b in data]
            except:
                self.bloque_genesis()
        else:
            self.bloque_genesis()

    def guardar_bloques(self):
        with open(ARCHIVO_BLOQUES, "w") as f:
            json.dump([b.to_dict() for b in self.cadena_bloques], f)

    def bloque_genesis(self):
        genesis = BlockchainMensaje(0, "0", time.time(), {"tipo": "GENESIS", "de": "SISTEMA", "para": "ALL", "mensaje": "Red anonima iniciada"})
        self.cadena_bloques.append(genesis)
        self.guardar_bloques()

    def verificar_pin(self, pin):
        return hmac.compare_digest(self.pin_correcto, pin)

    def derivar_clave(self, pin):
        sal = b'red_anonima_segura'
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=sal, iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(pin.encode()))

    def cifrar_mensaje(self, pin, mensaje):
        clave = self.derivar_clave(pin)
        f = Fernet(clave)
        return f.encrypt(mensaje.encode()).decode()

    def descifrar_mensaje(self, pin, token):
        try:
            clave = self.derivar_clave(pin)
            f = Fernet(clave)
            return f.decrypt(token.encode()).decode()
        except:
            return None

    def agregar_bloque(self, datos):
        ultimo = self.cadena_bloques[-1]
        nuevo = BlockchainMensaje(
            ultimo.indice + 1,
            ultimo.hash,
            time.time(),
            datos
        )
        self.cadena_bloques.append(nuevo)
        self.guardar_bloques()
        return nuevo

    def verificar_cadena(self):
        for i in range(1, len(self.cadena_bloques)):
            bloque_actual = self.cadena_bloques[i]
            bloque_anterior = self.cadena_bloques[i - 1]
            if bloque_actual.Hash_anterior != bloque_anterior.hash:
                return False
            if bloque_actual.hash != bloque_actual.calcular_hash():
                return False
        return True

    def obtener_mensajes(self, usuario):
        self.cargar_bloques()
        mensajes = []
        for bloque in self.cadena_bloques[1:]:
            datos = bloque.datos
            if datos.get("para") == usuario or datos.get("para") == "ALL":
                try:
                    msg = self.descifrar_mensaje(self.pin_correcto, datos.get("mensaje_cifrado", ""))
                    if msg:
                        mensajes.append((bloque.indice, datos.get("de"), msg))
                except:
                    pass
        return mensajes

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_banner(titulo):
    print("=" * 40)
    print(titulo)
    print("=" * 40)

def pedir_pin():
    return input("[PIN]: ")

def verificar_acceso(red):
    while True:
        limpiar_pantalla()
        mostrar_banner("RED ANONIMA E2E BLOCKCHAIN")
        pin = pedir_pin()
        if red.verificar_pin(pin):
            red.intentos_fallidos = 0
            break
        else:
            red.intentos_fallidos += 1
            print(f"[ERROR] PIN incorrecto. Intento: {red.intentos_fallidos}")
            time.sleep(1)
            if red.intentos_fallidos >= 5:
                print("[BLOQUEO]")
                time.sleep(2)
                sys.exit()

def obtener_usuario():
    limpiar_pantalla()
    mostrar_banner("IDENTIFICACION")
    nombre = input("NOMBRE DE USUARIO: ").strip().upper()
    return nombre if nombre else "USUARIO"

def mostrar_menu():
    print()
    print("[1] ENVIAR MENSAJE")
    print("[2] BANDEJA ENTRADA")
    print("[3] BLOCKCHAIN")
    print("[4] VERIFICAR RED")
    print("[5] CAMBIAR USUARIO")
    print("[6] SALIR")
    print()

def enviar_mensaje(red, usuario):
    limpiar_pantalla()
    mostrar_banner("ENVIAR MENSAJE")
    print("-" * 40)
    destinatario = input("DESTINATARIO: ").strip().upper()
    mensaje = input("MENSAJE: ")
    
    mensaje_cifrado = red.cifrar_mensaje(red.pin_correcto, mensaje)
    
    datos_bloque = {
        "de": usuario,
        "para": destinatario,
        "mensaje_cifrado": mensaje_cifrado,
        "timestamp": time.time()
    }
    
    bloque = red.agregar_bloque(datos_bloque)
    
    print()
    print(f"[OK] Bloque #{bloque.indice} agregado")
    print(f"HASH: {bloque.hash[:20]}...")
    time.sleep(2)

def ver_bandeja(red, usuario):
    limpiar_pantalla()
    mostrar_banner(f"BANDEJA - {usuario}")
    print("-" * 40)
    
    mensajes = red.obtener_mensajes(usuario)
    
    if mensajes:
        for idx, de, msg in mensajes:
            print(f"[{idx}] DE: {de} >> {msg}")
    else:
        print("[VACIO]")
    
    print()
    input("[ENTER]...")

def ver_blockchain(red):
    limpiar_pantalla()
    mostrar_banner("BLOCKCHAIN")
    print("-" * 40)
    
    red.cargar_bloques()
    for bloque in red.cadena_bloques:
        print(f"BLOQUE #{bloque.indice}")
        print(f"  HASH: {bloque.hash[:24]}...")
        if bloque.indice > 0:
            datos = bloque.datos
            print(f"  DE: {datos.get('de')} > {datos.get('para')}")
        print()
    
    input("[ENTER]...")

def verificar_red(red):
    limpiar_pantalla()
    mostrar_banner("VERIFICAR RED")
    print("-" * 40)
    
    red.cargar_bloques()
    es_valida = red.verificar_cadena()
    
    if es_valida:
        print("[OK] RED VERIFICADA")
    else:
        print("[ERROR] RED COMPROMETIDA")
    
    print(f"BLOQUES: {len(red.cadena_bloques)}")
    time.sleep(2)

def consola(red, usuario):
    while True:
        limpiar_pantalla()
        mostrar_banner("RED ANONIMA E2E")
        print(f"USUARIO: {usuario}")
        print(f"BLOQUES: {len(red.cadena_bloques)}")
        print()
        
        mostrar_menu()
        
        opcion = input("[>] ").strip()
        
        if opcion == "1":
            enviar_mensaje(red, usuario)
        elif opcion == "2":
            ver_bandeja(red, usuario)
        elif opcion == "3":
            ver_blockchain(red)
        elif opcion == "4":
            verificar_red(red)
        elif opcion == "5":
            return obtener_usuario()
        elif opcion == "6":
            print("[SALIENDO]")
            break
        else:
            print("[ERROR]")
            time.sleep(1)
    
    return usuario

def main():
    red = RedAnonimaMensajeria()
    verificar_acceso(red)
    usuario = obtener_usuario()
    
    while True:
        usuario = consola(red, usuario)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[DESCONEXION]")