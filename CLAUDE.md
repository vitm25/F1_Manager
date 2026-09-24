# F1 Manager 2025 – kontext pro AI

Jazyk komunikace s uživatelem: **čeština**.

## Přehled
Pygame F1 Manager simulace sezóny 2025. Hráč vybere tým, řídí strategii (pneumatiky,
boxy) a sleduje závody v reálném čase se zrychlením času. Kód je z velké části
monolitický v `manager.py`.

## Okno a škálování na libovolný displej
Celá hra se kreslí na pevné logické plátno `canvas` (= `screen`) `WIDTH x HEIGHT` =
1920x1080 - všechny souřadnice v UI jsou pro něj a NEMĚNÍ se. Do okna se plátno každý
snímek přeškáluje v `present_frame()` (smoothscale, zachovaný poměr 16:9, černé okraje
= letterbox, např. na 2560x1600 vznikne pruh nahoře a dole).
- Okno: `apply_display_mode()` - v okně `fit_window_size()` (největší 16:9, které se vejde
  na plochu i s titulkem a hlavním panelem, `pygame.RESIZABLE` = jde ručně zvětšovat),
  na celou obrazovku nativní rozlišení desktopu. Přepínání: tlačítko v Nastavení i
  klávesa F11 (`toggle_fullscreen()`).
- **Myš:** VŽDY `get_mouse_pos()` (přepočet okno -> logické souřadnice), nikdy
  `pygame.mouse.get_pos()` přímo, jinak by klikání na jiném než 1920x1080 míjelo tlačítka.
- Windows: před `pygame.init()` se volá `SetProcessDPIAware()`, aby hra na displeji se
  zvětšením 125-150 % (typicky notebook 2560x1600) dostala skutečné pixely a nebyla
  OS-rozmazaná.
- Nastavení FPS teď opravdu funguje: hlavní smyčka používá `CURRENT_FPS` (dřív
  natvrdo konstantu `FPS = 60`, kterou Nastavení nemělo jak změnit).
- Ověřeno headless (dummy driver): velikost okna pro 1366x768 až 3840x2160, letterbox,
  mapování myši tam a zpět. NEověřeno na skutečném displeji (DPI awareness, F11 na
  reálné obrazovce) - stojí za to zkusit ručně.

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

## Audio (složka `sounds/`)
- `start_cz.mp3` / `start_en.mp3` - startovní komentář při zhasnutí světel.
- **Zvuk výhry týmu hráče:** `win_cz.mp3` (čeština), `win_en.mp3` (ostatní jazyky), případně
  jediné společné `win.mp3` (záloha, když chybí soubor pro daný jazyk). Soubory zatím v
  repozitáři nejsou - uživatel je doplní; bez nich se nic nepřehraje a hra jede dál.
  Přehraje se v `finish_race()`, když `finished_drivers[0].team_name == player_team.name`
  (vítěz závodu = jezdec hráčova týmu), zastaví se v `leave_results()` (Další závod).
- **Strange sound:** vlastní zvuk `sounds/strange.mp3` (doplní uživatel), zapíná se v
  Nastavení přepínačem "STRANGE SOUND" (globál `STRANGE_SOUND_ENABLED`, výchozí VYP, po
  restartu hry se nepamatuje). Když je zapnutý, přehraje se **místo** běžného zvuku výhry
  (mixer.music umí jen jeden stream) při: výhře závodu jezdcem hráčova týmu, a po
  posledním závodě sezóny (`current_race_index + 1 == len(CALENDAR_2025)`) při titulu
  konstruktérů nebo jezdců hráčova týmu (`_player_won_championship()`, volá se z
  `finish_race()`). Chybí-li `strange.mp3`, u výhry závodu se použije běžný zvuk výhry.
- **Formát souborů:** pygame čte jen SKUTEČNÉ mp3/wav/ogg. Soubor z telefonu/editoru, který je
  ve skutečnosti MP4/M4A (AAC) jen přejmenovaný na `.mp3`, skončí chybou "Unrecognized audio
  format" (konzole to pozná a napíše důvod, viz `audio_problem_hint`). Tak to bylo u `radio_open`
  a `strange` - vedle originálů proto leží převedené `radio_open.wav` a `strange.wav`; loader
  (`load_sfx_named`, `find_sound_files`) zkouší přípony mp3 -> wav -> ogg a nečitelný soubor
  přeskočí. Originály se nikdy nepřepisují. Složka `sound kopie/` je záloha od uživatele -
  hra ji nepoužívá a testy do ní ani do `sounds/` nesmí zapisovat.
