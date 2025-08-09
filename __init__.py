# This file is part of the account_report_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool

from . import move
from . import account

__all__ = ['register']

def register():
    Pool.register(
        move.PrintGeneralJournalStart,
        module='account_report_ar', type_='model')
    Pool.register(
        move.PrintGeneralJournal,
        account.PrinChartAccountBalance,
        module='account_report_ar', type_='wizard')
    Pool.register(
        move.GeneralJournal,
        account.ChartAccount,
        account.ChartAccountBalance,
        module='account_report_ar', type_='report')
