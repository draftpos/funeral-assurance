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
    
    expected_premium = fields.Float(related='proposal_id.total_premium', string='Expected Premium', readonly=True)
    arrears_amount = fields.Float(string='Current Arrears', compute='_compute_arrears', readonly=True)
    advance_amount = fields.Float(string='Paid in Advance', compute='_compute_arrears', readonly=True)
    premium_amount = fields.Float(string='Amount Paid', required=True, tracking=True)
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words')
    
    proposal_state = fields.Char(related='proposal_id.state', string='Proposal State')
    
    payment_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Payment Frequency')
    
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today, tracking=True)
    payment_for_month = fields.Date(string='Payment For Month', required=True, default=fields.Date.context_today, help='The specific month this payment covers')
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
    ], string='Status', default='pending', tracking=True)

    def _compute_amount_in_words(self):
        currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        for record in self:
            if currency:
                record.amount_in_words = currency.amount_to_text(record.premium_amount)
            else:
                record.amount_in_words = f"USD {record.premium_amount:.2f}"
                
    @api.depends('proposal_id', 'proposal_id.paid_up_to', 'proposal_id.commencement_date', 'payment_date')
    def _compute_arrears(self):
        for record in self:
            record.arrears_amount = 0.0
            record.advance_amount = 0.0
            if record.proposal_id:
                today = record.payment_date or fields.Date.context_today(self)
                paid_up = record.proposal_id.paid_up_to or record.proposal_id.commencement_date
                if paid_up:
                    if paid_up < today:
                        months_diff = (today.year - paid_up.year) * 12 + today.month - paid_up.month
                        if today.day < paid_up.day:
                            months_diff -= 1
                        if months_diff > 0:
                            record.arrears_amount = months_diff * record.proposal_id.total_premium
                    elif paid_up > today:
                        months_diff = (paid_up.year - today.year) * 12 + paid_up.month - today.month
                        if paid_up.day < today.day:
                            months_diff -= 1
                        if months_diff > 0:
                            record.advance_amount = months_diff * record.proposal_id.total_premium
    
    def action_activate_policy(self):
        for record in self:
            if record.proposal_id:
                record.proposal_id.action_activate_policy()
    
    captured_by_id = fields.Many2one('res.users', string='Captured By', default=lambda self: self.env.user)
    branch_id = fields.Many2one('funeral.branch', string='Branch/Location')
    date_captured = fields.Datetime(string='Date Captured', default=fields.Datetime.now)
    commission_month_index = fields.Integer(string='Commission Month Index', default=0, readonly=True)

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
                current_status_name = proposal.status_id.name.lower() if proposal.status_id else ''
                
                if current_status_name in ['underwriting', 'accepted', 'ntu']:
                    active_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Active')], limit=1)
                    if active_status:
                        proposal.status_id = active_status.id
                
                elif current_status_name == 'lapsed':
                    # First payment after lapse shifts it to Revived
                    revival_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Revived')], limit=1)
                    if revival_status:
                        proposal.status_id = revival_status.id
                    proposal.revival_payments_count = 1
                
                elif current_status_name == 'revived':
                    # Second payment while revived graduates them to Active
                    proposal.revival_payments_count += 1
                    if proposal.revival_payments_count >= 2:
                        active_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Active')], limit=1)
                        if active_status:
                            proposal.status_id = active_status.id
                        proposal.revival_payments_count = 0
                
                if not proposal.commencement_date:
                    proposal.commencement_date = record.payment_date or fields.Date.context_today(self)
                
                # COMMISSION TRACKING
                base_prem = proposal.total_premium or proposal.premium_amount
                months_covered = 1
                if record.payment_frequency == 'monthly' and base_prem > 0:
                    months_covered = max(1, int(record.premium_amount / base_prem))
                
                record.commission_month_index = proposal.months_paid_to_agent + 1
                proposal.months_paid_to_agent += months_covered
            
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
