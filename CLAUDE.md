# F1 Manager 2025 – kontext pro AI

Jazyk komunikace s uživatelem: **čeština**.

## Přehled
Pygame F1 Manager simulace sezóny 2025. Hráč vybere tým, řídí strategii (pneumatiky,
boxy) a sleduje závody v reálném čase se zrychlením času. Kód je z velké části
monolitický v `manager.py`.

## Cesty k souborům (mapy, zvuky, uložené hry)
Všechny cesty k assetům (mapa tratě `tracks_data.py -> "map"`, zvuky `START_COMMENT_CS/EN`,
`save_folder`) se skládají přes `SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))`
definovaný na začátku `manager.py`, ne jako holé relativní řetězce. Důvod: pokud se hra
spustí s jiným pracovním adresářem, než je `F1_Manager/` (typicky když IDE nastaví cwd na
kořen workspace, což je nadřazená složka), `pygame.image.load("tracks/....png")` tiše
selže (chyba se jen vypíše do konzole přes `except Exception`) a mapa i auta na ní
zmizí – zbytek UI (leaderboard, standings, boxy) přitom funguje normálně, protože na
tom cestách nezávisí. Když se příště přidá nový asset (další zvuk, obrázek, soubor),
vždy ho načítat přes `os.path.join(SCRIPT_DIR, ...)`, jinak se stejný bug vrátí.

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

## Safety Car – opraveno (seřazování do vláčku funguje)
Stav: `safety_car_active`, `safety_car_timer`, `safety_car_index`, `safety_car_progress`,
`safety_car_laps` (kumulativní počet průjezdů SC, aby šla pozice SC srovnávat s pozicí
jezdců stejně jako `current_lap*path_len+track_index+progress`), `safety_car_lined_up`
(True, jakmile je celé pole seřazené v těsném vláčku).

Jak to funguje:
- `deploy_safety_car(min_duration, max_duration)` nasadí SC na pozici AKTUÁLNÍHO LÍDRA
  (ne na start/cíl) a nastaví náhodný timer.
- `update_safety_car_queue()` (volaná každý frame, dokud je SC aktivní) spočítá pro
  každého jezdce cílový slot ve frontě za SC (`sc_pos - SAFETY_CAR_LEADER_GAP - i*SAFETY_CAR_CAR_GAP`
  podle aktuálního pořadí) a rychlost dohánění úměrnou velikosti mezery
  (`SAFETY_CAR_MAX_CATCHUP_TIME` = i auto ztracené o celé kolo dožene frontu nejpozději
  za tuto dobu). Uloží výsledky do `self._sc_speed_overrides`.
- `get_speed()` při aktivním SC (a jezdec není v pit lane) vrací
  `race.get_safety_car_speed(driver)` místo normálního výpočtu.
- `handle_battles()` při aktivním SC rovnou vrací (žádné předjíždění).
- SC se stáhne (`safety_car_active=False`) až když je `safety_car_timer<=0` **A**
  zároveň `safety_car_lined_up` je True – ne jen podle vypršení časovače.
- **Důležité:** pokud během SC nastane další incident, NESMÍ se znovu volat
  `deploy_safety_car()` (to by resetovalo pozici SC i `lined_up` a fronta by se nikdy
  nedoseřadila) – místo toho se jen prodlouží `safety_car_timer`. Viz
  `generate_incident()`.
- SC se také nesmí spouštět (ani z `generate_incident()`, ani z náhodného triggeru v
  `update()`) během `RACE_PHASE_FORMATION` – obojí je ošetřené podmínkou
  `self.race_phase != RACE_PHASE_FORMATION`.

## Formační kolo – pevné pořadí podle roštu
Uživatel chtěl, aby se auta na formačním kole neproháněla/nepředjížděla, ale zůstala
přesně v pořadí, v jakém vyjela (P1 zůstane P1, P2 zůstane P2 atd.), stejně jako ve
skutečné F1.

