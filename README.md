<body style="font-family:monospace;">

# Snublejuice

Kildekode til [snublejuice](https://snublejuice.no) – en applikasjon for å utforske og sammenlikne [vinmonopolets](https://www.vinmonopolet.no) utvalg og prisendringer.

<div style="text-align: center;">
    <img src="./static/logo.jpg" style="width: 50%;">
</div>

---

## Informasjon

Applikasjonen bruker [Writer Framework](https://dev.writer.com/framework/introduction)
(tidligere [StreamSync](https://pypi.org/project/streamsync/)). Python brukes dermed for
funksjonaliteten til [snublejuice](https://snublejuice.no).

<details>
  <summary>Kjør applikasjonen lokalt</summary>

  For å kunne kjøre applikasjonen lokalt må (Python eksistere, og) de nødvendige pakkene
  installeres. Dette gjøres ved;

```bash
pip install -r requirements.txt
```

  i terminalen, for så å åpne applikasjonen med

```bash
writer run .
```

  (også fra terminalen).

  OBS: For å kunne kjøres lokalt må enkelte miljøvariabler settes. Dette gjøres ved å kjøre;

```bash
export mongodb_username=<username>
export mongodb_password=<password>
```

  (eller tilsvarende for ditt operativsystem). Hvor `<username>` og `<password>` er brukernavn og passord til din [MongoDB](https://www.mongodb.com)-database (hvilket kan opprettes gratis).

  Første gang applikasjonen kjøres lokalt må databasen initialiseres. Dette gjøres ved å kjøre;

```bash
python ./scrape/scrape.py
```

  (etter å ha oppretted databasen `vinskraper` og collection `varer`).

  For å få fullstendig produktinformasjon, må også funksjonen `details` i `./scrape/news.py` kjøres.

</details>

<details>
  <summary>DigitalOcean</summary>

  I tillegg til å kunne kjøres lokalt, er applikasjonen kjørt i "skyen" – ved bruk av
  [DigitalOcean](https://www.digitalocean.com).

  Baktanken her er å gjøre applikasjonen tilgjengelig for navngitte personer via internett, samt bli bedre kjent med fjern-løsninger.

  Hver dag kjøres `./scrape/available.py` for å oppdatere databasen med tilgjengelige produkter.

  Annenhver uke kjøres `./scrape/news.py` for å oppdatere databasen med ny informasjon om produkter.

  Hver månedsskifte kjøres `./scrape/scrape.py` for å oppdatere databasen med prisendringer.

</details>

</body>
