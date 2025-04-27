# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.http import FileResponse
from django.utils.safestring import mark_safe
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io, json

from .forms import (
    SignUpForm, TransactionForm, CategoryForm,
    BudgetForm, SavingsGoalForm, AddToGoalForm
)
from .models import Transaction, Category, UserProfile, SavingsGoal
from django.db.models import Sum


# Public pages
def index(request):
    """Public landing page."""
    return render(request, 'core/index.html')

def about(request):
    """About MoneyParce."""
    return render(request, 'core/about.html')


# Signup / Auth
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})


# Admin-only decorator
def admin_required(view_func):
    return login_required(user_passes_test(lambda u: u.is_staff)(view_func))


# Admin user management
@admin_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'core/user_list.html', {'users': users})

@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
    else:
        user.delete()
        messages.success(request, f"User '{user.username}' deleted.")
    return redirect('user_list')


# Transaction / Category / Budget
@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = request.user
            tx.save()
            messages.success(request, "Transaction added!")
            return redirect('dashboard')
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'core/create_transaction.html', {'form': form})

@admin_required
def review_financial_advice(request):
    """Admin view to review AI-generated financial advice."""
    advice_list = [
        {"id": 1, "advice": "Consider reducing discretionary spending."},
        {"id": 2, "advice": "Increase your savings rate for long-term goals."},
    ]
    return render(request, 'core/review_financial_advice.html', {
        'advice_list': advice_list
    })

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.user = request.user
            cat.save()
            messages.success(request, "Category created!")
            return redirect('dashboard')
    else:
        form = CategoryForm()
    return render(request, 'core/add_category.html', {'form': form})

