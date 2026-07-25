import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timezone, timedelta
from io import BytesIO
import requests

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False


# =========================
# CONFIG
# =========================
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
UNITS = "metric"
LANG = "en"
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"


#functii ajutatoare

#defineste o functie care primeste un dictionar, chei si are o valoare de rezerva daca nu exista
#folosita pt a extrage o valoare dintr un dictionar, fara sa dea eroare daca lipseste ceva
def safe(d, *keys, default=None):
    current = d #variabila care incepe cu dictionarul initial
    for k in keys: #parcurc fiecare cheie din keys
        if not isinstance(current, dict) or k not in current: #daca variabia curenta nu mai e in dictionar
            #sau daca cheia nu exista in dictionar
            return default #se returneaza default si se opreste metoda
        current = current[k] #variabila curenta devine valoare asociata cheii k
    return current

#functie folosita pt a rotunjii temperatura
def tmpRotunjire(x):
    return f"{round(x)}°C" if x is not None else "—"

#functie folosita pt a convertii de la m/s la km/s
def conversie_ms_la_kms(ms: float) -> float:
    return ms * 3.6

#functie care primeste un offset in secunde si returneaa un obiect datetime
def local_time_from_offset(offset_seconds: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)

#functie care primeste un string cu data si ora, il transforma in datetime si il marcheaza in utc
def parse_dt_utc(dt_txt: str) -> datetime:
    return datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

#functie care returneaza un string "mai frumos" pt afisarea orei
def afisareOraPretty(dt_local: datetime) -> str:
    try:
        return dt_local.strftime("%I %p").lstrip("0").lower()
    except Exception:
        return dt_local.strftime("%H:%M")

#functie care returneaza ziua saptamanii sub forma scurta
def ziuaPresc(d: datetime) -> str:
    # ex: Mon, Tue
    return d.strftime("%a")

#functie care primeste o lista de elemente, fiecare element reprezinta o prognoza din 3 in 3 ore
#returneaaz iconita cea mai frecventa dintre ele (icon dominant)
def dominant_icon(items):
    counts = {}
    for it in items:
        w0 = (it.get("weather") or [{}])[0]
        ic = w0.get("icon", "")
        if ic:
            counts[ic] = counts.get(ic, 0) + 1
    if not counts:
        return ""
    return max(counts, key=counts.get)

#functie care ia prognoza din 3 in 3 ore si o transforma in zile, facand min si maximul
def aggregate_daily(forecast: dict, tz_offset: int, days=7):
    pts = forecast.get("list") or []
    by_date = {} #dictionar pt gruparea pe zile

    for it in pts: #parcurgere interval de 3 ore
        dt_txt = it.get("dt_txt")
        if not dt_txt:
            continue
        dt_local = (parse_dt_utc(dt_txt) + timedelta(seconds=tz_offset)).replace(tzinfo=None)
        key = dt_local.date()
        by_date.setdefault(key, []).append(it)

    out = []
    for day in sorted(by_date.keys())[:days]:
        items = by_date[day]
        temps = [safe(x, "main", "temp") for x in items if safe(x, "main", "temp") is not None]
        tmin = min(temps) if temps else None
        tmax = max(temps) if temps else None
        icon = dominant_icon(items)
        # include a representative datetime for labels
        out.append({
            "date": day,
            "tmin": tmin,
            "tmax": tmax,
            "icon": icon,
        })
    return out


