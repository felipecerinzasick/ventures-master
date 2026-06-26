import base64
from datetime import datetime, timedelta, timezone
import json
import os
import ssl
from decimal import Decimal, InvalidOperation
from functools import wraps
from hmac import compare_digest
from urllib import parse, request as urlrequest
from urllib.error import URLError, HTTPError

from .models import Post, Comment, Resource
from newsletter.models import Newsletter
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PostForm,ContactForm
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView
)

SATOSHIS_PER_BTC = 100000000

STOCK_HOLDINGS = [
    {'name': 'Asset Entities', 'ticker': 'ASST', 'symbol': 'ASST', 'shares': Decimal('180'), 'average_price': Decimal('18.03'), 'cost_currency': 'USD', 'fallback_value': Decimal('2005'), 'fallback_currency': 'USD'},
    {'name': 'Cipher Mining', 'ticker': 'CFR', 'symbol': 'CIFR', 'shares': Decimal('40'), 'average_price': Decimal('7.15'), 'cost_currency': 'USD', 'fallback_value': Decimal('1016'), 'fallback_currency': 'USD'},
    {'name': 'CleanSpark', 'ticker': 'CLSK', 'symbol': 'CLSK', 'shares': Decimal('96'), 'average_price': Decimal('15.30'), 'cost_currency': 'USD', 'fallback_value': Decimal('1543'), 'fallback_currency': 'USD'},
    {'name': 'Metaplanet', 'ticker': 'DN3', 'symbol': 'DN3.F', 'shares': Decimal('2850'), 'average_price': Decimal('2.3117'), 'cost_currency': 'EUR', 'fallback_value': Decimal('3140'), 'fallback_currency': 'EUR'},
    {'name': 'IREN', 'ticker': 'IREN', 'symbol': 'IREN', 'shares': Decimal('30'), 'average_price': Decimal('11.99'), 'cost_currency': 'USD', 'fallback_value': Decimal('1399'), 'fallback_currency': 'USD'},
    {'name': 'The Keel', 'ticker': 'KEEL', 'symbol': 'KEEL', 'shares': Decimal('710'), 'average_price': Decimal('2.39'), 'cost_currency': 'USD', 'fallback_value': Decimal('4264'), 'fallback_currency': 'USD'},
    {'name': 'MARA Holdings', 'ticker': 'MARA', 'symbol': 'MARA', 'shares': Decimal('164'), 'average_price': Decimal('19.76'), 'cost_currency': 'USD', 'fallback_value': Decimal('2364'), 'fallback_currency': 'USD'},
    {'name': 'Strategy', 'ticker': 'MSTR', 'symbol': 'MSTR', 'shares': Decimal('51'), 'average_price': Decimal('153.69'), 'cost_currency': 'USD', 'fallback_value': Decimal('4284'), 'fallback_currency': 'USD'},
    {'name': 'PayPal', 'ticker': 'PYPL', 'symbol': 'PYPL', 'shares': Decimal('10'), 'average_price': Decimal('56.23'), 'cost_currency': 'USD', 'fallback_value': Decimal('441.60'), 'fallback_currency': 'USD'},
    {'name': 'Riot Platforms', 'ticker': 'RIOT', 'symbol': 'RIOT', 'shares': Decimal('20'), 'average_price': Decimal('11.16'), 'cost_currency': 'USD', 'fallback_value': Decimal('561'), 'fallback_currency': 'USD'},
    {'name': 'Shimano', 'ticker': 'SHM', 'symbol': 'SHM.F', 'shares': Decimal('5'), 'average_price': Decimal('172.40'), 'cost_currency': 'EUR', 'fallback_value': Decimal('475.75'), 'fallback_currency': 'EUR'},
    {'name': 'Strategy Preferred STRD', 'ticker': 'STRD', 'symbol': 'STRD', 'shares': Decimal('5'), 'average_price': Decimal('61.64'), 'cost_currency': 'USD', 'fallback_value': Decimal('267.40'), 'fallback_currency': 'USD'},
    {'name': 'STRC', 'ticker': 'STRC', 'symbol': 'STRC', 'shares': Decimal('5.5'), 'average_price': Decimal('88.69'), 'cost_currency': 'USD', 'fallback_value': Decimal('405.82'), 'fallback_currency': 'USD'},
    {'name': 'TeraWulf', 'ticker': 'WULF', 'symbol': 'WULF', 'shares': Decimal('25'), 'average_price': Decimal('6.77'), 'cost_currency': 'USD', 'fallback_value': Decimal('651.25'), 'fallback_currency': 'USD'},
    {'name': 'Canaan', 'ticker': 'CAN', 'symbol': 'CAN', 'shares': Decimal('231'), 'average_price': Decimal('2.60'), 'cost_currency': 'USD', 'fallback_value': Decimal('71.26'), 'fallback_currency': 'USD'},
    {'name': 'Argo Blockchain', 'ticker': '0XP', 'symbol': '0XP.DU', 'shares': Decimal('1100'), 'average_price': Decimal('0.23'), 'cost_currency': 'EUR', 'fallback_value': Decimal('13.20'), 'fallback_currency': 'EUR'},
    {'name': 'The Smarter Web Company', 'ticker': '3M8', 'symbol': '3M8.F', 'shares': Decimal('100'), 'average_price': Decimal('1.08'), 'cost_currency': 'EUR', 'fallback_value': Decimal('29.85'), 'fallback_currency': 'EUR'},
    {'name': 'Y6G0', 'ticker': 'Y6G0', 'symbol': 'Y6G0.F', 'shares': Decimal('120'), 'average_price': Decimal('21.146'), 'cost_currency': 'EUR', 'fallback_value': Decimal('1431'), 'fallback_currency': 'EUR'},
]

