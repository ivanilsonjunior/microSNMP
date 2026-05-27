import socket
import network
import machine
import time
from machine import Pin

# ==========================================
# LED
# ==========================================

led = Pin(12, Pin.OUT)

# ==========================================
# BOTÃO
# GPIO 5 é exemplo
# ajuste conforme sua BitDogLab
# ==========================================

button = Pin(5, Pin.IN, Pin.PULL_UP)

last_button_state = 1

# ==========================================
# TEMPERATURA
# ==========================================

def getTemp():
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / 65535
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    return round(temperature, 2)

# ==========================================
# UPTIME
# ==========================================

start_time = time.ticks_ms()

def get_uptime():
    uptime = time.ticks_diff(time.ticks_ms(), start_time)
    return int(uptime / 10)

# ==========================================
# ALTERA LED PELO BOTÃO
# ==========================================

def check_button():
    global last_button_state
    current = button.value()
    # detecta borda de descida
    if last_button_state == 1 and current == 0:
        led.toggle()
        print("Botão pressionado")
        time.sleep_ms(200)  # debounce
    last_button_state = current

# ==========================================
# INTEGER ASN.1
# ==========================================

def encode_integer(value):
    if value < 256:
        return bytes([
            0x02,
            0x01,
            value
        ])
    else:
        return bytes([
            0x02,
            0x02,
            (value >> 8) & 0xff,
            value & 0xff
        ])

# ==========================================
# WIFI
# ==========================================

SSID = 'wIFRN-IoT'
PASSWORD = 'deviceiotifrn'
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Conectando WiFi...")
while not wlan.isconnected():
    pass

ip = wlan.ifconfig()[0]
print("WiFi conectado")
print("IP:", ip)

# ==========================================
# OIDs
# ==========================================

SYS_DESCR_OID = b'\x2b\x06\x01\x02\x01\x01\x01\x00'
SYS_UPTIME_OID = b'\x2b\x06\x01\x02\x01\x01\x03\x00'
LED_OID = b'\x2b\x06\x01\x04\x01\xa6\x70\x01\x00'
TEMP_OID = b'\x2b\x06\x01\x04\x01\xa6\x70\x02\x00'

# ==========================================
# SOCKET SNMP
# ==========================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 161))
sock.settimeout(0.1)
print("Agente SNMP iniciado")

# ==========================================
# LOOP PRINCIPAL
# ==========================================

while True:
    # ======================================
    # VERIFICA BOTÃO
    # ======================================
    check_button()
    try:
        data, addr = sock.recvfrom(1024)
    except:
        continue

    print("\nPacote SNMP recebido")
    # ======================================
    # REQUEST-ID DINÂMICO
    # ======================================
    rid_index = data.find(b'\x02\x04')
    if rid_index == -1:
        continue
    request_id = data[rid_index + 2:rid_index + 6]
    oid = None
    varbind = bytearray()

    # ======================================
    # sysDescr
    # ======================================
    if SYS_DESCR_OID in data:
        print("Consulta sysDescr")
        oid = SYS_DESCR_OID
        descricao = "BitDogLab SNMP - IFRN - Ivanilson"
        descricao = descricao.encode()
        varbind.extend([
            0x06,
            len(oid)
        ])
        varbind.extend(oid)
        varbind.extend([
            0x04,
            len(descricao)
        ])
        varbind.extend(descricao)

    # ======================================
    # sysUpTime
    # ======================================
    elif SYS_UPTIME_OID in data:
        print("Consulta sysUpTime")
        oid = SYS_UPTIME_OID
        uptime = get_uptime()
        varbind.extend([
            0x06,
            len(oid)
        ])
        varbind.extend(oid)
        varbind.extend([
            0x43,
            0x04,
            (uptime >> 24) & 0xff,
            (uptime >> 16) & 0xff,
            (uptime >> 8) & 0xff,
            uptime & 0xff
        ])

    # ======================================
    # LED
    # ======================================
    elif LED_OID in data:
        print("Consulta LED")
        oid = LED_OID
        valor = led.value()
        varbind.extend([
            0x06,
            len(oid)
        ])
        varbind.extend(oid)
        varbind.extend(encode_integer(valor))

    # ======================================
    # TEMPERATURA
    # ======================================

    elif TEMP_OID in data:
        print("Consulta Temperatura")
        oid = TEMP_OID
        temperatura = int(getTemp() * 100)
        print("Temperatura:", temperatura)
        varbind.extend([
            0x06,
            len(oid)
        ])
        varbind.extend(oid)
        varbind.extend(encode_integer(temperatura))
    else:
        print("OID desconhecida")
        continue

    # ======================================
    # VARBIND
    # ======================================
    vb = bytearray()
    vb.extend([
        0x30,
        len(varbind)
    ])
    vb.extend(varbind)

    # ======================================
    # VARBIND LIST
    # ======================================
    vblist = bytearray()
    vblist.extend([
        0x30,
        len(vb)
    ])
    vblist.extend(vb)

    # ======================================
    # PDU
    # ======================================

    pdu = bytearray()
    pdu.extend([
        0x02,
        0x04
    ])
    pdu.extend(request_id)
    pdu.extend([
        0x02,
        0x01,
        0x00
    ])
    pdu.extend([
        0x02,
        0x01,
        0x00
    ])
    pdu.extend(vblist)
    pdu_final = bytearray()
    pdu_final.extend([
        0xA2,
        len(pdu)
    ])
    pdu_final.extend(pdu)

    # ======================================
    # SNMP MESSAGE
    # ======================================
    msg = bytearray()
    msg.extend([
        0x02,
        0x01,
        0x00
    ])
    msg.extend([
        0x04,
        0x06
    ])
    msg.extend(b'public')
    msg.extend(pdu_final)

    # ======================================
    # RESPOSTA FINAL
    # ======================================

    response = bytearray()
    response.extend([
        0x30,
        len(msg)
    ])
    response.extend(msg)
    sock.sendto(response, addr)
    print("Resposta enviada")