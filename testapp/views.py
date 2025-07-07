# testapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Q, Case, When, IntegerField
import json
import random
import datetime
from django.views.decorators.http import require_http_methods
from .utils.exports import (
    export_results_csv, export_results_excel,
    export_questions_csv, export_questions_json,
    export_subjects_csv,
)
from .utils.generate_questions import generate_questions
from .utils.analytics import AnalyticsEngine
from .utils.notifications import NotificationService
from django.urls import reverse


from .models import Subject, SubjectDay, Question, Test, TestQuestion, Result, StudentAnswer, ChatMessage
from .forms import LoginForm, SubjectForm, QuestionForm, BulkQuestionForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from google import genai
from google.genai.types import Content, GenerateContentConfig
from django.conf import settings
import requests


client = genai.Client(api_key=settings.API_KEY_GENAI)
def get_answer_ai(text, history, sys_instruct_chat):
    models = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-preview-04-17', 'gemini-2.5-flash-lite-preview-06-17']
    for model in models:
        try:
            chat = client.chats.create(
                    model=model,
                    config= GenerateContentConfig(system_instruction=sys_instruct_chat),
                    history=[Content(parts=[
                                {
                                    "video_metadata": None,
                                    "thought": None,
                                    "inline_data": None,
                                    "file_data": None,
                                    "thought_signature": None,
                                    "code_execution_result": None,
                                    "executable_code": None,
                                    "function_call": None,
                                    "function_response": None,
                                    "text": data.text
                                }
                            ],
                            role=data.role
                        ) 
                        for data in history
                        ]
                    )
            response = chat.send_message(text)
            return response.text
        except:
            print(f'Model {model} is not available!')
            continue


def send_message(chat_id, message, test_id=None):
    try:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        if test_id:
            keyboard = [[
                {
                    'text': 'Analizlew • Nátiyjeler',
                    'url': f'{settings.WEB_APP_URL}/results?startapp={test_id}'
                }
            ]]
            payload['reply_markup'] = json.dumps(keyboard)
        telegram_token = settings.TELEGRAM_BOT_TOKEN
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        print(payload, url)
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sending message: {e}")
        

# ==================== MAIN PAGES ====================

def home_view(request):
    return render(request, 'testapp/home.html')


def test_start_view(request):
    """Test start page"""
    test_id = request.GET.get('test_id') or request.GET.get('tgWebAppStartParam')
    # Show all get args
    print(request.GET)
    
    if not test_id:
        messages.error(request, 'Test ID not provided!')
        return redirect('testapp:home')
    
    try:
        test = get_object_or_404(Test, id=test_id, is_active=True)
    except:
        raise Http404("Test not found or inactive!")
    
    # Get test questions
    questions = test.get_questions()
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name')
        
        # Validation
        if not student_id or not student_name:
            messages.error(request, 'Student ID and Name are required!')
            context = {
                'test': test,
                'questions': questions,
                'student_id': student_id,
                'student_name': student_name,
            }
            return render(request, 'testapp/test/start.html', context)
        
        # # Duplicate test check
        # if Result.objects.filter(test=test, student_id=student_id).exists():
        #     messages.error(request, 'You have already taken this test!')
        #     return redirect(f"{reverse('testapp:test_results')}?test_id={test_id}")
        
        # Check and save answers
        correct_count = 0
        total_questions = questions.count()
        
        # Create result
        result = Result.objects.create(
            test=test,
            student_id=student_id,
            student_name=student_name,
            total_questions=total_questions,
            correct_answers=0,  # For now 0, will be updated later
            score_percentage=0,  # For now 0, will be updated later
        )

        text_model = f'Assalawma aleykum, {student_name}!\n'
        text_model += f'Sizge №{test.id} {test.subject.name} ({test.subject.grade}-klass) testin analizlewde kómeklesiwge tayarman.\n\n'
        n = 1
        for question in questions:
            student_answer = request.POST.get(f'question_{question.id}')
            text_model += f'<b>{n}. {question.question_text}</b><br>'
            text_model += f'A) {question.option_a}<br>'
            text_model += f'B) {question.option_b}<br>'
            text_model += f'C) {question.option_c}<br>'
            text_model += f'D) {question.option_d}<br>'
            text_model += f'Sizdiń juwabıńız: {student_answer}\n\n'            

            is_correct = (student_answer == question.correct_answer)
            if is_correct:
                correct_count += 1
            
            StudentAnswer.objects.create(
                result=result,
                question=question,
                student_answer=student_answer if student_answer else '',
                is_correct=is_correct
            )

            n += 1
        
        # Update result
        score_percentage = (correct_count / total_questions) * 100
        result.correct_answers = correct_count
        result.score_percentage = score_percentage
        result.save()

        message = f'🎉 <b>{student_name}</b> {test.subject.name} ({test.subject.grade}-klass) testinen nátiyjeńiz: {correct_count}/{total_questions}'
        send_message(student_id, message, test.id)

        text_model += f'Qaysı soraw boyınsha kómek kerek?'
        ChatMessage.objects.create(
            student_id=student_id,
            test_id=test.id,
            text=text_model,
            role='model'
        )
        
        # Redirect to results page
        # return redirect(f"{reverse('testapp:test_results')}?test_id={test_id}")
    
    context = {
        'test': test,
        'questions': questions,
    }
    return render(request, 'testapp/test/start.html', context)


