
# testapp/utils/analytics.py

from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from testapp.models import Subject, Test, Result, Question
import datetime


class AnalyticsEngine:
    """Analytics va statistics engine"""
    
    def __init__(self, date_range=None):
        self.date_range = date_range or self.get_default_date_range()
    
    def get_default_date_range(self):
        """Default 30 kun oldindan hozirgi vaqtgacha"""
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=30)
        return (start_date, end_date)
    
    def get_overall_statistics(self):
        """Umumiy statistika"""
        start_date, end_date = self.date_range
        
        stats = {
            'total_subjects': Subject.objects.count(),
            'total_questions': Question.objects.count(),
            'total_tests': Test.objects.filter(
                created_at__range=self.date_range
            ).count(),
            'total_participants': Result.objects.filter(
                completed_at__range=self.date_range
            ).count(),
            'average_score': Result.objects.filter(
                completed_at__range=self.date_range
            ).aggregate(avg=Avg('score_percentage'))['avg'] or 0,
            'highest_score': Result.objects.filter(
                completed_at__range=self.date_range
            ).aggregate(max=Max('score_percentage'))['max'] or 0,
            'pass_rate': self.calculate_pass_rate(),
        }
        
        return stats
    
    def calculate_pass_rate(self, passing_score=60):
        """O'tish foizi (60% va undan yuqori)"""
        start_date, end_date = self.date_range
        total_results = Result.objects.filter(
            completed_at__range=self.date_range
        ).count()
        
        if total_results == 0:
            return 0
        
        passed_results = Result.objects.filter(
            completed_at__range=self.date_range,
            score_percentage__gte=passing_score
        ).count()
        
        return (passed_results / total_results) * 100
    
    def get_subject_performance(self):
        """Fan bo'yicha performance"""
        subjects_data = []
        
        for subject in Subject.objects.all():
            results = Result.objects.filter(
                test__subject=subject,
                completed_at__range=self.date_range
            )
            
            if results.exists():
                subject_stats = results.aggregate(
                    avg_score=Avg('score_percentage'),
                    max_score=Max('score_percentage'),
                    min_score=Min('score_percentage'),
                    participant_count=Count('id')
                )
                
                subject_stats.update({
                    'subject_name': subject.name,
                    'subject_id': subject.id,
                    'grade': subject.grade,
                    'total_tests': subject.tests.filter(
                        created_at__range=self.date_range
                    ).count(),
                    'pass_rate': self.calculate_subject_pass_rate(subject),
                })
                
                subjects_data.append(subject_stats)
        
        return sorted(subjects_data, key=lambda x: x['avg_score'], reverse=True)
    
    def calculate_subject_pass_rate(self, subject, passing_score=60):
        """Fan uchun o'tish foizi"""
        results = Result.objects.filter(
            test__subject=subject,
            completed_at__range=self.date_range
        )
        
        total = results.count()
        if total == 0:
            return 0
        
        passed = results.filter(score_percentage__gte=passing_score).count()
        return (passed / total) * 100
    
    def get_daily_statistics(self, days=7):
        """Kunlik statistika"""
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days-1)
        
        daily_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            day_tests = Test.objects.filter(created_at__date=current_date).count()
            day_participants = Result.objects.filter(completed_at__date=current_date).count()
            day_avg_score = Result.objects.filter(
                completed_at__date=current_date
            ).aggregate(avg=Avg('score_percentage'))['avg'] or 0
            
            daily_stats.append({
                'date': current_date,
                'tests_created': day_tests,
                'participants': day_participants,
                'average_score': round(day_avg_score, 2),
                'day_name': current_date.strftime('%A')
            })
            
            current_date += datetime.timedelta(days=1)
        
        return daily_stats
    
    def get_top_performers(self, limit=10):
        """Eng yaxshi natijalar"""
        return Result.objects.filter(
            completed_at__range=self.date_range
        ).order_by('-score_percentage', '-completed_at')[:limit]
    
    def get_question_difficulty_analysis(self):
        """Savollar qiyinligi tahlili"""
        from django.db.models import Count, Case, When, IntegerField
        
        questions_data = []
        
        for question in Question.objects.all():
            # Bu savol qatnashgan barcha javoblar
            correct_answers = question.student_answers.filter(
                is_correct=True,
                result__completed_at__range=self.date_range
            ).count()
            
            total_answers = question.student_answers.filter(
                result__completed_at__range=self.date_range
            ).count()
            
            if total_answers > 0:
                difficulty_percentage = (correct_answers / total_answers) * 100
                
                # Qiyinlik darajasi
                if difficulty_percentage >= 80:
                    difficulty = 'Easy'
                elif difficulty_percentage >= 60:
                    difficulty = 'Medium'
                elif difficulty_percentage >= 40:
                    difficulty = 'Hard'
                else:
                    difficulty = 'Very Hard'
                
                questions_data.append({
                    'question_id': question.id,
                    'question_text': question.question_text[:100] + '...' if len(question.question_text) > 100 else question.question_text,
                    'subject': question.subject.name,
                    'correct_answers': correct_answers,
                    'total_answers': total_answers,
                    'success_rate': round(difficulty_percentage, 2),
                    'difficulty': difficulty
                })
        
        return sorted(questions_data, key=lambda x: x['success_rate'])
    
    def get_grade_comparison(self):
        """Sinflar bo'yicha taqqoslash"""
        grades_data = []
        
        for grade in range(1, 12):  # 1-11 sinflar
            results = Result.objects.filter(
                test__subject__grade=grade,
                completed_at__range=self.date_range
            )
            
            if results.exists():
                grade_stats = results.aggregate(
                    avg_score=Avg('score_percentage'),
                    max_score=Max('score_percentage'),
                    min_score=Min('score_percentage'),
                    participant_count=Count('id')
                )
                
                grade_stats.update({
                    'grade': grade,
                    'subjects_count': Subject.objects.filter(grade=grade).count(),
                    'tests_count': Test.objects.filter(
                        subject__grade=grade,
                        created_at__range=self.date_range
                    ).count()
                })
                
                grades_data.append(grade_stats)
        
        return sorted(grades_data, key=lambda x: x['grade'])