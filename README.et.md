# VACZEN Calendar

> Häireteta, ühe failiga Tk-kalender + ülesannete haldur.
> Vaikimisi Win95-tume. Üks Pythoni fail, null sõltuvust.

<p align="center">
  <img alt="Litsents" src="https://img.shields.io/github/license/vacterro/VACZEN-Calendar?style=for-the-badge&color=9DD9F9">
  <img alt="Versioon" src="https://img.shields.io/badge/version-0.0.1-9DD9F9?style=for-the-badge">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-9DD9F9?style=for-the-badge&logo=python&logoColor=black">
  <img alt="Üks fail" src="https://img.shields.io/badge/%C3%BCks%20fail-jah-9DD9F9?style=for-the-badge">
  <img alt="Sõltuvused" src="https://img.shields.io/badge/s%C3%B5ltuvused-stdlib%20only-9DD9F9?style=for-the-badge">
</p>

<p align="center">
  <img alt="Repo suurus" src="https://img.shields.io/github/repo-size/vacterro/VACZEN-Calendar?style=flat-square">
  <img alt="Koodi suurus" src="https://img.shields.io/github/languages/code-size/vacterro/VACZEN-Calendar/ZEN_CALENDAR.py?style=flat-square&label=ZEN_CALENDAR.py">
  <img alt="Viimane commit" src="https://img.shields.io/github/last-commit/vacterro/VACZEN-Calendar?style=flat-square">
  <img alt="Issues" src="https://img.shields.io/github/issues/vacterro/VACZEN-Calendar?style=flat-square">
</p>

<p align="center">
  <a href="https://buymeacoffee.com/vacuum34"><img alt="Toeta" src="https://img.shields.io/badge/%E2%9D%A4%EF%B8%8F%20Toeta-9DD9F9?style=for-the-badge"></a>
  <a href="docs/overview.md"><img alt="Dokid" src="https://img.shields.io/badge/%F0%9F%93%9D%20Dokid-9DD9F9?style=for-the-badge"></a>
  <a href="#-%C3%BCldklahendused"><img alt="Klahvid" src="https://img.shields.io/badge/%E2%9C%A8%20Otseteed-9DD9F9?style=for-the-badge"></a>
</p>

---

## 📸 Ekraanipilt

```
┌──────────────────────────────────────────────────────────────┐
│  Teisipäev, 01. sept 2026  14:23:07   ◀ ▶   September 2026   │
├──────────────────────────────────────────────────────────────┤
│  Es  Te  Ko  Ne  Re  La  Pü                                  │
│       [ 1] [ 2] [ 3] [ 4] [ 5] [ 6]                          │
│   [ 7] [ 8] [ 9][10] [11] [12] [13]                          │
│  [14] [15] [16] [17] [18] [19] [20]                          │
│  [21] [22] [23] [24] [25] [26] [27]                          │
│  [28] [29] [30] [ 1] [ 2] [ 3] [ 4]                          │
│                                                              │
│            ┌─ Valitud: Kolmapäev, 16. sept ─────┐             │
│            │ • 09:00  Tiimi koosolek   [teht]  │             │
│            │ • 14:00  PR #142 ülevaatus        │             │
│            │ • 19:30  🏃 Jooks, laiskvorst    │             │
│            └────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
   Ctrl+K  sätted    f   fookus    s   salvesta    Esc   välju
```

> ASCII-joonistus — päris asi on vaikimisi tume, kuldne-mustal, piksl-puhas.
> Kui tõeline ekraanipilt olemas, aseta see `docs/screenshot.png` ja eemalda
> allolev HTML-kommentaar.

<!-- ![VACZEN Calendar Windowsis](docs/screenshot.png) -->

---

## ✨ Võimalused

| | |
|---|---|
| 🎯 **Üks fail, üks mõte** | Kogu rakendus on `ZEN_CALENDAR.py`. Raamistikku, pakki, vendoreeritud koopiaid pole. |
| 📦 **Null sõltuvust** | Ainult Pythoni standardteek. `tkinter`, `json`, `datetime`, `pathlib`. `pip install` pole vaja. |
| 🌑 **Vaikimisi Win95-tume** | Mustad paneelid, kuldsed aktsendid, animatsioonideta, antialiasinguta. Aku-sõbralik. |
| ⚡ **Klaviatuur-esimene** | Iga tegevus on üks klahv. Hiir valikuline. |
| 💾 **Atomaarne salvestus** | Protsessidevahelise lukuga, generatsioonikontrolliga kirjutus. Kaks instantsi ei kirjuta teineteist üle. |
| 🛡️ **Iseparanev laadimine** | Vigane JSON → karantiini, viimast koopiat ei kirjutata kunagi üle. Vigased kuupäevad isoleeritakse, neid ei visata vaikselt minema. |
| 🪟 **Fookusrežiim** | Üks klahv (`f`) peidab kõik peale kalendri. Tähelepanematu-kindel. |
| ⚙️ **15 värvi teema** | Taust, paneelid, tekst, päis, nädalavahetus, täna, valitud, aktsent — kõik reaalajas seadistatavad. |
| 🌍 **i18n** | `lang: ru / en / uk`. Sätete võti, kõik UI-sõned järgivad. |
| 🔢 **ISO nädalate numbrid** | Valikuline veerg. |
| 🕐 **Reaalajas kell** | All-paremal, ise-ajastuv, ei jää kunagi maha. |
| 📐 **Geomeetria, mis mäletab** | Akna suurus, asukoht, täisekraan, always-on-top. Käib andmefaili kaudu ringluse. |

