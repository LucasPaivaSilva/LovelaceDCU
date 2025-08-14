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
float hvVoltage = 1.42;  // Exemplo de inicialização
float torqueLimit = 0; // Exemplo de inicialização

float hvCurrent = 1234;
float inverterPower = 1234;
float motorPower = 1234;
float motorRPM = 1234;
float motorTorque = 0;
float lvVoltage = 0;
float float_42_42 = 0;

float speed = 0;
int pedal = 70; 
int flag_run_identify = 0;

bool rtd = false;      // Exemplo de inicialização

// Configuração da Rede WiFi
const char* ssid = "Lovelace2-DCU";
const char* password = "bolodecenoura";

#define FILE_NAME "/lovelace2-2606.csv"

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

void sendTorqueMod(uint8_t mode){
    CAN_frame_t tx_frame;
    tx_frame.FIR.B.FF = CAN_frame_std;
    tx_frame.MsgID = 0x041;
    tx_frame.FIR.B.DLC = 8;
    tx_frame.data.u8[0] = mode;
    tx_frame.data.u8[1] = 0xFF;
    tx_frame.data.u8[2] = 0xFF;
    tx_frame.data.u8[3] = 0xFF;
    tx_frame.data.u8[4] = 0xFF;
    tx_frame.data.u8[5] = 0xFF;
    tx_frame.data.u8[6] = 0xFF;
    tx_frame.data.u8[7] = 0xFF;

    ESP32Can.CANWriteFrame(&tx_frame);

}


// Configuração do CAN
CAN_device_t CAN_cfg;
const int interval = 5000;
unsigned long previousMillis = 0;