Implementace (`Driver.grid_position`, `Driver.formation_start_delay`, konstanty
`FORMATION_SPEED_KMH`, `TRACK_LENGTH_KM` a `FORMATION_GRID_GAP` u `get_speed()`):
- V `_load_race()` se po resetu jezdců projde `self.drivers` v aktuálním pořadí
  (= pořadí, v jakém se zobrazují na startu leaderboardu) a každému se přiřadí
  `grid_position = i` a `formation_start_delay = i * FORMATION_GRID_GAP` (v sekundách
  `race_time`).
- `get_speed()` má na začátku větev pro `race.race_phase == RACE_PHASE_FORMATION`:
  dokud `race.race_time < driver.formation_start_delay`, auto stojí (rychlost 0);
  jakmile přijde na řadu, jede pevnou rychlostí dopočítanou z
  reálné délky okruhu (viz níže) – **stejnou pro všechny**, takže se
  jednou vzniklé rozestupy už nikdy nezmění.
- Aby to fungovalo, MUSÍ během formačního kola zůstat vypnuté všechny mechanismy, které
  by mohly pozici jezdce změnit mimo tuhle logiku:
  - `handle_battles()` – vrací se rovnou, pokud `self.race_phase == RACE_PHASE_FORMATION`
    (stejně jako u SC).
  - Generování incidentů/DNF/SC (`generate_incident`) – volá se jen mimo formaci.
  - Náhodný trigger SC v `update()` – stejně tak jen mimo formaci.
  - Celý blok "AI rozhodnutí" (pace mode, `ai_should_pit`, pity) – AI týmy během
    formačního kola nepitují ani nemění tempo (hráčovi jezdci nikdy nepitují sami,
    takže se jich to netýká přímo, ale bez téhle podmínky by cizí AI auta mohla
    zahájit pit stop uprostřed formačního kola a rozhodit pořadí).
- Ověřeno headless simulací (bez GUI, `exec` zdrojáku bez závěrečného `while True`):
  formační kolo proběhne bez jediné změny pořadí; jediná legitimní změna nastává na
  framu, kdy `race_phase` přejde na `RACING` (start na semaforech smí zamíchat
  pořadím, to je v pořádku).
- **Rychlost formace, nezávislost na SHORT/FULL i na trati:** Formační kolo je
  ÚMYSLNĚ nezávislé na `time_compression` (SHORT/FULL) - `get_speed()` u formace
  vrací `pace / time_compression`, což se o pár řádků výš v `update()` zase vynásobí
  `time_compression`, takže efektivní rychlost je vždy stejná bez ohledu na zvolený
  režim závodu. Bez tohohle formace v SHORT módu trvala 2x déle než ve FULL (uživatel
  to popsal jako "pocit, že se mi pomíchaly módy").
  `pace` se NEPOČÍTÁ jako pevná konstanta v "bodech racing_line/s": počet bodů v
  `racing_line` je jen rozlišení ručního vykreslení tratě a vůbec neodpovídá reálné
  délce okruhu (Nizozemsko má v datech 80 bodů, Austrálie 44, přestože Zandvoort je
  kratší okruh). Místo toho `get_speed()` počítá `pace = path_len /
  formation_lap_duration(track)`, kde délka formačního kola vychází z REÁLNÉ délky
  okruhu: `TRACK_LENGTH_KM[track name] / FORMATION_SPEED_KMH * 3600`.
  Reálné délky okruhů (km) jsou z Wikipedie (F1 sezóna 2025); `FORMATION_SPEED_KMH =
  120` (zdroje uvádějí formační tempo 50-120 km/h; 120 sedí s uživatelovým údajem pro
  Zandvoort 1:45-2:15 i s jeho požadavkem 2-3 min pro Austrálii). Konkrétní reálné
  časy formačního kola po okruzích nikde veřejně nejsou, proto model délka/rychlost.
  Výsledek: Monaco 1:40, Zandvoort 2:08, Austrálie 2:38, Silverstone 2:57, Spa 3:30
  atd. (všech 24 tratí ověřeno headless testem: doba = vzorec, SHORT i FULL stejně,
  0 změn pořadí). Při přidání nové tratě doplnit její délku do `TRACK_LENGTH_KM`,
  jinak se použije `FORMATION_LAP_DURATION_FALLBACK` (125 s).
  `FORMATION_GRID_GAP = 0.5` (kolik sekund později se každé další auto na roštu
  rozjede, ~9,5 s rozestup pro celé pole).
  Pořadí zůstává zachované nezávisle na těchto hodnotách (matematická vlastnost
  návrhu - uniformní rychlost + odstupňované starty), takže jde dál ladit beze strachu
  z rozbití - stačí měnit `FORMATION_SPEED_KMH`/`FORMATION_GRID_GAP`.

