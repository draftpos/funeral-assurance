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
