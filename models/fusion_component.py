# Copyright 2024 jaco tech
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

    # region Fields
    name = fields.Char(
        required=True,
        tracking=True,
        help="Name of the component as defined in Fusion 360"
    )
    fusion_id = fields.Char(
        string='Fusion ID',
        required=True,
        tracking=True,
        help="Unique identifier from Fusion 360"
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        tracking=True,
        help="Related product template in Odoo"
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product Variant',
        tracking=True,
        help="Specific product variant when component has configurations"
    )
    internal_identifier = fields.Char(
        related='product_id.default_code',
        string='Internal Reference',
        store=True,
        tracking=True,
        help="Internal reference from the related product"
    )
    parent_id = fields.Many2one(
        'fusion.component',
        string='Parent Assembly',
        tracking=True,
        help="Parent assembly component"
    )
    child_ids = fields.One2many(
        'fusion.component',
        'parent_id',
        string='Components',
        help="Child components in this assembly"
    )
    version = fields.Char(
        tracking=True,
        help="Version information from Fusion 360"
    )
    component_type = fields.Selection(
        selection=[
            ('component', 'Component'),
            ('assembly', 'Assembly')
        ],
        required=True,
        tracking=True,
        help="Type of the component in Fusion 360"
    )
    configuration_name = fields.Char(
        string='Configuration Name',
        tracking=True,
        help="Name of the active configuration in Fusion 360"
    )
    configuration_values = fields.Text(
        string='Configuration Values',
        tracking=True,
        help="JSON representation of configuration parameters"
    )
    last_modified = fields.Datetime(
        string='Last Modified',
        required=True,
        tracking=True,
        help="Last modification timestamp from Fusion 360"
    )
    version_identifier = fields.Char(
        string='Version ID',
        required=True,
        tracking=True,
        help='Unique identifier for this version of the component'
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        help="Company this component belongs to"
    )
    active = fields.Boolean(
        default=True,
        help="Set to false to hide the component without removing it"
    )
    # endregion

    # region Constraints and SQL Constraints
    _sql_constraints = [
        ('fusion_id_company_uniq',
         'unique(fusion_id, configuration_name, company_id)',
         'Component with this Fusion ID and configuration already exists!')
    ]
    # endregion

    # region CRUD Methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add additional logic."""
        return super().create(vals_list)

    def write(self, vals):
        """Override write to add additional logic."""
        return super().write(vals)
    # endregion

    # region Action Methods
    @api.model
    def create_from_fusion(self, vals):
        """Create or update component from Fusion 360 data.

        Args:
            vals (dict): Values for component creation/update

        Returns:
            fusion.component: Created or updated component record
        """
        self.ensure_one()
        existing = self._find_existing_component(vals)
        if existing:
            return existing.write(vals)

        product_tmpl = self._create_or_get_product_template(vals)
        vals['product_tmpl_id'] = product_tmpl.id

        if vals.get('configuration_values'):
            self._handle_configuration(vals, product_tmpl)
        else:
            vals['product_id'] = product_tmpl.product_variant_id.id

        vals['company_id'] = self.env.company.id
        return self.create(vals)
    # endregion

    # region Helper Methods
    def _find_existing_component(self, vals):
        """Find existing component based on Fusion ID and configuration.

        Args:
            vals (dict): Component values

        Returns:
            fusion.component: Existing component record if found
        """
        return self.search([
            ('fusion_id', '=', vals['fusion_id']),
            ('configuration_name', '=', vals.get('configuration_name', False)),
            ('company_id', '=', self.env.company.id),
        ])

    def _create_or_get_product_template(self, vals):
        """Create or get product template for component.

        Args:
            vals (dict): Component values

        Returns:
            product.template: Product template record
        """
        if vals.get('product_tmpl_id'):
            return self.env['product.template'].browse(vals['product_tmpl_id'])

        default_folder_id = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'fusion_integration.default_folder_id',
                False
            )
        )

        return self.env['product.template'].create({
            'name': vals['name'],
            'type': 'product',
            'detailed_type': 'product',
            'property_stock_inventory': default_folder_id or False,
            'company_id': self.env.company.id,
        })

    def _handle_configuration(self, vals, product_tmpl):
        """Handle component configuration and create product variant.

        Args:
            vals (dict): Component values
            product_tmpl (product.template): Product template record
        """
        config_values = json.loads(vals['configuration_values'])
        
        for attr_name, attr_value in config_values.items():
            attribute = self._get_or_create_attribute(attr_name)
            attr_value_obj = self._get_or_create_attribute_value(
                attribute, str(attr_value))
            self._update_attribute_line(product_tmpl, attribute, attr_value_obj)

        product_variant = self._get_or_create_variant(
            product_tmpl, config_values)
        vals['product_id'] = product_variant.id

    def _get_or_create_attribute(self, attr_name):
        """Get or create product attribute.

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
        """Get or create attribute value.

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

    def _update_attribute_line(self, product_tmpl, attribute, attr_value):
        """Update product template attribute line.

        Args:
            product_tmpl (product.template): Product template record
            attribute (product.attribute): Attribute record
            attr_value (product.attribute.value): Attribute value record
        """
        attr_line = product_tmpl.attribute_line_ids.filtered(
            lambda l: l.attribute_id.id == attribute.id
        )

        if not attr_line:
            self.env['product.template.attribute.line'].create({
                'product_tmpl_id': product_tmpl.id,
                'attribute_id': attribute.id,
                'value_ids': [(4, attr_value.id)]
            })
        elif attr_value not in attr_line.value_ids:
            attr_line.write({'value_ids': [(4, attr_value.id)]})

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
    # endregion
