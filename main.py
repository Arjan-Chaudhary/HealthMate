import hashlib, json, math, os, random, re, secrets, sqlite3, time
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="HealthMate AI")
KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("MODEL", "claude-sonnet-5-5")
W = "https://www.who.int/news-room/fact-sheets/detail/"
_K = [
("who-activity","WHO: Physical activity","physical-activity","exercise activity physical walk workout व्यायाम कसरत","Adults should do at least 150-300 minutes of moderate-intensity aerobic activity per week, plus muscle-strengthening activities on 2 or more days a week.","वयस्कों को हर हफ्ते कम से कम 150-300 मिनट मध्यम तीव्रता की एरोबिक गतिविधि और सप्ताह में 2 या अधिक दिन मांसपेशियों को मज़बूत करने वाले व्यायाम करने चाहिए।"),
("who-bp","WHO: Hypertension","hypertension","blood pressure salt hypertension bp रक्तचाप नमक बीपी","Reducing salt intake to less than 5 g per day (about one teaspoon) helps lower blood pressure. Regular physical activity and avoiding tobacco also help.","नमक का सेवन प्रतिदिन 5 ग्राम (लगभग एक चम्मच) से कम करने से रक्तचाप घटाने में मदद मिलती है। नियमित शारीरिक गतिविधि और तंबाकू से परहेज़ भी मदद करते हैं।"),
("who-diet","WHO: Healthy diet","healthy-diet","diet food sugar fruit vegetables nutrition eat आहार खाना खाएँ चीनी","Eat plenty of fruit, vegetables, legumes, nuts and whole grains. Limit free sugars to under 10% of total energy intake and salt to under 5 g a day.","खूब फल, सब्ज़ियाँ, दालें, मेवे और साबुत अनाज खाएँ। मुक्त शर्करा कुल ऊर्जा के 10% से कम और नमक प्रतिदिन 5 ग्राम से कम रखें।"),
("who-diabetes","WHO: Diabetes","diabetes","diabetes sugar thirst urination शुगर मधुमेह डायबिटीज","A healthy diet, regular physical activity, normal body weight and avoiding tobacco can prevent or delay type 2 diabetes. Increased thirst, frequent urination, tiredness and blurred vision are common symptoms; see a doctor for testing.","संतुलित आहार, नियमित शारीरिक गतिविधि, सामान्य वज़न और तंबाकू से परहेज़ टाइप 2 मधुमेह को रोकने या टालने में मदद करते हैं। अधिक प्यास, बार-बार पेशाब, थकान और धुंधली नज़र आम लक्षण हैं; जाँच के लिए डॉक्टर से मिलें।"),
("who-diarrhoea","WHO: Diarrhoeal disease","diarrhoeal-disease","diarrhoea diarrhea loose motion dehydration ors दस्त","Diarrhoea causes fluid loss. Oral rehydration solution (ORS) and zinc are the recommended treatment for children. Seek medical care for blood in stool, high fever or signs of dehydration.","दस्त में शरीर से पानी की कमी होती है। बच्चों के लिए ओआरएस और ज़िंक की सलाह दी जाती है। मल में खून, तेज़ बुखार या पानी की कमी के लक्षण हों तो डॉक्टर को दिखाएँ।"),
("who-tobacco","WHO: Tobacco","tobacco","tobacco smoking quit cigarette तंबाकू धूम्रपान सिगरेट","Tobacco harms nearly every organ. Quitting at any age brings benefits, and counselling and medicines increase the chance of success.","तंबाकू लगभग हर अंग को नुकसान पहुँचाता है। किसी भी उम्र में छोड़ना फ़ायदेमंद है, और परामर्श व दवाएँ सफलता की संभावना बढ़ाती हैं।"),
("who-depression","WHO: Depression","depression","depression sad mood anxiety stress अवसाद उदास तनाव चिंता","Depression is a common mental health condition causing persistent sadness or loss of interest. Effective treatments exist. Talk to someone you trust and seek professional help; if you have thoughts of self-harm, seek help immediately.","अवसाद एक आम मानसिक स्वास्थ्य स्थिति है जिसमें लगातार उदासी या रुचि में कमी रहती है। प्रभावी इलाज उपलब्ध है। किसी भरोसेमंद व्यक्ति से बात करें और पेशेवर मदद लें; खुद को नुकसान पहुँचाने के विचार आएँ तो तुरंत मदद लें।"),
("who-obesity","WHO: Obesity and overweight","obesity-and-overweight","obesity overweight weight fat मोटापा वज़न","Overweight and obesity raise the risk of diabetes, heart disease and some cancers. Balance the calories you eat with the calories you use, eat less fat and sugar, and stay physically active.","अधिक वज़न और मोटापा मधुमेह, हृदय रोग और कुछ कैंसर का खतरा बढ़ाते हैं। जितनी कैलोरी लें उतनी खर्च करें, वसा और चीनी कम खाएँ और सक्रिय रहें।"),
("who-anaemia","WHO: Anaemia","anaemia","anaemia anemia iron tired pale haemoglobin एनीमिया खून आयरन","Anaemia means too few healthy red blood cells, and iron deficiency is a common cause. Tiredness, pale skin and breathlessness are common signs. Get a blood test and ask a doctor before taking iron supplements.","एनीमिया में स्वस्थ लाल रक्त कोशिकाएँ कम होती हैं और आयरन की कमी इसका आम कारण है। थकान, पीलापन और साँस फूलना आम संकेत हैं। आयरन की गोलियाँ लेने से पहले खून की जाँच करवाएँ और डॉक्टर से पूछें।"),
("who-dengue","WHO: Dengue","dengue-and-severe-dengue","dengue mosquito fever platelet डेंगू मच्छर बुखार","Dengue spreads by mosquito bites and has no specific treatment. Remove standing water and prevent bites. Seek urgent care for severe abdominal pain, persistent vomiting, bleeding or extreme tiredness.","डेंगू मच्छर के काटने से फैलता है और इसका कोई विशिष्ट इलाज नहीं है। रुका हुआ पानी हटाएँ और मच्छरों से बचें। तेज़ पेट दर्द, लगातार उल्टी, रक्तस्राव या बहुत कमज़ोरी हो तो तुरंत इलाज लें।"),
]
KB = [dict(id=a, title=b, url=W + c, kw=d, text=e, hi=f) for a, b, c, d, e, f in _K]
STOP = {"the","and","how","what","can","for","with","about","should","much","are","you","does","tell","why","when","who","this","that","have","from","not"}
EMERG = re.compile(r"chest pain|can'?t breathe|cannot breathe|difficulty breathing|shortness of breath|unconscious|fainted|seizure|slurred|face droop|can'?t (lift|move)|severe bleeding|bleeding (a lot|heavily)|poison|overdose|suicid|kill myself|want to die|snake ?bite|सीने में दर्द|सांस (नहीं|लेने में)|बेहोश|दौरा|लकवा|ज़हर|जहर|आत्महत्या|खून बह|मरना चाहत|सांप ने", re.I)
EMERG_MSG = "This may be an emergency. Call 112 now (ambulance: 108) or go to the nearest hospital. Do not wait. If you are thinking of harming yourself, call Tele-MANAS 14416. / यह आपातकाल हो सकता है। अभी 112 (एम्बुलेंस 108) पर कॉल करें।"
HIGH = {"diabetes", "kidney", "heart", "pregnancy", "eating_disorder"}