TREASURY_STOCKS = {
    'metaplanet': {
        'name': 'Metaplanet',
        'ticker': 'DN3',
        'symbol': 'DN3.F',
        'benchmark_symbol': 'BTC-USD',
        'benchmark_name': 'Bitcoin',
        'benchmark_unit': 'BTC',
        'target_price': 250000,
        'start': '2024-01-01',
        'risk_rank': 2,
        'risk_label': 'Higher risk than MSTR: Japan-listed Bitcoin treasury with local market and liquidity risk.',
        'premium_label': 'BTC treasury re-rating',
        'baseline_note': 'Metaplanet is treated as a Bitcoin treasury equity with operating, jurisdiction, and Japan-market structure risk.',
        'thesis': 'Metaplanet is the closest non-US Bitcoin treasury analogue in this portfolio. The thesis is that it can compound BTC exposure through capital markets access, but the Japanese market introduces extra liquidity, governance, FX, and market-structure risks compared with MSTR.',
        'scenarios': [
            {'name': 'Tracks Bitcoin', 'multiple': 1.0},
            {'name': 'Treasury premium returns', 'multiple': 2.0},
            {'name': 'Japan re-rating', 'multiple': 4.0},
        ],
    },
    'asst': {
        'name': 'Asset Entities',
        'ticker': 'ASST',
        'symbol': 'ASST',
        'benchmark_symbol': 'BTC-USD',
        'benchmark_name': 'Bitcoin',
        'benchmark_unit': 'BTC',
        'target_price': 250000,
        'start': '2024-01-01',
        'risk_rank': 3,
        'risk_label': 'Microcap treasury wrapper: smaller size means larger upside premium but materially higher execution risk.',
        'premium_label': 'Microcap BTC premium',
        'baseline_note': 'ASST demands a larger premium than Metaplanet because size and liquidity create more convexity and more fragility.',
        'thesis': 'ASST is treated as a smaller, higher-beta treasury stock. If the market rewards Bitcoin balance-sheet leverage, a smaller vehicle can re-rate harder than Metaplanet, but the same size advantage also makes drawdowns, dilution, and liquidity risk more severe.',
        'scenarios': [
            {'name': 'Tracks Bitcoin', 'multiple': 1.0},
            {'name': 'Small-cap premium', 'multiple': 3.0},
            {'name': 'Convex re-rating', 'multiple': 6.0},
            {'name': 'Extreme treasury premium', 'multiple': 10.0},
        ],
    },
    'bitmine': {
        'name': 'BitMine Immersion',
        'ticker': 'BMNR',
        'symbol': 'BMNR',
        'benchmark_symbol': 'ETH-USD',
        'benchmark_name': 'Ethereum',
        'benchmark_unit': 'ETH',
        'target_price': 25000,
        'start': '2024-01-01',
        'risk_rank': 4,
        'risk_label': 'Highest risk in the treasury-stock sleeve: Ethereum treasury premium, operating risk, and more volatile market trust.',
        'premium_label': 'ETH treasury premium',
        'baseline_note': 'BitMine needs a very high target premium because Ethereum treasury equities demand a larger premium and carry more narrative and execution risk than Bitcoin treasury equities.',
        'thesis': 'BitMine is treated as the highest-beta treasury equity in this set. The target price assumptions should be aggressive because the market generally demands a larger premium for Ethereum-linked treasury exposure than for Bitcoin-linked balance-sheet exposure. This is not the fortress asset; it is the outer risk sleeve.',
        'scenarios': [
            {'name': 'Tracks Ethereum', 'multiple': 1.0},
            {'name': 'High premium returns', 'multiple': 5.0},
            {'name': 'ETH treasury mania', 'multiple': 10.0},
            {'name': 'Extreme premium', 'multiple': 20.0},
        ],
    },
}

