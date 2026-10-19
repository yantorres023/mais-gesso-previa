"""Gera o site estático Mais Gesso — v2 (Proposta 3 revisada para apresentação ao cliente).

Uso:  python3 build_site.py            (gera na pasta deste arquivo)
      MG_OUT=/tmp/x python3 build_site.py
      MG_DOMINIO=https://www.exemplo.com.br MG_INDEXAR=1 python3 build_site.py

Regra de dados: nada inventado. Dado que falta vira marcador visível [pendente: …]
(classe .pend) e fica fora do JSON-LD. Para preencher, edite LOJAS / CONTATO abaixo.
"""
import html, json, os, urllib.parse as u

OUT = os.environ.get("MG_OUT") or os.path.dirname(os.path.abspath(__file__))
# Domínio ainda não confirmado pelo cliente: sem domínio não há canonical nem og:url; sitemap só com INDEXAR.
DOMINIO = (os.environ.get("MG_DOMINIO") or "").rstrip("/")
# Só liga a indexação quando o site estiver publicado no domínio definitivo.
INDEXAR = bool(DOMINIO) and os.environ.get("MG_INDEXAR") == "1"
HOJE = "2026-10-16"

def esc(t): return html.escape(str(t), quote=True)
# v2: por padrão o site sai "limpo" para o cliente. Dado que falta vira um texto alternativo honesto
# (ex.: "Horário: consulte pelo WhatsApp") ou some. MG_PENDENTES=1 volta a mostrar os marcadores [pendente: …].
PEND = os.environ.get("MG_PENDENTES") == "1"
PREVIA = os.environ.get("MG_PREVIA", "1") == "1"   # faixa "prévia para aprovação"
BASE = os.environ.get("MG_BASE", "/")              # raiz no servidor (GitHub Pages de projeto: /nome-do-repo/)
def P(t, alt=""):
  if PEND: return f'<span class="pend">[pendente: {esc(t)}]</span>'
  return f'<span class="soon">{esc(alt)}</span>' if alt else ""

# ---------------------------------------------------------------- dados reais / pendentes
CENTRAL = "5531995224782"; CENTRAL_TXT = "(31) 99522-4782"   # número já usado pela loja de Coronel Fabriciano
IGU = "https://www.instagram.com/maisgessodistribuidora"
CONTATO = dict(email=None, cnpj=None)  # pendentes
LOJAS = [
  dict(id="fabriciano", n="Coronel Fabriciano", rua="Av. Presidente Tancredo de Almeida Neves, 3664", bairro="Caladinho",
       wa=CENTRAL, wa_proprio=True, horario=None, geo=[-19.52, -42.62]),
  dict(id="ipatinga", n="Ipatinga", rua=None, bairro=None, wa=CENTRAL, wa_proprio=False, horario=None, geo=[-19.47, -42.54]),
  dict(id="bh", n="Belo Horizonte", rua=None, bairro=None, wa=CENTRAL, wa_proprio=False, horario=None, geo=[-19.92, -43.94]),
]
for s in LOJAS:
  s["ok"] = bool(s["rua"])
  s["addr"] = f'{s["rua"]} – {s["bairro"]}, {s["n"]} - MG' if s["ok"] else ""
  s["addr_pend"] = "" if s["ok"] else (f'endereço da loja de {s["n"]}' if PEND else "Endereço e atendimento pelo WhatsApp")
  s["addr_html"] = esc(s["addr"]) if s["ok"] else P(f'endereço da loja de {s["n"]}', "Endereço e atendimento pelo WhatsApp")
  s["h_pend"] = "horário de funcionamento" if PEND else "Horário: consulte pelo WhatsApp"
  s["h_html"] = esc(s["horario"]) if s["horario"] else P("horário de funcionamento", "Horário: consulte pelo WhatsApp")
  s["c"] = {"fabriciano": "Fabriciano", "ipatinga": "Ipatinga", "bh": "BH"}[s["id"]]
  busca = "Mais Gesso Distribuidora " + (s["addr"] if s["ok"] else s["n"] + " MG")
  # Sem endereço confirmado o mapa mostra só a cidade, para não apontar um local errado.
  s["emb"] = ("https://maps.google.com/maps?q=" + u.quote(s["addr"] if s["ok"] else s["n"] + " - MG") + "&z=15&output=embed") if (s["ok"] or PEND) else ""
  s["lnk"] = "https://www.google.com/maps/search/?api=1&query=" + u.quote(busca)
  s["wa_pend"] = "" if (s["wa_proprio"] or not PEND) else f'WhatsApp da loja de {s["n"]} — por enquanto vai para a central {CENTRAL_TXT}'