- Přehrávání jde přes `play_first_existing_sound(paths, label)` (bere první existující
  soubor, chyby audia jen vypíše - kvůli PC bez zvuku), `stop_sound()`; použité i pro start
  komentář. Cesty vždy přes `SCRIPT_DIR`.

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

## Souboje o pozici (`handle_battles`) – šance přepočtená na reálnou sekundu
Uživatel: "jak ty auta jezdí, přijde mi to hektické". Příčina: `attack_chance` byla
konstanta NA SNÍMEK (`0.065 * overtake_skill`, s DRS `*2.4`), vyhodnocovaná v `update()`
každý reálný frame bez ohledu na FPS (Nastavení nabízí 30-240) nebo `time_scale`
(1/2/4/20x). Při 60 FPS to dávalo ~98% šanci na "předjetí" (okamžitý teleport pozice)
do JEDNÉ SEKUNDY od chvíle, co se dvě auta dostala do gapu < 2,2 bodu - a bez cooldownu
mohla stejná dvojice hned zase přehazovat pozice tam a zpátky. Čím vyšší FPS/time_scale
uživatel zvolil, tím častěji se `handle_battles()` volalo za stejný race-čas → tím
"hektičtější" to bylo (viz i jinde v kódu opakovaný vzorec: cokoliv frame-rate-závislého
= bug, srov. tire wear/weather, které jsou naopak správně škálované na `delta_time`).

Oprava (`OVERTAKE_RATE_PER_SEC`, `OVERTAKE_COOLDOWN`, `Driver.battle_cooldown`):
- `handle_battles(self, delta_time)` teď dostává `delta_time` (volá se
  `self.handle_battles(delta_time)` z `update()`, stejná hodnota jako pro pohyb aut - už
  po vynásobení `time_scale`).
- `OVERTAKE_RATE_PER_SEC = 0.22` je pravděpodobnost ÚSPĚCHU ZA REÁLNOU RACE-SEKUNDU (ne za
  frame), škálovaná stejně jako dřív `* overtake_skill` (0,8-1,2) a při DRS `* 2.4`.
  Převod na pravděpodobnost PRO TENTO KONKRÉTNÍ FRAME je `1 - (1 - rate_per_sec) **
  delta_time` (složené úročení, ne lineární `rate*delta_time` - správně funguje i při
  velkém `delta_time`, např. `time_scale=20`, kde by lineární aproximace mohla přestřelit
  přes 1.0). Výsledek: frekvence předjíždění je teď stejná bez ohledu na FPS/time_scale
  (ověřeno headless testem - kontrolovaná dvojice aut v gapu 1.0 dala prakticky identický
  počet předjetí za 20 race-sekund při 30/60/144/240 FPS i při `time_scale` 1-20).
- Po ÚSPĚŠNÉM předjetí dostanou OBA jezdci `battle_cooldown = OVERTAKE_COOLDOWN` (3 s),
  který se každý frame odečítá o `delta_time`; dokud je kladný, pár se vůbec nevyhodnocuje.
  Zabraňuje to okamžitému "vrácení" pozice v příštím framu (typický zdroj blikání).
  Neúspěšný pokus cooldown nedostává - u správně škálované pravděpodobnosti to není
  potřeba (na rozdíl od staré verze, kde by to bylo nutné, aby to vůbec šlo zkrotit).
- Práh gapu (2,2 bodu racing_line) a podmínka `behind_speed > front_speed * 0.94`
  zůstaly beze změny - o TOM, jestli je souboj vůbec kandidátem, se nic neměnilo, jen o
  tom, jak ČASTO a jak NEZÁVISLE NA FPS se vyhodnocuje.
- Ladění: `OVERTAKE_RATE_PER_SEC` výš = agresivnější/rychlejší předjíždění, níž = klidnější
  pole. `OVERTAKE_COOLDOWN` výš = souboje se táhnou déle (méně "yo-yo" efektu).

