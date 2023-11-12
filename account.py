# This file is part of the account_report_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal

from trytond.report import Report
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class ChartAccount(Report):
    __name__ = 'account.chart_account'

    @classmethod
    def get_context(cls, records, header, data):
        pool = Pool()
        Company = pool.get('company.company')
        Account = pool.get('account.account')

        report_context = super().get_context(records, header, data)

        company = Company(Transaction().context.get('company'))
        report_context['company'] = company

        records = []
        parent_accounts = Account.search([
            ('parent', '=', None),
            ('company', '=', company),
            ])
        for account in parent_accounts:
            cls._add_childs(account, records)
        report_context['records'] = records

        return report_context

    @classmethod
    def _add_childs(cls, account, records):
        level = cls._compute_level(account)
        records.append({
            'code': account.code,
            'name': account.name,
            'level': level,
            })
        for child in account.childs:
            cls._add_childs(child, records)

    @classmethod
    def _compute_level(cls, account):
        if not account.parent:
            return 0
        return 1 + cls._compute_level(account.parent)


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