def test_results_view(request):
    """Test results page"""
    test_id = request.GET.get('test_id') or request.GET.get('tgWebAppStartParam')
    
    if not test_id:
        messages.error(request, 'Test ID not provided!')
        return redirect('testapp:home')
    
    try:
        test = get_object_or_404(Test, id=test_id)
    except:
        raise Http404("Test not found!")
    
    # Get all results (ordered by highest score)
    results = Result.objects.filter(test=test).order_by('-score_percentage', 'completed_at')
    
    # Statistics
    stats = {
        'total_participants': results.count(),
        'average_score': results.aggregate(avg_score=Avg('score_percentage'))['avg_score'] or 0,
        'highest_score': results.first().score_percentage if results.exists() else 0,
    }
    
    context = {
        'test': test,
        'results': results,
        'stats': stats,
    }
    return render(request, 'testapp/test/results.html', context)


def test_landing_view(request):
    """Landing page for multiple tests"""
    test_ids = request.GET.get('tests') or request.GET.get('tgWebAppStartParam')
    
    if not test_ids:
        messages.error(request, 'Test IDs not provided!')
        return redirect('testapp:home')
    
    try:
        # Split test IDs and convert to list of integers
        test_id_list = [
            int(tid.strip()) for tid in test_ids.split('A')
            if tid.strip().isdigit()
        ]
        
        # Get all active tests with these IDs
        tests = Test.objects.filter(
            id__in=test_id_list,
            is_active=True
        ).select_related('subject').order_by('subject__grade')
                
        if not tests.exists():
            messages.error(request, 'No active tests found!')
            return redirect('testapp:home')
        
        context = {
            'tests': tests,
            'total_tests': tests.count(),
            'WEB_APP_URL': settings.WEB_APP_URL,
        }
        return render(request, 'testapp/test/landing.html', context)
        
    except (ValueError, TypeError):
        messages.error(request, 'Invalid test ID format!')
        return redirect('testapp:home')


def test_chatbot_view(request):
    """Test chatbot page"""
    test_id = request.GET.get('test_id') or request.GET.get('tgWebAppStartParam')
    
    if not test_id:
        messages.error(request, 'Test ID not provided!')
        return redirect('testapp:home')
    
    try:
        test = get_object_or_404(Test, id=test_id)
    except:
        raise Http404("Test not found!")
    
    
    context = {
        'test': test,
    }
    return render(request, 'testapp/test/chatbot.html', context)


def user_dashboard(request):
    return render(request, 'testapp/user_dashboard.html')





# ==================== ADMIN PAGES ====================


