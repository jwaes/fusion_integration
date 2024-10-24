# Copyright 2024 jaco tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import json


class TestFusionComponent(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create test location
        cls.test_location = cls.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
        })

        # Set default folder in settings
        cls.env['ir.config_parameter'].sudo().set_param(
            'fusion_integration.default_folder_id',
            cls.test_location.id
        )

    def setUp(self):
        super().setUp()
        self.simple_component_vals = {
            'name': 'Test Component',
            'fusion_id': 'FUSION_123',
            'component_type': 'component',
            'last_modified': '2024-01-01 00:00:00',
            'version_identifier': 'V1',
        }
        self.config_component_vals = {
            'name': 'Config Component',
            'fusion_id': 'FUSION_456',
            'component_type': 'component',
            'last_modified': '2024-01-01 00:00:00',
            'version_identifier': 'V1',
            'configuration_name': 'Config1',
            'configuration_values': json.dumps({
                'Length': '100',
                'Width': '50',
            }),
        }

    def test_01_create_simple_component(self):
        """Test creation of a simple component without configuration."""
        component = self.env['fusion.component'].create_from_fusion(
            self.simple_component_vals)
        
        self.assertTrue(component)
        self.assertEqual(component.name, 'Test Component')
        self.assertTrue(component.product_tmpl_id)
        self.assertTrue(component.product_id)
        self.assertEqual(
            component.product_tmpl_id.property_stock_inventory,
            self.test_location
        )

    def test_02_create_configured_component(self):
        """Test creation of a component with configuration."""
        component = self.env['fusion.component'].create_from_fusion(
            self.config_component_vals)
        
        self.assertTrue(component)
        self.assertEqual(component.configuration_name, 'Config1')
        
        # Check product template attributes
        product_tmpl = component.product_tmpl_id
        self.assertEqual(len(product_tmpl.attribute_line_ids), 2)
        
        # Check attribute values
        length_attr = product_tmpl.attribute_line_ids.filtered(
            lambda l: l.attribute_id.name == 'Fusion: Length')
        self.assertTrue(length_attr)
        self.assertEqual(length_attr.value_ids[0].name, '100')

    def test_03_update_existing_component(self):
        """Test updating an existing component."""
        component = self.env['fusion.component'].create_from_fusion(
            self.simple_component_vals)
        
        updated_vals = dict(
            self.simple_component_vals,
            name='Updated Component'
        )
        updated_component = self.env['fusion.component'].create_from_fusion(
            updated_vals)
        
        self.assertEqual(component, updated_component)
        self.assertEqual(updated_component.name, 'Updated Component')

    def test_04_component_constraints(self):
        """Test unique constraints on components."""
        self.env['fusion.component'].create_from_fusion(self.simple_component_vals)
        
        with self.assertRaises(ValidationError):
            self.env['fusion.component'].create_from_fusion(
                self.simple_component_vals)

    def test_05_create_assembly(self):
        """Test creation of an assembly with subcomponents."""
        # Create child component
        child = self.env['fusion.component'].create_from_fusion(
            self.simple_component_vals)
        
        # Create assembly
        assembly_vals = {
            'name': 'Test Assembly',
            'fusion_id': 'FUSION_789',
            'component_type': 'assembly',
            'last_modified': '2024-01-01 00:00:00',
            'version_identifier': 'V1',
            'child_ids': [(4, child.id)],
        }
        assembly = self.env['fusion.component'].create_from_fusion(assembly_vals)
        
        self.assertTrue(assembly)
        self.assertEqual(assembly.component_type, 'assembly')
        self.assertEqual(len(assembly.child_ids), 1)
        self.assertEqual(assembly.child_ids[0], child)

    def test_06_configuration_variants(self):
        """Test product variant creation for different configurations."""
        # Create first configuration
        component1 = self.env['fusion.component'].create_from_fusion(
            self.config_component_vals)
        
        # Create second configuration
        config2_vals = dict(
            self.config_component_vals,
            configuration_name='Config2',
            configuration_values=json.dumps({
                'Length': '200',
                'Width': '100',
            })
        )
        component2 = self.env['fusion.component'].create_from_fusion(
            config2_vals)
        
        self.assertEqual(
            component1.product_tmpl_id,
            component2.product_tmpl_id
        )
        self.assertNotEqual(component1.product_id, component2.product_id)
        self.assertEqual(
            len(component1.product_tmpl_id.product_variant_ids),
            2
        )

    def test_07_fusion_attributes(self):
        """Test fusion-specific attribute handling."""
        component = self.env['fusion.component'].create_from_fusion(
            self.config_component_vals)
        
        # Check attribute properties
        product_tmpl = component.product_tmpl_id
        for attr_line in product_tmpl.attribute_line_ids:
            self.assertTrue(attr_line.attribute_id.is_fusion_attribute)
            self.assertTrue(attr_line.attribute_id.fusion_parameter_name)
            self.assertTrue(attr_line.attribute_id.name.startswith('Fusion: '))

        # Create manual attribute
        manual_attr = self.env['product.attribute'].create({
            'name': 'Manual Attribute',
            'is_fusion_attribute': False,
        })
        
        # Verify it's not picked up in fusion attribute search
        attribute = self.env['fusion.component']._get_or_create_attribute('Manual Attribute')
        self.assertNotEqual(attribute.id, manual_attr.id)
        self.assertTrue(attribute.is_fusion_attribute)
        self.assertEqual(attribute.fusion_parameter_name, 'Manual Attribute')

    def test_08_attribute_naming(self):
        """Test fusion attribute naming convention."""
        component = self.env['fusion.component'].create_from_fusion(
            self.config_component_vals)
        
        for attr_line in component.product_tmpl_id.attribute_line_ids:
            attr = attr_line.attribute_id
            self.assertTrue(attr.name.startswith('Fusion: '))
            self.assertEqual(
                attr.fusion_parameter_name,
                attr.name.replace('Fusion: ', '')
            )
