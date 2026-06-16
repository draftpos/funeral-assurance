from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    funeral_lapse_months = fields.Integer(
        string='Months before Policy Lapses',
        config_parameter='funeral.lapse_months',
        default=3,
        help="Number of months of non-payment before a policy is considered lapsed or NTU."
    )
