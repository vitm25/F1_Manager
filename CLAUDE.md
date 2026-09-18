# F1 Manager 2025 – kontext pro AI

Jazyk komunikace s uživatelem: **čeština**.

## Přehled
Pygame F1 Manager simulace sezóny 2025. Hráč vybere tým, řídí strategii (pneumatiky,
boxy) a sleduje závody v reálném čase se zrychlením času. Kód je z velké části
monolitický v `manager.py`.

## Soubory
- `manager.py` – téměř veškerá herní logika (~2800+ řádků), třídy obrazovek, `Driver`,
  hlavní smyčka `while True`.
- `tracks_data.py` – data tratí (racing_line, mapa, DRS zóny, pit lane, laps…).
- `championship_data.py` – `TEAMS`, `DRIVER_BASE_TIMES`, `CALENDAR_2025`.
- `cover2.py` – (zjistit účel, pokud bude potřeba).
- `racing_line_editor.py` – editor tras pro `racing_lines/`.
- `saves/`, `savegame.json` – uložené hry v JSON.
- `sounds/` – `start_cz.mp3`, `start_en.mp3`.

## Klíčové globální proměnné
`CURRENT_LANGUAGE` (CS/EN/IT), `CURRENT_RACE_MODE` (SHORT/FULL), `CURRENT_FPS`,
`IS_FULLSCREEN`, `AUDIO_ENABLED`.

## Lokalizace
Vše přes slovník `TEXTS` + `get_text(key)`. Nikdy nenechávat hardcoded české texty v UI.

## Race mode (SHORT vs FULL)
Oba režimy jedou **plný počet kol** z dat tratě. Liší se jen `self.time_compression`
(nastaveno v `_load_race`, ~řádek 684): FULL = 1.0 (reálný čas), SHORT = 0.35
(zrychleno). Používá se v `update()` při výpočtu posunu: `speed *= self.time_compression`.

## Hlavní třídy/stavy
`ChampionshipScreen.state`: `TEAM_SELECT` → `SEASON_START` → `RACE`, plus `SAVE_LIST`.
In-game menu: `show_ingame_menu` + `paused` (ESC otvírá/zavírá, Pause tlačítko jen
pauzuje čas).

Race phases (`self.race_phase`): `RACE_PHASE_FORMATION` → `RACE_PHASE_START` →
`RACE_PHASE_RACING`.

## Pozice na trati (důležité pro pořadí/SC/předjíždění)
Skutečná "vzdálenost" jezdce se v `handle_battles()` počítá jako
`current_lap * path_len + track_index + progress` (kde `progress` je 0–1 úsek mezi
dvěma body racing line a `path_len = len(racing_line)`). **Toto je zdroj pravdy pro
pořadí na trati** – ne `driver.distance`, který se nastavuje jen v `__init__` na 0.0
a nikde jinde needituje (mrtvý atribut, používá ho ale `update_drs()` pro DRS gap –
tzn. DRS gap výpočet je aktuálně nefunkční/vždy stejný, protože `distance` se nemění).

## Safety Car – dlouhodobě nejproblematičtější systém
Stav: `safety_car_active`, `safety_car_timer`, `safety_car_index`, `safety_car_progress`.

Současné chování (viz `manager.py`):
- `get_speed()` (řádek ~230) vrací pevnou hodnotu `0.34` pro **všechny** jezdce, pokud
  je SC aktivní – bez ohledu na to, kde na trati jezdec je vůči SC.
- `handle_battles()` (řádek ~1131) má `return` hned na začátku, pokud je SC aktivní –
  žádné předjíždění, ale taky žádné vynucené řazení do vláčku.
- SC se vizuálně vykresluje jako žlutý kruh s textem „SC“ (kreslení kolem řádku 1539).
- **Problém:** protože všichni jezdci jedou stejnou rychlostí, jejich vzájemné rozestupy
  (které vznikly PŘED nasazením SC) se nikdy nesrovnají – nikdo se nezformuje do vláčku
  za safety carem. Efektivně jen zpomalí celé pole na místě, bez re-grupování.

**Cíl uživatele:** Auta se mají seřadit za safety carem (reálné rozestupy, ideálně
podle aktuálního pořadí) a teprve po seřazení/dojetí posledního jezdce se SC stáhne a
závod se restartuje – jako ve skutečné F1.

Navrhovaný směr opravy (nekódováno, jen poznámka pro příště): potřeba nová metoda
`enforce_safety_car_order()` volaná z `update()`, která:
1. Spočítá pozici SC vozu jako `safety_car_index + safety_car_progress` (bez laps,
   protože SC nekrouží "kola" stejně jako auta – nebo přidat ekvivalent lapu).
2. Nikomu nedovolí být před SC (leader capped na pozici SC).
3. Jezdcům za SC nastaví rychlost tak, aby dojeli na "svoje místo ve frontě" za
   vozem před nimi (ne fixní 0.34 pro všechny), dokud nejsou všichni v těsném vláčku.
4. Teprve když je poslední jezdec dostatečně blízko frontě, odpočítávat
   `safety_car_timer` / povolit stažení SC.
Změna se musí udělat současně v `get_speed()`, bloku pohybu SC v `update()` a
`handle_battles()` (a případně nové metodě výše).

## Ostatní implementované systémy
Pneumatiky + opotřebení + AI stinty (`ai_plan_stint`, `ai_should_pit`), počasí, DRS
(`update_drs`), incidenty/DNF (`generate_incident`), formation lap + startovací audio
komentář (CS/EN), plná lokalizace CS/EN/IT, ukládání/načítání JSON + auto-save po
závodě, in-game menu (ESC), Settings (FPS, Race Length, Language).

## TODO priority
**Vysoká:** Safety Car (viz výše).
**Střední:** doplnit chybějící překlady hardcoded textů; realističtější rozestupy
(aby nebyly 10+ kol rozdíl); lepší AI strategie při SC/VSC; formation lap pomalu 1 kolo
před startem.
**Nízká:** Practice mode (zatím prázdný); další jazyky (DE...).

## Styl práce
- Vždy nejdřív přečíst aktuální `manager.py` před úpravou (mění se často mimo session).
- Žádné hardcoded české texty v UI – vždy přes `get_text()`.
- Preferovat malé, cílené změny; uživatel často chce "nahraď tuto metodu tímto".
- Při úpravě SC upravit současně `get_speed()`, pohyb SC v `update()` a
  `handle_battles()`.
- Po úpravách UI otestovat tok ESC → in-game menu → Settings → zpět.
- `git` repozitář existuje v `F1_Manager/.git` (podsložka projektu, ne kořen).