class Chat(BaseModel):
    message: str = Field(min_length=2, max_length=1000)

def retrieve(q):
    toks = {t for t in re.findall(r"[^\s.,?!।]+", q.lower()) if len(t) > 2 and t not in STOP}
    out = []
    for d in KB:
        s = sum(2 for t in toks if t in d["kw"].lower()) + sum(1 for t in toks if t in d["text"].lower())
        out.append((s, d))
    out = [x for x in sorted(out, key=lambda x: -x[0]) if x[0] >= 2]
    return [d for _, d in out[:3]]

async def llm(q, ps):
    ctx = "\n\n".join(f"[{p['id']}] {p['text']}" for p in ps)
    sys = ("You are a health education assistant. Answer ONLY from the passages, in simple language, in the same language as the question. "
           "Cite passage ids like [who-bp]. If the passages don't answer it, say so. Never diagnose or recommend medicines/doses. Max 120 words.")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": KEY, "anthropic-version": "2023-06-01"},
            json={"model": MODEL, "max_tokens": 400, "system": sys,
                  "messages": [{"role": "user", "content": f"Passages:\n{ctx}\n\nQuestion: {q}"}]})
        r.raise_for_status()
        return r.json()["content"][0]["text"]

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.post("/api/chat")
async def chat(b: Chat):
    if EMERG.search(b.message):
        return {"emergency": True, "answer": EMERG_MSG, "sources": []}
    ps = retrieve(b.message)
    if not ps:
        return {"emergency": False, "answer": ("मुझे इसका सुरक्षित उत्तर देने के लिए भरोसेमंद जानकारी नहीं मिली। कृपया किसी योग्य डॉक्टर से सलाह लें।" if re.search(r"[\u0900-\u097F]", b.message) else "I could not find reliable information to answer this safely. Please consult a qualified healthcare professional."), "sources": []}
    ans = None
    if KEY:
        try: ans = await llm(b.message, ps)
        except Exception: ans = None
    if not ans:
        hi = bool(re.search(r"[\u0900-\u097F]", b.message))
        ans = " ".join(p["hi"] if hi else p["text"] for p in ps[:2])
    return {"emergency": False, "answer": ans, "sources": [{"id": p["id"], "title": p["title"], "url": p["url"]} for p in ps]}

