#!/usr/bin/env python3
"""find the process leaking memory"""

from collections import OrderedDict
from time import sleep
from humanize import naturalsize
import psutil

__author__ = 'Piotr Jankowski'


class ProcessDeltaException(Exception):
    pass


class ProcessDelta(object):
    __slots__ = ['delta', 'percent', 'pd']

    def __init__(self, p1, p2):
        self.pd = p1
        self.delta = p1.pss - p2.pss
        self.percent = ((self.delta / p2.pss) * 100)

    def __str__(self):
        sign = ''
        if self.percent > 0:
            sign = '+'
        return naturalsize(self.delta, gnu=True) + ' ' + sign + str(self.percent) + ': ' + ' '.join(self.pd.cmd)


class ProcessData(object):
    __slots__ = ['pid', 'name', 'cmd', 'pss']

    def __init__(self, pid, name, cmd, pss):
        self.pid = pid
        self.name = name
        self.cmd = cmd
        self.pss = int(pss)

    def __str__(self):
        return "{pid}: {pss} {name} {cmd}".format(
                pid=self.pid, pss=naturalsize(self.pss, gnu=True), name=self.name, cmd=' '.join(self.cmd))

    def __repr__(self):
        return "{cls}(pid={pid}, name={name}, cmd={cmd}, pss={pss})".format(
                cls=self.__class__.__name__, pid=self.pid, name=self.name,
                cmd=self.cmd, pss=self.pss)

    def __sub__(self, other):
        if self.pid == other.pid and self.name == other.name:
            return ProcessDelta(self, other)
        else:
            raise ProcessDeltaException("{sp}: {sn} != {op}: {on}".format(
                sp=self.pid, sn=self.name, op=other.pid, on=other.name))

    def __lt__(self, other):
        """to allow sorting by pss"""
        return self.pss < other.pss


class PSDict(OrderedDict):
    def read(self):
        for p in psutil.process_iter():
            with p.oneshot():
                pd = ProcessData(pid=p.pid, name=p.name(),
                        cmd=p.cmdline(), pss=p.memory_full_info().pss)
            if pd.pss > 0:
                self[pd.pid] = pd

    def sort(self):
        """return sorted by value"""
        return PSDict(sorted(self.items(), key=lambda x: x[1]))


class MemLeakFinder(object):
    def __init__(self):
        self.reference = PSDict()
        self.reference.read()

    def refresh(self):
        new_data = PSDict() 
        new_data.read()
        new_data = new_data.sort()
        for pid in new_data:
            if pid in self.reference:
                try:
                    delta = new_data[pid] - self.reference[pid]
                except ProcessDeltaException:
                    self.reference[pid] = new_data[pid]
            else:
                self.reference[pid] = new_data[pid]
            print(delta, new_data[pid])

    def infinite(self):
        while(True):
            sleep(2)
            self.refresh()
        

def main():
    m = MemLeakFinder()
    m.infinite()

def test():
    ps = PSDict()
    ps.read()
    ps = ps.sort()
    print(ps)


if __name__ == '__main__':
    main()
