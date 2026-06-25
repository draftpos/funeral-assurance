from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FuneralReportWizard(models.TransientModel):
    _name = 'funeral.report.wizard'
    _description = 'Funeral Report Wizard'

    category = fields.Selection([
        ('operations', 'Operations'),
        ('tombstones', 'Tombstones'),
        ('audit', 'Audit and Compliance'),
        ('vehicles', 'Vehicles')
    ], string='Category', required=True)
    
    report_action_id = fields.Many2one('ir.actions.act_window', string='Report', required=True)

    @api.onchange('category')
    def _onchange_category(self):
        self.report_action_id = False
        if not self.category:
            return {'domain': {'report_action_id': [('id', '=', False)]}}
            
        operations_reports = [
            'Clients Listing', 'New Clients', 'Clients Demographics', 'Dependants Report',
            'Active Policies', 'Lapsed Policies', 'Cancelled Policies', 'Suspended Policies',
            'Underwriting Policies', 'Extended Family Report', 'Collections Daily Premiums', 
            'Collections Monthly Premiums', 'Summarized Premiuns Collections', 'Debit Order Premiums Collections', 
            'Stop Order Premiums Collections', 'Outstanding Premiums Collected', 'Arrears Report', 
            'Premiums Collections Success Rate', 'Premiums Collection Failure Report', 'Premiums Reversed Transactions', 
            'Premiums Collection Reconciliation Report', 'Branch Premiums Collections Report', 'Agent Premiums Collections Report', 
            'Premiums Collection Analysis Report', 'Outstanding Premium Debtors', 'Premium Debtor Age Analysis', 
            'Premium Debtors by Funeral', 'Premium Debtors by Policy', 'Premium Debtors by Branch', 
            'Premium Collection Follow-up Report', 'Premium Bad Debt Report', 'Premium Debtor Payment History',
            'Not yet Done/Open Claims', 'Done & Closed Claims', 'Pending Claims', 'Approved Claims',
            'Rejected Claims', 'Claims by Branch', 'Claims by Agent', 'Claims by Product',
            'Claims Payout Report', 'Claims Turnaround Time', 'Claims History', 'Claims Audit Report',
            'Claims Trend Report', 'Actuary Claims Report Structure', 'Register - Detailed Funerals', 
            'Register- Upcoming Funerals', 'Register - Completed Funerals', 'Cost Analysis for Funerals', 
            'Income Report-Funerals', 'Funeral Profit made', 'Burial Reports', 'Detailed Cremation Report', 
            'Detailed Funeral Instruction Report', 'Police Report B11 Report availability', 'Actual Funeral Vehicle Usage', 
            'Debtors Report', 'Audit Report', 'Burial Society Listing', 'Burial Society Members', 
            'Burial Society Collections', 'Burial Society Arrears', 'Burial Society Claims', 'Burial Society Payments', 
            'Burial Society Growth Report', 'Burial Society Summarized Report', 'Summary of New Business Written', 
            'Premiums Overpayment Report', 'New Business Underwriter Collections', 'Summarized Underwriter Claims', 
            'Product by Product Performance', 'Product by product Profitability Report', 'Payover Reconciliation Report',
            'Monthly Agent Commission Statements', 'Monthly Broker Commission Statements', 'Summarised Monthly Commission Report by branch',
            'Summarized Monthly Broker Commissions', 'Outstanding Commission Report', 'Commissions by Product Summarized',
            'Commissions by Branch Summarized', 'Current Stock Levels', 'Low Stock Report', 'Stock Movement Report', 
            'Stock Valuation', 'Stock Issues Report', 'Stock Purchases', 'Stock Usage Report', 'Stock Audit Report',
            'Income Report', 'Expense Report', 'Profitability Report', 'Cash Flow Report', 'Revenue Analysis',
            'Monthly Financial Summary', 'Branch Financial Report', 'Collection vs Claims Analysis',
            'Performance Summary', 'Growth Analysis', 'Collection KPIs', 'Claims KPIs', 'Branch Comparison',
            'Agent Performance', 'Monthly Executive Summary', 'Year-to-Date Performance Report'
        ]
        
        tombstones_reports = [
            'Tombstones Orders Report', 'Pending Orders Report', 'Completed Orders Report', 'Tombstones Debtors Report',
            'Suppliers Report', 'Tombstone Profitability report', 'Tombstone Sales Analysis report',
            'Tombstones Sales by Branch', 'Highest Sales by Branch list'
        ]
        
        audit_reports = [
            'User Activity Report', 'Login History', 'Transaction Audit Trail', 'Deleted Records Report',
            'Data Changes Report', 'Branch Activity Report', 'Fraud Investigation Report', 'Security Audit Report'
        ]
        
        vehicles_reports = [
            'Vehicle Registers - Vehicle Master List', 'Vehicle Status Report', 'Active Vehicles', 'Inactive Vehicles',
            'Vehicle Allocation Report', 'Vehicle Ownership Report', 'Vehicle Utilization Report', 'Vehicle Trip Report',
            'Daily Vehicle Usage', 'Monthly Vehicle Usage', 'Vehicle Booking Report', 'Vehicle Movement Report',
            'Vehicle Mileage Report', 'Driver Allocation Report', 'Fuel Consumption Report', 'Fuel Cost Analysis',
            'Fuel per Vehicle Report', 'Fuel per Driver Report', 'Monthly Fuel Summary', 'Fuel Variance Report',
            'Vehicle Maintenance Report', 'Scheduled Services Report', 'Service History Report', 'Maintenance Cost Analysis',
            'Workshop Repair Report', 'Vehicle Breakdown Report', 'Parts Replacement Report', 'Hearse Usage Report',
            'Family Car Usage Report', 'Funeral Vehicle Allocation', 'Funeral Transport Costs', 'Vehicle Usage by Funeral',
            'Vehicle Availability Report', 'Driver Assignment Report', 'Driver Performance Report', 'Driver Trip History Report',
            'Driver Incident Report', 'Driver Licence Expiry Report', 'Vehicle Licence Expiry Report', 'Insurance Expiry Report',
            'Roadworthy Certificate Report', 'Vehicle Inspection Report', 'Compliance Status Report', 'Vehicle Cost Analysis',
            'Vehicle Profitability Report', 'Vehicle Expense Report', 'Vehicle Budget Report', 'Cost per Kilometer Report',
            'Fleet Operating Cost Report', 'Vehicle Audit Trail', 'Vehicle Damage Report', 'Accident Report',
            'Vehicle Downtime Report', 'Fleet Performance Summary'
        ]
        
        if self.category == 'operations':
            return {'domain': {'report_action_id': [('name', 'in', operations_reports)]}}
        elif self.category == 'tombstones':
            return {'domain': {'report_action_id': [('name', 'in', tombstones_reports)]}}
        elif self.category == 'audit':
            return {'domain': {'report_action_id': [('name', 'in', audit_reports)]}}
        elif self.category == 'vehicles':
            return {'domain': {'report_action_id': [('name', 'in', vehicles_reports)]}}

    def action_open_report(self):
        self.ensure_one()
        if not self.report_action_id:
            raise UserError(_("Please select a report to open."))
            
        action = self.report_action_id.read()[0]
        # Clear out unnecessary action properties that might cause view errors
        action['views'] = [(False, 'list'), (False, 'form')]
        return action
