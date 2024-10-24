# Copyright 2024 Your Company Name
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import json
import logging

_logger = logging.getLogger(__name__)


class FusionComponent(models.Model):
    """
    Model representing a component from Fusion 360.
    Links Fusion 360 components with Odoo products and manages their synchronization.
    """
    _name = 'fusion.component'
    _description = 'Fusion 360 Component'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, id'

    # [Previous field definitions remain unchanged...]

    def _get_or_create_attribute(self, attr_name):
        """Get or create product attribute, marking it as fusion-generated.

        Args:
            attr_name (str): Attribute name

        Returns:
            product.attribute: Attribute record
        """
        attribute = self.env['product.attribute'].search([
            ('fusion_parameter_name', '=', attr_name),
            ('is_fusion_attribute', '=', True),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not attribute:
            attribute = self.env['product.attribute'].create({
                'name': f'Fusion: {attr_name}',
                'fusion_parameter_name': attr_name,
                'is_fusion_attribute': True,
                'company_id': self.env.company.id,
            })

        return attribute

    def _get_or_create_attribute_value(self, attribute, value):
        """Get or create attribute value for fusion attribute.

        Args:
            attribute (product.attribute): Attribute record
            value (str): Value to create

        Returns:
            product.attribute.value: Attribute value record
        """
        attr_value = self.env['product.attribute.value'].search([
            ('attribute_id', '=', attribute.id),
            ('name', '=', value),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not attr_value:
            attr_value = self.env['product.attribute.value'].create({
                'attribute_id': attribute.id,
                'name': value,
                'company_id': self.env.company.id,
            })

        return attr_value

    def _get_or_create_variant(self, product_tmpl, config_values):
        """Get or create product variant based on configuration.

        Args:
            product_tmpl (product.template): Product template record
            config_values (dict): Configuration values

        Returns:
            product.product: Product variant record
        """
        domain = [
            ('product_tmpl_id', '=', product_tmpl.id),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', self.env.company.id)
        ]

        for attr_name, attr_value in config_values.items():
            attribute = self._get_or_create_attribute(attr_name)
            attr_value_obj = self._get_or_create_attribute_value(
                attribute, str(attr_value))
            domain.append((
                'product_template_attribute_value_ids.product_attribute_value_id',
                '=',
                attr_value_obj.id
            ))

        product_variant = self.env['product.product'].search(domain, limit=1)
        if not product_variant:
            product_variant = product_tmpl._create_product_variant(
                product_tmpl._get_first_possible_combination()
            )

        return product_variant

    # [Rest of the class implementation remains unchanged...]
