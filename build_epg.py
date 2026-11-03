#!/usr/bin/env python3
"""Zo zdrojového EPG (kozmali/sk-cz-epg) vyrobí malý epg.xml.gz iba s programami z apky.
ID kanála vo výstupe = presný názov programu z channels.json."""
import gzip, io, re, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

SRC = "https://raw.githubusercontent.com/kozmali/sk-cz-epg/main/epg.xml.gz"
NAMES = "names.txt"
OUT = "epg.xml.gz"
HOURS_BACK, HOURS_AHEAD = 6, 72

# názov programu v apke -> zoznam ID v zdroji (použije sa prvé, ktoré má dáta)
MAP = {
 "Jednotka": ["Jednotka.HD.sk", "JEDNOTKA.cz"], "Dvojka": ["Dvojka.HD.sk", "DVOJKA.cz"],
 "TV JOJ": ["JOJ.HD.sk", "JOJ.cz"], "JOJ Plus": ["JOJPLUS.cz", "JOJ.Plus.HD.sk"],
 "JOJ Krimi": ["Wau.HD.sk", "JOJ.Krimi.HD.sk"], "JOJ Family": ["JOJFAMILY.cz", "JOJ.Family.HD.sk"],
 "JOJ Cinema": ["JOJ.Cinema.HD.sk", "JOJCINEMA.cz"], "JOJ Šport": ["JOJ.ŠPORT.HD.sk", "JOJŠPORT.cz"],
 "Dajto": ["DAJTO.HD.sk", "DAJTO.cz"], "Markíza": ["Markíza.HD.sk", "MARKÍZA.cz"],
 "Markíza Krimi": ["Markíza.KRIMI.HD.sk", "MARKIZA_KRIMI.cz"], "Markíza Klasik": ["Markíza.Klasik.HD.sk", "MarkizaKlasik.cz"],
 "Prima SK": ["Prima.SK.HD.sk"], "Prima Cool SK": ["Prima.COOL.SK.HD.sk"],
 "Prima Krimi SK": ["Prima.Krimi.HD.sk", "PRIMAKRIMI.cz"], "Prima Love SK": ["Prima.LOVE.SK.HD.sk"],
 "ČT1": ["ČT1.HD.sk"], "ČT2": ["ČT2.HD.sk"], "CT24": ["ČT24.HD.sk"], "CT Decko": ["ČT.:D.-.ČT.Art.HD.sk", "ČT D", "CTD.cz"],
 "Nova HD": ["NOVA.cz"], "Nova Action HD": ["NOVAACTION.cz"], "Nova Krimi": ["NOVAGOLD.cz", "NOVAKRIMI.cz"], "Nova Cinema": ["NOVACINEMA.cz"],
 "Prima CZ": ["PRIMA.cz"], "Prima Cool CZ": ["PRIMACOOL.cz"], "Prima Krimi CZ": ["PRIMAKRIMI.cz"],
 "Prima Love CZ": ["PRIMALOVE.cz"], "Prima Max": ["PRIMAMAX.cz"], "Prima Show": ["PRIMASHOW.cz"],
 "Prima Star": ["PRIMASTAR.cz"], "Prima Zoom": ["PRIMAZOOM.cz"],
 "AMC": ["AMCCHANNEL.cz"], "AXN": ["AXN.cz", "AXN.HD.sk"], "AXN Black": ["AXNBLACK.cz"], "AXN White": ["AXNWHITE.cz"],
 "HBO": ["HBO.HD.sk"], "HBO 2": ["HBO2.HD.sk"], "HBO 3": ["HBO3.HD.sk"],
 "Cinemax": ["Cinemax.HD.sk", "CINEMAX.cz"], "Cinemax 2": ["Cinemax.2.HD.sk", "CINEMAX2.cz"],
 "Filmbox": ["Filmbox.HD.sk", "FILMBOX.cz"], "FILMBOX+ Love & Crime": ["FILMBOXPLUS.cz", "Filmbox.Stars.HD.sk"],
 "Filmbox+ Emotion": ["FILMBOXEXTRA.cz", "Filmbox.Extra.HD.sk"], "FILMBOX+ Comedy Czechia": ["FILMBOXFAMILY.cz", "Filmbox.Family.sk"],
 "Film+": ["FILM+.cz"], "Barrandov Krimi": ["Barrandov.Krimi.HD.sk", "BARRANDOVKRIMI.cz"],
 "FILMBOX+ Hits": ["FILMBOXPREMIUM.cz", "Filmbox.Premium.HD.sk"],
 "Nova Fun HD": ["NOVAFUN.cz"], "Nova Lady HD": ["NOVALADY.cz"], "Nova International": ["Nova.Intl..HD.sk"],
 "Doma": ["Doma.HD.sk", "DOMA.cz"], "Markíza International": ["MARKÍZAINT.cz"],
 "JOJ WAU": ["Wau.HD.sk"], "JOJ24": ["JOJ.24.HD.sk", "JOJ24.cz"], "CS Film": ["CS.Film-CS.Horror.HD.sk", "CSFILM,MINI.cz"],
 "Kino Barrandov": ["Kino.Barrandov.HD.sk", "BARRANDOVKINO.cz"], "TV Barrandov": ["Barrandov.TV.HD.sk", "TVBARRANDOV.cz"],
 "Story4 Czechia": ["STORY.4.sk", "4StoryTV.cz"], "Warner TV": ["WarnerTV.cz"], "Televize Seznam": ["SEZNAMTV.cz"],
 "Viasat Epic Drama Czechia": ["Epic.Drama.HD.sk", "VIASATEPICDRAMA.cz"],
 "Cartoon Network CEE Czech Republic": ["Cartoon.Network.HD.sk", "CARTOONNETWORK.cz"], "Cartoonito CEE Czechia": ["CARTOONITO.cz"],
 "Disney Channel (Czech Republic)": ["Disney.Channel.sk", "DISNEYCHANNEL.cz"], "Disney Junior (Czech Republic)": ["DISNEYJUNIOR.cz"],
 "ducktv PLUS": ["Duck.TV.HD.sk"], "Minimax CEE": ["Minimax.sk", "MINIMAX.cz"],
 "Nick Jr. (Czech Republic)": ["NICKJRTHORCZ.cz"], "Nickelodeon (Czech Republic)": ["NICKELODEON.cz"], "Nicktoons (Czech Republic)": ["NICKTOON.cz"],
 "Turbo TV": ["Turbo.TV.sk"], "History (Czech Republic)": ["History.HD.sk", "THEHISTORYCHANNEL.cz"], "History2": ["HISTORY2.cz", "History.2.sk"],
 "Investigation Discovery (Czech Republic)": ["CRIMEandINVESTIGATION.cz"],
 "National Geographic (Czech Republic)": ["NATIONALGEOGRAPHIC.cz"], "National Geographic Wild (Czech Republic)": ["NATGEOWILD.cz"],
 "Travel Channel (Czech Republic)": ["Travel.Channel.HD.sk", "TRAVELCHANNEL.cz"],
 "Viasat Explore (Czech Republic)": ["Viasat.Explore.HD.sk", "ViasatExplore.cz"], "Viasat History (Czech Republic)": ["Viasat.History.HD.sk", "VIASATHISTORY.cz"],
 "Viasat Nature (Czech Republic)": ["Viasat.Nature.HD.sk", "VIASATNATURE.cz"], "Animal Planet (Czech Republic)": ["Animal.Planet.HD.sk", "ANIMALPLANET.cz"],
 "TV Lux (Slovakia)": ["Lux.TV.HD.sk", "TVLUX.cz"], "TV Noe+": ["NOE.sk"], "TV Noe": ["NOE.sk", "TVNOE.cz"], "TV NRSR": ["tv.NRSR.sk"],
 "TLC (Czech Republic)": ["TLC.HD.sk"],
 "Music Box Classic": ["MUSICBOXCLASSIC.cz"], "Music Box Dance": ["MUSICBOXDANCE.cz"], "Music Box Hits": ["MUSICBOXHITS.cz"], "Music Box Sexy": ["MUSICBOXSEXY.cz"],
 "Ocko": ["Óčko.HD.sk", "ÓČKO.cz"], "Ocko Black": ["Óčko.Black.HD.sk", "ÓČKOBlack.cz"], "Ocko Expres": ["Óčko.Expres.HD.sk", "ÓČKOEXPRES.cz"],
 "Ocko Star": ["Óčko.Star.HD.sk", "ÓČKOSTAR.cz"], "Retro Music TV": ["RETRO.Music.TV.sk", "RETROMUSICTV.cz"], "Senzi": ["Senzi.sk", "SENZITV.cz"],
 "Eurosport 4K Czechia": ["Eurosport.1.HD.sk", "EUROSPORT.cz"], "Sport (Slovakia)": [":ŠPORT.HD.sk"],
 "Sport1": ["SPORT1.cz", "Sport1.HD.sk"], "Sport2": ["SPORT2.cz"],
 "Arena Sport 1": ["Arena.Sport.1.HD.sk", "ARENASPORT1.cz"], "Arena Sport 2": ["Arena.Sport.2.HD.sk", "ARENASPORT2.cz"],
 ":24": [":24.HD.sk"], "CNN Prima News": ["CNN.Prima.News.HD.sk", "CNNPRIMANEWS.cz"],
 "CS History": ["CS.History.sk", "CSHistory.cz"], "CS Mystery": ["CS.Mystery.sk", "CSMYSTERY.cz"],
}

