# Copyright 2024 jaco tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestFusionSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def setUp(self):
        super().setUp()
        self.test_location = self.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
        })

    def test_01_default_folder_setting(self):
        """Test setting and retrieving default folder."""
        # Create settings record
        settings = self.env['res.config.settings'].create({
            'fusion_default_folder_id': self.test_location.id,
        })
        settings.execute()

        # Check if parameter was saved
        param_value = self.env['ir.config_parameter'].sudo().get_param(
            'fusion_integration.default_folder_id'
        )
        self.assertEqual(int(param_value), self.test_location.id)

        # Check if new settings instance gets the value
        new_settings = self.env['res.config.settings'].create({})
        new_settings.execute()
        self.assertEqual(
            new_settings.fusion_default_folder_id.id,
            self.test_location.id
        )

    def test_02_folder_company_restriction(self):
        """Test company restrictions on folder selection."""
        company2 = self.env['res.company'].create({'name': 'Test Company'})
        location2 = self.env['stock.location'].create({
            'name': 'Company 2 Location',
            'usage': 'internal',
            'company_id': company2.id,
        })

        settings = self.env['res.config.settings'].create({})
        
        # Check domain includes company filter
        domain = settings._fields['fusion_default_folder_id'].domain
        self.assertIn(('usage', '=', 'internal'), domain)
        self.assertIn('|', domain)
        self.assertIn(('company_id', '=', False), domain)
        self.assertIn(('company_id', '=', 'company_id'), domain)
