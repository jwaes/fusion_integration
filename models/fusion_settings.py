# Copyright 2024 jaco tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Settings configuration for Fusion 360 integration."""
    _inherit = 'res.config.settings'

    fusion_default_folder_id = fields.Many2one(
        'stock.location',
        string='Default Folder for Fusion Products',
        config_parameter='fusion_integration.default_folder_id',
        domain="[('usage', '=', 'internal'), '|', "
               "('company_id', '=', False), ('company_id', '=', company_id)]",
        help='Default location for newly created products from Fusion 360'
    )