## Tempo jezdců, VSC, incidenty (opraveno při revizi kódu)
- **Tempo podle jezdce:** dřív se `DRIVER_BASE_TIMES`/`base_lap_time` nikde nepoužívalo a
  rychlost dávalo jen náhodné `base_speed` 0,95-1,05 (Williams mohl celou sezónu porážet
  McLaren). Teď `base_speed = driver_base_speed(base_lap_time)` = `1 + DRIVER_PACE_WEIGHT *
  (DRIVER_REFERENCE_LAP_TIME - čas) / DRIVER_REFERENCE_LAP_TIME` (ref. 1,85, váha 0,6 → pole
  v ~3,6 %) a navíc `driver.race_form` = náhodná forma ±`RACE_FORM_SPREAD` (1 %) losovaná v
  `_load_race()`. `racing_speed()` násobí `base_speed * race_form`. Headless: Spearmanova
  korelace pořadí v cíli s tempem ~0,45 (zbytek = náhodný rošt, strategie, souboje; vyšší
  váha korelaci nezvedne). Až bude kvalifikace, korelace poroste.
- **VSC** dřív bylo jen nápisem. Teď: `get_speed()` pod VSC (mimo pit lane) vrací
  `min(VSC_PACE, racing_speed)` - celé pole stejné tempo (0,65), rozestupy zamrznou;
  `handle_battles()` i `update_drs()` se vrací. Délka VSC je v kolech (`VSC_MIN_LAPS`..
  `VSC_MAX_LAPS` × `lap_race_seconds()`), ne pevné sekundy. VSC se nevyhlásí, když jede SC,
  a `deploy_safety_car()` běžící VSC ukončí.
- **Žlutá vlajka:** zakazuje souboje a DRS (globálně, sektory hra nemá).
- **Incidenty a náhodný SC nezávislé na FPS:** dřív `random() < 0.012` za SNÍMEK na jezdce a
  `random() < 0.001` za snímek pro SC → počet nehod závisel na FPS/time_scale (stejný typ bugu
  jako dřív předjíždění). Teď jsou pravděpodobnosti ZA KOLO (`INCIDENT_SPIN_PER_LAP`,
  `INCIDENT_DNF_PER_LAP`, `RANDOM_SC_PER_LAP`) převedené přes `chance_in(rate, frame_laps)`
  (`1-(1-rate)**amount`), kde `frame_laps = delta_time / lap_race_seconds()`.
  `incident_cooldown` je v kolech. Náhodný SC nejde v prvních `START_NO_BATTLE_SECONDS` po
  startu. Headless (16 závodů, 30 i 120 FPS, 20x): ~3,5 spinu, ~1,6 DNF a ~1 SC/VSC na závod,
  v obou nastaveních stejně.
- **Předjetí přes cílovou čáru už nebere kolo:** `handle_battles()` dřív kopírovalo jen
  `track_index`, takže jezdec těsně před čárou předjel auto za čárou a zůstal mu starý
  `current_lap` (= ztratil celé kolo). Teď `_place_driver(driver, pozice, path_len)` nastaví
  celou pozici včetně kola (a započítá kolo do `current_stint_laps`/`total_time`).
- Ladění: `DRIVER_PACE_WEIGHT` (vliv jezdce), `VSC_PACE`, `INCIDENT_*_PER_LAP`,
  `RANDOM_SC_PER_LAP`. Simulační skript: viz "Styl práce" (exec bez `while True`).

## Safety Car – opraveno (seřazování do vláčku funguje)
Stav: `safety_car_active`, `safety_car_timer`, `safety_car_index`, `safety_car_progress`,
`safety_car_laps` (kumulativní počet průjezdů SC, aby šla pozice SC srovnávat s pozicí
jezdců stejně jako `current_lap*path_len+track_index+progress`), `safety_car_lined_up`
(True, jakmile je celé pole seřazené v těsném vláčku).

Jak to funguje:
- `deploy_safety_car(min_duration, max_duration)` SC jen vyhlásí: SC "čeká v boxové uličce"
  u výjezdu (viz životní cyklus níže) a nastaví náhodný timer (= nejkratší doba SC na trati).
