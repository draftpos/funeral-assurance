from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class FuneralPayment(models.Model):
    _name = 'funeral.payment'
    _description = 'Funeral Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Payment ID', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    proposal_id = fields.Many2one('funeral.proposal', string='Proposal / Customer ID', required=True)
    customer_name = fields.Char(related='proposal_id.full_name', string='Customer Name', readonly=True)
    national_id = fields.Char(related='proposal_id.national_id', string='National ID', readonly=True)
    account_payment_id = fields.Many2one('account.payment', string='Linked Accounting Payment', readonly=True, tracking=True)
    
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
    
    receipt_number = fields.Char(string='Receipt Number', required=True, copy=False)
    entry_type = fields.Selection([
        ('manual', 'Manual Entry'),
        ('excel', 'Excel Upload')
    ], string='Entry Type', default='manual', required=True)
    premium_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue')
    ], string='Premium Status', default='pending')
    
    captured_by_id = fields.Many2one('res.users', string='Captured By', default=lambda self: self.env.user)
    branch_id = fields.Many2one('funeral.branch', string='Branch/Location')
    date_captured = fields.Datetime(string='Date Captured', default=fields.Datetime.now)

    @api.onchange('proposal_id')
    def _onchange_proposal_id(self):
        if self.proposal_id:
            base_amount = self.proposal_id.total_premium or self.proposal_id.premium_amount
            
            if self.proposal_id.is_in_arrears and self.proposal_id.paid_up_to:
                today = fields.Date.context_today(self)
                diff = relativedelta(today, self.proposal_id.paid_up_to)
                months_owed = diff.years * 12 + diff.months
                if diff.days > 0:
                    months_owed += 1
                    
                if months_owed > 1:
                    self.premium_amount = base_amount * months_owed
                else:
                    self.premium_amount = base_amount
            else:
                self.premium_amount = base_amount
                
            self.payment_frequency = self.proposal_id.frequency
            self.branch_id = self.proposal_id.branch_id

    def write(self, vals):
        res = super(FuneralPayment, self).write(vals)
        if vals.get('premium_status') == 'paid':
            for record in self:
                if not record.account_payment_id and record.proposal_id.partner_id:
                    journal = self.env['account.journal'].search([('type', 'in', ['bank', 'cash']), ('company_id', '=', self.env.company.id)], limit=1)
                    if journal:
                        payment_vals = {
                            'partner_id': record.proposal_id.partner_id.id,
                            'amount': record.premium_amount,
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'date': record.payment_date or fields.Date.context_today(self),
                            'journal_id': journal.id,
                            'memo': f"Funeral Premium: {record.receipt_number or record.name}",
                        }
                        acc_payment = self.env['account.payment'].create(payment_vals)
                        acc_payment.action_post()
                        record.account_payment_id = acc_payment.id
                        
                if record.proposal_id:
                    current_paid_up = record.proposal_id.paid_up_to or record.proposal_id.commencement_date or fields.Date.context_today(self)
                    base = record.proposal_id.total_premium or record.proposal_id.premium_amount
                    
                    if record.payment_frequency == 'monthly':
                        months_paid = int(record.premium_amount / base) if base > 0 else 1
                        months_paid = max(1, months_paid)
                        record.proposal_id.paid_up_to = current_paid_up + relativedelta(months=months_paid)
                    elif record.payment_frequency == 'quarterly':
                        quarters_paid = int(record.premium_amount / base) if base > 0 else 1
                        quarters_paid = max(1, quarters_paid)
                        record.proposal_id.paid_up_to = current_paid_up + relativedelta(months=3 * quarters_paid)
                    elif record.payment_frequency == 'yearly':
                        years_paid = int(record.premium_amount / base) if base > 0 else 1
                        years_paid = max(1, years_paid)
                        record.proposal_id.paid_up_to = current_paid_up + relativedelta(years=years_paid)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        processed_vals = []
        for v in vals_list:
            if isinstance(v, list):
                processed_vals.extend(v)
            else:
                processed_vals.append(v)
                
        for vals in processed_vals:
            if not vals.get('premium_status') or vals.get('premium_status') == 'pending':
                vals['premium_status'] = 'paid'
                
            if vals.get('receipt_number', _('New')) == _('New'):
                vals['receipt_number'] = self.env['ir.sequence'].next_by_code('funeral.receipt') or _('New')
                
            if vals.get('proposal_id'):
                prop = self.env['funeral.proposal'].browse(vals['proposal_id'])
                if prop.national_id:
                    vals['name'] = prop.national_id
            
        records = super(FuneralPayment, self).create(processed_vals)
        
        for record in records:
            if record.proposal_id:
                proposal = record.proposal_id
                if record.branch_id:
                    proposal.branch_id = record.branch_id
                    
                # 1. Update Status to Active or Revival
                if proposal.state in ['pending', 'accepted', 'ntu']:
                    proposal.state = 'active'
                    active_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Active')], limit=1)
                    if active_status:
                        proposal.status_id = active_status.id
                elif proposal.state == 'lapse':
                    proposal.state = 'revival'
                    revival_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Revival')], limit=1)
                    if revival_status:
                        proposal.status_id = revival_status.id
                
                if not proposal.commencement_date:
                    proposal.commencement_date = record.payment_date or fields.Date.context_today(self)
                
                # 2. Commission Logic
                agent = proposal.agent_id
                if agent:
                    commission_amount = 0.0
                    months_paid = proposal.months_paid_to_agent
                    
                    if agent.agent_type == 'executive':
                        if months_paid == 0:
                            commission_amount = record.premium_amount * (agent.commission_rate / 100.0) if agent.commission_rate else record.premium_amount * 0.3333
                    else: # general
                        if months_paid < 3:
                            commission_amount = record.premium_amount * (agent.commission_rate / 100.0) if agent.commission_rate else record.premium_amount * 0.3333
                        else:
                            commission_amount = record.premium_amount * 0.10
                    
                    if commission_amount > 0:
                        self.env['funeral.commission'].create({
                            'agent_id': agent.id,
                            'proposal_id': proposal.id,
                            'payment_id': record.id,
                            'amount': commission_amount,
                            'type': 'earned',
                            'state': 'draft'
                        })
                    
                    proposal.months_paid_to_agent += 1
            
            if record.premium_status == 'paid' and not record.account_payment_id and record.proposal_id.partner_id:
                journal = self.env['account.journal'].search([('type', 'in', ['bank', 'cash']), ('company_id', '=', self.env.company.id)], limit=1)
                if journal:
                    payment_vals = {
                        'partner_id': record.proposal_id.partner_id.id,
                        'amount': record.premium_amount,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'date': record.payment_date or fields.Date.context_today(self),
                        'journal_id': journal.id,
                        'memo': f"Funeral Premium: {record.receipt_number or record.name}",
                    }
                    acc_payment = self.env['account.payment'].create(payment_vals)
                    acc_payment.action_post()
                    record.account_payment_id = acc_payment.id
                    
                if record.proposal_id:
                    current_paid_up = record.proposal_id.paid_up_to or record.proposal_id.commencement_date or fields.Date.context_today(self)
                    base = record.proposal_id.total_premium or record.proposal_id.premium_amount
                    
                    if record.payment_frequency == 'monthly':
                        months_paid = int(record.premium_amount / base) if base > 0 else 1
                        months_paid = max(1, months_paid)
                        record.proposal_id.paid_up_to = current_paid_up + relativedelta(months=months_paid)
                    elif record.payment_frequency == 'quarterly':
                        quarters_paid = int(record.premium_amount / base) if base > 0 else 1
                        quarters_paid = max(1, quarters_paid)
                        record.proposal_id.paid_up_to = current_paid_up + relativedelta(months=3 * quarters_paid)
                    elif record.payment_frequency == 'yearly':
                        years_paid = int(record.premium_amount / base) if base > 0 else 1
                        years_paid = max(1, years_paid)
                        record.proposal_id.paid_up_to = current_paid_up + relativedelta(years=years_paid)
                    
        return records

    @api.constrains('receipt_number')
    def _check_receipt_validity(self):
        import re
        for record in self:
            if not record.receipt_number or record.receipt_number == 'New':
                continue
                
            # Uniqueness check
            if self.search_count([('receipt_number', '=', record.receipt_number), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Receipt number %s already exists!" % record.receipt_number))
                
            # Range check
            books = self.env['funeral.receipt.book'].search([])
            if books:
                match = re.search(r'\d+', record.receipt_number)
                if match:
                    number = int(match.group())
                    valid = False
                    for book in books:
                        prefix_match = True
                        if book.prefix and not record.receipt_number.upper().startswith(book.prefix.upper()):
                            prefix_match = False
                        
                        if prefix_match and book.start_number <= number <= book.end_number:
                            valid = True
                            break
                    if not valid:
                        raise ValidationError(_("The receipt number '%s' does not fall within any configured Receipt Book Range in Static Data." % record.receipt_number))
                else:
                    raise ValidationError(_("Receipt number '%s' must contain numbers to be validated against the Receipt Book Ranges." % record.receipt_number))

    def action_print_receipt(self):
        return self.env.ref('funeral_assurance.action_report_payment_receipt').report_action(self)
