#!/usr/bin/env python3
"""Validação estática do site (sem dependências externas).

Uso: python3 scripts/check.py [raiz]      (padrão: pasta acima deste script)
Sai com código 1 se houver qualquer ERRO. Avisos não reprovam.

Confere: links internos e âncoras, assets (href/src/srcset/url() no CSS), links wa.me,
textos de placeholder esquecidos, JSON-LD, metadados básicos e acessibilidade mínima
(lang, title, description, viewport, 1 h1, alt, title em iframe, nome em botões/links,
ids duplicados, handlers inline), e coerência robots.txt × sitemap.xml × meta robots.
"""
import json, os, re, shutil, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlunsplit, urlsplit, unquote, urljoin, quote

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {".git", "scripts", "node_modules", "__pycache__"}
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","source","track","wbr"}
PROIBIDOS = [r"PLACEHOLDER", r"\bA CONFIRMAR\b", r"\ba confirmar\b", r"\[bairro\]", r"lorem ipsum", r"\[ENDERE"]
WA_OK = re.compile(r"^https://wa\.me/55\d{10,11}(\?text=[^\s\"'<>]*)?$")

erros, avisos = [], []
def E(arq, msg): erros.append(f"{arq}: {msg}")
def W(arq, msg): avisos.append(f"{arq}: {msg}")
def rel(p): return os.path.relpath(p, ROOT)