- `update_safety_car_queue()` (volaná každý frame, dokud je SC aktivní) spočítá pro
  každého jezdce cílový slot ve frontě za SC (`sc_pos - SAFETY_CAR_LEADER_GAP - i*SAFETY_CAR_CAR_GAP`
  podle aktuálního pořadí) a rychlost dohánění úměrnou velikosti mezery
  (`SAFETY_CAR_MAX_CATCHUP_TIME` = i auto ztracené o celé kolo dožene frontu nejpozději
  za tuto dobu). Uloží výsledky do `self._sc_speed_overrides`.
- `get_speed()` při aktivním SC (a jezdec není v pit lane) vrací
  `min(race.get_safety_car_speed(driver), racing_speed(driver, race))` - dohánějící /
  odlapující se auto tedy nikdy nejede rychleji než při normálním závodním tempu.
- `handle_battles()` při aktivním SC rovnou vrací (žádné předjíždění).
- SC končí až když je `safety_car_timer<=0` **A** `safety_car_lined_up` **A** nikdo není
  lapovaný (`_lapped_cars()` = aktivní auta o ≥ 1 kolo za lídrem) – ne jen podle časovače.
  DNF auta se nepočítají. V praxi trvá SC 1-2 kola SC tempem (odlapování ~1-2 min
  race-času podle tratě), což odpovídá reálným 3-6 kolům pod SC.
- **Důležité:** pokud během SC nastane další incident, NESMÍ se znovu volat
  `deploy_safety_car()` (to by resetovalo pozici SC i `lined_up` a fronta by se nikdy
  nedoseřadila) – místo toho se jen prodlouží `safety_car_timer`. Viz
  `generate_incident()`.
- **Životní cyklus** `safety_car_phase` (řeší `_update_safety_car()`, vždy přes boxovou uličku):
  `WAITING` (SC stojí v uličce před výjezdem - `deploy_safety_car` ho zaparkuje o
  `SAFETY_CAR_EXIT_RUN` před koncem uličky, na nejbližším výjezdu PŘED lídrem; celé pole jede
  do té doby stejným tempem `SAFETY_CAR_WAIT_SPEED`, aby se nezměnily rozestupy) ->
  `LEADING` (lídr je do `SAFETY_CAR_JOIN_DISTANCE` bodů od výjezdu: SC vyjede na trať, pole
  se řadí a odlapuje; `safety_car_in_lane` = vykreslený v uličce, dokud nepřejede výjezd) ->
  `ENDING` (podmínky konce splněné; SC dál jede po trati až k vjezdu do boxů; nová nehoda =
  prodloužený timer vrátí fázi na LEADING) -> `PITTING` (SC zatočil do uličky - TEĎ se pole
  uvolní, `safety_car_active=False`; SC dojede uličkou, `safety_car_lane_d`) -> `NONE`.
  `safety_car_active` je True ve fázích WAITING/LEADING/ENDING, SC je vidět i v PITTING.
  Vykreslení používá `pit_lane_position()` v uličce, jinak souřadnice racing_line. Pod SC se
  ukazuje popisek fáze / počet odlapovaných aut a DRS je vypnuté (`update_drs`).
- SC se také nesmí spouštět (ani z `generate_incident()`, ani z náhodného triggeru v
  `update()`) během `RACE_PHASE_FORMATION` – obojí je ošetřené podmínkou
  `self.race_phase != RACE_PHASE_FORMATION`.

## Formační kolo – pevné pořadí podle roštu
Uživatel chtěl, aby se auta na formačním kole neproháněla/nepředjížděla, ale zůstala
přesně v pořadí, v jakém vyjela (P1 zůstane P1, P2 zůstane P2 atd.), stejně jako ve
skutečné F1.