class Profile(BaseModel):
    age: int = Field(ge=5, le=100)
    sex: str = Field(pattern="^(male|female)$")
    height_cm: float = Field(ge=100, le=230)
    weight_kg: float = Field(ge=30, le=250)
    activity: str = Field(default="light", pattern="^(sedentary|light|moderate|active)$")
    goal: str = Field(default="maintain", pattern="^(lose|maintain|gain)$")
    veg: bool = True
    conditions: list[str] = []

def refer(p):
    if p.age < 18 or HIGH & set(p.conditions):
        return {"plan": None, "message": "Your age or health condition needs personalised advice. Please consult your doctor or a registered dietitian before changing diet or exercise."}

@app.post("/api/diet-plan")
def diet(p: Profile):
    if (r := refer(p)): return r
    bmr = 10*p.weight_kg + 6.25*p.height_cm - 5*p.age + (5 if p.sex == "male" else -161)
    tdee = bmr * {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}[p.activity]
    target = tdee + {"lose": -400, "maintain": 0, "gain": 300}[p.goal]
    floor = 1500 if p.sex == "male" else 1200
    target = round(max(target, floor))
    macros = {"protein_g": round(target*.2/4), "carbs_g": round(target*.5/4), "fat_g": round(target*.3/9)}
    meals = {
     "breakfast": (.25, ["Vegetable poha with peanuts + curd", "Besan chilla with mint chutney", "Idli (3) with sambar"] + ([] if p.veg else ["Egg bhurji + 1 roti"])),
     "lunch": (.35, ["2 rotis, dal, seasonal sabzi, salad, curd", "1 katori rice, rajma/chole, salad"] + ([] if p.veg else ["Fish/chicken curry, 1 roti or rice, salad"])),
     "snack": (.10, ["Roasted chana", "Fruit + a few nuts", "Buttermilk"]),
     "dinner": (.30, ["Vegetable khichdi + curd", "2 rotis, paneer or dal, sabzi"] + ([] if p.veg else ["Egg curry or grilled chicken, 1 roti, sabzi"])),
    }
    return {"bmr_kcal": round(bmr), "maintenance_kcal": round(tdee), "target_kcal": target, "floor_applied": target == floor,
            "macros": macros, "meals": {k: {"kcal": round(target*f), "options": o} for k, (f, o) in meals.items()},
            "notes": ["Formula: Mifflin-St Jeor. Drink 2-3 L water daily unless your doctor says otherwise.", "General guidance, not medical advice."]}

