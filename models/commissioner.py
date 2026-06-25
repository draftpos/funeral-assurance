from odoo import models, fields, api

class CommissionerData(models.Model):
    _name = 'funeral.commissioner.data'
    _description = 'Commissioner Data Processing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Report Reference', required=True, tracking=True)
    report_date = fields.Date(string='Report Date', default=fields.Date.context_today, tracking=True)
    submission_status = fields.Selection([
        ('pending', 'Pending Preparation'), 
        ('review', 'Under Review'),
        ('submitted', 'Submitted to Commissioner'), 
        ('approved', 'Approved/Acknowledged')
    ], string='Status', default='pending', tracking=True)
    
    report_type = fields.Selection([
        ('monthly', 'Monthly Returns'),
        ('quarterly', 'Quarterly Report'),
        ('annual', 'Annual Financials'),
        ('ad_hoc', 'Ad-Hoc Request')
    ], string='Report Type', required=True)
    
    prepared_by = fields.Many2one('res.users', string='Prepared By', default=lambda self: self.env.user)
    notes = fields.Text(string='Executive Summary / Notes')
    attachment = fields.Binary(string='Official Document')
    file_name = fields.Char(string='File Name')


class ActuaryData(models.Model):
    _name = 'funeral.actuary.data'
    _description = 'Actuaries Data Processing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Valuation Reference', required=True, tracking=True)
    actuary_name = fields.Char(string='Actuary / Firm Name', required=True)
    valuation_date = fields.Date(string='Valuation Date', tracking=True)
    data_period_start = fields.Date(string='Data Period Start')
    data_period_end = fields.Date(string='Data Period End')
    
    total_liabilities = fields.Float(string='Total Liabilities Evaluated')
    solvency_ratio = fields.Float(string='Solvency Ratio (%)')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='draft', tracking=True)
    
    findings = fields.Text(string='Key Findings')
    recommendations = fields.Text(string='Recommendations')
    attachment = fields.Binary(string='Actuarial Report')
    file_name = fields.Char(string='File Name')


class AuditorData(models.Model):
    _name = 'funeral.auditor.data'
    _description = 'Auditors Data Processing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Audit Reference', required=True, tracking=True)
    auditor_name = fields.Char(string='Auditor / Firm Name', required=True)
    financial_year = fields.Char(string='Financial Year')
    
    start_date = fields.Date(string='Audit Start Date')
    end_date = fields.Date(string='Audit End Date')
    
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('query', 'Pending Queries')
    ], string='Status', default='scheduled', tracking=True)
    
    management_letter = fields.Binary(string='Management Letter')
    file_name = fields.Char(string='File Name')
    audit_opinion = fields.Selection([
        ('unqualified', 'Unqualified (Clean)'),
        ('qualified', 'Qualified'),
        ('adverse', 'Adverse'),
        ('disclaimer', 'Disclaimer of Opinion')
    ], string='Audit Opinion', tracking=True)
    key_audit_matters = fields.Text(string='Key Audit Matters')


class PropertyValuation(models.Model):
    _name = 'funeral.property.valuation'
    _description = 'Property Valuation & Reminders'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Property Name / Address', required=True, tracking=True)
    property_type = fields.Selection([
        ('land', 'Land'),
        ('building', 'Building'),
        ('equipment', 'Heavy Equipment')
    ], string='Property Type', required=True)
    
    last_valuation_date = fields.Date(string='Last Valuation Date')
    last_valuation_amount = fields.Float(string='Last Valued Amount')
    evaluator = fields.Char(string='Evaluator Firm')
    
    next_valuation_due = fields.Date(string='Next Valuation Due Date', required=True, tracking=True)
    status = fields.Selection([
        ('valid', 'Valid'),
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue')
    ], string='Status', compute='_compute_status', store=True)
    
    @api.depends('next_valuation_due')
    def _compute_status(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.next_valuation_due:
                delta = (rec.next_valuation_due - today).days
                if delta < 0:
                    rec.status = 'overdue'
                elif delta <= 30:
                    rec.status = 'due_soon'
                else:
                    rec.status = 'valid'
            else:
                rec.status = 'valid'