Implementace (`Driver.grid_position`, `Driver.formation_start_delay`, konstanty
`FORMATION_SPEED_KMH`, `TRACK_LENGTH_KM` a `FORMATION_GRID_GAP` u `get_speed()`):
- V `_load_race()` se po resetu jezdců vytvoří kopie `self.drivers`, ta se
  **náhodně zamíchá** (`random.shuffle` - DOČASNÉ řešení, dokud nebude kvalifikace, viz
  TODO) a v tomhle pořadí se přiřadí `grid_position = i` a `formation_start_delay =
  i * FORMATION_GRID_GAP` (v sekundách `race_time`). `self.drivers` samotné se
  nepřehazuje - nic jiného v kódu se jeho pořadím neřídí, o roštu rozhoduje jen
  `grid_position`/`formation_start_delay`. Až bude kvalifikace, stačí tu nahradit
  `random.shuffle` výsledkem kvalifikace (seřadit `grid_order` podle kvalifikačního času).
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
- **Dva jemné bugy odhalené až po zavedení náhodného roštu** (dokud `self.drivers` pořadí
  == pořadí na roštu, byly neviditelné - teď už na sobě nezávisí, viz "Startovní rošt"):
  1. `get_speed()` u FORMATION dřív binárně přepínala 0/plné tempo podle toho, jestli
     `race.race_time` (konec framu) přesáhl `formation_start_delay` - při vyšším `time_scale`
     (kdy 1 frame > `FORMATION_GRID_GAP` 0,5 s) se tak víc aut se sousedními starty
     "odemklo" ve stejném framu a dostala identickou pozici (nedeterministické pořadí mezi
     nimi navždy poté). Oprava: `get_speed(driver, race, delta_time)` teď počítá `active_dt`
     - přesně tu část framu, po kterou auto už mělo jet (lineární interpolace mezi
     předchozím a aktuálním `race.race_time`), takže i menší časový náskok než jeden frame
     se projeví jako menší (ne nulový/plný) posun. Volání mimo hlavní smyčku
     (`handle_battles`) `delta_time` nepředávají - tam formace stejně nikdy neběží.
  2. Přechod `RACE_PHASE_FORMATION -> RACE_PHASE_START` (lídr dojel kolo 1) se dřív
     vyhodnocoval uvnitř cyklu `for driver in self.drivers`, u KTERÉHOKOLIV jezdce, kdo
     zrovna dojel svoje kolo - u lídra to vyjde chronologicky první, ale když byl lídr ve
     `self.drivers` zpracovaný uprostřed seznamu, auta zpracovaná před ním v tomtéž framu
     ještě dostala celý frame formačního tempa navíc, zatímco auta po něm už žádný (fáze
     už byla START) - u dvou sousedních aut na roštu to v posledním framu formace uměle
     otočilo pořadí. Oprava: dokud `race_phase == RACE_PHASE_FORMATION`, cyklus jede v
     pořadí `sorted(self.drivers, key=lambda d: d.grid_position)` (lídr vždy zpracovaný
     první), mimo formaci beze změny (`self.drivers` napřímo, kvůli výkonu).
  Ověřeno headless testem na všech 24 tratích, SHORT i FULL, `time_scale` 1/2/4/20: 0 porušení
  pořadí (dřív při náhodném roštu a `time_scale=20` běžně několik desítek za závod).

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

## Pit stopy (skutečný průjezd boxovou uličkou)
Dřív se pit stop simuloval tak, že auto po žádosti hned na místě "zamrzlo" na 5 s a pak
se přeskočilo o 8 bodů dopředu (zisk pozice, ne ztráta). Teď:
- **Stavy** (`Driver.pit_phase`, plus `in_pit`/`on_pit_lane` = True po celou dobu):
  žádost (`pit_requested`, hráč tlačítkem BOX / AI přes `ai_should_pit`) → auto jede dál
  po trati, až dojede k vjezdu do uličky (`d < PIT_ENTRY_WINDOW`) → `"ENTRY"` (jede
  uličkou pit limiterem = `get_speed` × 0.4) → dojede k boxu SVÉHO týmu → `"SERVICE"`
  (`get_speed` vrací 0, stojí `PIT_TIME / time_compression`; potom výměna gum,
  `current_stint_laps = 0`, AI přeplánuje stint) → `"EXIT"` → na konci uličky zpět na trať.
  Logika je v `ChampionshipScreen._update_pit()`, volá se z hlavní smyčky v `update()`.
- Virtuální pozice auta (`track_index`/`progress`) se nikdy nepřeskakuje - ulička je jen
  "interval bodů racing_line od vjezdu o `length` bodů", takže řazení, počítání kol
  (i přejezd cílové čáry v uličce) a Safety Car fungují beze změny. Auto v uličce je
  vyřazené z `handle_battles`/`update_drs`/fronty za SC (`in_pit`).