## Startovní semafor (po formačním kole)
Race phases jsou `FORMATION` → `START` → `RACING`. Fáze `START` je startovní semafor:
- Když první auto dojede formační kolo, `race_phase` přejde na `RACE_PHASE_START`. Auta
  během ní STOJÍ (`get_speed()` vrací 0.0) na místech, kde formační kolo skončilo.
- 5 světel se rozsvěcí po jednom (`START_LIGHT_INTERVAL` = 1 s), pak náhodná prodleva
  `START_HOLD_MIN`..`START_HOLD_MAX` (0,2-3,0 s, losuje se v `_load_race()` do
  `self.start_hold_time`), všechna světla zhasnou → `RACE_PHASE_RACING`, přehraje se
  startovní komentář (`_play_start_comment()`, dřív se přehrával hned při vstupu do START)
  a 1,5 s (`START_LIGHTS_OUT_DISPLAY`) svítí nápis "světla zhasla".
- Semafor se časuje v REÁLNÝCH sekundách (`real_delta_time` v `update()`, před
  `time_scale`), takže vypadá vždy stejně i na 20x; při pauze stojí. Stav:
  `start_lights_on`, `start_timer`, `start_hold_time`, `start_lights_out_timer`.
- Kreslení: `_draw_start_lights()` (2 řady x 5 světel, pod mapou trati, ať nezakrývá
  okruh), volané z `draw()` ve fázi START a po dobu `start_lights_out_timer`.
- Všechno, co mělo být vypnuté "před startem", se teď kontroluje jako
  `race_phase == RACE_PHASE_RACING` (ne `!= FORMATION`): incidenty/DNF, náhodný SC,
  AI rozhodování, `handle_battles()`, `update_drs()` - takže platí i pro semafor.
- Hned po zhasnutí se `START_NO_BATTLE_SECONDS` (8 s race_time) nekonají souboje
  (`handle_battles()`): auta stojí těsně za sebou (pod prahem souboje), takže by se
  pole hned první snímek náhodně přeskákalo. `self.race_start_time` = race_time zhasnutí.
- DRS je zakázané v prvních dvou kolech závodu (`DRS_FIRST_LAP = 3`), jako ve F1.
- Související opravy: (1) leaderboard počítá rozestup podle skutečné pozice na trati
  (sekundy, nebo "+N kol" až od celého kola), ne podle rozdílu `current_lap` - dřív po
  každém průjezdu lídra cílem (a hlavně na startu) svítili všichni ostatní jako "+1
  kolo". (2) `current_lap` je číslo kola, které lídr právě jede (formační kolo ho
  přepne na 1), takže konec závodu je `leader.current_lap > laps` (dřív `>=` = závod
  byl o kolo kratší, 57 místo 58), a hlavička "Kolo N/M" se ořezává na `laps`.

## Pit stopy / stinty pneumatik – opraveno (počítání i wear rate)
Dřív `ai_should_pit()` počítalo `driver.current_stint_laps += 1` při KAŽDÉM AI
rozhodovacím tiku (~každých 0.9 s), ne jednou za skutečně dojeté kolo, a navíc to
porovnávalo s `target_stint_end`, což je ABSOLUTNÍ číslo kola (`current_lap + délka
stintu` nastavené v `ai_plan_stint()`), takže šlo o srovnání dvou různých jednotek.
Opraveno:
- `driver.current_stint_laps += 1` se teď počítá centrálně v `update()` při skutečném
  dojetí kola (`if driver.track_index == 0: ...`), jednou za kolo pro všechny jezdce.
