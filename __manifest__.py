# Copyright 2024 jaco tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Fusion 360 Integration',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Integration with Autodesk Fusion 360',
    'author': 'jaco tech',
    'website': 'https://jaco.tech',
    'license': 'AGPL-3',
    'depends': ['mrp', 'base'],
    'data': [
        'security/fusion_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/product_attribute_views.xml',
        'views/fusion_component_views.xml',
        'views/fusion_menu.xml',
    ],
    'demo': [],
    'test': [
        'tests/test_fusion_component.py',
        'tests/test_fusion_settings.py',
    ],
    'installable': True,
    'application': True,
    'assets': {},
    'development_status': 'Beta',
    'maintainers': ['jwaes'],
}
