# microSNMP

> Minimalist SNMP v1 library for **MicroPython** — developed for academic use at IFRN.

**Languages:** [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Français](README.fr.md)

[![MicroPython](https://img.shields.io/badge/MicroPython-1.20%2B-blue)](https://micropython.org/)
[![SNMP](https://img.shields.io/badge/SNMP-v1%20%28RFC%201157%29-green)](https://www.rfc-editor.org/rfc/rfc1157)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [What is SNMP?](#what-is-snmp)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [`SNMPAgent` Class](#snmpagent-class)
  - [`OID` Class](#oid-class)
  - [`ASN1` Class](#asn1-class)
  - [`BER` Class](#ber-class)
- [Complete Example (BitDogLab)](#complete-example-bitdoglab)
- [Testing with SNMP Tools](#testing-with-snmp-tools)
- [How It Works Internally](#how-it-works-internally)
- [Adding New OIDs](#adding-new-oids)
- [Project Architecture](#project-architecture)
- [Known Limitations](#known-limitations)
- [Contributing](#contributing)
- [References](#references)
- [License](#license)

---

## Overview

`microSNMP` is an educational implementation of the **SNMP v1** protocol for **MicroPython** devices, such as the **BitDogLab** board based on the Raspberry Pi Pico W.

Its main goal is **education**: the library is designed so students of computer networks and embedded systems can learn, in practice, how SNMP works, how ASN.1/BER encoding is structured, and how IoT devices integrate with network management tools.

**What you can do with it:**

- Turn any MicroPython device into an **SNMP v1 agent**
- Expose hardware variables such as temperature, LED state, and buttons over SNMP
- Integrate the device with tools such as `snmpget`, Zabbix, Nagios, and PRTG
- Learn ASN.1 BER and SNMP fundamentals hands-on

---

## What is SNMP?

**SNMP** (Simple Network Management Protocol) is a standard Internet protocol for **monitoring and managing network devices**. It is widely used in routers, switches, servers, and any device connected to a network.

### Core concepts

| Concept | Description |
|---|---|
| **Agent** | Software running on the monitored device, for example a Pico W, that replies to queries |
| **Manager** | Software that sends queries and collects data, for example Zabbix or `snmpget` |
| **MIB** | *Management Information Base* — the "dictionary" that describes which variables exist |
| **OID** | *Object Identifier* — the unique address of each variable, for example `1.3.6.1.2.1.1.1.0` |
| **PDU** | *Protocol Data Unit* — the protocol data unit, or SNMP message |
| **Community** | String that acts like a password in SNMPv1, for example `"public"` |

### SNMP operation types

```
Manager ──── GET-REQUEST  ──────────────► Agent
             (what is the value of OID X?)

Manager ◄─── GET-RESPONSE ──────────────  Agent
             (the value of OID X is Y)
```

This library implements only **GET** operations. **SET** and **TRAP** are not included in this educational version.

### OID structure

An OID is a unique hierarchical path, such as:

```
1 . 3 . 6 . 1 . 2 . 1 . 1 . 1 . 0
│   │   │   │   │   │   │   │   └── instance (0 = scalar)
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

## Requirements

- Board with **MicroPython**, tested on BitDogLab / Raspberry Pi Pico W
- **MicroPython 1.20** or newer
- Required standard modules: `socket`, `network`, `time`, `machine`
- Active **Wi-Fi** connection, with the board on the same network as the SNMP manager

---

## Installation

### Option 1 - Copy the file directly

Copy `microSNMP.py` to the root of your board filesystem using **Thonny**, **rshell**, **mpremote**, or another tool:

```bash
# With mpremote
mpremote cp microSNMP.py :microSNMP.py

# With rshell
rshell cp microSNMP.py /pyboard/microSNMP.py
```

### Option 2 - Using mip, the MicroPython package manager

```python
import mip
mip.install("github:seu-usuario/microSNMP/microSNMP.py")
```

---

## Quick Start

```python
import network
import time
from microSNMP import SNMPAgent, OID, ASN1

# 1. Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("NetworkName", "NetworkPassword")
while not wlan.isconnected():
    time.sleep(0.1)
print("IP:", wlan.ifconfig()[0])

# 2. Create the agent
agent = SNMPAgent(community="public")

# 3. Register the OIDs answered by this agent
agent.register_oid(OID.SYS_DESCR,   lambda: "My MicroPython device")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)

# 4. Start the blocking loop
agent.start()
```

---

## API Reference

### `SNMPAgent` Class

Main agent class. It manages the UDP socket, OID table, and SNMP protocol.

#### Constructor

```python
SNMPAgent(community="public", port=161, timeout=0.1)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `community` | `str` | `"public"` | SNMP community string, used like a password in v1 |
| `port` | `int` | `161` | UDP listening port |
| `timeout` | `float` | `0.1` | Socket timeout in seconds |

#### Methods

##### `register_oid(oid, callback, oid_type=None)`

Registers an OID in the agent local MIB.

```python
agent.register_oid(OID.SYS_DESCR, lambda: "BitDogLab")
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

| Parameter | Type | Description |
|---|---|---|
| `oid` | `bytes` | OID in binary BER format, preferably using `OID` constants |
| `callback` | `callable` | Function with no arguments that returns the current value |
| `oid_type` | `int` or `None` | ASN.1 type, using an `ASN1` constant. If `None`, it is inferred automatically |

**Automatic type inference:**

| Python type | Inferred ASN.1 type |
|---|---|
| `str` | `ASN1.OCTET_STR` |
| `int` | `ASN1.INTEGER` |
| Other | Error — provide `oid_type` explicitly |

##### `setup()`

Creates and opens the UDP socket. Call it after the Wi-Fi connection is ready.

```python
agent.setup()
```

##### `poll()`

Processes one SNMP packet in non-blocking mode. Returns `True` if a packet was processed, or `False` if no packet was available.

```python
while True:
    agent.poll()
    check_button()
    read_sensor()
```

##### `start()`

Starts the blocking loop and does not return. It calls `setup()` automatically if needed.

```python
agent.start()
```

##### `uptime()`

Returns the time since the agent was created in hundredths of a second, using the TimeTicks format.

```python
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

##### `list_oids()`

Prints all registered OIDs, their types, and current values to the console. Useful for debugging.

```python
agent.list_oids()
```

##### `close()`

Closes the socket and releases port 161.

```python
agent.close()
```

### `OID` Class

Predefined OID constants in binary BER format.

| Constant | Textual OID | Description | Type |
|---|---|---|---|
| `OID.SYS_DESCR` | `1.3.6.1.2.1.1.1.0` | System description | OCTET STRING |
| `OID.SYS_UPTIME` | `1.3.6.1.2.1.1.3.0` | Uptime in hundredths of a second | TimeTicks |
| `OID.SYS_NAME` | `1.3.6.1.2.1.1.5.0` | Device name, or hostname | OCTET STRING |
| `OID.LED_STATUS` | `1.3.6.1.4.1.21616.1.0` | LED state, 0 or 1 | INTEGER |
| `OID.TEMPERATURE` | `1.3.6.1.4.1.21616.2.0` | Temperature x 100, for example 2573 = 25.73 C | INTEGER |

To add custom OIDs, see [Adding New OIDs](#adding-new-oids).

### `ASN1` Class

Constants for ASN.1 types used by the SNMP protocol.

| Constant | Value | Description |
|---|---|---|
| `ASN1.INTEGER` | `0x02` | Signed integer |
| `ASN1.OCTET_STR` | `0x04` | Byte sequence / string |
| `ASN1.OBJ_ID` | `0x06` | Object Identifier |
| `ASN1.SEQUENCE` | `0x30` | Ordered sequence |
| `ASN1.TIMETICKS` | `0x43` | Hundredths of a second |
| `ASN1.GET_REQUEST` | `0xA0` | Request PDU |
| `ASN1.GET_RESPONSE` | `0xA2` | Response PDU |

### `BER` Class

ASN.1 BER encoding utilities, useful for understanding or extending the protocol.

| Method | Description |
|---|---|
| `BER.encode_integer(value)` | Encodes an integer as ASN.1 INTEGER |
| `BER.encode_string(text)` | Encodes a string as ASN.1 OCTET STRING |
| `BER.encode_timeticks(value)` | Encodes an integer as ASN.1 TimeTicks |
| `BER.encode_oid(oid_bytes)` | Encodes a binary OID as ASN.1 OID |
| `BER.encode_length(n)` | Encodes a length in BER format |
| `BER.wrap_sequence(tag, content)` | Wraps content in a TLV envelope |

---

## Complete Example (BitDogLab)

```python
"""
Complete example for the BitDogLab board (Raspberry Pi Pico W).

Hardware used:
  - LED on GPIO 12
  - Button on GPIO 5 with internal pull-up
  - Internal temperature sensor on ADC channel 4

Available OIDs:
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

def read_temperature():
    """Reads the RP2040 internal temperature and returns hundredths of a degree."""
    adc = ADC(4)
    factor = 3.3 / 65535
    reading = adc.read_u16() * factor
    temp = 27 - (reading - 0.706) / 0.001721
    return int(temp * 100)

def check_button():
    """Toggles the LED when a falling edge is detected on the button."""
    global last_button
    current = button.value()
    if last_button == 1 and current == 0:
        led.toggle()
        print("Button pressed")
        time.sleep_ms(200)
    last_button = current

SSID     = "NetworkName"
PASSWORD = "NetworkPassword"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Connecting to Wi-Fi...")
while not wlan.isconnected():
    time.sleep(0.1)
print("Connected! IP:", wlan.ifconfig()[0])

agent = SNMPAgent(community="public")
agent.register_oid(OID.SYS_DESCR,   lambda: "BitDogLab SNMP - IFRN")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)
agent.register_oid(OID.LED_STATUS,   lambda: led.value())
agent.register_oid(OID.TEMPERATURE,  read_temperature)

agent.setup()
agent.list_oids()

print("\nAgent ready. Waiting for SNMP requests...")
while True:
    check_button()
    agent.poll()
```

---

## Testing with SNMP Tools

### Linux / macOS - `snmp-utils`

```bash
sudo apt install snmp          # Debian/Ubuntu
brew install net-snmp          # macOS

snmpget -v1 -c public <DEVICE_IP> 1.3.6.1.2.1.1.1.0
snmpget -v1 -c public <DEVICE_IP> 1.3.6.1.2.1.1.3.0
snmpget -v1 -c public <DEVICE_IP> 1.3.6.1.4.1.21616.1.0
snmpget -v1 -c public <DEVICE_IP> 1.3.6.1.4.1.21616.2.0
```

### Windows - iReasoning MIB Browser

1. Download it from: https://www.ireasoning.com/mibbrowser.shtml
2. Enter the device IP and the `public` community
3. Navigate to the desired OID and click **Get**

### Python - `pysnmp` library

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

## How It Works Internally

### GET-REQUEST flow

```
Manager                            Agent (BitDogLab)
   │                                      │
   │── UDP:161 GET-REQUEST ───────────────►│
   │   SEQUENCE {                          │
   │     INTEGER 0 (SNMPv1)               │  1. Receives the UDP packet
   │     OCTET STRING "public"            │  2. Validates the community
   │     GetRequest-PDU {                 │  3. Extracts the request-id
   │       INTEGER request-id             │  4. Identifies the OID
   │       INTEGER 0 (error)              │  5. Calls the callback
   │       INTEGER 0 (error-index)        │  6. Encodes the value in BER
   │       VarBind { OID sysDescr }       │  7. Builds the GET-RESPONSE
   │     }                                │
   │   }                                  │
   │                                      │
   │◄─ UDP:src GET-RESPONSE ──────────────│
```

### BER encoding (TLV)

Each SNMP packet field is encoded as **TLV** (*Type-Length-Value*):

```
TAG | LENGTH | VALUE

Example: INTEGER 1  ->  0x02  0x01  0x01
         STRING "Hi" ->  0x04  0x02  0x48  0x69
```

---

## Adding New OIDs

### 1. Define the binary OID

Private OIDs live under `1.3.6.1.4.1.<enterprise>`. For academic projects, you can use any number while you do not have an official IANA PEN.

BER conversion follows these rules:

- The first two components `X.Y` become one byte: `40*X + Y`
- Components below 128 use one byte
- Larger components use multi-byte encoding with the most significant bit set to 1

```python
# OID: 1.3.6.1.4.1.99999.3.0
MY_OID = b'\x2b\x06\x01\x04\x01\x86\x8d\x1f\x03\x00'
```

### 2. Register it with a callback

```python
from machine import ADC
adc = ADC(26)

agent.register_oid(MY_OID, lambda: adc.read_u16() >> 8)
```

### 3. Test with snmpget

```bash
snmpget -v1 -c public <IP> 1.3.6.1.4.1.99999.3.0
```

---

## Project Architecture

```
microSNMP/
├── microSNMP.py          <- Main library
├── examples/
│   ├── basic.py          <- Minimal example
│   └── bitdoglab.py      <- Complete example with LED, button, and temperature
├── README.md             <- Portuguese README
├── README.en.md          <- English README
├── README.es.md          <- Spanish README
├── README.fr.md          <- French README
└── LICENSE
```

### Class diagram

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

## Known Limitations

| Limitation | Description |
|---|---|
| GET only | SET and TRAP are not implemented |
| SNMPv1 only | SNMPv2c and SNMPv3 are not supported |
| One OID per request | GetNextRequest and GetBulk are not implemented |
| No real authentication | The community is checked with a simple byte search in the packet |
| Integers up to 65535 | Larger integers need adjustments in `BER.encode_integer()` |
| No SEQUENCE OF support | MIB tables are not supported |

---

## Contributing

Contributions are welcome. This is an academic project focused on **code clarity** and **documentation quality**.

1. Fork the repository
2. Create a branch: `git checkout -b my-feature`
3. Commit your changes: `git commit -m "Add SET support"`
4. Push: `git push origin my-feature`
5. Open a Pull Request

**Contribution ideas:**

- SET operation support
- TRAP support
- More predefined MIB-II OIDs
- Unit tests with simulated SNMP packets
- Multiple OIDs per request, such as GetNext

---

## References

| Document | Description |
|---|---|
| [RFC 1157](https://www.rfc-editor.org/rfc/rfc1157) | A Simple Network Management Protocol (SNMP) |
| [RFC 1155](https://www.rfc-editor.org/rfc/rfc1155) | Structure of Management Information (SMI) |
| [RFC 1213](https://www.rfc-editor.org/rfc/rfc1213) | MIB-II — Management Information Base |
| [X.690 (ITU-T)](https://www.itu.int/rec/T-REC-X.690) | ASN.1 BER encoding rules |
| [MicroPython docs](https://docs.micropython.org/) | Official MicroPython documentation |
| [BitDogLab](https://github.com/BitDogLab/BitDogLab) | Educational hardware platform |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Developed at IFRN (Federal Institute of Rio Grande do Norte) for academic use.*
