# This file is part of the account_report_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import logging
from decimal import Decimal

from trytond.pool import PoolMeta

logger = logging.getLogger(__name__)


class GeneralJournal(metaclass=PoolMeta):
    __name__ = 'account.move.general_journal'

    @classmethod
    def get_context(cls, records, header, data):
        report_context = super().get_context(records, header, data)
        report_context['get_total_move'] = cls.get_total_move
        return report_context

    @classmethod
    def get_total_move(self, lines, type):
        amount = Decimal('0')
        if type == 'debit':
            for line in lines:
                amount += line.debit
        elif type == 'credit':
            for line in lines:
                amount += line.credit
        return amount
