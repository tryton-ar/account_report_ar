# This file is part of the account_report_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.wizard import Wizard, StateView, StateReport, Button
from trytond.report import Report
from trytond.pool import Pool
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


class PrinChartAccountBalance(Wizard):
    'Balance of Accounts'
    __name__ = 'account.print_chart_account_balance'

    start = StateView('account.account.context',
        'account.account_context_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('account.chart_account_balance')

    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            'fiscalyear': (self.start.fiscalyear and
                self.start.fiscalyear.id or None),
            'posted': self.start.posted,
            }
        return action, data


class ChartAccountBalance(Report):
    __name__ = 'account.chart_account_balance'

    @classmethod
    def get_context(cls, records, header, data):
        pool = Pool()
        Company = pool.get('company.company')
        FiscalYear = pool.get('account.fiscalyear')
        Account = pool.get('account.account')

        report_context = super().get_context(records, header, data)

        company = Company(data.get('company'))
        report_context['company'] = company
        fiscalyear_id = data.get('fiscalyear',
            FiscalYear.find(company).id)
        report_context['fiscalyear'] = (fiscalyear_id and
            FiscalYear(fiscalyear_id).rec_name or '')

        records = []
        with Transaction().set_context(
                fiscalyear=fiscalyear_id,
                posted=data.get('posted', False)):
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
            'debit': account.debit,
            'credit': account.credit,
            'balance': account.balance,
            'view': bool(account.childs),
            })
        for child in account.childs:
            cls._add_childs(child, records)

    @classmethod
    def _compute_level(cls, account):
        if not account.parent:
            return 0
        return 1 + cls._compute_level(account.parent)