class WeatherClean(tk.Tk):
    def __init__(self):
        super().__init__() #constructorul clasei
        self.title("Weather") #titlul ferestrei principale - fara ea nu avem root
        self.geometry("520x860") #dimensiunea implicita a ferestrei
        self.minsize(480, 780) #fereastra nu poate fi mai mica decat dimensiunea asta

        # culori
        self.BG = "#FFFFFF" #culoare fundal
        self.CARD = "#F7FBFF" #culoare pt current card (vremea curenta)
        self.CARD2 = "#FFFFFF" #folosit la zonele de statistici, zile, ore
        self.LINE = "#E6EEF7" #culoare pentru linii
        self.TEXT = "#2B2F38" #culoare pentru textul principal
        self.MUTED = "#7B8794" #culoare pt textul secundar
        self.ACCENT = "#3B82F6" #culoare pentru accent (butoane, valori) etc

        self.configure(bg=self.BG) #setez fundalul ferestrei ca fiind self.BG

        # sesiun HTTP reutilizabila, mai rapida si mai eficienta pt requesturi (forecast, iconite etc)
        self.session = requests.Session()
        self.icon_cache = {} #dictionar unde salvez iconitele descarcate si convertite in PhotoImage

        # imagini
        self.icon_main = None #referinta iconita de vreme mare
        self.hourly_icons_refs = [] #lista pt referintele la iconitele din zona de ora
        self.daily_icons_refs = [] #lista pt referintele la iconitele din zona zile

        self._build_ui() #se apeleaza metoda care construieste toate componentele din UI

    # metoda de construire a interfetei
    def _build_ui(self):
        #se creeaza un frame numit root in interiorul ferestrei principale, i se pune fundal alb
        root = tk.Frame(self, bg=self.BG) #containerul principal
        root.pack(fill="both", expand=True, padx=16, pady=16) #se intinde pe latime si inaltime, ocupa spatiu liber, padding

        # bara de cautare
        top = tk.Frame(root, bg=self.BG) #creeaza un frame top in root (se creeaza bara de sus)
        top.pack(fill="x") #il intinde doar pe latime (orizonala)

        self.city_var = tk.StringVar() #variabila Tkinter de tip string
        #se poate citii/scrie automat in ea

        #se creeza un entry in frame-ul top , legat de variabila "city_var"
        self.entry = tk.Entry(
            top, textvariable=self.city_var,
            font=("Helvetica", 12),
            bg=self.CARD2, fg=self.TEXT,
            relief="solid", bd=1,
            highlightthickness=1, highlightbackground=self.LINE, highlightcolor=self.ACCENT,
            insertbackground=self.TEXT
        )
        #se aseaza entry ul in top, pe stanga, se intinde pe latime
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.cautareOras()) #cand se apasa pe enter in entry, se apeleaza cautarea

        #butonul cauta
        self.btn = tk.Button( #creeaza un buton in frame ul "top", text: cauta
            top, text="Caută",
            font=("Helvetica", 11, "bold"),
            bg=self.ACCENT, fg="white",
            activebackground=self.ACCENT, activeforeground="white",
            bd=0, padx=16, pady=10,
            command=self.cautareOras #la click se apeleaza metoda de cautare
        )
        self.btn.pack(side="right") #se aseaza butonul in partea dreapta a barei top

        #se creeaza un label sub search, in root, cu text informativ
        self.status = tk.Label(root, text="Introdu un oraș (ex: Sibiu / București / London,UK)",
                               bg=self.BG, fg=self.MUTED, font=("Helvetica", 10))
        self.status.pack(anchor="w", pady=(10, 10)) #se azeaza labelul, aliniat la stanga

        # ==> Cardul cu vremea curenta
        #se creeaza un frame cu cardul principal
        current = tk.Frame(root, bg=self.CARD, highlightthickness=1, highlightbackground=self.LINE)
        current.pack(fill="x", pady=(0, 12)) #se intinde pe latime cu spatiu de 12

        #creez un frame interior pt un padding mai frumos, in interiorul frameului cu vreme curenta
        curent_inner = tk.Frame(current, bg=self.CARD)
        curent_inner.pack(fill="x", padx=14, pady=14)

        # blocul centrat (icon,tmp,city,time)
        center = tk.Frame(curent_inner, bg=self.CARD) #frame pt continutul central, in interiorul current_inner
        center.pack(fill="x") # pe latime

        #label pt iconita principala cu imaginea
        self.icon_lbl = tk.Label(center, bg=self.CARD) #il asez in interiorul ferestrei de centru
        self.icon_lbl.pack(anchor="center", pady=(2, 0)) #centrez imaginea

        #label pt temperatura, adaugata in fereastra si centrata
        self.temp_lbl = tk.Label(center, text="—", font=("Helvetica", 44, "bold"),
                                 bg=self.CARD, fg=self.TEXT)
        self.temp_lbl.pack(anchor="center", pady=(4, 0))

        #label pt oras
        self.city_lbl = tk.Label(center, text="—", font=("Helvetica", 12, "bold"),
                                 bg=self.CARD, fg=self.MUTED)
        self.city_lbl.pack(anchor="center", pady=(8, 0))

        # label pentru descriere + ora locala
        self.desc_time_lbl = tk.Label(center, text="—", font=("Helvetica", 11),
                                      bg=self.CARD, fg=self.MUTED)
        self.desc_time_lbl.pack(anchor="center", pady=(6, 0))

        # Statistici vreme (pe linie)
        stats = tk.Frame(root, bg=self.BG) #frame care va contine 3 "cutii"
        stats.pack(fill="x", pady=(0, 12))

        #creez 3 frameuri folosind metoda _start
        #fiecare bix contine valoade si titlu
        self.stat_wind = self._statistici(stats, "Vant", "—")
        self.stat_rain = self._statistici(stats, "Precip", "—")
        self.stat_hum = self._statistici(stats, "Umiditate", "—")

        #asez boxurile
        self.stat_wind.pack(side="left", fill="both", expand=True, padx=(0, 8)) #in stanga
        self.stat_rain.pack(side="left", fill="both", expand=True, padx=8) #in centru
        self.stat_hum.pack(side="left", fill="both", expand=True, padx=(8, 0)) #in dreapta

        # Frame pt sectiunea cu vremea in urmatorele ore
        hourly_card = tk.Frame(root, bg=self.CARD2, highlightthickness=1, highlightbackground=self.LINE)
        hourly_card.pack(fill="x", pady=(0, 12))

        #label cu titlu, asezat in sectiunea cu vremea
        tk.Label(hourly_card, text="Forecast din 3 în 3 ore",
                 bg=self.CARD2, fg=self.TEXT, font=("Helvetica", 11, "bold")
                 ).pack(anchor="w", padx=12, pady=(10, 0))

        #canvas folosit ca fereastra de vizualizare pt continutul scrolabil
        self.hourly_canvas = tk.Canvas(hourly_card, bg=self.CARD2, highlightthickness=0, height=120)
        self.hourly_canvas.pack(fill="x", padx=8, pady=(8, 6))

        #scroll orizontal care controleaza canvas-ul pe axa X
        self.hscroll = tk.Scrollbar(hourly_card, orient="horizontal", command=self.hourly_canvas.xview)
        self.hscroll.pack(fill="x", padx=8, pady=(0, 10))
        #leg canvas ul de scrollbar: cand canvas ul se misca, scrollbar ul se actualizeaza
        self.hourly_canvas.configure(xscrollcommand=self.hscroll.set)

        #frameul cu chipurile(framurile mici), asezate in canva pt a fi scrollabile
        self.hourly_inner = tk.Frame(self.hourly_canvas, bg=self.CARD2)
        #canvas nu poate contine direc widgeturi, creez un window item in canvas
        self.hourly_window = self.hourly_canvas.create_window((0, 0), window=self.hourly_inner, anchor="nw") #coordonate, in coltul st sus
        #cand se schimba dimensiunea continutului, se actualizeaza scrollRegion la dimensiunea continutului
        self.hourly_inner.bind("<Configure>", lambda e: self.hourly_canvas.configure(scrollregion=self.hourly_canvas.bbox("all")))

        # Frame ul pt vremea pe zile
        daily_card = tk.Frame(root, bg=self.CARD2, highlightthickness=1, highlightbackground=self.LINE)
        daily_card.pack(fill="x")

        tk.Label(daily_card, text="Forecast pe zile",
                 bg=self.CARD2, fg=self.TEXT, font=("Helvetica", 11, "bold")
                 ).pack(anchor="w", padx=12, pady=(10, 0))

        self.daily_canvas = tk.Canvas(daily_card, bg=self.CARD2, highlightthickness=0, height=120)
        self.daily_canvas.pack(fill="x", padx=8, pady=(8, 6))

        self.dscroll = tk.Scrollbar(daily_card, orient="horizontal", command=self.daily_canvas.xview)
        self.dscroll.pack(fill="x", padx=8, pady=(0, 10))
        self.daily_canvas.configure(xscrollcommand=self.dscroll.set)

        self.daily_inner = tk.Frame(self.daily_canvas, bg=self.CARD2)
        self.daily_window = self.daily_canvas.create_window((0, 0), window=self.daily_inner, anchor="nw")
        self.daily_inner.bind("<Configure>", lambda e: self.daily_canvas.configure(scrollregion=self.daily_canvas.bbox("all")))

        self.entry.focus_set()

    #pt construirea boxurilor de la statistici
    def _statistici(self, parent, title, value):
        box = tk.Frame(parent, bg=self.CARD2, highlightthickness=1, highlightbackground=self.LINE)
        box.configure(padx=10, pady=10) #adaug padding

        #lbl pt valoare
        val_lbl = tk.Label(box, text=value, font=("Helvetica", 14, "bold"), bg=self.CARD2, fg=self.ACCENT)
        val_lbl.pack() #lbl asezat in box

        #creare label pt titlu (ex. vant)
        tk.Label(box, text=title, font=("Helvetica", 9), bg=self.CARD2, fg=self.MUTED).pack(pady=(4, 0))
        #atasare label cu valoarea
        box._value_label = val_lbl
        return box

    # iconite -> metoda care primeste codul iconitei de la openWeather
    def get_icon(self, icon_code: str, size: tuple[int, int]):
        if not (PIL_OK and icon_code): #verificam daca Pillow e instalat si daca exista un cod valid de icon
            return None #functia se orpeste daca nu e
        key = (icon_code, size) #o cheie pt memoria cache
        if key in self.icon_cache: #daca cheia a fost deja descarcata, convertita, redimensionata o returnam din memorie
            return self.icon_cache[key]

        #trimite request get catre openWeather pt icon
        r = self.session.get(ICON_URL.format(icon=icon_code), timeout=6)
        r.raise_for_status() #pt tratarea exceptilor
        #conversia de la bytes la RGBA pt afisarea corecta in interfata
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        #redimensionare imagine la dimensiunea ceruta
        #lanczos -> algoritm de calitate mare
        img = img.resize(size, Image.LANCZOS)
        #transformare imagine PILLOW in PhotoImage
        tk_img = ImageTk.PhotoImage(img)
        self.icon_cache[key] = tk_img #salvarea cheii in cache (codul+dimensiunea)
        return tk_img #returnare icon

    # functie ce porneste cautarea orasului, cheama API ul, actualizeaza UI ul
    def cautareOras(self):
        city = self.city_var.get().strip() #ia textul din entry, entry e legat de city_var
        if not city: #daca nu e introdus un oras
            messagebox.showinfo("Info", "Scrie un oraș (ex: Sibiu / București / London,UK).")
            return
        if not API_KEY: #daca nu e valabila cheia API
            messagebox.showerror("Missing API key", "Set the OPENWEATHER_API_KEY environment variable.")
            return

        self.btn.config(state="disabled") #se opreste butonul de cautare
        self.status.config(text="Caut...") #se schimba statusul (sub search)

        try:
            current = self.vremeCurentaFetch(city)  #metoda care face request la /weather si primeste un json (dict)
            fc = self.prognozaMeteoFetch(city)  #metoda care face request la /forecast si primeste json (dict)
            self.actualizareUI(current, fc)  #trimite datele in render ca sa actualizeze interfata
            self.status.config(text="Oras gasit") #se actualizeaza status
        except requests.HTTPError as e: #eroare http
            try:
                msg = e.response.json().get("message", str(e))
            except Exception:
                msg = str(e)
            messagebox.showerror("Eroare OpenWeather", msg)
            self.status.config(text="Eroare.")
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
            self.status.config(text="Eroare.")
        finally:
            self.btn.config(state="normal")

    #metoda care returneaza un dictionar cu vremea curenta
    def vremeCurentaFetch(self, city: str) -> dict:
        params = {"q": city, "appid": API_KEY, "units": UNITS, "lang": LANG}
        #trimite request get catre server
        r = self.session.get(CURRENT_URL, params=params, timeout=8)
        #verifica status HTTP
        r.raise_for_status()
        return r.json() #converteste de la json la dictionar

    #metoda care returneaza un dictionar cu vremea pe zile
    def prognozaMeteoFetch(self, city: str) -> dict:
        params = {"q": city, "appid": API_KEY, "units": UNITS, "lang": LANG}
        #request get catre server
        r = self.session.get(FORECAST_URL, params=params, timeout=8)
        r.raise_for_status() #verificare erori
        return r.json() #returnare dictionar de la json

    #primeste doua json uri -> current si forecast
    def actualizareUI(self, current: dict, forecast: dict):
        name = current.get("name", "—") #pt numele orasului
        country = safe(current, "sys", "country", default="") #pt mumele tarii
        self.city_lbl.config(text=f"{name}, {country}" if country else name) #actualizare lbl oras

        #timezone in secunde
        tz_offset = int(current.get("timezone", 0))
        lt = local_time_from_offset(tz_offset) #ora locala in UTC now + offset
        time_str = lt.strftime("%H:%M") #transformare in format

        #temperatura curenta
        temp = safe(current, "main", "temp")
        self.temp_lbl.config(text=tmpRotunjire(temp)) #actualizare lbl tmp

        #descriere + ora (labelul de sub oras)
        w0 = (current.get("weather") or [{}])[0]
        desc = (w0.get("main") or w0.get("description") or "—").upper()
        self.desc_time_lbl.config(text=f"{desc} • {time_str}") #actualizare

        # iconita principala (cea mare)
        icon_code = w0.get("icon", "") #ia codul iconitei
        #obtine iconita redimensionata, daca nu o obtine nu avem iconita
        self.icon_main = None
        try:
            self.icon_main = self.get_icon(icon_code, (110, 110))
        except Exception:
            self.icon_main = None
        #daca exista iconita o seteaza in lbl , daca nu, o goleste ca sa nu ramana una goala
        if self.icon_main:
            self.icon_lbl.config(image=self.icon_main, text="")
        else:
            self.icon_lbl.config(image="", text="")

        # statistici
        #vantul in m/s, daca nu exista pun 0.0
        wind_ms = safe(current, "wind", "speed", default=0.0) or 0.0
        #umiditatea cu %
        hum = safe(current, "main", "humidity", default=0) or 0
        #ploaia pe ultima ora, daca exista
        rain1h = safe(current, "rain", "1h", default=0.0) or 0.0

        #afisez vantul cu conversie m/s -> km/h, fara zecimale
        self.stat_wind._value_label.config(text=f"{conversie_ms_la_kms(float(wind_ms)) :.0f} km/h")
        self.stat_rain._value_label.config(text=f"{rain1h:.1f} mm") #1 zecimala la mm
        self.stat_hum._value_label.config(text=f"{int(hum)} %") #transfrma in int si adauag %

        #prognora din 3 in 3 ore
        for w in self.hourly_inner.winfo_children(): #sterg imaginile vechi (refresh), din cardul precedent
            w.destroy()
        self.hourly_icons_refs.clear() #golesc lista de referinte la iconite

        items = (forecast.get("list") or [])[:12] #iau primele 12 puncte (pt 36 de ore)
        for it in items:
            dt_txt = it.get("dt_txt") #timpu; in format string
            if not dt_txt:
                continue
            #determinare ora locala a orasului
            dt_local = (parse_dt_utc(dt_txt) + timedelta(seconds=tz_offset)).replace(tzinfo=None)

            #temperatura
            t = safe(it, "main", "temp")
            #iconul intervalului
            w1 = (it.get("weather") or [{}])[0]
            icon = w1.get("icon", "")

            #creare chip vizual pt forecast pe ore
            chip = tk.Frame(self.hourly_inner, bg=self.CARD2, highlightthickness=1, highlightbackground=self.LINE)
            chip.pack(side="left", padx=6, pady=8)

            #afisare ora: ex 3 pm
            tk.Label(chip, text=afisareOraPretty(dt_local), bg=self.CARD2, fg=self.MUTED, font=("Helvetica", 9)).pack(
                padx=12, pady=(10, 2)
            )

            #se incarca iconita mica
            img = None
            try:
                img = self.get_icon(icon, (40, 40))
            except Exception:
                img = None
            if img:
                self.hourly_icons_refs.append(img)
                tk.Label(chip, image=img, bg=self.CARD2).pack(padx=12)
            else:
                tk.Label(chip, text="•", bg=self.CARD2, fg=self.MUTED).pack(padx=12)

            #temperatura chip
            tk.Label(chip, text=tmpRotunjire(t), bg=self.CARD2, fg=self.TEXT, font=("Helvetica", 11, "bold")).pack(
                padx=12, pady=(2, 10)
            )

        #update scroll-region
        self.hourly_canvas.configure(scrollregion=self.hourly_canvas.bbox("all"))

        # forecast pe zile
        #sterg forecastul vechi si icon refs
        for w in self.daily_inner.winfo_children():
            w.destroy()
        self.daily_icons_refs.clear()

        #aleg pt 5 zile
        daily = aggregate_daily(forecast, tz_offset, days=5)
        #pt fiecare zi creez un frame
        for d in daily:
            day_date = d["date"]
            tmin, tmax = d["tmin"], d["tmax"]
            icon = d["icon"]

            chip = tk.Frame(self.daily_inner, bg=self.CARD2, highlightthickness=1, highlightbackground=self.LINE)
            chip.pack(side="left", padx=6, pady=8)

            # label: zi si data
            day_label = ziuaPresc(datetime.combine(day_date, datetime.min.time()))
            date_label = day_date.strftime("%d %b")

            #le adaug
            tk.Label(chip, text=day_label, bg=self.CARD2, fg=self.MUTED, font=("Helvetica", 9)).pack(
                padx=12, pady=(10, 0)
            )
            tk.Label(chip, text=date_label, bg=self.CARD2, fg=self.MUTED, font=("Helvetica", 9)).pack(
                padx=12, pady=(2, 6)
            )

            #iconita zilnica, la fel ca prognoza pe ore
            img = None
            try:
                img = self.get_icon(icon, (20, 20)) #iconita
            except Exception:
                img = None
            if img:
                self.daily_icons_refs.append(img) #o salvam in daily refs
                tk.Label(chip, image=img, bg=self.CARD2).pack(padx=12)
            else:
                tk.Label(chip, text="•", bg=self.CARD2, fg=self.MUTED).pack(padx=12)

            tk.Label(
                chip,
                text=f"{tmpRotunjire(tmin)} / {tmpRotunjire(tmax)}",
                bg=self.CARD2, fg=self.TEXT, font=("Helvetica", 11, "bold")
            ).pack(padx=12, pady=(6, 10))

        #update scroll
        self.daily_canvas.configure(scrollregion=self.daily_canvas.bbox("all"))


if __name__ == "__main__":
    WeatherClean().mainloop()