- **Geometrie:** `get_pit_geometry(track)` (vjezd, délka v bodech z `PIT_LANE_LENGTH_M`
  a reálné délky okruhu, strana) a `pit_lane_position()` (souřadnice na mapě = bod
  racing_line + boční odsazení `PIT_LANE_OFFSET_PX` s plynulým odklonem/návratem).
  Ulička se ODVOZUJE z `racing_line`; ručně nakreslená `pit_lane` v `tracks_data.py` je
  u ~třetiny tratí stovky pixelů vedle racing_line (nenavazuje), proto slouží jen jako
  nápověda pro místo vjezdu a stranu (a jen když sedí do 45 px). Boxy týmů = malé barevné
  čtverečky v uličce (`pit_box_distance`), druhý jezdec týmu stojí o kousek dřív.
- Ztráta času (změřeno na všech 24 tratích, SHORT i FULL shodně): ~21-39 % kola v
  uličce vč. zastávky, čistá ztráta ~20-27 % kola - blízko realitě (20-25 s z ~80 s).
- UI: tlačítko BOX u hráčových jezdců je červené (klid) / žluté (pit požadován, čeká na
  vjezd) / zelené (v uličce). Opětovné zadání pitu během průjezdu uličkou se ignoruje.

## Panel pit stopu ("Boxová zeď") + rádio
- Tlačítko BOX u hráčova jezdce **neobjednává pit rovnou**, otevře panel `_draw_pit_panel()`
  (stav `pit_panel_open`; dřívější malý výběr gum `show_tire_select` je pryč). Panel jde
  otevřít jen ve fázi `RACING` a jen jezdci, který jede (ne `in_pit`/DNF/v cíli). Je v něm:
  záložky obou jezdců, aktuální guma + opotřebení + kol na sadě, zbývající kola, počasí,
  5 karet gum (výdrž `~1/TIRE_WEAR_PER_LAP` kol, přilnavost `tire_grip()` při aktuální
  vlhkosti, štítek DOPORUČENO z `recommended_tire()`), tlačítka **BOX THIS LAP** (objedná pit
  na vybrané gumy: `next_tire` + `pit_requested`) a **STAY OUT** (zruší objednaný pit); X /
  ESC panel jen zavře beze změny. Předvybraná guma = doporučená, u už objednaného pitu ta objednaná.
- **Závod je při otevřeném panelu pozastavený**: `update()` se vrací při `pit_panel_open`
  (nepoužívá `self.paused`, takže nekoliduje s PAUSE/ESC menu); `handle_events()` posílá
  panelu veškerý vstup (`continue`). Na pozadí běží jen `_update_radio()` (reálný čas).
- **Rádio** (`_start_radio`, `_update_radio`, `_draw_radio`): po *nově* objednaném pitu
  (změna gum u už objednaného pitu rádio nespouští) se ukáže pruh "RÁDIO | jezdec | "BOX, BOX""
  přes horní okraj mapy a zahraje se: úvod (globál `RADIO_INTRO_MODE` = `BEEP` /
  `STRANGE` / `OFF`, cyklí se tlačítkem "ÚVOD RÁDIA" v Nastavení, po restartu se
  nepamatuje) + po `RADIO_INTRO_GAP` náhodně jedna z `RADIO_VOICE_LINES`
  ("Box, box" / "Box this lap"). Úvod delší než `RADIO_INTRO_MAX_WAIT` (3 s) hlášku nezdrží.
- Soubory v `sounds/` (mp3/wav/ogg, hledá `find_sound_file(name)`): `radio_open`,
  `box_box`, `box_this_lap`, u úvodu STRANGE `strange`. Chybějící soubor se přeskočí (a vypíše
  varování do konzole), titulek se ukáže vždy. Hláška se losuje jen z těch, které mají soubor -
  jinak by při jediné nahrávce půlka pit stopů proběhla potichu. Krátké zvuky jdou přes `pygame.mixer.Sound` (`load_sfx`, cache), takže
  nepřeruší komentář / zvuk výhry přes `mixer.music`.