- `ai_should_pit()` porovnává OVERCUT i normální pit už správně přes
  `driver.current_lap >= driver.target_stint_end (- 3)`, ne přes `current_stint_laps`.
- Undercut logika (`ahead.current_stint_laps > 4 and driver.current_stint_laps >= 7`)
  zůstala beze změny – tam `current_stint_laps` správně slouží jako relativní "stáří
  stintu v kolech", teď už počítané korektně.

**Wear rate přeladěn:** Původní vzorec (`base_wear * tire_life_factor * 0.145 *
delta_time`) opotřebovával gumy podle UPLYNULÉHO ČASU, ne podle ujeté vzdálenosti, a
byl navíc tak silný, že MEDIUM guma dosáhla nouzového prahu `tire_wear > 0.88` už
kolem 1.-2. kola bez ohledu na plán (`ai_plan_stint()` přitom plánuje 12-25 kol) - navíc
nekonzistentně mezi tratěmi (různá délka `racing_line`) i mezi SHORT/FULL módem.
Nahrazeno novým vzorcem v `update()`:
```python
lap_fraction = (speed * delta_time) / path_len
driver.tire_wear += lap_fraction * PACE[driver.pace_mode]["wear"] * TIRE_WEAR_PER_LAP[driver.tire]
```
`speed * delta_time` je stejná hodnota, která jde do `driver.progress` (skutečně ujetá
vzdálenost tento frame), takže opotřebení je teď 1:1 svázané s ujetými koly, ne s
reálným časem – funguje stejně na všech tratích i při libovolném time_scale/
time_compression. Nová tabulka `TIRE_WEAR_PER_LAP` (u definice `TIRES`, řádek ~140) je
nakalibrovaná tak, aby guma dosáhla 100 % opotřebení cca v 1.4× průměrné plánované
délky stintu (SOFT ~13, MEDIUM ~20, HARD ~29, INTER ~11, WET ~10 kol) - normální piťování
tak řídí `target_stint_end`, a `tire_wear > 0.88` je jen nouzová pojistka pro agresivní
tempo (PUSH) nebo dlouhý overcut.
Ověřeno headless simulací: "suché" pity (mimo vynucené kvůli dešti) teď v průměru
vychází na ~9-22. kolo (odpovídá plánovaným cílům), místo dřívějšího 1.-2. kola u
každého jezdce bez rozdílu.

**Opraveno:** Počasí (`current_weather`) se dřív přehazovalo MNOHEM častěji, než mělo –
`WEATHER_CHANGE_TIME=12.0` (reroll co 18 real/race-time sekund), ale jedno kolo trvá
typicky 100-200+ race-time sekund, takže docházelo k 5-10 rerollům počasí PER KOLO a
pravděpodobnost deště hned na začátku závodu byla přes 50 %. Nahrazeno losováním podle
ODJETÝCH KOL LÍDRA (`WEATHER_CHANGE_LAPS = 4`, `self.weather_last_check_lap`) místo
podle uplynulého reálného času - viz `update()`.

