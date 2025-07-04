
# testapp/utils/exports.py

import csv
import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from io import BytesIO
import json


def export_results_csv(results, filename=None):
    """Export results to CSV format"""
    if not filename:
        filename = f"test_results_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Student Name',
        'Student ID',
        'Test ID',
        'Subject',
        'Grade',
        'Score (%)',
        'Correct Answers',
        'Total Questions',
        'Completion Date',
        'Completion Time'
    ])
    
    # Data
    for result in results:
        writer.writerow([
            result.student_name,
            result.student_id,
            result.test.id,
            result.test.subject.name,
            result.test.subject.grade,
            round(result.score_percentage, 2),
            result.correct_answers,
            result.total_questions,
            result.completed_at.strftime('%Y-%m-%d'),
            result.completed_at.strftime('%H:%M:%S')
        ])
    
    return response


def export_results_excel(results, filename=None):
    """Export results to Excel format"""
    if not filename:
        filename = f"test_results_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Create workbook
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Test Results"
    
    # Header
    headers = [
        'Student Name', 'Student ID', 'Test ID', 'Subject', 'Grade',
        'Score (%)', 'Correct Answers', 'Total Questions', 
        'Completion Date', 'Completion Time'
    ]
    worksheet.append(headers)
    
    # Style header
    for cell in worksheet[1]:
        cell.font = openpyxl.styles.Font(bold=True)
        cell.fill = openpyxl.styles.PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = openpyxl.styles.Font(color="FFFFFF", bold=True)
    
    # Data
    for result in results:
        worksheet.append([
            result.student_name,
            result.student_id,
            result.test.id,
            result.test.subject.name,
            result.test.subject.grade,
            round(result.score_percentage, 2),
            result.correct_answers,
            result.total_questions,
            result.completed_at.strftime('%Y-%m-%d'),
            result.completed_at.strftime('%H:%M:%S')
        ])
    
    # Auto-adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # Save to BytesIO
    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)
    
    response = HttpResponse(
        excel_file.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def export_questions_csv(questions, filename=None):
    """Export questions to CSV format"""
    if not filename:
        filename = f"questions_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Subject',
        'Grade',
        'Question Text',
        'Option A',
        'Option B',
        'Option C',
        'Option D',
        'Correct Answer',
        'Created Date'
    ])
    
    # Data
    for question in questions:
        writer.writerow([
            question.subject.name,
            question.subject.grade,
            question.question_text,
            question.option_a,
            question.option_b,
            question.option_c,
            question.option_d,
            question.correct_answer,
            question.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


def export_questions_json(questions, filename=None):
    """Export questions to JSON format"""
    if not filename:
        filename = f"questions_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    data = []
    for question in questions:
        data.append({
            'id': question.id,
            'subject': {
                'name': question.subject.name,
                'grade': question.subject.grade,
                'id': question.subject.id
            },
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d
            },
            'correct_answer': question.correct_answer,
            'created_at': question.created_at.isoformat()
        })
    
    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def export_subjects_csv(subjects, filename=None):
    """Export subjects to CSV format"""
    if not filename:
        filename = f"subjects_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Subject Name',
        'Grade',
        'Start Time',
        'Questions Count',
        'Available Questions',
        'Scheduled Days',
        'Total Tests',
        'Created Date'
    ])
    
    # Data
    for subject in subjects:
        scheduled_days = ', '.join([
            day.get_day_of_week_display() 
            for day in subject.subject_days.all()
        ])
        
        writer.writerow([
            subject.name,
            subject.grade,
            subject.start_time.strftime('%H:%M'),
            subject.questions_count,
            subject.questions.count(),
            scheduled_days,
            subject.tests.count(),
            subject.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response
