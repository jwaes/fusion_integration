# Copyright 2024 jaco tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Settings configuration for Fusion 360 integration."""
    _inherit = 'res.config.settings'

    fusion_default_category_id = fields.Many2one(
        'product.category',
        string='Default Category for Fusion Products',
        config_parameter='fusion_integration.default_category_id',
        help='Default category for newly created products from Fusion 360'
    )
