'''
Backtrader data class
'''
import backtrader.feeds as btfeed


import datetime

from backtrader import TimeFrame
from backtrader import date2num

from backtrader import Strategy

class StockHLOC(btfeed.GenericCSVData):
    params = (
        ('fromdate', datetime.datetime(1900, 12, 31)),
        ('todate', datetime.datetime(2100, 12, 31)),
        ('nullvalue', 0.0),
        ('dtformat', ('%Y-%m-%d %H:%M:%S')),
        ('tmformat', ('%H:%M:%S')),
        ('datetime', 0),
        ('time', -1),
        ('high', 2),
        ('low', 3),
        ('open', 4),
        ('close', 5),
        ('volume', 6),
        ('openinterest', -1)
    )

    def _loadline(self, linetokens):
        # Datetime needs special treatment
        dtfield = linetokens[self.p.datetime]
        if self._dtstr:
            dtformat = self.p.dtformat

            if self.p.time >= 0:
                # add time value and format if it's in a separate field
                dtfield += 'T' + linetokens[self.p.time]
                dtformat += 'T' + self.p.tmformat


            dt = datetime.datetime.strptime(dtfield, dtformat)
        else:
            dt = self._dtconvert(dtfield)

        if self.p.timeframe >= TimeFrame.Days:
            # check if the expected end of session is larger than parsed
            if self._tzinput:
                dtin = self._tzinput.localize(dt)  # pytz compatible-ized
            else:
                dtin = dt

            dtnum = date2num(dtin)  # utc'ize

            dteos = datetime.datetime.combine(dt.date(), self.p.sessionend)
            dteosnum = self.date2num(dteos)  # utc'ize

            if dteosnum > dtnum:
                self.lines.datetime[0] = dteosnum
            else:
                # Avoid reconversion if already converted dtin == dt
                self.l.datetime[0] = date2num(dt) if self._tzinput else dtnum
        else:
            self.lines.datetime[0] = date2num(dt)

        # The rest of the fields can be done with the same procedure
        for linefield in (x for x in self.getlinealiases() if x != 'datetime'):
            # Get the index created from the passed params
            csvidx = getattr(self.params, linefield)

            if csvidx is None or csvidx < 0:
                # the field will not be present, assignt the "nullvalue"
                csvfield = self.p.nullvalue
            else:
                # get it from the token
                csvfield = linetokens[csvidx]

            if csvfield == '':
                # if empty ... assign the "nullvalue"
                csvfield = self.p.nullvalue

            # get the corresponding line reference and set the value
            line = getattr(self.lines, linefield)
            line[0] = float(float(csvfield))

        return True