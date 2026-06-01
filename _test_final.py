import sys, os
sys.path.insert(0, '.')
from dotenv import find_dotenv, load_dotenv
p1 = find_dotenv(usecwd=True)
print("From CWD (root):", p1)
if p1:
    load_dotenv(p1)
    print("KEY from root:", bool(os.getenv("OPENAI_API_KEY")))
old_cwd = os.getcwd()
os.chdir("backend")
p2 = find_dotenv(usecwd=True)
print("From CWD (backend):", p2)
os.chdir(old_cwd)
from backend.services.openai_service import HAS_OPENAI, OPENAI_API_KEY, analyze_message
print()
print("HAS_OPENAI:", HAS_OPENAI)
print("KEY loaded:", bool(OPENAI_API_KEY))
print("KEY prefix:", OPENAI_API_KEY[:18] if OPENAI_API_KEY else "NONE")
tests = [
    "Это просто отличный сервис!",
    "Ужас! Всё сломалось и не работает.",
    "Когда будет обновление?"
]
print()
for t in tests:
    r = analyze_message(t)
    print(f"sent={r['sentiment']:8s} emotion={r['emotion']:10s} cat={r['category']:10s} priority={r['priority']:6s} complaint={str(r['complaint']):5s}")
print()
print("All OK - OpenAI analysis works!")
