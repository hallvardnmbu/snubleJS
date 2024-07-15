<body style="font-family:monospace;">

# Vinskraper

Utforsk og sammenlikn [Vinmonopolets](https://www.vinmonopolet.no) utvalg og prisendringer.

![Vinskraper](./vinskraper.jpg)

---

## Veiledning

For å kjøre applikasjonen lokalt må først de nødvendige pakkene installeres;

```bash
pip install -r requirements.txt
```

Deretter åpnes applikasjonen med

```bash
writer run vinskraper
```

i terminalen (fra hovedmappen).

---

### Henting og oppdatering av data

Dersom ingen data finnes fra før av, vil programmet automatisk hente ny data for den valgte 
kategorien. 

For historikkens skyld, lagres all hentet data i respektive `parquet`-filer. Dersom disse 
slettes vil ikke tilbud kunne utreknes (iom. at de baseres på historisk pris).

Dersom historisk data eksisterer (i kategoriens respektive `parquet`-fil), vil den nye prisen 
bli lagt til som en egen kolonne. Alle pris-kolonner har datoen de ble hentet som _suffix_.

---

</body>