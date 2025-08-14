# Estonia Building Age Map

[Browse it here](https://osmz.ee/hooned/).

Where to get the data:

* [ETAK](https://geoportaal.maaamet.ee/est/ruumiandmed/eesti-topograafia-andmekogu/laadi-etak-andmed-alla-p609.html):
    open Geoportal / Ruumiandmed, Eesti topograafia andmekogu, Laadi ETAK andmed alla.
    Choose "Ehitised" as Esri SHP.
* [EHR](https://livekluster.ehr.ee/ui/ehr/v1/infoportal/reports):
    open E-ehitus, choose Infoportaal ja avaandmed, Ehitisregistri avaandmed, Aruanded.
    There open "Ehitised", put in your e-mail and choose "CSV" for the file format. Click "Saadan tellimuse"
    and wait a couple minutes for an email.

Unpack the zip file into the `data` directory and rename the file to `ehr-YYMMDD.csv` (with the current date).
Put the ETAK zip there as well (do not unpack, you will regret it). Then run:

    uv run scripts/prepare_jsonl.py > hooned.jsonl

Then [install Tippecanoe](https://github.com/felt/tippecanoe?tab=readme-ov-file#installation) and prepare the
vector tiles:

    tippecanoe -z13 --drop-densest-as-needed --simplify-only-low-zooms -l hooned -S 6 -M 300000 --generate-ids -o web/hooned.pmtiles -f hooned.jsonl

Finally, upload the contents of the `web` directory somewhere.

## Why the dates are wrong?

We are using the "Esmase kasutuselevõtu aasta" field from the building register, which is not exactly the date it was first built.
The hint can be translated as _"The year the building was completed or the year its first notice of use or occupancy permit
was entered into the building register. The year of the building's initial commissioning is presumptive if it is derived
from indirect sources, such as historical orthophotos and maps."_ So, it can be incorrect.
Some examples we've found:

* [Pihlaka 12i, Tallinn](https://livekluster.ehr.ee/ui/ehr/v1/building/101018040) is marked 1999, but before that it was a school building
    finished somewhere in 1950s. In 1999 it was converted to a social house.
* [Tuukri 1b, Tallinn](https://livekluster.ehr.ee/ui/ehr/v1/building/120796837) is marked 1972, but it was completely raised after that,
    rebuilt from scratch in 2020. There is a [service building](https://livekluster.ehr.ee/ui/ehr/v1/building/220795174) from 2020
    at that place, but it's not split into visible buildings.
* [Narva Castle](https://livekluster.ehr.ee/ui/ehr/v1/building/118008962) is marked 1986, despite being built way, way before that (around 1256).
    Same for buildings around it.
* [Tallinna Raekoda](https://livekluster.ehr.ee/ui/ehr/v1/building/101036399) and many other buildings on the old town
    don't have dates at all.

## Acknowledgments

This code is published under ISC licence by its author, Ilja Zverev.

Big thank you goes to Maa- ja Ruumiamet, whose geodata packages are over-comprehensive, containing links
to every register imaginable. And for managing all those registers. And publishing them as open data.

Based on the [2017 map](http://eilat.ee/2017-01-09-tallinna-hoonete-vanus/) by Toomas Eilat.

For learning about future developments, I recommend [Citify](https://citify.eu/).
