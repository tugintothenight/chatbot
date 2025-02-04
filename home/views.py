from django.shortcuts import render, redirect
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
        if "clear_history" in request.POST:
            request.session.pop("chat_history", None)  # Xóa lịch sử khỏi session
            Answer.objects.all().delete()
            return render(request, 'home/chatGoD.html', {"answer": None})
        question = request.POST.get("question", "")
        logger.error(question)
        pdf_file_path = None
        pdf_folder = os.path.join(settings.MEDIA_ROOT, "documents")
        logger.error("qua bước nhận file và câu hỏi")
        # if question != "" and pdf_file is not None:
        #     logger.error("hỏi rag")
        #     pdf_text = extract_text_from_pdf(pdf_file)
        #     chunks = split_text_into_chunks(pdf_text)
        #     relevant_chunks = find_relevant_chunks(question, chunks, embedding_model)
        #     combined_context = " ".join(relevant_chunks)
        #     answer = ask_gemini(question, combined_context)
        #     logger.error(answer)
        #     logger.error("đã xử lý file")
        #     logger.error("tốn token")
        #     form_data = {
        #         "ask_content": request.POST.get("question", ""),
        #         "answer_content": answer
        #     }
        #
        #     # Khởi tạo form với dữ liệu mới
        #     form = AnswerForm(form_data)
        #     if form.is_valid():
        #         # Lưu dữ liệu từ form
        #         ask = form.save(commit=False)
        #         ask.uploaded_by = request.user
        #         ask.save()
        #         logger.error("đã có form rag")
        #         answer = Answer.objects.last()
        #         logger.error(answer.answer_content)
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
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, "Tải lên thành công!")
            return redirect('upload')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng thử lại.")

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
