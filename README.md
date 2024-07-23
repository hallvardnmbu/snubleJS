<body style="font-family:monospace;">


![Vinskraper](./static/vinskraper.jpg)

Utforsk og sammenlikn [vinmonopolets](https://www.vinmonopolet.no) utvalg og prisendringer.

<div style="text-align: center;">
    <img src="./static/logo.jpg" style="width: 50%;">
</div>

---

![Veiledning](./static/veiledning.jpg)

Applikasjonen bruker [Writer Framework](https://dev.writer.com/framework/introduction)
(tidligere [StreamSync](https://pypi.org/project/streamsync/)). Python brukes dermed for
funksjonaliteten til `vinskraper`.

![Lokalt](./static/lokalt.jpg)

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

![DigitalOcean](./static/DigitalOcean.jpg)

I tillegg til å kunne kjøres lokalt, er applikasjonen kjørt i "skyen" – ved bruk av
[DigitalOcean](https://www.digitalocean.com).

Baktanken her er å gjøre applikasjonen tilgjengelig for navngitte personer via internett, samt
bli bedre kjent med fjern-løsninger.

For å få tilgang til nettsiden; gi lyd.

Hver månedsskifte kjøres en jobb som henter ny data for alle kategorier, og lagrer oppdateringene til databasen.

---

</body>
