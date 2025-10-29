# Raspberry Pi Zero 2 W -ohjausjärjestelmän käyttöönotto

Tämä ohje käy läpi koko prosessin käyttöjärjestelmän asennuksesta levyautomaatin ohjelmiston käyttöönottoon. Ohje on kirjoitettu askel askeleelta -tyyliin eikä vaadi ohjelmointitaitoja.

## 1. Valmistele Raspberry Pi

1. Lataa "Raspberry Pi Imager" -ohjelma tietokoneellesi osoitteesta <https://www.raspberrypi.com/software/>.
2. Aseta vähintään 16 Gt microSD-kortti kortinlukijaan.
3. Käynnistä Raspberry Pi Imager ja valitse:
   - **Operating System**: *Raspberry Pi OS Lite (64-bit)*.
   - **Storage**: SD-korttisi.
4. Paina rataskuvaketta ja aseta seuraavat:
   - Käyttäjätunnus: `pi` ja salasana (kirjaa ylös!).
   - Ota SSH-yhteys käyttöön.
   - Aseta aikavyöhykkeeksi `Europe/Helsinki`.
5. Kirjoita käyttöjärjestelmä kortille ja anna ohjelman valmistua.
6. Irrota kortti ja aseta se Raspberry Pi Zero 2 W -laitteeseen.

## 2. Liitä laitteisto

1. Kytke Raspberry Pi:hin 12 V -> 5 V DC-DC -muunnin ja syötä muuntimen 5 V ulostulo Pi:n 5 V- ja GND-pinnejä käyttäen.
2. Kytke DS3231-kellomoduuliin virta (3V3 ja GND) sekä I²C-väylä (SDA = GPIO2, SCL = GPIO3).
3. Kytke rajakytkin GPIO23 (pin 16) ja GND välille. NC-kytkentä pitää piirin suljettuna levyn ollessa palautuneena.
4. Kytke rele tai servo `hardware`-tiedoston mukaan:
   - **Rele**: signaalijohto GPIO18 (pin 12), 5 V ja GND relekortille.
   - **Servo**: signaalijohto GPIO18, lisäksi servo tarvitsee oman 5 V syötön ja GND-yhteyden Pi:hin.
5. Testaa että manuaalinen hätävipu toimii mekaanisesti ilman virtaa.

## 3. Ensikäynnistys ja päivitykset

1. Liitä näyttö ja näppäimistö tai muodosta SSH-yhteys (esim. `ssh pi@raspberrypi.local`).
2. Päivitä järjestelmä:
   ```bash
   sudo apt update
   sudo apt full-upgrade -y
   sudo reboot
   ```

## 4. Ota I²C ja DS3231 käyttöön

1. Avaa raspi-config:
   ```bash
   sudo raspi-config
   ```
2. Valitse **Interface Options** → **I2C** → `Enable`.
3. Käynnistä uudelleen tarvittaessa.
4. Asenna tarvittavat työkalut ja tarkista että DS3231 löytyy:
   ```bash
   sudo apt install -y i2c-tools
   sudo i2cdetect -y 1
   ```
   Listassa tulee näkyä osoite `0x68`.
5. Ota kello käyttöön:
   ```bash
   sudo apt install -y python3-smbus
   sudo timedatectl set-ntp true
   sudo hwclock -w
   ```
   Tämä kopioi järjestelmäajan DS3231:lle. Kun Pi käynnistyy ilman internetiä, `hwclock -s` suoritetaan automaattisesti.

## 5. Valmistele ohjelmiston kansiorakenne

```bash
mkdir -p ~/feeder/data
cd ~/feeder
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r /home/pi/project/software/requirements.txt
```

> Korvaa polku `/home/pi/project` sillä hakemistolla, johon kopioit tämän repositoryn sisällön (esim. SFTP:llä). Helpoin tapa on kopioida koko `software`-hakemisto Pi:lle:
>
> ```bash
> scp -r <tietokoneesi polku>/software pi@raspberrypi.local:/home/pi/feeder
> scp -r <tietokoneesi polku>/docs pi@raspberrypi.local:/home/pi/feeder
> ```

## 6. Hotspotin käyttöönotto

1. Asenna hostapd ja dnsmasq:
   ```bash
   sudo apt install -y hostapd dnsmasq
   sudo systemctl stop hostapd
   sudo systemctl stop dnsmasq
   ```