@app.post("/api/exercise-plan")
def exercise(p: Profile, level: str = "beginner", days: int = 4):
    if (r := refer(p)): return r
    days = max(2, min(days, 6)); mins = 20 if level == "beginner" else 30
    order = [0, 3, 1, 4, 2, 5]; active = sorted(order[:days])
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]; strength = {0, 3}
    plan = []
    for i, n in enumerate(names):
        if i in strength and i in active:
            plan.append({"day": n, "type": "Strength", "minutes": mins, "what": "Squats, wall push-ups, glute bridges, plank (2-3 sets each)"})
        elif i in active:
            plan.append({"day": n, "type": "Cardio", "minutes": mins, "what": "Brisk walk, cycling or Surya Namaskar rounds"})
        else:
            plan.append({"day": n, "type": "Rest", "minutes": 0, "what": "Rest or gentle stretching"})
    tot = sum(d["minutes"] for d in plan)
    return {"weekly_minutes": tot, "plan": plan,
            "notes": ["Warm up 5 min, cool down 5 min. Stop if you feel pain, dizziness or chest discomfort.",
                      "WHO target: 150-300 min/week moderate activity + strength on 2+ days. " + ("Build up gradually towards it." if tot < 150 else "This meets the minimum.")]}

class Risk(BaseModel):
    age: int = Field(ge=18, le=100)
    sex: str = Field(pattern="^(male|female)$")
    waist_cm: float = Field(ge=50, le=200)
    activity: str = Field(pattern="^(regular|some|none)$")
    family: int = Field(ge=0, le=2)

@app.post("/api/risk-screen")
def risk(r: Risk):
    s = 0 if r.age < 35 else 20 if r.age < 50 else 30
    lo, hi = (90, 100) if r.sex == "male" else (80, 90)
    s += 0 if r.waist_cm < lo else 10 if r.waist_cm < hi else 20
    s += {"regular": 0, "some": 20, "none": 30}[r.activity] + 10 * r.family
    band = "low" if s < 30 else "moderate" if s < 60 else "high"
    msg = {"low": "Keep up healthy habits.", "moderate": "Consider a blood sugar check at your next doctor visit.", "high": "Please discuss diabetes testing with a doctor soon."}[band]
    return {"score": s, "of": 100, "band": band, "message": msg + " This is a screening score (IDRS-style), not a diagnosis."}

@app.get("/api/band")
def band(scenario: str = "normal"):
    rnd = random.Random(7); c = scenario == "concerning"; days = []
    for d in range(14):
        late = c and d >= 7
        days.append({"day": d+1, "resting_hr": round(62 + rnd.uniform(-2, 2) + ((d-6)*2 if late else 0)),
                     "steps": int(rnd.uniform(5500, 9000) * (0.45 if late else 1)),
                     "sleep_h": round(rnd.uniform(6.8, 8) - (1.8 if late else 0), 1),
                     "spo2": round(rnd.uniform(95, 98) - (7 if late and d % 3 == 0 else 0))})
    f = []
    if sum(x["resting_hr"] for x in days[-5:])/5 - sum(x["resting_hr"] for x in days[:5])/5 >= 8: f.append("Resting heart rate has risen noticeably over two weeks.")
    if sum(x["spo2"] < 92 for x in days) >= 2: f.append("Several low oxygen readings (<92%).")
    if sum(x["sleep_h"] for x in days[-7:])/7 < 6: f.append("Average sleep under 6 hours this week.")
    if sum(x["steps"] for x in days[-7:])/7 < 4000: f.append("Very low activity this week.")
    return {"simulated": True, "days": days, "flags": f or ["No concerning patterns."],
            "advice": "Flags are patterns worth discussing with a doctor, not a diagnosis." if f else ""}

@app.get("/api/nearby")
async def nearby(lat: float, lon: float, radius: int = 5000):
    q = f'[out:json][timeout:15];nwr(around:{min(radius,15000)},{lat},{lon})[amenity~"hospital|clinic"];out center 40;'
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            els = (await c.post("https://overpass-api.de/api/interpreter", data={"data": q})).json()["elements"]
    except Exception:
        return {"places": [], "note": "Map service unavailable. Call 112 in an emergency."}
    res = []
    for e in els:
        la = e.get("lat") or e.get("center", {}).get("lat"); lo = e.get("lon") or e.get("center", {}).get("lon")
        if la is None: continue
        t = e.get("tags", {})
        dx = math.radians(lo-lon)*math.cos(math.radians(lat)); dy = math.radians(la-lat)
        res.append({"name": t.get("name", "Unnamed " + t.get("amenity", "facility")), "type": t.get("amenity"), "phone": t.get("phone") or t.get("contact:phone"),
                    "km": round(6371*math.hypot(dx, dy), 1), "lat": la, "lon": lo})
    return {"places": sorted(res, key=lambda x: x["km"])[:10], "note": "Listings may be outdated. Call ahead. Emergency: 112 / 108."}