## Pořadí v cíli / body do šampionátu – opraven zásadní bug
Když lídr dokončil poslední kolo, VŠICHNI zbývající jezdci se v tom samém framu
najednou označili jako `finished=True` a dostali IDENTICKÝ `driver.total_time =
self.race_time`. `finish_race()` přitom body přiděluje podle `sort(key=lambda
d: d.total_time)` - se stejným total_time u všech to znamenalo, že pořadí (a tedy i
body) ve skutečnosti odpovídalo jen tomu, v jakém pořadí byli jezdci v `self.drivers`
(pořadí týmů v `championship_data.py`), NE tomu, jak závod doopravdy dopadl!
Opraveno v bloku `# === KONEC ZÁVODU ===` v `update()`: lídr (nově správně dohledaný
přes celou poziční hodnotu `current_lap*path_len+track_index+progress`, ne jen přes
`current_lap` - jinak by remíza v počtu kol nahodile vybrala špatného lídra) dostane
`total_time = self.race_time` přesně, všichni ostatní dostanou `self.race_time +
odhadovaný_gap` dopočítaný ze skutečné finální pozice na trati (stejný `88s/kolo`
odhad, jaký už používal živý leaderboard). Ověřeno testem: pořadí podle `total_time`
teď 1:1 odpovídá pořadí podle skutečné finální pozice, body klesají s umístěním.

## Další opravené bugy (nalezeny při hloubkové revizi)
- **DRS bylo prakticky pořád zapnuté pro celé pole:** `update_drs()` počítalo mezeru
  přes `driver.distance`, který se nikde needituje (zůstává 0.0) → `gap = front.distance
  - driver.distance` bylo vždy 0 → `0 < 25` vždy pravda. Nahrazeno stejným pozičním
  vzorcem jako jinde (`current_lap*path_len+track_index+progress`, nový práh
  `DRS_GAP_THRESHOLD=3.5`). `driver.distance` (mrtvý atribut) smazán z `Driver.__init__`.
- **`handle_battles()` a `update_drs()` nevyřazovaly dojeté/DNF/pitující jezdce** - šlo
  si "spočítat souboj" nebo dokonce "předjet" zaparkované auto po nehodě, nebo souboj s
  autem v boxové uličce. Obě metody teď filtrují `not d.finished and not d.is_dnf and
  not d.in_pit`, stejně jako `update_safety_car_queue()`.
- **Fragilní poziční vzorce s natvrdo zadanými konstantami** (`current_lap*100+...` v
  `ai_should_pit()`, `current_lap*10000+track_index*100+progress*100` v leaderboardu
  během závodu) - fungovalo to jen náhodou, dokud žádná trať nemá `racing_line` delší
  než 100 bodů (nejdelší dnes je Nizozemsko s 80). Nahrazeno `path_len`-based vzorcem
  jako všude jinde (`current_lap*path_len+track_index+progress`).
- **Nastavení z probíhajícího závodu zahazovalo celý závod:** `change_screen()`
  kontrolovalo `isinstance(current_screen, ChampionshipScreen)` AŽ PO PŘEPSÁNÍ
  `current_screen` na nový `SettingsScreen()` - podmínka tak byla vždy False,
  `SettingsScreen.from_ingame` zůstávalo vždy False, a ESC ze Settings proto VŽDY
  vedlo do hlavního menu (`change_screen(GAME_STATE_MENU)`), i když hráč přišel ze
  závodu přes in-game menu (ESC → Settings). Navíc i kdyby `from_ingame` bylo True,
  `change_screen(GAME_STATE_RACE)` vždy zakládalo úplně NOVÝ `ChampionshipScreen()` -
  žádná cesta zpět k rozjetému závodu neexistovala. Opraveno: `change_screen()` si
  nejdřív zapamatuje `previous_screen` PŘED přepsáním, `SettingsScreen` dostane
  referenci na rozjetý `ChampionshipScreen` (`self.race_screen`), a `change_screen(
  GAME_STATE_RACE)` tuhle instanci obnoví (`show_ingame_menu=False, paused=False,
  state="RACE"`) místo založení nové. Ověřeno testem - `race_time`, `current_track` i
  identita objektu zůstávají po cestě Settings→ESC zachované.
