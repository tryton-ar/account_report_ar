# This file is part of the account_report_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from functools import reduce

from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateReport, Button
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction


class PrintGeneralJournalStart(ModelView):
    "General Journal"
    __name__ = 'account.print_move_general_journal.start'

    company = fields.Many2One('company.company', "Company", required=True)
    fiscalyear = fields.Many2One('account.fiscalyear', "Fiscal Year",
        domain=[('company', '=', Eval('company', -1))], required=True)

    @classmethod
    def default_company(cls):
        return Transaction().context.get('company')

    @fields.depends('company', 'fiscalyear')
    def on_change_company(self):
        if self.fiscalyear and self.fiscalyear.company != self.company:
            self.fiscalyear = None


class PrintGeneralJournal(Wizard):
    'General Journal'
    __name__ = 'account.print_move_general_journal'

    start = StateView('account.print_move_general_journal.start',
        'account_report_ar.print_move_general_journal_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('account.move.general_journal')

    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            'fiscalyear': (self.start.fiscalyear and
                self.start.fiscalyear.id or None),
            }
        return action, data


class GeneralJournal(metaclass=PoolMeta):
    __name__ = 'account.move.general_journal'

    @classmethod
    def get_context(cls, records, header, data):
        pool = Pool()
        Company = pool.get('company.company')
        Move = pool.get('account.move')

        if not records and 'fiscalyear' in data:
            records = Move.search([
                ('state', '=', 'posted'),
                ('period.fiscalyear', '=', data['fiscalyear']),
                ])
        records = sorted(records, key=lambda i: (i.post_number or '', i.date))
        context = Transaction().context
        report_context = super().get_context(records, header, data)
        report_context['company'] = Company(
            data.get('company', context['company']))
        report_context['get_total_move'] = cls.get_total_move
        return report_context

    @classmethod
    def get_total_move(self, lines, type_):
        if type_ == 'debit':
            return reduce(lambda a, b: a + b, [l.debit for l in lines])
        elif type_ == 'credit':
            return reduce(lambda a, b: a + b, [l.credit for l in lines])