- **Tempo směsí**: `TIRES[...]["speed"]` (SOFT 1.010, MEDIUM 1.000, HARD 0.990, INTER 0.985,
  WET 0.975) násobí rychlost v `racing_speed()` (= základ auta × opotřebení × tempo směsi ×
  přilnavost). Rozdíl SOFT-HARD 2 % je vyvážený ztrátou času na dalších zastávkách (SOFT stint ~9.5
  kola, ztráta ~25 % kola za pit; celkový čas SOFT/MEDIUM/HARD vychází v rozmezí ~0.4 %),
  žádná směs tedy není jednoznačně nejlepší. Panel ukazuje na kartě gumy Tempo / Výdrž / Přilnavost.

## Počasí a vlhkost trati (`WEATHER_TYPES` nahrazeno)
- Počasí `SUN`/`CLOUD`/`RAIN` se každé `WEATHER_CHANGE_LAPS` (4) kola lídra mění podle
  `WEATHER_TRANSITIONS` (Markovův řetězec: déšť nepřijde z čistého nebe, SUN→CLOUD→RAIN).
  Ladění: ~39 % závodů má někdy déšť, ~6 % času prší (původní nezávislý los 65/23/12 dával
  80 % závodů s deštěm). Start je vždy SUN.
- **Vlhkost trati** `track_wetness` (0-1): v dešti stoupá (celá trať promokne za
  `WETTING_LAPS` = 3 kola), jinak schne (`DRYING_LAPS`: SUN 5 kol, CLOUD 9 kol) - počítá se
  v "kolech" (`path_len / time_compression`), takže je stejné na všech tratích i v SHORT/FULL.
  Ukládá se do savu (`track_wetness`).
- **Tempo:** `get_speed()` násobí `tire_grip(tire, wetness)` - parabola kolem optimální
  vlhkosti gumy (slick 0, inter 0,5, wet 1; profily v `TIRE_GRIP_PROFILE`). Slick při
  vlhkosti 0,5 ztrácí 15 %, při 1,0 přes 55 %; inter na suchu ~10 %, wet na suchu ~28 %.
  Nahrazuje původní ručně natvrdo zadané `SOFT*0.85 / INTER*1.05` v dešti.
- **Opotřebení:** inter/wet na sušší trati se ničí až 2-3,5x rychleji
  (`tire_wear_weather_factor`), slicky beze změny.
- **AI přezouvání** (`ai_should_pit`, `ai_choose_tire`) podle vlhkosti + osobní
  `driver.weather_bias` (každý reaguje v trochu jiný okamžik, ne všichni naráz): slick→inter
  od `AI_INTER_WETNESS` 0,30, inter→wet od 0,78, wet→inter pod 0,50, inter→slick pod 0,15 (a
  nesprchává). Mezi "nahoru" a "dolů" je záměrně mezera (hystereze), aby se auta nepřezouvala
  sem a tam. Přezutí kvůli počasí se řeší i hned po poslední zastávce (obchází 6kolové
  pravidlo). `ai_choose_tire`/`ai_choose_pace` teď berou `race`/vlhkost, ne řetězec počasí.
- **Bezpečnost:** `generate_incident` má riziko `1 + 1,5*wetness` (+2,5 při slicku s
  přilnavostí < 0,8); náhodný Safety Car je také častější na mokru. DRS je zakázané při
  `wetness >= DRS_MAX_WETNESS` (0,25).
- **Zobrazení:** hlavička ukazuje počasí (lokalizované `WEATHER_*`) a "Vlhkost trati: N %";
  přes mapu se ztmavením podle vlhkosti/oblačnosti a padající déšť při `RAIN`.
- Vedlejší: nápisy Safety Car / VSC / žlutá vlajka (`FLAG_*`) jsou lokalizované a bez
  emoji (v herním fontu se kreslily jako čtverečky) a už nepřekrývají "Championship
  standings".

## Testovací režim (dočasný, v Nastavení)
Slouží k ručnímu zkoušení nových věcí bez odjetí celého závodu. V Nastavení tlačítko
ZAP/VYP a volba počtu kol (`TEST_MODE_LAP_OPTIONS` = 3 / 5 / 10, výchozí `TEST_MODE_LAPS` = 5;
kliknutí na počet kol režim rovnou zapne).
- Globály `TEST_MODE` / `TEST_MODE_LAPS` (u `CURRENT_RACE_MODE`); platí od DALŠÍHO načtení
  závodu (`_load_race()`), ne pro už rozjetý. Nastavení se neukládá na disk.
