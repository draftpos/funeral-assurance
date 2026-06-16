from odoo import models, fields, api

class FuneralAgent(models.Model):
    _name = 'funeral.agent'
    _description = 'Agent'

    name = fields.Char(string='Full Name', compute='_compute_name', store=True)
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    national_id = fields.Char(string='National ID/Passport Number')
    contact_number = fields.Char(string='Contact Number')
    email = fields.Char(string='Email Address')
    physical_address = fields.Text(string='Physical Address')
    city_id = fields.Many2one('funeral.city', string='City')
    region_id = fields.Many2one('funeral.region', string='Region')
    branch_id = fields.Many2one('funeral.branch', string='Branch')
    agent_category_id = fields.Many2one('funeral.agent.category', string='Agent Category')
    agent_type = fields.Selection([
        ('general', 'General Agent'),
        ('executive', 'Executive Agent')
    ], string='Agent Type', default='general')
    engagement_date = fields.Date(string='Date of Engagement')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for record in self:
            if record.first_name and record.last_name:
                record.name = f"{record.first_name} {record.last_name}"
            elif record.first_name:
                record.name = record.first_name
            elif record.last_name:
                record.name = record.last_name
            else:
                record.name = "New Agent"