@login_required
def set_budget(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget updated!")
            return redirect('dashboard')
    else:
        form = BudgetForm(instance=profile)
    return render(request, 'core/set_budget.html', {'form': form})


# Dashboard
@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    now = datetime.now()
    current_month_year = now.strftime("%B %Y")

    # Build exactly 12 months from Jan of this year
    start = datetime(now.year, 1, 1)
    months, incs, exps, nets = [], [], [], []
    exp_by_month, inc_by_month = {}, {}
    cats = Category.objects.filter(user=request.user)

    for i in range(12):
        dt = start + relativedelta(months=i)
        label = dt.strftime("%b %Y")
        months.append(label)

        mi = transactions.filter(
            transaction_type='income',
            date__year=dt.year,
            date__month=dt.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        me = transactions.filter(
            transaction_type='expense',
            date__year=dt.year,
            date__month=dt.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        incs.append(mi)
        exps.append(me)
        nets.append(mi - me)

        # category breakdown
        elabs, eds, ilabs, ids = [], [], [], []
        for c in cats:
            amt_e = transactions.filter(
                transaction_type='expense',
                category=c,
                date__year=dt.year,
                date__month=dt.month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            if amt_e:
                elabs.append(c.name); eds.append(amt_e)

            amt_i = transactions.filter(
                transaction_type='income',
                category=c,
                date__year=dt.year,
                date__month=dt.month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            if amt_i:
                ilabs.append(c.name); ids.append(amt_i)

        exp_by_month[label] = {'labels': elabs, 'data': eds}
        inc_by_month[label] = {'labels': ilabs, 'data': ids}

    # Totals
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    net_worth = total_income - total_expenses

    # Fallback to the current month (even though chart covers full year)
    curr_label = now.strftime("%b %Y")
    cb = exp_by_month.get(curr_label, {'labels': [], 'data': []})
    ib = inc_by_month.get(curr_label, {'labels': [], 'data': []})

    context = {
        'monthly_labels': mark_safe(json.dumps(months)),
        'monthly_income_data': mark_safe(json.dumps(incs)),
        'monthly_expense_data': mark_safe(json.dumps(exps)),
        'monthly_networth_data': mark_safe(json.dumps(nets)),
        'monthly_expense_breakdown': mark_safe(json.dumps(exp_by_month)),
        'monthly_income_breakdown': mark_safe(json.dumps(inc_by_month)),

        'category_labels': mark_safe(json.dumps(cb['labels'])),
        'category_data': mark_safe(json.dumps(cb['data'])),
        'income_category_labels': mark_safe(json.dumps(ib['labels'])),
        'income_category_data': mark_safe(json.dumps(ib['data'])),

        'category_breakdown_list': list(zip(cb['labels'], cb['data'])),
        'income_category_breakdown_list': list(zip(ib['labels'], ib['data'])),

        'income': total_income,
        'expenses': total_expenses,
        'net_worth': net_worth,
        'current_month_year': current_month_year,
    }
    return render(request, 'core/dashboard.html', context)


# Reports & PDF
@login_required
def reports(request):
    txs = Transaction.objects.filter(user=request.user)
    ctx = {
        'total_income': sum(t.amount for t in txs if t.transaction_type=='income'),
        'total_expenses': sum(t.amount for t in txs if t.transaction_type=='expense'),
        'transactions': txs,
    }
    return render(request, 'core/reports.html', ctx)

@login_required
def export_pdf(request):
    buf = io.BytesIO()
    p = io.BytesIO()  # using reportlab directly
    from reportlab.pdfgen import canvas
    can = canvas.Canvas(buf)
    txs = Transaction.objects.filter(user=request.user)
    inc = sum(t.amount for t in txs if t.transaction_type=='income')
    exp = sum(t.amount for t in txs if t.transaction_type=='expense')
    can.drawString(100,800,f"Report for {request.user.username}")
    can.drawString(100,780,f"Income: ${inc}")
    can.drawString(100,760,f"Expenses: ${exp}")
    y = 740
    for t in txs:
        can.drawString(100,y,f"{t.date} – {t.transaction_type}: ${t.amount}")
        y -= 20
        if y < 50: break
    can.showPage()
    can.save(); buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename='report.pdf')


# Savings Goals
@login_required
def savings(request):
    goals = SavingsGoal.objects.filter(user=request.user)
    if request.method=='POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.user = request.user
            g.save()
            return redirect('savings_goal')
    else:
        form = SavingsGoalForm()
    for g in goals:
        g.add_form = AddToGoalForm()
    return render(request, 'core/savings_goal.html', {
        'savings_goal_form': form,
        'goals': goals,
    })

@login_required
def add_to_goal(request, goal_id):
    goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
    if request.method=='POST':
        f = AddToGoalForm(request.POST)
        if f.is_valid():
            goal.curr_amount += f.cleaned_data['amount']
            goal.save()
    return redirect('savings_goal')


# User settings and profile
@login_required
def user_settings(request):
    return render(request, 'core/user_settings.html')

@login_required
def update_profile_color(request):
    if request.method=='POST':
        color = request.POST.get('avatar_color', '#0d6efd')
        prof, _ = UserProfile.objects.get_or_create(user=request.user)
        prof.color = color
        prof.save()
        messages.success(request, "Color updated!")
    return redirect('user_settings')

@login_required
def update_profile_picture(request):
    if request.method=='POST' and 'profile_picture' in request.FILES:
        pic = request.FILES['profile_picture']
        prof, _ = UserProfile.objects.get_or_create(user=request.user)
        prof.profile_picture = pic
        prof.save()
        messages.success(request, "Picture updated!")
    else:
        messages.error(request, "No picture uploaded.")
    return redirect('user_settings')

@login_required
def remove_profile_picture(request):
    if request.method=='POST':
        prof,_ = UserProfile.objects.get_or_create(user=request.user)
        prof.profile_picture = None
        prof.save()
        messages.success(request, "Picture removed!")
    return redirect('user_settings')

@login_required
def delete_account(request):
    if request.method=='POST':
        request.user.delete()
        messages.success(request, "Account deleted.")
        return redirect('index')
    return render(request, 'core/confirm_delete_account.html')