PORTFOLIO_REPORT = {
    'date': '31.05.2026',
    'cash': Decimal('5976.43'),
    'bitcoin': Decimal('19285.36'),
    'stocks': Decimal('24489.50'),
    'bitcoin_amount': Decimal('0.39094743'),
}

PORTFOLIO_HISTORY = [
    {
        'date': '31.01.2024',
        'cash': Decimal('7110.21'),
        'bitcoin': Decimal('10851.60'),
        'stocks': Decimal('18142.41'),
        'bitcoin_amount': Decimal('0.2946247629551326'),
    },
    {
        'date': '29.02.2024',
        'cash': Decimal('2388.94'),
        'bitcoin': Decimal('12928.14'),
        'stocks': Decimal('20950.55'),
        'bitcoin_amount': Decimal('0.2397075677272512'),
    },
    {
        'date': '31.03.2024',
        'cash': Decimal('3386.41'),
        'bitcoin': Decimal('11357.49'),
        'stocks': Decimal('18728.13'),
        'bitcoin_amount': Decimal('0.1765335984382139'),
    },
    {
        'date': '30.04.2024',
        'cash': Decimal('6877.06'),
        'bitcoin': Decimal('12531.81'),
        'stocks': Decimal('18351.72'),
        'bitcoin_amount': Decimal('0.2247575441063611'),
    },
    {
        'date': '31.05.2024',
        'cash': Decimal('5615.86'),
        'bitcoin': Decimal('14284.10'),
        'stocks': Decimal('18997.96'),
        'bitcoin_amount': Decimal('0.2348517807444580'),
    },
    {
        'date': '30.06.2024',
        'cash': Decimal('2208.09'),
        'bitcoin': Decimal('18138.39'),
        'stocks': Decimal('15315.33'),
        'bitcoin_amount': Decimal('0.3214492187168093'),
    },
    {
        'date': '31.07.2024',
        'cash': Decimal('1900.96'),
        'bitcoin': Decimal('14823.17'),
        'stocks': Decimal('15062.26'),
        'bitcoin_amount': Decimal('0.2612268963536279'),
    },
    {
        'date': '31.08.2024',
        'cash': Decimal('1925.06'),
        'bitcoin': Decimal('17341.34'),
        'stocks': Decimal('11012.24'),
        'bitcoin_amount': Decimal('0.3466047341343739'),
    },
    {
        'date': '30.09.2024',
        'cash': Decimal('2734.18'),
        'bitcoin': Decimal('16948.10'),
        'stocks': Decimal('11518.24'),
        'bitcoin_amount': Decimal('0.3166081864515977'),
    },
    {
        'date': '31.10.2024',
        'cash': Decimal('1694.92'),
        'bitcoin': Decimal('20365.39'),
        'stocks': Decimal('12202.31'),
        'bitcoin_amount': Decimal('0.3355430997875829'),
    },
    {
        'date': '30.11.2024',
        'cash': Decimal('850.76'),
        'bitcoin': Decimal('26956.29'),
        'stocks': Decimal('22621.59'),
        'bitcoin_amount': Decimal('0.3172632643403502'),
    },
    {
        'date': '31.12.2024',
        'cash': Decimal('305.68'),
        'bitcoin': Decimal('30763.68'),
        'stocks': Decimal('19168.79'),
        'bitcoin_amount': Decimal('0.3625882315064564'),
    },
    {
        'date': '28.02.2025',
        'cash': Decimal('210.53'),
        'bitcoin': Decimal('28642.43'),
        'stocks': Decimal('15676.32'),
        'bitcoin_amount': Decimal('0.3766390831527100'),
    },
    {
        'date': '31.03.2025',
        'cash': Decimal('295.67'),
        'bitcoin': Decimal('21925.51'),
        'stocks': Decimal('13417.09'),
        'bitcoin_amount': Decimal('0.3005265492782613'),
    },
    {
        'date': '30.04.2025',
        'cash': Decimal('0.00'),
        'bitcoin': Decimal('21079.35'),
        'stocks': Decimal('13665.59'),
        'bitcoin_amount': Decimal('0.2708611526954541'),
    },
    {
        'date': '31.05.2025',
        'cash': Decimal('575.50'),
        'bitcoin': Decimal('23485.12'),
        'stocks': Decimal('13728.42'),
        'bitcoin_amount': Decimal('0.2723326450644974'),
    },
    {
        'date': '30.06.2025',
        'cash': Decimal('575.03'),
        'bitcoin': Decimal('23465.79'),
        'stocks': Decimal('13717.11'),
        'bitcoin_amount': Decimal('0.2762691679308987'),
    },
    {
        'date': '31.07.2025',
        'cash': Decimal('527.66'),
        'bitcoin': Decimal('26353.66'),
        'stocks': Decimal('15003.17'),
        'bitcoin_amount': Decimal('0.2797028679418128'),
    },
    {
        'date': '31.08.2025',
        'cash': Decimal('2215.88'),
        'bitcoin': Decimal('23378.65'),
        'stocks': Decimal('17594.47'),
        'bitcoin_amount': Decimal('0.2697982147065591'),
    },
    {
        'date': '30.09.2025',
        'cash': Decimal('8018.84'),
        'bitcoin': Decimal('25179.16'),
        'stocks': Decimal('22149.03'),
        'bitcoin_amount': Decimal('0.2771976212991545'),
    },
    {
        'date': '31.10.2025',
        'cash': Decimal('10726.08'),
        'bitcoin': Decimal('24234.97'),
        'stocks': Decimal('24488.53'),
        'bitcoin_amount': Decimal('0.2766214853458475'),
    },
    {
        'date': '30.11.2025',
        'cash': Decimal('10792.11'),
        'bitcoin': Decimal('24384.16'),
        'stocks': Decimal('24639.28'),
        'bitcoin_amount': Decimal('0.3353186521362005'),
    },
    {
        'date': '31.12.2025',
        'cash': Decimal('4183.23'),
        'bitcoin': Decimal('19637.38'),
        'stocks': Decimal('25608.66'),
        'bitcoin_amount': Decimal('0.2804621057210911'),
    },
    {
        'date': '31.01.2026',
        'cash': Decimal('3054.89'),
        'bitcoin': Decimal('18233.63'),
        'stocks': Decimal('15978.94'),
        'bitcoin_amount': Decimal('0.2804621057210911'),
    },
    {
        'date': '28.02.2026',
        'cash': Decimal('6473.79'),
        'bitcoin': Decimal('15999.41'),
        'stocks': Decimal('13270.44'),
        'bitcoin_amount': Decimal('0.31562533'),
    },
    {
        'date': '31.03.2026',
        'cash': Decimal('626.71'),
        'bitcoin': Decimal('16470.45'),
        'stocks': Decimal('15670.57'),
        'bitcoin_amount': Decimal('0.3041361'),
    },
    {
        'date': '30.04.2026',
        'coingecko_date': '30-04-2026',
        'cash': Decimal('4055.42'),
        'bitcoin': Decimal('18132.71'),
        'stocks': Decimal('22767.77'),
    },
    PORTFOLIO_REPORT,
]

