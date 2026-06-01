import sys, os
sys.path.insert(0, "backend")
os.chdir("C:\\Users\\Danil\\Desktop\\test")

# Fresh import
for mod in list(sys.modules.keys()):
    if "openai_service" in mod or "backend" in mod:
        del sys.modules[mod]

from backend.services.openai_service import HAS_OPENAI, OPENAI_API_KEY
print("HAS_OPENAI:", HAS_OPENAI)
print("KEY loaded:", bool(OPENAI_API_KEY))

from dotenv import find_dotenv, load_dotenv
p = find_dotenv(usecwd=True)
print("Dotenv path:", p)
if p:
    print("Dotenv exists:", os.path.isfile(p))
    print("Dotenv dir:", os.path.dirname(p))