def admin_login_view(request):
    """Admin login page"""
    if request.user.is_authenticated:
        return redirect('testapp:admin_dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_staff:
                login(request, user)
                return redirect('testapp:admin_dashboard')
            else:
                messages.error(request, 'Login or password is incorrect!')
    else:
        form = LoginForm()
    
    context = {'form': form}
    return render(request, 'testapp/admin/login.html', context)


def admin_logout_view(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('testapp:admin_login')


@login_required
def admin_dashboard_view(request):
    """Admin dashboard page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    # Statistics
    stats = {
        'total_subjects': Subject.objects.count(),
        'total_questions': Question.objects.count(),
        'total_tests': Test.objects.count(),
        'today_tests': Test.objects.filter(created_at__date=timezone.now().date()).count(),
        'total_participants': Result.objects.count(),
    }
    
    # Today's tests
    today_tests = Test.objects.filter(created_at__date=timezone.now().date())
    
    # Recent results
    recent_results = Result.objects.all().order_by('-completed_at')[:20]
    
    context = {
        'stats': stats,
        'today_tests': today_tests,
        'recent_results': recent_results,
        'now': timezone.now(),
    }
    return render(request, 'testapp/admin/dashboard.html', context)


@login_required
def admin_subjects_view(request):
    """Subjects management page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')

    subjects = Subject.objects.all().order_by('name')

    # Filterlar
    name_filter = request.GET.get('name')
    grade_filter = request.GET.get('grade')

    if name_filter:
        subjects = subjects.filter(name=name_filter)
    if grade_filter:
        subjects = subjects.filter(grade=grade_filter)

    # Unikal fan nomlari va sinflar select uchun
    all_names = Subject.objects.values_list('name', flat=True).distinct()
    all_grades = Subject.objects.values_list('grade', flat=True).distinct().order_by('grade')

    context = {
        'subjects': subjects,
        'selected_name': name_filter,
        'selected_grade': grade_filter,
        'all_names': all_names,
        'all_grades': all_grades,
    }
    return render(request, 'testapp/admin/subjects.html', context)


@login_required
def admin_subject_add_view(request):
    """Add subject page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f' Subject {subject.name} successfully added!')
            return redirect('testapp:admin_subjects')
    else:
        form = SubjectForm()
    
    context = {'form': form}
    return render(request, 'testapp/admin/subject_form.html', context)


@login_required
def admin_subject_edit_view(request, subject_id):
    """Edit subject page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject {subject.name} successfully updated!')
            return redirect('testapp:admin_subjects')
    else:
        form = SubjectForm(instance=subject)
    
    context = {'form': form, 'subject': subject}
    return render(request, 'testapp/admin/subject_form.html', context)


@login_required
def admin_subject_delete_view(request, subject_id):
    """Delete subject"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, f'Subject {subject.name} deleted successfully!')
    return redirect('testapp:admin_subjects')


@login_required
def admin_questions_view(request):
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    questions = Question.objects.all().order_by('-created_at')

    subject_filter = request.GET.get('subject')
    if subject_filter:
        questions = questions.filter(subject_id=subject_filter)

    # Paginate: 10 ta savol har bir sahifada
    paginator = Paginator(questions, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    subjects = Subject.objects.all()
    
    context = {
        'questions': page_obj,  # o‘zgartirildi
        'subjects': subjects,
        'selected_subject': subject_filter,
        'page_obj': page_obj,   # pagination uchun template’da kerak
    }
    return render(request, 'testapp/admin/questions.html', context)


@login_required
def admin_question_add_view(request):
    """Add question page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            messages.success(request, 'Question successfully added!')
            return redirect('testapp:admin_questions')
    else:
        form = QuestionForm()
    
    context = {'form': form}
    return render(request, 'testapp/admin/question_form.html', context)


@login_required
def admin_questions_bulk_add_view(request):
    """Bulk add questions page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    if request.method == 'POST':
        form = BulkQuestionForm(request.POST)
        if form.is_valid():
            questions_data = form.cleaned_data['questions_data']
            subject = form.cleaned_data['subject']
            
            created_count = 0
            for q_data in questions_data:
                Question.objects.create(
                    subject=subject,
                    question_text=q_data['question_text'],
                    option_a=q_data['option_a'],
                    option_b=q_data['option_b'],
                    option_c=q_data['option_c'],
                    option_d=q_data['option_d'],
                    correct_answer=q_data['correct_answer'],
                )
                created_count += 1
            
            messages.success(request, f'{created_count} questions successfully added!')
            return redirect('testapp:admin_questions')
    else:
        form = BulkQuestionForm()
    
    context = {'form': form}
    return render(request, 'testapp/admin/bulk_questions.html', context)


@login_required
def admin_question_edit_view(request, question_id):
    """Edit question page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question successfully updated!')
            return redirect('testapp:admin_questions')
    else:
        form = QuestionForm(instance=question)
    
    context = {'form': form, 'question': question}
    return render(request, 'testapp/admin/question_form.html', context)


@login_required
def admin_question_delete_view(request, question_id):
    """Delete question"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    question = get_object_or_404(Question, id=question_id)
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    return redirect('testapp:admin_questions')


@login_required
def admin_tests_view(request):
    """Tests list page with search, filtering, and pagination"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    # Get all tests as base queryset
    tests = Test.objects.select_related('subject').prefetch_related('results', 'test_questions')
    
    # Search by Test ID
    test_id = request.GET.get('test_id', '').strip()
    if test_id:
        tests = tests.filter(id__icontains=test_id)
    
    # Filter by Subject
    subject_id = request.GET.get('subject_id', '').strip()
    selected_subject = None
    if subject_id:
        try:
            selected_subject = Subject.objects.get(id=subject_id)
            tests = tests.filter(subject_id=subject_id)
        except Subject.DoesNotExist:
            pass
    
    # Sort functionality
    sort_by = request.GET.get('sort_by', '-created_at')
    
    # Handle special sorting cases that need annotations
    if sort_by in ['-participants_count', 'participants_count']:
        tests = tests.annotate(
            participants_count=Count('results')
        )
        tests = tests.order_by(sort_by.replace('participants_count', 'participants_count'))
    
    elif sort_by in ['-avg_score', 'avg_score']:
        tests = tests.annotate(
            avg_score=Avg('results__score_percentage')
        )
        # Handle null values for tests with no participants
        tests = tests.annotate(
            avg_score_nulls_last=Case(
                When(avg_score__isnull=True, then=0),
                default='avg_score',
                output_field=IntegerField()
            )
        )
        order_field = 'avg_score_nulls_last' if sort_by == 'avg_score' else '-avg_score_nulls_last'
        tests = tests.order_by(order_field)
    
    else:
        # Standard sorting
        valid_sort_fields = ['id', '-id', 'created_at', '-created_at', 'subject__name', '-subject__name']
        if sort_by in valid_sort_fields:
            tests = tests.order_by(sort_by)
        else:
            tests = tests.order_by('-created_at')  # Default sort
    
    # Get all subjects for the filter dropdown
    subjects = Subject.objects.all().order_by('name')
    
    # Calculate summary statistics BEFORE pagination
    total_participants = Result.objects.filter(test__in=tests).count()
    
    # Overall average score
    overall_avg = Result.objects.filter(test__in=tests).aggregate(
        avg_score=Avg('score_percentage')
    )['avg_score'] or 0
    
    # Count active tests
    active_tests = tests.filter(is_active=True).count()
    
    # PAGINATION
    items_per_page = int(request.GET.get('per_page', 20))  # Default 20 items per page
    if items_per_page not in [10, 20, 50, 100]:
        items_per_page = 20  # Fallback to default
    
    paginator = Paginator(tests, items_per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.get_page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        page_obj = paginator.get_page(paginator.num_pages)
    
    context = {
        'tests': page_obj,  # This is now paginated
        'page_obj': page_obj,
        'paginator': paginator,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'total_participants': total_participants,
        'overall_avg_score': overall_avg,
        'active_tests': active_tests,
        'items_per_page': items_per_page,
        'total_tests': paginator.count,  # Total count before pagination
    }
    
    return render(request, 'testapp/admin/tests.html', context)

@login_required
def admin_test_detail_view(request, test_id):
    """Test details page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    test = get_object_or_404(Test, id=test_id)
    results = Result.objects.filter(test=test).order_by('-score_percentage')
    
    context = {
        'test': test,
        'results': results,
    }
    return render(request, 'testapp/admin/test_detail.html', context)


@login_required
def admin_results_view(request):
    """Results page with search, filtering, and pagination"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    # Get all results as base queryset
    results = Result.objects.select_related('test', 'test__subject').all()
    
    # Search by Student Name
    student_name = request.GET.get('student_name', '').strip()
    if student_name:
        results = results.filter(student_name__icontains=student_name)
    
    # Search by Student ID
    student_id = request.GET.get('student_id', '').strip()
    if student_id:
        results = results.filter(student_id__icontains=student_id)

    # Search by Test ID
    test_id = request.GET.get('test_id', '').strip()
    if test_id:
        results = results.filter(test_id=test_id)
    
    # Filter by Subject
    subject_id = request.GET.get('subject_id', '').strip()
    selected_subject = None
    if subject_id:
        try:
            selected_subject = Subject.objects.get(id=subject_id)
            results = results.filter(test__subject_id=subject_id)
        except Subject.DoesNotExist:
            pass
    
    # Sort functionality
    sort_by = request.GET.get('sort_by', '-completed_at')
    
    # Valid sort fields
    valid_sort_fields = [
        'completed_at', '-completed_at',
        'score_percentage', '-score_percentage',
        'student_name', '-student_name',
        'student_id', '-student_id',
        'test__subject__name', '-test__subject__name'
    ]
    
    if sort_by in valid_sort_fields:
        results = results.order_by(sort_by)
    else:
        results = results.order_by('-completed_at')  # Default sort
    
    # Get all subjects for the filter dropdown
    subjects = Subject.objects.all().order_by('name')
    
    # Calculate summary statistics BEFORE pagination
    total_results = results.count()
    average_score = results.aggregate(avg_score=Avg('score_percentage'))['avg_score'] or 0
    
    # PAGINATION
    items_per_page = int(request.GET.get('per_page', 20))  # Default 20 items per page
    if items_per_page not in [10, 20, 50, 100]:
        items_per_page = 20  # Fallback to default
    
    paginator = Paginator(results, items_per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.get_page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        page_obj = paginator.get_page(paginator.num_pages)
    
    context = {
        'results': page_obj,  # This is now paginated
        'page_obj': page_obj,
        'paginator': paginator,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'items_per_page': items_per_page,
        'total_results': paginator.count,  # Total count before pagination
        'average_score': average_score,
        # Keep current search/filter values
        'current_student_name': student_name,
        'current_student_id': student_id,
        'current_test_id': test_id,
        'current_sort': sort_by,
    }
    
    return render(request, 'testapp/admin/results.html', context)


# ==================== API ENDPOINTS ====================

@csrf_exempt
@login_required
def api_create_test(request):
    """Test creation API"""
    if request.method == 'POST':
        data = json.loads(request.body)
        subject_id = data.get('subject_id')
        
        try:
            subject = Subject.objects.get(id=subject_id)
            
            # Check if enough questions are available
            available_questions = Question.objects.filter(subject=subject)
            if available_questions.count() < subject.questions_count:
                return JsonResponse({
                    'success': False,
                    'message': f'Not enough questions for this subject! Required: {subject.questions_count}, Available: {available_questions.count()}'
                })
            
            # Create test
            test = Test.objects.create(subject=subject)
            
            # Select random questions
            selected_questions = random.sample(list(available_questions), subject.questions_count)
            
            # Create test-question relation
            for index, question in enumerate(selected_questions, 1):
                TestQuestion.objects.create(
                    test=test,
                    question=question,
                    order_number=index
                )
            
            return JsonResponse({
                'success': True,
                'test_id': test.id,
                'message': 'Test created successfully!'
            })
            
        except Subject.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Subject not found!'
            })
    
    return JsonResponse({'success': False, 'message': 'Only POST requests are accepted!'})


def api_check_test(request):
    """Check test existence API"""
    test_id = request.GET.get('test_id')
    
    if not test_id:
        return JsonResponse({'exists': False, 'message': 'Test ID not provided!'})
    
    try:
        test = Test.objects.get(id=test_id, is_active=True)
        return JsonResponse({
            'exists': True,
            'test': {
                'id': test.id,
                'subject': test.subject.name,
                'grade': test.subject.grade,
                'questions_count': test.test_questions.count(),
                'created_at': test.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    except Test.DoesNotExist:
        return JsonResponse({'exists': False, 'message': 'Test not found or inactive!'})
    


# ==================== EXPORT VIEWS ====================

@login_required
def export_results_view(request):
    """Export results in various formats"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    format_type = request.GET.get('format', 'csv')
    test_id = request.GET.get('test_id')
    subject_id = request.GET.get('subject_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Build queryset
    results = Result.objects.all().order_by('-completed_at')
    
    if test_id:
        results = results.filter(test_id=test_id)
    
    if subject_id:
        results = results.filter(test__subject_id=subject_id)
    
    if date_from:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            results = results.filter(completed_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            results = results.filter(completed_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Export based on format
    if format_type == 'excel':
        return export_results_excel(results)
    else:
        return export_results_csv(results)


@login_required
def export_questions_view(request):
    """Export questions in various formats"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    format_type = request.GET.get('format', 'csv')
    subject_id = request.GET.get('subject_id')
    
    questions = Question.objects.all().order_by('-created_at')
    
    if subject_id:
        questions = questions.filter(subject_id=subject_id)
    
    if format_type == 'json':
        return export_questions_json(questions)
    else:
        return export_questions_csv(questions)


@login_required
def export_subjects_view(request):
    """Export subjects to CSV"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    subjects = Subject.objects.all().order_by('name')
    return export_subjects_csv(subjects)


# ==================== ANALYTICS VIEWS ====================

@login_required
def analytics_dashboard_view(request):
    """Analytics dashboard"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    # Date range filter
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - datetime.timedelta(days=days)
    
    analytics = AnalyticsEngine(date_range=(start_date, end_date))
    
    context = {
        'overall_stats': analytics.get_overall_statistics(),
        'subject_performance': analytics.get_subject_performance(),
        'daily_stats': analytics.get_daily_statistics(days=7),
        'top_performers': analytics.get_top_performers(limit=10),
        'question_difficulty': analytics.get_question_difficulty_analysis()[:20],
        'grade_comparison': analytics.get_grade_comparison(),
        'selected_days': days,
    }
    
    return render(request, 'testapp/admin/analytics.html', context)


@login_required
def question_difficulty_analysis_view(request):
    """Question difficulty analysis page"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    subject_id = request.GET.get('subject_id')
    
    analytics = AnalyticsEngine()
    difficulty_data = analytics.get_question_difficulty_analysis()
    
    if subject_id:
        difficulty_data = [
            q for q in difficulty_data 
            if Question.objects.get(id=q['question_id']).subject_id == int(subject_id)
        ]
    
    subjects = Subject.objects.all()
    
    context = {
        'difficulty_data': difficulty_data,
        'subjects': subjects,
        'selected_subject': subject_id,
    }
    
    return render(request, 'testapp/admin/question_difficulty.html', context)


# ==================== ADVANCED SEARCH AND FILTER ====================

@login_required
def advanced_search_view(request):
    """Advanced search across all data"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    
    results = {
        'subjects': [],
        'questions': [],
        'tests': [],
        'results': [],
        'students': [],
    }
    
    if query:
        if search_type in ['all', 'subjects']:
            results['subjects'] = Subject.objects.filter(
                Q(name__icontains=query) | Q(grade__icontains=query)
            )[:10]
        
        if search_type in ['all', 'questions']:
            results['questions'] = Question.objects.filter(
                Q(question_text__icontains=query) |
                Q(option_a__icontains=query) |
                Q(option_b__icontains=query) |
                Q(option_c__icontains=query) |
                Q(option_d__icontains=query)
            )[:20]
        
        if search_type in ['all', 'tests']:
            results['tests'] = Test.objects.filter(
                Q(subject__name__icontains=query) |
                Q(id__icontains=query)
            )[:10]
        
        if search_type in ['all', 'results', 'students']:
            results['results'] = Result.objects.filter(
                Q(student_name__icontains=query) |
                Q(student_id__icontains=query)
            )[:20]
    
    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_found': sum(len(r) for r in results.values())
    }
    
    return render(request, 'testapp/admin/advanced_search.html', context)


# ==================== BULK OPERATIONS ====================

@login_required
@require_http_methods(["POST"])
def bulk_delete_questions_view(request):
    """Bulk delete questions"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    question_ids = request.POST.getlist('question_ids[]')
    
    if not question_ids:
        return JsonResponse({'success': False, 'message': 'No questions selected'})
    
    try:
        deleted_count = Question.objects.filter(id__in=question_ids).count()
        Question.objects.filter(id__in=question_ids).delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} questions'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting questions: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def bulk_activate_tests_view(request):
    """Bulk activate/deactivate tests"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    test_ids = request.POST.getlist('test_ids[]')
    action = request.POST.get('action')  # 'activate' or 'deactivate'
    
    if not test_ids or action not in ['activate', 'deactivate']:
        return JsonResponse({'success': False, 'message': 'Invalid parameters'})
    
    try:
        is_active = action == 'activate'
        updated_count = Test.objects.filter(id__in=test_ids).update(is_active=is_active)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully {action}d {updated_count} tests'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating tests: {str(e)}'
        })


# ==================== API ENDPOINTS FOR AJAX ====================

@csrf_exempt
def api_get_subjects(request):
    """Get subjects list for dropdowns"""
    subjects = Subject.objects.all().values('id', 'name', 'grade', 'questions_count')
    
    # Add additional info
    for subject in subjects:
        subject_obj = Subject.objects.get(id=subject['id'])
        subject['available_questions'] = subject_obj.questions.count()
        subject['has_enough_questions'] = subject_obj.has_enough_questions()
        subject['scheduled_days'] = [
            day.get_day_of_week_display() 
            for day in subject_obj.subject_days.all()
        ]
    
    return JsonResponse({'subjects': list(subjects)})


@csrf_exempt
def api_get_subject_stats(request, subject_id):
    """Get detailed stats for a subject"""
    try:
        subject = Subject.objects.get(id=subject_id)
        
        # Calculate stats
        total_tests = subject.tests.count()
        total_participants = Result.objects.filter(test__subject=subject).count()
        avg_score = Result.objects.filter(test__subject=subject).aggregate(
            avg=Avg('score_percentage')
        )['avg'] or 0
        
        recent_tests = subject.tests.order_by('-created_at')[:5]
        
        stats = {
            'subject_name': subject.name,
            'grade': subject.grade,
            'total_questions': subject.questions.count(),
            'required_questions': subject.questions_count,
            'total_tests': total_tests,
            'total_participants': total_participants,
            'average_score': round(avg_score, 2),
            'has_enough_questions': subject.has_enough_questions(),
            'recent_tests': [
                {
                    'id': test.id,
                    'created_at': test.created_at.strftime('%Y-%m-%d %H:%M'),
                    'participants': test.get_participants_count(),
                    'avg_score': test.get_average_score()
                }
                for test in recent_tests
            ]
        }
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Subject not found'})


@csrf_exempt
def api_get_test_stats(request, test_id):
    """Get detailed stats for a test"""
    try:
        test = Test.objects.get(id=test_id)
        results = Result.objects.filter(test=test)
        
        stats = {
            'test_id': test.id,
            'subject_name': test.subject.name,
            'grade': test.subject.grade,
            'created_at': test.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_active': test.is_active,
            'total_questions': test.test_questions.count(),
            'total_participants': results.count(),
            'average_score': results.aggregate(avg=Avg('score_percentage'))['avg'] or 0,
            'highest_score': results.aggregate(max=Max('score_percentage'))['max'] or 0,
            'lowest_score': results.aggregate(min=Min('score_percentage'))['min'] or 0,
            'pass_rate': results.filter(score_percentage__gte=60).count() / max(results.count(), 1) * 100,
        }
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except Test.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Test not found'})


@csrf_exempt
def api_duplicate_test(request, test_id):
    """Duplicate an existing test"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        original_test = Test.objects.get(id=test_id)
        
        # Create new test
        new_test = Test.objects.create(
            subject=original_test.subject,
            is_active=True
        )
        
        # Copy test questions
        for test_question in original_test.test_questions.all():
            TestQuestion.objects.create(
                test=new_test,
                question=test_question.question,
                order_number=test_question.order_number
            )
        
        return JsonResponse({
            'success': True,
            'test_id': new_test.id,
            'message': f'Test duplicated successfully! New test ID: {new_test.id}'
        })
        
    except Test.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Original test not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ==================== REAL-TIME UPDATES ====================

@csrf_exempt
def api_live_results(request, test_id):
    """Get live results for a test (for real-time updates)"""
    try:
        test = Test.objects.get(id=test_id)
        results = Result.objects.filter(test=test).order_by('-score_percentage', '-completed_at')
        
        # Check for new results since last check
        last_check = request.GET.get('since')
        if last_check:
            try:
                since_time = datetime.datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                new_results = results.filter(completed_at__gt=since_time)
                has_new_results = new_results.exists()
            except:
                has_new_results = False
        else:
            has_new_results = True
        
        data = {
            'test_id': test.id,
            'has_new_results': has_new_results,
            'total_participants': results.count(),
            'average_score': results.aggregate(avg=Avg('score_percentage'))['avg'] or 0,
            'results': [
                {
                    'student_name': result.student_name,
                    'student_id': result.student_id,
                    'score_percentage': result.score_percentage,
                    'correct_answers': result.correct_answers,
                    'total_questions': result.total_questions,
                    'completed_at': result.completed_at.isoformat(),
                    'rank': idx + 1
                }
                for idx, result in enumerate(results[:50])  # Limit to top 50
            ],
            'last_updated': timezone.now().isoformat()
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Test.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Test not found'})


# ==================== NOTIFICATION VIEWS ====================

@login_required
def send_test_notification_view(request, test_id):
    """Send notification about test creation"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        test = Test.objects.get(id=test_id)
        recipients = request.POST.getlist('recipients[]')
        
        if not recipients:
            return JsonResponse({'success': False, 'message': 'No recipients specified'})
        
        notification_service = NotificationService()
        notification_service.send_test_created_notification(test, recipients)
        
        return JsonResponse({
            'success': True,
            'message': f'Notification sent to {len(recipients)} recipients'
        })
        
    except Test.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Test not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ==================== IMPORT FUNCTIONS ====================

@login_required
def import_questions_view(request):
    """Import questions from CSV/Excel file"""
    if not request.user.is_staff:
        return redirect('testapp:admin_login')
    
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'No file selected')
            return redirect('testapp:admin_questions')
        
        uploaded_file = request.FILES['file']
        subject_id = request.POST.get('subject_id')
        
        if not subject_id:
            messages.error(request, 'Please select a subject')
            return redirect('testapp:admin_questions')
        
        try:
            subject = Subject.objects.get(id=subject_id)
            
            # Process file based on extension
            if uploaded_file.name.endswith('.csv'):
                imported_count = process_csv_import(uploaded_file, subject)
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                imported_count = process_excel_import(uploaded_file, subject)
            else:
                messages.error(request, 'Unsupported file format. Please use CSV or Excel.')
                return redirect('testapp:admin_questions')
            
            messages.success(request, f'Successfully imported {imported_count} questions')
            
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found')
        except Exception as e:
            messages.error(request, f'Error importing file: {str(e)}')
    
    return redirect('testapp:admin_questions')


def process_csv_import(file, subject):
    """Process CSV file import"""
    import csv
    import io
    
    file_content = file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_content))
    
    imported_count = 0
    
    for row in csv_reader:
        if all([
            row.get('question_text'),
            row.get('option_a'),
            row.get('option_b'),
            row.get('option_c'),
            row.get('option_d'),
            row.get('correct_answer') in ['A', 'B', 'C', 'D']
        ]):
            Question.objects.create(
                subject=subject,
                question_text=row['question_text'].strip(),
                option_a=row['option_a'].strip(),
                option_b=row['option_b'].strip(),
                option_c=row['option_c'].strip(),
                option_d=row['option_d'].strip(),
                correct_answer=row['correct_answer'].upper().strip()
            )
            imported_count += 1
    
    return imported_count


