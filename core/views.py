from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, FileResponse
from .forms import SignUpForm, TransactionForm, CategoryForm, BudgetForm, SavingsGoalForm, AddToGoalForm
from .models import Transaction, Category, UserProfile, SavingsGoal
import io
import reportlab.pdfgen.canvas
import json
from django.utils.safestring import mark_safe
from datetime import datetime


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
    """Allows users to manually input transactions."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('dashboard')
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'core/create_transaction.html', {'form': form})

@login_required
def add_category(request):
    """Allows users to create categories for expenditures."""
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
    """Allows users to set or adjust their budget."""
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
    """Dashboard showing net worth and spending breakdown."""
    transactions = Transaction.objects.filter(user=request.user)
    income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    net_worth = income - expenses
    current_month_year = datetime.now().strftime("%B %Y")

    # Calculate spending breakdown by category
    categories = Category.objects.filter(user=request.user)
    category_breakdown = []
    for cat in categories:
        cat_expenses = transactions.filter(category=cat, transaction_type='expense')
        total = sum(t.amount for t in cat_expenses)
        if total > 0:
            category_breakdown.append((cat.name, total))
    # Calculate income breakdown by category
    income_category_breakdown = []
    for cat in categories:
        cat_income = transactions.filter(category=cat, transaction_type='income')
        total_income = sum(t.amount for t in cat_income)
        if total_income > 0:
            income_category_breakdown.append((cat.name, total_income))

    context = {
        'expenses': expenses,
        'category_labels': mark_safe(json.dumps([cat for cat, _ in category_breakdown])),
        'category_data': mark_safe(json.dumps([amt for _, amt in category_breakdown])),
        'income': income,
        'income_category_labels': mark_safe(json.dumps([cat for cat, _ in income_category_breakdown])),
        'income_category_data': mark_safe(json.dumps([amt for _, amt in income_category_breakdown])),
        'net_worth': net_worth,
        'category_breakdown': category_breakdown,
        'income_category_breakdown': income_category_breakdown,
        'current_month_year': current_month_year,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def reports(request):
    """Shows a financial report."""
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
def savings(request):
    goals = SavingsGoal.objects.filter(user=request.user)
    if request.method == 'POST':
        savings_goal_form = SavingsGoalForm(request.POST)
        if savings_goal_form.is_valid():
            goal = savings_goal_form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('savings_goal')
    else:
        savings_goal_form = SavingsGoalForm()

    for goal in goals:
        goal.add_form=AddToGoalForm()

    return render(request, 'core/savings_goal.html', {
        'savings_goal_form': savings_goal_form,
        'goals': goals,
            #'add_forms': {g.id: AddToGoalForm() for g in goals}
    })
@login_required
def add_to_goal(request, goal_id):
    goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
    if request.method == 'POST':
        add_goal_form = AddToGoalForm(request.POST)
        if add_goal_form.is_valid():
            goal.curr_amount += add_goal_form.cleaned_data['amount']
            goal.save()
    return redirect('savings_goal')



@login_required
def export_pdf(request):
    """Exports the financial report as a PDF."""
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
    """Admin view to review AI-generated financial advice."""
    advice_list = [
        {"id": 1, "advice": "Consider reducing discretionary spending."},
        {"id": 2, "advice": "Increase your savings rate for long-term goals."},
    ]
    context = {'advice_list': advice_list}
    return render(request, 'core/review_financial_advice.html', context)

# -----------------------------
# New Views for User Settings
# -----------------------------

@login_required
def user_settings(request):
    """Display the user settings page."""
    return render(request, 'core/user_settings.html')

@login_required
def update_profile_color(request):
    """Update the user’s profile color."""
    if request.method == 'POST':
        new_color = request.POST.get('avatar_color', '#0d6efd')
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.color = new_color
        user_profile.save()
        messages.success(request, "Profile color updated successfully!")
    return redirect('user_settings')
@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        # Ensure the file is provided:
        if 'profile_picture' in request.FILES:
            picture = request.FILES['profile_picture']
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            user_profile.profile_picture = picture
            user_profile.save()
            messages.success(request, "Profile picture updated successfully!")
        else:
            messages.error(request, "Please upload a valid image.")
        return redirect('user_settings')
    else:
        messages.error(request, "Invalid request.")
        return redirect('user_settings')
@login_required
def remove_profile_picture(request):
    if request.method == 'POST':
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.profile_picture = None  # Clear the image
        user_profile.save()
        messages.success(request, "Profile picture removed successfully!")
    else:
        messages.error(request, "Invalid request.")
    return redirect('user_settings')
@login_required
def delete_account(request):
    """Delete the current user’s account after confirmation."""
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('index')
    # If GET request, show confirmation page
    return render(request, 'core/confirm_delete_account.html')
