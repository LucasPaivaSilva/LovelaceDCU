#include <Arduino.h>
#include "config.h"
#include <HardwareSerial.h>
#include <ESP32CAN.h>
#include <CAN_config.h>
#include <SPI.h>
#include <SD.h>

#define FILE_NAME "/lovelace2506.csv"

// Função para listar diretórios
void listDir(fs::FS &fs, const char *dirname, uint8_t levels)
{
    Serial.printf("Listing directory: %s\n", dirname);

    File root = fs.open(dirname);
    if (!root)
    {
        Serial.println("Failed to open directory");
        return;
    }
    if (!root.isDirectory())
    {
        Serial.println("Not a directory");
        return;
    }

    File file = root.openNextFile();
    while (file)
    {
        if (file.isDirectory())
        {
            Serial.print("  DIR : ");
            Serial.println(file.name());
            if (levels)
            {
                // listDir(fs, file, levels -1);
            }
        }
        else
        {
            Serial.print("  FILE: ");
            Serial.print(file.name());
            Serial.print("  SIZE: ");
            Serial.println(file.size());
        }
        file = root.openNextFile();
    }
}

// Função para criar diretórios
void createDir(fs::FS &fs, const char *path)
{
    Serial.printf("Creating Dir: %s\n", path);
    if (fs.mkdir(path))
    {
        Serial.println("Dir created");
    }
    else
    {
        Serial.println("mkdir failed");
    }
}

// Função para remover diretórios
void removeDir(fs::FS &fs, const char *path)
{
    Serial.printf("Removing Dir: %s\n", path);
    if (fs.rmdir(path))
    {
        Serial.println("Dir removed");
    }
    else
    {
        Serial.println("rmdir failed");
    }
}

// Função para ler arquivos
void readFile(fs::FS &fs, const char *path)
{
    Serial.printf("Reading file: %s\n", path);

    File file = fs.open(path);
    if (!file)
    {
        Serial.println("Failed to open file for reading");
        return;
    }

    Serial.print("Read from file: ");
    while (file.available())
    {
        Serial.write(file.read());
    }
    file.close();
}

// Função para escrever arquivos
void writeFile(fs::FS &fs, const char *path, const char *message)
{
    Serial.printf("Writing file: %s\n", path);

    File file = fs.open(path, FILE_WRITE);
    if (!file)
    {
        Serial.println("Failed to open file for writing");
        return;
    }
    if (file.print(message))
    {
        Serial.println("File written");
    }
    else
    {
        Serial.println("Write failed");
    }
    file.close();
}

// Função para adicionar a arquivos
void appendFile(fs::FS &fs, const char *path, const char *message)
{
    Serial.printf("Appending to file: %s\n", path);

    File file = fs.open(path, FILE_APPEND);
    if (!file)
    {
        Serial.println("Failed to open file for appending");
        return;
    }
    if (file.print(message))
    {
        Serial.println("Message appended");
    }
    else
    {
        Serial.println("Append failed");
    }
    file.close();
}

// Função para deletar arquivos
void deleteFile(fs::FS &fs, const char *path)
{
    Serial.printf("Deleting file: %s\n", path);
    if (fs.remove(path))
    {
        Serial.println("File deleted");
    }
    else
    {
        Serial.println("Delete failed");
    }
}

// Testar SD Card
void SD_test(void)
{
    SPI.begin(SD_SCLK_PIN, SD_MISO_PIN, SD_MOSI_PIN, SD_CS_PIN);
    if (!SD.begin(SD_CS_PIN, SPI)) {
        Serial.println("SDCard MOUNT FAIL");
    } else {
        uint32_t cardSize = SD.cardSize() / (1024 * 1024);
        String str = "SDCard Size: " + String(cardSize) + "MB";
        Serial.println(str);
    }

    uint64_t cardSize = SD.cardSize() / (1024 * 1024);
    Serial.printf("SD Card Size: %lluMB\n", cardSize);
    Serial.printf("Total space: %lluMB\n", SD.totalBytes() / (1024 * 1024));
    Serial.printf("Used space: %lluMB\n", SD.usedBytes() / (1024 * 1024));



}

// Configuração do CAN
CAN_device_t CAN_cfg;
const int interval = 5000;
unsigned long previousMillis = 0;

// Função de setup
void setup()
{
    pinMode(PIN_5V_EN, OUTPUT);
    digitalWrite(PIN_5V_EN, HIGH);

    pinMode(CAN_SE_PIN, OUTPUT);
    digitalWrite(CAN_SE_PIN, LOW);

    Serial.begin(115200);

    SD_test();

    delay(10000);

    Serial.println("Basic Demo - ESP32-Arduino-CAN");
    CAN_cfg.speed = CAN_SPEED_500KBPS;
    CAN_cfg.tx_pin_id = GPIO_NUM_27;
    CAN_cfg.rx_pin_id = GPIO_NUM_26;
    CAN_cfg.rx_queue = xQueueCreate(10, sizeof(CAN_frame_t));

    // Init CAN Module
    ESP32Can.CANInit();

    Serial.print("CAN SPEED :");
    Serial.println(CAN_cfg.speed);

    // Verificar e criar arquivo CSV se necessário
    if (!SD.exists(FILE_NAME))
    {
        writeFile(SD, FILE_NAME, "tempoDoSistema,frameType,msgId,DLC,data0,data1,data2,data3,data4,data5,data6,data7\n");
    }
}

// Função de loop
void loop()
{
    CAN_frame_t rx_frame;
    unsigned long currentMillis = millis();

    // Receber próxima trama CAN da fila
    if (xQueueReceive(CAN_cfg.rx_queue, &rx_frame, 3 * portTICK_PERIOD_MS) == pdTRUE)
    {
        // Obter o tempo do sistema
        unsigned long tempoDoSistema = millis();

        // Determinar o tipo de quadro
        const char* frameType = (rx_frame.FIR.B.FF == CAN_frame_std) ? "standard" : "extended";

        // Obter o ID da mensagem e DLC
        uint32_t msgId = rx_frame.MsgID;
        uint8_t dlc = rx_frame.FIR.B.DLC;

        // Obter dados da mensagem
        char data[100];
        snprintf(data, sizeof(data), "%lu,%s,%08X,%u,%02X,%02X,%02X,%02X,%02X,%02X,%02X,%02X\n",
                 tempoDoSistema, frameType, msgId, dlc,
                 rx_frame.data.u8[0], rx_frame.data.u8[1], rx_frame.data.u8[2], rx_frame.data.u8[3],
                 rx_frame.data.u8[4], rx_frame.data.u8[5], rx_frame.data.u8[6], rx_frame.data.u8[7]);

        // Adicionar ao arquivo CSV
        appendFile(SD, FILE_NAME, data);

        // Print debug information
        Serial.print(data);
    }

    // Enviar mensagem CAN
    if (currentMillis - previousMillis >= interval)
    {
        previousMillis = currentMillis;
        CAN_frame_t tx_frame;
        tx_frame.FIR.B.FF = CAN_frame_std;
        tx_frame.MsgID = 0x042;
        tx_frame.FIR.B.DLC = 8;
        tx_frame.data.u8[0] = 0xFF;
        tx_frame.data.u8[1] = 0xFF;
        tx_frame.data.u8[2] = 0x03;
        tx_frame.data.u8[3] = 0x03;
        tx_frame.data.u8[4] = 0xFF;
        tx_frame.data.u8[5] = 0x05;
        tx_frame.data.u8[6] = 0x06;
        tx_frame.data.u8[7] = 0x07;

        //ESP32Can.CANWriteFrame(&tx_frame);
        Serial.println("CAN send done");
    }
}