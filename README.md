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
installeres. Dette gjøres ved å først navigere seg til riktig mappe:

```bash
cd local
```

for så å kjøre;

```bash
pip install -r requirements.txt
```

i terminalen. Deretter åpnes applikasjonen med

```bash
writer run .
```

(også fra terminalen).

![DigitalOcean](./static/DigitalOcean.jpg)

I tillegg til å kunne kjøres lokalt, er applikasjonen kjørt i "skyen" – ved bruk av 
[DigitalOcean](https://www.digitalocean.com).

Baktanken her er å gjøre applikasjonen tilgjengelig for navngitte personer via internett, samt 
bli bedre kjent med fjern-løsninger.

For å få tilgang til nettsiden; gi lyd.

---

![Data](./static/data.jpg)

![Lokalt](./static/lokalt.jpg)

Dersom ingen data finnes fra før av, vil programmet automatisk hente ny data for den valgte 
kategorien. 

For historikkens skyld, lagres all hentet data i respektive `parquet`-filer. Dersom disse 
slettes vil ikke tilbud kunne utreknes (iom. at de baseres på historisk pris).

Dersom historisk data eksisterer (i kategoriens respektive `parquet`-fil), vil den nye prisen 
bli lagt til som en egen kolonne. Alle pris-kolonner har datoen de ble hentet som _suffix_.

![DigitalOcean](./static/DigitalOcean.jpg)

For å gjøre ting enda mere komplisert, brukes en ekstern database for "sky"-applikasjonen (selv 
om det vel å merke er mulig å bruke "lokale" `parquet`-filer her også). 

I lik linje er dette gjort for å få en bedre forståelse for sammenkoblede tjenester i "skyen".

Her brukes [MongoDB](https://www.mongodb.com) som vert.

---

</body>