from odoo import models, fields, api, _

class FuneralCommission(models.Model):
    _name = 'funeral.commission'
    _description = 'Agent Commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    agent_id = fields.Many2one('funeral.agent', string='Agent', required=True, tracking=True)
    proposal_id = fields.Many2one('funeral.proposal', string='Proposal / Policy', required=False, tracking=True)
    payment_id = fields.Many2one('funeral.payment', string='Payment Reference', required=False)
    run_id = fields.Many2one('funeral.commission.run', string='Commission Run', ondelete='cascade')
    
    amount = fields.Float(string='Commission Amount', required=True, tracking=True)
    commission_date = fields.Date(string='Date', default=fields.Date.context_today)
    
    type = fields.Selection([
        ('earned', 'Earned'),
        ('penalty', 'Lapse Penalty')
    ], string='Commission Type', default='earned', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

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
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('funeral.commission') or _('New')
                
        return super(FuneralCommission, self).create(processed_vals)

class FuneralCommissionRun(models.Model):
    _name = 'funeral.commission.run'
    _description = 'Monthly Commission Batch Run'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Run Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True)
    year = fields.Char(string='Year', required=True, default=lambda self: str(fields.Date.context_today(self).year))
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Completed')
    ], string='Status', default='draft', tracking=True)
    
    commission_ids = fields.One2many('funeral.commission', 'run_id', string='Generated Commissions')
    total_commission = fields.Float(string='Total Commission Generated', compute='_compute_total')

    def _compute_total(self):
        for run in self:
            run.total_commission = sum(c.amount for c in run.commission_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('funeral.commission.run') or _('New')
        return super(FuneralCommissionRun, self).create(vals_list)

    @api.constrains('month', 'year')
    def _check_unique_run(self):
        from odoo.exceptions import ValidationError
        for record in self:
            existing_run = self.search([
                ('month', '=', record.month), 
                ('year', '=', record.year), 
                ('state', '=', 'done'), 
                ('id', '!=', record.id)
            ])
            if existing_run:
                month_name = dict(self._fields['month'].selection).get(record.month)
                raise ValidationError(f"A completed Commission Run already exists for {month_name} {record.year}. Please review the existing run instead of creating a new one.")

    def action_run_commissions(self):
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        import calendar
        from odoo.exceptions import ValidationError
        
        for record in self:
            if record.state == 'done':
                continue
                
            # Prevent duplicate completed runs for the same month
            existing_run = self.search([('month', '=', record.month), ('year', '=', record.year), ('state', '=', 'done'), ('id', '!=', record.id)])
            if existing_run:
                raise ValidationError(f"A completed Commission Run already exists for {dict(self._fields['month'].selection).get(record.month)} {record.year}.")
                
            start_date = datetime.strptime(f"{record.year}-{record.month}-01", "%Y-%m-%d").date()
            last_day = calendar.monthrange(int(record.year), int(record.month))[1]
            end_date = datetime.strptime(f"{record.year}-{record.month}-{last_day}", "%Y-%m-%d").date()
            
            # Clear old draft commissions from this run just in case
            record.commission_ids.unlink()
            
            # Find all payments in this period
            payments = self.env['funeral.payment'].search([
                ('payment_date', '>=', start_date),
                ('payment_date', '<=', end_date),
                ('premium_status', '=', 'paid')
            ])
            
            # Group payments by Agent
            agent_payments = {}
            for pay in payments:
                agent = pay.proposal_id.agent_id
                if not agent:
                    continue
                if agent not in agent_payments:
                    agent_payments[agent] = []
                agent_payments[agent].append(pay)
                
            commission_vals = []
            
            for agent, pays in agent_payments.items():
                if agent.agent_type == 'executive':
                    # Executive Agent Logic: $200 threshold for the month, on FIRST payments only
                    first_payments = [p for p in pays if p.commission_month_index == 1]
                    total_first_month_collected = sum(p.premium_amount for p in first_payments)
                    
                    if total_first_month_collected > 200.0:
                        excess = total_first_month_collected - 200.0
                        comm_rate = (agent.commission_rate / 100.0) if agent.commission_rate else 0.3333
                        amount = excess * comm_rate
                        
                        commission_vals.append({
                            'agent_id': agent.id,
                            'run_id': record.id,
                            'amount': amount,
                            'type': 'earned',
                            'state': 'draft',
                        })
                else:
                    # General / Office Agents
                    for p in pays:
                        amount = 0.0
                        comm_rate = (agent.commission_rate / 100.0) if agent.commission_rate else 0.3333
                        
                        # Assuming 'general' includes office agents or we rely on agent_category.
                        # For general agents: paid out over 3 months
                        if p.commission_month_index <= 3:
                            amount = p.premium_amount * comm_rate
                        
                        if amount > 0:
                            commission_vals.append({
                                'agent_id': agent.id,
                                'run_id': record.id,
                                'proposal_id': p.proposal_id.id,
                                'payment_id': p.id,
                                'amount': amount,
                                'type': 'earned',
                                'state': 'draft',
                            })
            
            # CLAWBACK LOGIC
            lapsed_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Lapsed')], limit=1)
            if lapsed_status:
                lapsed_proposals = self.env['funeral.proposal'].search([('status_id', '=', lapsed_status.id)])
                for l_prop in lapsed_proposals:
                    agent = l_prop.agent_id
                    if not agent:
                        continue
                        
                    earned_comms = self.env['funeral.commission'].search([
                        ('proposal_id', '=', l_prop.id),
                        ('agent_id', '=', agent.id),
                        ('type', '=', 'earned')
                    ])
                    penalty_comms = self.env['funeral.commission'].search([
                        ('proposal_id', '=', l_prop.id),
                        ('agent_id', '=', agent.id),
                        ('type', '=', 'penalty')
                    ])
                    
                    total_earned = sum(c.amount for c in earned_comms)
                    total_penalty = abs(sum(c.amount for c in penalty_comms))
                    
                    if total_earned > total_penalty:
                        clawback_amount = total_earned - total_penalty
                        commission_vals.append({
                            'agent_id': agent.id,
                            'run_id': record.id,
                            'proposal_id': l_prop.id,
                            'amount': -clawback_amount,
                            'type': 'penalty',
                            'state': 'draft',
                        })
            
            if commission_vals:
                self.env['funeral.commission'].create(commission_vals)
            
            record.state = 'done'
