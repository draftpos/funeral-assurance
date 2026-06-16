from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FuneralPayment(models.Model):
    _name = 'funeral.payment'
    _description = 'Funeral Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Payment ID', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    proposal_id = fields.Many2one('funeral.proposal', string='Proposal / Customer ID')
    policy_id = fields.Many2one('funeral.policy', string='Policy Number', tracking=True)
    
    premium_amount = fields.Float(string='Premium Amount', required=True, tracking=True)
    payment_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Payment Frequency')
    
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today, tracking=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('mobile', 'Mobile Money'),
        ('debit', 'Debit Order')
    ], string='Payment Method', required=True)
    
    receipt_number = fields.Char(string='Receipt Number', required=True)
    premium_status = fields.Selection([
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue')
    ], string='Premium Status', default='paid')
    
    captured_by_id = fields.Many2one('res.users', string='Captured By', default=lambda self: self.env.user)
    branch_id = fields.Many2one('funeral.branch', string='Branch/Location')
    date_captured = fields.Datetime(string='Date Captured', default=fields.Datetime.now)

    @api.onchange('proposal_id')
    def _onchange_proposal_id(self):
        if self.proposal_id:
            self.premium_amount = self.proposal_id.premium_amount
            self.payment_frequency = self.proposal_id.frequency
            self.branch_id = self.proposal_id.branch_id
            
            # If a policy already exists for this proposal, auto-link it
            existing_policy = self.env['funeral.policy'].search([('proposal_id', '=', self.proposal_id.id)], limit=1)
            if existing_policy:
                self.policy_id = existing_policy.id

    @api.onchange('policy_id')
    def _onchange_policy_id(self):
        if self.policy_id:
            self.premium_amount = self.policy_id.total_premium or self.policy_id.premium
            self.payment_frequency = self.policy_id.frequency_of_payments
            self.branch_id = self.policy_id.branch_id
            if self.policy_id.proposal_id:
                self.proposal_id = self.policy_id.proposal_id

    @api.model_create_multi
    def create(self, vals_list):
        # Bulletproof check in case Odoo passes a single dict or a list of lists
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        processed_vals = []
        for v in vals_list:
            if isinstance(v, list):
                processed_vals.extend(v)
            else:
                processed_vals.append(v)
                
        for vals in processed_vals:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('funeral.payment') or _('New')
                
            if vals.get('proposal_id') and not vals.get('policy_id'):
                proposal = self.env['funeral.proposal'].browse(vals['proposal_id'])
                
                # Check if policy already exists for this proposal
                existing_policy = self.env['funeral.policy'].search([('proposal_id', '=', proposal.id)], limit=1)
                
                if existing_policy:
                    vals['policy_id'] = existing_policy.id
                else:
                    # Fetch default policy document from Admin Policies (Latest active one with a document)
                    admin_policy = self.env['funeral.admin.policy'].search([
                        ('document_upload', '!=', False)
                    ], order='id desc', limit=1)
                    
                    default_doc = admin_policy.document_upload if admin_policy else False
                    default_doc_name = (admin_policy.name + '.pdf') if admin_policy else False
                    
                    # Create Policy from Proposal
                    policy_vals = {
                        'proposal_id': proposal.id,
                        'name': proposal.national_id or _('New'),
                        'product_id': proposal.product_id.id,
                        'sum_assured': proposal.sum_assured,
                        'premium': proposal.premium_amount,
                        'policy_term': proposal.policy_term,
                        'waiting_period': proposal.waiting_period,
                        'mode_of_payment': proposal.mode_of_payment,
                        'frequency_of_payments': proposal.frequency,
                        'agent_id': proposal.agent_id.id,
                        'branch_id': proposal.branch_id.id,
                        'commencement_date': vals.get('payment_date'),
                        'state': 'active',
                        'policy_document': default_doc,
                        'policy_document_name': default_doc_name,
                    }
                    policy = self.env['funeral.policy'].create(policy_vals)
                    
                    # Transfer dependants and extended family
                    for dep in proposal.dependant_ids:
                        dep.policy_id = policy.id
                    for ext in proposal.extended_family_ids:
                        ext.policy_id = policy.id
                        
                    vals['policy_id'] = policy.id
                    proposal.state = 'accepted'
            
        records = super(FuneralPayment, self).create(processed_vals)
        
        # When payment is created, process policy update and commission
        for record in records:
            if record.policy_id:
                policy = record.policy_id
                if record.branch_id:
                    policy.branch_id = record.branch_id
                    
                # 1. Update Policy Status to active
                if policy.state in ['lapsed', 'cancelled', 'ntu']:
                    policy.state = 'active'
                
                # 2. Commission Logic
                agent = policy.agent_id
                if agent:
                    commission_amount = 0.0
                    months_paid = policy.months_paid_to_agent
                    
                    if agent.agent_type == 'executive':
                        if months_paid == 0:
                            commission_amount = record.premium_amount * 0.3333
                    else: # general
                        if months_paid < 3:
                            commission_amount = record.premium_amount * 0.3333
                        else:
                            commission_amount = record.premium_amount * 0.10
                    
                    if commission_amount > 0:
                        self.env['funeral.commission'].create({
                            'agent_id': agent.id,
                            'policy_id': policy.id,
                            'payment_id': record.id,
                            'amount': commission_amount,
                            'type': 'earned',
                            'state': 'draft'
                        })
                    
                    # Increment months paid
                    policy.months_paid_to_agent += 1
                    
        return records

    @api.constrains('receipt_number')
    def _check_receipt_unique(self):
        for record in self:
            if self.search_count([('receipt_number', '=', record.receipt_number), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Receipt number must be unique!"))

    def action_print_receipt(self):
        return self.env.ref('funeral_assurance.action_report_payment_receipt').report_action(self)
