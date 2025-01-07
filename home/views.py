from django.shortcuts import render, redirect
from home.models import Document
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from home.forms import DocumentForm


def upload(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Bạn cần đăng nhập để tiếp tục.")
        return redirect('login')
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, "Tải lên thành công!")
            return redirect('upload')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng thử lại.")
    else:
        form = DocumentForm()
    documents = Document.objects.all()
    documentP = Document.objects.filter(uploaded_by=request.user)
    return render(request, 'home/upload.html',
                  {'form': form,
                   'documents': documents,
                   'documentP': documentP})


def logout_view(request):
    logout(request)
    messages.success(request, 'Đăng xuất thành công.')
    return redirect('login')


def admin_check(user):
    return user.is_staff


@login_required(login_url='login')
@user_passes_test(admin_check, login_url='home')
def account(request):
    users = User.objects.all()
    return render(request, 'admin/account.html', {'users': users})


def chatGoD(request):
    documents = Document.objects.all()

    return render(request, 'home/chatGoD.html', {'documents': documents})


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request, 'Mật khẩu không khớp!')
            return render(request, 'home/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tên tài khoản đã tồn tại!')
            return render(request, 'home/register.html')

        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, e)
            return render(request, 'home/register.html')

        user = User.objects.create_user(username=username, password=password)
        user.save()
        messages.success(request, 'Đăng ký thành công!')
        return redirect('login')

    return render(request, 'home/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # messages.success(request, f'Chào mừng, {user.username}! Đăng nhập thành công!')
            return redirect('account')
        else:
            messages.error(request, 'Tên tài khoản hoặc mật khẩu không đúng.')

    return render(request, 'home/login.html')
