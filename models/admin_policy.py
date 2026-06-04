from odoo import models, fields

class FuneralAdminPolicy(models.Model):
    _name = 'funeral.admin.policy'
    _description = 'Company Admin Policy Database'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    date_edited = fields.Date(string='Date Edited')
    date_posted_to_history = fields.Date(string='Date posted to history')
    department_name = fields.Selection([
        ('sales', 'Sales'),
        ('marketing', 'Marketing'),
        ('claims', 'Claims'),
        ('new_business', 'New Business'),
        ('finance', 'Finance'),
        ('motor_vehicle', 'Motor Vehicle management'),
        ('customer_care', 'Customer Care'),
        ('business_dev', 'Business Development')
    ], string='Department Name')
    name = fields.Char(string='Admin Policy Title', required=True, tracking=True)
    policy_description = fields.Text(string='Admin Policy Description', tracking=True)
    document_upload = fields.Binary(string='Document Upload', tracking=True)
    effective_date = fields.Date(string='Effective Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)
