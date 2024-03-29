# This file is part of the account_report_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from . import move
from . import account


def register():
    Pool.register(
        move.GeneralJournal,
        account.ChartAccount,
        module='account_report_ar', type_='report')