- `_load_race()` bere počet kol z `ORIGINAL_TRACK_LAPS` (kopie z `tracks_data` pořízená při
  importu), NE z `current_track["laps"]` - to se přepisuje a jinak by po vypnutí režimu
  zůstala trať trvale zkrácená.
- Během závodu svítí v hlavičce oranžový štítek "TESTOVACÍ REŽIM" u čísla kola.
- Tip: formační kolo trvá ~2 min i v testu (je časované reálně); pro rychlé zkoušení použít
  rychlost 20x.
- **Až nebude potřeba, smazat:** blok `TEST_MODE*` u `CURRENT_RACE_MODE`, `ORIGINAL_TRACK_LAPS`
  + jeho použití v `_load_race()`, tlačítka v `SettingsScreen` (`test_mode_rect`,
  `test_lap_buttons`), štítek v hlavičce a klíče `TEST MODE*`/`ON`/`OFF` v `TEXTS`.
- Vedlejší oprava: tlačítko Celá obrazovka v Nastavení dřív neexistovalo (`fullscreen_rect`
  zůstávalo `None`, přepínalo jen F11) - teď se kreslí ("ZOBRAZENÍ").

## Výsledkové okno po závodě
Po skončení závodu (`race_finished`) `draw()` místo běžného závodního UI kreslí
`_draw_results_screen()` (celá obrazovka) - nahradilo malé okénko "ZÁVOD SKONČIL", podium v
záhlaví a finální leaderboard vlevo (to všechno je smazané).
- Vpravo nahoře tlačítko "DALŠÍ ZÁVOD" (`NEXT RACE`), Enter dělá totéž (`leave_results()`).
  Po POSLEDNÍM závodě sezóny je místo něj "NÁVRAT DO MENU" a v podtitulku "KONEC SEZÓNY".
  Okno polkne veškeré kliky (pit tlačítka pod ním nesmí reagovat) - viz `handle_events`.
- Tři okna vedle sebe (`_draw_results_panel`): **Race finish** (pořadí v cíli: čas vítěze,
  odstup `+X.Xs` nebo `+N kol` od 88 s, body `+25`, DNF s důvodem), **Driver standings**
  a **Team standings** (body celkem, `+body` za tento závod, změna pozice). Řádky týmu
  hráče jsou zvýrazněné. Data skládá `_results_data()`.
- **Změna pozice** (`moves()`): rank = kolik položek má aspoň tolik bodů (shoda = nejhůř);
  kdo před závodem nemá body, do pořadí ještě nepatřil a změna se u něj neukazuje (jinak by
  se po 1. závodě objevovaly nesmyslné "-10"). Zelené +N / červené -N / šedé =.
- Všechny texty přes `get_text()` (CS/EN/IT): `RACE FINISH`, `DRIVER STANDINGS`, `TEAM
  STANDINGS`, `NEXT RACE`, `RACE FINISHED`, `SEASON OVER`, `ROUND`, `PTS`, `LAP`/`LAPS` a
  důvody DNF (`Engine`, `Crash`, ...). Stejné klíče se použily i pro pravý panel během
  závodu (dřív natvrdo anglicky) a živý leaderboard ("kolo/kol" -> `LAP`/`LAPS`).
- Opravená chyba: `driver.race_points` zůstávalo ze starého závodu (přiřazovalo se jen
  jezdcům v bodech). Teď se nuluje v `finish_race()` i `_load_race()`.

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
  `update_drs()` vypíná DRS před startem, pod SC, pod VSC i při žluté vlajce (viz sekce
  "Tempo jezdců, VSC, incidenty").
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
**Plánováno uživatelem:** kvalifikace - až bude hotová, nahradí `random.shuffle` startovního
roštu (viz "Formační kolo") a bude rozhodovat o `grid_position`/`formation_start_delay`.
**Střední:** doplnit chybějící překlady hardcoded textů (např. "ULOŽENÉ HRY"); pit stopy: double-stack (oba jezdci týmu se dvěma auty v boxu naráz
nečekají na sebe), v uličce se nekontroluje kolize aut; počasí: bez předpovědi.
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
