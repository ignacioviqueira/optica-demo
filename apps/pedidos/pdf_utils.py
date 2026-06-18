"""
Generación de la Orden de Trabajo Técnica (HU-11).
Usa reportlab para el PDF y qrcode+Pillow para el código QR.
"""
import io

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _qr_image(data: str, size: int = 110) -> Image:
    qr = qrcode.QRCode(version=1, box_size=3, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    pil_img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return Image(buf, width=size, height=size)


def generar_orden_trabajo(pedido) -> bytes:
    """
    Genera el PDF de la orden de trabajo técnica para un Pedido.
    Devuelve los bytes del PDF listo para enviar como HttpResponse.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    center = ParagraphStyle("center", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9)
    label = ParagraphStyle("label", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#555555"))

    elements = []

    # ── Encabezado ───────────────────────────────────────────────────────────
    elements.append(Paragraph("ÓPTICA DEMO", h1))
    elements.append(Paragraph("ORDEN DE TRABAJO TÉCNICA", ParagraphStyle(
        "sub", parent=styles["Normal"], alignment=TA_CENTER, fontSize=12,
        textColor=colors.HexColor("#1a73e8"), spaceBefore=0, spaceAfter=8,
    )))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a73e8")))
    elements.append(Spacer(1, 0.3 * cm))

    # Número de pedido + QR en la misma fila
    from django.utils.timezone import localtime
    fecha_str = localtime(pedido.fecha).strftime("%d/%m/%Y %H:%M")
    qr_data = f"OPTICA-DEMO|PEDIDO#{pedido.pk}|{pedido.usuario.email}"
    qr_img = _qr_image(qr_data, size=90)

    header_data = [
        [
            Paragraph(f"<b>N° de Pedido:</b> #{pedido.pk:05d}", body),
            qr_img,
        ],
        [
            Paragraph(f"<b>Fecha:</b> {fecha_str}", body),
            Paragraph(f"<font size='7'>Escanear para verificar</font>", center),
        ],
        [
            Paragraph(f"<b>Estado:</b> {pedido.get_estado_display()}", body),
            "",
        ],
    ]
    header_tbl = Table(header_data, colWidths=[12 * cm, 4 * cm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (1, 0), (1, 2)),
        ("ALIGN", (1, 0), (1, 2), "CENTER"),
    ]))
    elements.append(header_tbl)
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2 * cm))

    # ── Datos del cliente ────────────────────────────────────────────────────
    elements.append(Paragraph("DATOS DEL CLIENTE", h2))
    cliente = pedido.usuario
    nombre = cliente.get_full_name() or "—"
    cliente_data = [
        [Paragraph("<b>Nombre:</b>", label), Paragraph(nombre, body)],
        [Paragraph("<b>Email:</b>", label), Paragraph(cliente.email, body)],
    ]
    tbl = Table(cliente_data, colWidths=[3.5 * cm, 12.5 * cm])
    tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(tbl)

    # ── Productos ────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("PRODUCTOS", h2))

    prod_header = [
        Paragraph("<b>Producto</b>", label),
        Paragraph("<b>Marca</b>", label),
        Paragraph("<b>Cant.</b>", label),
        Paragraph("<b>P. Unit.</b>", label),
        Paragraph("<b>Subtotal</b>", label),
    ]
    prod_rows = [prod_header]
    for d in pedido.detalles.all():
        prod_rows.append([
            Paragraph(d.producto.nombre, body),
            Paragraph(d.producto.marca, body),
            Paragraph(str(d.cantidad), body),
            Paragraph(f"${d.precio_unitario:,.2f}", body),
            Paragraph(f"${d.subtotal:,.2f}", body),
        ])
    # Total row
    prod_rows.append([
        Paragraph("", body),
        Paragraph("", body),
        Paragraph("", body),
        Paragraph("<b>TOTAL:</b>", ParagraphStyle("bold_right", parent=body, alignment=2)),
        Paragraph(f"<b>${pedido.total:,.2f}</b>", body),
    ])

    prod_tbl = Table(prod_rows, colWidths=[6.5 * cm, 3 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm])
    prod_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0fe")),
        ("GRID", (0, 0), (-1, -2), 0.4, colors.HexColor("#cccccc")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1a73e8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    elements.append(prod_tbl)

    # ── Prescripción / Receta ────────────────────────────────────────────────
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("PRESCRIPCIÓN ÓPTICA", h2))

    receta = pedido.receta
    if receta:
        rx_data = [
            [
                Paragraph("<b>Campo</b>", label),
                Paragraph("<b>Valor</b>", label),
            ],
            [Paragraph("Esfera OD", body), Paragraph(f"{receta.esfera_od:+.2f} D", body)],
            [Paragraph("Cilindro OD", body), Paragraph(f"{receta.cilindro_od:+.2f} D", body)],
            [Paragraph("Eje OD", body), Paragraph(f"{receta.eje_od}°", body)],
            [Paragraph("DNP", body), Paragraph(f"{receta.dnp} mm", body)],
            [Paragraph("Fecha emisión", body), Paragraph(str(receta.fecha_emision), body)],
        ]
        rx_tbl = Table(rx_data, colWidths=[5 * cm, 11 * cm])
        rx_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0fe")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        elements.append(rx_tbl)
    else:
        elements.append(Paragraph(
            "ATENCION: Receta no digitalizada. Adjuntar receta fisica al pedido.",
            ParagraphStyle("warn", parent=body, textColor=colors.HexColor("#c0392b")),
        ))

    # ── Observaciones técnicas ───────────────────────────────────────────────
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph("OBSERVACIONES TÉCNICAS", h2))
    obs_tbl = Table(
        [[""]],
        colWidths=[16 * cm],
        rowHeights=[2.5 * cm],
    )
    obs_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
    ]))
    elements.append(obs_tbl)

    # ── Firma ────────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.8 * cm))
    firma_data = [
        [
            Paragraph("_______________________", center),
            Paragraph("_______________________", center),
        ],
        [
            Paragraph("Técnico Óptico", center),
            Paragraph("Control de Calidad", center),
        ],
    ]
    firma_tbl = Table(firma_data, colWidths=[8 * cm, 8 * cm])
    elements.append(firma_tbl)

    doc.build(elements)
    buf.seek(0)
    return buf.read()
