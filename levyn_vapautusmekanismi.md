# Levyn vapautusmekanismin toteutussuunnitelma

## 1. Vapautusmekanismi ja mekaniikka
- **Levy ja vipu**: Suunnittele vipu 6 mm teräslevystä, pituus 150 mm, kiinnityspiste 40 mm päässä levyn lukituskohdasta. Vipusuhde ~1:3 mahdollistaa riittävän voiman vapautukseen.
- **Kiinnikkeet**: Käytä 3 mm teräksestä taivutettuja U-profiilisia kiinnikkeitä vanerilaatikon sisäpuolella. Kiinnitä M6-pulteilla ja nyloc-muttereilla.
- **Palautusjousi**: Asenna 1.2 mm jousiteräksestä valmistettu vetojousi, vapaapituus 70 mm, kiinnityspisteet vipuvarren takaosaan ja laatikon seinään. Valitse jousi, jonka nimellisvoima ~15 N 30 mm venymällä.
- **Liikevara**: Jyrsitty ura 5 mm vipuvarren liikeradalle; varmista vähintään 2 mm välys joka suuntaan, ettei vaneri ota kiinni.

## 2. Toimilaite ja voima
- **Vaihtoehdot**: 12 V lineaarinen toimilaite (isku 50 mm, voima 150 N) tai 20 kg·cm vääntävä servo.
- **Kiinnitys**: Kiinnitä toimilaite vipuun 2 mm teräsvaijerilla tai M5-nivelellä 20 mm päähän pivotista.
- **Testaus**: Mittaa vapautusvoima kalibroidulla jousivaa'alla; varmista < 40 N vaadittu voima. Testaa molemmat toimilaitteet ja valitse nopeuden/voiman perusteella.

## 3. Ohjain ja logiikka
- **Pääohjain**: Raspberry Pi Zero 2 W (Debian Bookworm Lite) toimii keskitettynä ohjaimena.
- **Lisämoduulit**:
  - DS3231-reaaliaikakello I²C-väylässä, varmistaa ajastuksen myös sähkökatkojen aikana.
  - 1-kanavainen relekortti lineaariselle toimilaitteelle *tai* I²C-servokontrolleri (esim. PCA9685) servolle.
  - NC-rajakatkaisija vipuvarren palautumisen valvontaan (kytketään GPIO:hon sisäisellä pull-upilla).
- **Ohjelmistoarkkitehtuuri**:
  - Python-palvelu (systemd) vastaa ajastettujen tapahtumien käsittelystä, rele-/servo-ohjauksesta ja rajakytkimen valvonnasta.
  - Ajastusluettelo tallennetaan SQLite-tietokantaan; DS3231 synkronoi ajan bootissa ja joka yö.
  - Manuaalinen vapautus mahdollista web-käyttöliittymän painikkeen kautta sekä fyysisellä hätävivulla.

## 4. Verkkoyhteys ja hotspot
- **WLAN-hotspot**: Konfiguroi Raspberry Pi Zero 2 W toimimaan access pointina (hostapd + dnsmasq), SSID:nä esim. "LevyFeeder" ja WPA2-PSK -salasana.
- **Verkon eristys**: DHCP-palvelu jakaa IP-osoitteet 192.168.20.0/24-verkosta. Estä ulospäin ohjautuva liikenne (iptables) ja rajoita pääsyä vain web-käyttöliittymään ja SSH-huoltoon.
- **Käynnistyminen**: Hotspot-palvelut käynnistyvät automaattisesti bootissa; LED-indikaattori (GPIO) kertoo, kun verkko on käytettävissä.

## 5. Virtajärjestelmä
- **Syöttö**: 12 V lyijyakku + aurinkolaturi *tai* 12 V verkkolaite.
- **Suojaus**: 5 A sulake akun välittömässä läheisyydessä.
- **Muunnin**: DC-DC step-down 12 V -> 5 V mikro-ohjaimelle.
- **Kaapelointi**: Käytä IP67-johtimia, vedonpoistot ja silikonitiivistys.

## 6. Kotelointi ja turvallisuus
- **IP65-kotelo** ohjaimelle ja virtakomponenteille.
- **Kaapelointi**: Vedä kaapelit suojaputkissa; tiivistä läpiviennit kumitiivisteillä.
- **Hätävipu**: Asenna manuaalinen ohitusvipu ulkopuolelle.

## 7. Rajakytkin ja testaus
- **Rajakytkin**: Asenna vipuun; NC-asento valvoo palautusta.
- **Testaus**: Suorita useita syöttösyklejä, tarkista levyn palautuminen ja varmista, että servo ei pidä kuormaa pysyvästi.

## 8. Käyttöliittymä ja dokumentointi
- **Web-käyttöliittymä**:
  - Flask- tai FastAPI-pohjainen sovellus palvelee ajastusnäkymää hotspot-verkon kautta.
  - Toiminnot: ajastuslistan näyttö ja muokkaus (lisäys, poisto, aktiivisuuden togglaus), manuaalinen vapautus, rajakytkimen tila, akun jännite.
  - UI suojaa kirjautumisella; tunnukset talletetaan salattuina (bcrypt) ja HTTPS voidaan toteuttaa paikallisella itseallekirjoitetulla sertifikaatilla.
- **Paikalliset hallintanapit**: Kaksi IP67-painiketta (manuaalinen vapautus / peruutus) kytketty Pi:n GPIO:ihin.
- **Dokumentointi**: Huolto-ohjeet, viikoittainen tarkastuslista, varmistusprotokollat (manuaalinen testi, akun tarkistus, toimilaitteen rasvaus), sekä verkko- ja käyttäjätilien hallinnan ohjeet.


## 9. Ohjelmisto ja käyttöönotto
- Täydellinen asennus- ja käyttöohje löytyy tiedostosta `docs/installation_guide.md`.
- Raspberry Pi -ohjelmiston lähdekoodi sijaitsee hakemistossa `software/feeder_app`. Se tarjoaa Flask-pohjaisen web-käyttöliittymän ja taustalla ajastuksia suorittavan palvelun.
- Hotspotin asetukset (hostapd, dnsmasq, dhcpcd) löytyvät hakemistosta `software/config` ja voidaan asentaa skriptillä `software/scripts/setup_hotspot.sh`.
- Systemd-palvelutiedosto (`software/systemd/feeder.service`) käynnistää Python-palvelun automaattisesti bootissa.