- **Mrtvý/nedosažitelný kód smazán** (matoucí duplicitní/legacy zbytky z dřívější
  verze, bez vlivu na chování): modulová proměnná `buttons` + `draw_menu()` +
  `menu_options`/`selected_menu_index` (nahrazeno dávno `MenuScreen.buttons`/`draw()`),
  `award_championship_points()` + `reset_race()` (nahrazeno `finish_race()`/
  `_load_race()`), `calculate_gaps()` (nikde volané), duplicitní `elif event.key ==
  pygame.K_k:` blok (první z nich stínil druhý - `show_save_list()` se přes K nikdy
  nezavolalo, teď zavolá), dva nedosažitelné `elif self.state == "PAUSE":` bloky
  (`self.state` se do `"PAUSE"` nikde nenastavuje), a s tím související mrtvé globály
  `GAME_STATE_CHAMPIONSHIP`, `GAME_STATE_PAUSE`, `GAME_STATE_LOAD`, `pit_entry_index`,
  modulové `race_finished`/`points_awarded`/`race_time`/`font`, `barvy_pozadi`,
  `RACE_ARE_WIDTH`.

## Ostatní implementované systémy
Pneumatiky + opotřebení + AI stinty (`ai_plan_stint`, `ai_should_pit`), počasí, DRS
(`update_drs`), incidenty/DNF (`generate_incident`), formation lap s pevným pořadím +
startovací audio komentář (CS/EN), plná lokalizace CS/EN/IT, ukládání/načítání JSON +
auto-save po závodě, in-game menu (ESC), Settings (FPS, Race Length, Language).

## TODO priority
**Vysoká:** žádná otevřená (viz opravy výše).
**Střední:** doplnit chybějící překlady hardcoded textů; `WEATHER_TYPES` dict
(`wear_modifier`/`lap_modifier`) je definovaný, ale nikde se nepoužívá - CLOUD počasí
tak nemá žádný herní efekt (jen RAIN je ručně ošetřený v `get_speed()`); pokud se má
počasí reálně promítat do rychlosti/opotřebení, je potřeba to promyslet a napojit
(riziko rozladění tempa, radši nedělat bez odsouhlasení).
**Střední (k ověření s uživatelem):** `load_game()` obnoví jezdce (kola, pozice, gumy...) a hned
potom zavolá `_load_race()`, které je celé resetuje - reálně se tedy načte jen šampionát
(body, kolo sezóny) a závod začne znovu formačním kolem. Nejspíš to není záměr (uložení
během závodu ukládá i pozice), ale chování se nezměnilo - nejdřív zjistit, co uživatel chce.
**Nízká:** Practice mode (zatím prázdný); další jazyky (DE...).

## Styl práce
- Vždy nejdřív přečíst aktuální `manager.py` před úpravou (mění se často mimo session).
- Žádné hardcoded české texty v UI – vždy přes `get_text()`.
- Preferovat malé, cílené změny; uživatel často chce "nahraď tuto metodu tímto".
- Při úpravě SC upravit současně `get_speed()`, pohyb SC v `update()`,
  `update_safety_car_queue()` a `handle_battles()`.
- Při úpravě formačního kola pamatovat na VŠECHNA místa, která by mohla za formace
  změnit pozici jezdce mimo `formation_start_delay`/`formation_lap_duration()` (viz sekce výše) –
  jinak se pořadí zase rozjede.
- Po úpravách UI otestovat tok ESC → in-game menu → Settings → zpět.
- Nový asset (zvuk, obrázek, soubor) vždy načítat přes `os.path.join(SCRIPT_DIR, ...)`,
  nikdy jako holý relativní řetězec (viz sekce "Cesty k souborům" výše).
- Herní logiku (SC, formační kolo, pozice) lze ověřit i bez GUI: načíst zdroj
  `manager.py`, uříznout ho před `\nwhile True:` a `exec`-nout do vlastního namespace
  s `SDL_VIDEODRIVER=dummy` – pak jde přímo volat `ChampionshipScreen.update(dt)` v
  cyklu a kontrolovat stav. `manager.py` nejde normálně `import`-ovat (má na modulové
  úrovni `pygame.display.set_mode()` a nekonečnou `while True` smyčku).
- `git` repozitář existuje v `F1_Manager/.git` (podsložka projektu, ne kořen).