DASHBOARD_USERNAME = os.environ.get('HASHEN_DASHBOARD_USERNAME', 'hashen')
DASHBOARD_PASSWORD = os.environ.get('HASHEN_DASHBOARD_PASSWORD', 'hashen123')


def require_dashboard_auth(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Basic '):
            try:
                encoded = auth_header.split(' ', 1)[1].strip()
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)
                if (
                    compare_digest(username, DASHBOARD_USERNAME) and
                    compare_digest(password, DASHBOARD_PASSWORD)
                ):
                    return view_func(request, *args, **kwargs)
            except (ValueError, UnicodeDecodeError):
                pass
        response = HttpResponse('Authentication required', status=401)
        response['WWW-Authenticate'] = 'Basic realm="Hashen private dashboard"'
        return response
    return wrapped


def portfolio_total():
    return PORTFOLIO_REPORT['cash'] + PORTFOLIO_REPORT['bitcoin'] + PORTFOLIO_REPORT['stocks']


def period_total(period):
    return period['cash'] + period['bitcoin'] + period['stocks']


def chf(value):
    return "CHF {:,.2f}".format(value).replace(",", "'")


def pdf_escape(value):
    return str(value).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def build_simple_pdf(lines):
    content_lines = ['BT', '/F1 11 Tf', '50 790 Td', '16 TL']
    for line in lines:
        content_lines.append('(%s) Tj' % pdf_escape(line))
        content_lines.append('T*')
    content_lines.append('ET')
    stream = '\n'.join(content_lines).encode('latin-1', 'replace')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length %d >>\nstream\n%s\nendstream' % (len(stream), stream),
    ]
    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(b'%d 0 obj\n' % index)
        pdf.extend(obj)
        pdf.extend(b'\nendobj\n')
    xref_offset = len(pdf)
    pdf.extend(b'xref\n0 %d\n' % (len(objects) + 1))
    pdf.extend(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        pdf.extend(b'%010d 00000 n \n' % offset)
    pdf.extend(b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objects) + 1, xref_offset))
    return bytes(pdf)


