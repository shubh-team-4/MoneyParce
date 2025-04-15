from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, FileResponse
from .forms import SignUpForm, TransactionForm, CategoryForm, BudgetForm
from .models import Transaction, Category, UserProfile
import io
import reportlab.pdfgen.canvas

def index(request):
    """Public page explaining MoneyParce."""
    return render(request, 'core/index.html')

def about(request):
    """Additional info about MoneyParce purpose."""
    return render(request, 'core/about.html')

def signup(request):
    """User signup view for new account creation."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

# Decorator to ensure only admins can access certain pages
def admin_required(view_func):
    decorated_view_func = login_required(
        user_passes_test(lambda u: u.is_staff, login_url='/', redirect_field_name=None)(view_func)
    )
    return decorated_view_func

@admin_required
def user_list(request):
    """Admin view to list and manage users."""
    users = User.objects.all()
    return render(request, 'core/user_list.html', {'users': users})

@admin_required
def delete_user(request, user_id):
    """Admin view to delete a user account."""
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')
    user.delete()
    messages.success(request, f"User '{user.username}' has been deleted.")
    return redirect('user_list')

@login_required
def create_transaction(request):
    """Allows users to manually input transactions (User Stories #8 and #9)."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            # Stub for Plaid auto-categorization could be inserted here (User Story #10)
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('dashboard')
    else:
        form = TransactionForm()
    return render(request, 'core/create_transaction.html', {'form': form})

@login_required
def add_category(request):
    """Allows users to create categories for expenditures (User Story #11)."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, "Category created successfully!")
            return redirect('dashboard')
    else:
        form = CategoryForm()
    return render(request, 'core/add_category.html', {'form': form})

@login_required
def set_budget(request):
    """Allows users to set or adjust their budget (User Stories #12 and #13)."""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget updated successfully!")
            return redirect('dashboard')
    else:
        form = BudgetForm(instance=user_profile)
    return render(request, 'core/set_budget.html', {'form': form})

@login_required
def dashboard(request):
    """Dashboard showing net worth and spending breakdown (User Stories #17 and #18)."""
    transactions = Transaction.objects.filter(user=request.user)
    income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    net_worth = income - expenses

    # Calculate spending breakdown by category
    categories = Category.objects.filter(user=request.user)
    category_breakdown = []
    for cat in categories:
        cat_expenses = transactions.filter(category=cat, transaction_type='expense')
        total = sum(t.amount for t in cat_expenses)
        category_breakdown.append((cat.name, total))
    context = {
        'income': income,
        'expenses': expenses,
        'net_worth': net_worth,
        'category_breakdown': category_breakdown,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def reports(request):
    """Shows a financial report (User Story #15)."""
    transactions = Transaction.objects.filter(user=request.user)
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'transactions': transactions,
    }
    return render(request, 'core/reports.html', context)

@login_required
def export_pdf(request):
    """Exports the financial report as a PDF (User Story #16)."""
    buffer = io.BytesIO()
    p = reportlab.pdfgen.canvas.Canvas(buffer)
    transactions = Transaction.objects.filter(user=request.user)
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    p.drawString(100, 800, f"Financial Report for {request.user.username}")
    p.drawString(100, 780, f"Total Income: ${total_income}")
    p.drawString(100, 760, f"Total Expenses: ${total_expenses}")
    p.drawString(100, 740, "Transactions:")
    y = 720
    for t in transactions:
        p.drawString(100, y, f"{t.date} - {t.transaction_type.capitalize()}: ${t.amount}")
        y -= 20
        if y < 50:
            break  # Only listing a few transactions for brevity
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='report.pdf')

@admin_required
def review_financial_advice(request):
    """Admin view to review AI-generated financial advice (User Story #20). This stub can be expanded."""
    advice_list = [
        {"id": 1, "advice": "Consider reducing discretionary spending."},
        {"id": 2, "advice": "Increase your savings rate for long-term goals."},
    ]
    context = {'advice_list': advice_list}
    return render(request, 'core/review_financial_advice.html', context)
