#!/usr/bin/env python3
"""Teste de navegador (Playwright Python) em 390px e 1280px.

Uso: python3 scripts/e2e.py [pasta_de_prints]
Sobe um servidor HTTP local, bloqueia a rede externa (responde vazio para fontes/mapas)
e confere: regressões de build/check (sem navegador), 0 erros JS, sem overflow horizontal, focus trap/Esc/retorno de foco no menu,
seletor e gaveta, sanitização da lista no localStorage e a mensagem do WhatsApp.
"""
import functools, http.server, json, os, shutil, subprocess, sys, tempfile, threading, urllib.parse as up
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHOTS = sys.argv[1] if len(sys.argv) > 1 else None
PAGES = ["/index.html", "/produtos/gesso.html", "/produtos/drywall.html", "/produtos/piso-vinilico.html",
         "/produtos/parafusos.html", "/produtos/fitas.html", "/404.html"]
falhas, ok = [], []
def check(cond, msg):
    (ok if cond else falhas).append(msg)

# --- regressões de build/check (sem navegador), em pastas temporárias
PY = sys.executable
def roda(args, env=None):
    return subprocess.run([PY] + args, capture_output=True, text=True, env={**os.environ, **(env or {})})
TMP = tempfile.mkdtemp(prefix="mg-e2e-")
try:
    # 1) check.py resolve links como URL: "../<pasta>/index.html" na home sai da raiz servida.
    #    A cópia mantém o nome da pasta para que o caminho exista no disco (é o que enganava o check antigo).
    copia = os.path.join(TMP, os.path.basename(ROOT))
    shutil.copytree(ROOT, copia, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    rc0 = roda([os.path.join(ROOT, "scripts", "check.py"), copia])
    check(rc0.returncode == 0, f"check.py aprova a cópia intacta (exit {rc0.returncode})")
    ruim = f"../{os.path.basename(ROOT)}/index.html"
    check(os.path.isfile(os.path.normpath(os.path.join(copia, ruim))), f"pré-condição: {ruim} existe no disco a partir da raiz")
    ih = os.path.join(copia, "index.html"); txt = open(ih, encoding="utf-8").read()
    open(ih, "w", encoding="utf-8").write(txt.replace("</main>", f'<a href="{ruim}">volta</a></main>', 1))
    rc1 = roda([os.path.join(ROOT, "scripts", "check.py"), copia])
    check(rc1.returncode == 1 and f"quebrado: {ruim}" in rc1.stdout, f"check.py rejeita {ruim} (exit {rc1.returncode})")
    # 2) domínio com indexação desligada: sem sitemap (e remove um sitemap antigo), robots sem Sitemap, check OK.
    #    Também confere que MG_OUT numa pasta nova recebe os assets estáticos.
    out = os.path.join(TMP, "dominio-noindex"); os.makedirs(out)
    open(os.path.join(out, "sitemap.xml"), "w").write("<urlset></urlset>")
    rb = roda([os.path.join(ROOT, "build_site.py")], {"MG_OUT": out, "MG_DOMINIO": "https://www.exemplo.com.br", "MG_INDEXAR": "0"})
    check(rb.returncode == 0, f"build com MG_DOMINIO e MG_INDEXAR=0 roda (exit {rb.returncode}) {rb.stderr[-200:]}")
    check(not os.path.exists(os.path.join(out, "sitemap.xml")), "MG_DOMINIO + MG_INDEXAR=0: sem sitemap.xml (antigo removido)")
    rob = open(os.path.join(out, "robots.txt"), encoding="utf-8").read()
    check("Sitemap:" not in rob, "MG_DOMINIO + MG_INDEXAR=0: robots.txt sem linha Sitemap")
    falta = [f for f in os.listdir(os.path.join(ROOT, "assets")) if not os.path.isfile(os.path.join(out, "assets", f))]
    check(not falta, f"MG_OUT em pasta nova recebe todos os assets {falta or ''}")
    rc2 = roda([os.path.join(ROOT, "scripts", "check.py"), out])
    check(rc2.returncode == 0, f"check.py aprova saída MG_DOMINIO + MG_INDEXAR=0 (exit {rc2.returncode}) {rc2.stdout[-300:] if rc2.returncode else ''}")
    # 3) controle: com MG_INDEXAR=1 o sitemap existe, lista as 6 páginas e o check aprova.
    out2 = os.path.join(TMP, "dominio-index"); os.makedirs(out2)
    roda([os.path.join(ROOT, "build_site.py")], {"MG_OUT": out2, "MG_DOMINIO": "https://www.exemplo.com.br", "MG_INDEXAR": "1"})
    sm = os.path.join(out2, "sitemap.xml")
    check(os.path.isfile(sm) and open(sm, encoding="utf-8").read().count("<loc>") == 6, "MG_INDEXAR=1: sitemap com 6 URLs")
    rc3 = roda([os.path.join(ROOT, "scripts", "check.py"), out2])
    check(rc3.returncode == 0, f"check.py aprova saída indexável (exit {rc3.returncode})")
finally:
    shutil.rmtree(TMP, ignore_errors=True)

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_port}"