def get_default_newsletter():
    newsletter = Newsletter.objects.first()
    if newsletter:
        return newsletter
    return Newsletter.objects.create(
        title='Hashen',
        slug='daily-news',
        email='contact@hashen.finance',
        sender='Hashen',
    )


def privacy_policy(request):
    return render(request, 'blog/privacy.html')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for contacting us!")
            return redirect('index')  # Redirect to a success page.
        else:
            print(form.errors)
    # else:
    #     form = ContactForm()
    
    # return render(request, 'base1.html', {'form': form})



@login_required
def resources_view(request):
    resources = Resource.objects.all().order_by('-created_at')  # Assuming you want the newest resources first
    return render(request, 'blog/resources.html', {'resources': resources})



@login_required
def dashboard(request):
    # Fetch the posts by the current user
    user_posts = Post.objects.filter(author=request.user).order_by('-date_posted')

    # Fetch comments on the user's posts
    user_comments = Comment.objects.filter(post__author=request.user).order_by('-created_at')

    # You can add more context as per your application's functionality
    context = {
        'title': 'Dashboard',
        'user_posts': user_posts,
        'user_comments': user_comments
    }

    return render(request, 'blog/dashboard.html', context)

class PostListView(ListView):
    model = Post
    template_name = 'blog/blog.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        try:
            keyword = self.request.GET['q']
        except:
            keyword = ''
        if (keyword != ''):
            object_list = self.model.objects.filter(
                Q(content__icontains=keyword) | Q(title__icontains=keyword))
        else:
            object_list = self.model.objects.all()
        return object_list


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

def bitcoin(request):
    return render(request, 'blog/bitcoin.html', {'title': 'Bitcoin'})

def blog(request):
        return render(request, 'blog/blog.html', {'title': 'Blog'})

def index(request):
    newsletter = get_default_newsletter()
    return render(request, 'blog/index.html', {'title': 'Index', 'newsletter':newsletter})

@require_dashboard_auth
def dashboard(request):
    return render(request, 'blog/dashboard.html', {'title': 'Dashboard'})


@require_dashboard_auth
def mstr_dashboard(request):
    return render(request, 'blog/mstr_dashboard.html', {'title': 'MSTR'})


@require_dashboard_auth
def stocks_dashboard(request):
    return render(request, 'blog/stocks_dashboard.html', {'title': 'Stocks'})


@require_dashboard_auth
def treasury_stock_dashboard(request, slug):
    config = TREASURY_STOCKS.get(slug)
    if not config:
        return redirect('stocks_dashboard')
    context = {
        'title': config['name'],
        'stock': config,
        'stock_json': json.dumps(config),
        'slug': slug,
        'treasury_stocks': TREASURY_STOCKS,
    }
    return render(request, 'blog/treasury_stock_dashboard.html', context)


def get_historical_bitcoin_chf(date):
    params = parse.urlencode({
        'date': date,
        'localization': 'false',
    })
    url = 'https://api.coingecko.com/api/v3/coins/bitcoin/history?%s' % params
    with urlrequest.urlopen(url, timeout=8) as response:
        data = json.loads(response.read().decode('utf-8'))
    return Decimal(str(data['market_data']['current_price']['chf']))


@require_dashboard_auth
def wealth_progression(request):
    periods = []
    for period in PORTFOLIO_HISTORY:
        historical_price = None
        btc_amount = None
        if period.get('bitcoin_amount'):
            btc_amount = period['bitcoin_amount']
        elif period.get('coingecko_date'):
            try:
                historical_price = get_historical_bitcoin_chf(period['coingecko_date'])
                btc_amount = period['bitcoin'] / historical_price
            except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError, InvalidOperation):
                historical_price = None
                btc_amount = None
        periods.append({
            'date': period['date'],
            'cash_chf': float(period['cash']),
            'bitcoin_chf': float(period['bitcoin']),
            'stocks_chf': float(period['stocks']),
            'total_chf': float(period_total(period)),
            'bitcoin_price_chf': float(historical_price) if historical_price else None,
            'bitcoin_amount': float(btc_amount) if btc_amount else None,
        })

    first_total = period_total(PORTFOLIO_HISTORY[0])
    latest_total = period_total(PORTFOLIO_HISTORY[-1])
    return JsonResponse({
        'status': 'ok',
        'source': 'CoinGecko',
        'source_url': 'https://docs.coingecko.com/reference/coins-id-history',
        'periods': periods,
        'change_chf': float(latest_total - first_total),
        'change_pct': float((latest_total - first_total) / first_total * Decimal('100')),
    })


