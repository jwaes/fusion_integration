# Copyright 2024 jaco tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class ProductAttribute(models.Model):
    """Extend product.attribute to add fusion-specific fields."""
    _inherit = 'product.attribute'

    is_fusion_attribute = fields.Boolean(
        string='Is Fusion Attribute',
        default=False,
        help='This attribute was generated from Fusion 360 configuration'
    )
    fusion_parameter_name = fields.Char(
        string='Fusion Parameter Name',
        help='Original parameter name in Fusion 360'
    )

    @api.onchange('fusion_parameter_name', 'is_fusion_attribute')
    def _onchange_fusion_parameter_name(self):
        """Update name when fusion parameter name changes."""
        for record in self:
            if record.is_fusion_attribute and record.fusion_parameter_name:
                record.name = f'Fusion: {record.fusion_parameter_name}'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set name for fusion attributes."""
        for vals in vals_list:
            if vals.get('is_fusion_attribute') and vals.get('fusion_parameter_name'):
                vals['name'] = f'Fusion: {vals["fusion_parameter_name"]}'
        return super().create(vals_list)

    def write(self, vals):
        """Override write to update name when fusion parameter changes."""
        if 'fusion_parameter_name' in vals and self.filtered('is_fusion_attribute'):
            vals['name'] = f'Fusion: {vals["fusion_parameter_name"]}'
        elif 'is_fusion_attribute' in vals and vals['is_fusion_attribute']:
            for record in self:
                if record.fusion_parameter_name:
                    vals['name'] = f'Fusion: {record.fusion_parameter_name}'
        return super().write(vals)