def rota(route):
    if route.request.url.startswith(BASE): route.continue_()
    else: route.fulfill(status=200, body="", content_type="text/html")

def foco(pg): return pg.evaluate("""()=>{const a=document.activeElement;return a?(a.id||a.getAttribute('data-pick')||a.className||a.tagName):null}""")
def foco_dentro(pg, sel): return pg.evaluate(f"()=>!!document.querySelector({json.dumps(sel)}).contains(document.activeElement)")

with sync_playwright() as p:
    br = p.chromium.launch()
    for w, h in [(390, 844), (1280, 800)]:
        ctx = br.new_context(viewport={"width": w, "height": h})
        ctx.route("**/*", rota)
        pg = ctx.new_page()
        erros = []
        pg.on("pageerror", lambda e: erros.append(f"pageerror: {e}"))
        pg.on("console", lambda m: erros.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        # --- todas as páginas: erros JS e overflow
        for path in PAGES:
            erros.clear()
            pg.goto(BASE + path); pg.wait_for_load_state("load"); pg.wait_for_timeout(150)
            ov = pg.evaluate("()=>({sw:document.documentElement.scrollWidth,iw:window.innerWidth,bw:document.body.scrollWidth})")
            check(ov["sw"] <= ov["iw"] and ov["bw"] <= ov["iw"], f"[{w}] {path} sem overflow horizontal ({ov})")
            check(not erros, f"[{w}] {path} 0 erros JS {erros or ''}")
            if SHOTS:
                os.makedirs(SHOTS, exist_ok=True)
                pg.screenshot(path=os.path.join(SHOTS, f"{path.strip('/').replace('/', '_')}-{w}.png"), full_page=True)
        # --- localStorage corrompido é saneado
        erros.clear()
        pg.goto(BASE + "/index.html")
        lixo = [None, "x", 42, {"n": "<img src=x onerror=window.__xss=1>", "q": 5}, {"n": "Fita telada", "q": "7"},
                {"n": "Fita telada", "q": 2}, {"n": "Gesso cola", "q": -3}, {"n": "Gesso cola ", "q": 1e9}, {"n": ["array"]}]
        pg.evaluate(f"()=>{{localStorage.setItem('mgCart',{json.dumps(json.dumps(lixo))});localStorage.setItem('mgStore','__proto__')}}")
        pg.reload(); pg.wait_for_timeout(150)
        salvo = pg.evaluate("()=>JSON.parse(localStorage.getItem('mgCart'))")
        check(salvo == [{"n": "Fita telada", "q": 7}, {"n": "Gesso cola", "q": 1}], f"[{w}] lista saneada e regravada: {salvo}")
        check(pg.evaluate("()=>localStorage.getItem('mgStore')") == "fabriciano", f"[{w}] loja inválida descartada")
        check(pg.evaluate("()=>!window.__xss && !document.querySelector('#cartlist img')"), f"[{w}] nomes renderizados como texto (sem HTML injetado)")
        pg.evaluate("()=>localStorage.setItem('mgCart','{nao json')"); pg.reload(); pg.wait_for_timeout(100)
        check(pg.evaluate("()=>localStorage.getItem('mgCart')") == "[]", f"[{w}] JSON inválido no localStorage vira lista vazia")
        many = [{"n": "Fita telada", "q": 1}] * 500
        pg.evaluate(f"()=>localStorage.setItem('mgCart',{json.dumps(json.dumps(many))})"); pg.reload(); pg.wait_for_timeout(100)
        check(pg.evaluate("()=>JSON.parse(localStorage.getItem('mgCart')).length") == 1, f"[{w}] duplicados removidos / limite de itens")
        pg.evaluate("()=>localStorage.clear()"); pg.reload(); pg.wait_for_timeout(100)
        # --- gaveta fechada não recebe foco
        check(pg.evaluate("()=>getComputedStyle(document.getElementById('drawer')).visibility") == "hidden", f"[{w}] gaveta fechada fora da tabulação")
        # --- seletor: abre, prende foco, Esc, devolve foco
        pg.click(".storechip")
        check(foco_dentro(pg, "#picker"), f"[{w}] seletor recebe o foco ao abrir")
        fora = []
        for k in ["Tab"] * 8 + ["Shift+Tab"] * 8:
            pg.keyboard.press(k)
            if not foco_dentro(pg, "#picker"): fora.append(f"{k}→{foco(pg)}")
        check(not fora, f"[{w}] Tab/Shift+Tab ficam presos no seletor a cada tecla {fora or ''}")
        pg.keyboard.press("Escape")
        check(not pg.evaluate("()=>document.body.classList.contains('pick')"), f"[{w}] Esc fecha o seletor")
        check("storechip" in (foco(pg) or ""), f"[{w}] foco volta ao botão da loja ({foco(pg)})")
        # --- adiciona itens, gaveta, diálogo aninhado
        pg.click("#painel-gesso .add >> nth=0")
        pg.click("#cartbtn")
        check(foco_dentro(pg, "#drawer"), f"[{w}] gaveta recebe o foco")
        fora = []
        for k in ["Tab"] * 12 + ["Shift+Tab"] * 12:
            pg.keyboard.press(k)
            if not foco_dentro(pg, "#drawer"): fora.append(f"{k}→{foco(pg)}")
        check(not fora, f"[{w}] Tab/Shift+Tab ficam presos na gaveta a cada tecla {fora or ''}")
        pg.click("#drawer [data-open-picker]")
        check(foco_dentro(pg, "#picker"), f"[{w}] 'trocar' abre o seletor por cima da gaveta")
        pg.keyboard.press("Escape")
        check(pg.evaluate("()=>document.body.classList.contains('cart') && !document.body.classList.contains('pick')"), f"[{w}] Esc fecha só o seletor")
        check(pg.evaluate("()=>document.activeElement.matches('#drawer [data-open-picker]')"), f"[{w}] foco volta ao 'trocar'")
        pg.keyboard.press("Escape")
        check(foco(pg) == "cartbtn", f"[{w}] Esc fecha a gaveta e foco volta ao botão Orçamento ({foco(pg)})")
        # --- loja sem dados: pendências visíveis + WhatsApp seguro
        pg.click("#lojas-pick [data-pick=ipatinga]"); pg.wait_for_timeout(100)
        check(pg.is_visible("#swarn") and pg.locator("#saddr .pend").count() == 1, f"[{w}] Ipatinga mostra [pendente] de endereço e aviso")
        href = pg.get_attribute("#swa", "href")
        check(href.startswith("https://wa.me/5531995224782?"), f"[{w}] WhatsApp de Ipatinga vai para a central (número real)")
        pg.click("#cartbtn")
        pg.fill("#cname", "Teste <b>")
        pg.evaluate("()=>{document.getElementById('cobs').value='x'.repeat(900)}")  # ignora maxlength para testar o corte no JS
        with pg.expect_popup() as pop: pg.click("#send")
        url = pop.value.url; pop.value.close()
        msg = up.unquote(up.urlsplit(url).query.split("text=", 1)[-1])
        check(url.startswith("https://wa.me/5531995224782?text=") and "loja de Ipatinga" in msg and "1x Placa de gesso 60x60" in msg and "Teste <b>" in msg,
              f"[{w}] mensagem do WhatsApp com loja e itens")
        check(len(msg.split("Obs.: ", 1)[-1]) <= 500, f"[{w}] observação truncada no limite")
        pg.keyboard.press("Escape")
        # --- abas por teclado
        pg.focus("#tab-gesso"); pg.keyboard.press("ArrowRight")
        check(pg.evaluate("()=>document.activeElement.id==='tab-drywall' && !document.getElementById('painel-drywall').hidden"), f"[{w}] abas navegáveis por seta")
        # --- menu móvel
        if w < 900:
            pg.click("[data-menu]")
            check(pg.get_attribute("[data-menu]", "aria-expanded") == "true" and foco_dentro(pg, "#nav"), f"[{w}] menu abre e foca o 1º link")
            # ciclo esperado: links do nav na ordem e o burger; o botão da loja (entre eles no DOM) fica de fora
            ciclo = pg.evaluate("()=>[...document.querySelectorAll('#nav a[href]')].map(a=>a.textContent.trim()).concat(['burger'])")
            def atual(): return pg.evaluate("()=>{const a=document.activeElement;return a.matches('[data-menu]')?'burger':(document.getElementById('nav').contains(a)?a.textContent.trim():'FORA:'+(a.className||a.tagName))}")
            n, pos, erradas = len(ciclo), 0, []
            for k in ["Tab"] * (2 * n) + ["Shift+Tab"] * (2 * n):
                pg.keyboard.press(k); pos = (pos + (1 if k == "Tab" else -1)) % n
                if atual() != ciclo[pos]: erradas.append(f"{k}: esperado {ciclo[pos]}, foco em {atual()}")
            check(not erradas and n == 5, f"[{w}] menu: foco correto a cada Tab/Shift+Tab ({n} itens) {erradas[:3] or ''}")
            pg.keyboard.press("Escape")
            check(pg.get_attribute("[data-menu]", "aria-expanded") == "false" and foco(pg) and "burger" in foco(pg), f"[{w}] Esc fecha o menu e devolve foco")
        check(not erros, f"[{w}] interações sem erro JS {erros or ''}")
        ctx.close()
    br.close()
srv.shutdown()
for m in ok: print("OK   ", m)
for m in falhas: print("FALHA", m)
print(f"RESULTADO: {'FALHOU' if falhas else 'OK'} ({len(ok)} ok, {len(falhas)} falha(s))")
sys.exit(1 if falhas else 0)