@require_dashboard_auth
def portfolio_report_pdf(request):
    total = portfolio_total()
    lines = [
        'Hashen - Portfolio Report',
        'Reporting date: %s' % PORTFOLIO_REPORT['date'],
        '',
        'Portfolio summary',
        'Cash: %s' % chf(PORTFOLIO_REPORT['cash']),
        'Bitcoin: %s' % chf(PORTFOLIO_REPORT['bitcoin']),
        'Stocks: %s' % chf(PORTFOLIO_REPORT['stocks']),
        'Total portfolio value: %s' % chf(total),
        '',
        'Allocation',
        'Cash: %.2f%%' % (PORTFOLIO_REPORT['cash'] / total * Decimal('100')),
        'Bitcoin: %.2f%%' % (PORTFOLIO_REPORT['bitcoin'] / total * Decimal('100')),
        'Stocks: %.2f%%' % (PORTFOLIO_REPORT['stocks'] / total * Decimal('100')),
        '',
        'Notes',
        'This report reflects user-provided figures for the month-end reporting date.',
        'Values are shown in CHF and are intended for local portfolio reporting.',
    ]
    response = HttpResponse(build_simple_pdf(lines), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="hashen-portfolio-report-2026-05-31.pdf"'
    return response


def bitcoin_price(request):
    currencies = request.GET.get('currencies', 'chf,usd,eur,gbp').lower()
    allowed_currencies = {'chf', 'usd', 'eur', 'gbp'}
    selected_currencies = [
        currency for currency in currencies.split(',')
        if currency in allowed_currencies
    ] or ['chf']
    params = parse.urlencode({
        'ids': 'bitcoin',
        'vs_currencies': ','.join(selected_currencies),
        'include_24hr_change': 'true',
        'include_last_updated_at': 'true',
        'precision': 'full',
    })
    url = 'https://api.coingecko.com/api/v3/simple/price?%s' % params
    market_url = 'https://api.coingecko.com/api/v3/coins/markets?%s' % parse.urlencode({
        'vs_currency': 'chf',
        'ids': 'bitcoin',
        'precision': 'full',
    })

    try:
        with urlrequest.urlopen(url, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
        market_data = {}
        try:
            with urlrequest.urlopen(market_url, timeout=6) as response:
                market = json.loads(response.read().decode('utf-8'))
            if market:
                market_data = {
                    'ath_chf': market[0].get('ath'),
                    'ath_date': market[0].get('ath_date'),
                    'ath_change_percentage': market[0].get('ath_change_percentage'),
                }
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, IndexError, KeyError):
            market_data = {}
        return JsonResponse({
            'source': 'CoinGecko',
            'source_url': 'https://docs.coingecko.com/reference/simple-price',
            'status': 'live',
            'data': data,
            'market': market_data,
        })
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return JsonResponse({
            'source': 'CoinGecko',
            'source_url': 'https://docs.coingecko.com/reference/simple-price',
            'status': 'unavailable',
            'data': {
                'bitcoin': {
                    'chf': None,
                    'usd': None,
                    'eur': None,
                    'gbp': None,
                    'last_updated_at': None,
                    'chf_24h_change': None,
                    'usd_24h_change': None,
                    'eur_24h_change': None,
                    'gbp_24h_change': None,
                }
            },
            'market': {},
        }, status=503)


def _unix_date(value):
    parsed = datetime.strptime(value, '%Y-%m-%d')
    return int(parsed.replace(tzinfo=timezone.utc).timestamp())


def _fetch_yahoo_daily_series(symbol, start):
    period1 = _unix_date(start)
    period2 = int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp())
    params = parse.urlencode({
        'period1': period1,
        'period2': period2,
        'interval': '1d',
        'events': 'history',
        'includeAdjustedClose': 'true',
    })
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/%s?%s' % (parse.quote(symbol), params)
    req = urlrequest.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlrequest.urlopen(req, timeout=8) as response:
        payload = json.loads(response.read().decode('utf-8'))

    result = payload['chart']['result'][0]
    timestamps = result.get('timestamp') or []
    quote = result['indicators']['quote'][0]
    closes = quote.get('close') or []
    adjusted = result.get('indicators', {}).get('adjclose', [{}])[0].get('adjclose') or closes
    points = []
    for timestamp, close in zip(timestamps, adjusted):
        if close is None:
            continue
        points.append({
            'date': datetime.fromtimestamp(timestamp, tz=timezone.utc).date(),
            'close': float(close),
        })
    if not points:
        raise ValueError('No Yahoo Finance data returned for %s' % symbol)
    return points


def _month_end_points(points):
    months = {}
    for point in points:
        months[point['date'].strftime('%Y-%m')] = point
    return months


