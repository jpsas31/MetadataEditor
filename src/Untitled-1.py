from __future__ import annotations

import math
import time

import urwid

UPDATE_INTERVAL = 1 / 30  # 30 FPS


class GraphView(urwid.WidgetWrap):
    palette = [
        ("bg background", "light gray", "black"),
        ("bg 1", "black", "dark blue", "standout"),
        ("bg 1 smooth", "dark blue", "black"),
        ("bg 2", "black", "dark cyan", "standout"),
        ("bg 2 smooth", "dark cyan", "black"),
    ]

    graph_samples_per_bar = 10
    graph_num_bars = 1000
    graph_offset_per_second = 20

    def __init__(self, controller):
        self.controller = controller
        self.offset = 0
        self.start_time = time.monotonic()

        satt = {(1, 0): "bg 1 smooth", (2, 0): "bg 2 smooth"}
        self.graph = urwid.BarGraph(["bg background", "bg 1", "bg 2"], satt=satt)
        super().__init__(self.graph)

        # Initial draw so the graph is visible immediately.
        self.update_graph()

    def _get_visible_bar_count(self) -> int:
        num_bars = self.graph_num_bars
        loop = getattr(self.controller, "loop", None)
        screen = getattr(loop, "screen", None) if loop else None
        if screen is not None:
            try:
                maxcol, _maxrow = screen.get_cols_rows()
                num_bars = min(num_bars, maxcol)
            except Exception:
                pass
        return max(1, num_bars)

    def update_graph(self) -> bool:
        tdelta = time.monotonic() - self.start_time
        phase = self.offset + (tdelta * self.graph_offset_per_second)

        num_bars = self._get_visible_bar_count()
        samples_per_bar = self.graph_samples_per_bar
        r = samples_per_bar * num_bars
        d, max_value = self.controller.get_data(phase, r)
        lines = []
        idx = 0
        for n in range(num_bars):
            total = 0.0
            for _ in range(samples_per_bar):
                total += d[idx]
                idx += 1
            value = total / samples_per_bar
            # toggle between two bar types
            if n & 1:
                lines.append([0, value])
            else:
                lines.append([value, 0])
        self.graph.set_data(lines, max_value)

        return True


class GraphController:
    def __init__(self):
        self.loop = None
        self._next_tick = None
        self.view = GraphView(self)

    def get_data(self, phase: float, r: int) -> tuple[list[float], float]:
        # Smooth/continuous wave: period of 100 samples (sin((x+phase)*pi/50)).
        scale = math.pi / 50
        sin = math.sin
        return ([50 + 50 * sin((x + phase) * scale) for x in range(r)], 100)

    def main(self):
        urwid.util.set_encoding("utf-8")
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self._next_tick = time.time()
        self.loop.set_alarm_in(0, self.animate_graph)
        self.loop.run()

    def _next_deadline(self, now: float) -> float:
        """Compute the next tick time, staying aligned to UPDATE_INTERVAL."""
        next_tick = self._next_tick
        if next_tick is None:
            next_tick = now

        next_tick += UPDATE_INTERVAL
        while next_tick < now:
            next_tick += UPDATE_INTERVAL

        self._next_tick = next_tick
        return next_tick

    def animate_graph(self, loop, user_data=None):
        self.view.update_graph()

        loop.set_alarm_at(
            self._next_deadline(time.time()),
            self.animate_graph,
        )


def main():
    GraphController().main()


if __name__ == "__main__":
    main()