def wa(store, txt=""):
  return f"https://wa.me/{CENTRAL}?text=" + u.quote(f"Olá, Mais Gesso! Gostaria de um orçamento na loja de {store}. {txt}".strip())
def wa_loja(s, txt=""):
  return f"https://wa.me/{s['wa']}?text=" + u.quote(f"Olá, Mais Gesso! Gostaria de um orçamento na loja de {s['n']}. {txt}".strip())

C = [("gesso","Gesso","Placas, gesso em pó, sancas e acabamento","M4 20h16M6 20V9l6-5 6 5v11",["Placa de gesso 60x60","Gesso em pó (saco)","Gesso cola","Sanca de gesso","Moldura de gesso","Massa para acabamento"]),
("drywall","Drywall","Chapas ST, RU, RF, perfis e massas","M3 4h18v16H3zM9 4v16M15 4v16",["Chapa drywall ST","Chapa drywall RU (verde)","Chapa drywall RF (rosa)","Perfil montante","Perfil guia","Massa para drywall"]),
("piso-vinilico","Piso Vinílico","Réguas, mantas, rodapés e acessórios","M3 3h8v8H3zM13 13h8v8h-8zM13 3h8v8h-8zM3 13h8v8H3z",["Piso vinílico em régua","Piso vinílico clicado","Manta vinílica","Rodapé","Cola para piso vinílico","Perfil de acabamento"]),
("parafusos","Parafusos","Fixação para drywall, steel frame e forro","M12 2v20M8 6h8M8 10h8M8 14h8M8 18h8",["Parafuso GN25 (drywall)","Parafuso metal-metal","Parafuso ponta broca","Bucha e parafuso","Pino para fixação","Arame galvanizado"]),
("fitas","Fitas","Fitas telada, papel, reforço e isolamento","M4 12a8 8 0 1016 0 8 8 0 10-16 0M9 12a3 3 0 106 0 3 3 0 10-6 0",["Fita telada","Fita de papel microperfurada","Fita de reforço metálica","Fita banda acústica","Fita crepe","Cantoneira de papel"])]
ITENS = [p for c in C for p in c[4]]
# descrições curtas de uso (genéricas, sem medida nem marca inventada)
DESC = {"Placa de gesso 60x60":"Para forro de gesso tradicional.","Gesso em pó (saco)":"Revestimento, assentamento e reparos.","Gesso cola":"Cola placas, sancas e molduras.",
 "Sanca de gesso":"Acabamento entre teto e parede.","Moldura de gesso":"Detalhe decorativo para teto e parede.","Massa para acabamento":"Deixa a superfície lisa para pintar.",
 "Chapa drywall ST":"Uso geral em áreas secas.","Chapa drywall RU (verde)":"Resiste à umidade: banheiro e cozinha.","Chapa drywall RF (rosa)":"Resiste ao fogo: áreas técnicas.",
 "Perfil montante":"Estrutura vertical da parede.","Perfil guia":"Fixa a estrutura no piso e no teto.","Massa para drywall":"Tratamento das juntas entre chapas.",
 "Piso vinílico em régua":"Réguas com aparência de madeira.","Piso vinílico clicado":"Encaixe sem cola, instala mais rápido.","Manta vinílica":"Rolo contínuo para áreas amplas.",
 "Rodapé":"Acabamento entre piso e parede.","Cola para piso vinílico":"Fixa réguas e mantas coladas.","Perfil de acabamento":"Transição entre ambientes.",
 "Parafuso GN25 (drywall)":"Fixa as chapas nos perfis.","Parafuso metal-metal":"Une os perfis da estrutura.","Parafuso ponta broca":"Para perfis de chapa mais grossa.",
 "Bucha e parafuso":"Fixação em alvenaria e concreto.","Pino para fixação":"Fixa guias em laje e piso.","Arame galvanizado":"Sustentação de forros.",
 "Fita telada":"Reforça as juntas antes da massa.","Fita de papel microperfurada":"Tratamento de juntas de drywall.","Fita de reforço metálica":"Protege cantos e quinas.",
 "Fita banda acústica":"Isola a estrutura e reduz ruído.","Fita crepe":"Proteção e marcação na obra.","Cantoneira de papel":"Acabamento de cantos."}
