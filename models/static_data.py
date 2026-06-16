from odoo import models, fields

class FuneralRegion(models.Model):
    _name = 'funeral.region'
    _description = 'Region'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Region Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralGender(models.Model):
    _name = 'funeral.gender'
    _description = 'Gender'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Gender Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralAgentCategory(models.Model):
    _name = 'funeral.agent.category'
    _description = 'Agent Category'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Category Name', required=True)
    commission_structure = fields.Text(string='Commission Structure')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralBranch(models.Model):
    _name = 'funeral.branch'
    _description = 'Branch'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Branch Name', required=True)
    branch_code = fields.Char(string='Branch Code')
    physical_address = fields.Text(string='Physical Address')
    city_id = fields.Many2one('funeral.city', string='City ID')
    region_id = fields.Many2one('funeral.region', string='Region ID')
    contact_number = fields.Char(string='Contact Number')
    email_address = fields.Char(string='Email Address')
    branch_manager = fields.Char(string='Branch Manager')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralPolicyStatus(models.Model):
    _name = 'funeral.policy.status'
    _description = 'Policy Status'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Status Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralControlRight(models.Model):
    _name = 'funeral.control.right'
    _description = 'Management Systems Control Right'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Role Name', required=True)
    access_rights = fields.Selection([('create', 'Create'), ('read', 'Read'), ('update', 'Update'), ('delete', 'Delete')], string='Access Rights')
    module_name = fields.Char(string='Module/Feature Name')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralPeriodToPay(models.Model):
    _name = 'funeral.period.to.pay'
    _description = 'Period to Pay'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    agent_category_id = fields.Many2one('funeral.agent.category', string='Agents Category')
    period_to_pay = fields.Char(string='Period to pay')

class FuneralOptionalBenefit(models.Model):
    _name = 'funeral.optional.benefit'
    _description = 'Optional Benefit'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Benefit Name', required=True)
    description = fields.Text(string='Description')
    premium_amount = fields.Float(string='Premium Amount', required=True)
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)