def _fetch_yahoo_quote(symbol):
    params = parse.urlencode({
        'range': '1d',
        'interval': '1m',
    })
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/%s?%s' % (parse.quote(symbol), params)
    req = urlrequest.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlrequest.urlopen(req, timeout=8) as response:
        payload = json.loads(response.read().decode('utf-8'))
    result = payload['chart']['result'][0]
    meta = result.get('meta', {})
    quote = result.get('indicators', {}).get('quote', [{}])[0]
    closes = [price for price in quote.get('close', []) if price is not None]
    price = meta.get('regularMarketPrice') or meta.get('previousClose') or (closes[-1] if closes else None)
    if price is None:
        raise ValueError('No price returned for %s' % symbol)
    return {
        'price': Decimal(str(price)),
        'currency': (meta.get('currency') or 'USD').upper(),
        'exchange': meta.get('exchangeName') or meta.get('fullExchangeName') or '',
        'time': meta.get('regularMarketTime'),
    }


def _fx_rate_to_chf(currency):
    currency = (currency or 'CHF').upper()
    if currency == 'CHF':
        return Decimal('1')
    if currency == 'USD':
        symbol = 'USDCHF=X'
    elif currency == 'EUR':
        symbol = 'EURCHF=X'
    else:
        symbol = '%sCHF=X' % currency
    return _fetch_yahoo_quote(symbol)['price']


@require_dashboard_auth
def stock_portfolio(request):
    fx_cache = {}
    holdings = []
    totals = {
        'USD': Decimal('0'),
        'EUR': Decimal('0'),
        'CHF': Decimal('0'),
        'cost_chf': Decimal('0'),
    }
    live_count = 0

    for holding in STOCK_HOLDINGS:
        error = None
        try:
            quote = _fetch_yahoo_quote(holding['symbol'])
            price = quote['price']
            currency = quote['currency']
            value = price * holding['shares']
            live = True
            live_count += 1
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            price = holding['fallback_value'] / holding['shares']
            currency = holding['fallback_currency']
            value = holding['fallback_value']
            live = False
            error = str(exc)

        fx_key = currency
        if fx_key not in fx_cache:
            try:
                fx_cache[fx_key] = _fx_rate_to_chf(fx_key)
            except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError):
                fx_cache[fx_key] = Decimal('0.89') if fx_key == 'EUR' else Decimal('0.80') if fx_key == 'USD' else Decimal('1')

        cost_currency = holding['cost_currency']
        if cost_currency not in fx_cache:
            try:
                fx_cache[cost_currency] = _fx_rate_to_chf(cost_currency)
            except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError):
                fx_cache[cost_currency] = Decimal('0.89') if cost_currency == 'EUR' else Decimal('0.80') if cost_currency == 'USD' else Decimal('1')

        value_chf = value * fx_cache[fx_key]
        cost_value = holding['shares'] * holding['average_price']
        cost_chf = cost_value * fx_cache[cost_currency]
        unrealized_chf = value_chf - cost_chf
        totals['CHF'] += value_chf
        totals['cost_chf'] += cost_chf
        if currency in totals:
            totals[currency] += value

        holdings.append({
            'name': holding['name'],
            'ticker': holding['ticker'],
            'symbol': holding['symbol'],
            'shares': float(holding['shares']),
            'price': float(price),
            'currency': currency,
            'value': float(value),
            'value_chf': float(value_chf),
            'average_price': float(holding['average_price']),
            'cost_currency': holding['cost_currency'],
            'cost_value': float(cost_value),
            'cost_chf': float(cost_chf),
            'unrealized_chf': float(unrealized_chf),
            'live': live,
            'error': error,
        })

    return JsonResponse({
        'status': 'ok',
        'source': 'Yahoo Finance',
        'live_count': live_count,
        'total_count': len(STOCK_HOLDINGS),
        'total_chf': float(totals['CHF']),
        'total_cost_chf': float(totals['cost_chf']),
        'unrealized_chf': float(totals['CHF'] - totals['cost_chf']),
        'totals': {
            'USD': float(totals['USD']),
            'EUR': float(totals['EUR']),
            'CHF': float(totals['CHF']),
        },
        'holdings': holdings,
    })