void setupServer() {
    WiFi.softAP(ssid, password);
    IPAddress IP = WiFi.softAPIP();
    Serial.println("IP do Ponto de Acesso: " + IP.toString());

    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        char htmlResponse[4500];
        sprintf(htmlResponse, "<!DOCTYPE html><html><head><title>LovelaceDCU</title>"
                              "<meta charset=\"UTF-8\">"
                              "<style>"
                                "body { font-family: Arial, sans-serif; font-size: 22px; text-align: center; }"
                                "h1 { color: navy; }"
                                "button, input[type='text'] { margin: 10px; padding: 10px; }"
                                "button { font-size: 24px; }"
                                "input[type='text'] {"
                                    "font-size: 18px; /* Diminui o tamanho da fonte */"
                                    "width: 80px; /* Reduz a largura da caixa */"
                                    "padding: 5px; /* Diminui o padding */"
                                    "text-align: center; /* Centraliza o texto */"
                                    "margin: 10px; /* Mantém a margem consistente com outros elementos */"
                                "}"
                                ".column { display: inline-block; vertical-align: top; width: 45%; margin: 10px; }"
                                ".green { color: green; }"
                                ".red { color: red; }"
                              "</style>"
                              "<script>"
                              "setInterval(function() {"
                              "fetch('/data').then(response => response.json()).then(data => {"
                              "document.getElementById('tempInversor').innerText = data.tempInversor.toFixed(1) + '°C';"
                              "document.getElementById('tempMotor').innerText = data.tempMotor.toFixed(1) + '°C';"
                              "document.getElementById('erro').innerText = data.erro;"
                              "document.getElementById('hvVoltage').innerText = data.hvVoltage.toFixed(1) + 'V';"
                              "document.getElementById('torqueLimit').value = data.torqueLimit.toFixed(1);"
                              "document.getElementById('hvCurrent').innerText = data.hvCurrent.toFixed(1) + 'A';"
                              "document.getElementById('motorPower').innerText = data.motorPower.toFixed(1) + 'W';"
                              "document.getElementById('inverterPower').innerText = data.inverterPower.toFixed(1) + 'W';"
                              "document.getElementById('speed').innerText = data.speed.toFixed(1) + ' km/h';"
                              "document.getElementById('pedal').innerText = data.pedal;"
                              "document.getElementById('rtd').className = data.rtd ? 'green' : 'red';"
                              "document.getElementById('rtd').innerText = data.rtd ? 'Yes' : 'No';"
                              "document.getElementById('erro').className = data.erro != 0 ? 'red' : '';"
                              "}).catch(error => console.error('Fetch error:', error));"
                              "}, 500);"
                              "</script>"
                              "</head><body>"
                              "<h1>Lovelace DCU - WebServer</h1>"
                              "<div style='text-align: center;'>"
                              "<button onclick=\"location.href='/func1'\">Mode1</button>"
                              "<button onclick=\"location.href='/func2'\">Mode2</button>"
                              "<button onclick=\"location.href='/func3'\">Mode3</button>"
                              "<button onclick=\"location.href='/func4'\">Mode4</button>"
                              "<input type='text' id='torqueLimit' readonly>"
                              "</div>"
                              "<div class='column'>"
                              "<p>RTD Status: <span id='rtd'></span></p>"
                              "<p>Inverter Temperature: <span id='tempInversor'></span></p>"
                              "<p>HV Voltage: <span id='hvVoltage'></span></p>"
                              "<p>Inverter Power: <span id='inverterPower'></span></p>"
                              "<p>Motor Speed: <span id='speed'></span></p>"
                              "</div>"
                              "<div class='column'>"
                              "<p>Error: <span id='erro'></span></p>"
                              "<p>Motor Temperature: <span id='tempMotor'></span></p>"
                              "<p>HV Current: <span id='hvCurrent'></span></p>"
                              "<p>Motor Power: <span id='motorPower'></span></p>"
                              "<p>Pedal: <span id='pedal'></span></p>"
                              "</div>"
                              "</body></html>");
        request->send(200, "text/html", htmlResponse);
    });

    server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request) {
        String jsonData = "{\"tempInversor\":" + String(inverterTemp, 1) +
                           ", \"tempMotor\":" + String(motorTemp, 1) +
                           ", \"erro\":" + String(errorCode) +
                           ", \"hvVoltage\":" + String(hvVoltage, 1) +
                           ", \"torqueLimit\":" + String(torqueLimit, 1) +
                           ", \"hvCurrent\":" + String(hvCurrent, 1) +
                           ", \"motorPower\":" + String(motorPower, 1) +
                           ", \"inverterPower\":" + String(inverterPower, 1) +
                           ", \"speed\":" + String(speed, 1) +
                           ", \"pedal\":" + String(pedal) +
                           ", \"rtd\":" + (rtd ? "\"Yes\"" : "\"No\"") + "}";
        request->send(200, "application/json", jsonData);
    });

    // Configura as ações dos botões
    server.on("/func1", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 4;
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });
    server.on("/func2", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 6;
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });
    server.on("/func3", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 8;
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });
    server.on("/func4", HTTP_GET, [](AsyncWebServerRequest *request) {
        torqueModeMod = 10;
        flagUpdateTorqueMode = true;
        request->redirect("/");
    });
 
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
    CAN_cfg.speed = CAN_SPEED_250KBPS;
    CAN_cfg.tx_pin_id = GPIO_NUM_27;
    CAN_cfg.rx_pin_id = GPIO_NUM_26;
    CAN_cfg.rx_queue = xQueueCreate(10, sizeof(CAN_frame_t));

    randomSeed(132);

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

        if (rx_frame.MsgID == 0x106){
            errorCode = rx_frame.data.u8[0];
        }

        if (rx_frame.MsgID == 0x300){
            // 0x300
            // Byte 0 -> dspUsage 
            // Byte 1 -> dspUsageMax
            // Byte 2 -> TorqueMod
            // Byte 3 -> flag_run_identify
            dpsUsage = rx_frame.data.u8[0];

            torqueCode = rx_frame.data.u8[2];
            torqueLimit = (float) (torqueCode * 0.1f);

            flag_run_identify = rx_frame.data.u8[3];
        }

        if (rx_frame.MsgID == 0x301) {
            // 0x301
            // Float 1 - 42.42
            // Float 2 - LV voltage
            // Reconstruir os floats
            float value1, value2;
            memcpy(&value1, &rx_frame.data.u8[0], sizeof(float));
            memcpy(&value2, &rx_frame.data.u8[4], sizeof(float));

            float_42_42 = value1;
            lvVoltage = value2;
        }

        if (rx_frame.MsgID == 0x302) {
            // 0x302
            // Float 1 - Inverter Temp
            // Float 2 - Motor Temp
            // Reconstruir os floats
            float value1, value2;
            memcpy(&value1, &rx_frame.data.u8[0], sizeof(float));
            memcpy(&value2, &rx_frame.data.u8[4], sizeof(float));

            inverterTemp = value1;
            motorTemp = value2;
        }

        if (rx_frame.MsgID == 0x303) {
            // 0x303
            // Float 1 - HVCurrent
            // Float 2 - HVVoltage
            // Reconstruir os floats
            float value1, value2;
            memcpy(&value1, &rx_frame.data.u8[0], sizeof(float));
            memcpy(&value2, &rx_frame.data.u8[4], sizeof(float));

            hvCurrent = value1;
            hvVoltage = value2;
        }

        if (rx_frame.MsgID == 0x304) {
            // 0x304
            // Float 1 - Motor Output Power
            // Float 2 - Motor Input Power / Inverter Power
            // Reconstruir os floats
            // Reconstruir os floats
            float value1, value2;
            memcpy(&value1, &rx_frame.data.u8[0], sizeof(float));
            memcpy(&value2, &rx_frame.data.u8[4], sizeof(float));

            motorPower = value1;
            inverterPower = value2;
        }

        if (rx_frame.MsgID == 0x305) {
            // 0x305
            // Float 1 - Motor Torque
            // Float 2 - Motor RPM
            // Reconstruir os floats
            // Reconstruir os floats
            float value1, value2;
            memcpy(&value1, &rx_frame.data.u8[0], sizeof(float));
            memcpy(&value2, &rx_frame.data.u8[4], sizeof(float));

            motorTorque = value1;
            motorRPM = value2;
            speed = motorRPM * 0.0196;
        }

        if (rx_frame.MsgID == 0x171){
            pedal = (rx_frame.data.u8[1] << 8) | rx_frame.data.u8[0];
            rtd = rx_frame.data.u8[5];
        }
        // Print debug information
        Serial.print(data);
    }

     // Enviar mensagem CAN
    if (flagUpdateTorqueMode == true)
    {
        sendTorqueMod(torqueModeMod);
        flagUpdateTorqueMode = false;
    }
}

