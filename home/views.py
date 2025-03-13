from django.shortcuts import render, redirect, get_object_or_404
from home.models import Document, Answer
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from home.forms import DocumentForm, AnswerForm
from home.rag import get_all_pdf_text, split_text_into_chunks, find_relevant_chunks, asking
from sentence_transformers import SentenceTransformer
import logging
import os
from django.conf import settings

logger = logging.getLogger('django')
# Mô hình Sentence Transformer
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


# View chính để hiển thị giao diện
def making_context(question, pdf_url='media'):
    pdf_text = get_all_pdf_text(pdf_url)
    chunks = split_text_into_chunks(pdf_text)
    relevant_chunks = find_relevant_chunks(question, chunks, embedding_model)
    combined_context = " ".join(relevant_chunks)
    return combined_context


def chatGoD(request):

    history = request.session.get("chat_history", [])
    if request.method == "POST":
        logger.error("đã nhận POST")
        logger.error(request.POST)
        if "clear_history" in request.POST:
            request.session.pop("chat_history", None)  # Xóa lịch sử khỏi session
            Answer.objects.all().delete()
            return render(request, 'home/chatGoD.html', {"answer": None})
        question = request.POST.get("question", "")
        logger.error(question)
        pdf_file_path = None
        pdf_folder = os.path.join(settings.MEDIA_ROOT, "documents")
        logger.error("qua bước nhận file và câu hỏi")

        if question != "":
            context = making_context(question, pdf_folder)
            answer = asking(question, context, history)
            history.append((question, answer))
            request.session["chat_history"] = history
            logger.error("tốn token")
            form_data = {
                "ask_content": request.POST.get("question", ""),
                "answer_content": answer
            }
            form = AnswerForm(form_data)
            if form.is_valid():
                # Lưu dữ liệu từ form
                ask = form.save(commit=False)
                ask.uploaded_by = request.user
                ask.save()
                logger.error("đã có form thường")
                answer = Answer.objects.last()
                logger.error(answer.answer_content)
    answer = Answer.objects.last()

    logger.error("hết")
    return render(request, 'home/chatGoD.html', {"answer": answer})


def admin_check(user):
    return user.is_staff


@user_passes_test(admin_check, login_url='home')
def upload(request):
    if request.method == 'POST':
        logger.error("post request")
        logger.error(request.POST)

        if "delete_document" in request.POST:
            try:
                logger.error("Nhận post delete")
                document_id = request.POST.get("id")  # Lấy ID từ form
                logger.error(document_id)
                document = get_object_or_404(Document, id=document_id)
                if document.document:
                    file_path = document.document.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                document.delete()
                messages.success(request, "Tài liệu đã được xóa thành công!")
            except Exception as e:
                logger.error(f"Lỗi khi xóa tài liệu: {e}")
                messages.error(request, "Có lỗi xảy ra khi xóa tài liệu. Vui lòng thử lại!")
            return redirect('upload')

        if "update_note" in request.POST:
            try:
                document_id = request.POST.get("id")
                document = get_object_or_404(Document, id=document_id)
                document.description = request.POST.get("input-req")
                document.save()
                messages.success(request, "Cập nhật mô tả thành công!")
            except Exception as e:
                logger.error(f"Lỗi khi cập nhật mô tả: {e}")
                messages.error(request, "Có lỗi xảy ra khi cập nhật mô tả. Vui lòng thử lại!")
            return redirect('upload')

        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.uploaded_by = request.user
                document.save()
                messages.success(request, "Tải lên thành công!")
            except Exception as e:
                logger.error(f"Lỗi khi tải lên tài liệu: {e}")
                messages.error(request, "Có lỗi xảy ra khi tải lên. Vui lòng thử lại!")
            return redirect('upload')

    documents = Document.objects.all()

    return render(request, 'admin/uploadManage.html',
                  {
                      'documents': documents})


def select_files(request):
    return render(request, 'home/select_files.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Đăng xuất thành công.')
    return redirect('login')


@login_required(login_url='login')
@user_passes_test(admin_check, login_url='home')
def account(request):
    users = User.objects.all()
    if "delete_account" in request.POST:
        account_id = request.POST.get("id")  # Lấy ID từ form
        acc = get_object_or_404(User, id=account_id)
        acc.delete()  # Xóa tài liệu trong database
        messages.success(request, "Tài khoản đã được xóa thành công!")
        return redirect('account')
    if "update_auth" in request.POST:
        try:
            account_id = request.POST.get("id")
            account = get_object_or_404(User, id=account_id)
            if request.POST.get("newauth") == "Superadmin":
                account.is_superuser = True
                account.is_staff = True
            elif request.POST.get("newauth") == "Staff":
                account.is_superuser = False
                account.is_staff = True
            else:
                account.is_superuser = False
                account.is_staff = False
            account.save()
            messages.success(request, "Cập nhật thành công!")
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật mô tả: {e}")
            messages.error(request, "Có lỗi xảy ra khi cập nhật mô tả. Vui lòng thử lại!")
        return redirect('account')
    return render(request, 'admin/account.html', {'users': users})


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