---

## 🚀 Paigaldus

```bash
# 1. Klooni
git clone https://github.com/vacterro/VACZEN-Calendar.git
cd VACZEN-Calendar

# 2. Käivita (paigaldussammu pole)
python ZEN_CALENDAR.py
```

See on kõik. Python 3.11 või uuem. Virtuaalenv pole vaja — midagi pole
paigaldada. Windowsis võid ka ümber nimetada `.pyw`-ks või käivitada
`pythonw.exe`-ga, et konsooli ei kuvataks.

---

## ⌨️ Üldklahendused

Kõik allolevad seosed on summutatud, kui trükid redaktoris või kui
Sätete paneel on lahti — nii ei lähe mustand kaduma juhusliku klahvi tõttu.

| Klahv | Tegevus |
|---|---|
| `←` / `→` | Eelmine / järgmine kuu |
| `↑` / `↓` | Eelmine / järgmine aasta |
| `f` | Lülita **fookusrežiimi** |
| `a` | Lisa ülesanne valitud päevale |
| `e` | Muuda valitud ülesannet |
| `d` | Kustuta valitud ülesanne |
| `s` | Salvesta kohe |
| `Tühik` | Märgi valitud ülesanne tehtuks / tagasi |
| `Enter` | Redaktoris → kinnita; mujal → värskenda detailkasti |
| `Esc` | Sätted lahti → sulge; redigeerid → tühista; muidu → välju |
| `Ctrl+K` | Lülita sätete paneel |

---

## 📂 Projekti paigutus

```
VACZEN-Calendar/
├── ZEN_CALENDAR.py          ← kogu rakendus
├── CalendarTask_data.json   ← sinu ülesanded (luuakse automaatselt, gitignore'is)
├── ZenCalendar_data.json    ← (pärand) sama faili alternatiivne nimi
├── docs/                    ← arhitektuur ja viited
│   ├── overview.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── ui-and-rendering.md
│   ├── settings.md
│   ├── keyboard.md
│   └── canonical-ids.md
├── README.md                ← siin sa oled
├── README.et.md             ← eesti keel
├── README.ru.md             ← русский
├── CONTRIBUTING.md
└── LICENSE                  ← MIT
```

---

## 📚 Dokumentatsioon

| Doc | Mida katab |
|---|---|
| [Ülevaade](docs/overview.md) | Mis rakendus see on, ja mis ta pole. |
| [Arhitektuur](docs/architecture.md) | Meetod-haaval kaart `ZEN_CALENDAR.py`-st. Ilma kätevõbistamiseta. |
| [Andmemudel](docs/data-model.md) | JSON-i kuju, atomaarne salvestus, karantiin, taastumine. |
| [UI & renderdus](docs/ui-and-rendering.md) | Teema, fondid, geomeetria, fookusrežiim. |
| [Sätted](docs/settings.md) | `DEFAULT_SETTINGS`, valideerimisleping, rakendamise torustik. |
| [Klahvid](docs/keyboard.md) | Täielik klahv → teisendaja tabel. |
| [Kanoonilised ID-d](docs/canonical-ids.md) | Nimed, mida refaktoreerimine ei tohi murda. |

---

## 🤝 Kaastöö

Issues ja PR-d on teretulnud. Veateated: lisa oma OS, Pythoni versioon
(`python --version`) ja andmefaili sisu (või redigeeritud katkend — teed
ja märkmed võib puhastada).

Suuremate muudatuste jaoks ava enne issue, et saaksime kujus enne sinu
nädalavahetust kokku leppida. Vaata [CONTRIBUTING.md](CONTRIBUTING.md).

---

## ❤️ Toeta

Kui see hoiab su telefoni eemal ja sind oma tegeliku ajakava ees:

<a href="https://buymeacoffee.com/vacuum34"><img alt="Osta mulle kohvi" src="https://img.shields.io/badge/osta%20mulle%20kohvi-vacuum34-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>

---

## 📜 Litsents

[MIT](LICENSE) — tee mida tahad, lihtsalt hoia autoriõiguse rida alles.

---

<p align="center">
  <sub>VACZEN Calendar · v0.0.1 · üks fail · null sõltuvust · klaviatuur-esimene</sub>
</p>
