"""Translation strings for Anchorpoint.

Pragmatic, non-exhaustive translation set covering high-visibility strings:
nav bar, dashboard headings/stat labels, landing page hero + feature cards,
and common button labels reused across pages.

Usage:
    from translations import t
    t('nav_dashboard', lang='es')  # -> 'Panel'

Missing keys fall back to returning the key itself, so templates never
crash on an untranslated string.
"""

TRANSLATIONS = {
    'en': {
        # Nav bar
        'nav_dashboard': 'Dashboard',
        'nav_transactions': 'Transactions',
        'nav_debts': 'Debts',
        'nav_goals': 'Goals',
        'nav_summary': 'Summary',
        'nav_projections': 'Projections',
        'nav_profile': 'Profile',
        'nav_logout': 'Log out',
        'nav_login': 'Log in',
        'nav_get_started': 'Get started',

        # Dashboard
        'dashboard_welcome': 'Welcome back',
        'dashboard_subtitle': "Here's where your money stands today.",
        'stat_total_income': 'Total Income',
        'stat_total_expenses': 'Total Expenses',
        'stat_available': 'Available to Allocate',
        'stat_total_debt': 'Total Debt Remaining',
        'income_vs_expenses': 'Income vs. Expenses',
        'budget_allocation': 'Budget Allocation',
        'savings_goals': 'Savings Goals',
        'recent_activity': 'Recent Activity',
        'view_all': 'View all',
        'manage': 'Manage',

        # Landing page
        'landing_eyebrow': 'Personal finance, clarified',
        'landing_headline': 'See your whole financial picture in one place.',
        'landing_subtext': 'Track income and expenses, pay down debt, hit your savings goals, and get a personalized budget split — all in one clean dashboard.',
        'landing_get_started': 'Get started free',
        'landing_feature1_title': '📈 Track everything',
        'landing_feature1_body': 'Log income, expenses, and debt payments and watch your available cash update automatically.',
        'landing_feature2_title': '🥧 Smart budgeting',
        'landing_feature2_body': 'Get a recommended budget split based on your age and financial picture — or build your own.',
        'landing_feature3_title': '🎯 Hit your goals',
        'landing_feature3_body': 'Set savings targets, track progress with visual indicators, and celebrate when you reach them.',

        # Common buttons
        'btn_add_transaction': '+ Add Transaction',
        'btn_save_changes': 'Save Changes',
        'btn_delete': 'Delete',
        'btn_cancel': 'Cancel',
        'btn_add_goal': 'Add a Goal',
    },
    'es': {
        # Nav bar
        'nav_dashboard': 'Panel',
        'nav_transactions': 'Transacciones',
        'nav_debts': 'Deudas',
        'nav_goals': 'Metas',
        'nav_summary': 'Resumen',
        'nav_projections': 'Proyecciones',
        'nav_profile': 'Perfil',
        'nav_logout': 'Cerrar sesión',
        'nav_login': 'Iniciar sesión',
        'nav_get_started': 'Comenzar',

        # Dashboard
        'dashboard_welcome': 'Bienvenido de nuevo',
        'dashboard_subtitle': 'Así está tu dinero hoy.',
        'stat_total_income': 'Ingresos Totales',
        'stat_total_expenses': 'Gastos Totales',
        'stat_available': 'Disponible para Asignar',
        'stat_total_debt': 'Deuda Total Pendiente',
        'income_vs_expenses': 'Ingresos vs. Gastos',
        'budget_allocation': 'Distribución del Presupuesto',
        'savings_goals': 'Metas de Ahorro',
        'recent_activity': 'Actividad Reciente',
        'view_all': 'Ver todo',
        'manage': 'Administrar',

        # Landing page
        'landing_eyebrow': 'Finanzas personales, claras',
        'landing_headline': 'Ve toda tu situación financiera en un solo lugar.',
        'landing_subtext': 'Registra ingresos y gastos, paga tus deudas, alcanza tus metas de ahorro y obtén un plan de presupuesto personalizado — todo en un panel claro.',
        'landing_get_started': 'Comienza gratis',
        'landing_feature1_title': '📈 Controla todo',
        'landing_feature1_body': 'Registra ingresos, gastos y pagos de deudas, y observa cómo se actualiza automáticamente tu efectivo disponible.',
        'landing_feature2_title': '🥧 Presupuesto inteligente',
        'landing_feature2_body': 'Obtén una distribución de presupuesto recomendada según tu edad y situación financiera, o crea la tuya propia.',
        'landing_feature3_title': '🎯 Alcanza tus metas',
        'landing_feature3_body': 'Define metas de ahorro, sigue tu progreso con indicadores visuales y celebra cuando las alcances.',

        # Common buttons
        'btn_add_transaction': '+ Agregar Transacción',
        'btn_save_changes': 'Guardar Cambios',
        'btn_delete': 'Eliminar',
        'btn_cancel': 'Cancelar',
        'btn_add_goal': 'Agregar una Meta',
    },
}


def t(key, lang='en'):
    """Return the translated string for key/lang, falling back to English,
    then to the raw key if no translation exists anywhere."""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, TRANSLATIONS['en'].get(key, key))