def parse_time(s):
    m = re.match(r"(\d{14})\s*([+-]\d{4})?", s)
    dt = datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
    off = m.group(2) or "+0000"
    sign = 1 if off[0] == "+" else -1
    tz = timezone(sign * timedelta(hours=int(off[1:3]), minutes=int(off[3:5])))
    return dt.replace(tzinfo=tz)

def main():
    names = [l.strip() for l in open(NAMES, encoding="utf-8") if l.strip()]
    print("Sťahujem zdroj…", flush=True)
    raw = urllib.request.urlopen(urllib.request.Request(SRC, headers={"User-Agent": "epg-builder"}), timeout=120).read()
    now = datetime.now(timezone.utc)
    lo, hi = now - timedelta(hours=HOURS_BACK), now + timedelta(hours=HOURS_AHEAD)
    wanted = {i for ids in MAP.values() for i in ids}
    progs = {}  # id zdroja -> zoznam (start, stop, title, desc)
    with gzip.open(io.BytesIO(raw), "rb") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == "programme":
                cid = el.get("channel")
                if cid in wanted:
                    st, sp = parse_time(el.get("start")), parse_time(el.get("stop"))
                    if sp > lo and st < hi:
                        t = el.findtext("title") or ""
                        d = (el.findtext("desc") or "")[:300]
                        progs.setdefault(cid, []).append((st, sp, t, d))
                el.clear()
            elif el.tag == "channel":
                el.clear()
    root = ET.Element("tv", {"generated": now.strftime("%Y-%m-%d %H:%M UTC")})
    ok, miss = 0, []
    for name in names:
        src = next((i for i in MAP.get(name, []) if progs.get(i)), None)
        if not src:
            miss.append(name); continue
        ok += 1
        ET.SubElement(root, "channel", {"id": name})
        for st, sp, t, d in sorted(progs[src]):
            p = ET.SubElement(root, "programme", {
                "start": st.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S +0000"),
                "stop": sp.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S +0000"), "channel": name})
            ET.SubElement(p, "title").text = t
            if d: ET.SubElement(p, "desc").text = d
    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with gzip.open(OUT, "wb") as g:
        g.write(data)
    print(f"Hotovo: {ok} z {len(names)} programov má EPG, súbor {len(data)//1024} kB (gz {len(open(OUT,'rb').read())//1024} kB)")
    if miss:
        print("BEZ EPG:", ", ".join(miss))

if __name__ == "__main__":
    main()
