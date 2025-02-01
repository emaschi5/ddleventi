import xml.etree.ElementTree as ET
import random
import uuid
import fetcher
import json
import os
import datetime
import pytz

# Costanti
NUM_CHANNELS = 10000
DADDY_JSON_FILE = "daddyliveSchedule.json"
M3U8_OUTPUT_FILE = "daily.m3u8"
EPG_OUTPUT_FILE = "daily.xml"
LOGO = "https://raw.githubusercontent.com/emaschi5/daddylive/refs/heads/main/stremioita.png"

mStartTime = 0
mStopTime = 0

# Rimuove i file esistenti per garantirne la rigenerazione
for file in [M3U8_OUTPUT_FILE, EPG_OUTPUT_FILE, DADDY_JSON_FILE]:
    if os.path.exists(file):
        os.remove(file)

# Funzioni
def generate_unique_ids(count, seed=42):
    random.seed(seed)
    return [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(count)]

def loadJSON(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def createSingleChannelEPGData(UniqueID, tvgName):
    xmlChannel = ET.Element('channel', id=UniqueID)
    xmlDisplayName = ET.SubElement(xmlChannel, 'display-name')
    xmlIcon = ET.SubElement(xmlChannel, 'icon', src=LOGO)

    xmlDisplayName.text = tvgName
    return xmlChannel

def createSingleEPGData(startTime, stopTime, UniqueID, channelName, description):
    programme = ET.Element('programme', start=f"{startTime} +0000", stop=f"{stopTime} +0000", channel=UniqueID)
    
    title = ET.SubElement(programme, 'title')
    desc = ET.SubElement(programme, 'desc')
    
    title.text = channelName
    desc.text = description
    
    return programme

def addChannelsByLeagueSport():
    global channelCount
    for day, value in dadjson.items():
        try:
            for sport in dadjson[day].values():
                for game in sport:
                    for channel in game["channels"]:
                        date_time = day.replace("th ", " ").replace("rd ", " ").replace("st ", " ").replace("nd ", " ").replace("Dec Dec", "Dec")
                        date_time = date_time.replace("-", game["time"] + " -")
                        date_format = "%A %d %b %Y %H:%M - Schedule Time UK GMT"
                        
                        try:
                            start_date_utc = datetime.datetime.strptime(date_time, date_format)
                        except ValueError:
                            print(f"Errore nel parsing della data: {date_time}")
                            continue
                        
                        amsterdam_timezone = pytz.timezone("Europe/Amsterdam")
                        start_date_amsterdam = start_date_utc.replace(tzinfo=pytz.utc).astimezone(amsterdam_timezone)

                        mStartTime = start_date_amsterdam.strftime("%Y%m%d%H%M%S")
                        mStopTime = (start_date_amsterdam + datetime.timedelta(days=2)).strftime("%Y%m%d%H%M%S")

                        formatted_date_time_cet = start_date_amsterdam.strftime("%m/%d/%y") + " - " + start_date_amsterdam.strftime("%H:%M") + " (CET)"

                        UniqueID = unique_ids.pop(0)
                        try:
                            channelName = game["event"] + " " + formatted_date_time_cet + " " + channel["channel_name"]
                        except TypeError:
                            print("JSON mal formattato, canale saltato per questa partita.")
                            continue

                        channelID = f"{channel['channel_id']}"
                        tvgName = channelName
                        tvLabel = tvgName
                        channelCount += 1

                        with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:
                            if channelCount == 1:
                                file.write('#EXTM3U url-tvg="https://raw.githubusercontent.com/emaschi/daddylive/refs/heads/main/daily.xml"\n')

                            file.write(f'#EXTINF:-1 tvg-id="{UniqueID}" tvg-name="{tvgName}" tvg-logo="{LOGO}" group-title="Live", {tvLabel}\n')
                            file.write('#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
                            file.write('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n')
                            file.write('#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
                            file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channelID}/index.m3u8\n\n")

                        xmlChannel = createSingleChannelEPGData(UniqueID, tvgName)
                        root.append(xmlChannel)

                        programme = createSingleEPGData(mStartTime, mStopTime, UniqueID, channelName, "No Description")
                        root.append(programme)
        except KeyError as e:
            print(f"KeyError: {e} - Una delle chiavi {day} non esiste.")

# Inizializza contatore e genera ID univoci
channelCount = 0
unique_ids = generate_unique_ids(NUM_CHANNELS)

# Scarica il file JSON con la programmazione
fetcher.fetchHTML(DADDY_JSON_FILE, "https://thedaddy.to/schedule/schedule-generated.json")

# Carica i dati dal JSON
dadjson = loadJSON(DADDY_JSON_FILE)

# Crea il nodo radice dell'EPG
root = ET.Element('tv')

# Aggiunge i canali reali
addChannelsByLeagueSport()

# Verifica se sono stati creati canali validi
if channelCount == 0:
    print("Nessun canale valido trovato. Nessun file M3U8 creato.")
else:
    tree = ET.ElementTree(root)
    tree.write(EPG_OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
    print(f"EPG generato con {channelCount} canali validi.")

