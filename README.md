# Mais Gesso Distribuidora — prévia do site (v2)

Prévia para aprovação do cliente. Site estático gerado por `build_site.py`.

```
MG_BASE=/mais-gesso-previa/ python3 build_site.py   # gera as páginas para o GitHub Pages
python3 scripts/check.py                           # validação de links e assets
MG_PENDENTES=1 python3 build_site.py               # mostra os marcadores [pendente: …] para revisão interna
```

As páginas usam `noindex` até o domínio definitivo ser publicado.
