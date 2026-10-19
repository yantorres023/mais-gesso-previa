/* Mais Gesso — seletor de loja, lista de orçamento e diálogos acessíveis. Sem dependências. */
(function () {
  "use strict";
  var d = document, b = d.body;
  var S = window.MG_STORES || {}, ITEMS = window.MG_ITEMS || [];
  var K_STORE = "mgStore", K_CART = "mgCart", MAX_ITENS = 60, MAX_QTD = 999, MAX_NOME = 120;
  var LIM = { nome: 80, entrega: 60, obs: 500 };
  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }
  var PEND = window.MG_PENDENTES === true;
  function pend(t) { var e = d.createElement("span"); e.className = PEND ? "pend" : "soon"; e.textContent = PEND ? "[pendente: " + t + "]" : t; return e; }
  function fill(el, txt, pendTxt) { el.textContent = ""; if (txt) el.textContent = txt; else el.appendChild(pend(pendTxt)); }
  function waLink(num, msg) { return "https://wa.me/" + String(num).replace(/\D/g, "") + "?text=" + encodeURIComponent(msg); }
  function clip(v, n) { return String(v || "").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, "").trim().slice(0, n); }

  /* ---------- armazenamento validado ---------- */
  var VALIDOS = {}; ITEMS.forEach(function (n) { VALIDOS[n] = 1; });
  function limpar(raw) {
    if (!Array.isArray(raw)) return [];
    var out = [], visto = {};
    for (var i = 0; i < raw.length && out.length < MAX_ITENS; i++) {
      var it = raw[i];
      if (!it || typeof it !== "object" || typeof it.n !== "string") continue;
      var n = it.n.trim().slice(0, MAX_NOME);
      if (!VALIDOS[n] || visto[n]) continue;
      var q = parseInt(it.q, 10);
      visto[n] = 1; out.push({ n: n, q: q >= 1 && q <= MAX_QTD ? q : 1 });
    }
    return out;
  }
  var cur = null, cart = [];
  try {
    cur = localStorage.getItem(K_STORE);
    var raw = localStorage.getItem(K_CART);
    cart = limpar(raw ? JSON.parse(raw) : []);
  } catch (e) { cart = []; }
  if (!Object.prototype.hasOwnProperty.call(S, cur)) cur = null;
  function save() {
    try {
      if (cur) localStorage.setItem(K_STORE, cur); else localStorage.removeItem(K_STORE);
      localStorage.setItem(K_CART, JSON.stringify(cart));
    } catch (e) { /* modo privado / cota cheia: segue sem persistir */ }
  }

  /* ---------- loja ---------- */
  function sel(id) {
    if (!Object.prototype.hasOwnProperty.call(S, id)) return;
    cur = id; var s = S[id];
    $$("[data-store-name]").forEach(function (e) { e.textContent = s.n; });
    $$("[data-store-short]").forEach(function (e) { e.textContent = s.c || s.n; });
    $$("[data-store-in]").forEach(function (e) { e.textContent = "em " + s.n; });
    $$("[data-pick]").forEach(function (o) { var on = o.getAttribute("data-pick") === id; o.classList.toggle("on", on); o.setAttribute("aria-pressed", on ? "true" : "false"); });
    var a = $("#saddr"); if (a) fill(a, s.addr, s.addrPend);
    var h = $("#shours"); if (h) fill(h, s.h, s.hPend);
    var w = $("#swa"); if (w) w.href = waLink(s.wa, "Olá, Mais Gesso! Vim pelo site e gostaria de atendimento na loja de " + s.n + ".");
    var l = $("#slnk"); if (l) l.href = s.lnk;
    var sw = $("#swarn"); if (sw) sw.hidden = !PEND || (!s.waPend && s.ok);
    var cw = $("#cwarn"); if (cw) cw.hidden = !PEND || !s.waPend;
    var m = $("#smap"), nm = $("#snomap");
    if (m) { m.hidden = !s.emb; if (s.emb && m.getAttribute("src") !== s.emb) m.setAttribute("src", s.emb); }
    if (nm) nm.hidden = !!s.emb;
    save();
  }

  /* ---------- lista de orçamento ---------- */
  function render() {
    var n = $("#cartn"); if (n) n.textContent = cart.length;
    var cb = $("#cartbtn"); if (cb) cb.setAttribute("aria-label", "Abrir lista de orçamento (" + cart.length + (cart.length === 1 ? " item)" : " itens)"));
    var ul = $("#cartlist");
    if (ul) {
      ul.textContent = "";
      if (!cart.length) { var v = d.createElement("li"); v.className = "empty"; v.textContent = "Nenhum item ainda. Toque em “+ Adicionar ao orçamento”."; ul.appendChild(v); }
      cart.forEach(function (it, i) {
        var li = d.createElement("li");
        var nm = d.createElement("span"); nm.textContent = it.n;
        var q = d.createElement("input"); q.type = "number"; q.min = "1"; q.max = String(MAX_QTD); q.inputMode = "numeric"; q.value = it.q; q.setAttribute("aria-label", "Quantidade de " + it.n);
        q.addEventListener("change", function () { var x = parseInt(q.value, 10); it.q = x >= 1 ? Math.min(x, MAX_QTD) : 1; q.value = it.q; save(); });
        var rm = d.createElement("button"); rm.type = "button"; rm.textContent = "✕"; rm.setAttribute("aria-label", "Remover " + it.n);
        rm.addEventListener("click", function () { cart.splice(i, 1); sync(); var f = $("#cartlist button") || $("#send"); if (f) f.focus(); });
        li.appendChild(nm); li.appendChild(q); li.appendChild(rm); ul.appendChild(li);
      });
    }
    $$(".add").forEach(function (bt) {
      var on = cart.some(function (x) { return x.n === bt.getAttribute("data-item"); });
      bt.classList.toggle("ok", on); bt.setAttribute("aria-pressed", on ? "true" : "false");
      bt.textContent = on ? "✓ Na lista" : "+ Adicionar ao orçamento";
    });
  }
  function sync() { render(); save(); }
  $$(".add").forEach(function (bt) {
    bt.addEventListener("click", function () {
      var n = bt.getAttribute("data-item"); if (!VALIDOS[n]) return;
      var i = -1; cart.forEach(function (x, k) { if (x.n === n) i = k; });
      if (i >= 0) cart.splice(i, 1); else if (cart.length < MAX_ITENS) cart.push({ n: n, q: 1 });
      sync();
    });
  });

  /* ---------- diálogos (gaveta e seletor): focus trap, Esc, retorno de foco ---------- */
  var DLG = { cart: { el: $("#drawer"), cls: "cart" }, pick: { el: $("#picker"), cls: "pick" } };
  var pilha = [];
  function focaveis(root) {
    return $$('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])', root)
      .filter(function (e) { return e.getClientRects().length > 0 && getComputedStyle(e).visibility !== "hidden"; });
  }
  function abrir(nome) {
    var g = DLG[nome]; if (!g || !g.el) return;
    for (var i = 0; i < pilha.length; i++) if (pilha[i].nome === nome) return;
    if (b.classList.contains("menu")) fecharMenu(false);
    pilha.push({ nome: nome, volta: d.activeElement });
    b.classList.add(g.cls); g.el.removeAttribute("aria-hidden");
    var alvo = nome === "pick" ? ($(".opt.on", g.el) || focaveis(g.el)[0]) : focaveis(g.el)[0];
    (alvo || g.el).focus();
  }
  function fechar(nome) {
    var g = DLG[nome], k = -1;
    for (var i = 0; i < pilha.length; i++) if (pilha[i].nome === nome) k = i;
    if (!g || k < 0) return;
    var item = pilha.splice(k, 1)[0];
    b.classList.remove(g.cls); if (nome === "cart") g.el.setAttribute("aria-hidden", "true");
    if (item.volta && d.contains(item.volta) && item.volta.focus) item.volta.focus();
  }
  var MG = window.MG = {
    toggle: function (o) { o ? abrir("cart") : fechar("cart"); },
    picker: function (o) { o ? abrir("pick") : fechar("pick"); }
  };
  var cbtn = $("#cartbtn"); if (cbtn) cbtn.addEventListener("click", function () { abrir("cart"); });
  $$("[data-close-cart]").forEach(function (e) { e.addEventListener("click", function () { fechar("cart"); }); });
  $$("[data-open-picker]").forEach(function (e) { e.addEventListener("click", function () { abrir("pick"); }); });
  $$("[data-close-picker]").forEach(function (e) { e.addEventListener("click", function () { fechar("pick"); }); });
  var pk = $("#picker"); if (pk) pk.addEventListener("click", function (e) { if (e.target === pk) fechar("pick"); });

  /* ---------- menu móvel ---------- */
  var burger = $("[data-menu]"), nav = $("#nav");
  function menuFocaveis() { return (nav ? $$("a[href]", nav) : []).concat(burger ? [burger] : []); }
  function abrirMenu() {
    b.classList.add("menu"); burger.setAttribute("aria-expanded", "true"); burger.setAttribute("aria-label", "Fechar menu");
    var f = nav && $("a[href]", nav); if (f) f.focus();
  }
  function fecharMenu(devolver) {
    b.classList.remove("menu"); if (!burger) return;
    burger.setAttribute("aria-expanded", "false"); burger.setAttribute("aria-label", "Abrir menu");
    if (devolver) burger.focus();
  }
  if (burger) burger.addEventListener("click", function () { b.classList.contains("menu") ? fecharMenu(true) : abrirMenu(); });
  if (nav) $$("a", nav).forEach(function (a) { a.addEventListener("click", function () { if (b.classList.contains("menu")) fecharMenu(false); }); });
  d.addEventListener("click", function (e) { if (b.classList.contains("menu") && !e.target.closest(".top")) fecharMenu(false); });
  window.addEventListener("resize", function () { if (window.innerWidth >= 900 && b.classList.contains("menu")) fecharMenu(false); });

  /* O trap move o foco ele mesmo a cada Tab: no menu os focáveis não são contíguos no DOM
     (o botão da loja fica entre o nav e o burger), então não dá para confiar na ordem nativa. */
  function prender(lista, e) {
    e.preventDefault();
    if (!lista.length) return;
    var i = lista.indexOf(d.activeElement), n = lista.length;
    var j = i < 0 ? (e.shiftKey ? n - 1 : 0) : (i + (e.shiftKey ? n - 1 : 1)) % n;
    lista[j].focus();
  }
  d.addEventListener("keydown", function (e) {
    var topo = pilha[pilha.length - 1];
    if (e.key === "Escape" || e.key === "Esc") {
      if (topo) { e.preventDefault(); fechar(topo.nome); }
      else if (b.classList.contains("menu")) { e.preventDefault(); fecharMenu(true); }
      return;
    }
    if (e.key !== "Tab") return;
    if (topo) prender(focaveis(DLG[topo.nome].el), e);
    else if (b.classList.contains("menu")) prender(menuFocaveis(), e);
  });

  /* ---------- escolha de loja ---------- */
  $$("[data-pick]").forEach(function (bt) {
    bt.addEventListener("click", function () {
      sel(bt.getAttribute("data-pick"));
      var noHero = !!bt.closest("#lojas-pick");
      fechar("pick");
      var alvo = $("#sua-loja");
      if (noHero && alvo) { alvo.scrollIntoView({ behavior: "smooth" }); var h = $("#sua-loja-t"); if (h) { h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); } }
    });
  });

  /* ---------- envio pelo WhatsApp ---------- */
  var send = $("#send");
  if (send) send.addEventListener("click", function () {
    if (!cur) { abrir("pick"); return; }
    var s = S[cur], nome = clip(($("#cname") || {}).value, LIM.nome), ent = clip(($("#ccep") || {}).value, LIM.entrega), obs = clip(($("#cobs") || {}).value, LIM.obs);
    var m = "Olá, Mais Gesso! Gostaria de um orçamento na loja de " + s.n + ".\n";
    if (nome) m += "Nome: " + nome + "\n";
    m += cart.length ? "\nItens:\n" + cart.map(function (x) { return "• " + x.q + "x " + x.n; }).join("\n") + "\n" : "\n(ainda sem itens; quero ajuda para montar a lista)\n";
    if (ent) m += "\nEntrega: " + ent;
    if (obs) m += "\nObs.: " + obs;
    var a = d.createElement("a"); a.href = waLink(s.wa, m); a.target = "_blank"; a.rel = "noopener noreferrer";
    b.appendChild(a); a.click(); a.remove();
  });

  /* ---------- abas de produto (padrão ARIA tabs) ---------- */
  var tabs = $$(".tab[role=tab]");
  function ativar(t, foco) {
    tabs.forEach(function (x) { var on = x === t; x.classList.toggle("on", on); x.setAttribute("aria-selected", on ? "true" : "false"); x.tabIndex = on ? 0 : -1; });
    $$(".tabp").forEach(function (p) { p.hidden = p.getAttribute("data-panel") !== t.getAttribute("data-tab"); });
    if (foco) t.focus();
  }
  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { ativar(t); });
    t.addEventListener("keydown", function (e) {
      var n = null;
      if (e.key === "ArrowRight") n = tabs[(i + 1) % tabs.length];
      else if (e.key === "ArrowLeft") n = tabs[(i - 1 + tabs.length) % tabs.length];
      else if (e.key === "Home") n = tabs[0];
      else if (e.key === "End") n = tabs[tabs.length - 1];
      if (n) { e.preventDefault(); ativar(n, true); }
    });
  });

  /* ---------- geolocalização (cidade mais próxima) ---------- */
  var g = $("#geo");
  if (g) g.addEventListener("click", function () {
    if (!navigator.geolocation) { g.textContent = "Localização indisponível neste navegador"; return; }
    g.setAttribute("aria-busy", "true");
    navigator.geolocation.getCurrentPosition(function (p) {
      var melhor = null, dist = Infinity;
      Object.keys(S).forEach(function (k) { var c = S[k].geo; if (!c) return; var x = Math.pow(c[0] - p.coords.latitude, 2) + Math.pow(c[1] - p.coords.longitude, 2); if (x < dist) { dist = x; melhor = k; } });
      g.removeAttribute("aria-busy");
      if (melhor) { sel(melhor); var a = $("#sua-loja"); if (a) a.scrollIntoView({ behavior: "smooth" }); }
    }, function () { g.removeAttribute("aria-busy"); g.textContent = "Não foi possível obter sua localização — escolha a loja acima"; }, { timeout: 8000 });
  });

  sel(cur || "fabriciano");
  render(); save();
})();