@require_dashboard_auth
def treasury_stock_data(request, slug):
    config = TREASURY_STOCKS.get(slug)
    if not config:
        return JsonResponse({
            'status': 'not_found',
            'error': 'Unknown treasury stock',
            'points': [],
        }, status=404)

    start = request.GET.get('start', config.get('start', '2024-01-01'))
    try:
        stock_months = _month_end_points(_fetch_yahoo_daily_series(config['symbol'], start))
        benchmark_months = _month_end_points(_fetch_yahoo_daily_series(config['benchmark_symbol'], start))
        points = []
        for month in sorted(set(stock_months) & set(benchmark_months)):
            stock_point = stock_months[month]
            benchmark_point = benchmark_months[month]
            benchmark_per_share = stock_point['close'] / benchmark_point['close']
            points.append({
                'date': stock_point['date'].strftime('%Y-%m-%d'),
                'label': stock_point['date'].strftime('%b %Y'),
                'stock_price': round(stock_point['close'], 4),
                'benchmark_price': round(benchmark_point['close'], 2),
                'benchmark_per_share': round(benchmark_per_share, 10),
                'units_per_share': round(benchmark_per_share * SATOSHIS_PER_BTC),
            })
        return JsonResponse({
            'status': 'ok',
            'source': 'Yahoo Finance',
            'stock': config,
            'symbol': '%s/%s' % (config['symbol'], config['benchmark_symbol']),
            'formula': '%s adjusted close / %s close * 100,000,000' % (config['symbol'], config['benchmark_symbol']),
            'points': points,
        })
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({
            'status': 'unavailable',
            'source': 'Yahoo Finance',
            'error': 'Could not build treasury stock chart data',
            'detail': str(exc),
            'points': [],
        }, status=503)


@require_dashboard_auth
def mstr_btc(request):
    start = request.GET.get('start', '2021-06-01')
    try:
        mstr_months = _month_end_points(_fetch_yahoo_daily_series('MSTR', start))
        btc_months = _month_end_points(_fetch_yahoo_daily_series('BTC-USD', start))
        points = []
        for month in sorted(set(mstr_months) & set(btc_months)):
            mstr_point = mstr_months[month]
            btc_point = btc_months[month]
            btc_per_share = mstr_point['close'] / btc_point['close']
            points.append({
                'date': mstr_point['date'].strftime('%Y-%m-%d'),
                'label': mstr_point['date'].strftime('%b %Y'),
                'mstr_usd': round(mstr_point['close'], 2),
                'btc_usd': round(btc_point['close'], 2),
                'btc_per_share': round(btc_per_share, 8),
                'sats_per_share': round(btc_per_share * SATOSHIS_PER_BTC),
            })
        return JsonResponse({
            'status': 'ok',
            'source': 'Yahoo Finance',
            'symbol': 'MSTR/BTC',
            'formula': 'MSTR adjusted close / BTC-USD close * 100,000,000',
            'points': points,
        })
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({
            'status': 'unavailable',
            'source': 'Yahoo Finance',
            'error': 'Could not build MSTR/BTC chart data',
            'detail': str(exc),
            'points': [],
        }, status=503)


@require_dashboard_auth
def ibkr_portfolio(request):
    base_url = os.environ.get('IBKR_GATEWAY_URL', 'https://localhost:5000').rstrip('/')
    context = ssl._create_unverified_context()

    def get_json(path):
        url = '%s%s' % (base_url, path)
        req = urlrequest.Request(url, headers={'Accept': 'application/json'})
        with urlrequest.urlopen(req, timeout=6, context=context) as response:
            return json.loads(response.read().decode('utf-8'))

    try:
        auth_status = get_json('/v1/api/iserver/auth/status')
        accounts = get_json('/v1/api/portfolio/accounts')
        if not accounts:
            raise ValueError('No IBKR accounts returned')

        account_id = accounts[0].get('id') or accounts[0].get('accountId') or accounts[0].get('account')
        if not account_id:
            raise ValueError('No IBKR account identifier returned')

        summary = get_json('/v1/api/portfolio/%s/summary' % parse.quote(str(account_id)))
        net_liquidation = None
        currency = None
        for key, value in summary.items():
            normalized_key = key.lower().replace(' ', '').replace('_', '')
            if normalized_key in ('netliquidation', 'netliquidationvalue', 'totalcashvalue'):
                if isinstance(value, dict):
                    net_liquidation = value.get('amount') or value.get('value')
                    currency = value.get('currency') or currency
                else:
                    net_liquidation = value
                break

        return JsonResponse({
            'status': 'connected',
            'gateway_url': base_url,
            'auth': auth_status,
            'account': accounts[0],
            'account_id': account_id,
            'summary': summary,
            'net_liquidation': net_liquidation,
            'currency': currency,
        })
    except (HTTPError, URLError, TimeoutError, ssl.SSLError, ValueError, json.JSONDecodeError) as error:
        return JsonResponse({
            'status': 'unavailable',
            'gateway_url': base_url,
            'message': 'IBKR Client Portal Gateway is not reachable or not authenticated.',
            'detail': str(error),
        }, status=503)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        user = User.objects.get(id=request.POST.get('user_id'))
        text = request.POST.get('text')
        Comment(author=user, post=post, text=text).save()
        messages.success(request, "Your comment has been added successfully.")
    else:
        return redirect('post_detail', pk=pk)
    return redirect('post_detail', pk=pk)
