====================
RG3685 AFIP Scenario
====================

Imports::
    >>> import datetime as dt
    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.tools import file_open
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart
    >>> from trytond.modules.account_ar.tests.tools import get_accounts
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences
    >>> from trytond.modules.account_invoice_ar.tests.tools import \
    ...     create_pos, get_pos, get_invoice_types, get_tax
    >>> from trytond.tests.tools import activate_modules, assertEqual, assertTrue

    >>> # today = dt.date.today()
    >>> today = dt.date(2019, 1, 1)

Install account_report_ar::

    >>> config = activate_modules('account_report_ar')

Create company::

    >>> currency = get_currency('ARS')
    >>> currency.afip_code = 'PES'
    >>> currency.save()
    >>> _ = create_company(currency=currency)
    >>> company = get_company()
    >>> tax_identifier = company.party.identifiers.new()
    >>> tax_identifier.type = 'ar_vat'
    >>> tax_identifier.code = '30710158254' # gcoop CUIT
    >>> company.party.iva_condition = 'responsable_inscripto'
    >>> company.party.save()

Set employee::

    >>> User = Model.get('res.user')
    >>> Party = Model.get('party.party')
    >>> Employee = Model.get('company.employee')
    >>> employee_party = Party(name="Employee")
    >>> employee_party.save()
    >>> employee = Employee(party=employee_party)
    >>> employee.save()
    >>> user = User(config.user)
    >>> user.employees.append(employee)
    >>> user.employee = employee
    >>> user.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company, today))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]
    >>> period_ids = [p.id for p in fiscalyear.periods]

Create chart of accounts::

    >>> _ = create_chart(company, chart='account_ar.root_ar')
    >>> accounts = get_accounts(company)
    >>> account_receivable = accounts['receivable']
    >>> account_payable = accounts['payable']
    >>> account_revenue = accounts['revenue']
    >>> account_expense = accounts['expense']
    >>> account_tax = accounts['sale_tax']
    >>> account_cash = accounts['cash']

Create point of sale::

    >>> _ = create_pos(company)
    >>> pos = get_pos()
    >>> invoice_types = get_invoice_types()

Create taxes::

    >>> sale_tax = get_tax('IVA Ventas 21%')
    >>> purchase_tax = get_tax('IVA Compras 21%')
    >>> purchase_tax_nogravado = get_tax('IVA Compras No Gravado')

Create payment method::

    >>> Journal = Model.get('account.journal')
    >>> PaymentMethod = Model.get('account.invoice.payment.method')
    >>> Sequence = Model.get('ir.sequence')
    >>> journal_cash, = Journal.find([('type', '=', 'cash')])
    >>> payment_method = PaymentMethod()
    >>> payment_method.name = 'Cash'
    >>> payment_method.journal = journal_cash
    >>> payment_method.credit_account = account_cash
    >>> payment_method.debit_account = account_cash
    >>> payment_method.save()

Create Write Off method::

    >>> WriteOff = Model.get('account.move.reconcile.write_off')
    >>> journal_writeoff = Journal(name='Write-Off', type='write-off')
    >>> journal_writeoff.save()
    >>> writeoff_method = WriteOff()
    >>> writeoff_method.name = 'Rate loss'
    >>> writeoff_method.journal = journal_writeoff
    >>> writeoff_method.credit_account = account_expense
    >>> writeoff_method.debit_account = account_expense
    >>> writeoff_method.save()

Create Supplier Responsable Inscripto::

    >>> Party = Model.get('party.party')
    >>> supplier_ri = Party(name='Supplier',
    ...     iva_condition='responsable_inscripto',
    ...     vat_number='33333333339')
    >>> supplier_ri.account_payable = account_payable
    >>> supplier_ri.save()

Create Supplier Monotributo::

    >>> Party = Model.get('party.party')
    >>> supplier_mn = Party(name='Supplier',
    ...     iva_condition='monotributo',
    ...     vat_number='33333333339')
    >>> supplier_mn.account_payable = account_payable
    >>> supplier_mn.save()

Create Customer Responsable Inscripto::

    >>> customer_ri = Party(name='Customer',
    ...     iva_condition='responsable_inscripto',
    ...     vat_number='33333333339')
    >>> customer_ri.account_receivable = account_receivable
    >>> customer_ri.save()

Create Customer Monotributo::

    >>> customer_mn = Party(name='Customer',
    ...     iva_condition='monotributo',
    ...     vat_number='33333333339')
    >>> customer_mn.account_receivable = account_receivable
    >>> customer_mn.save()

