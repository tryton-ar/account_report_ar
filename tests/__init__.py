# The COPYRIGHT file at the top level of this repository contains the
# full copyright notices and license terms.

try:
    from trytond.modules.sale_pos_ar.tests.test_account_report_ar import suite
except ImportError:
    from .test_account_report_ar import suite

__all__ = ['suite']