# ---------- Accounts and saved data (SQLite) ----------
DB = os.getenv("DB_PATH", "healthmate.db")
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
with db() as _c:
    _c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE, pw TEXT, salt TEXT, profile TEXT, consent_at REAL, created REAL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, uid INTEGER, created REAL);
CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, uid INTEGER, kind TEXT, data TEXT, created REAL);""")

class Cred(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=200)
    password: str = Field(min_length=8, max_length=200)
    consent: bool = False

class Hist(BaseModel):
    kind: str = Field(pattern="^(chat|diet|exercise|risk)$")
    data: dict

def hp(pw, salt): return hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()
def new_session(c, uid):
    t = secrets.token_urlsafe(32); c.execute("INSERT INTO sessions VALUES(?,?,?)", (t, uid, time.time())); return t
def tok(authorization): return (authorization or "").removeprefix("Bearer ").strip()
def who(authorization: str = Header(None)):
    with db() as c:
        s = c.execute("SELECT uid,created FROM sessions WHERE token=?", (tok(authorization),)).fetchone()
    if not s or time.time() - s["created"] > 30 * 86400: raise HTTPException(401, "Please log in again.")
    return s["uid"]

@app.post("/api/register")
def register(b: Cred):
    if not b.consent: raise HTTPException(400, "Consent is required to create an account.")
    salt = secrets.token_hex(16)
    with db() as c:
        try:
            k = c.execute("INSERT INTO users(email,pw,salt,consent_at,created) VALUES(?,?,?,?,?)",
                          (b.email.lower(), hp(b.password, salt), salt, time.time(), time.time()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Email already registered.")
        return {"token": new_session(c, k.lastrowid)}

@app.post("/api/login")
def login(b: Cred):
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (b.email.lower(),)).fetchone()
        if not u or not secrets.compare_digest(u["pw"], hp(b.password, u["salt"])): raise HTTPException(401, "Wrong email or password.")
        return {"token": new_session(c, u["id"])}

@app.post("/api/logout")
def logout(authorization: str = Header(None)):
    with db() as c: c.execute("DELETE FROM sessions WHERE token=?", (tok(authorization),))
    return {"ok": True}

@app.get("/api/me/profile")
def get_profile(uid: int = Depends(who)):
    with db() as c: r = c.execute("SELECT profile FROM users WHERE id=?", (uid,)).fetchone()
    return {"profile": json.loads(r["profile"]) if r and r["profile"] else None}

@app.put("/api/me/profile")
def put_profile(p: Profile, uid: int = Depends(who)):
    with db() as c: c.execute("UPDATE users SET profile=? WHERE id=?", (p.model_dump_json(), uid))
    return {"ok": True}

@app.post("/api/history")
def add_history(h: Hist, uid: int = Depends(who)):
    d = json.dumps(h.data)
    if len(d) > 20000: raise HTTPException(413, "Too large.")
    with db() as c: c.execute("INSERT INTO history(uid,kind,data,created) VALUES(?,?,?,?)", (uid, h.kind, d, time.time()))
    return {"ok": True}

@app.get("/api/history")
def get_history(uid: int = Depends(who)):
    with db() as c: rows = c.execute("SELECT kind,data,created FROM history WHERE uid=? ORDER BY id DESC LIMIT 50", (uid,)).fetchall()
    return {"items": [{"kind": r["kind"], "data": json.loads(r["data"]), "created": r["created"]} for r in rows]}

@app.delete("/api/me")
def delete_me(uid: int = Depends(who)):
    with db() as c:
        for t, col in (("history", "uid"), ("sessions", "uid"), ("users", "id")): c.execute(f"DELETE FROM {t} WHERE {col}=?", (uid,))
    return {"deleted": True}

app.mount("/", StaticFiles(directory="static", html=True), name="static")
