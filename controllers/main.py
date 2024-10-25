from odoo import http
from odoo.http import request
import json

class FusionController(http.Controller):
    
    @http.route('/fusion_api/component', type='json', auth='user')
    def create_component(self, **post):
        """API endpoint to create/update components from Fusion 360"""
        try:
            component = request.env['fusion.component'].create_from_fusion(post)
            return {'success': True, 'id': component.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/fusion_api/bom', type='json', auth='api_key')
    def create_bom(self, **post):
        """API endpoint to create/update BOMs from Fusion 360"""
        try:
            # Get or create the parent component
            parent = request.env['fusion.component'].search([
                ('fusion_id', '=', post['parent_id'])
            ])
            
            if not parent:
                return {'success': False, 'error': 'Parent component not found'}
                
            # Create/Update BOM
            bom_vals = {
                'product_tmpl_id': parent.product_id.id,
                'type': 'normal'
            }
            
            bom = request.env['mrp.bom'].create(bom_vals)
            
            # Add BOM lines
            for component in post['components']:
                child = request.env['fusion.component'].search([
                    ('fusion_id', '=', component['fusion_id'])
                ])
                if child:
                    request.env['mrp.bom.line'].create({
                        'bom_id': bom.id,
                        'product_id': child.product_id.product_variant_id.id,
                        'product_qty': component['quantity']
                    })
            
            return {'success': True, 'id': bom.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