# cor da amostra de cada item (ilustração no lugar da foto)
TINT = {"Chapa drywall RU (verde)":"#7fa98a","Chapa drywall RF (rosa)":"#d9a3ad","Piso vinílico clicado":"#a7774c","Manta vinílica":"#8f6b4c","Rodapé":"#e9e6e1"}

def ic(p,s=40,c="currentColor"): return f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" aria-hidden="true" focusable="false"><path d="{p}"/></svg>'
WA='<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 2a10 10 0 00-8.6 15.1L2 22l5-1.3A10 10 0 1012 2zm5.3 14.2c-.2.6-1.3 1.2-1.8 1.2s-1 .3-3.4-.7-3.9-3.5-4-3.7-1-1.3-1-2.5.6-1.8.9-2 .5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.4.6c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3.1.2.1.7-.1 1.2z"/></svg>'
IG='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>'
TRUCK="M1 6h13v10H1zM14 9h5l4 4v3h-9M5 19a2 2 0 100-4 2 2 0 000 4M18 19a2 2 0 100-4 2 2 0 000 4"
def A(t): return f'<span aria-hidden="true">{t}</span>'
PIN = "M12 22s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12zM12 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5"
ARR = "M5 12h14M13 6l6 6-6 6"
GEO = "M12 2v3M12 19v3M2 12h3M19 12h3M12 17a5 5 0 100-10 5 5 0 000 10M12 13a1 1 0 100-2 1 1 0 000 2"
BOX = "M3 7l9-4 9 4-9 4-9-4zM3 7v10l9 4 9-4V7M12 11v10"
MAPI = "M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14"
CLOCK = "M12 21a9 9 0 100-18 9 9 0 000 18zM12 7v5l3 2"

# FAQ: (pergunta, resposta_html, confirmada). Só as confirmadas vão para o JSON-LD.
FAQ=[("Vocês entregam fora de Minas Gerais?","Sim. Entregamos para todo o Brasil. Envie sua lista pelo WhatsApp com o CEP da obra e calculamos o frete.",True),
("Como peço um orçamento?","Escolha sua loja, adicione os produtos à lista de orçamento e toque em “Enviar pelo WhatsApp”. A mensagem já vai pronta para a loja escolhida.",True),
("Vocês atendem gesseiros, construtoras e lojistas?","Sim, atendemos profissionais e consumidores finais. "+(P("condições para compras em volume") if PEND else "Para compras em volume, peça as condições pelo WhatsApp."),False),
("Quais formas de pagamento?",P("formas de pagamento aceitas") if PEND else "A loja informa as formas de pagamento junto com o orçamento, pelo WhatsApp.",False),
("Qual o horário das lojas?",P("horário de funcionamento de cada loja") if PEND else "Chame a loja mais próxima pelo WhatsApp para confirmar o horário do dia.",False),
("Posso retirar na loja?",P("se há retirada na loja e em quais unidades") if PEND else "Combine a retirada com a loja ao fechar o orçamento pelo WhatsApp.",False)]

# ---------------------------------------------------------------- JSON-LD
def ref(frag): return f"{DOMINIO}/#{frag}" if DOMINIO else f"#{frag}"
def ld_store(s):
  d={"@type":"HardwareStore","@id":ref(s["id"]),"name":f"Mais Gesso Distribuidora – {s['n']}","parentOrganization":{"@id":ref("org")},
     "areaServed":[{"@type":"City","name":s["n"]},{"@type":"Country","name":"Brasil"}],"hasMap":s["lnk"],
     "address":{"@type":"PostalAddress","addressLocality":s["n"],"addressRegion":"MG","addressCountry":"BR"}}
  if s["ok"]: d["address"]["streetAddress"]=f"{s['rua']} – {s['bairro']}"
  if s["wa_proprio"]: d["telephone"]="+"+s["wa"]
  if DOMINIO: d["url"]=f"{DOMINIO}/#loja-{s['id']}"; d["image"]=f"{DOMINIO}/assets/og-image.png"
  return d
ORG={"@type":"Organization","@id":ref("org"),"name":"Mais Gesso Distribuidora","slogan":"Drywall no ponto, obra no prazo.","sameAs":[IGU],
     "contactPoint":{"@type":"ContactPoint","telephone":"+"+CENTRAL,"contactType":"sales","areaServed":"BR","availableLanguage":"pt-BR"}}
