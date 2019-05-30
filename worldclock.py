#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Cairo world clock. Even if it's using GTK, it's ignore most of the
possible goodies, which GTK provides, because of limitations, that DrawingArea
and container managers in GTK have.

Putting DA in grid for example, will kind of work, but, you'll end up with
this:
    - every single DA in a grid cells will have 1x1 px dimension,
    - unless you initialize DA with some values for its width and height, but
      you'll loose scalability of the widget,
    - every thing you draw on DA will be "invisible", since coordinates, which
      we can get are limited to the current widget (DrawingArea descendant)
      which will get you relative coordinates, and there is no way to get
      coordinates of the grid cell, so that you'll end up with several
      DrawingAreas, which have absolute coordinates just like the first one,
      and the others just will be hidden behind the first one in the best
      case, and in worst - view window od the DrawingArea will be shifted by
      the selected cell, which eventually end up with no drawings at all.
As for Box manager, you'll suffer from the last item of the grid list above,
which will end up with "invisible" or misplaced widget in the box itself.

Due to this stupid design, DrawingArea descendant object should be placed
directly in window object. Using single clock in container manager (like grid,
table, box) will make you hurt, and you'll be swearing a lot like I did. Don't
do that. It's a waste of time.
"""
import argparse
from datetime import datetime
import math
import os
import sys

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject
import pytz
import yaml


CLOCK_DA_DIAMETER = 140
DATE_FMT = '%Y-%m-%d %H:%M %Z'
CFG_GNAME = "gtkworldclock.yaml"


class Clock:
    """Clock class for conveniently keeping it's state"""
    def __init__(self, conf, row=0, col=0, size=CLOCK_DA_DIAMETER,
                 show_seconds=True):
        self.tz = pytz.timezone(conf['tz'])
        self.label = conf['label']
        self.row = row
        self.col = col
        self.now = None
        self.size = size
        self.show_seconds = show_seconds

        self._calculate_coordinates()

    def _calculate_coordinates(self):
        self.x = self.col * self.size + self.size / 2
        self.y = self.row * self.size + self.size / 2
        self.y = self.y + self.row * self.size / 4
        self.radius = self.size / 2 - 5

    def _show_caption(self, ctx):
        self._calculate_coordinates()
        ctx.save()
        ctx.set_font_size(self.radius / 7)
        x, y, width, height, dx, dy = ctx.text_extents(self.label)
        ctx.move_to(self.x - x/2 - width/2,
                    self.y + self.radius + 2 * self.radius / 10)
        ctx.show_text(self.label)

        date = self.now.strftime(DATE_FMT)

        x, y, width, height, dx, dy = ctx.text_extents(date)
        ctx.move_to(self.x - x/2 - width/2,
                    self.y + self.radius + 2 * self.radius / 10 +
                    self.size / 10)
        ctx.show_text(date)
        ctx.restore()

    def _draw_face(self, ctx):
        self._calculate_coordinates()
        ctx.move_to(self.x + self.radius * math.cos(0 * math.pi/30),
                    self.y + self.radius * math.sin(0 * math.pi/30))
        ctx.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill_preserve()
        ctx.set_source_rgb(0, 0, 0)
        ctx.stroke()

    def _draw_ticks(self, ctx):
        self._calculate_coordinates()
        for i in range(180):
            ctx.save()
            if i % 5 == 0:
                if i % 3 == 0:
                    # hours: 12, 3, 6, and 9
                    inset = 0.15 * self.radius
                else:
                    # all other hours
                    inset = 0.1 * self.radius
                    ctx.set_line_width(0.5 * ctx.get_line_width())
            else:
                # seconds
                inset = 0.05 * self.radius
                ctx.set_line_width(0.25 * ctx.get_line_width())

            ctx.move_to(self.x + (self.radius-inset) *
                        math.cos(i * math.pi/30),
                        self.y + (self.radius-inset) *
                        math.sin(i * math.pi/30))
            ctx.line_to(self.x + self.radius * math.cos(i * math.pi/30),
                        self.y + self.radius * math.sin(i * math.pi/30))
            ctx.stroke()
            ctx.restore()

    def _draw_hands(self, ctx):
        self._calculate_coordinates()
        self.now = datetime.now(self.tz)
        hours = self.now.hour * math.pi / 6
        minutes = self.now.minute * math.pi / 30
        seconds = self.now.second * math.pi / 30

        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        # draw the hours hand
        ctx.save()
        ctx.set_line_width(3)
        ctx.move_to(self.x, self.y)
        ctx.line_to(self.x + math.sin(hours + minutes/12) *
                    (self.radius * 0.5),
                    self.y - math.cos(hours + minutes/12) *
                    (self.radius * 0.5))
        ctx.stroke()
        ctx.restore()

        # draw the minutes hand
        ctx.save()
        ctx.set_line_width(2)
        ctx.move_to(self.x, self.y)
        ctx.line_to(self.x + math.sin(minutes + seconds/60) *
                    (self.radius * 0.8),
                    self.y - math.cos(minutes + seconds/60) *
                    (self.radius * 0.8))
        ctx.stroke()
        ctx.restore()

        if not self.show_seconds:
            return

        # draw the seconds hand
        ctx.save()
        ctx.set_line_width(1)
        ctx.move_to(self.x, self.y)
        ctx.line_to(self.x + math.sin(seconds) * (self.radius * 0.9),
                    self.y - math.cos(seconds) * (self.radius * 0.9))
        ctx.stroke()
        ctx.restore()


