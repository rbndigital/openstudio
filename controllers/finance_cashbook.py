# -*- coding: utf-8 -*-

@auth.requires(auth.has_membership(group_id='Admins') or \
               auth.has_permission('read', 'accounting_cashbooks'))
def index():
    """

    :return:
    """
    response.title = T('c_finance_cashbook_title')

    if session.finance_cashbook_date:
        date = session.finance_cashbook_date
    else:
        date = TODAY_LOCAL
        session.finance_cashbook_date = date

    response.subtitle = SPAN(
        T('c_finance_cashbook_subtitle'), ': ',
        date.strftime(DATE_FORMAT)
    )
    response.view = 'general/only_content_no_box.html'

    debit = get_debit(date)
    debit_total = debit['total']

    credit = get_credit(date)
    credit_total = credit['total']

    balance = index_get_balance(debit_total, credit_total)

    content = DIV(
        balance,
        debit['column_content'],
        credit['column_content'],
        _class='row'
    )

    header_tools = DIV(
        get_day_chooser(date)
    )

    return dict(
        content=content,
        header_tools=header_tools
    )


def get_debit(date):
    """
    Populate the credit column
    :param date: datetime.date
    :return: dict['total'] & dict['column_content']
    """
    total = 0

    additional_items = get_additional_items(date, 'debit')
    total += additional_items['total']

    # Class balance (total revenue - teacher payments)
    classes_balance = get_debit_classes(date, 'balance')
    total += classes_balance['total']

    # Class teacher payments
    teacher_payments = get_debit_classes(date, 'teacher_payments')
    total += teacher_payments['total']


    column = DIV(
        H4(T("c_finance_cashbook_get_debit_title")),
        additional_items['box'],
        classes_balance['box'],
        teacher_payments['box'],
        _class=' col-md-6'

    )

    return dict(
        total = total,
        column_content = column
    )


def get_credit(date):
    """
    Populate the credit column
    :param date: datetime.date
    :return: dict['total'] & dict['column_content']
    """
    total = 0

    additional_items = get_additional_items(date, 'credit')
    total += additional_items['total']

    column = DIV(
        H4(T("c_finance_cashbook_get_credit_title")),
        additional_items['box'],
        _class=' col-md-6'

    )

    return dict(
        total = total,
        column_content = column
    )


def get_additional_items(date, booking_type):
    """

    :param date:
    :return: dict
    """
    from openstudio.os_accounting_cashbooks_additional_items import AccountingCashbooksAdditionalItems

    acai = AccountingCashbooksAdditionalItems()
    result = acai.list_formatted(date, date, booking_type)
    acai_debit_list = result['table']
    acai_debit_total = result['total']

    if booking_type == 'debit':
        box_class = 'box-success'
    elif booking_type == 'credit':
        box_class = 'box-danger'

    additional_items = DIV(
        DIV(H3("Additional items", _class='box-title'),
            DIV(os_gui.get_button(
                'add',
                URL('additional_item_add', vars={'booking_type': booking_type})),
                _class='box-tools pull-right'
            ),
            _class='box-header'),
        DIV(acai_debit_list, _class='box-body no-padding'),
        _class='box ' + box_class
    )

    return dict(
        box = additional_items,
        total = acai_debit_total
    )


def index_get_balance(debit_total=0, credit_total=0):
    """

    :return:
    """
    note = ''
    link_opening=URL('opening_balance_add')
    opening_balance = 0
    info = SPAN()

    row = db.accounting_cashbooks_balance(
        BalanceDate = session.finance_cashbook_date,
        BalanceType = 'opening'
    )

    if row:
        note = row.Note
        link_opening=URL('opening_balance_edit', vars={'acbID': row.id})
        opening_balance = row.Amount

        au = db.auth_user(row.auth_user_id)
        info = SPAN(
            T("c_finance_cashbook_get_balance_opening_balance_set_by"), ' ',
            A(au.display_name,
              _href=URL('customers', 'edit', args=[au.id])), ' ',
            # T("@"), ' ',
            # row.CreatedOn.strftime(DATETIME_FORMAT),
            XML(' &bull; '),
            _class="text-muted"
        )

    link_set_opening_balance = A(
        T("c_finance_cashbook_get_balance_set_opening_balance"),
        _href=link_opening,
    )
    info.append(link_set_opening_balance)

    balance = (opening_balance + debit_total) - credit_total
    balance_class = ''
    if balance < 0:
        balance_class = 'text-red bold'

    box = DIV(DIV(
        DIV(
            H3(T("general_summary"), _class='box-title'),
            DIV(info, _class='box-tools pull-right'),
            _class='box-header'
        ),
        DIV(note,
            _class='box-body'
        ),
        DIV(DIV(DIV(DIV(H5(T("c_finance_cashbook_opening_balance"), _class='description-header'),
                        DIV(represent_float_as_amount(opening_balance), _class='description-text'),
                        _class='description-block'),
                    _class='col-md-3 border-right'),
                DIV(DIV(H5(T("c_finance_cashbook_get_balance_debit"), _class='description-header'),
                        SPAN(represent_float_as_amount(debit_total), _class='description-text'),
                        _class='description-block'),
                    _class='col-md-3 border-right'),
                DIV(DIV(H5(T("c_finance_cashbook_get_balance_credit"), _class='description-header'),
                        SPAN(represent_float_as_amount(credit_total), _class='description-text'),
                        _class='description-block'),
                    _class='col-md-3 border-right'),
                DIV(DIV(H5(T("c_finance_cashbook_get_balance_total"), _class='description-header'),
                        SPAN(represent_float_as_amount(balance), _class='description-text ' + balance_class),
                        _class='description-block'),
                    _class='col-md-3'),
                _class='row'),
            _class='box-footer'
        ),
        _class='box box-primary'
    ), _class='col-md-12')

    return box


