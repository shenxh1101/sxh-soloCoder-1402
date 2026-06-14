from typing import List, Tuple
from datetime import datetime


class AsciiChart:
    @staticmethod
    def draw_line_chart(
        data_points: List[Tuple[datetime, float]],
        title: str = "价格走势",
        height: int = 10,
        width: int = 60
    ) -> str:
        if not data_points:
            return "无数据可显示"

        sorted_points = sorted(data_points, key=lambda x: x[0])
        prices = [p[1] for p in sorted_points]
        min_price = min(prices)
        max_price = max(prices)

        if max_price == min_price:
            max_price = min_price * 1.1
            min_price = min_price * 0.9

        price_range = max_price - min_price

        chart = []
        chart.append(f"\n{'=' * width}")
        chart.append(f"{title:^{width}}")
        chart.append(f"{'=' * width}")

        num_points = len(sorted_points)
        step = max(1, (num_points - 1) // (width - 10)) if width > 10 else 1
        display_points = sorted_points[::step]
        if len(display_points) < 2 and len(sorted_points) >= 2:
            display_points = [sorted_points[0], sorted_points[-1]]

        y_labels = []
        for i in range(height + 1):
            price = max_price - (price_range * i / height)
            y_labels.append(f"{price:7.2f} |")

        plot_width = width - 10
        chart_data = [' ' * plot_width for _ in range(height + 1)]

        for idx, (timestamp, price) in enumerate(display_points):
            x_pos = int(idx * (plot_width - 1) / max(len(display_points) - 1, 1))
            y_pos = int((max_price - price) / price_range * height)
            y_pos = max(0, min(y_pos, height))

            row = list(chart_data[y_pos])
            if 0 <= x_pos < len(row):
                row[x_pos] = '*'
            chart_data[y_pos] = ''.join(row)

            if y_pos > 0:
                row_below = list(chart_data[y_pos - 1])
                if 0 <= x_pos < len(row_below) and row_below[x_pos] == ' ':
                    row_below[x_pos] = '|'
                chart_data[y_pos - 1] = ''.join(row_below)

        for i in range(height + 1):
            chart.append(f"{y_labels[i]}{chart_data[i]}")

        chart.append(f"{'        +'}{'-' * plot_width}")

        x_labels = []
        for idx, (timestamp, _) in enumerate(display_points):
            x_pos = int(idx * (plot_width - 1) / max(len(display_points) - 1, 1))
            date_str = timestamp.strftime("%m-%d")
            x_labels.append((x_pos, date_str))

        x_axis_row = [' ' * plot_width for _ in range(2)]
        for x_pos, label in x_labels:
            for i, char in enumerate(label):
                if x_pos + i < plot_width:
                    row = list(x_axis_row[1])
                    row[x_pos + i] = char
                    x_axis_row[1] = ''.join(row)

        chart.append(f"        |{x_axis_row[0]}")
        chart.append(f"        |{x_axis_row[1]}")
        chart.append(f"{'=' * width}")
        chart.append(f"最低价格: {min_price:.2f} 元 | 最高价格: {max_price:.2f} 元")
        chart.append(f"数据点数: {len(sorted_points)} 个 | 显示点数: {len(display_points)} 个")

        return '\n'.join(chart)

    @staticmethod
    def draw_bar_chart(
        data: List[Tuple[str, float]],
        title: str = "数据统计",
        max_bar_width: int = 40
    ) -> str:
        if not data:
            return "无数据可显示"

        max_value = max(v for _, v in data)
        max_label_len = max(len(label) for label, _ in data)

        chart = []
        width = max_label_len + max_bar_width + 20
        chart.append(f"\n{'=' * width}")
        chart.append(f"{title:^{width}}")
        chart.append(f"{'=' * width}")

        for label, value in data:
            bar_length = int((value / max_value) * max_bar_width) if max_value > 0 else 0
            bar = '█' * bar_length
            chart.append(f"{label:<{max_label_len}} | {bar} {value:.2f}")

        chart.append(f"{'=' * width}")

        return '\n'.join(chart)
