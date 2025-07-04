# testapp/models.py

from django.db import models
from django.utils import timezone
import random

class Subject(models.Model):
    """Fanlar jadvali"""
    name = models.CharField(max_length=100, verbose_name="Subject name")
    grade = models.IntegerField(verbose_name="Grade")
    start_time = models.TimeField(verbose_name="Boshlanish vaqti")
    questions_count = models.IntegerField(verbose_name="Test savollar soni", default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.grade}-klass)"

    def get_scheduled_days(self):
        """Fanning belgilangan kunlarini qaytaradi"""
        return self.subject_days.all()
    
    def has_enough_questions(self):
        """Fanda yetarli savol bor-yo'qligini tekshiradi"""
        return self.questions.count() >= self.questions_count


class SubjectDay(models.Model):
    """Fan kunlari jadvali"""
    DAY_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='subject_days')
    day_of_week = models.IntegerField(choices=DAY_CHOICES, verbose_name="Hafta kuni")
    
    class Meta:
        verbose_name = "Fan kuni"
        verbose_name_plural = "Fan kunlari"
        unique_together = ['subject', 'day_of_week']
    
    def __str__(self):
        return f"{self.subject.name} - {self.get_day_of_week_display()}"


class Question(models.Model):
    """Savollar jadvali"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(verbose_name="Savol matni")
    option_a = models.CharField(max_length=255, verbose_name="A variant")
    option_b = models.CharField(max_length=255, verbose_name="B variant")
    option_c = models.CharField(max_length=255, verbose_name="C variant")
    option_d = models.CharField(max_length=255, verbose_name="D variant")
    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        verbose_name="To'g'ri javob"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject.name} - {self.question_text[:50]}..."
    
    def get_options(self):
        """Variantlarni dict ko'rinishida qaytaradi"""
        return {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }


class Test(models.Model):
    """Testlar jadvali"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tests')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    
    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Testlar"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Test #{self.id} - {self.subject.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_questions(self):
        """Test savollarini tartib bo'yicha qaytaradi"""
        return Question.objects.filter(
            test_questions__test=self
        ).order_by('test_questions__order_number')
    
    def get_participants_count(self):
        """Qatnashuvchilar sonini qaytaradi"""
        return self.results.count()
    
    def get_average_score(self):
        """O'rtacha ballni qaytaradi"""
        results = self.results.all()
        if results:
            return sum([r.score_percentage for r in results]) / len(results)
        return 0


class TestQuestion(models.Model):
    """Test-savol aloqasi jadvali"""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='test_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='test_questions')
    order_number = models.IntegerField(verbose_name="Tartib raqami")
    
    class Meta:
        verbose_name = "Test savoli"
        verbose_name_plural = "Test savollari"
        unique_together = ['test', 'question']
        ordering = ['order_number']
    
    def __str__(self):
        return f"Test {self.test.id} - Savol {self.order_number}"


class Result(models.Model):
    """Natijalar jadvali"""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results')
    student_id = models.CharField(max_length=50, verbose_name="Student ID")
    student_name = models.CharField(max_length=100, verbose_name="Ism-familiya")
    score_percentage = models.FloatField(verbose_name="Ball (foiz)")
    total_questions = models.IntegerField(verbose_name="Jami savollar")
    correct_answers = models.IntegerField(verbose_name="To'g'ri javoblar")
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Natija"
        verbose_name_plural = "Natijalar"
        unique_together = ['test', 'student_id']  # Bir testga faqat bir marta qatnashish
        ordering = ['-score_percentage', '-completed_at']
    
    def __str__(self):
        return f"{self.student_name} - {self.score_percentage}% (Test #{self.test.id})"
    
    def get_rank(self):
        """Reytingdagi o'rinni qaytaradi"""
        better_results = Result.objects.filter(
            test=self.test,
            score_percentage__gt=self.score_percentage
        ).count()
        return better_results + 1


class StudentAnswer(models.Model):
    """Talaba javoblari jadvali"""
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    student_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        verbose_name="Talaba javobi"
    )
    is_correct = models.BooleanField(verbose_name="To'g'ri javobmi")
    
    class Meta:
        verbose_name = "Talaba javobi"
        verbose_name_plural = "Talaba javoblari"
        unique_together = ['result', 'question']
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{self.result.student_name} - Savol {self.question.id} - {self.student_answer} {status}"


class ChatMessage(models.Model):
    """Chatbot message history"""
    student_id = models.CharField(max_length=50, verbose_name="Student ID")
    test_id = models.IntegerField(verbose_name="Test ID")
    text = models.TextField(verbose_name="Message text")
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('model', 'Model')], verbose_name="Role")
    system = models.BooleanField(default=False, verbose_name="System message")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {self.role}: {self.text[:40]}..."