# microSNMP

> Biblioteca SNMP v1 minimalista para **MicroPython** — desarrollada con fines académicos en el IFRN.

**Idiomas:** [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Français](README.fr.md)

[![MicroPython](https://img.shields.io/badge/MicroPython-1.20%2B-blue)](https://micropython.org/)
[![SNMP](https://img.shields.io/badge/SNMP-v1%20%28RFC%201157%29-green)](https://www.rfc-editor.org/rfc/rfc1157)
[![Licencia](https://img.shields.io/badge/licencia-MIT-orange)](LICENSE)

---

## Índice

- [Descripción general](#descripción-general)
- [¿Qué es SNMP?](#qué-es-snmp)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso rápido](#uso-rápido)
- [Referencia de la API](#referencia-de-la-api)
  - [Clase `SNMPAgent`](#clase-snmpagent)
  - [Clase `OID`](#clase-oid)
  - [Clase `ASN1`](#clase-asn1)
  - [Clase `BER`](#clase-ber)
- [Ejemplo completo (BitDogLab)](#ejemplo-completo-bitdoglab)
- [Pruebas con herramientas SNMP](#pruebas-con-herramientas-snmp)
- [Funcionamiento interno](#funcionamiento-interno)
- [Agregar nuevos OIDs](#agregar-nuevos-oids)
- [Arquitectura del proyecto](#arquitectura-del-proyecto)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Contribuir](#contribuir)
- [Referencias](#referencias)
- [Licencia](#licencia)

---

## Descripción general

`microSNMP` es una implementación didáctica del protocolo **SNMP v1** para dispositivos con **MicroPython**, como la placa **BitDogLab** basada en Raspberry Pi Pico W.

Su objetivo principal es **educativo**: la biblioteca fue diseñada para que estudiantes de redes de computadoras y sistemas embebidos puedan aprender en la práctica cómo funciona SNMP, cómo se estructura la codificación ASN.1/BER y cómo se integran dispositivos IoT con herramientas de gestión de redes.

**Qué puedes hacer con ella:**

- Convertir cualquier dispositivo MicroPython en un **agente SNMP v1**
- Exponer variables de hardware, como temperatura, estado de LEDs y botones, mediante SNMP
- Integrar el dispositivo con herramientas como `snmpget`, Zabbix, Nagios y PRTG
- Aprender los fundamentos de ASN.1 BER y SNMP de forma práctica

---

## ¿Qué es SNMP?

**SNMP** (Simple Network Management Protocol) es un protocolo estándar de Internet para el **monitoreo y la gestión de dispositivos de red**. Se usa ampliamente en routers, switches, servidores y cualquier equipo conectado a una red.

### Conceptos fundamentales

| Concepto | Descripción |
|---|---|
| **Agente** | Software que se ejecuta en el dispositivo monitoreado, por ejemplo un Pico W, y responde consultas |
| **Gestor** | Software que envía consultas y recopila datos, por ejemplo Zabbix o `snmpget` |
| **MIB** | *Management Information Base* — el "diccionario" que describe qué variables existen |
| **OID** | *Object Identifier* — la dirección única de cada variable, por ejemplo `1.3.6.1.2.1.1.1.0` |
| **PDU** | *Protocol Data Unit* — unidad de datos del protocolo, o mensaje SNMP |
| **Comunidad** | Cadena que actúa como contraseña en SNMPv1, por ejemplo `"public"` |

### Tipos de operación SNMP

```
Gestor ──── GET-REQUEST  ──────────────► Agente
            (¿cuál es el valor del OID X?)

Gestor ◄─── GET-RESPONSE ──────────────  Agente
            (el valor del OID X es Y)
```

Esta biblioteca implementa solo operaciones **GET**. **SET** y **TRAP** no están incluidos en esta versión didáctica.

### Estructura de un OID

Un OID es una ruta jerárquica única, como:

```
1 . 3 . 6 . 1 . 2 . 1 . 1 . 1 . 0
│   │   │   │   │   │   │   │   └── instancia (0 = escalar)
│   │   │   │   │   │   │   └────── sysDescr
│   │   │   │   │   │   └────────── system group
│   │   │   │   │   └────────────── mib-2
│   │   │   │   └────────────────── mgmt
│   │   │   └────────────────────── internet
│   │   └────────────────────────── dod
│   └────────────────────────────── org
└────────────────────────────────── iso
```

---

## Requisitos

- Placa con **MicroPython**, probada en BitDogLab / Raspberry Pi Pico W
- **MicroPython 1.20** o superior
- Módulos estándar necesarios: `socket`, `network`, `time`, `machine`
- Conexión **Wi-Fi** activa, con la placa en la misma red que el gestor SNMP

---

## Instalación

### Opción 1 - Copiar el archivo directamente

Copia `microSNMP.py` en la raíz del sistema de archivos de tu placa usando **Thonny**, **rshell**, **mpremote** u otra herramienta:

```bash
# Con mpremote
mpremote cp microSNMP.py :microSNMP.py

# Con rshell
rshell cp microSNMP.py /pyboard/microSNMP.py
```

### Opción 2 - Usando mip, el gestor de paquetes de MicroPython

```python
import mip
mip.install("github:seu-usuario/microSNMP/microSNMP.py")
```

---

## Uso rápido

```python
import network
import time
from microSNMP import SNMPAgent, OID, ASN1

# 1. Conecta al Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("NombreDeRed", "ContrasenaDeRed")
while not wlan.isconnected():
    time.sleep(0.1)
print("IP:", wlan.ifconfig()[0])

# 2. Crea el agente
agent = SNMPAgent(community="public")

# 3. Registra los OIDs que responde este agente
agent.register_oid(OID.SYS_DESCR,   lambda: "Mi dispositivo MicroPython")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)

# 4. Inicia el bucle bloqueante
agent.start()
```

---

## Referencia de la API

### Clase `SNMPAgent`

Clase principal del agente. Gestiona el socket UDP, la tabla de OIDs y el protocolo SNMP.

#### Constructor

```python
SNMPAgent(community="public", port=161, timeout=0.1)
```

| Parámetro | Tipo | Valor predeterminado | Descripción |
|---|---|---|---|
| `community` | `str` | `"public"` | Cadena de comunidad SNMP, usada como contraseña en v1 |
| `port` | `int` | `161` | Puerto UDP de escucha |
| `timeout` | `float` | `0.1` | Tiempo de espera del socket en segundos |

#### Métodos

##### `register_oid(oid, callback, oid_type=None)`

Registra un OID en la MIB local del agente.

```python
agent.register_oid(OID.SYS_DESCR, lambda: "BitDogLab")
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

| Parámetro | Tipo | Descripción |
|---|---|---|
| `oid` | `bytes` | OID en formato BER binario, preferiblemente usando constantes de `OID` |
| `callback` | `callable` | Función sin argumentos que devuelve el valor actual |
| `oid_type` | `int` o `None` | Tipo ASN.1, usando una constante de `ASN1`. Si es `None`, se infiere automáticamente |

**Inferencia automática de tipo:**

| Tipo Python | Tipo ASN.1 inferido |
|---|---|
| `str` | `ASN1.OCTET_STR` |
| `int` | `ASN1.INTEGER` |
| Otros | Error — indica `oid_type` explícitamente |

##### `setup()`

Crea y abre el socket UDP. Debe llamarse después de que la conexión Wi-Fi esté lista.

```python
agent.setup()
```

##### `poll()`

Procesa un paquete SNMP en modo no bloqueante. Devuelve `True` si se procesó un paquete o `False` si no había paquetes disponibles.

```python
while True:
    agent.poll()
    verificar_boton()
    leer_sensor()
```

##### `start()`

Inicia el bucle bloqueante y no retorna. Llama a `setup()` automáticamente si es necesario.

```python
agent.start()
```

##### `uptime()`

Devuelve el tiempo desde la creación del agente en centésimas de segundo, usando el formato TimeTicks.

```python
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

##### `list_oids()`

Imprime en consola todos los OIDs registrados, sus tipos y valores actuales. Es útil para depuración.

```python
agent.list_oids()
```

##### `close()`

Cierra el socket y libera el puerto 161.

```python
agent.close()
```

### Clase `OID`

Constantes de OIDs predefinidos en formato BER binario.

| Constante | OID textual | Descripción | Tipo |
|---|---|---|---|
| `OID.SYS_DESCR` | `1.3.6.1.2.1.1.1.0` | Descripción del sistema | OCTET STRING |
| `OID.SYS_UPTIME` | `1.3.6.1.2.1.1.3.0` | Uptime en centésimas de segundo | TimeTicks |
| `OID.SYS_NAME` | `1.3.6.1.2.1.1.5.0` | Nombre del dispositivo, o hostname | OCTET STRING |
| `OID.LED_STATUS` | `1.3.6.1.4.1.21616.1.0` | Estado del LED, 0 o 1 | INTEGER |
| `OID.TEMPERATURE` | `1.3.6.1.4.1.21616.2.0` | Temperatura x 100, por ejemplo 2573 = 25.73 C | INTEGER |

Para agregar OIDs personalizados, consulta [Agregar nuevos OIDs](#agregar-nuevos-oids).

### Clase `ASN1`

Constantes de los tipos ASN.1 usados por el protocolo SNMP.

| Constante | Valor | Descripción |
|---|---|---|
| `ASN1.INTEGER` | `0x02` | Entero con signo |
| `ASN1.OCTET_STR` | `0x04` | Secuencia de bytes / string |
| `ASN1.OBJ_ID` | `0x06` | Object Identifier |
| `ASN1.SEQUENCE` | `0x30` | Secuencia ordenada |
| `ASN1.TIMETICKS` | `0x43` | Centésimas de segundo |
| `ASN1.GET_REQUEST` | `0xA0` | PDU de solicitud |
| `ASN1.GET_RESPONSE` | `0xA2` | PDU de respuesta |

### Clase `BER`

Utilidades de codificación ASN.1 BER, útiles para entender o extender el protocolo.

| Método | Descripción |
|---|---|
| `BER.encode_integer(value)` | Codifica un entero como ASN.1 INTEGER |
| `BER.encode_string(text)` | Codifica una string como ASN.1 OCTET STRING |
| `BER.encode_timeticks(value)` | Codifica un entero como ASN.1 TimeTicks |
| `BER.encode_oid(oid_bytes)` | Codifica un OID binario como ASN.1 OID |
| `BER.encode_length(n)` | Codifica una longitud en formato BER |
| `BER.wrap_sequence(tag, content)` | Envuelve contenido en un sobre TLV |

---

## Ejemplo completo (BitDogLab)

```python
"""
Ejemplo completo para la placa BitDogLab (Raspberry Pi Pico W).

Hardware utilizado:
  - LED en GPIO 12
  - Boton en GPIO 5 con pull-up interno
  - Sensor interno de temperatura en ADC canal 4

OIDs disponibles:
  sysDescr    -> 1.3.6.1.2.1.1.1.0
  sysUpTime   -> 1.3.6.1.2.1.1.3.0
  ledStatus   -> 1.3.6.1.4.1.21616.1.0
  temperature -> 1.3.6.1.4.1.21616.2.0
"""

import network
import machine
import time
from machine import Pin, ADC
from microSNMP import SNMPAgent, OID, ASN1

led    = Pin(12, Pin.OUT)
button = Pin(5, Pin.IN, Pin.PULL_UP)
last_button = 1

def leer_temperatura():
    """Lee la temperatura interna del RP2040 y devuelve centesimas de grado."""
    adc = ADC(4)
    factor = 3.3 / 65535
    lectura = adc.read_u16() * factor
    temp = 27 - (lectura - 0.706) / 0.001721
    return int(temp * 100)

def verificar_boton():
    """Alterna el LED al detectar un flanco descendente en el boton."""
    global last_button
    actual = button.value()
    if last_button == 1 and actual == 0:
        led.toggle()
        print("Boton presionado")
        time.sleep_ms(200)
    last_button = actual

SSID     = "NombreDeRed"
PASSWORD = "ContrasenaDeRed"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Conectando al Wi-Fi...")
while not wlan.isconnected():
    time.sleep(0.1)
print("Conectado! IP:", wlan.ifconfig()[0])

agent = SNMPAgent(community="public")
agent.register_oid(OID.SYS_DESCR,   lambda: "BitDogLab SNMP - IFRN")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)
agent.register_oid(OID.LED_STATUS,   lambda: led.value())
agent.register_oid(OID.TEMPERATURE,  leer_temperatura)

agent.setup()
agent.list_oids()

print("\nAgente listo. Esperando solicitudes SNMP...")
while True:
    verificar_boton()
    agent.poll()
```

---

## Pruebas con herramientas SNMP

### Linux / macOS - `snmp-utils`

```bash
sudo apt install snmp          # Debian/Ubuntu
brew install net-snmp          # macOS

snmpget -v1 -c public <IP_DEL_DISPOSITIVO> 1.3.6.1.2.1.1.1.0
snmpget -v1 -c public <IP_DEL_DISPOSITIVO> 1.3.6.1.2.1.1.3.0
snmpget -v1 -c public <IP_DEL_DISPOSITIVO> 1.3.6.1.4.1.21616.1.0
snmpget -v1 -c public <IP_DEL_DISPOSITIVO> 1.3.6.1.4.1.21616.2.0
```

### Windows - iReasoning MIB Browser

1. Descárgalo desde: https://www.ireasoning.com/mibbrowser.shtml
2. Informa la IP del dispositivo y la comunidad `public`
3. Navega hasta el OID deseado y haz clic en **Get**

### Python - biblioteca `pysnmp`

```python
from pysnmp.hlapi import *

def snmp_get(ip, oid):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData("public", mpModel=0),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
    if errorIndication:
        print("Error:", errorIndication)
    else:
        for varBind in varBinds:
            print(varBind.prettyPrint())

snmp_get("192.168.1.100", "1.3.6.1.2.1.1.1.0")
```

---

## Funcionamiento interno

### Flujo de un GET-REQUEST

```
Gestor                             Agente (BitDogLab)
   │                                      │
   │── UDP:161 GET-REQUEST ───────────────►│
   │   SEQUENCE {                          │
   │     INTEGER 0 (SNMPv1)               │  1. Recibe el paquete UDP
   │     OCTET STRING "public"            │  2. Valida la comunidad
   │     GetRequest-PDU {                 │  3. Extrae el request-id
   │       INTEGER request-id             │  4. Identifica el OID
   │       INTEGER 0 (error)              │  5. Llama al callback
   │       INTEGER 0 (error-index)        │  6. Codifica el valor en BER
   │       VarBind { OID sysDescr }       │  7. Construye el GET-RESPONSE
   │     }                                │
   │   }                                  │
   │                                      │
   │◄─ UDP:src GET-RESPONSE ──────────────│
```

### Codificación BER (TLV)

Cada campo del paquete SNMP se codifica como **TLV** (*Type-Length-Value*):

```
TAG | LONGITUD | VALOR

Ejemplo: INTEGER 1  ->  0x02  0x01  0x01
         STRING "Hi" ->  0x04  0x02  0x48  0x69
```

---

## Agregar nuevos OIDs

### 1. Define el OID binario

Los OIDs privados se ubican bajo `1.3.6.1.4.1.<enterprise>`. Para proyectos académicos, puedes usar cualquier número mientras no tengas un PEN oficial de IANA.

La conversión a BER sigue estas reglas:

- Los dos primeros componentes `X.Y` se convierten en un byte: `40*X + Y`
- Componentes menores que 128 usan un byte
- Componentes mayores usan codificación multi-byte con el bit más significativo en 1

```python
# OID: 1.3.6.1.4.1.99999.3.0
MI_OID = b'\x2b\x06\x01\x04\x01\x86\x8d\x1f\x03\x00'
```

### 2. Regístralo con un callback

```python
from machine import ADC
adc = ADC(26)

agent.register_oid(MI_OID, lambda: adc.read_u16() >> 8)
```

### 3. Prueba con snmpget

```bash
snmpget -v1 -c public <IP> 1.3.6.1.4.1.99999.3.0
```

---

## Arquitectura del proyecto

```
microSNMP/
├── microSNMP.py          <- Biblioteca principal
├── examples/
│   ├── basic.py          <- Ejemplo mínimo
│   └── bitdoglab.py      <- Ejemplo completo con LED, botón y temperatura
├── README.md             <- README en portugués
├── README.en.md          <- README en inglés
├── README.es.md          <- README en español
├── README.fr.md          <- README en francés
└── LICENSE
```

### Diagrama de clases

```
SNMPAgent
├── _oid_table: list[OIDEntry]
├── _sock: socket
├── register_oid(oid, callback, oid_type) -> OIDEntry
├── setup()
├── poll() -> _handle_request()

OIDEntry
├── oid: bytes
├── callback: callable
├── oid_type: int | None
├── get_value()
└── encode_value() -> BER.*

BER
├── encode_integer(value)
├── encode_string(text)
├── encode_timeticks(value)
├── encode_oid(oid_bytes)
├── encode_length(n)
└── wrap_sequence(tag, content)
```

---

## Limitaciones conocidas

| Limitación | Descripción |
|---|---|
| Solo GET | SET y TRAP no están implementados |
| Solo SNMPv1 | SNMPv2c y SNMPv3 no están soportados |
| Un OID por solicitud | GetNextRequest y GetBulk no están implementados |
| Sin autenticación real | La comunidad se verifica mediante una búsqueda simple de bytes en el paquete |
| Enteros hasta 65535 | Enteros mayores necesitan ajustes en `BER.encode_integer()` |
| Sin soporte para SEQUENCE OF | Las tablas MIB no están soportadas |

---

## Contribuir

Las contribuciones son bienvenidas. Este es un proyecto académico centrado en la **claridad del código** y la **calidad de la documentación**.

1. Haz un fork del repositorio
2. Crea una rama: `git checkout -b mi-feature`
3. Haz commit de los cambios: `git commit -m "Agrega soporte para SET"`
4. Haz push: `git push origin mi-feature`
5. Abre un Pull Request

**Ideas de contribución:**

- Soporte para la operación SET
- Soporte para TRAP
- Más OIDs MIB-II predefinidos
- Pruebas unitarias con paquetes SNMP simulados
- Múltiples OIDs por solicitud, como GetNext

---

## Referencias

| Documento | Descripción |
|---|---|
| [RFC 1157](https://www.rfc-editor.org/rfc/rfc1157) | A Simple Network Management Protocol (SNMP) |
| [RFC 1155](https://www.rfc-editor.org/rfc/rfc1155) | Structure of Management Information (SMI) |
| [RFC 1213](https://www.rfc-editor.org/rfc/rfc1213) | MIB-II — Management Information Base |
| [X.690 (ITU-T)](https://www.itu.int/rec/T-REC-X.690) | Reglas de codificación ASN.1 BER |
| [MicroPython docs](https://docs.micropython.org/) | Documentación oficial de MicroPython |
| [BitDogLab](https://github.com/BitDogLab/BitDogLab) | Plataforma de hardware educativo |

---

## Licencia

MIT License — consulta [LICENSE](LICENSE) para más detalles.

---

*Desarrollado en el IFRN (Instituto Federal de Rio Grande do Norte) con fines académicos.*
