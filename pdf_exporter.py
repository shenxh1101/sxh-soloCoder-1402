import os
from typing import List
from models import DishCostAnalysis
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


CN_FONT = 'STSong-Light'
CN_FONT_REGISTERED = False


def _register_cn_font():
    global CN_FONT_REGISTERED
    if not CN_FONT_REGISTERED:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(CN_FONT))
            CN_FONT_REGISTERED = True
            return True
        except Exception:
            return False
    return True


class PDFExporter:
    @staticmethod
    def is_available() -> bool:
        return PDF_AVAILABLE

    @staticmethod
    def export_cost_cards(
        analyses: List[DishCostAnalysis],
        output_path: str,
        title: str = "餐饮连锁店菜品成本卡"
    ) -> bool:
        global CN_FONT
        if not PDF_AVAILABLE:
            print("错误: 未安装reportlab库。请运行: pip install reportlab")
            return False

        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            font_ok = _register_cn_font()

            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                topMargin=2 * cm,
                bottomMargin=2 * cm,
                leftMargin=1.5 * cm,
                rightMargin=1.5 * cm,
                title=title,
                author="餐饮成本分析系统"
            )
            elements = []
            styles = getSampleStyleSheet()

            font_name = CN_FONT if font_ok else 'Helvetica'

            title_style = ParagraphStyle(
                'CNTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=20,
                alignment=1,
                leading=26,
                spaceAfter=20,
                textColor=colors.darkblue
            )
            elements.append(Paragraph(title, title_style))

            subtitle_style = ParagraphStyle(
                'CNSubtitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                alignment=1,
                textColor=colors.grey,
                spaceAfter=20,
                leading=14
            )
            elements.append(Paragraph("生成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subtitle_style))

            summary_text = "共 " + str(len(analyses)) + " 道菜"
            elements.append(Paragraph(summary_text, ParagraphStyle(
                'CNSummary',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                alignment=1,
                spaceAfter=15,
                leading=15
            )))

            h2_style = ParagraphStyle(
                'CNH2',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=14,
                textColor=colors.darkblue,
                spaceAfter=10,
                spaceBefore=5,
                leading=18
            )

            normal_style = ParagraphStyle(
                'CNNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                leading=14
            )

            h3_style = ParagraphStyle(
                'CNH3',
                parent=styles['Heading3'],
                fontName=font_name,
                fontSize=11,
                textColor=colors.black,
                spaceAfter=8,
                leading=14
            )

            for idx, analysis in enumerate(analyses):
                if idx > 0:
                    elements.append(Spacer(1, 0.3 * cm))
                    if idx % 2 == 0:
                        elements.append(PageBreak())

                dish_num = str(idx + 1) + ". " + analysis.dish.name
                elements.append(Paragraph(dish_num, h2_style))

                total_cal_str = (str(round(analysis.total_calorie, 0)) + ' kcal') if analysis.total_calorie else '未提供'
                info_data = [
                    ['菜品类别', analysis.dish.category, '目标毛利率', str(round(analysis.dish.target_margin * 100, 1)) + '%'],
                    ['物料成本', '¥' + str(round(analysis.material_cost, 2)), '建议售价', '¥' + str(round(analysis.suggested_price, 2))],
                    ['毛利额', '¥' + str(round(analysis.gross_profit, 2)), '实际毛利率', str(round(analysis.gross_margin * 100, 1)) + '%'],
                    ['总热量', total_cal_str, '', '']
                ]

                info_table = Table(info_data, colWidths=[2.8 * cm, 4 * cm, 2.8 * cm, 4 * cm])
                info_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.7, 0.7, 0.7)),
                    ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.92, 0.95, 1.0)),
                    ('BACKGROUND', (2, 0), (2, -1), colors.Color(0.92, 0.95, 1.0)),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, colors.Color(0.98, 0.98, 0.98)]),
                    ('ROWBACKGROUNDS', (3, 0), (3, -1), [colors.white, colors.Color(0.98, 0.98, 0.98)]),
                ]))
                elements.append(info_table)
                elements.append(Spacer(1, 0.3 * cm))

                elements.append(Paragraph("配方明细", h3_style))

                recipe_header = ['序号', '原材料', '用量', '单位', '成本(元)', '成本占比']
                recipe_data = [recipe_header]
                for i, (name, cost) in enumerate(analysis.ingredient_costs):
                    recipe_item = next((item for item in analysis.dish.recipe if item.ingredient_name == name), None)
                    amount = recipe_item.amount if recipe_item else 0
                    unit = recipe_item.unit if recipe_item else ''
                    percentage = str(round((cost / analysis.material_cost * 100), 1)) + '%' if analysis.material_cost > 0 else '0%'
                    amount_str = str(int(amount)) if amount == int(amount) else str(round(amount, 2))
                    recipe_data.append([
                        str(i + 1),
                        name,
                        amount_str,
                        unit,
                        str(round(cost, 2)),
                        percentage
                    ])

                recipe_table = Table(recipe_data, colWidths=[1.3 * cm, 3.8 * cm, 2 * cm, 1.5 * cm, 2.5 * cm, 2 * cm])
                recipe_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.7, 0.7, 0.7)),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.98, 1.0)]),
                ]))
                elements.append(recipe_table)

                margin_warn_style = ParagraphStyle(
                    'CNWarn',
                    parent=styles['Normal'],
                    fontName=font_name,
                    fontSize=9,
                    textColor=colors.red,
                    spaceBefore=8,
                    leading=12
                )
                if analysis.gross_margin < 0.4:
                    warn_text = "⚠ 毛利率低于 40%，建议调整售价或优化配方。"
                    elements.append(Paragraph(warn_text, margin_warn_style))

                if idx < len(analyses) - 1:
                    elements.append(Spacer(1, 0.4 * cm))
                    hr_style = ParagraphStyle(
                        'CNHr',
                        parent=styles['Normal'],
                        fontName=font_name,
                        fontSize=8,
                        textColor=colors.lightgrey,
                        alignment=1,
                        spaceBefore=5,
                        spaceAfter=5
                    )
                    elements.append(Paragraph("— — — — — — — — — — — — — — — — — — — — — — — — — — — — — — — — — —", hr_style))

            footer_style = ParagraphStyle(
                'CNFooter',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                textColor=colors.grey,
                alignment=1,
                spaceBefore=30,
                leading=12
            )
            elements.append(Spacer(1, 0.5 * cm))
            elements.append(Paragraph("本成本卡由「餐饮连锁店菜品成本卡与毛利率分析系统」自动生成", footer_style))

            doc.build(elements)
            print("✅ PDF导出成功: " + output_path)
            return True

        except Exception as e:
            print("PDF导出失败:", str(e))
            import traceback
            traceback.print_exc()
            return False
