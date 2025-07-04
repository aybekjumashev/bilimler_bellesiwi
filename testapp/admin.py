# testapp/admin.py

from django.contrib import admin
from .models import Subject, SubjectDay, Question, Test, TestQuestion, Result, StudentAnswer

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'start_time', 'questions_count', 'get_questions_available', 'created_at']
    list_filter = ['grade', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    
    def get_questions_available(self, obj):
        count = obj.questions.count()
        return f"{count} ta savol"
    get_questions_available.short_description = "Mavjud savollar"


class SubjectDayInline(admin.TabularInline):
    model = SubjectDay
    extra = 1


@admin.register(SubjectDay)
class SubjectDayAdmin(admin.ModelAdmin):
    list_display = ['subject', 'get_day_of_week_display']
    list_filter = ['day_of_week', 'subject']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'question_text_short', 'correct_answer', 'created_at']
    list_filter = ['subject', 'correct_answer', 'created_at']
    search_fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d']
    ordering = ['-created_at']
    
    def question_text_short(self, obj):
        return obj.question_text[:100] + "..." if len(obj.question_text) > 100 else obj.question_text
    question_text_short.short_description = "Savol matni"


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 0
    readonly_fields = ['order_number']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'created_at', 'is_active', 'get_participants_count', 'get_questions_count']
    list_filter = ['subject', 'is_active', 'created_at']
    ordering = ['-created_at']
    inlines = [TestQuestionInline]
    readonly_fields = ['created_at']
    
    def get_participants_count(self, obj):
        return obj.get_participants_count()
    get_participants_count.short_description = "Qatnashuvchilar"
    
    def get_questions_count(self, obj):
        return obj.test_questions.count()
    get_questions_count.short_description = "Savollar soni"


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ['test', 'question_short', 'order_number']
    list_filter = ['test']
    ordering = ['test', 'order_number']
    
    def question_short(self, obj):
        return obj.question.question_text[:50] + "..."
    question_short.short_description = "Savol"


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ['question', 'student_answer', 'is_correct']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_id', 'test', 'score_percentage', 'correct_answers', 'total_questions', 'completed_at']
    list_filter = ['test', 'completed_at', 'score_percentage']
    search_fields = ['student_name', 'student_id']
    ordering = ['-completed_at', '-score_percentage']
    inlines = [StudentAnswerInline]
    readonly_fields = ['test', 'student_id', 'student_name', 'score_percentage', 'total_questions', 'correct_answers', 'completed_at']


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['result', 'question_short', 'student_answer', 'correct_answer', 'is_correct']
    list_filter = ['is_correct', 'student_answer']
    ordering = ['result', 'question']
    
    def question_short(self, obj):
        return obj.question.question_text[:50] + "..."
    question_short.short_description = "Savol"
    
    def correct_answer(self, obj):
        return obj.question.correct_answer
    correct_answer.short_description = "To'g'ri javob"