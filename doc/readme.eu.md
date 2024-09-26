# mupl - MangaDex Bulk Uploader
Karpetak eta (.zip/.cbz) fitxategiak igotzen ditu MangaDexera modu azkar eta errazean.

Jatorrizko bertsioa:
[English](/readme.md)

## Eduki Taula
- [Nola erabili](#erabilera)
  - [Komando-lerroko argumentuak](#argumentuak)
- [Igo beharreko fitxategien izenaren formatua](#fitxategi-izen-formatua)
  - [Izenaren formatua](#izen-formatua)
  - [Izenaren parametroak](#izen-parametroak)
  - [Onartutako Fitxategi Formatuak](#onartutako-fitxategi-formatuak)
- [Konfigurazioa](#konfigurazioa)
  - [Erabiltzailearen Ezarpenak](#erabiltzailearen-ezarpenak)
  - [MangaDexeko kredentzialak](#mangadexeko-kredentzialak)
  - [Programaren rutak](#rutak)
- [Izen-ID mapa](#mapa)
  - [Adibidea](#adibidea)
- [Ekarpenak egin](#ekarpenak)
  - [Itzulpenak](#itzulpenak)


## Erabilera
[Azken bertsioa] deskargatu (iturburu-kodea duen zip fitxategia) bertsioak orrialdetik, deskonprimitu fitxategia karpeta batean eta ireki terminal bat karpeta berean.

Terminalean (bash, powershell, cmd) `python mupl.py` idatzi programa erabiltzeko.
Ziurtatu Python 3.9+ instalatuta duzula, eta erabili `python` Windows-erako eta `python3` Mac eta Linux-erako.

### Argumentuak
Komando-lerroko argumentuak daude komando nagusiaren ondoren gehi daitezkeenak programaren portaera aldatzeko, adibidez `python mupl.py -u`.

##### Aukerak
- `--update` `-u` Ez konprobatu eguneratze berririk programaren hasieran.
- `--verbose` `-v` Egin komando-lerroko mezuak eta erregistroak zehatzagoak.
- `--threaded` `-t` Exekutatu hari bat baino gehiagorekin. *Defektuz: false/faltsua*

## Fitxategi Izen Formatua
#### Izen formatua
`manga_titulua [hizkuntza] - cXXX (vYY) (kapitulu_izena) {argitaratze_data} [taldea(k)]`

#### Izen parametroak
- `manga_titulua` Mangaren izenburua (`name_id_map.json`-eko gako bera) edo MangaDex-eko IDa.
- `[hizkuntza]` Kapituluaren hizkuntza-kodea ISO formatuan. *Ingeleserako ez da beharrezkoa.*
- `cXXX` Kapituluaren zenbakia. *Kendu kapituluaren aurrizkia titulua kapitulu bakarrekoa bada (Oneshot), adibidez `cXXX` > `XXX`.*
- `(vYY)` Kapituluaren bolumena. *Ez da derrigorrezkoa.*
- `(kapitulu_izena)` Kapituluaren izenburua. `?` karakterearen ordez, `{question_mark}` erabili. *Ez da derrigorrezkoa.*
- `{argitaratze_data}` Kapitulua MangaDexen argitaratzeko nahi den etorkizuneko data. **Ezartzen bada, `YYYY-MM-DDTHH-MM-SS` formatua jarraitu behar du.** *Ez da derrigorrezkoa.*
- `[taldea(k)]` Taldeen izenen edo IDen zerrenda. Talde-izenak badira, `name_id_map.json`-en IDekin batera sartu behar dira. *Talde bat baino gehiago bereizi `+` erabiliz.* *Ez da derrigorrezkoa.*

#### Onartutako Fitxategi Formatuak
- `png`
- `jpg` / `jpeg`
- `gif`
- `webp` *`png`, `jpg` edo `gif` bihurtuko dira karga prozesuan.*

## Konfigurazioa
Erabiltzaileak alda ditzakeen ezarpenak `config.json` fitxategian daude eskuragarri. Hemen ere jarri behar dira MangaDex-eko kredentzialak.
Kopiatu eta kendu `.example` zatia `config.json.example` fitxategitik konfigurazio fitxategia erabiltzen hasteko.

*Oharra: JSON balioak ezin dira hutsik egon, beraz, erabili (`null`) balio bat hutsik utzi nahi den tokian, karaktere-kate bat (`"erabiltzaile-izena"`) kate-balioentzako edo zifrak (`1`) zenbaki-balioentzako.*

#### Aukerak
- `number_of_images_upload` Aldi berean igo beharreko irudi kopurua. *Defektuz: 10*
- `upload_retry` Irudiak edo kapitulua igotzeko saiakera kopurua. *Defektuz: 3*
- `ratelimit_time` API deien ondoren itxaroteko denbora (segundutan). *Defektuz: 2*
- `max_log_days` Erregistroak mantentzeko egun kopurua. *Defektuz: 30*
- `group_fallback_id` Erabili beharreko talde IDa, fitxategian edo ID mapan ezarritako talde IDa aurkitzen ez bada. *Defektuz: null*
- `number_threads` Aldi berean irudiak igotzeko hari kopurua. **Honek mugatu zaitzake.** Hariak 1-3 tartera mugatzen dira (biak barne). *Defektuz: 3*
- `language` Komando-lerroko mezuetarako hizkuntza. *Defektuz: null*

#### Kredentzialak
***Balio hauek ezin dira hutsik egon, bestela programa ez da abiaraziko.***
- `mangadex_username` MangaDex erabiltzaile-izena.
- `mangadex_password` MangaDex pasahitza.
- `client_id` MangaDex API bezeroaren IDa.
- `client_secret` MangaDex API bezeroaren kode sekretua.

#### Rutak
*Aukera hauek dauden bezala utzi daitezke, ez da beharrezkoa ezer aldatzea.*
- `name_id_map_file` Izen-ID-maparen fitxategi izena. *Defektuz: name_id_map.json*
- `uploads_folder` Igotzeko kapituluak kargatzeko direktorioa. *Defektuz: to_uploads*
- `uploaded_files` Igotako kapituluak mugitzeko direktorioa. *Defektuz: uploaded*
- `mangadex_api_url` MangaDex API URLa. *Defektuz: https://api.mangadex.org*
- `mangadex_auth_url` MangaDex autentifikazio URLa. *Defektuz: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` MangaDex-en saioa hasteko tokena gordetzeko fitxategia. *Defektuz: .mdauth*

<details>
  <summary>Nola lortu bezero IDa eta kode sekretua.</summary>

  ![mangadex-mass-uploaderraren pantaila-argazki bat](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![mangadex-mass-uploaderraren pantaila-argazki bat](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />

## Mapa
`name_id_map.json` fitxategiak honelako formatua du:
```json
{
    "manga": {
        "hyakkano": "efb4278c-a761-406b-9d69-19603c5e4c8b"
    },
    "group": {
        "XuN": "b6d57ade-cab7-4be7-b2b8-be68484b3ad3"
    }
}
```
`manga` eta `group` igo beharreko manga eta taldeen IDak dituzte hurrenez hurren. Izenak igo beharreko fitxategien berdina izan behar du. Exekutatzerakoan arazoak ekiditeko, minuskulak eta zuriuneak ez dituen izenak erabiltzen saiatu.

Izen-ID bikote berri bakoitza lerroaren amaieran koma batekin eta izenaren eta IDaren artean bi puntu batez bereizi behar dira. Mapa bakoitzeko azken bikoteak ez luke komarik izan behar.

#### Adibidea
Haru `hyakkano - c025 (v04) [XuN].cbz` igo nahi dugun kapitulu gisa. Gure `name_id_map.json` fitxategian, `hyakkano` gakoa eta `efb4278c-a761-406b-9d69-19603c5e4c8b` balioa erabili beharko genituzke titulu-ID bikotea ezartzeko. Talde maparako, `XuN` ere jarri beharko genuke `b6d57ade-cab7-4be7-b2b8-be68484b3ad3` balioarekin.

Exekutatzerakoan, programak fitxategi honetan bilatuko lituzke `hyakkano` eta `XuN` haien esleitutako IDak lortzeko.

`efb4278c-a761-406b-9d69-19603c5e4c8b [eu] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]` izeneko fitxategi bat badugu, programak kapituluaren atributuak honela ezarritu egingo lituzke:
- `efb4278c-a761-406b-9d69-19603c5e4c8b`: Mangaren IDa fitxategitik zuzenean hartuko luke.
- `[eu]`: Hizkuntza gisa euskara `eu` kodearekin.
- `000`: Kapitulu zenbakia nulua (Oneshot).
- Bolumenik ez (nulua).
- `(Momi-san)`: `Momi-san` kapituluaren izenburua izango litzateke.
- `[XuN+00e03853-1b96-4f41-9542-c71b8692033b]`: `XuN` taldearen IDa `name_id_map.json` fitxategitik hartuko luke, eta bigarren taldearena fitxategi izenean bertan dago.

## Ekarpenak
- Ziurtatu ez daudela bikoiztutako arazorik irekita berri bat sortu baino lehen.
- Beharrezkoa dela uste baduzu "Pull Request" (PR) bat ireki dezakezu, baina mesedez kodea Python Black erabiliz formateatu hori egin aurretik (lehenetsitako ezarpenekin).

### Itzulpenak
Bi fitxategi daude itzultzeko, readme hau eta [mupl/loc/en.json](/mupl/loc/en.json) fitxategia.

- Itzulitako README fitxategia [/doc/](doc/) direktorioan sartu `readme.<>.md` izenarekin, eta <> dagokion ISO hizkuntza-kodearekin ordezkatu. Adibidez: `readme.eu.md`. Zure readme fitxategia eguneratu jatorrizko readme fitxategira estekatzeko "Jatorrizko bertsioa" atalean.
- Itzulitako JSON fitxategia [/mupl/loc/](/mupl/loc/) direktorioan gorde behar da `<>.json` izenarekin, eta <> lehen erabilitako ISO kode bera erabiliz ordezkatuz. Adibidez: `eu.json`.

Fitxategi hauek itzuli ondoren, eguneratu jatorrizko README fitxategia zure itzulpenaren esteka batekin. Horren ondoren, PR bat sortu aldaketekin.