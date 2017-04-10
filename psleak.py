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
        if p2.mem != 0:
            self.percent = ((self.delta / p2.mem) * 100)
        else:
            self.percent = 9999

    def human_readable(self):
        return naturalsize(self.delta, gnu=True)

    def get_command(self):
        #return ' '.join(self.pd.cmd)
        return self.pd.cmd[0]

    def __str__(self):
        sign = ''
        if self.percent > 0:
            sign = '+'
        return self.human_readable() + ' ' + sign + str(self.percent) + ': ' + self.get_command()

    def __lt__(self, other):
        """to allow sorting by mem"""
        return self.delta < other.delta


class ProcessSnapshot(object):
    __slots__ = ['pid', 'name', 'cmd', 'mem']

    def __init__(self, pid, name, cmd, mem):
        self.pid = pid
        self.name = name
        self.cmd = cmd
        self.mem = int(mem)

    def human_readable(self):
        return naturalsize(self.mem, gnu=True)

    def __str__(self):
        return "{pid}: {mem} {name} {cmd}".format(
                pid=self.pid, mem=self.human_readable(), name=self.name, cmd=' '.join(self.cmd))

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
    """store memory information for all processes"""
    def get_data(self, pss=False):
        # for each process on system
        for p in psutil.process_iter():
            with p.oneshot():
                # use pss for more precise measurement but is requires root
                if pss:
                    mem = p.memory_full_info().pss
                else:
                    mem = p.memory_info().rss
                pd = ProcessSnapshot(pid=p.pid, name=p.name(),
                                     cmd=p.cmdline(), mem=mem)
            # the key of the dict is the process pid
            if pd.mem > 0:
                self[pd.pid] = pd
        return self

    def sort(self):
        """return sorted by value - so memory usage"""
        return PSDict(sorted(self.items(), key=lambda x: x[1]))

    def __sub__(self, other):
        return DeltaDict(new=self, old=other)


class DeltaDict(OrderedDict):
    def __init__(self, new, old):
        for key in new:
            if key not in old:
                # emulate old process consuming zero memory if not existing
                old[key] = self.emulate_zero(new[key])
            try:
                delta = new[key] - old[key]
            except ProcessDeltaException:
                # was not the same process so assume it is new so old is zero
                delta = new[key] - self.emulate_zero(new[key])
            self[key] = delta

    @staticmethod
    def emulate_zero(ps):
        """ps should be a ProcessSnapshot
        creates a made up historical snapshot consuming zero memory"""
        return ProcessSnapshot(pid=ps.pid, name=ps.name, cmd=ps.cmd, mem=0)

    def sort(self):
        """return sorted by value - so memory delta"""
        return PSDict(sorted(self.items(), key=lambda x: x[1]))


class MemLeakFinder(object):
    def __init__(self, stdscr, pss=False):
        self.reference = PSDict().get_data(pss=pss)
        self.stdscr = stdscr

    def line_output(self, counter, key, item):
        self.stdscr.addstr(counter, 0, str(key))
        self.stdscr.addstr(counter, 10, str(item))

    def output(self, delta_dict):
        counter = 0
        for key in delta_dict:
            if counter < 20:
                self.line_output(counter, key, delta_dict[key])
            counter += 1
        self.stdscr.refresh()

    def refresh(self):
        self.stdscr.clear()
        new_data = PSDict().get_data()
        new_data = new_data.sort()
        counter = 0
        delta_dict = new_data - self.reference
        delta_dict = delta_dict.sort()
        self.output(delta_dict)

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
