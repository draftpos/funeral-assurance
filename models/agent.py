import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FuneralAgent(models.Model):
    _name = 'funeral.agent'
    _description = 'Agent'

    name = fields.Char(string='Full Name', compute='_compute_name', store=True)
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    national_id = fields.Char(string='National ID/Passport Number', required=True)
    contact_number = fields.Char(string='Contact Number')
    email = fields.Char(string='Email Address')
    physical_address = fields.Text(string='Physical Address')
    city_id = fields.Many2one('funeral.city', string='City')
    region_id = fields.Many2one('funeral.region', string='Region')
    branch_id = fields.Many2one('funeral.branch', string='Branch')
    agent_category_id = fields.Many2one('funeral.agent.category', string='Agent Category', required=True)
    agent_type = fields.Selection([
        ('general', 'General Agent'),
        ('executive', 'Executive Agent'),
        ('office', 'Office Agent')
    ], string='Agent Type', default='general')
    engagement_date = fields.Date(string='Date of Engagement', required=True)
    commission_rate = fields.Float(string='Commission Rate (%)')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)
    
    commission_ids = fields.One2many('funeral.commission', 'agent_id', string='Commissions')
    unpaid_commission_total = fields.Float(string='Unpaid Commission', compute='_compute_unpaid_commission')

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email:
                match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', record.email.lower())
                if match == None:
                    raise ValidationError(_('Please enter a valid email address!'))

    def _compute_unpaid_commission(self):
        for agent in self:
            draft_commissions = agent.commission_ids.filtered(lambda c: c.state == 'draft')
            agent.unpaid_commission_total = sum(c.amount for c in draft_commissions)

    def action_pay_commissions(self):
        for agent in self:
            draft_commissions = agent.commission_ids.filtered(lambda c: c.state == 'draft')
            if draft_commissions:
                draft_commissions.write({'state': 'paid'})

    @api.onchange('agent_category_id')
    def _onchange_agent_category_id(self):
        if self.agent_category_id:
            rate = self.env['funeral.commission.rate'].search([('agent_category_id', '=', self.agent_category_id.id), ('active', '=', True)], limit=1)
            if rate and rate.commission_percentage > 0:
                self.commission_rate = rate.commission_percentage
            else:
                self.commission_rate = 0.0
                return {
                    'warning': {
                        'title': "Missing Commission Rate",
                        'message': f"No active commission rate found for the category '{self.agent_category_id.name}'. Please create one in Static Data -> Commission Rates to ensure this agent gets paid!"
                    }
                }

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
