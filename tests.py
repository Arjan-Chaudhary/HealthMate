import os, re
os.environ["DB_PATH"] = "test_tmp.db"; os.environ.pop("ANTHROPIC_API_KEY", None)
from fastapi.testclient import TestClient
from main import app
c = TestClient(app); P = [0, 0]
def check(n, ok):
    P[0 if ok else 1] += 1; print(("PASS " if ok else "FAIL ") + n)
def chat(m): return c.post("/api/chat", json={"message": m}).json()
HI = r"[\u0900-\u097F]"
check("EN emergency", chat("I have chest pain")["emergency"])
check("EN indirect stroke", chat("my father's speech is slurred and he can't lift his arm")["emergency"])
check("HI emergency", chat("मुझे सीने में दर्द हो रहा है")["emergency"])
r = chat("how much salt should I eat"); check("salt question grounded in who-bp", "who-bp" in [s["id"] for s in r["sources"]])
check("unsupported question refuses", chat("tell me about the moon landing")["sources"] == [])
r = chat("नमक कितना खाना चाहिए"); check("Hindi question gets Hindi answer + source", bool(re.search(HI, r["answer"])) and bool(r["sources"]))
check("dengue question grounded", bool(chat("dengue fever what to do")["sources"]))
base = dict(age=30, sex="female", height_cm=150, weight_kg=45, activity="sedentary", goal="lose", veg=True, conditions=[])
check("calorie floor enforced", c.post("/api/diet-plan", json=base).json()["target_kcal"] >= 1200)
check("diabetes -> doctor referral", c.post("/api/diet-plan", json={**base, "conditions": ["diabetes"]}).json()["plan"] is None)
check("minor -> doctor referral", c.post("/api/exercise-plan", json={**base, "age": 16}).json()["plan"] is None)
check("exercise meets 150 min", c.post("/api/exercise-plan?level=intermediate&days=5", json=base).json()["weekly_minutes"] >= 150)
check("risk high", c.post("/api/risk-screen", json=dict(age=55, sex="male", waist_cm=105, activity="none", family=2)).json()["band"] == "high")
check("risk low", c.post("/api/risk-screen", json=dict(age=25, sex="female", waist_cm=70, activity="regular", family=0)).json()["band"] == "low")
check("band concerning flags", len(c.get("/api/band?scenario=concerning").json()["flags"]) >= 2)
check("band normal no flags", c.get("/api/band").json()["flags"] == ["No concerning patterns."])
cr = dict(email="t@example.com", password="password123", consent=True)
check("register needs consent", c.post("/api/register", json={**cr, "consent": False}).status_code == 400)
tk = c.post("/api/register", json=cr).json()["token"]; H = {"Authorization": "Bearer " + tk}
check("duplicate email blocked", c.post("/api/register", json=cr).status_code == 409)
c.post("/api/history", json={"kind": "risk", "data": {"x": 1}}, headers=H)
check("history saved", len(c.get("/api/history", headers=H).json()["items"]) == 1)
check("history needs login", c.get("/api/history").status_code == 401)
check("delete account", c.delete("/api/me", headers=H).json()["deleted"])
check("login fails after delete", c.post("/api/login", json=cr).status_code == 401)
print(f"\n{P[0]} passed, {P[1]} failed")
try: os.remove("test_tmp.db")
except OSError: pass
