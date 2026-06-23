import base64
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

PORTFOLIO_REPORT = {
    'date': '31.05.2026',
    'cash': Decimal('5976.43'),
    'bitcoin': Decimal('19285.36'),
    'stocks': Decimal('24489.50'),
    'bitcoin_amount': Decimal('0.39094743'),
}

PORTFOLIO_HISTORY = [
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

    try:
        with urlrequest.urlopen(url, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
        return JsonResponse({
            'source': 'CoinGecko',
            'source_url': 'https://docs.coingecko.com/reference/simple-price',
            'status': 'live',
            'data': data,
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
