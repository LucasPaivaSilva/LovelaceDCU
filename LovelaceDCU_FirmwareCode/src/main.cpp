#include <Arduino.h>
#include "config.h"
#include <HardwareSerial.h>
#include <ESP32CAN.h>
#include <CAN_config.h>
#include <SPI.h>
#include <SD.h>

#include <WiFi.h>
#include <ESPAsyncWebServer.h>

// Variáveis para exibição
float inverterTemp = 12.3; // Exemplo
float motorTemp = 45.6; // Exemplo
int inverterErrorCode = 0; // Exemplo
uint8_t pwmData, dpsUsage, torqueCode, errorCode;
// Variáveis adicionais
float hvVoltage = 350.0;  // Exemplo de inicialização
float torqueLimit = 0; // Exemplo de inicialização

float dcCurrent = 1234;
float inverterPower = 1234;
float motorPower = 1234;
float motorRPM = 1234;

// Configuração da Rede WiFi
const char* ssid = "Lovelace-DCU";
const char* password = "15072024";

#define FILE_NAME "/lovelace1507-ufsc.csv"

bool flagUpdateTorqueMode = false;
uint8_t torqueModeMod = 0;

// Criar objeto servidor na porta 80
AsyncWebServer server(80);

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
    //Serial.printf("Appending to file: %s\n", path);

    File file = fs.open(path, FILE_APPEND);
    if (!file)
    {
        Serial.println("Failed to open file for appending");
        return;
    }
    if (file.print(message))
    {
        //Serial.println("Message appended");
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

void sendTorqueMod(int mode){
    CAN_frame_t tx_frame;
    tx_frame.FIR.B.FF = CAN_frame_std;
    tx_frame.MsgID = 0x041;
    tx_frame.FIR.B.DLC = 8;
    tx_frame.data.u8[0] = 0xFF;
    tx_frame.data.u8[1] = 0xFF;
    tx_frame.data.u8[2] = 0xFF;
    tx_frame.data.u8[3] = 0xFF;
    tx_frame.data.u8[4] = 0xFF;
    tx_frame.data.u8[5] = 0xFF;
    tx_frame.data.u8[6] = 0xFF;
    tx_frame.data.u8[7] = 0xFF;
    switch (mode)
    {
    case 1:
        tx_frame.data.u8[0] = 0x01;
        break;
    case 2:
        tx_frame.data.u8[0] = 0x02;
        break;
    case 3: 
        tx_frame.data.u8[0] = 0x03;
        break;
    case 4:
        tx_frame.data.u8[0] = 0x04;
        break;
    case 5:
        tx_frame.data.u8[0] = 0x05;
        break;
    
    default:
        tx_frame.data.u8[0] = 0x00;
        break;
    }
    ESP32Can.CANWriteFrame(&tx_frame);

}

// Configuração do CAN
CAN_device_t CAN_cfg;
const int interval = 5000;
unsigned long previousMillis = 0;

void setupServer() {
    // Inicializa o ESP32 como um ponto de acesso
    WiFi.softAP(ssid, password);
    IPAddress IP = WiFi.softAPIP();
    Serial.println();
    Serial.print("IP do Ponto de Acesso: ");
    Serial.println(IP);

    // Rotas
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        char htmlResponse[4000];
        sprintf(htmlResponse, "<!DOCTYPE html><html><head><title>LovelaceDCU</title>"
                              "<meta charset=\"UTF-8\">"
                              "<style>"
                              "body { font-family: Arial, sans-serif; font-size: 24px; }"
                              "h1 { font-size: 36px; color: navy; }"
                              "button { font-size: 30px; margin: 10px; padding: 10px; }"
                              "</style>"
                              "<script>"
                              "setInterval(function() {"
                              "fetch('/data').then(response => response.json()).then(data => {"
                              "document.getElementById('tempInversor').innerText = data.tempInversor.toFixed(1) + '°C';"
                              "document.getElementById('tempMotor').innerText = data.tempMotor.toFixed(1) + '°C';"
                              "document.getElementById('erro').innerText = data.erro;"
                              "document.getElementById('hvVoltage').innerText = data.hvVoltage.toFixed(1) + 'V';"
                              "document.getElementById('torqueLimit').innerText = data.torqueLimit.toFixed(1);"
                              "document.getElementById('hvCurrent').innerText = data.hvCurrent.toFixed(1) + 'A';"
                              "document.getElementById('motorPower').innerText = data.motorPower.toFixed(1) + 'W';"
                              "document.getElementById('inverterPower').innerText = data.inverterPower.toFixed(1) + 'W';"
                              "document.getElementById('motorRPM').innerText = data.motorRPM.toFixed(1) + ' RPM';"
                              "});"
                              "}, 1000);"
                              "</script>"
                              "</head><body>"
                              "<h1>Lovelace DCU - WebServer</h1>"
                              "<button onclick=\"location.href='/func1'\">Mode1</button>"
                              "<button onclick=\"location.href='/func2'\">Mode2</button>"
                              "<button onclick=\"location.href='/func3'\">Mode3</button>"
                              "<button onclick=\"location.href='/func4'\">Mode4</button>"
                              "<p>Inverter temperature: <span id='tempInversor'>%.1f°C</span></p>"
                              "<p>Motor temperature: <span id='tempMotor'>%.1f°C</span></p>"
                              "<p>Error: <span id='erro'>%d</span></p>"
                              "<p>HV Voltage: <span id='hvVoltage'>%.1fV</span></p>"
                              "<p>Torque Limit: <span id='torqueLimit'>%.1f</span></p>"
                              "<p>HV Current: <span id='hvCurrent'>%.1fA</span></p>"
                              "<p>Motor Power: <span id='motorPower'>%.1fW</span></p>"
                              "<p>Inverter Power: <span id='inverterPower'>%.1fW</span></p>"
                              "<p>Motor RPM: <span id='motorRPM'>%.1f RPM</span></p>"
                              "</body></html>", inverterTemp, motorTemp, errorCode, hvVoltage, torqueLimit, dcCurrent, motorPower, inverterPower, motorRPM);
        request->send(200, "text/html", htmlResponse);
    });

    server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request) {
        String jsonData = String("{\"tempInversor\":" + String(inverterTemp) + 
                                 ",\"tempMotor\":" + String(motorTemp) + 
                                 ",\"erro\":" + String(errorCode) + 
                                 ",\"hvVoltage\":" + String(hvVoltage) +
                                 ",\"torqueLimit\":" + String(torqueLimit) +
                                 ",\"hvCurrent\":" + String(dcCurrent) +
                                 ",\"motorPower\":" + String(motorPower) +
                                 ",\"inverterPower\":" + String(inverterPower) +
                                 ",\"motorRPM\":" + String(motorRPM) + "}");
        request->send(200, "application/json", jsonData);
    });

    // Funções para os botões
    server.on("/func1", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 1; 
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });
    server.on("/func2", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 2; 
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });
    server.on("/func3", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 3; 
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });
    server.on("/func4", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 4; 
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });

    // Inicia o servidor
    server.begin();
}

