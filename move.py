# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.pool import Pool, PoolMeta
from decimal import Decimal

import logging
logger = logging.getLogger(__name__)

__all__ = ['GeneralJournal']


class GeneralJournal:
    __metaclass__ = PoolMeta
    __name__ = 'account.move.general_journal'

    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('account.move')

        clause = [
            ('date', '>=', data['from_date']),
            ('date', '<=', data['to_date']),
            ('period.fiscalyear.company', '=', data['company']),
            ]
        if data['posted']:
            clause.append(('state', '=', 'posted'))
        return Move.search(clause,
                 order=[('date', 'ASC'), ('post_number', 'ASC')])

    @classmethod
    def get_context(cls, records, data):
        report_context = super(GeneralJournal, cls).get_context(records, data)
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