if DOMINIO: ORG.update(url=DOMINIO+"/")
LD={"@context":"https://schema.org","@graph":[ORG]+[ld_store(s) for s in LOJAS]+
 [{"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a,ok in FAQ if ok]}]}

# ---------------------------------------------------------------- partes
def head(title,desc,path,ld,root=""):
  canon = f'<link rel="canonical" href="{DOMINIO}{path}"><meta property="og:url" content="{DOMINIO}{path}">' if DOMINIO else ""
  ogimg = (DOMINIO + "/" if DOMINIO else root) + "assets/og-image.png"
  robots = "index,follow" if INDEXAR else "noindex,follow"
  ldjs = json.dumps(ld,ensure_ascii=False).replace("</","<\\/") if ld else ""
  ldtag = f'<script type="application/ld+json">{ldjs}</script>' if ld else ""
  return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}">{canon}<meta name="theme-color" content="#1E2124"><meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="Mais Gesso Distribuidora"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{ogimg}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Mais Gesso Distribuidora: drywall no ponto, obra no prazo.">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="geo.region" content="BR-MG"><meta name="geo.placename" content="Coronel Fabriciano; Ipatinga; Belo Horizonte">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Bebas+Neue&display=swap" rel="stylesheet"><link rel="stylesheet" href="{root}assets/style.css">
{ldtag}</head><body>'''
LOGO='<span class="logo-ph"><svg class="lm" viewBox="0 0 80 80" aria-hidden="true" focusable="false"><rect width="80" height="80" rx="6" fill="#D7262E"/><path d="M28 12h24v16h16v24H52v16H28V52H12V28h16z" fill="#fff"/></svg><span><b>MAIS GESSO</b><small>DISTRIBUIDORA</small></span></span>'
def opt_btn(s):
  return f'<button type="button" class="opt" data-pick="{s["id"]}" aria-pressed="false"><span>{esc(s["n"])}<small>{s["addr_html"]}</small></span>{ic(ARR,22)}</button>'
def header(root=""):
  previa = '<div class="previa">Prévia para aprovação · versão de demonstração</div>' if PREVIA else ""
  return f'''<a class="skip" href="#main">Pular para o conteúdo</a>{previa}<header class="top"><a href="{root}index.html" aria-label="Mais Gesso – início">{LOGO}</a>
<nav id="nav" aria-label="Principal"><a href="{root}index.html#lojas">Lojas</a><a href="{root}index.html#produtos">Produtos</a><a href="{root}index.html#entrega">Entregas</a><a href="{root}index.html#faq">Dúvidas</a></nav>
<button type="button" class="storechip" data-open-picker aria-haspopup="dialog">{ic(PIN,18)} <span class="sr-only">Loja: </span><span data-store-short>Escolha a loja</span></button><button type="button" class="burger" aria-label="Abrir menu" aria-expanded="false" aria-controls="nav" data-menu>{A("☰")}</button></header><div class="hz" aria-hidden="true"></div>'''
def cart_ui():
  return f'''<button type="button" class="cartbtn" id="cartbtn" aria-label="Abrir lista de orçamento" aria-haspopup="dialog" aria-controls="drawer">{WA}<span>Orçamento</span><b id="cartn">0</b></button>
<aside class="drawer" id="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-t" aria-hidden="true" tabindex="-1"><div class="dh"><h2 id="drawer-t">Lista de orçamento</h2><button type="button" data-close-cart aria-label="Fechar lista de orçamento">{A("✕")}</button></div>
<p class="dstore">Loja: <b data-store-name>—</b> <button type="button" class="lnk" data-open-picker aria-haspopup="dialog">trocar</button></p><ul id="cartlist" aria-live="polite"></ul>
<label class="fld">Nome<input id="cname" name="nome" autocomplete="name" maxlength="80" placeholder="Seu nome"></label><label class="fld">CEP / cidade da entrega (opcional)<input id="ccep" name="entrega" autocomplete="postal-code" maxlength="60" placeholder="Ex.: 35170-000"></label><label class="fld">Observações<textarea id="cobs" name="obs" rows="2" maxlength="500" placeholder="Medidas, quantidades, prazo..."></textarea></label>
<button type="button" class="big" id="send">{WA} Enviar pelo WhatsApp</button><p class="tiny" id="cwarn" hidden>{P("WhatsApp próprio de Ipatinga e BH — por enquanto a mensagem vai para a central " + CENTRAL_TXT)}</p></aside><div class="scrim" data-close-cart aria-hidden="true"></div>
<div class="picker" id="picker" role="dialog" aria-modal="true" aria-labelledby="picker-t"><div class="pbox"><h2 id="picker-t">Qual loja fica mais perto?</h2>{"".join(opt_btn(s) for s in LOJAS)}<button type="button" class="lnk" data-close-picker>Fechar</button></div></div>'''
def footer(root=""):
  email = (f'<p>E-mail: {esc(CONTATO["email"]) if CONTATO["email"] else P("e-mail")}</p>') if (CONTATO["email"] or PEND) else ""
  cnpj = (f'<p>CNPJ: {esc(CONTATO["cnpj"]) if CONTATO["cnpj"] else P("CNPJ")}</p>') if (CONTATO["cnpj"] or PEND) else ""
  logo_pend = f'<p>{P("logo oficial em vetor — marca acima recriada a partir do brand kit")}</p>' if PEND else ""
  return f'''<footer class="foot"><div class="fg"><div>{LOGO}{logo_pend}<p>Distribuidora de materiais para construção a seco: gesso, drywall, piso vinílico, parafusos e fitas. Entregamos para todo o Brasil.</p><a class="iglink" href="{IGU}" rel="noopener">{IG} @maisgessodistribuidora</a></div>
<div><h2>Lojas</h2>{"".join(f'<p><b>{esc(s["n"])}</b><br>{s["addr_html"]}<br>{s["h_html"]}</p>' for s in LOJAS)}</div><div><h2>Produtos</h2>{"".join(f'<a href="{root}produtos/{c[0]}.html">{c[1]}</a>' for c in C)}</div>
<div><h2>Contato</h2><p>WhatsApp: <a href="https://wa.me/{CENTRAL}" rel="noopener">{CENTRAL_TXT}</a></p>{email}{cnpj}</div></div><p class="copy">© 2026 Mais Gesso Distribuidora · Coronel Fabriciano · Ipatinga · Belo Horizonte – MG</p></footer>'''
def prod_cards(c,h="h4"):
  def ph(p):
    tint = f' style="--t:{TINT[p]}"' if p in TINT else ""
    tag = f'<small>{P("foto real")}</small>' if PEND else ""
    return f'<div class="ph ph-{c[0]}"{tint}><span class="sw" aria-hidden="true"></span>{ic(c[3],44)}{tag}</div>'
  def ds(p): return P("especificações e medidas") if PEND else esc(DESC.get(p, ""))
  return "".join(f'<article class="pc">{ph(p)}<div class="pb"><span class="tag">{c[1]}</span><{h}>{esc(p)}</{h}><p class="tiny">{ds(p)}</p><button type="button" class="add" data-item="{esc(p)}" aria-pressed="false">+ Adicionar ao orçamento</button></div></article>' for p in c[4])
def store_map(s):
  if s["emb"]: return f'<iframe title="Mapa – {esc(s["n"])}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="{s["emb"]}"></iframe>'
  return f'<div class="nomap">{ic(PIN,46)}<b>{esc(s["n"])}</b><span>Peça a localização pelo WhatsApp</span></div>'
REELS = [("reel1-forro-pvc","capa-reel1","Forro PVC: branco ou amadeirado"),("reel2-piso-vinilico","capa-reel2","Piso vinílico Ecomex"),("reel3-entrega","capa-reel3","Do estoque pra sua obra")]
DICAS = [("post1-drywall-x-alvenaria","Dica: drywall ou alvenaria"),("post2-checklist-forro-drywall","Dica: o que comprar para forro de drywall"),("post3-calculo-piso","Dica: quantos metros de piso comprar")]
def midia():
  rs = "".join(f'<figure class="reel"><video src="assets/midia/{v}.mp4" poster="assets/midia/{c}.png" controls playsinline preload="none"></video><figcaption>{t}</figcaption></figure>' for v,c,t in REELS)
  ds = "".join(f'<a class="dica" href="assets/midia/{f}.png" rel="noopener"><img src="assets/midia/{f}.png" alt="{a}" loading="lazy" width="1080" height="1350"></a>' for f,a in DICAS)
  return f'<div class="reels">{rs}</div><div class="dicas">{ds}</div>'
def scripts(r): return f'<script src="{r}assets/mg-data.js"></script><script src="{r}assets/app.js"></script>'
def page_end(root): return footer(root)+cart_ui()+scripts(root)+"</body></html>"

# MG_OUT em outra pasta: leva junto os assets estáticos (CSS, JS, ícones, imagens).
# mg-data.js é gerado abaixo, então não é copiado.
SRC = os.path.dirname(os.path.abspath(__file__))
if os.path.abspath(OUT) != SRC:
  import shutil
  os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
  for f in sorted(os.listdir(os.path.join(SRC, "assets"))):
    if f != "mg-data.js" and os.path.isfile(os.path.join(SRC, "assets", f)):
      shutil.copy2(os.path.join(SRC, "assets", f), os.path.join(OUT, "assets", f))

def write(rel, content):
  path = os.path.join(OUT, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "w", encoding="utf-8") as f: f.write(content)

# ---------------------------------------------------------------- dados para o app.js (sem HTML: o JS usa textContent)
STJS={s["id"]:dict(n=s["n"],c=s["c"],addr=s["addr"],addrPend=s["addr_pend"],h=s["horario"] or "",hPend=s["h_pend"],emb=s["emb"],lnk=s["lnk"],wa=s["wa"],waPend=s["wa_pend"],ok=s["ok"],geo=s["geo"]) for s in LOJAS}
write("assets/mg-data.js", "/* Gerado por build_site.py — não editar à mão. */\nwindow.MG_PENDENTES="+("true" if PEND else "false")+";\nwindow.MG_STORES="+json.dumps(STJS,ensure_ascii=False)+";\nwindow.MG_ITEMS="+json.dumps(ITENS,ensure_ascii=False)+";\n")

s0 = LOJAS[0]
# ---------------------------------------------------------------- index
idx=head("Mais Gesso Distribuidora | Gesso, Drywall e Piso Vinílico em Coronel Fabriciano, Ipatinga e BH",
 "Gesso, drywall, piso vinílico, parafusos e fitas. Lojas em Coronel Fabriciano, Ipatinga e Belo Horizonte (MG). Orçamento rápido pelo WhatsApp e entrega para todo o Brasil.","/",LD)+header()+f'''<main id="main">
<section class="hero"><div><p class="kick">Distribuidora · Construção a seco</p><h1>Construção a seco.<br><em>Perto de você.</em></h1><p class="slogan">Drywall no ponto, <em>obra no prazo.</em></p><p class="lead">Gesso, drywall, piso vinílico, parafusos e fitas. 3 lojas em MG, entrega para todo o Brasil. Escolha a loja, monte a lista, chame no WhatsApp.</p>
<div class="stats"><div><b>3</b>lojas em MG</div><div><b>5</b>linhas de produto</div><div><b>BR</b>entrega nacional</div></div></div>
<div class="opts" id="lojas-pick" role="group" aria-labelledby="pick-t"><p class="kick" id="pick-t">1. Escolha sua loja</p>{"".join(opt_btn(s) for s in LOJAS)}<button type="button" class="lnk geo" id="geo">{ic(GEO,18)} Usar minha localização</button></div></section>
<section class="panel" id="sua-loja" aria-labelledby="sua-loja-t"><div class="info"><p class="kick dark">Sua loja</p><h2 id="sua-loja-t" data-store-name>{s0["n"]}</h2><p id="saddr">{s0["addr_html"]}</p><p class="tiny" id="shours">{s0["h_html"]}</p>
<a class="big" id="swa" href="{wa_loja(s0)}" rel="noopener">{WA} Precisou, chamou</a><div class="row"><a class="ghost" id="slnk" href="{s0["lnk"]}" rel="noopener">Como chegar {A("→")}</a><a class="ghost" href="#produtos">Ver produtos {A("↓")}</a></div><p class="warn" id="swarn" hidden>{A("⚠")} {P("endereço, horário e WhatsApp desta loja — por enquanto o WhatsApp vai para a central " + CENTRAL_TXT)}</p></div>
<div class="map"><div class="nomap" id="snomap" hidden>{ic(PIN,46)}<b data-store-name></b><span>Peça a localização pelo WhatsApp</span></div><iframe id="smap" title="Mapa da loja selecionada" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="{s0["emb"]}"></iframe></div></section>
<section class="how" aria-labelledby="how-t"><h2 class="s" id="how-t">Orçamento em <span>3 passos</span></h2><ol class="steps"><li><b>01</b>Escolha a loja mais próxima</li><li><b>02</b>Adicione os produtos à lista</li><li><b>03</b>Envie pelo WhatsApp e receba o orçamento</li></ol></section>
<section id="produtos" aria-labelledby="produtos-t"><h2 class="s" id="produtos-t">Produtos <span data-store-in></span></h2><div class="tabs" role="tablist" aria-label="Linhas de produto">{"".join(f'<button type="button" class="tab{" on" if i==0 else ""}" role="tab" id="tab-{c[0]}" aria-controls="painel-{c[0]}" aria-selected="{"true" if i==0 else "false"}" tabindex="{0 if i==0 else -1}" data-tab="{c[0]}">{ic(c[3],22)}{c[1]}</button>' for i,c in enumerate(C))}</div>
{"".join(f'<div class="tabp" role="tabpanel" id="painel-{c[0]}" aria-labelledby="tab-{c[0]}" data-panel="{c[0]}"{"" if i==0 else " hidden"}><div class="ch"><div><h3 class="ct">{c[1]}</h3><p>{c[2]}</p></div><a class="ghost dk" href="produtos/{c[0]}.html">Ver página de {c[1]} {A("→")}</a></div><div class="grid">{prod_cards(c)}</div></div>' for i,c in enumerate(C))}</section>
<section class="br" id="entrega" aria-labelledby="entrega-t"><div class="bw">{ic(TRUCK,80,"#fff")}<div><h2 id="entrega-t">Entregamos para<br>todo o Brasil</h2><p>Longe das lojas? Sem problema. Mande a lista e o CEP da obra: o frete sai no orçamento, para qualquer estado.</p><a class="big wht" href="{wa("Coronel Fabriciano","Preciso de entrega para outro estado. CEP: ")}" rel="noopener">{WA} Consultar frete</a></div></div>
<ul class="perks"><li>{ic(TRUCK,22)} Entrega na obra</li><li>{ic(BOX,22)} Pedidos de volume</li><li>{ic(MAPI,22)} Todo o território nacional</li><li>{ic(CLOCK,22)} Prazo informado no orçamento</li></ul></section><div class="hz" aria-hidden="true"></div>
<section id="lojas" aria-labelledby="lojas-t"><h2 class="s" id="lojas-t">Nossas <span>lojas</span></h2><div class="stores">{"".join(f'<article class="store" id="loja-{s["id"]}">{store_map(s)}<div class="sb"><h3>{esc(s["n"])}</h3><p>{s["addr_html"]}</p><p class="tiny">{s["h_html"]}</p>{"" if not s["wa_pend"] else f'<p class="warn">{A("⚠")} {P(s["wa_pend"])}</p>'}<div class="row"><a class="ghost dk" href="{s["lnk"]}" rel="noopener">Como chegar</a><a class="ghost wa" href="{wa_loja(s)}" rel="noopener">{WA} WhatsApp</a></div></div></article>' for s in LOJAS)}</div></section>
<section id="instagram" aria-labelledby="ig-t"><h2 class="s" id="ig-t">Mais Gesso <span>Resolve</span></h2><p class="sp">Dica rápida de obra, toda semana no @maisgessodistribuidora.</p>{midia()}<a class="ghost big2" href="{IGU}" rel="noopener">{IG} Seguir no Instagram</a></section>
<section id="faq" aria-labelledby="faq-t"><h2 class="s" id="faq-t">Perguntas <span>frequentes</span></h2><div class="faq">{"".join(f'<details><summary>{esc(q)}</summary><p>{a}</p></details>' for q,a,_ in FAQ)}</div></section></main>'''+page_end("")
write("index.html", idx)

# ---------------------------------------------------------------- categorias
for c in C:
  crumbs=[{"@type":"ListItem","position":1,"name":"Início"},{"@type":"ListItem","position":2,"name":c[1]}]
  if DOMINIO: crumbs[0]["item"]=DOMINIO+"/"; crumbs[1]["item"]=f"{DOMINIO}/produtos/{c[0]}.html"
  ld={"@context":"https://schema.org","@graph":[{"@type":"BreadcrumbList","itemListElement":crumbs},
   {"@type":"ItemList","name":f"{c[1]} – Mais Gesso","itemListElement":[{"@type":"ListItem","position":i+1,"name":p} for i,p in enumerate(c[4])]}]}
  pg=head(f"{c[1]} em Coronel Fabriciano, Ipatinga e BH | Mais Gesso Distribuidora",f"{c[1]}: {c[2].lower()}. Orçamento pelo WhatsApp nas lojas de Coronel Fabriciano, Ipatinga e Belo Horizonte, com entrega para todo o Brasil.",f"/produtos/{c[0]}.html",ld,"../")+header("../")+f'''<main id="main">
<section class="hero sm"><div><p class="kick"><a href="../index.html">Início</a> / <a href="../index.html#produtos">Produtos</a></p><h1>{c[1]}</h1><p class="lead">{c[2]}. {P("texto da linha e marcas trabalhadas") if PEND else "Monte a lista e receba o orçamento pelo WhatsApp da loja mais perto."}</p></div><div class="bigic">{ic(c[3],160,"#D7262E")}</div></section>
<section aria-labelledby="linha-t"><h2 class="s" id="linha-t">Linha de <span>{c[1]}</span> <span class="sub" data-store-in></span></h2><div class="grid">{prod_cards(c,"h3")}</div></section>
<section class="br" aria-labelledby="entrega-t"><div class="bw">{ic(TRUCK,70,"#fff")}<div><h2 id="entrega-t">Entregamos {c[1].lower()} para todo o Brasil</h2><p>Monte sua lista e envie pelo WhatsApp da loja escolhida.</p></div></div></section>
<section aria-labelledby="outras-t"><h2 class="s" id="outras-t">Outras <span>linhas</span></h2><div class="cats">{"".join(f'<a class="cat" href="{o[0]}.html">{ic(o[3],34)}{o[1]}<small>{o[2]}</small></a>' for o in C if o[0]!=c[0])}</div></section></main>'''+page_end("../")
  write(f"produtos/{c[0]}.html", pg)

# ---------------------------------------------------------------- 404 (caminhos absolutos: o servidor entrega em qualquer URL)
nf=head("Página não encontrada | Mais Gesso Distribuidora","A página procurada não existe ou mudou de endereço.","/404.html",None,BASE)
nf=nf.replace('<meta name="robots" content="index,follow">','<meta name="robots" content="noindex,follow">')
nf+=header(BASE)+f'''<main id="main">
<section class="hero sm"><div><p class="kick">Erro 404</p><h1>Página não encontrada</h1><p class="lead">O endereço pode ter mudado. Volte ao início para escolher sua loja ou vá direto a uma linha de produto.</p><div class="row"><a class="ghost" href="{BASE}index.html">Ir para o início {A("→")}</a><a class="ghost" href="{BASE}index.html#lojas">Ver lojas {A("→")}</a></div></div><div class="bigic">{ic("M4 20h16M6 20V9l6-5 6 5v11",160,"#D7262E")}</div></section>
<section aria-labelledby="linhas-t"><h2 class="s" id="linhas-t">Nossas <span>linhas</span></h2><div class="cats c6">{"".join(f'<a class="cat" href="{BASE}produtos/{o[0]}.html">{ic(o[3],34)}{o[1]}<small>{o[2]}</small></a>' for o in C)}<a class="cat" href="{BASE}index.html#lojas">{ic("M12 22s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12zM12 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5",34)}Lojas<small>Coronel Fabriciano, Ipatinga e Belo Horizonte</small></a></div></section></main>'''+page_end(BASE)
write("404.html", nf)

# ---------------------------------------------------------------- robots / sitemap coerentes com a indexação
# Sitemap só com indexação ligada: domínio com MG_INDEXAR≠1 deixa as páginas em noindex,
# e um sitemap listando páginas noindex é incoerente (o check.py reprova).
sm = os.path.join(OUT, "sitemap.xml")
if INDEXAR:
  write("sitemap.xml",'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f"  <url><loc>{DOMINIO}{p}</loc><lastmod>{HOJE}</lastmod></url>\n" for p in ["/"]+[f"/produtos/{c[0]}.html" for c in C])+"</urlset>\n")
elif os.path.exists(sm):
  os.remove(sm)
if INDEXAR:
  write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMINIO}/sitemap.xml\n")
else:
  write("robots.txt", "# Prévia: domínio ainda não publicado. Todas as páginas têm <meta name=\"robots\" content=\"noindex,follow\">.\n"
        "# O rastreio fica liberado para que os buscadores leiam esse noindex. Sem sitemap até haver domínio.\n"
        "# Ao publicar: MG_DOMINIO=https://... MG_INDEXAR=1 python3 build_site.py\nUser-agent: *\nAllow: /\n")
print("ok:", OUT, "| domínio:", DOMINIO or "(pendente)", "| indexar:", INDEXAR)