float convert_to_float(uint16_t value, float scale) {
    return value * scale;
}

// Função de setup
void setup()
{
    pinMode(PIN_5V_EN, OUTPUT);
    digitalWrite(PIN_5V_EN, HIGH);

    pinMode(CAN_SE_PIN, OUTPUT);
    digitalWrite(CAN_SE_PIN, LOW);

    Serial.begin(115200);

    setupServer();

    SD_test();

    delay(6000);

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

        if (rx_frame.MsgID == 0x048) { // Supondo que o ID da mensagem seja 0x048
            pwmData = rx_frame.data.u8[0];
            dpsUsage = rx_frame.data.u8[1];
            torqueCode = rx_frame.data.u8[2];
            errorCode = rx_frame.data.u8[3];
            torqueLimit = (float) (torqueCode * 0.1f);
            
        }

        if (rx_frame.MsgID == 0x046) { // Supondo que o ID da mensagem seja 0x046
            // Extrair as temperaturas
            uint16_t motor_temp_raw = (rx_frame.data.u8[5] << 8) | rx_frame.data.u8[4];
            uint16_t dc_current_raw = (rx_frame.data.u8[3] << 8) | rx_frame.data.u8[2];
            uint16_t inverter_temp_raw = (rx_frame.data.u8[7] << 8) | rx_frame.data.u8[6];
            uint16_t hv_voltage_raw = (rx_frame.data.u8[1] << 8) | rx_frame.data.u8[0];

            // Converter para float (assumindo que cada unidade representa 0.1 grau)
            motorTemp = convert_to_float(motor_temp_raw, 0.1);
            inverterTemp = convert_to_float(inverter_temp_raw, 0.1);
            hvVoltage = convert_to_float(hv_voltage_raw, 0.1);
            dcCurrent = convert_to_float(dc_current_raw, 0.1);
        }

        if (rx_frame.MsgID == 0x047) { // Supondo que o ID da mensagem seja 0x046
            // Extrair as temperaturas
            uint16_t motor_power_raw = (rx_frame.data.u8[3] << 8) | rx_frame.data.u8[2];
            uint16_t inverter_power_raw = (rx_frame.data.u8[5] << 8) | rx_frame.data.u8[4];
            uint16_t motor_RPM_raw = (rx_frame.data.u8[7] << 8) | rx_frame.data.u8[6];

            // Converter para float (assumindo que cada unidade representa 0.1 grau)
            motorPower = convert_to_float(motor_power_raw, 1);
            inverterPower = convert_to_float(inverter_power_raw, 1);
            motorRPM = convert_to_float(motor_RPM_raw, 1);
        }

        // Print debug information
        //Serial.print(data);
    }

     // Enviar mensagem CAN
    if (flagUpdateTorqueMode == true)
    {
        flagUpdateTorqueMode = false;
        sendTorqueMod(torqueModeMod);

        //ESP32Can.CANWriteFrame(&tx_frame);
        //Serial.println("CAN send done");
    }

}