def process_excel_import(file, subject):
    """Process Excel file import"""
    import openpyxl
    
    workbook = openpyxl.load_workbook(file)
    worksheet = workbook.active
    
    imported_count = 0
    
    # Skip header row
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        if len(row) >= 6 and all([row[0], row[1], row[2], row[3], row[4], row[5]]):
            if row[5].upper() in ['A', 'B', 'C', 'D']:
                Question.objects.create(
                    subject=subject,
                    question_text=str(row[0]).strip(),
                    option_a=str(row[1]).strip(),
                    option_b=str(row[2]).strip(),
                    option_c=str(row[3]).strip(),
                    option_d=str(row[4]).strip(),
                    correct_answer=str(row[5]).upper().strip()
                )
                imported_count += 1
    
    return imported_count


@csrf_exempt
def api_check_participation(request):
    """Endpoint to check if a student has participated in a test"""
    student_id = request.GET.get('student_id')
    test_id = request.GET.get('test_id')

    if not student_id or not test_id:
        return JsonResponse({'participated': False, 'message': 'student_id and test_id are required.'})

    exists = Result.objects.filter(test_id=test_id, student_id=student_id).exists()
    if exists:
        result = Result.objects.filter(test_id=test_id, student_id=student_id).first()
        result = {
            'student_name': result.student_name,
            'correct_answers': result.correct_answers,
            'total_questions': result.total_questions,
            'completed_at': result.completed_at.strftime('%H:%M %d.%m.%Y'),
        }
    else:
        result = None
    return JsonResponse({'participated': exists, 'result': result})