@auth.requires(auth.has_membership(group_id='Admins') or \
               auth.has_permission('read', 'accounting_cashbooks'))
def set_date():
    """
    Set date for cashbook
    :return:
    """
    from general_helpers import datestr_to_python

    date_formatted = request.vars['date']
    date = datestr_to_python(DATE_FORMAT, request.vars['date'])

    session.finance_cashbook_date = date

    redirect(URL('cashbook'))


def get_day_chooser(date):
    """
    Set day for cashbook
    :param date: datetime.date
    :return: HTML prev/next buttons
    """
    yesterday = (date - datetime.timedelta(days=1)).strftime(DATE_FORMAT)
    tomorrow = (date + datetime.timedelta(days=1)).strftime(DATE_FORMAT)

    link = 'set_date'
    url_prev = URL(link, vars={'date': yesterday})
    url_next = URL(link, vars={'date': tomorrow})
    url_today = URL(link, vars={'date': TODAY_LOCAL.strftime(DATE_FORMAT)})

    today = ''
    if date != TODAY_LOCAL:
        today = A(os_gui.get_fa_icon('fa fa-calendar-o'), ' ', T("general_today"),
                 _href=url_today,
                 _class='btn btn-default')

    previous = A(I(_class='fa fa-angle-left'),
                 _href=url_prev,
                 _class='btn btn-default')
    nxt = A(I(_class='fa fa-angle-right'),
            _href=url_next,
            _class='btn btn-default')

    return DIV(previous, today, nxt, _class='btn-group pull-right')


def index_return_url(var=None):
    return URL('index')


@auth.requires_login()
def opening_balance_add():
    """
    Set opening balance
    """
    from openstudio.os_forms import OsForms

    date = session.finance_cashbook_date

    response.title = T('c_finance_cashbook_title')
    response.subtitle = SPAN(
        T("c_finance_cashbook_subtitle"), ': ',
        date.strftime(DATE_FORMAT), ' - ',
        T("c_finance_cashbook_opening_balance_add_subtitle")

    )
    response.view = 'general/only_content.html'

    return_url = index_return_url()

    db.accounting_cashbooks_balance.BalanceDate.default = date
    db.accounting_cashbooks_balance.BalanceType.default = 'opening'

    os_forms = OsForms()
    result = os_forms.get_crud_form_create(
        db.accounting_cashbooks_balance,
        return_url,
        message_record_created=T("general_saved")
    )

    form = result['form']
    back = os_gui.get_button('back', return_url)

    content = form

    return dict(content=content,
                save=result['submit'],
                back=back)


@auth.requires_login()
def opening_balance_edit():
    """
    Set opening balance
    """
    from openstudio.os_forms import OsForms

    acbID = request.vars['acbID']

    date = session.finance_cashbook_date

    response.title = T('c_finance_cashbook_title')
    response.subtitle = SPAN(
        T("c_finance_cashbook_subtitle"), ': ',
        date.strftime(DATE_FORMAT), ' - ',
        T("c_finance_cashbook_opening_balance_edit_subtitle")

    )
    response.view = 'general/only_content.html'

    return_url = index_return_url()

    os_forms = OsForms()
    result = os_forms.get_crud_form_update(
        db.accounting_cashbooks_balance,
        return_url,
        acbID,
        message_record_updated=T("general_saved"),
    )

    form = result['form']
    back = os_gui.get_button('back', return_url)

    content = form

    return dict(content=content,
                save=result['submit'],
                back=back)


