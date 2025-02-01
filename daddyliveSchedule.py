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

# Remove existing files to ensure they are always regenerated
for file in [M3U8_OUTPUT_FILE, EPG_OUTPUT_FILE, DADDY_JSON_FILE]:
    if os.path.exists(file):
        os.remove(file)

# Funzioni
def generate_unique_ids(count, seed=42):
    random.seed(seed)
    ids = []
    for _ in range(count):
        id_str = str(uuid.UUID(int=random.getrandbits(128)))
        ids.append(id_str)
    return ids

def loadJSON(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        json_object = json.load(file)
    return json_object

def createSingleChannelEPGData(UniqueID, tvgName):
    xmlChannel = ET.Element('channel')
    xmlDisplayName = ET.Element('display-name')
    xmlIcon = ET.Element('icon')

    xmlChannel.set('id', UniqueID)
    xmlDisplayName.text = tvgName
    xmlIcon.set('src', LOGO)

    xmlChannel.append(xmlDisplayName)
    xmlChannel.append(xmlIcon)

    return xmlChannel

def createSingleEPGData(startTime, stopTime, UniqueID, channelName, description):
    programme = ET.Element('programme')
    title = ET.Element('title')
    desc = ET.Element('desc')

    programme.set('start', str(startTime) + " +0000")  # Correzione qui
    programme.set('stop', str(stopTime) + " +0000")    # Correzione qui
    programme.set('channel', UniqueID)

    title.text = channelName
    desc.text = description

    programme.append(title)
    programme.append(desc)

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
                        start_date_utc = datetime.datetime.strptime(date_time, date_format)

                        amsterdam_timezone = pytz.timezone("Europe/Amsterdam")
                        start_date_amsterdam = start_date_utc.replace(tzinfo=pytz.utc).astimezone(amsterdam_timezone)

                        mStartTime = start_date_amsterdam.strftime("%Y%m%d%H%M%S")
                        stop_date_amsterdam = start_date_amsterdam + datetime.timedelta(days=2)
                        mStopTime = stop_date_amsterdam.strftime("%Y%m%d%H%M%S")

                        formatted_date_time_cet = start_date_amsterdam.strftime("%m/%d/%y")
                        startHour = start_date_amsterdam.strftime("%H:%M") + " (CET)"
                        formatted_date_time_cet = formatted_date_time_cet + " - " + startHour

                        UniqueID = unique_ids.pop(0)
                        try:
                            channelName = game["event"] + " " + formatted_date_time_cet + " " + channel["channel_name"]
                        except TypeError:
                            print("JSON mal formattato, canale saltato per questa partita.")
                            continue

                        channelID = f"{channel['channel_id']}"

                        global channelCount
                        tvgName = channelName
                        tvLabel = tvgName
                        channelCount = channelCount + 1

                        with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:
                            if channelCount == 1:
                                file.write('#EXTM3U url-tvg="https://raw.githubusercontent.com/emaschi/daddylive/refs/heads/main/daily.xml"\n')

                            file.write(f'#EXTINF:-1 tvg-id="{UniqueID}" tvg-name="{tvgName}" tvg-logo="{LOGO}" group-title="Live", {tvLabel}\n')
                            file.write(f'#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
                            file.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n')
                            file.write(f'#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
                            file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channelID}/index.m3u8\n")
                            file.write('\n')

                        xmlChannel = createSingleChannelEPGData(UniqueID, tvgName)
                        root.append(xmlChannel)

                        programme = createSingleEPGData(mStartTime, mStopTime, UniqueID, channelName, "No Description")
                        root.append(programme)
        except KeyError as e:
            print(f"KeyError: {e} - Una delle chiavi {day} non esiste.")

channelCount = 0
unique_ids = generate_unique_ids(NUM_CHANNELS)

fetcher.fetchHTML(DADDY_JSON_FILE, "https://thedaddy.to/schedule/schedule-generated.json")

dadjson = loadJSON(DADDY_JSON_FILE)

if os.path.isfile(M3U8_OUTPUT_FILE):
    os.remove(M3U8_OUTPUT_FILE)

root = ET.Element('tv')

addChannelsByLeagueSport()

for id in unique_ids:
    with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:
        channelNumber = str(channelCount).zfill(3)
        tvgName = "OpenChannel" + channelNumber
        file.write(f'#EXTINF:-1 tvg-id="{id}" tvg-name="{tvgName}" tvg-logo="{LOGO}" group-title="Live", {tvgName}\n')
        file.write(f'#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
        file.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n')
        file.write(f'#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
        file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channelNumber}/index.m3u8\n")
        file.write('\n')
        channelCount += 1

    xmlChannel = createSingleChannelEPGData(id, tvgName)
    root.append(xmlChannel)

    programme = createSingleEPGData(mStartTime, mStopTime, id, "No Programm Available", "No Description")
    root.append(programme)

tree = ET.ElementTree(root)
tree.write(EPG_OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
