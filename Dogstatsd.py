#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <Statsd.h>
#include <DHTesp.h>

char ssid[] = "name";     //  your network SSID (name)
char pass[] = "password";  // your network password
int status = WL_IDLE_STATUS;

// Define NTP Client to get time
WiFiUDP ntpUDP;
WiFiUDP udp;  // or EthernetUDP, as appropriate.
Statsd statsd(udp, "IP Address Here", 8125); //Sellari Desktop
NTPClient timeClient(ntpUDP);

DHTesp dht;
int dhtPin = 27;

unsigned long epochTime;

#ifdef __cplusplus
extern "C" {
#endif

  uint8_t temprature_sens_read();
  //uint8_t g_phyFuns;

#ifdef __cplusplus
}
#endif

uint8_t temp_farenheit;

// Variables to save date and time
String formattedDate;
String dayStamp;
String timeStamp;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // attempt to connect to Wifi network:
  while (status != WL_CONNECTED) {
    // wait 10 seconds for connection:
    delay(10000);
    Serial.print("Attempting to connect to WPA SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network:
    status = WiFi.begin(ssid, pass);  
  }

  // you're connected now, so print out the data:
  Serial.println("You're connected to the network");
  Serial.println("Local IP: " + String(WiFi.localIP()));

  Serial.println("Initialize a NTPClient to get time");

  timeClient.begin();
  // Set offset time in seconds to adjust for your timezone, for example:
  // GMT +1 = 3600
  // GMT +8 = 28800
  // GMT -1 = -3600
  // GMT 0 = 0
  //timeClient.setTimeOffset(-21600);
  timeClient.setTimeOffset(0);
  while (!timeClient.update()) {
    timeClient.forceUpdate();
  }
    // The formattedDate comes with the following format:
    // 2018-05-28T16:00:13Z
    // We need to extract date and time
  //formattedDate = timeClient.getFormattedDate();
  epochTime = timeClient.getEpochTime();

  Serial.print("Initialize DHT Sensor");
  dht.setup(dhtPin, DHTesp::DHT22);
  Serial.print("DHT Sensor Ready");
  Serial.print("");

}

float fanSpeed = 40;
unsigned long fanStartTime = 0;
int fanStatus = 1; //0=off 1=on
unsigned long currentEpoch;
unsigned long epochDiff;
unsigned long fanEpochDiff;

 
void loop() 
{ 
  Serial.println("*********************************");
  Serial.println("Getting Air Temperature, Humidity, Heat Index, Device Temperature, and Device Uptime");
  float temp = dht.toFahrenheit(dht.getTemperature());
  float humidity = dht.getHumidity();
  float hi = dht.computeHeatIndex(temp,humidity,true);
  temp_farenheit = temprature_sens_read();

  fanSpeed = 40+(temp_farenheit-120);
  if(fanSpeed > 100)
  {
    fanSpeed = 100;
  }
  if(fanSpeed < 40)
  {
    fanSpeed = 40;
  }
  if(temp_farenheit>=150)
  {
    fanSpeed = 100; 
  } 

  
  currentEpoch = timeClient.getEpochTime();
  epochDiff = currentEpoch - epochTime;
  Serial.println("Temperature: " + String(temp));
  Serial.println("Humidity: " + String(humidity));
  Serial.println("Heat Index: " + String(hi));
  Serial.println("Device Temperature: " + String(temp_farenheit));
  Serial.println("Device Uptime: " + String(epochDiff));

  String tags = "city:frisco,location:sellari_house,floor:1,device_name:Sellari-ESP2-Board1";
  
  Serial.println("Publishing to StatsD");
  sendGaugeToStatsD("device.sensor.air.humidity", humidity, tags);
  sendGaugeToStatsD("device.sensor.air.temperature", temp, tags);
  sendGaugeToStatsD("device.sensor.air.heatindex", hi, tags);
  sendGaugeToStatsD("device.sensor.temperature", temp_farenheit, tags);
  sendGaugeToStatsD("device.sensor.uptime", epochDiff, tags);
  sendGaugeToStatsD("device.fan.status", fanStatus, tags);
  sendGaugeToStatsD("device.fan.speed", fanSpeed, tags);
  Serial.println("Finished publishing to StatsD");
  
  Serial.println("Waiting 1 Second");
  delay(1000);

}

float getFanSpeed()
{
  //will be added when I get a fan....
  return 50;
}

void sendGaugeToStatsD(String aMetric, float aVal, String aTags)
{
  statsd.setTagStyle(TAG_STYLE_DATADOG);
  statsd.begin();
  statsd.gauge(aMetric, aVal, aTags, 1.0);
  statsd.end();
}
