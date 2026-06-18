import csv
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import localdate, localtime

from apps.cuentas.decorators import rol_requerido
from apps.inventario.models import Producto
from apps.pedidos.models import DetallePedido, Pedido
from apps.vto.models import EventoVTO

User = get_user_model()

_PERIODOS = [
    ('hoy', 'Hoy'),
    ('semana', 'Semana'),
    ('mes', 'Mes'),
    ('todo', 'Todo'),
]


def _date_range(periodo):
    hoy = localdate()
    if periodo == 'hoy':
        return hoy, hoy
    if periodo == 'semana':
        return hoy - timedelta(days=6), hoy
    if periodo == 'mes':
        return hoy - timedelta(days=29), hoy
    return None, None


def _apply_period(qs, field, fecha_inicio, fecha_fin):
    if fecha_inicio:
        qs = qs.filter(**{f"{field}__date__gte": fecha_inicio, f"{field}__date__lte": fecha_fin})
    return qs


def _safe_json(data) -> str:
    """json.dumps escapando <, > y & para inyección segura en bloque <script>."""
    return (
        json.dumps(data)
        .replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('&', '\\u0026')
    )


@rol_requerido("gerencia")
def index(request):
    periodo = request.GET.get('periodo', 'mes')
    if periodo not in ('hoy', 'semana', 'mes', 'todo'):
        periodo = 'mes'
    fecha_inicio, fecha_fin = _date_range(periodo)

    # Pedidos excl. rechazados, filtrados por período
    pedidos_activos = Pedido.objects.exclude(estado=Pedido.Estado.RECHAZADO)
    pedidos_activos = _apply_period(pedidos_activos, 'fecha', fecha_inicio, fecha_fin)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    ventas_total = pedidos_activos.aggregate(t=Sum('total'))['t'] or Decimal('0')
    volumen_pedidos = pedidos_activos.count()

    clientes_nuevos = _apply_period(
        User.objects.filter(rol='cliente'), 'date_joined', fecha_inicio, fecha_fin
    ).count()

    vto_qs = _apply_period(EventoVTO.objects.all(), 'timestamp', fecha_inicio, fecha_fin)
    total_pruebas = vto_qs.count()
    usuarios_con_vto = list(vto_qs.values_list('usuario_id', flat=True).distinct())
    usuarios_con_vto_count = len(usuarios_con_vto)
    # Usuarios únicos que probaron VTO y realizaron al menos un pedido activo
    conversiones_vto = (
        pedidos_activos
        .filter(usuario_id__in=usuarios_con_vto)
        .values('usuario_id')
        .distinct()
        .count()
    )
    tasa_conversion = round(conversiones_vto / usuarios_con_vto_count * 100, 1) if usuarios_con_vto_count else 0.0

    # ── Chart: ventas diarias ─────────────────────────────────────────────────
    ventas_diarias = (
        pedidos_activos
        .annotate(dia=TruncDate('fecha'))
        .values('dia')
        .annotate(monto=Sum('total'), cantidad=Count('id'))
        .order_by('dia')
    )
    chart_ventas = {
        'labels': [v['dia'].strftime('%d/%m') for v in ventas_diarias],
        'montos': [float(v['monto']) for v in ventas_diarias],
        'cantidades': [v['cantidad'] for v in ventas_diarias],
    }

    # ── Chart: productos más vendidos ─────────────────────────────────────────
    top_prods = (
        DetallePedido.objects
        .filter(pedido__in=pedidos_activos)
        .values('producto__nombre')
        .annotate(total_qty=Sum('cantidad'))
        .order_by('-total_qty')[:8]
    )
    chart_productos = {
        'labels': [p['producto__nombre'] for p in top_prods],
        'qtys': [p['total_qty'] for p in top_prods],
    }

    # ── Chart: VTO top modelos ────────────────────────────────────────────────
    top_vto = (
        vto_qs
        .values('producto__nombre')
        .annotate(pruebas=Count('id'))
        .order_by('-pruebas')[:6]
    )
    chart_vto = {
        'labels': [v['producto__nombre'] for v in top_vto],
        'pruebas': [v['pruebas'] for v in top_vto],
    }

    # ── Stock crítico ─────────────────────────────────────────────────────────
    stock_critico_qs = Producto.objects.filter(activo=True, stock_actual__lte=F('stock_minimo'))
    alertas_stock_count = stock_critico_qs.count()
    stock_critico = list(stock_critico_qs.order_by('stock_actual')[:10])

    # ── Pedidos recientes (sin filtro de período) ─────────────────────────────
    pedidos_recientes = (
        Pedido.objects
        .select_related('usuario')
        .order_by('-fecha')[:8]
    )

    context = {
        'periodo': periodo,
        'periodos': _PERIODOS,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        # KPIs
        'ventas_total': ventas_total,
        'volumen_pedidos': volumen_pedidos,
        'clientes_nuevos': clientes_nuevos,
        'total_pruebas': total_pruebas,
        'usuarios_con_vto_count': usuarios_con_vto_count,
        'conversiones_vto': conversiones_vto,
        'tasa_conversion': tasa_conversion,
        # Charts — nombres de producto escapados para evitar inyección en <script>
        'chart_ventas_json': _safe_json(chart_ventas),
        'chart_productos_json': _safe_json(chart_productos),
        'chart_vto_json': _safe_json(chart_vto),
        # Tables
        'stock_critico': stock_critico,
        'alertas_stock_count': alertas_stock_count,
        'pedidos_recientes': pedidos_recientes,
    }
    return render(request, 'dashboard/index.html', context)


@rol_requerido("gerencia")
def export_csv(request):
    periodo = request.GET.get('periodo', 'mes')
    if periodo not in ('hoy', 'semana', 'mes', 'todo'):
        periodo = 'mes'
    fecha_inicio, fecha_fin = _date_range(periodo)

    # BOM para compatibilidad con Excel
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="pedidos_{periodo}.csv"'

    writer = csv.writer(response)
    writer.writerow(['N° Pedido', 'Fecha', 'Cliente', 'Email', 'Total', 'Estado', 'Receta'])

    pedidos = _apply_period(
        Pedido.objects.select_related('usuario').order_by('-fecha'),
        'fecha', fecha_inicio, fecha_fin,
    )
    for p in pedidos:
        tiene_receta = 'Sí' if (p.receta or p.receta_imagen) else 'No'
        writer.writerow([
            f"#{p.pk:05d}",
            localtime(p.fecha).strftime('%d/%m/%Y %H:%M'),
            p.usuario.get_full_name() or '—',
            p.usuario.email,
            str(p.total),
            p.get_estado_display(),
            tiene_receta,
        ])

    return response
