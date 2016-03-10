# LinkIt 7688, not 7688 Duo!
# PM2.5 Sensor (PMS3003) + 0.96" OLED (SSD1306)
# Sending data to MQTT + ThingSpeak
#
# Used pins for PM2.5 laser dust sensor (PMS3003) are GND, 5V, P18 (UART_RXD0).
# Used pins for 0.96" 128*64 I2C OLED (SSD1306) are GND, 3V3, P20 (I2C SDA), P21 (I2C SCL). 
#
# MQTT Server: gpssensor.ddns.net
# https://thingspeak.com/channels/76698
# http://nrl.iis.sinica.edu.tw/LASS/show.php?device_id=LASS-TST_0226
#
import time
import serial
import binascii
import pyupm_i2clcd as upmLCD
import httplib, urllib, mosquitto

serial_port = serial.Serial( port="/dev/ttyS0", baudrate=9600 )
LCD_096 = upmLCD.SSD1306(0, 0x3C);
LCD_096.clear()

mqtt_msg = ('|ver_format=3|fmt_opt=0|app=PM25|ver_app=0.7.13|device_id=LASS-TST_0226|device=LinkIt7688')
mqttc = mosquitto.Mosquitto("python_pub")
mqttc.connect("gpssensor.ddns.net", 1883)

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

while True:
    serial_port.flush()
    input = serial_port.read(1)
    if input != '\x42': continue
    input = serial_port.read(1)
    if input == '\x4d':
        sensor_data = serial_port.read(22)
        PM_Data = bytearray( sensor_data )
        #
        checksum = 0x42 + 0x4d
        for byte in PM_Data[:-2]:
            checksum = ( checksum + byte ) & 0xFFFF
            if checksum != ( ( PM_Data[20] << 8 ) | PM_Data[21] ):
                print 'Checksum Error'
                continue
        #
        PM_2p5 = ( PM_Data[12-2] << 8 ) | PM_Data[13-2]
        PM_10p = ( PM_Data[14-2] << 8 ) | PM_Data[15-2]
        #
        LCD_096.setCursor( 1, 0 )
        LCD_096.write( 'PM  2.5 = %6d' % PM_2p5 )
        LCD_096.setCursor( 2, 0 )
        LCD_096.write( 'PM 10   = %6d' % PM_10p )
        #
        mqttc.publish( "LASS/Test/PM25", mqtt_msg + '|date=' + time.strftime('%Y-%m-%d')
                                                  + '|time=' + time.strftime('%H:%M:%S')
                                                  + '|s_d0=' + str(PM_2p5) 
                                                  + '|s_d1=' + str(PM_10p) )
        #
        params = urllib.urlencode({'field1': PM_2p5, 'field2': PM_10p, 
                                   'key': 'SVQUYNSSKAHYEIVU'})
        conn = httplib.HTTPConnection("api.thingspeak.com:80")
        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        #
        for x in range(0, 60):
            print binascii.b2a_hex( serial_port.read(24) )