class Pag(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.refs, self.tags, self.ld, self.meta = [], [], [], [], {}
        self.h1 = 0; self.title = ""; self.lang = None
        self.pilha = []          # [tag, attrs, texto]
        self._in_title = False; self._ld = None
    def handle_starttag(self, tag, at):
        a = dict(at)
        if tag == "html": self.lang = a.get("lang")
        if "id" in a: self.ids.append(a["id"])
        for k in ("href", "src"):
            if a.get(k) is not None: self.refs.append((tag, k, a[k]))
        if a.get("srcset"):
            for part in a["srcset"].split(","):
                if part.strip(): self.refs.append((tag, "srcset", part.strip().split()[0]))
        if tag == "meta":
            k = a.get("name") or a.get("property")
            if k: self.meta[k] = a.get("content", "")
            if a.get("property") in ("og:image",) and a.get("content") and not re.match(r"^https?:", a["content"]):
                self.refs.append((tag, "og:image", a["content"]))
        for k in a:
            if k.startswith("on"): self.tags.append(("inline-handler", tag, k))
        if tag == "h1": self.h1 += 1
        if tag == "title": self._in_title = True
        if tag == "script" and a.get("type") == "application/ld+json": self._ld = ""
        if tag == "img" and "alt" not in a: self.tags.append(("img-sem-alt", tag, a.get("src")))
        if tag == "iframe" and not a.get("title"): self.tags.append(("iframe-sem-title", tag, a.get("src")))
        if tag in ("button", "a"):
            self.pilha.append([tag, a, ""])
        if tag in VOID and self.pilha and tag == "img" and a.get("alt"):
            self.pilha[-1][2] += a["alt"]
    def handle_endtag(self, tag):
        if tag == "title": self._in_title = False
        if tag == "script" and self._ld is not None: self.ld.append(self._ld); self._ld = None
        if tag in ("button", "a") and self.pilha and self.pilha[-1][0] == tag:
            t, a, txt = self.pilha.pop()
            nome = (a.get("aria-label") or a.get("title") or txt).strip()
            if not nome: self.tags.append(("sem-nome-acessivel", t, a.get("href") or a.get("class")))
            if self.pilha: self.pilha[-1][2] += txt
    def handle_data(self, data):
        if self._in_title: self.title += data
        if self._ld is not None: self._ld += data
        if self.pilha: self.pilha[-1][2] += data

BASE_URL = "https://site.invalid"
def url_da_pagina(pagina):
    """URL em que o arquivo é servido, com ROOT como raiz do servidor."""
    return BASE_URL + "/" + "/".join(quote(x) for x in os.path.relpath(pagina, ROOT).split(os.sep))

def alvo_local(pagina, url):
    """Resolve um link interno para (arquivo, fragmento) ou None se externo.

    Resolve com semântica de URL (como o navegador) e só depois mapeia para o disco:
    "../" acima da raiz é descartado, então "../mais-gesso-site/index.html" na home
    vira /mais-gesso-site/index.html, que não existe na raiz servida."""
    s = urlsplit(url)
    if s.scheme or url.startswith("//"): return None
    # pontos codificados (%2e) contam como "." para o navegador (WHATWG): normaliza antes do urljoin
    seg = "/".join(re.sub(r"^(?:%2e|\.)(?:%2e|\.)?$", lambda m: m.group(0).lower().replace("%2e", "."), x, flags=re.I) for x in s.path.split("/"))
    alvo = urlsplit(urljoin(url_da_pagina(pagina), urlunsplit(("", "", seg, s.query, s.fragment))))
    if not s.path: return pagina, s.fragment
    caminho = unquote(alvo.path)
    arq = os.path.normpath(os.path.join(ROOT, *[x for x in caminho.split("/") if x]))
    if caminho.endswith("/") or os.path.isdir(arq): arq = os.path.join(arq, "index.html")
    return arq, s.fragment

paginas = {}
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [x for x in dns if x not in SKIP_DIRS]
    for f in fns:
        if f.endswith(".html"):
            p = os.path.join(dp, f); pg = Pag(); txt = open(p, encoding="utf-8").read()
            pg.feed(txt); pg.close(); pg.raw = txt; paginas[p] = pg

if not paginas: E(".", "nenhuma página HTML encontrada");
usados = set()
robots_meta = {}
for p, pg in sorted(paginas.items()):
    r = rel(p)
    # metadados
    if pg.lang != "pt-BR": E(r, f"<html lang> deveria ser pt-BR (achou {pg.lang!r})")
    if not pg.title.strip(): E(r, "sem <title>")
    for m in ("description", "viewport", "robots", "og:title", "og:description", "og:image"):
        if not pg.meta.get(m): E(r, f"meta {m} ausente")
    robots_meta[p] = pg.meta.get("robots", "")
    if pg.h1 != 1: E(r, f"esperado 1 <h1>, achou {pg.h1}")
    dup = {i for i in pg.ids if pg.ids.count(i) > 1}
    if dup: E(r, f"ids duplicados: {sorted(dup)}")
    for kind, tag, extra in pg.tags: E(r, f"{kind} em <{tag}> ({extra})")
    if 'href="#"' in pg.raw: E(r, 'link vazio href="#"')
    # textos esquecidos (fora de JSON-LD também, pega tudo)
    for pat in PROIBIDOS:
        for m in re.finditer(pat, pg.raw):
            E(r, f"texto de placeholder esquecido: {m.group(0)!r} (use [pendente: …])"); break
    # JSON-LD
    for bloco in pg.ld:
        try: dado = json.loads(bloco)
        except Exception as ex: E(r, f"JSON-LD inválido: {ex}"); continue
        if re.search(r"pendente|placeholder", json.dumps(dado, ensure_ascii=False), re.I): E(r, "JSON-LD contém dado pendente/placeholder")
    # links e assets
    for tag, attr, url in pg.refs:
        url = url.strip()
        if url.lower().startswith("javascript:"): E(r, f"link javascript: em <{tag}>"); continue
        if url.startswith(("mailto:", "tel:", "data:")): continue
        if "wa.me" in url:
            if not WA_OK.match(url): E(r, f"link wa.me inválido/sem número real: {url[:80]}")
            continue
        if url.startswith("http://"): E(r, f"link inseguro (http): {url}")
        alvo = alvo_local(p, url)
        if alvo is None: continue
        arq, frag = alvo
        if not os.path.isfile(arq): E(r, f"<{tag} {attr}> quebrado: {url}"); continue
        usados.add(os.path.abspath(arq))
        if frag and arq.endswith(".html"):
            destino = paginas.get(os.path.abspath(arq))
            if destino and frag not in destino.ids: E(r, f"âncora inexistente: {url}")

# CSS: url(...)
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [x for x in dns if x not in SKIP_DIRS]
    for f in fns:
        if f.endswith(".css"):
            p = os.path.join(dp, f)
            for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", open(p, encoding="utf-8").read()):
                u = m.group(1)
                if u.startswith(("data:", "#")) or urlsplit(u).scheme: continue
                a = alvo_local(p, u)
                if a and not os.path.isfile(a[0]): E(rel(p), f"url() quebrado: {u}")
                elif a: usados.add(os.path.abspath(a[0]))

# assets órfãos (aviso)
adir = os.path.join(ROOT, "assets")
if os.path.isdir(adir):
    for f in sorted(os.listdir(adir)):
        if os.path.abspath(os.path.join(adir, f)) not in usados: W(f"assets/{f}", "não referenciado por nenhuma página")

# JS: sintaxe (se houver node)
if shutil.which("node"):
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [x for x in dns if x not in SKIP_DIRS]
        for f in fns:
            if f.endswith(".js"):
                p = os.path.join(dp, f); rc = subprocess.run(["node", "--check", p], capture_output=True, text=True)
                if rc.returncode: E(rel(p), "erro de sintaxe JS: " + rc.stderr.strip().splitlines()[-1])
else:
    W(".", "node não encontrado: sintaxe JS não conferida")

# robots × sitemap × meta robots
rob_p, sm_p = os.path.join(ROOT, "robots.txt"), os.path.join(ROOT, "sitemap.xml")
robots = open(rob_p, encoding="utf-8").read() if os.path.isfile(rob_p) else None
if robots is None: E("robots.txt", "ausente")
indexaveis = [p for p, m in robots_meta.items() if "noindex" not in m and not p.endswith("404.html")]
p404 = os.path.join(ROOT, "404.html")
if not os.path.isfile(p404): E("404.html", "ausente")
elif "noindex" not in robots_meta.get(p404, ""): E("404.html", "deveria ter noindex")
sm_linha = re.search(r"(?im)^\s*Sitemap:\s*(\S+)", robots or "")
if not indexaveis:
    if sm_linha: E("robots.txt", "site em noindex não deveria anunciar Sitemap")
    if os.path.isfile(sm_p): W("sitemap.xml", "existe, mas todas as páginas estão em noindex")
    if robots and re.search(r"(?im)^\s*Disallow:\s*/\s*$", robots): E("robots.txt", "Disallow: / impede os buscadores de lerem o noindex")
else:
    if not os.path.isfile(sm_p): E("sitemap.xml", "há páginas indexáveis e não há sitemap")
    if not sm_linha: E("robots.txt", "há páginas indexáveis e falta a linha Sitemap")
    if len(set(robots_meta.values()) - {""}) > 1 and any("noindex" in m for p, m in robots_meta.items() if not p.endswith("404.html")):
        E(".", "meta robots incoerente entre páginas")
if os.path.isfile(sm_p):
    locs = re.findall(r"<loc>([^<]+)</loc>", open(sm_p, encoding="utf-8").read())
    if not locs: E("sitemap.xml", "sem <loc>")
    for loc in locs:
        s = urlsplit(loc)
        if s.scheme != "https": E("sitemap.xml", f"URL não absoluta/https: {loc}"); continue
        arq = os.path.join(ROOT, s.path.lstrip("/")) if s.path not in ("", "/") else os.path.join(ROOT, "index.html")
        if not os.path.isfile(arq): E("sitemap.xml", f"aponta para arquivo inexistente: {loc}")
        elif "noindex" in robots_meta.get(os.path.abspath(arq), ""): E("sitemap.xml", f"lista página com noindex: {loc}")

print(f"Páginas: {len(paginas)} · links/assets conferidos · raiz {ROOT}")
for a in avisos: print("AVISO ", a)
for e in erros: print("ERRO  ", e)
print("RESULTADO:", "FALHOU" if erros else "OK", f"({len(erros)} erro(s), {len(avisos)} aviso(s))")
sys.exit(1 if erros else 0)