2. Kopioi valmiit asetustiedostot:
   ```bash
   cd /home/pi/feeder/software
   sudo chmod +x scripts/setup_hotspot.sh
   sudo ./scripts/setup_hotspot.sh
   ```
3. Aseta hostapd:n salasana vaihtamalla rivi `wpa_passphrase` tiedostossa `/etc/hostapd/hostapd.conf`:
   ```bash
   sudo nano /etc/hostapd/hostapd.conf
   ```
   Tallenna uusi salasana ja sulje editori.
4. Varmista että palvelut käynnistyvät automaattisesti:
   ```bash
   sudo systemctl enable hostapd
   sudo systemctl enable dnsmasq
   ```
5. Kytke toiseen laitteeseen LevyFeeder-verkkoon ja testaa että saat IP-osoitteen 192.168.20.x.

## 7. Sovelluksen konfigurointi

1. Luo salainen avain web-sovellukselle:
   ```bash
   python - <<'PY'
   import secrets
   print(secrets.token_hex(16))
   PY
   ```
   Kopioi tulostettu merkkijono.
2. Avaa tiedosto `/home/pi/feeder/software/feeder_app/web.py` ja vaihda `app.secret_key` -riville uusi arvo. Voit käyttää komentoa:
   ```bash
   sed -i "s/change-me/<uusi-avain>/" /home/pi/feeder/software/feeder_app/web.py
   ```
3. Jos käytät servoa, muuta ympäristömuuttuja `FEEDER_GPIO_MODE=servo` ja päivitä myös servoimpulssien rajat `.service`-tiedostossa.
4. Jos rajakytkin on NO-tyyppinen, lisää ympäristömuuttuja `FEEDER_LIMIT_SWITCH_INVERT=true`.

## 8. Systemd-palvelun käyttöönotto

1. Kopioi palvelutiedosto ja päivitä polut tarvittaessa (esim. jos käyttäjänimesi ei ole `pi`).
   ```bash
   sudo install -m 644 /home/pi/feeder/software/systemd/feeder.service /etc/systemd/system/feeder.service
   ```
2. Lataa systemd uudelleen ja ota palvelu käyttöön:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable feeder.service
   sudo systemctl start feeder.service
   ```
3. Tarkista lokit:
   ```bash
   journalctl -u feeder.service -f
   ```
   Kun palvelu on käynnissä, selaimessa osoitteessa `http://192.168.20.1:8080` näkyy käyttöliittymä.

## 9. Käyttöliittymän käyttö

- Kirjaudu LevyFeeder-verkkoon.
- Avaa selaimessa `http://192.168.20.1:8080`.
- Lisää ajastuksia täyttämällä lomake ja valitsemalla viikonpäivät.
- Manuaalinen vapautus löytyy sivun alaosasta.
- Ajastukset tallentuvat automaattisesti.

## 10. Testaus

1. Tarkista että rajakytkin näkyy lokissa `Schedule runner` -viesteissä.
2. Lisää testiajastus minuutin päähän nykyhetkestä ja varmista että levy vapautuu.
3. Tarkkaile, ettei rele/servo jää vetämään pysyvästi (kuuntele ja tunnustele).
4. Tee mekaaninen hätävapautus ja varmista että järjestelmä palautuu rajakytkimen mukaan.

## 11. Huolto ja varmuuskopiot

- Viikoittain: tarkista akun jännite, puhdista mekanismi, varmista että hotspot toimii.
- Kuukausittain: lataa `~/feeder/data/feeder.db` talteen (varmuuskopio ajastuksista).
- Päivitä järjestelmä komennolla `sudo apt update && sudo apt full-upgrade`.
- Jos haluat päivittää ohjelmiston, kopioi uudet tiedostot ja käynnistä `sudo systemctl restart feeder.service`.

## 12. Vianetsintä

| Ongelma | Ratkaisu |
| --- | --- |
| Hotspot ei näy | `sudo systemctl status hostapd dnsmasq`, tarkista /etc/hostapd/hostapd.conf salasanarivi |
| Web-sivu ei aukea | `sudo systemctl status feeder.service`, tarkista lokit `journalctl -u feeder.service` |
| Levy ei vapautu | Tarkista rajakytkimen tila, releen äänet ja 12 V syöttö |
| Kellonaika väärä | `sudo timedatectl set-ntp true`, `sudo hwclock -w` ja käynnistä uudelleen |

Onnittelut! Järjestelmä on käyttövalmis.
