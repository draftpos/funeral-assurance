from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    funeral_lapse_months = fields.Integer(
        string='Months before Policy Lapses',
        config_parameter='funeral.lapse_months',
        default=4,
        help="Number of months of non-payment before a policy is considered lapsed or NTU."
    )

    funeral_executive_allowance = fields.Float(
        string='Executive Agent Allowance Threshold',
        config_parameter='funeral.executive_allowance',
        default=200.0,
        help="The baseline allowance for Executive Agents. Commissions apply only on amounts above this threshold."
    )
