# microSNMP

> Biblioteca SNMP v1 minimalista para **MicroPython** — desenvolvida para fins acadêmicos no IFRN.

**Idiomas:** [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Français](README.fr.md)

[![MicroPython](https://img.shields.io/badge/MicroPython-1.20%2B-blue)](https://micropython.org/)
[![SNMP](https://img.shields.io/badge/SNMP-v1%20%28RFC%201157%29-green)](https://www.rfc-editor.org/rfc/rfc1157)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-orange)](LICENSE)

---

## Sumário

- [Visão Geral](#visão-geral)
- [O que é SNMP?](#o-que-é-snmp)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Uso Rápido](#uso-rápido)
- [Referência da API](#referência-da-api)
  - [Classe `SNMPAgent`](#classe-snmpagent)
  - [Classe `OID`](#classe-oid)
  - [Classe `ASN1`](#classe-asn1)
  - [Classe `BER`](#classe-ber)
- [Exemplo Completo (BitDogLab)](#exemplo-completo-bitdoglab)
- [Testando com ferramentas SNMP](#testando-com-ferramentas-snmp)
- [Como funciona internamente](#como-funciona-internamente)
- [Adicionando novos OIDs](#adicionando-novos-oids)
- [Arquitetura do projeto](#arquitetura-do-projeto)
- [Limitações conhecidas](#limitações-conhecidas)
- [Contribuindo](#contribuindo)
- [Referências](#referências)

---

## Visão Geral

`microSNMP` é uma implementação didática do protocolo **SNMP v1** para dispositivos com **MicroPython**, como a placa **BitDogLab** (baseada no Raspberry Pi Pico W).

O objetivo principal é **educacional**: a biblioteca foi projetada para que estudantes de redes de computadores e sistemas embarcados possam aprender na prática como funciona o protocolo SNMP, a codificação ASN.1/BER e a integração de dispositivos IoT com ferramentas de gerência de redes.

**O que você consegue fazer com ela:**

- Transformar qualquer dispositivo MicroPython em um **agente SNMP v1**
- Expor variáveis do hardware (temperatura, estado de LEDs, botões) via SNMP
- Integrar o dispositivo com ferramentas como `snmpget`, Zabbix, Nagios, PRTG
- Aprender os fundamentos de ASN.1 BER e do protocolo SNMP na prática

---

## O que é SNMP?

**SNMP** (Simple Network Management Protocol) é um protocolo padrão da Internet para **monitoramento e gerenciamento de dispositivos de rede**. É amplamente utilizado em roteadores, switches, servidores e qualquer equipamento conectado a uma rede.

### Conceitos fundamentais

| Conceito | Descrição |
|---|---|
| **Agente** | Software que roda no dispositivo monitorado (ex: seu Pico W) e responde a consultas |
| **Gerente** | Software que envia consultas e coleta dados (ex: Zabbix, `snmpget`) |
| **MIB** | *Management Information Base* — "dicionário" que descreve quais variáveis existem |
| **OID** | *Object Identifier* — endereço único de cada variável (ex: `1.3.6.1.2.1.1.1.0`) |
| **PDU** | *Protocol Data Unit* — unidade de dados do protocolo (mensagem SNMP) |
| **Comunidade** | String que funciona como senha no SNMPv1 (ex: `"public"`) |

### Tipos de operação SNMP

```
Gerente ──── GET-REQUEST  ──────────────► Agente
             (qual o valor do OID X?)

Gerente ◄─── GET-RESPONSE ──────────────  Agente
             (o valor do OID X é Y)
```

Esta biblioteca implementa apenas o **GET** (leitura). O **SET** (escrita) e o **TRAP** (notificação) não estão incluídos nesta versão didática.

### Estrutura de um OID

Um OID é um caminho hierárquico único, como:

```
1 . 3 . 6 . 1 . 2 . 1 . 1 . 1 . 0
│   │   │   │   │   │   │   │   └── instância (0 = escalar)
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

## Pré-requisitos

- Placa com **MicroPython** (testado na BitDogLab / Raspberry Pi Pico W)
- MicroPython **1.20** ou superior
- Módulos padrão necessários: `socket`, `network`, `time`, `machine`
- Conexão **Wi-Fi** ativa (a placa deve estar na mesma rede que o gerente SNMP)

---

## Instalação

### Opção 1 — Copiar o arquivo diretamente

Copie o arquivo `microSNMP.py` para a raiz do sistema de arquivos da sua placa usando **Thonny**, **rshell**, **mpremote** ou qualquer outra ferramenta:

```bash
# Com mpremote
mpremote cp microSNMP.py :microSNMP.py

# Com rshell
rshell cp microSNMP.py /pyboard/microSNMP.py
```

### Opção 2 — Via mip (MicroPython package manager)

```python
import mip
mip.install("github:seu-usuario/microSNMP/microSNMP.py")
```

---

## Uso Rápido

```python
import network
import time
from microSNMP import SNMPAgent, OID, ASN1

# 1. Conecta ao Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("NomeDaRede", "SenhaDaRede")
while not wlan.isconnected():
    time.sleep(0.1)
print("IP:", wlan.ifconfig()[0])

# 2. Cria o agente
agent = SNMPAgent(community="public")

# 3. Registra os OIDs que este agente responde
agent.register_oid(OID.SYS_DESCR,   lambda: "Meu dispositivo MicroPython")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)

# 4. Inicia (loop bloqueante)
agent.start()
```

---

## Referência da API

### Classe `SNMPAgent`

Classe principal do agente. Gerencia o socket UDP, a tabela de OIDs e o protocolo SNMP.

#### Construtor

```python
SNMPAgent(community="public", port=161, timeout=0.1)
```

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `community` | `str` | `"public"` | String de comunidade SNMP (funciona como senha no v1) |
| `port` | `int` | `161` | Porta UDP de escuta |
| `timeout` | `float` | `0.1` | Timeout do socket em segundos |

#### Métodos

---

##### `register_oid(oid, callback, oid_type=None)`

Registra um OID na MIB local do agente.

```python
agent.register_oid(OID.SYS_DESCR, lambda: "BitDogLab")
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `oid` | `bytes` | OID em formato BER binário (use as constantes de `OID`) |
| `callback` | `callable` | Função sem argumentos que retorna o valor atual |
| `oid_type` | `int` ou `None` | Tipo ASN.1 (constante de `ASN1`). Se `None`, inferido automaticamente |

**Inferência automática de tipo:**

| Tipo Python | Tipo ASN.1 inferido |
|---|---|
| `str` | `ASN1.OCTET_STR` |
| `int` | `ASN1.INTEGER` |
| Outros | Erro — informe `oid_type` explicitamente |

---

##### `setup()`

Cria e abre o socket UDP. Deve ser chamado após a conexão Wi-Fi estar pronta.

```python
agent.setup()
```

---

##### `poll()`

Processa um pacote SNMP (não bloqueante). Retorna `True` se um pacote foi processado, `False` se não havia pacotes.

```python
while True:
    agent.poll()
    verificar_botao()
    ler_sensor()
```

---

##### `start()`

Inicia o loop bloqueante (não retorna). Chama `setup()` automaticamente se necessário.

```python
agent.start()
```

---

##### `uptime()`

Retorna o tempo desde a criação do agente em centésimos de segundo (formato TimeTicks).

```python
agent.register_oid(OID.SYS_UPTIME, lambda: agent.uptime(), ASN1.TIMETICKS)
```

---

##### `list_oids()`

Imprime no console todos os OIDs registrados com seus tipos e valores atuais. Útil para depuração.

```python
agent.list_oids()
```

---

##### `close()`

Fecha o socket e libera a porta 161.

```python
agent.close()
```

---

### Classe `OID`

Constantes de OIDs pré-definidos em formato BER binário.

| Constante | OID textual | Descrição | Tipo |
|---|---|---|---|
| `OID.SYS_DESCR` | `1.3.6.1.2.1.1.1.0` | Descrição do sistema | OCTET STRING |
| `OID.SYS_UPTIME` | `1.3.6.1.2.1.1.3.0` | Uptime em centésimos de segundo | TimeTicks |
| `OID.SYS_NAME` | `1.3.6.1.2.1.1.5.0` | Nome do dispositivo (hostname) | OCTET STRING |
| `OID.LED_STATUS` | `1.3.6.1.4.1.21616.1.0` | Estado do LED (0/1) | INTEGER |
| `OID.TEMPERATURE` | `1.3.6.1.4.1.21616.2.0` | Temperatura × 100 (ex: 2573 = 25,73°C) | INTEGER |

Para adicionar OIDs personalizados, veja a seção [Adicionando novos OIDs](#adicionando-novos-oids).

---

### Classe `ASN1`

Constantes dos tipos ASN.1 usados no protocolo SNMP.

| Constante | Valor | Descrição |
|---|---|---|
| `ASN1.INTEGER` | `0x02` | Número inteiro com sinal |
| `ASN1.OCTET_STR` | `0x04` | Sequência de bytes / string |
| `ASN1.OBJ_ID` | `0x06` | Object Identifier |
| `ASN1.SEQUENCE` | `0x30` | Sequência ordenada |
| `ASN1.TIMETICKS` | `0x43` | Centésimos de segundo |
| `ASN1.GET_REQUEST` | `0xA0` | PDU de requisição |
| `ASN1.GET_RESPONSE` | `0xA2` | PDU de resposta |

---

### Classe `BER`

Utilitários de codificação ASN.1 BER. Útil para quem quer entender ou estender o protocolo.

| Método | Descrição |
|---|---|
| `BER.encode_integer(value)` | Codifica inteiro como ASN.1 INTEGER |
| `BER.encode_string(text)` | Codifica string como ASN.1 OCTET STRING |
| `BER.encode_timeticks(value)` | Codifica inteiro como ASN.1 TimeTicks |
| `BER.encode_oid(oid_bytes)` | Codifica OID binário como ASN.1 OID |
| `BER.encode_length(n)` | Codifica comprimento no formato BER |
| `BER.wrap_sequence(tag, content)` | Envolve conteúdo em envelope TLV |

---

## Exemplo Completo (BitDogLab)

```python
"""
Exemplo completo para a placa BitDogLab (Raspberry Pi Pico W).

Hardware utilizado:
  - LED no GPIO 12
  - Botão no GPIO 5 (pull-up interno)
  - Sensor de temperatura interno (ADC canal 4)

OIDs disponíveis:
  sysDescr    → 1.3.6.1.2.1.1.1.0
  sysUpTime   → 1.3.6.1.2.1.1.3.0
  ledStatus   → 1.3.6.1.4.1.21616.1.0
  temperature → 1.3.6.1.4.1.21616.2.0
"""

import network
import machine
import time
from machine import Pin, ADC
from microSNMP import SNMPAgent, OID, ASN1

# --- Hardware ---
led    = Pin(12, Pin.OUT)
button = Pin(5, Pin.IN, Pin.PULL_UP)
last_button = 1

def ler_temperatura():
    """Lê a temperatura interna do RP2040 e retorna em centésimos de grau."""
    adc = ADC(4)
    fator = 3.3 / 65535
    leitura = adc.read_u16() * fator
    temp = 27 - (leitura - 0.706) / 0.001721
    return int(temp * 100)  # ex: 2573 = 25,73°C

def verificar_botao():
    """Alterna o LED ao detectar borda de descida no botão."""
    global last_button
    atual = button.value()
    if last_button == 1 and atual == 0:
        led.toggle()
        print("Botão pressionado")
        time.sleep_ms(200)
    last_button = atual

# --- Wi-Fi ---
SSID     = "NomeDaRede"
PASSWORD = "SenhaDaRede"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Conectando ao Wi-Fi...")
while not wlan.isconnected():
    time.sleep(0.1)
print("Conectado! IP:", wlan.ifconfig()[0])

# --- Agente SNMP ---
agent = SNMPAgent(community="public")

agent.register_oid(OID.SYS_DESCR,   lambda: "BitDogLab SNMP - IFRN")
agent.register_oid(OID.SYS_UPTIME,  lambda: agent.uptime(), ASN1.TIMETICKS)
agent.register_oid(OID.LED_STATUS,   lambda: led.value())
agent.register_oid(OID.TEMPERATURE,  ler_temperatura)

agent.setup()
agent.list_oids()  # exibe tabela de OIDs no console

# --- Loop principal ---
print("\nAgente pronto. Aguardando requisições SNMP...")
while True:
    verificar_botao()   # verifica o botão a cada ciclo
    agent.poll()        # processa 1 pacote SNMP (non-blocking)
```

---

## Testando com ferramentas SNMP

### Linux / macOS — `snmp-utils`

```bash
# Instalar
sudo apt install snmp          # Debian/Ubuntu
brew install net-snmp          # macOS

# Consultar sysDescr
snmpget -v1 -c public <IP_DO_DISPOSITIVO> 1.3.6.1.2.1.1.1.0

# Consultar sysUpTime
snmpget -v1 -c public <IP_DO_DISPOSITIVO> 1.3.6.1.2.1.1.3.0

# Consultar LED
snmpget -v1 -c public <IP_DO_DISPOSITIVO> 1.3.6.1.4.1.21616.1.0

# Consultar temperatura (valor × 100)
snmpget -v1 -c public <IP_DO_DISPOSITIVO> 1.3.6.1.4.1.21616.2.0
```

### Windows — iReasoning MIB Browser

1. Baixe em: https://www.ireasoning.com/mibbrowser.shtml
2. Informe o IP do dispositivo e a comunidade `public`
3. Navegue até o OID desejado e clique em **Get**

### Python — biblioteca `pysnmp`

```python
from pysnmp.hlapi import *

def snmp_get(ip, oid):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData("public", mpModel=0),  # mpModel=0 → SNMPv1
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
    if errorIndication:
        print("Erro:", errorIndication)
    else:
        for varBind in varBinds:
            print(varBind.prettyPrint())

snmp_get("192.168.1.100", "1.3.6.1.2.1.1.1.0")
```

---

## Como funciona internamente

### Fluxo de um GET-REQUEST

```
Gerente                            Agente (BitDogLab)
   │                                      │
   │── UDP:161 GET-REQUEST ───────────────►│
   │   SEQUENCE {                          │
   │     INTEGER 0 (SNMPv1)               │  1. Recebe o pacote UDP
   │     OCTET STRING "public"            │  2. Valida a comunidade
   │     GetRequest-PDU {                 │  3. Extrai o request-id
   │       INTEGER request-id             │  4. Identifica o OID
   │       INTEGER 0 (error)              │  5. Chama o callback
   │       INTEGER 0 (error-index)        │  6. Codifica o valor em BER
   │       VarBind { OID sysDescr }       │  7. Monta o GET-RESPONSE
   │     }                                │
   │   }                                  │
   │                                      │
   │◄─ UDP:src GET-RESPONSE ──────────────│
   │   SEQUENCE {                          │
   │     INTEGER 0 (SNMPv1)               │
   │     OCTET STRING "public"            │
   │     GetResponse-PDU {                │
   │       INTEGER request-id (mesmo)     │
   │       INTEGER 0 (sem erro)           │
   │       INTEGER 0 (sem erro)           │
   │       VarBind {                      │
   │         OID sysDescr                 │
   │         OCTET STRING "BitDogLab..."  │
   │       }                              │
   │     }                                │
   │   }                                  │
```

### Codificação BER (TLV)

Cada campo do pacote SNMP é codificado no formato **TLV** (*Type-Length-Value*):

```
┌─────────┬──────────────┬──────────────────────┐
│  TAG    │  COMPRIMENTO │  VALOR               │
│ (1 byte)│ (1-3 bytes)  │ (N bytes)            │
└─────────┴──────────────┴──────────────────────┘

Exemplo: INTEGER 1  →  0x02  0x01  0x01
         STRING "Hi" →  0x04  0x02  0x48  0x69
```

---

## Adicionando novos OIDs

### 1. Defina o OID binário

OIDs privados ficam sob `1.3.6.1.4.1.<enterprise>`. Para projetos acadêmicos, use qualquer número enquanto não registrar um PEN (Private Enterprise Number) oficial na IANA.

A conversão para BER segue estas regras:
- Os dois primeiros componentes `X.Y` viram um único byte: `40*X + Y`
- Componentes menores que 128: um byte com o valor
- Componentes maiores: codificação multi-byte com bit mais significativo = 1

```python
# OID: 1.3.6.1.4.1.99999.3.0
# 1.3 → 0x2B
# 6   → 0x06
# 1   → 0x01
# 4   → 0x04
# 1   → 0x01
# 99999 → codificação multi-byte: 0x86, 0x8D, 0x1F
# 3   → 0x03
# 0   → 0x00

MEU_OID = b'\x2b\x06\x01\x04\x01\x86\x8d\x1f\x03\x00'
```

### 2. Registre com um callback

```python
# Leitura de um pino analógico
from machine import ADC
adc = ADC(26)

agent.register_oid(MEU_OID, lambda: adc.read_u16() >> 8)
# O tipo será inferido como INTEGER (valor inteiro)
```

### 3. Teste com snmpget

```bash
snmpget -v1 -c public <IP> 1.3.6.1.4.1.99999.3.0
```

---

## Arquitetura do projeto

```
microSNMP/
├── microSNMP.py          ← Biblioteca principal
├── examples/
│   ├── basic.py          ← Exemplo mínimo
│   └── bitdoglab.py      ← Exemplo completo com LED, botão e temperatura
├── README.md             ← Este arquivo
└── LICENSE
```

### Diagrama de classes

```
SNMPAgent
│
├── _oid_table: list[OIDEntry]
├── _sock: socket
│
├── register_oid(oid, callback, oid_type) ──► OIDEntry
├── setup()
├── poll() ─────────────────────────────────► _handle_request()
│                                                  │
│                                             _parse_request()
│                                             _build_response()
│                                                  │
│                                             BER.encode_*()
│
OIDEntry
│
├── oid: bytes
├── callback: callable
├── oid_type: int | None
│
├── get_value()
└── encode_value() ──────────────────────────► BER.*

BER (métodos estáticos)
├── encode_integer(value)
├── encode_string(text)
├── encode_timeticks(value)
├── encode_oid(oid_bytes)
├── encode_length(n)
└── wrap_sequence(tag, content)

OID (constantes)
ASN1 (constantes)
SNMPError (constantes)
```

---

## Limitações conhecidas

| Limitação | Descrição |
|---|---|
| Apenas GET | SET e TRAP não implementados |
| SNMPv1 apenas | SNMPv2c e SNMPv3 não suportados |
| Um OID por requisição | GetNextRequest e GetBulk não implementados |
| Sem autenticação real | A comunidade é comparada por simples busca de bytes no pacote |
| Valores inteiros até 65535 | Inteiros maiores precisam de ajuste em `BER.encode_integer()` |
| Sem suporte a SEQUENCE OF | Tabelas MIB não são suportadas |

---

## Contribuindo

Contribuições são bem-vindas! Este é um projeto acadêmico e o foco é a **clareza do código** e a **qualidade da documentação**.

Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch: `git checkout -b minha-feature`
3. Faça commit das alterações: `git commit -m "Adiciona suporte a SET"`
4. Faça push: `git push origin minha-feature`
5. Abra um Pull Request

**Ideias de contribuição:**
- Suporte a operação SET (escrita de variáveis)
- Suporte a TRAP (notificações proativas)
- Mais OIDs MIB-II pré-definidos
- Testes unitários com pacotes SNMP simulados
- Suporte a múltiplos OIDs por requisição (GetNext)

---

## Referências

| Documento | Descrição |
|---|---|
| [RFC 1157](https://www.rfc-editor.org/rfc/rfc1157) | A Simple Network Management Protocol (SNMP) |
| [RFC 1155](https://www.rfc-editor.org/rfc/rfc1155) | Structure of Management Information (SMI) |
| [RFC 1213](https://www.rfc-editor.org/rfc/rfc1213) | MIB-II — Management Information Base |
| [X.690 (ITU-T)](https://www.itu.int/rec/T-REC-X.690) | ASN.1 BER encoding rules |
| [MicroPython docs](https://docs.micropython.org/) | Documentação oficial do MicroPython |
| [BitDogLab](https://github.com/BitDogLab/BitDogLab) | Plataforma de hardware educacional |

---

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

*Desenvolvido no IFRN (Instituto Federal do Rio Grande do Norte) para fins acadêmicos.*
