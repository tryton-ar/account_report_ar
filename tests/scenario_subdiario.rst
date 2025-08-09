==================
subdiario Scenario
==================

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
    ...     create_pos, get_pos, get_tax
    >>> today = dt.date.today()

Install account_report_ar::

    >>> config = activate_modules('account_report_ar')

Create company::

    >>> currency = get_currency('ARS')
    >>> _ = create_company(currency=currency)
    >>> company = get_company()
    >>> tax_identifier = company.party.identifiers.new()
    >>> tax_identifier.type = 'ar_vat'
    >>> tax_identifier.code = '30710158254' # gcoop CUIT
    >>> company.party.iva_condition = 'responsable_inscripto'
    >>> company.party.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
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

Create taxes::

    >>> sale_tax = get_tax('IVA Ventas 21%')
    >>> purchase_tax = get_tax('IVA Compras 21%')
    >>> purchase_tax_nogravado = get_tax('IVA Compras No Gravado')

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier',
    ...     iva_condition='responsable_inscripto',
    ...     vat_number='33333333339')
    >>> supplier.account_payable = account_payable
    >>> supplier.save()
    >>> customer = Party(name='Customer',
    ...     iva_condition='responsable_inscripto',
    ...     vat_number='33333333339')
    >>> customer.account_receivable = account_receivable
    >>> customer.save()

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
    >>> invoice = Invoice()
    >>> invoice.party = customer
    >>> invoice.pos = pos
    >>> invoice.invoice_date = period.start_date
    >>> line = invoice.lines.new()
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('40')
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
    >>> invoice.total_amount
    Decimal('242.00')
    >>> invoice = Invoice()
    >>> invoice.party = customer
    >>> invoice.pos = pos
    >>> invoice.invoice_date = period.start_date
    >>> line = invoice.lines.new()
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
    >>> invoice = Invoice()
    >>> invoice.type = 'in'
    >>> invoice.party = supplier
    >>> invoice.tipo_comprobante = '001'
    >>> invoice.reference = '00001-00000312'
    >>> invoice.invoice_date = period.start_date
    >>> line = invoice.lines.new()
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('40')
    >>> invoice.click('validate_invoice')
    >>> invoice.state
    'validated'
    >>> bool(invoice.move)
    True
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
    >>> invoice = Invoice()
    >>> invoice.type = 'in'
    >>> invoice.party = supplier
    >>> invoice.tipo_comprobante = '011'
    >>> invoice.reference = '00002-00000061'
    >>> invoice.invoice_date = period.start_date
    >>> line = invoice.lines.new()
    >>> line.account = account_expense
    >>> line.taxes.append(purchase_tax_nogravado)
    >>> line.description = 'Test'
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('20')
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

Execute subdiario sale report::

    >>> subdiario_sale = Wizard('subdiario.sale')
    >>> subdiario_sale.form.from_date = period.start_date
    >>> subdiario_sale.form.to_date = period.end_date
    >>> subdiario_sale.execute('print_')
    >>> extension, content, _, name = subdiario_sale.actions[0]
    >>> # content
    >>> extension
    'ods'
    >>> name
    'Subdiario de Ventas'

    >>> subdiario_sale = Wizard('subdiario.sale.type')
    >>> subdiario_sale.form.from_date = period.start_date
    >>> subdiario_sale.form.to_date = period.end_date
    >>> subdiario_sale.execute('print_')
    >>> extension, content, _, name = subdiario_sale.actions[0]
    >>> # content
    >>> extension
    'ods'
    >>> name
    'Subdiario de Ventas por tipo de comprobante'

    >>> subdiario_sale = Wizard('subdiario.sale.subdivision')
    >>> subdiario_sale.form.from_date = period.start_date
    >>> subdiario_sale.form.to_date = period.end_date
    >>> subdiario_sale.execute('print_')
    >>> extension, content, _, name = subdiario_sale.actions[0]
    >>> # content
    >>> extension
    'ods'
    >>> name
    'Subdiario de Ventas por jurisdicción'

    >>> subdiario_purchase = Wizard('subdiario.purchase')
    >>> subdiario_purchase.form.from_date = period.start_date
    >>> subdiario_purchase.form.to_date = period.end_date
    >>> subdiario_purchase.execute('print_')
    >>> extension, content, _, name = subdiario_purchase.actions[0]
    >>> # content
    >>> extension
    'ods'
    >>> name
    'Subdiario de Compras'
