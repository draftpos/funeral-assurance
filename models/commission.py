from odoo import models, fields, api, _

class FuneralCommission(models.Model):
    _name = 'funeral.commission'
    _description = 'Agent Commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    agent_id = fields.Many2one('funeral.agent', string='Agent', required=True, tracking=True)
    proposal_id = fields.Many2one('funeral.proposal', string='Proposal / Policy', required=True, tracking=True)
    payment_id = fields.Many2one('funeral.payment', string='Payment Reference')
    
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
