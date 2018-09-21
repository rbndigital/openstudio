# -*- coding: utf-8 -*-

from gluon import *


class OSExactOnline:
    def get_api(self):
        """
        Return ExactAPI linked to config and token storage
        """
        import os
        from exactonline.api import ExactApi
        from exactonline.exceptions import ObjectDoesNotExist
        from exactonline.storage import IniStorage

        storage = self.get_storage()

        return ExactApi(storage=storage)


    def get_storage(self):
        """
        Get ini storage
        """
        import os
        from ConfigParser import NoOptionError
        from exactonline.storage import IniStorage

        class MyIniStorage(IniStorage):
            def get_response_url(self):
                "Configure your custom response URL."
                return self.get_base_url() + '/exact_online/oauth2_success/'

        request = current.request

        config_file = os.path.join(
            request.folder,
            'private',
            'eo_config.ini'
        )

        return MyIniStorage(config_file)


    def create_sales_entry(self, os_invoice):
        """
        :param os_customer: OsCustomer object
        :param os_invoice: OsInvoice Object
        :return:
        """
        from os_customer import Customer
        from tools import OsTools

        os_tools = OsTools()
        authorized = os_tools.get_sys_property('exact_online_authorized')

        if not authorized:
            self._log_error(
                'create',
                'sales_entry',
                os_invoice.invoice.id,
                "Exact online integration not authorized"
            )

            return


        import pprint

        from ConfigParser import NoOptionError
        from exactonline.http import HTTPError

        storage = self.get_storage()
        api = self.get_api()
        cuID = os_invoice.get_linked_customer_id()
        print "Customer:"
        print cuID
        os_customer = Customer(os_invoice.get_linked_customer_id())

        try:
            selected_division = int(storage.get('transient', 'division'))
        except NoOptionError:
            selected_division = None

        print "division:"
        print selected_division

        amounts = os_invoice.get_amounts()

        remote_journal = 70
        invoice_date = os_invoice.invoice.DateCreated
        local_invoice_number = os_invoice.invoice.id

        invoice_data = {
            'AmountDC': str(amounts.TotalPriceVAT),  # DC = default currency
            'AmountFC': str(amounts.TotalPriceVAT),  # FC = foreign currency
            'EntryDate': invoice_date.strftime('%Y-%m-%dT%H:%M:%SZ'),  # pretend we're in UTC
            'Customer': os_customer.row.exact_online_relation_id,
            'Description': os_invoice.invoice.Description,
            'Journal': remote_journal,  # 70 "Verkoopboek"
            'ReportingPeriod': invoice_date.month,
            'ReportingYear': invoice_date.year,
            'SalesEntryLines': [],
            'VATAmountDC': str(amounts.VAT),
            'VATAmountFC': str(amounts.VAT),
            'YourRef': local_invoice_number,
            # must start uniquely at the start of a year, defaults to:
            # YYJJ0001 where YY=invoice_date.year, and JJ=remote_journal
            # 'InvoiceNumber': '%d%d%04d' % (invoice_date.year, remote_journal,
            #                                int(local_invoice_number)),
            'InvoiceNumber': local_invoice_number
        }

        error = False

        try:
            result = api.invoices.create(invoice_data)
            eoseID = result['ID']
            print "Create invoice result:"
            pp = pprint.PrettyPrinter(depth=6)
            pp.pprint(result)

        except HTTPError as e:
            error = True
            self._log_error(
                'create',
                'sales_entry',
                os_invoice.invoice.id,
                e
            )

        if error:
            return False

        return eoseID


    def get_sales_entry_lines(self, os_invoice):
        """
        :param os_invoice: Invoice object
        :return: SalesEntryLines dict
        """
        items = os_invoice.get_invoice_items_rows()

        lines = []

        for item in items:
            lines.append({
                'AmountDC': item.TotalPrice,
                'AmountFC': item.TotalPrice,
                'Description': item.Description,
                'GLAccount': item.GLAccount
            })


    def update_sales_entry(self, os_invoice):
        """
        :param os_customer: OsCustomer object
        :return: None
        """
        from os_customer import Customer
        from tools import OsTools

        os_tools = OsTools()
        authorized = os_tools.get_sys_property('exact_online_authorized')

        if not authorized:
            self._log_error(
                'update',
                'sales_entry',
                os_invoice.invoice.id,
                "Exact online integration not authorized"
            )

            return

        eoseID = os_invoice.invoice.ExactOnlineSalesEntryID

        print eoseID
        if not eoseID:
            print 'creating sales entry'
            self.create_sales_entry(os_invoice)
            return


        import pprint

        from ConfigParser import NoOptionError
        from exactonline.http import HTTPError

        storage = self.get_storage()
        api = self.get_api()
        cuID = os_invoice.get_linked_customer_id()
        print "Customer:"
        print cuID
        os_customer = Customer(os_invoice.get_linked_customer_id())

        try:
            selected_division = int(storage.get('transient', 'division'))
        except NoOptionError:
            selected_division = None

        print "division:"
        print selected_division

        amounts = os_invoice.get_amounts()

        remote_journal = 70
        invoice_date = os_invoice.invoice.DateCreated
        local_invoice_number = os_invoice.invoice.id

        invoice_data = {
            'AmountDC': str(amounts.TotalPriceVAT),  # DC = default currency
            'AmountFC': str(amounts.TotalPriceVAT),  # FC = foreign currency
            'EntryDate': invoice_date.strftime('%Y-%m-%dT%H:%M:%SZ'),  # pretend we're in UTC
            'Customer': os_customer.row.exact_online_relation_id,
            'Description': os_invoice.invoice.Description,
            'Journal': remote_journal,  # 70 "Verkoopboek"
            'ReportingPeriod': invoice_date.month,
            'ReportingYear': invoice_date.year,
            'SalesEntryLines': [],
            'VATAmountDC': str(amounts.VAT),
            'VATAmountFC': str(amounts.vAT),
            'YourRef': local_invoice_number,
            # must start uniquely at the start of a year, defaults to:
            # YYJJ0001 where YY=invoice_date.year, and JJ=remote_journal
            'InvoiceNumber': '%d%d%04d' % (invoice_date.year, remote_journal,
                                           int(local_invoice_number)),
        }

        error = False

        try:
            result = api.invoices.create(invoice_data)
            print "Create invoice result:"
            pp = pprint.PrettyPrinter(depth=6)
            pp.pprint(result)

        except HTTPError as e:
            error = True
            self._log_error(
                'create',
                'sales_entry',
                os_invoice.invoice.id,
                e
            )

        if error:
            return False


    def create_relation(self, os_customer):
        """
        :param os_customer: OsCustomer object
        :return: exact online relation id
        """
        from tools import OsTools

        os_tools = OsTools()
        authorized = os_tools.get_sys_property('exact_online_authorized')

        if not authorized:
            self._log_error(
                'create',
                'relation',
                os_customer.row.id,
                "Exact online integration not authorized"
            )

            return

        else:
            import pprint

            from ConfigParser import NoOptionError
            from exactonline.http import HTTPError

            storage = self.get_storage()
            api = self.get_api()

            try:
                selected_division = int(storage.get('transient', 'division'))
            except NoOptionError:
                selected_division = None

            print "division:"
            print selected_division

            relation_dict = {
                "Name": os_customer.row.display_name,
                "ChamberOfCommerce": os_customer.row.company_registration,
                "Code": os_customer.row.id,
                "Division": selected_division,
                "Email": os_customer.row.email,
                "Status": "C", # Customer
                "VATNumber": os_customer.row.company_tax_registration
            }

            error = False

            try:
                result = api.relations.create(relation_dict)
                rel_id = result['ID']
                print rel_id
                os_customer.row.exact_online_relation_id = rel_id
                os_customer.row.update_record()

            except HTTPError as e:
                error = True
                self._log_error(
                    'create',
                    'relation',
                    os_customer.row.id,
                    e
                )

            if error:
                return False

            return rel_id


    def update_relation(self, os_customer):
        """
        :param os_customer: OsCustomer object
        :return: dict(error=True|False, message='')
        """
        from tools import OsTools

        os_tools = OsTools()
        authorized = os_tools.get_sys_property('exact_online_authorized')

        if not authorized:
            self._log_error(
                'create',
                'relation',
                os_customer.row.id,
                "Exact online integration not authorized"
            )

            return

        print 'update'

        eoID = os_customer.row.exact_online_relation_id

        print eoID
        if not eoID:
            print 'creating relation'
            self.create_relation(os_customer)
            return

        import pprint

        from ConfigParser import NoOptionError
        from exactonline.http import HTTPError

        storage = self.get_storage()
        api = self.get_api()

        try:
            selected_division = int(storage.get('transient', 'division'))
        except NoOptionError:
            selected_division = None

        print "division:"
        print selected_division

        relation_dict = {
            "Name": os_customer.row.display_name,
            "ChamberOfCommerce": os_customer.row.company_registration,
            "Code": os_customer.row.id,
            "Email": os_customer.row.email,
            "Status": "C", # Customer
            "VATNumber": os_customer.row.company_tax_registration
        }

        error = False
        message = ''

        print 'update'
        print eoID

        # api.relations.update(eoID, relation_dict)
        try:
            api.relations.update(eoID, relation_dict)
        except HTTPError as e:
            error = True
            message = e

            self._log_error(
                'update',
                'relation',
                os_customer.row.id,
                e
            )


        return dict(error=error, message=message)


    def get_bankaccount(self, os_customer):
        """
        :param os_customer: OsCustomer object
        :return: ExactOnline bankaccount for os_customer
        """
        eoID = os_customer.row.exact_online_relation_id

        import pprint

        from ConfigParser import NoOptionError
        from exactonline.http import HTTPError

        storage = self.get_storage()
        api = self.get_api()

        try:
            return api.bankaccounts.filter(account=eoID)
        except HTTPError as e:
            error = True
            self._log_error(
                'get',
                'bankaccount',
                os_customer.row.id,
                e
            )
            return False


    def create_bankaccount(self, os_customer, os_customer_payment_info):
        """
        :param os_customer: OsCustomer object
        :return: None
        """
        from exactonline.http import HTTPError
        from tools import OsTools

        os_tools = OsTools()
        authorized = os_tools.get_sys_property('exact_online_authorized')

        if not authorized:
            self._log_error(
                'create',
                'bankaccount',
                os_customer.row.id,
                "Exact online integration not authorized"
            )

            return

        api = self.get_api()
        eoID = os_customer.row.exact_online_relation_id

        bank_account_dict = {
            'Account': eoID,
            'BankAccount': os_customer_payment_info.row.AccountNumber,
            'BankAccountHolderName': os_customer_payment_info.row.AccountHolder,
            'BICCode': os_customer_payment_info.row.BIC
        }

        try:
            result = api.bankaccounts.create(bank_account_dict)
            os_customer_payment_info.row.exact_online_bankaccount_id = result['ID']
            os_customer_payment_info.row.update_record()

        except HTTPError as e:
            error = True
            self._log_error(
                'create',
                'bankaccount',
                os_customer_payment_info.row.id,
                e
            )


    def update_bankaccount(self, os_customer, os_customer_payment_info):
        """
        :param os_customer: OsCustomer object
        :return: None
        """
        from exactonline.http import HTTPError
        from tools import OsTools

        os_tools = OsTools()
        authorized = os_tools.get_sys_property('exact_online_authorized')

        if not authorized:
            self._log_error(
                'update',
                'bankaccount',
                os_customer.row.id,
                "Exact online integration not authorized"
            )

            return

        api = self.get_api()
        eoID = os_customer.row.exact_online_relation_id

        exact_account = self.get_bankaccount(os_customer)
        if not len(exact_account):
            self.create_bankaccount(os_customer, os_customer_payment_info)

        print exact_account

        bank_account_dict = {
            'Account': eoID,
            'BankAccount': os_customer_payment_info.row.AccountNumber,
            'BankAccountHolderName': os_customer_payment_info.row.AccountHolder,
            'BICCode': os_customer_payment_info.row.BIC
        }

        try:
            print 'updating bank details'
            print bank_account_dict

            api.bankaccounts.update(
                os_customer_payment_info.row.exact_online_bankaccount_id,
                bank_account_dict
            )

        except HTTPError as e:
            error = True
            self._log_error(
                'update',
                'bankaccount',
                os_customer.row.id,
                e
            )


    def _log_error(self, action, object, object_id, result):
        """
        :param action: should be in ['create', 'read', 'update', 'delete']
        :param object: object name
        :param object_id: object id
        :param message: string
        :return: None
        """
        db = current.db

        db.integration_exact_online_log.insert(
            ActionName = action,
            ObjectName = object,
            ObjectID = object_id,
            ActionResult = result,
            Status = 'fail'
        )



