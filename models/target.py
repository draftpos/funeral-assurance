from odoo import models, fields

class FuneralTarget(models.Model):
    _name = 'funeral.target'
    _description = 'Targets'

    agent_id = fields.Many2one('funeral.agent', string='Agent ID', required=True)
    category_id = fields.Many2one('funeral.agent.category', string='Category ID')
    
    written_daily_target = fields.Float(string='Written Daily Target')
    written_weekly_target = fields.Float(string='Written Weekly Target')
    written_monthly_target = fields.Float(string='Written Monthly Target')
    written_annual_target = fields.Float(string='Wtitten Annual Target')
    
    collection_daily_target = fields.Float(string='Collection Daily Target')
    collection_weekly_target = fields.Float(string='Collection Weekly Target')
    collection_monthly_target = fields.Float(string='Collection Monthly Target')
    collection_annual_target = fields.Float(string='Collection Annual Target')
    
    conversion_daily_target = fields.Float(string='Conversion Daily Target')
    conversion_weekly_target = fields.Float(string='Conversion Weekly Target')
    conversion_monthly_target = fields.Float(string='Conversion Monthly Target')
    conversion_annual_target = fields.Float(string='Conversion Annual Target')

class FuneralAgentCommissionRate(models.Model):
    _name = 'funeral.agent.commission.rate'
    _description = 'Agents Commissions Rates'

    agent_id = fields.Many2one('funeral.agent', string='Agent ID', required=True)
    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    agent_category_id = fields.Many2one('funeral.agent.category', string='Agents Category')
    commissions_rates = fields.Float(string='Commissions Rates')