@csrf_exempt
def api_generate_questions(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Faqat POST so‘rovi qabul qilinadi'}, status=405)

    try:
        data = json.loads(request.body)
        subject_id = data.get('subject_id')
        questions_count = int(data.get('questionsCount', 5))
        topics = data.get('topics') 
        print(topics)

        subject = get_object_or_404(Subject, id=subject_id)

        response_questions = generate_questions(subject=subject.name, grade=subject.grade, count=questions_count, topics=topics)

        # List of fake questions
        questions = []
        for q in response_questions:
            questions.append({
                'questionText': q.question,
                'options': {
                    'A': q.options[0],
                    'B': q.options[1],
                    'C': q.options[2],
                    'D': q.options[3],
                    'correct': q.correct_option_id,
                }
            })
        return JsonResponse({'questions': questions})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@csrf_exempt
def api_generate_answer(request):
    """Chatbot answer generation endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        test_id = data.get('test_id')
        student_id = data.get('student_id')
        message = data.get('message')
        print(test_id, student_id, message)
        if not (test_id and student_id and message):
            return JsonResponse({'success': False, 'error': 'test_id, student_id, and message are required'}, status=400)
        # TODO: Replace with real answer logic
        history = ChatMessage.objects.filter(student_id=student_id, test_id=test_id).order_by('created_at')
        today_histories = history.filter(created_at__date=timezone.now().date()).count()
        if today_histories >= int(settings.LIMIT_MESSAGES_PER_DAY):
            return JsonResponse({'success': True, 'answer': '`❗️Sizdiń bul test ushın búgingi kúnlik limitińiz tawsıldı.` '})
        result = get_object_or_404(Result, student_id=student_id, test_id=test_id)
        test = get_object_or_404(Test, id=test_id)
        sys_instruct_chat = '''
            1. ROL HÁM MAQSET:
                Sen – matematika páninen tájiriybeli oqıtıwshı hám Telegramdaǵı keńes-beriwshiseń. Seniń baslı maqsetiń – paydalanıwshılarǵa test máselelerin óz betinshe sheshiwge járdem beriw, olardı oylanıwǵa hám matematikalıq principlerdi tereńirek túsiniwge úyretiw.
                EŃ ÁHMIYETLI QAǴIYDA: Sen hesh qashan máselelerdiń durıs juwabın tuwrıdan-tuwrı aytpaysań. Seniń wazıypań – juwaptı tabıw emes, al juwapqa alıp baratuǵın joldı kórsetiw.
            
            2. KOMMUNIKACIYA STILI HÁM TILI:
                Stil: Ustazǵa tán, biraq qatań emes, doslarsha hám qollap-quwatlawshı tonda sóyle. Paydalanıwshınıń háreketlerin ("Jaqsı urınıs!", "Ájayıp soraw!") xoshametlep tur.
                Til: Juwaplarıń hárdayım qaraqalpaq tiliniń latın álipbesinde, grammatikalıq qátesiz hám kásiplik dárejede bolsın. Ápiwayı hám túsinikli sózlerdi qollan.
            
            3. AYRÍQSHA JAǴDAYLARDÍ BASQARÍW:
                Paydalanıwshı tuwrı juwaptı talap etse: Sıpayı túrde bas tart hám maqsetińdi qayta túsindir. Mısalı: "Maqsetim - sizge juwaptı aytıw emes, al onı ózińiz tabıwıńızǵa járdemlesiw. Keliń, birinshi qádemnen baslayıq, neni anıqlaw kerek dep oylaysız?".
                Paydalanıwshı qáte sheshimin kórsetse: "Bul nadurıs" dep aytpa. Onıń ornına, logikasındaǵı kemshilikke itibarın qarat. Mısalı: "Juwapqa júdá jaqın kelipsiz! Esaplawlarıńızdı qayta tekserip kóriń, ásirese kvadratqa kótergen jerde yamasa qawsırmanı ashqanda kishkene qátelik ketken bolıwı múmkin".
            
            4. FORMATLAW QAǴIYDALARI (EŃ ÁHMIYETLI):
                Mobil ekranǵa sáykeslik: Barlıq juwaplar mobil telefon ekranına (mobile viewport) qolaylı etip sáykeslestiriliwi kerek. Uzın gáplerdi qısqartıwǵa háreket et.
                Jańa qatardan baslaw: Formulalar, matematikalıq ańlatpalar (x^2 + 2y = 0), sanap ótiwler (spisoklar) hám hár bir logikalıq jańa pikir hárdayım jańa qatardan baslanıwı kerek. Bul oqıwǵa júdá qolaylı.
                Nadurıs: Bul teńlemeni sheshiw ushın dáslep diskriminanttı tabamız: D = b^2 - 4ac, sonnan keyin x1,2 = (-b ± √D) / 2a formulasın paydalanamız.
                Durıs:
                Bul teńlemeni sheshiw ushın tómendegi basqıshlardı orınlaymız:
                1. Dáslep diskriminanttı tabamız:
                D = b^2 - 4ac
                2. Keyin teńlemeniń korenlerin esaplaymız:
                x₁,₂ = (-b ± √D) / 2a
        '''
        sys_instruct_chat += f"\n\nTest: {test.subject.name} ({test.subject.grade})\n"
        sys_instruct_chat += f"Test ID: {test.id}\n"
        sys_instruct_chat += f"Student ID: {student_id}\n"
        sys_instruct_chat += f"Student Atı: {result.student_name}\n"
        sys_instruct_chat += f"Sorawlar sanı: {test.test_questions.count()}\n"
        sys_instruct_chat += f"Durıs juwaplar sanı: {result.correct_answers}\n"
        sys_instruct_chat += f"Testti juwmaqlaǵan waqıtı: {result.completed_at.strftime('%H:%M %d.%m.%Y')}\n"
        sys_instruct_chat += f"Házirgi waqıt: {timezone.now().strftime('%H:%M %d.%m.%Y')}\n"
        n = 1
        for answer in result.student_answers.all():
            sys_instruct_chat += f"{n}. {answer.question.question_text}\n"
            sys_instruct_chat += f"A: {answer.question.option_a}\n"
            sys_instruct_chat += f"B: {answer.question.option_b}\n"
            sys_instruct_chat += f"C: {answer.question.option_c}\n"
            sys_instruct_chat += f"D: {answer.question.option_d}\n"
            sys_instruct_chat += f"Paydalanıwshınıń juwabı: {answer.student_answer}\n"
            n += 1
        answer = get_answer_ai(text=message, history=history, sys_instruct_chat=sys_instruct_chat)
        ChatMessage.objects.create(
            student_id=student_id,
            test_id=test_id,
            role='user',
            text=message
        )
        ChatMessage.objects.create(
            student_id=student_id,
            test_id=test_id,
            role='model',
            text=answer
        )

        return JsonResponse({'success': True, 'answer': answer})
    return JsonResponse({'success': False, 'error': 'Only POST requests are allowed'}, status=405)


@csrf_exempt
def api_get_chat_history(request):
    """Get chat history for a student and test"""
    student_id = request.GET.get('student_id')
    test_id = request.GET.get('test_id')
    if not (student_id and test_id):
        return JsonResponse({'success': False, 'error': 'student_id and test_id are required'}, status=400)
    messages = ChatMessage.objects.filter(student_id=student_id, test_id=test_id, system=False).order_by('created_at')
    history = [
        {
            'text': msg.text,
            'role': msg.role,
        }
        for msg in messages
    ]
    return JsonResponse({'success': True, 'history': history})



@csrf_exempt
def api_get_topics(request):
    subject_id = request.GET.get('subject_id')

    if not subject_id:
        return JsonResponse({'error': 'subject_id is required'}, status=400)
    
    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)
    
    return JsonResponse({
        'subject_id': subject_id,
        'topics': subject.topics or ''
    })


@csrf_exempt
def api_get_user_results(request):
    """Get last 1 month results for a student"""
    student_id = request.GET.get('student_id')
    if not student_id:
        return JsonResponse({'success': False, 'error': 'student_id is required'}, status=400)
    from datetime import timedelta
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    results = Result.objects.filter(
        student_id=student_id,
        completed_at__gte=month_ago
    ).order_by('-completed_at')
    data = [
        {
            'test_id': r.test.id,
            'test_name': r.test.subject.name,
            'grade': r.test.subject.grade,
            'score_percentage': r.score_percentage,
            'correct_answers': r.correct_answers,
            'total_questions': r.total_questions,
            'completed_at': (
                r.completed_at.strftime('%H:%M') + " BÚGIN"
                if r.completed_at.date() == now.date()
                else r.completed_at.strftime('%H:%M %d.%m.%Y')
            ),
        }
        for r in results
    ]
    return JsonResponse({'success': True, 'results': data})