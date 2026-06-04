{
    'name': 'Funeral Assurance System',
    'version': '1.0',
    'category': 'Sales/Funeral',
    'summary': 'Manage Funeral Assurance static data, agents, and policies.',
    'description': 'A comprehensive system to manage funeral assurance business including agents, products, targets, commissions, etc.',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_view.xml',
        'views/funeral_menus.xml',
        'views/city_view.xml',
        'views/agent_view.xml',
        'views/static_data_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