@auth.requires_login()
def additional_item_add():
    """
    Set opening balance
    """
    from openstudio.os_forms import OsForms

    date = session.finance_cashbook_date
    db.accounting_cashbooks_additional_items.BookingDate.default = date

    booking_type = request.vars['booking_type']
    if booking_type == 'credit':
        db.accounting_cashbooks_additional_items.BookingType.default = 'credit'
        subtitle_type = T("general_credit")
    elif booking_type == 'debit':
        db.accounting_cashbooks_additional_items.BookingType.default = 'debit'
        subtitle_type = T("general_debit")

    response.title = T('c_finance_cashbook_title')
    response.subtitle = SPAN(
        T("c_finance_cashbook_subtitle"), ': ',
        date.strftime(DATE_FORMAT), ' - ',
        T("c_finance_cashbook_additional_item_add_subtitle") % subtitle_type
    )
    response.view = 'general/only_content.html'

    return_url = index_return_url()


    os_forms = OsForms()
    result = os_forms.get_crud_form_create(
        db.accounting_cashbooks_additional_items,
        return_url,
        message_record_created=T("general_saved")
    )

    form = result['form']
    back = os_gui.get_button('back', return_url)

    content = form

    return dict(content=content,
                save=result['submit'],
                back=back)


@auth.requires_login()
def additional_item_edit():
    """
    Set opening balance
    """
    from openstudio.os_forms import OsForms

    acaiID = request.vars['aciID']

    date = session.finance_cashbook_date

    item = db.accounting_cashbooks_additional_items(aciID)

    booking_type = item.BookingType
    if booking_type == 'credit':
        subtitle_type = T("general_credit")
    elif booking_type == 'debit':
        subtitle_type = T("general_debit")

    response.title = T('c_finance_cashbook_title')
    response.subtitle = SPAN(
        T("c_finance_cashbook_subtitle"), ': ',
        date.strftime(DATE_FORMAT), ' - ',
        T("c_finance_cashbook_additional_item_edit_subtitle") % subtitle_type

    )
    response.view = 'general/only_content.html'

    return_url = index_return_url()

    os_forms = OsForms()
    result = os_forms.get_crud_form_update(
        db.accounting_cashbooks_additional_items,
        return_url,
        acaiID,
        message_record_updated=T("general_saved"),
    )

    form = result['form']
    back = os_gui.get_button('back', return_url)

    content = form

    return dict(content=content,
                save=result['submit'],
                back=back)


@auth.requires(auth.has_membership(group_id='Admins') or \
               auth.has_permission('delete', 'accounting_cashbooks_additional_items'))
def additional_item_delete():
    """
    Delete cashbook item
    :return:
    """
    aciaID = request.vars['aciaID']

    query = (db.accounting_cashbooks_additional_items.id == aciaID)
    db(query).delete()

    redirect(index_return_url())


def get_debit_classes(date, list_type='balance'):
    """
    return a box and total of class profit or class revenue
    :param list_type: one of 'revenue' or 'teacher_payments'
    :param date: datetime.date
    :return:
    """
    from general_helpers import max_string_length
    from openstudio.os_reports import Reports

    reports = Reports()
    revenue = reports.get_classes_revenue_summary_day(session.finance_cashbook_date)

    if list_type == 'balance':
        total = revenue['revenue_total']
        box_title = T("Class balance")
    elif list_type == 'teacher_payments':
        total = revenue['teacher_payments']
        box_title = T("Teacher payments")

    header = THEAD(TR(
        TH(T("general_time")),
        TH(T("general_location")),
        TH(T("general_classtype")),
        TH(T("general_amount")),
    ))

    table = TABLE(header, _class='table table-striped table-hover')
    for cls in revenue['data']:
        if list_type == 'balance':
            amount = cls['Balance']
        elif list_type == 'teacher_payments':
            amount = cls['TeacherPayment']

        tr = TR(
            TD(cls['Starttime']),
            TD(max_string_length(cls['Location'], 18)),
            TD(max_string_length(cls['ClassType'], 18)),
            TD(represent_float_as_amount(amount))
        )

        table.append(tr)

    # Footer total
    table.append(TFOOT(TR(
        TH(),
        TH(),
        TH(T('general_total')),
        TH(represent_float_as_amount(revenue['balance']))
    )))

    box = DIV(
        DIV(H3(box_title, _class='box-title'), _class='box-header'),
        DIV(table, _class='box-body no-padding'),
        _class='box box-success',
    )

    return dict(
        box = box,
        total = total
    )

