# microSNMP

> Bibliothèque SNMP v1 minimaliste pour **MicroPython** — développée à des fins académiques à l'IFRN.

**Langues :** [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Français](README.fr.md)

[![MicroPython](https://img.shields.io/badge/MicroPython-1.20%2B-blue)](https://micropython.org/)
[![SNMP](https://img.shields.io/badge/SNMP-v1%20%28RFC%201157%29-green)](https://www.rfc-editor.org/rfc/rfc1157)
[![Licence](https://img.shields.io/badge/licence-MIT-orange)](LICENSE)

---

## Sommaire

- [Vue d'ensemble](#vue-densemble)
- [Qu'est-ce que SNMP ?](#quest-ce-que-snmp-)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Démarrage rapide](#démarrage-rapide)
- [Référence de l'API](#référence-de-lapi)
  - [Classe `SNMPAgent`](#classe-snmpagent)
  - [Classe `OID`](#classe-oid)
  - [Classe `ASN1`](#classe-asn1)
  - [Classe `BER`](#classe-ber)
- [Exemple complet (BitDogLab)](#exemple-complet-bitdoglab)
- [Tests avec des outils SNMP](#tests-avec-des-outils-snmp)
- [Fonctionnement interne](#fonctionnement-interne)
- [Ajouter de nouveaux OID](#ajouter-de-nouveaux-oid)
- [Architecture du projet](#architecture-du-projet)
- [Limitations connues](#limitations-connues)
- [Contribuer](#contribuer)
- [Références](#références)
- [Licence](#licence)

---

## Vue d'ensemble

`microSNMP` est une implémentation pédagogique du protocole **SNMP v1** pour les appareils **MicroPython**, comme la carte **BitDogLab** basée sur le Raspberry Pi Pico W.

Son objectif principal est **éducatif** : la bibliothèque est conçue pour permettre aux étudiants en réseaux informatiques et systèmes embarqués d'apprendre concrètement le fonctionnement de SNMP, la structure de l'encodage ASN.1/BER et l'intégration d'appareils IoT avec des outils de gestion réseau.

**Ce que vous pouvez faire avec elle :**

- Transformer n'importe quel appareil MicroPython en **agent SNMP v1**
- Exposer des variables matérielles, comme la température, l'état des LED et les boutons, via SNMP
- Intégrer l'appareil avec des outils comme `snmpget`, Zabbix, Nagios et PRTG
- Apprendre les bases d'ASN.1 BER et de SNMP par la pratique

---

## Qu'est-ce que SNMP ?

**SNMP** (Simple Network Management Protocol) est un protocole Internet standard pour la **surveillance et la gestion des équipements réseau**. Il est largement utilisé dans les routeurs, commutateurs, serveurs et tout équipement connecté à un réseau.

### Concepts fondamentaux

| Concept | Description |
|---|---|
| **Agent** | Logiciel exécuté sur l'appareil surveillé, par exemple un Pico W, et qui répond aux requêtes |
| **Gestionnaire** | Logiciel qui envoie des requêtes et collecte les données, par exemple Zabbix ou `snmpget` |
| **MIB** | *Management Information Base* — le "dictionnaire" qui décrit les variables disponibles |
| **OID** | *Object Identifier* — l'adresse unique de chaque variable, par exemple `1.3.6.1.2.1.1.1.0` |
| **PDU** | *Protocol Data Unit* — unité de données du protocole, ou message SNMP |
| **Communauté** | Chaîne qui agit comme un mot de passe en SNMPv1, par exemple `"public"` |

### Types d'opération SNMP

```
Gestionnaire ──── GET-REQUEST  ──────────────► Agent
                  (quelle est la valeur de l'OID X ?)

Gestionnaire ◄─── GET-RESPONSE ──────────────  Agent
                  (la valeur de l'OID X est Y)
```

Cette bibliothèque implémente uniquement les opérations **GET**. **SET** et **TRAP** ne sont pas inclus dans cette version pédagogique.

### Structure d'un OID

Un OID est un chemin hiérarchique unique, comme :

```
1 . 3 . 6 . 1 . 2 . 1 . 1 . 1 . 0
│   │   │   │   │   │   │   │   └── instance (0 = scalaire)
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

## Prérequis

- Carte avec **MicroPython**, testée sur BitDogLab / Raspberry Pi Pico W
- **MicroPython 1.20** ou supérieur
- Modules standard requis : `socket`, `network`, `time`, `machine`
- Connexion **Wi-Fi** active, avec la carte sur le même réseau que le gestionnaire SNMP

---

## Installation

### Option 1 - Copier directement le fichier

Copiez `microSNMP.py` à la racine du système de fichiers de votre carte avec **Thonny**, **rshell**, **mpremote** ou un autre outil :

```bash
# Avec mpremote
mpremote cp microSNMP.py :microSNMP.py

# Avec rshell
rshell cp microSNMP.py /pyboard/microSNMP.py
```

### Option 2 - Avec mip, le gestionnaire de paquets MicroPython

```python
import mip
mip.install("github:seu-usuario/microSNMP/microSNMP.py")
```

---

## Démarrage rapide

```python
import network
import time
from microSNMP import SNMPAgent, OID, ASN1

# 1. Connexion au Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("NomDuReseau", "MotDePasse")
while not wlan.isconnected():
    time.sleep(0.1)
print("IP:", wlan.ifconfig()[0])

# 2. Création de l'agent
agent = SNMPAgent(community="public")

# 3. Enregistrement des OID auxquels cet agent répond
agent.register_oid(OID.SYS_DESCR,   lambda: "Mon appareil MicroPython")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)

# 4. Démarrage de la boucle bloquante
agent.start()
```

---

## Référence de l'API

### Classe `SNMPAgent`

Classe principale de l'agent. Elle gère le socket UDP, la table d'OID et le protocole SNMP.

#### Constructeur

```python
SNMPAgent(community="public", port=161, timeout=0.1)
```

| Paramètre | Type | Défaut | Description |
|---|---|---|---|
| `community` | `str` | `"public"` | Chaîne de communauté SNMP, utilisée comme mot de passe en v1 |
| `port` | `int` | `161` | Port UDP d'écoute |
| `timeout` | `float` | `0.1` | Délai d'attente du socket en secondes |

#### Méthodes

##### `register_oid(oid, callback, oid_type=None)`

Enregistre un OID dans la MIB locale de l'agent.

```python
agent.register_oid(OID.SYS_DESCR, lambda: "BitDogLab")
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

| Paramètre | Type | Description |
|---|---|---|
| `oid` | `bytes` | OID au format BER binaire, de préférence via les constantes `OID` |
| `callback` | `callable` | Fonction sans argument qui retourne la valeur actuelle |
| `oid_type` | `int` ou `None` | Type ASN.1, via une constante `ASN1`. Si `None`, il est inféré automatiquement |

**Inférence automatique du type :**

| Type Python | Type ASN.1 inféré |
|---|---|
| `str` | `ASN1.OCTET_STR` |
| `int` | `ASN1.INTEGER` |
| Autre | Erreur — fournissez explicitement `oid_type` |

##### `setup()`

Crée et ouvre le socket UDP. À appeler après l'établissement de la connexion Wi-Fi.

```python
agent.setup()
```

##### `poll()`

Traite un paquet SNMP en mode non bloquant. Retourne `True` si un paquet a été traité, ou `False` si aucun paquet n'était disponible.

```python
while True:
    agent.poll()
    verifier_bouton()
    lire_capteur()
```

##### `start()`

Démarre la boucle bloquante et ne retourne pas. Appelle automatiquement `setup()` si nécessaire.

```python
agent.start()
```

##### `uptime()`

Retourne le temps écoulé depuis la création de l'agent en centièmes de seconde, au format TimeTicks.

```python
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

##### `list_oids()`

Affiche dans la console tous les OID enregistrés, leurs types et leurs valeurs actuelles. Utile pour le débogage.

```python
agent.list_oids()
```

##### `close()`

Ferme le socket et libère le port 161.

```python
agent.close()
```

### Classe `OID`

Constantes d'OID prédéfinies au format BER binaire.

| Constante | OID textuel | Description | Type |
|---|---|---|---|
| `OID.SYS_DESCR` | `1.3.6.1.2.1.1.1.0` | Description du système | OCTET STRING |
| `OID.SYS_UPTIME` | `1.3.6.1.2.1.1.3.0` | Uptime en centièmes de seconde | TimeTicks |
| `OID.SYS_NAME` | `1.3.6.1.2.1.1.5.0` | Nom de l'appareil, ou hostname | OCTET STRING |
| `OID.LED_STATUS` | `1.3.6.1.4.1.21616.1.0` | État de la LED, 0 ou 1 | INTEGER |
| `OID.TEMPERATURE` | `1.3.6.1.4.1.21616.2.0` | Température x 100, par exemple 2573 = 25.73 C | INTEGER |

Pour ajouter des OID personnalisés, consultez [Ajouter de nouveaux OID](#ajouter-de-nouveaux-oid).

### Classe `ASN1`

Constantes des types ASN.1 utilisés par le protocole SNMP.

| Constante | Valeur | Description |
|---|---|---|
| `ASN1.INTEGER` | `0x02` | Entier signé |
| `ASN1.OCTET_STR` | `0x04` | Séquence d'octets / chaîne |
| `ASN1.OBJ_ID` | `0x06` | Object Identifier |
| `ASN1.SEQUENCE` | `0x30` | Séquence ordonnée |
| `ASN1.TIMETICKS` | `0x43` | Centièmes de seconde |
| `ASN1.GET_REQUEST` | `0xA0` | PDU de requête |
| `ASN1.GET_RESPONSE` | `0xA2` | PDU de réponse |

### Classe `BER`

Utilitaires d'encodage ASN.1 BER, utiles pour comprendre ou étendre le protocole.

| Méthode | Description |
|---|---|
| `BER.encode_integer(value)` | Encode un entier en ASN.1 INTEGER |
| `BER.encode_string(text)` | Encode une chaîne en ASN.1 OCTET STRING |
| `BER.encode_timeticks(value)` | Encode un entier en ASN.1 TimeTicks |
| `BER.encode_oid(oid_bytes)` | Encode un OID binaire en ASN.1 OID |
| `BER.encode_length(n)` | Encode une longueur au format BER |
| `BER.wrap_sequence(tag, content)` | Enveloppe le contenu dans une enveloppe TLV |

---

## Exemple complet (BitDogLab)

```python
"""
Exemple complet pour la carte BitDogLab (Raspberry Pi Pico W).

Matériel utilisé :
  - LED sur GPIO 12
  - Bouton sur GPIO 5 avec pull-up interne
  - Capteur de température interne sur le canal ADC 4

OID disponibles :
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

def lire_temperature():
    """Lit la température interne du RP2040 et retourne des centièmes de degré."""
    adc = ADC(4)
    facteur = 3.3 / 65535
    lecture = adc.read_u16() * facteur
    temp = 27 - (lecture - 0.706) / 0.001721
    return int(temp * 100)

def verifier_bouton():
    """Bascule la LED lorsqu'un front descendant est détecté sur le bouton."""
    global last_button
    actuel = button.value()
    if last_button == 1 and actuel == 0:
        led.toggle()
        print("Bouton appuye")
        time.sleep_ms(200)
    last_button = actuel

SSID     = "NomDuReseau"
PASSWORD = "MotDePasse"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Connexion au Wi-Fi...")
while not wlan.isconnected():
    time.sleep(0.1)
print("Connecte ! IP:", wlan.ifconfig()[0])

agent = SNMPAgent(community="public")
agent.register_oid(OID.SYS_DESCR,   lambda: "BitDogLab SNMP - IFRN")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)
agent.register_oid(OID.LED_STATUS,   lambda: led.value())
agent.register_oid(OID.TEMPERATURE,  lire_temperature)

agent.setup()
agent.list_oids()

print("\nAgent pret. En attente de requetes SNMP...")
while True:
    verifier_bouton()
    agent.poll()
```

---

## Tests avec des outils SNMP

### Linux / macOS - `snmp-utils`

```bash
sudo apt install snmp          # Debian/Ubuntu
brew install net-snmp          # macOS

snmpget -v1 -c public <IP_DE_LAPPAREIL> 1.3.6.1.2.1.1.1.0
snmpget -v1 -c public <IP_DE_LAPPAREIL> 1.3.6.1.2.1.1.3.0
snmpget -v1 -c public <IP_DE_LAPPAREIL> 1.3.6.1.4.1.21616.1.0
snmpget -v1 -c public <IP_DE_LAPPAREIL> 1.3.6.1.4.1.21616.2.0
```

### Windows - iReasoning MIB Browser

1. Téléchargez-le depuis : https://www.ireasoning.com/mibbrowser.shtml
2. Renseignez l'adresse IP de l'appareil et la communauté `public`
3. Naviguez jusqu'à l'OID souhaité et cliquez sur **Get**

### Python - bibliothèque `pysnmp`

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
        print("Erreur:", errorIndication)
    else:
        for varBind in varBinds:
            print(varBind.prettyPrint())

snmp_get("192.168.1.100", "1.3.6.1.2.1.1.1.0")
```

---

## Fonctionnement interne

### Flux d'un GET-REQUEST

```
Gestionnaire                        Agent (BitDogLab)
   │                                      │
   │── UDP:161 GET-REQUEST ───────────────►│
   │   SEQUENCE {                          │
   │     INTEGER 0 (SNMPv1)               │  1. Reçoit le paquet UDP
   │     OCTET STRING "public"            │  2. Valide la communauté
   │     GetRequest-PDU {                 │  3. Extrait le request-id
   │       INTEGER request-id             │  4. Identifie l'OID
   │       INTEGER 0 (error)              │  5. Appelle le callback
   │       INTEGER 0 (error-index)        │  6. Encode la valeur en BER
   │       VarBind { OID sysDescr }       │  7. Construit le GET-RESPONSE
   │     }                                │
   │   }                                  │
   │                                      │
   │◄─ UDP:src GET-RESPONSE ──────────────│
```

### Encodage BER (TLV)

Chaque champ du paquet SNMP est encodé en **TLV** (*Type-Length-Value*) :

```
TAG | LONGUEUR | VALEUR

Exemple : INTEGER 1  ->  0x02  0x01  0x01
          STRING "Hi" ->  0x04  0x02  0x48  0x69
```

---

## Ajouter de nouveaux OID

### 1. Définir l'OID binaire

Les OID privés se trouvent sous `1.3.6.1.4.1.<enterprise>`. Pour les projets académiques, vous pouvez utiliser n'importe quel numéro tant que vous n'avez pas de PEN officiel de l'IANA.

La conversion BER suit ces règles :

- Les deux premiers composants `X.Y` deviennent un seul octet : `40*X + Y`
- Les composants inférieurs à 128 utilisent un octet
- Les composants plus grands utilisent un encodage multi-octets avec le bit de poids fort à 1

```python
# OID: 1.3.6.1.4.1.99999.3.0
MON_OID = b'\x2b\x06\x01\x04\x01\x86\x8d\x1f\x03\x00'
```

### 2. L'enregistrer avec un callback

```python
from machine import ADC
adc = ADC(26)

agent.register_oid(MON_OID, lambda: adc.read_u16() >> 8)
```

### 3. Tester avec snmpget

```bash
snmpget -v1 -c public <IP> 1.3.6.1.4.1.99999.3.0
```

---

## Architecture du projet

```
microSNMP/
├── microSNMP.py          <- Bibliothèque principale
├── examples/
│   ├── basic.py          <- Exemple minimal
│   └── bitdoglab.py      <- Exemple complet avec LED, bouton et température
├── README.md             <- README en portugais
├── README.en.md          <- README en anglais
├── README.es.md          <- README en espagnol
├── README.fr.md          <- README en français
└── LICENSE
```

### Diagramme de classes

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

## Limitations connues

| Limitation | Description |
|---|---|
| GET uniquement | SET et TRAP ne sont pas implémentés |
| SNMPv1 uniquement | SNMPv2c et SNMPv3 ne sont pas pris en charge |
| Un OID par requête | GetNextRequest et GetBulk ne sont pas implémentés |
| Pas d'authentification réelle | La communauté est vérifiée par une simple recherche d'octets dans le paquet |
| Entiers jusqu'à 65535 | Les entiers plus grands nécessitent des ajustements dans `BER.encode_integer()` |
| Pas de support SEQUENCE OF | Les tables MIB ne sont pas prises en charge |

---

## Contribuer

Les contributions sont les bienvenues. Il s'agit d'un projet académique centré sur la **clarté du code** et la **qualité de la documentation**.

1. Faites un fork du dépôt
2. Créez une branche : `git checkout -b ma-feature`
3. Validez vos changements : `git commit -m "Ajoute le support de SET"`
4. Poussez la branche : `git push origin ma-feature`
5. Ouvrez une Pull Request

**Idées de contribution :**

- Support de l'opération SET
- Support de TRAP
- Davantage d'OID MIB-II prédéfinis
- Tests unitaires avec paquets SNMP simulés
- Plusieurs OID par requête, comme GetNext

---

## Références

| Document | Description |
|---|---|
| [RFC 1157](https://www.rfc-editor.org/rfc/rfc1157) | A Simple Network Management Protocol (SNMP) |
| [RFC 1155](https://www.rfc-editor.org/rfc/rfc1155) | Structure of Management Information (SMI) |
| [RFC 1213](https://www.rfc-editor.org/rfc/rfc1213) | MIB-II — Management Information Base |
| [X.690 (ITU-T)](https://www.itu.int/rec/T-REC-X.690) | Règles d'encodage ASN.1 BER |
| [MicroPython docs](https://docs.micropython.org/) | Documentation officielle de MicroPython |
| [BitDogLab](https://github.com/BitDogLab/BitDogLab) | Plateforme matérielle éducative |

---

## Licence

MIT License — consultez [LICENSE](LICENSE) pour plus de détails.

---

*Développé à l'IFRN (Institut fédéral du Rio Grande do Norte) à des fins académiques.*
