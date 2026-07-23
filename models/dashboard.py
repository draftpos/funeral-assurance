from odoo import models, fields

class FuneralDashboard(models.Model):
    _name = 'funeral.dashboard'
    _description = 'Funeral Dashboard'

    name = fields.Char(default='Dashboard')
    agent_count = fields.Integer(compute='_compute_counts', string='Agents')
    city_count = fields.Integer(compute='_compute_counts', string='Cities')
    region_count = fields.Integer(compute='_compute_counts', string='Regions')
    branch_count = fields.Integer(compute='_compute_counts', string='Branches')
    product_count = fields.Integer(compute='_compute_counts', string='Products')
    policy_count = fields.Integer(compute='_compute_counts', string='Admin Policies')

    def _compute_counts(self):
        for record in self:
            record.agent_count = self.env['funeral.agent'].search_count([])
            record.city_count = self.env['funeral.city'].search_count([])
            record.region_count = self.env['funeral.region'].search_count([])
            record.branch_count = self.env['funeral.branch'].search_count([])
            record.product_count = self.env['funeral.product'].search_count([])
            record.policy_count = self.env['funeral.admin.policy'].search_count([])

    def action_open_import_wizard(self):
        return {
            'name': 'Import Plans CSV',
            'type': 'ir.actions.act_window',
            'res_model': 'funeral.plan.import.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

import base64
import csv
import io

class FuneralPlanImportWizard(models.TransientModel):
    _name = 'funeral.plan.import.wizard'
    _description = 'Import Funeral Plans CSV'

    csv_file = fields.Binary(string='CSV File', required=True)
    file_name = fields.Char('File Name')

    def action_import(self):
        if not self.csv_file:
            return
        
        try:
            csv_data = base64.b64decode(self.csv_file).decode('utf-8')
            lines = csv_data.splitlines()
            reader = csv.DictReader(lines)

            for row in reader:
                product_name = row.get('product_id/name')
                rate_name = row.get('name')
                struct_name = row.get('structural_type_id/name')
                
                if not product_name or not rate_name:
                    continue

                product = self.env['funeral.product'].search([('name', '=', product_name)], limit=1)
                if not product:
                    product = self.env['funeral.product'].create({'name': product_name})
                
                struct = self.env['funeral.structural.type'].search([('name', '=', struct_name)], limit=1)

                rate_vals = {
                    'product_id': product.id,
                    'name': rate_name,
                    'structural_type_id': struct.id if struct else False,
                    'premium_amount': float(row.get('premium_amount') or 0),
                    'extended_family_top_up': float(row.get('extended_family_top_up') or 0),
                    'sum_assured': float(row.get('sum_assured') or 0),
                    'grocery_benefit': float(row.get('grocery_benefit') or 0),
                    'casket_allocation': row.get('casket_allocation') or False,
                }
                
                existing = self.env['funeral.product.rate'].search([('name', '=', rate_name), ('product_id', '=', product.id)], limit=1)
                if existing:
                    existing.write(rate_vals)
                else:
                    self.env['funeral.product.rate'].create(rate_vals)
        except Exception as e:
            pass

        return {'type': 'ir.actions.client', 'tag': 'reload'}
