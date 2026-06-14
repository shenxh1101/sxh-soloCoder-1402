import os
from typing import List
from models import DishCostAnalysis
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


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
        if not PDF_AVAILABLE:
            print("错误: 未安装reportlab库。请运行: pip install reportlab")
            return False

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
            elements = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                alignment=1,
                spaceAfter=30
            )
            elements.append(Paragraph(title, title_style))

            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=10,
                alignment=1,
                textColor=colors.grey,
                spaceAfter=20
            )
            elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))

            for idx, analysis in enumerate(analyses):
                elements.append(Spacer(1, 0.5 * cm))

                dish_header = f"{idx + 1}. {analysis.dish.name}"
                dish_header_style = ParagraphStyle(
                    'DishHeader',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.darkblue,
                    spaceAfter=10
                )
                elements.append(Paragraph(dish_header, dish_header_style))

                info_data = [
                    ['菜品类别', analysis.dish.category, '目标毛利率', f"{analysis.dish.target_margin * 100:.1f}%"],
                    ['物料成本', f"¥{analysis.material_cost:.2f}", '建议售价', f"¥{analysis.suggested_price:.2f}"],
                    ['毛利额', f"¥{analysis.gross_profit:.2f}", '实际毛利率', f"{analysis.gross_margin * 100:.1f}%"],
                    ['总热量', f"{analysis.total_calorie:.0f} kcal" if analysis.total_calorie else '未提供', '', '']
                ]

                info_table = Table(info_data, colWidths=[3 * cm, 4 * cm, 3 * cm, 4 * cm])
                info_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(info_table)
                elements.append(Spacer(1, 0.3 * cm))

                elements.append(Paragraph("配方明细:", styles['Heading3']))

                recipe_data = [['序号', '原材料', '用量', '单位', '成本(元)', '占比']]
                for i, (name, cost) in enumerate(analysis.ingredient_costs):
                    recipe_item = next((item for item in analysis.dish.recipe if item.ingredient_name == name), None)
                    amount = recipe_item.amount if recipe_item else 0
                    unit = recipe_item.unit if recipe_item else ''
                    percentage = (cost / analysis.material_cost * 100) if analysis.material_cost > 0 else 0
                    recipe_data.append([
                        str(i + 1),
                        name,
                        f"{amount:.0f}" if amount == int(amount) else f"{amount:.2f}",
                        unit,
                        f"{cost:.2f}",
                        f"{percentage:.1f}%"
                    ])

                recipe_table = Table(recipe_data, colWidths=[1.5 * cm, 4 * cm, 2 * cm, 1.5 * cm, 2.5 * cm, 2 * cm])
                recipe_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(recipe_table)
                elements.append(Spacer(1, 0.5 * cm))

                if idx < len(analyses) - 1:
                    elements.append(Paragraph('_' * 80, styles['Normal']))

            doc.build(elements)
            print(f"PDF导出成功: {output_path}")
            return True

        except Exception as e:
            print(f"PDF导出失败: {e}")
            return False
