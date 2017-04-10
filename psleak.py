#!/usr/bin/env python3
"""find the process leaking memory"""

from collections import OrderedDict
from time import sleep
import curses


from humanize import naturalsize
import psutil

__author__ = 'Piotr Jankowski'


class ProcessDeltaException(Exception):
    pass


class ProcessDelta(object):
    __slots__ = ['delta', 'percent', 'pd']

    def __init__(self, p1, p2):
        self.pd = p1
        self.delta = p1.mem - p2.mem
        self.percent = ((self.delta / p2.mem) * 100)

    def get_natural_delta(self):
        return naturalsize(self.delta, gnu=True)

    def get_command(self):
        #return ' '.join(self.pd.cmd)
        return self.pd.cmd[0]

    def __str__(self):
        sign = ''
        if self.percent > 0:
            sign = '+'
        return self.get_natural_delta() + ' ' + sign + str(self.percent) + ': ' + self.get_command()


class ProcessSnapshot(object):
    __slots__ = ['pid', 'name', 'cmd', 'mem']

    def __init__(self, pid, name, cmd, mem):
        self.pid = pid
        self.name = name
        self.cmd = cmd
        self.mem = int(mem)

    def __str__(self):
        return "{pid}: {mem} {name} {cmd}".format(
                pid=self.pid, mem=naturalsize(self.mem, gnu=True), name=self.name, cmd=' '.join(self.cmd))

    def __repr__(self):
        return "{cls}(pid={pid}, name={name}, cmd={cmd}, mem={mem})".format(
                cls=self.__class__.__name__, pid=self.pid, name=self.name,
                cmd=self.cmd, mem=self.mem)

    def __sub__(self, other):
        if self.pid == other.pid and self.name == other.name:
            return ProcessDelta(self, other)
        else:
            raise ProcessDeltaException("{sp}: {sn} != {op}: {on}".format(
                sp=self.pid, sn=self.name, op=other.pid, on=other.name))

    def __lt__(self, other):
        """to allow sorting by mem"""
        return self.mem < other.mem


class PSDict(OrderedDict):
    def get_data(self, pss=False):
        for p in psutil.process_iter():
            with p.oneshot():
                if pss:
                    mem = p.memory_full_info().pss
                else:
                    mem = p.memory_info().rss
                pd = ProcessSnapshot(pid=p.pid, name=p.name(),
                                     cmd=p.cmdline(), mem=mem)
            if pd.mem > 0:
                self[pd.pid] = pd
        return self

    def sort(self):
        """return sorted by value"""
        return PSDict(sorted(self.items(), key=lambda x: x[1]))


class MemLeakFinder(object):
    def __init__(self, stdscr):
        self.reference = PSDict().get_data()
        self.stdscr = stdscr

    def refresh(self):
        self.stdscr.clear()
        new_data = PSDict().get_data()
        new_data = new_data.sort()
        for pid in new_data:
            if pid in self.reference:
                try:
                    delta = new_data[pid] - self.reference[pid]
                except ProcessDeltaException:
                    self.reference[pid] = new_data[pid]
            else:
                self.reference[pid] = new_data[pid]
            try:
                self.stdscr.addstr(str(delta))
            except curses.error:
                pass
            #self.stdscr.addstr(str(new_data[pid]))
            #print(delta, new_data[pid])
        self.stdscr.refresh()

    def infinite(self):
        while(True):
            self.refresh()
            sleep(1)


def main(stdscr):
    stdscr.clear()
    m = MemLeakFinder(stdscr)
    m.infinite()


def test():
    ps = PSDict()
    ps.get_data()
    ps = ps.sort()
    print(ps)


if __name__ == '__main__':
    curses.wrapper(main)