class Clocks(Gtk.DrawingArea):

    def __init__(self, conf=None, size=CLOCK_DA_DIAMETER,
                 disable_seconds=False, disable_resize=False):
        super(Clocks, self).__init__()
        self._conf = conf
        self._clocks = []
        self.size = size
        self.show_seconds = not disable_seconds
        self.disable_resize = disable_resize

        self._parse_conf()

    def _parse_conf(self):
        self.height = len(self._conf) * (self.size + self.size / 4)
        width = 0
        if isinstance(self._conf[0], dict):
            self.width = self.size
            for row_no, conf in enumerate(self._conf):
                self._clocks.append(Clock(conf, row_no, 0, self.size,
                                          self.show_seconds))
            return

        for row_no, row in enumerate(self._conf):
            width = len(row) if len(row) > width else width
            for col_no, conf in enumerate(row):
                self._clocks.append(Clock(conf, row_no, col_no, self.size,
                                         self.show_seconds))

        self.width = self.size * width

    def run(self):
        self.connect('draw', self._draw)
        GObject.timeout_add(100, self.on_timeout)
        win = Gtk.Window()
        win.set_title('World Clock')
        win.set_resizable(not self.disable_resize)
        win.connect('destroy', lambda w: Gtk.main_quit())
        win.set_default_size(int(self.width), int(self.height))
        win.resize(int(self.width), int(self.height))
        win.add(self)
        win.show_all()
        Gtk.main()

    def on_timeout(self):
        """Tic-toc"""
        win = self.get_window()
        rect = self.get_allocation()
        win.invalidate_rect(rect, True)
        return True

    def _draw(self, da, cairo_ctx):
        for clock in self._clocks:
            clock._draw_face(cairo_ctx)
            clock._draw_ticks(cairo_ctx)
            clock._draw_hands(cairo_ctx)
            clock._show_caption(cairo_ctx)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Provide configuration as YAML"
                        "file.")
    parser.add_argument("-s", "--size", help="Size of the clock faces, "
                        "default %d" % CLOCK_DA_DIAMETER, type=int,
                        default=CLOCK_DA_DIAMETER)
    parser.add_argument("-d", "--disable-seconds", help="Disable seconds in "
                        "clock face", action="store_true", default=False)
    parser.add_argument("-r", "--disable-resize", help="Disable resize of "
                        "the window. Note, that with single clock you'll "
                        "have at least 200px width no matter if you put "
                        "something less in size option.", action="store_true",
                        default=False)
    args = parser.parse_args()
    args = parser.parse_args()

    conf = None
    xdg_conf = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

    if not args.config:
        conf_path = os.path.join(xdg_conf, CFG_GNAME)
        if not os.path.exists(conf_path):
            print("Cannot find proper configuration for the World Clock. "
                  "Please provide proper configuration in %s file, or use "
                  "`--config` switch for providing it at the "
                  "commandline." % conf_path)
            sys.exit(1)
    else:
        conf_path = args.config

    with open(conf_path) as fobj:
        conf = yaml.safe_load(fobj)

    clocks = Clocks(conf,
                    size=args.size,
                    disable_seconds=args.disable_seconds,
                    disable_resize=args.disable_resize)
    clocks.run()


if __name__ == "__main__":
    main()