# class ExactOnlineStorage(ExactOnlineConfig):
#     def get_response_url(self):
#         """Configure your custom response URL."""
#         return self.get_base_url() + '/exact_online/oauth2_success/'
#
#     def get(self, section, option):
#         option = self._get_value(section, option)
#
#         if not option:
#             raise ValueError('Required option is not set')
#
#         return option
#
#     def set(self, section, option, value):
#         self._set_value(section, option, value)
#
#
#     def _get_value(self, section, option):
#         """
#
#         :param section:
#         :param option:
#         :return:
#         """
#         db = current.db
#
#         query = (db.integration_exact_online_storage.ConfigSection == section) & \
#                 (db.integration_exact_online_storage.ConfigOption == option)
#         rows = db(query).select(db.integration_exact_online_storage.ConfigValue)
#
#         value = None
#         if rows:
#             value = rows.first().ConfigValue
#
#         return value
#
#
#     def _set_value(self, section, option, value):
#         """
#
#         :param section:
#         :param option:
#         :return:
#         """
#         db = current.db
#
#         query = (db.integration_exact_online_storage.ConfigSection == section) & \
#                 (db.integration_exact_online_storage.ConfigOption == option)
#         rows = db(query).select(db.integration_exact_online_storage.ALL)
#
#         if rows:
#             row = rows.first()
#             row.ConfigValue = value
#             row.update_record()
#         else:
#             db.integration_exact_online_storage.insert(
#                 ConfigSection = section,
#                 ConfigOption = option,
#                 ConfigValue = value
#             )
#