Create account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = account_expense
    >>> account_category.account_revenue = account_revenue
    >>> account_category.customer_taxes.append(sale_tax)
    >>> account_category.supplier_taxes.append(purchase_tax)
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.list_price = Decimal('40')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

Create customer invoices::

    >>> Invoice = Model.get('account.invoice')
    >>> InvoiceLine = Model.get('account.invoice.line')
    >>> invoice = Invoice(type='out')
    >>> invoice.party = customer_ri
    >>> invoice.pos = pos
    >>> # invoice.payment_term = payment_term
    >>> invoice.invoice_date = period.start_date
    >>> line = InvoiceLine()
    >>> invoice.lines.append(line)
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('40')
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
    >>> invoice.total_amount
    Decimal('242.00')
    >>> invoice = Invoice(type='out')
    >>> invoice.party = customer_mn
    >>> invoice.pos = pos
    >>> # invoice.payment_term = payment_term
    >>> invoice.invoice_date = period.start_date
    >>> line = InvoiceLine()
    >>> invoice.lines.append(line)
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('20')
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
    >>> invoice.total_amount
    Decimal('121.00')

Create supplier invoices::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice(type='in')
    >>> invoice.party = supplier_ri
    >>> invoice.tipo_comprobante = '001'
    >>> invoice.ref_pos_number = '1'
    >>> invoice.ref_voucher_number = '312'
    >>> invoice.invoice_date = period.start_date
    >>> line = InvoiceLine()
    >>> invoice.lines.append(line)
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('40')
    >>> invoice.save()
    >>> invoice.click('validate_invoice')
    >>> invoice.state
    'validated'
    >>> bool(invoice.move)
    True
    >>> invoice.move.state
    'draft'
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
    >>> bool(invoice.move)
    True
    >>> invoice.move.state
    'posted'
    >>> invoice.untaxed_amount
    Decimal('200.00')
    >>> invoice.tax_amount
    Decimal('42.00')
    >>> invoice.total_amount
    Decimal('242.00')
    >>> invoice = Invoice(type='in')
    >>> invoice.party = supplier_mn
    >>> invoice.tipo_comprobante = '011'
    >>> invoice.ref_pos_number = '1'
    >>> invoice.ref_voucher_number = '061'
    >>> invoice.invoice_date = period.start_date
    >>> line = InvoiceLine()
    >>> invoice.lines.append(line)
    >>> line.account = account_expense
    >>> line.taxes.append(purchase_tax_nogravado)
    >>> line.description = 'Test'
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('20')
    >>> invoice.save()
    >>> invoice.click('validate_invoice')
    >>> invoice.state
    'validated'
    >>> bool(invoice.move)
    True
    >>> invoice.move.state
    'draft'
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
    >>> bool(invoice.move)
    True
    >>> invoice.move.state
    'posted'
    >>> invoice.untaxed_amount
    Decimal('100.00')
    >>> invoice.tax_amount
    Decimal('0.00')
    >>> invoice.total_amount
    Decimal('100.00')

Generate rg3685 report::

    >>> Attachment = Model.get('ir.attachment')
    >>> rg3685 = Wizard('citi.afip.wizard')
    >>> rg3685.form.csv_format = False
    >>> rg3685.form.period = period
    >>> rg3685.execute('exportar')
    >>> rg3685.state
    'exportar'
    >>> len(rg3685.form.sale_docs) > 0
    True
    >>> len(rg3685.form.sale_aliqs) > 0
    True
    >>> len(rg3685.form.purchase_docs) > 0
    True
    >>> len(rg3685.form.purchase_aliqs) > 0
    True
    >>> # rg3685.form.sale_docs
    >>> # rg3685.form.sale_aliqs
    >>> # rg3685.form.purchase_docs
    >>> # rg3685.form.purchase_aliqs
    >>> with file_open('account_report_ar/tests/VENTAS_RG3685.txt', 'rb') as f:
    ...     rg3685.form.sale_docs == f.read()
    True
    >>> with file_open('account_report_ar/tests/VENTAS_ALICUOTAS_RG3685.txt', 'rb') as f:
    ...     rg3685.form.sale_aliqs == f.read()
    True
    >>> with file_open('account_report_ar/tests/COMPRAS_ALICUOTAS_RG3685.txt', 'rb') as f:
    ...     rg3685.form.purchase_aliqs == f.read()
    True
    >>> with file_open('account_report_ar/tests/COMPRAS_RG3685.txt', 'rb') as f:
    ...     rg3685.form.purchase_docs == f.read()
    True
