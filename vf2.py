import urllib.request as r2, urllib.parse as p2, http.cookiejar as cj, re, json

base = "http://localhost:8000"

def make_opener():
    jar = cj.CookieJar()
    op = r2.build_opener(r2.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent","Mozilla/5.0")]
    return op

def login(op, email, pw):
    rr = op.open(base + "/cuentas/login/")
    h = rr.read().decode()
    cs = re.search(r'csrfmiddlewaretoken[^>]+value="([^"]+)"', h).group(1)
    d = p2.urlencode({"email": email, "password": pw, "csrfmiddlewaretoken": cs}).encode()
    rq = r2.Request(base + "/cuentas/login/", data=d,
         headers={"Referer": base + "/cuentas/login/",
                  "Content-Type": "application/x-www-form-urlencoded"})
    return op.open(rq)

def chk(cond, label):
    s = "OK" if cond else "FAIL"
    print(f"  [{s}] {label}")
    return cond

print("=== FLUJO CLIENTE ===")
op = make_opener()
r = login(op, "cliente@optica.demo", "Cliente@123")
print(f"1. Login cliente => {r.url}")

r = op.open(base + "/catalogo/")
h = r.read().decode()
print(f"2. GET /catalogo/ => {r.status}")
chk("navbar-optica" in h, "navbar-optica class")
chk("fonts.googleapis" in h, "Inter font link")
chk("badge-rol" in h, "badge de rol")
chk("Óptica" in h, "logo Óptica")
chk("Prueba Virtual" in h, "botón VTO en catálogo")
chk("producto-card" in h, "clase producto-card")

r = op.open(base + "/api/productos/?categoria=1")
d = json.loads(r.read())
prods = d.get("results", d) if isinstance(d, dict) else d
prods_with_vto = [p for p in prods if p.get("imagen_vto_url")]
pid = prods_with_vto[0]["id"] if prods_with_vto else prods[0]["id"] if prods else 16
print(f"3. API /api/productos/?categoria=1 => {len(prods)} armazones, {len(prods_with_vto)} con vto_url, usando pid={pid}")

r = op.open(base + "/catalogo/" + str(pid) + "/")
h = r.read().decode()
print(f"4. GET /catalogo/{pid}/ => {r.status}")
chk("Prueba Virtual" in h, "botón VTO en detalle")
chk(h.count("thumbnail") >= 1, f"thumbnails de galería (count={h.count('thumbnail')})")
chk("cambiarImg" in h, "función cambiarImg")
chk("_2.png" in h or "_3.png" in h, "imágenes galería _2.png / _3.png")

r = op.open(base + "/vto/?producto=" + str(pid))
h = r.read().decode()
print(f"5. GET /vto/?producto={pid} => {r.status}")
chk("/static/vto/opencv.js" in h, "opencv.js cargado localmente")
chk(h.count("adj-slider") >= 4, f"4 sliders (count={h.count('adj-slider')})")
chk("Probar otros modelos" in h, "panel otros modelos")
chk("const ARMAZONES" in h, "array ARMAZONES en JS")
chk("drawOverlay" in h, "función drawOverlay")
chk("actualizarEstadoControles" in h, "controles deshabilitados sin rostro")

r = op.open(base + "/pedidos/carrito/")
h = r.read().decode()
print(f"6. GET /carrito/ => {r.status}")
title = re.search(r"<title>([^<]+)", h)
print(f"   título: {title.group(1) if title else 'N/A'}")

print("\n=== FLUJO GERENCIA ===")
op2 = make_opener()
r = login(op2, "gerencia@optica.demo", "Gerencia@123")
print(f"7. Login gerencia => {r.url}")

r = op2.open(base + "/dashboard/")
h = r.read().decode()
print(f"8. GET /dashboard/ => {r.status}")
chk(h.count("kpi-card") >= 4, f"4 kpi-cards (count={h.count('kpi-card')})")
chk(h.count("kpi-value") >= 4, f"4 kpi-values (count={h.count('kpi-value')})")
chk("chartVentas" in h, "Chart.js gráfico ventas")
chk("table-striped" in h, "table-striped en dashboard")
chk("empty-state" in h or "kpi-sub" in h, "empty-state o kpi-sub")

r = op2.open(base + "/pedidos/operativo/")
h = r.read().decode()
print(f"9. GET /operativo/ => {r.status}")
chk("table-striped" in h, "table-striped en operativo")
chk("badge-estado" in h, "badge-estado en operativo")
chk("navbar-optica" in h, "navbar hereda de base.html")

r = op2.open(base + "/inventario/")
h = r.read().decode()
print(f"10. GET /inventario/ => {r.status}")
chk("table-striped" in h, "table-striped en inventario")
chk("badge-estado" in h, "badge-estado en inventario")
chk("empty-state" in h, "empty-state en inventario")
chk("opacity-60" in h, "opacity-60 para inactivos")

r = op2.open(base + "/pedidos/historial/")
h = r.read().decode()
print(f"11. GET /historial/ => {r.status}")
chk("table-striped" in h, "table-striped en historial")
chk("badge-estado" in h, "badge-estado en historial")

print("\n=== VERIFICACION COMPLETA ===")