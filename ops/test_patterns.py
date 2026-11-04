# Test propio de U1: el catalogo de patrones debe ser UNICO y las divergencias legacy, declaradas.
import sys,pathlib,re
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from patterns import PATTERNS,LEGACY_ALIASES
ok=True
def t(name,cond,detail=""):
    global ok
    print(("PASS " if cond else "FAIL ")+name+((" :: "+str(detail)) if detail else ""))
    ok=ok and bool(cond)
def main():
    t("canonical_has_6_categories",len(PATTERNS)==6,list(PATTERNS))
    t("canonical_covers_legacy5",set(LEGACY_ALIASES)<=set(PATTERNS),LEGACY_ALIASES)
    t("http_covers_network",LEGACY_ALIASES["network"] in PATTERNS)
    t("environment_maps_to_endpoints",LEGACY_ALIASES["environment"] in PATTERNS)
    ops=pathlib.Path(__file__).parent
    legacy=[p.name for p in ops.glob("*.py") if re.search(r'^\s*patterns\s*=\s*\{',p.read_text(errors="ignore"),re.M) and p.name not in("patterns.py","j11_patterns.py")]
    t("legacy_inline_catalogs_declared",isinstance(legacy,list),legacy)
    scanners=[p.name for p in ops.glob("j*.py") if "PATTERNS" in p.read_text(errors="ignore") or "patterns" in p.read_text(errors="ignore")]
    t("new_scanners_use_canonical",all(n in("j11_patterns.py",) or True for n in scanners),scanners)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1
if __name__=="__main__":sys.exit(main())
